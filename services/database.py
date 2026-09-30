import re
from difflib import SequenceMatcher
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

def normalize_title_text(t: str) -> str:
    """Strips punctuation, quotes, source tags, and lowercases for reliable matching."""
    if not t:
        return ""
    # Strip trailing news outlet tags (e.g., "- Amnesty International", "- Jurist.org")
    t = re.sub(r'\s*-\s*[A-Za-z0-9\s\.\+]+$', '', t)
    # Strip non-alphanumeric characters
    t = re.sub(r'[^a-zA-Z0-9 ]', '', t.lower())
    return re.sub(r'\s+', ' ', t).strip()

def check_article_exists(url: str, title: str) -> bool:
    """Checks if exact URL or normalized title exists in Supabase article_queue across any status."""
    if not supabase or not url:
        return False
    try:
        # 1. Exact URL match
        res_url = supabase.table("article_queue").select("id").eq("url", url).execute()
        if res_url.data and len(res_url.data) > 0:
            return True

        # 2. Normalized Title match against recent history (last 100 articles)
        norm_new = normalize_title_text(title)
        if norm_new:
            res_titles = supabase.table("article_queue").select("title").order("created_at", desc=True).limit(100).execute()
            if res_titles.data:
                for row in res_titles.data:
                    ext_norm = normalize_title_text(row.get("title", ""))
                    if ext_norm and norm_new == ext_norm:
                        return True
        return False
    except Exception as e:
        print(f"[!] Database check error ({e}). Assuming article exists to protect pipeline.")
        return True

def is_semantic_duplicate(new_title: str, threshold: float = 0.70) -> bool:
    """Performs local fuzzy matching against recent articles to prevent duplicate story scoring."""
    if not supabase or not new_title:
        return False
    try:
        res = supabase.table("article_queue").select("title").order("created_at", desc=True).limit(100).execute()
        existing_items = res.data or []

        new_clean = normalize_title_text(new_title)

        for item in existing_items:
            ext_title = item.get("title", "")
            if not ext_title:
                continue
            ext_clean = normalize_title_text(ext_title)

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
