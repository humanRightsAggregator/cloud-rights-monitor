import json
from datetime import datetime, timezone
import google.generativeai as genai
from config import GEMINI_API_KEY
from services.database import supabase
from services.ai_engine import get_active_model

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"[!] Gemini Queue Manager config error: {e}")

def score_article_with_ai(title: str, snippet: str) -> tuple:
    """Evaluates human rights importance (60%) and global popularity/trending potential (40%). Returns (imp, pop, err)."""
    prompt = f"""
    You are an expert global news editor and human rights analyst.
    Evaluate this news report:
    - Headline: {title}
    - Snippet: {snippet}

    Assign two numeric scores from 1.0 to 10.0:
    1. "importance_score": Rate gravity of human rights impact (10 = active genocide, war crimes, mass displacement, crimes against humanity; 1 = routine organizational notice).
    2. "popularity_score": Rate search interest & global trending potential (10 = major geopolitical entities/regions like UN/US/Iran/Ukraine/China, high search interest; 1 = obscure local legal dispute).

    Output strictly valid JSON without markdown:
    {{
      "importance_score": 8.5,
      "popularity_score": 7.0
    }}
    """
    try:
        model = get_active_model()
        # Enforce JSON mode to prevent parsing errors
        res = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        clean_text = res.text.strip()
        data = json.loads(clean_text)
        
        imp = float(data.get("importance_score", 0.0))
        pop = float(data.get("popularity_score", 0.0))
        if imp == 0.0 or pop == 0.0:
            return None, None, "AI returned zero/invalid scores"
            
        return imp, pop, None
    except Exception as e:
        print(f"[!] AI Scoring error for '{title[:25]}': {e}")
        return None, None, str(e)

def process_and_queue_article(title: str, snippet: str, url: str, image_url: str, source_feed: str) -> dict:
    """Scores article, applies 5.5 auto-purge threshold, and handles scoring errors safely."""
    existing = supabase.table("article_queue").select("id, status").eq("url", url).execute()
    if existing.data and existing.data[0]["status"] not in ["needs_rescore"]:
        return {"action": "ignored", "reason": "already_queued"}

    imp_score, pop_score, err = score_article_with_ai(title, snippet)

    # Prevent silent purge: if AI fails, mark as 'needs_rescore' instead of auto-purging
    if err or imp_score is None:
        supabase.table("article_queue").upsert({
            "url": url,
            "title": title,
            "snippet": snippet,
            "image_url": image_url,
            "source_feed": source_feed,
            "importance_score": 0.0,
            "popularity_score": 0.0,
            "combined_score": 0.0,
            "status": "needs_rescore"
        }, on_conflict="url").execute()
        return {"action": "needs_rescore", "error": err}

    combined_score = round((imp_score * 0.6) + (pop_score * 0.4), 2)

    # 1. Auto-Purge Rule (< 5.5)
    if combined_score < 5.5:
        supabase.table("article_queue").upsert({
            "url": url,
            "title": title,
            "snippet": snippet,
            "image_url": image_url,
            "source_feed": source_feed,
            "importance_score": imp_score,
            "popularity_score": pop_score,
            "combined_score": combined_score,
            "status": "discarded"
        }, on_conflict="url").execute()
        return {"action": "discarded", "score": combined_score}

    # 2. Breaking News Fast-Track (>= 9.0)
    status = "fast_tracked" if combined_score >= 9.0 else "queued"

    record = supabase.table("article_queue").upsert({
        "url": url,
        "title": title,
        "snippet": snippet,
        "image_url": image_url,
        "source_feed": source_feed,
        "importance_score": imp_score,
        "popularity_score": pop_score,
        "combined_score": combined_score,
        "status": status
    }, on_conflict="url").execute()

    record_data = record.data[0] if record.data else {}
    return {"action": status, "score": combined_score, "data": record_data}

def get_top_prioritized_queue(limit: int = 2) -> list:
    """Retrieves top-ranked queued items applying Time-Decay and Source Diversity constraints."""
    response = supabase.table("article_queue").select("*").eq("status", "queued").execute()
    queued_items = response.data or []

    if not queued_items:
        return []

    now = datetime.now(timezone.utc)

    for item in queued_items:
        created_at = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
        hours_in_queue = (now - created_at).total_seconds() / 3600.0
        effective_score = item["combined_score"] - (hours_in_queue * 0.15)
        item["effective_score"] = effective_score

    queued_items.sort(key=lambda x: x["effective_score"], reverse=True)

    selected_batch = []
    used_sources = set()

    for item in queued_items:
        source = item.get("source_feed")
        if source not in used_sources:
            selected_batch.append(item)
            used_sources.add(source)
            if len(selected_batch) == limit:
                break

    return selected_batch

def rescore_discarded_or_pending_articles() -> dict:
    """Rescue utility to re-evaluate articles stuck in 'discarded' with a default 5.0 score or 'needs_rescore' status."""
    response = supabase.table("article_queue").select("*").in_("status", ["discarded", "needs_rescore"]).execute()
    items = response.data or []
    
    rescored_total = 0
    newly_queued = 0
    fast_tracked = 0
    errors = []

    for item in items:
        # Rescore if it was stuck on default 5.0 or marked for rescore
        if item["combined_score"] in [5.0, 0.0] or item["status"] == "needs_rescore":
            imp_score, pop_score, err = score_article_with_ai(item["title"], item["snippet"])
            if err or imp_score is None:
                errors.append(f"Rescore error for '{item['title'][:25]}': {err}")
                continue

            combined_score = round((imp_score * 0.6) + (pop_score * 0.4), 2)
            
            if combined_score >= 9.0:
                new_status = "fast_tracked"
                fast_tracked += 1
            elif combined_score >= 5.5:
                new_status = "queued"
                newly_queued += 1
            else:
                new_status = "discarded"

            supabase.table("article_queue").update({
                "importance_score": imp_score,
                "popularity_score": pop_score,
                "combined_score": combined_score,
                "status": new_status
            }).eq("id", item["id"]).execute()
            
            rescored_total += 1

    return {
        "rescored_total": rescored_total,
        "newly_queued": newly_queued,
        "fast_tracked": fast_tracked,
        "errors": errors
    }

def get_queue_status_metrics() -> tuple:
    """Returns (total_pending_count, next_up_title)."""
    response = supabase.table("article_queue").select("title, combined_score").eq("status", "queued").order("combined_score", desc=True).execute()
    data = response.data or []
    count = len(data)
    next_title = data[0]["title"] if count > 0 else ""
    return count, next_title
