import re
from difflib import SequenceMatcher
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

def check_article_exists(url: str, title: str) -> bool:
    """Checks if the exact URL or title exists using safe parameter binding."""
    if not supabase:
        return False
    try:
        res_url = supabase.table("article_queue").select("id").eq("url", url).execute()
        if res_url.data and len(res_url.data) > 0:
            return True
            
        res_title = supabase.table("article_queue").select("id").eq("title", title).execute()
        return len(res_title.data) > 0 if res_title.data else False
    except Exception as e:
        print(f"[!] Database check error: {e}")
        return False

def is_semantic_duplicate(new_title: str, threshold: float = 0.65) -> bool:
    """Performs local fuzzy matching against recent articles to prevent duplicate story scoring."""
    if not supabase or not new_title:
        return False
    try:
        res = supabase.table("article_queue").select("title").order("created_at", desc=True).limit(40).execute()
        existing_items = res.data or []

        new_clean = re.sub(r'[^a-zA-Z0-9 ]', '', new_title.lower()).strip()

        for item in existing_items:
            ext_title = item.get("title", "")
            if not ext_title:
                continue
            ext_clean = re.sub(r'[^a-zA-Z0-9 ]', '', ext_title.lower()).strip()

            similarity = SequenceMatcher(None, new_clean, ext_clean).ratio()
            if similarity >= threshold:
                print(f"[!] Semantic Duplicate Blocked ({round(similarity*100, 1)}% match): '{new_title[:30]}...' matches '{ext_title[:30]}...'")
                return True
        return False
    except Exception as e:
        print(f"[!] Semantic check error: {e}")
        return False

def save_article_draft(url: str, title: str, draft_text: str, status: str = "processing"):
    """Updates article status cleanly in article_queue."""
    if not supabase:
        return
    try:
        supabase.table("article_queue").update({"status": status}).eq("url", url).execute()
    except Exception as e:
        print(f"[!] Save status error: {e}")

def get_recent_articles(limit: int = 15) -> list:
    """Fetches recent titles from article_queue for context matching."""
    if not supabase:
        return []
    try:
        res = supabase.table("article_queue").select("title").order("created_at", desc=True).limit(limit).execute()
        return [r["title"] for r in res.data if r.get("title")] if res.data else []
    except Exception as e:
        print(f"[!] Fetch recent articles error: {e}")
        return []
