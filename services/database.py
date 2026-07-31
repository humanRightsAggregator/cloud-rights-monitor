from config import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client, Client

supabase: Client = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"[!] Supabase Init Error: {e}")

def check_article_exists(url: str) -> bool:
    """Checks if an article has already been saved in the database."""
    if not supabase:
        return False
    try:
        existing = supabase.table("processed_articles").select("url").eq("url", url).execute()
        return len(existing.data) > 0
    except Exception as e:
        print(f"[!] Supabase Select Error: {e}")
        return False

def save_article_draft(url: str, headline: str, draft_text: str, status: str = "pending") -> int:
    """Inserts or updates an article draft and returns its database ID."""
    if not supabase:
        return 1
    try:
        res = supabase.table("processed_articles").upsert({
            "url": url,
            "headline": headline,
            "draft_text": draft_text,
            "status": status
        }).execute()
        if res.data:
            return res.data[0]["id"]
    except Exception as e:
        print(f"[!] Supabase Save Error: {e}")
    return 1

def get_draft_by_id(article_id: str):
    """Fetches a specific article draft by its ID."""
    if not supabase:
        return None
    try:
        res = supabase.table("processed_articles").select("draft_text").eq("id", article_id).execute()
        if res.data:
            return res.data[0]["draft_text"]
    except Exception as e:
        print(f"[!] Supabase Fetch Error: {e}")
    return None

def update_article_status(article_id: str, new_status: str):
    """Updates status to 'published' or 'rejected'."""
    if not supabase:
        return
    try:
        supabase.table("processed_articles").update({"status": new_status}).eq("id", article_id).execute()
    except Exception as e:
        print(f"[!] Supabase Status Update Error: {e}")
