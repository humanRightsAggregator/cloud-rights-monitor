import re
from datetime import datetime, timedelta, timezone
from services.ai_engine import get_authorized_models
from services.database import supabase

def calculate_urgency_score(title: str, snippet: str) -> float:
    """Calculates news urgency score (1.0 - 10.0) using Gemini models safely."""
    models = get_authorized_models()
    if not models:
        return 7.0  # Default fallback score

    prompt = f"Rate the human rights news urgency of this item from 1.0 to 10.0. Return ONLY a single numeric float.\nTitle: {title}\nSnippet: {snippet}"

    for model in models:
        try:
            response = model.generate_content(prompt)
            match = re.search(r'\d+(\.\d+)?', response.text)
            if match:
                score = float(match.group(0))
                return min(max(score, 1.0), 10.0)
        except Exception as e:
            print(f"[!] AI Scoring attempt failed: {e}")
            continue
    return 7.0

def process_and_queue_article(title: str, snippet: str, link: str, image_url: str, source: str) -> dict:
    """Evaluates and routes incoming RSS items into the 4-tier pipeline."""
    score = calculate_urgency_score(title, snippet)
    item_data = {
        "title": title,
        "snippet": snippet,
        "url": link,
        "image_url": image_url,
        "source": source,
        "combined_score": score,
        "status": "pending"
    }

    if score >= 8.5:
        return {"action": "fast_tracked", "data": item_data}
    elif score >= 6.8:
        if supabase:
            try:
                supabase.table("article_queue").insert(item_data).execute()
            except Exception as e:
                print(f"[!] Queue insert error: {e}")
        return {"action": "queued", "data": item_data}
    elif score >= 5.5:
        return {"action": "low_tier_immediate", "data": item_data}
    else:
        return {"action": "discarded", "data": item_data}

def get_top_prioritized_queue(limit: int = 4) -> list:
    """Fetches highest-scoring pending articles from Supabase queue (Default batch: 4)."""
    if not supabase:
        return []
    try:
        res = supabase.table("article_queue") \
            .select("*") \
            .eq("status", "pending") \
            .order("combined_score", desc=True) \
            .limit(limit) \
            .execute()
        return res.data or []
    except Exception as e:
        print(f"[!] Error fetching queue: {e}")
        return []

def get_queue_status_metrics() -> tuple:
    """Returns (pending_count, next_up_title)."""
    if not supabase:
        return 0, "N/A"
    try:
        res = supabase.table("article_queue") \
            .select("title") \
            .eq("status", "pending") \
            .order("combined_score", desc=True) \
            .execute()
        data = res.data or []
        count = len(data)
        next_title = data[0]["title"] if count > 0 else "None"
        return count, next_title
    except Exception as e:
        print(f"[!] Metric fetch error: {e}")
        return 0, "N/A"

def clean_expired_queue_items() -> int:
    """Purges queue items older than 48 hours."""
    if not supabase:
        return 0
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
        res = supabase.table("article_queue") \
            .delete() \
            .lt("created_at", cutoff) \
            .eq("status", "pending") \
            .execute()
        return len(res.data) if res.data else 0
    except Exception as e:
        print(f"[!] Expired queue cleanup error: {e}")
        return 0

def rescore_discarded_or_pending_articles() -> dict:
    return {"rescored_total": 0, "newly_queued": 0, "fast_tracked": 0, "errors": []}
