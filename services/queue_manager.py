import json
import time
from datetime import datetime, timezone
import google.generativeai as genai
from config import GEMINI_API_KEY
from services.database import supabase
from services.ai_engine import get_authorized_models

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"[!] Gemini Queue Manager config error: {e}")

def score_article_with_ai(title: str, snippet: str) -> tuple:
    prompt = f"""
    You are an expert global news editor and human rights analyst.
    Evaluate this news report:
    - Headline: {title}
    - Snippet: {snippet}

    Assign two numeric scores from 1.0 to 10.0:
    1. "importance_score": Rate gravity of human rights impact (10 = active genocide, war crimes, mass displacement; 1 = routine organizational notice).
    2. "popularity_score": Rate search interest & global trending potential (10 = major geopolitical entities, high search interest; 1 = obscure local dispute).

    Output strictly valid JSON without markdown:
    {{
      "importance_score": 8.5,
      "popularity_score": 7.0
    }}
    """
    model_candidates = get_authorized_models()
    last_error = None

    for model_name in model_candidates:
        try:
            model = genai.GenerativeModel(model_name)
            try:
                gen_config = genai.types.GenerationConfig(response_mime_type="application/json")
                res = model.generate_content(prompt, generation_config=gen_config)
            except Exception:
                res = model.generate_content(prompt)

            clean_text = res.text.replace('```json', '').replace('```', '').strip()
            data = json.loads(clean_text)
            
            imp = float(data.get("importance_score", 0.0))
            pop = float(data.get("popularity_score", 0.0))
            if imp == 0.0 or pop == 0.0:
                continue
                
            return imp, pop, None
        except Exception as e:
            last_error = str(e)
            print(f"[!] Scoring fallback on dynamically fetched '{model_name}' for '{title[:20]}': {e}")
            continue

    return None, None, last_error or "All candidate models failed"

def clean_expired_queue_items() -> int:
    """Removes items older than 48 hours unless importance_score >= 8.0."""
    response = supabase.table("article_queue").select("*").eq("status", "queued").execute()
    items = response.data or []
    now = datetime.now(timezone.utc)
    expired_count = 0

    for item in items:
        created_at = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
        hours_in_queue = (now - created_at).total_seconds() / 3600.0
        
        # Expiry Logic: > 48 hours AND Importance < 8.0
        if hours_in_queue > 48.0 and float(item.get("importance_score", 0)) < 8.0:
            supabase.table("article_queue").update({"status": "discarded_expired"}).eq("id", item["id"]).execute()
            expired_count += 1
            
    return expired_count

def process_and_queue_article(title: str, snippet: str, url: str, image_url: str, source_feed: str) -> dict:
    existing = supabase.table("article_queue").select("id, status").eq("url", url).execute()
    if existing.data and existing.data[0]["status"] not in ["needs_rescore"]:
        return {"action": "ignored", "reason": "already_queued"}

    imp_score, pop_score, err = score_article_with_ai(title, snippet)

    if err or imp_score is None:
        supabase.table("article_queue").upsert({
            "url": url, "title": title, "snippet": snippet, "image_url": image_url,
            "source_feed": source_feed, "importance_score": 0.0, "popularity_score": 0.0,
            "combined_score": 0.0, "status": "needs_rescore"
        }, on_conflict="url").execute()
        return {"action": "needs_rescore", "error": err}

    combined_score = round((imp_score * 0.6) + (pop_score * 0.4), 2)

    # 4-Tier Traffic Controller Logic
    if combined_score < 5.5:
        status = "discarded"
    elif combined_score < 6.8:
        status = "low_tier_immediate"
    elif combined_score < 8.5:
        status = "queued"
    else:
        status = "fast_tracked"

    record = supabase.table("article_queue").upsert({
        "url": url, "title": title, "snippet": snippet, "image_url": image_url,
        "source_feed": source_feed, "importance_score": imp_score,
        "popularity_score": pop_score, "combined_score": combined_score, "status": status
    }, on_conflict="url").execute()

    record_data = record.data[0] if record.data else {}
    return {"action": status, "score": combined_score, "data": record_data}

def get_top_prioritized_queue(limit: int = 2) -> list:
    response = supabase.table("article_queue").select("*").eq("status", "queued").execute()
    queued_items = response.data or []

    if not queued_items:
        return []

    now = datetime.now(timezone.utc)
    for item in queued_items:
        created_at = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
        hours_in_queue = (now - created_at).total_seconds() / 3600.0
        item["effective_score"] = item["combined_score"] - (hours_in_queue * 0.15)

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
    response = supabase.table("article_queue").select("*").in_("status", ["discarded", "needs_rescore"]).execute()
    items = response.data or []
    
    rescored_total = newly_queued = fast_tracked = 0
    errors = []

    for item in items:
        if item["combined_score"] in [5.0, 0.0] or item["status"] == "needs_rescore":
            imp_score, pop_score, err = score_article_with_ai(item["title"], item["snippet"])
            if err or imp_score is None:
                errors.append(f"'{item['title'][:30]}': {err}")
            else:
                combined_score = round((imp_score * 0.6) + (pop_score * 0.4), 2)
                
                # Re-apply 4-Tier Logic
                if combined_score < 5.5:
                    new_status = "discarded"
                elif combined_score < 6.8:
                    new_status = "low_tier_immediate"
                    newly_queued += 1 # Treating low-tier as rescued for stats
                elif combined_score < 8.5:
                    new_status = "queued"
                    newly_queued += 1
                else:
                    new_status = "fast_tracked"
                    fast_tracked += 1

                supabase.table("article_queue").update({
                    "importance_score": imp_score, "popularity_score": pop_score,
                    "combined_score": combined_score, "status": new_status
                }).eq("id", item["id"]).execute()
                
                rescored_total += 1
            time.sleep(2.5)

    return {"rescored_total": rescored_total, "newly_queued": newly_queued, "fast_tracked": fast_tracked, "errors": errors}

def get_queue_status_metrics() -> tuple:
    response = supabase.table("article_queue").select("title, combined_score").eq("status", "queued").order("combined_score", desc=True).execute()
    data = response.data or []
    return len(data), data[0]["title"] if data else ""
