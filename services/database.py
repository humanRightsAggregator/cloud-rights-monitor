import re
from difflib import SequenceMatcher
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

def check_article_exists(url: str, title: str) -> bool:
    """Checks if the exact URL or exact title already exists in Supabase."""
    if not supabase:
        return False
    try:
        res = supabase.table("article_queue").select("id").or_(f"url.eq.{url},title.eq.{title}").execute()
        return len(res.data) > 0
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
    if not supabase:
        return
    try:
        supabase.table("processed_articles").upsert({
            "url": url,
            "title": title,
            "draft_text": draft_text,
            "status": status
        }, on_conflict="url").execute()
    except Exception as e:
        print(f"[!] Save draft error: {e}")

def get_recent_articles(limit: int = 15) -> list:
    if not supabase:
        return []
    try:
        res = supabase.table("processed_articles").select("title").order("created_at", desc=True).limit(limit).execute()
        return [r["title"] for r in res.data] if res.data else []
    except Exception as e:
        print(f"[!] Fetch recent articles error: {e}")
        return []
