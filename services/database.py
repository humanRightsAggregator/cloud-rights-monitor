from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"[!] Supabase initialization error: {e}")

def check_article_exists(url: str) -> bool:
    """Checks if an article exists. Returns True on error to prevent duplicate spamming."""
    if not supabase:
        print("[!] Supabase client uninitialized. Skipping article for safety.")
        return True
    try:
        res = supabase.table("articles").select("id").eq("url", url).execute()
        return len(res.data) > 0
    except Exception as e:
        print(f"[!] Supabase Select Error: {e}")
        # SAFEGUARD: Return True on error so offline DB never triggers duplicate posts
        return True

def save_article_draft(url: str, headline: str, draft: str, status: str = "published"):
    """Saves published article record to Supabase."""
    if not supabase:
        return
    try:
        supabase.table("articles").insert({
            "url": url,
            "headline": headline,
            "draft_text": draft,
            "status": status
        }).execute()
    except Exception as e:
        print(f"[!] Supabase Save Error: {e}")

def get_recent_articles(limit: int = 15) -> list:
    """Retrieves recent published articles."""
    if not supabase:
        return []
    try:
        res = supabase.table("articles").select("headline, draft_text").order("created_at", desc=True).limit(limit).execute()
        return res.data
    except Exception as e:
        print(f"[!] Supabase Fetch Recent Error: {e}")
        return []
