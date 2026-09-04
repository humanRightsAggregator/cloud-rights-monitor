from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

CLEAN_URL = SUPABASE_URL.strip() if SUPABASE_URL else ""
CLEAN_KEY = SUPABASE_KEY.replace('\n', '').replace('\r', '').replace(' ', '').strip() if SUPABASE_KEY else ""

supabase: Client = None

if CLEAN_URL and CLEAN_KEY:
    try:
        supabase = create_client(CLEAN_URL, CLEAN_KEY)
    except Exception as e:
        print(f"[!] Supabase initialization error: {e}")

def check_article_exists(url: str, headline: str = "") -> bool:
    """Checks if an article exists by normalized URL OR exact headline."""
    if not supabase:
        print("[!] Supabase client uninitialized. Skipping for safety.")
        return True
    try:
        clean_url = url.strip().rstrip('/')
        
        # 1. Check URL
        res_url = supabase.table("articles").select("id").eq("url", clean_url).execute()
        if len(res_url.data) > 0:
            return True

        # 2. Check Headline (secondary safety net)
        if headline:
            res_title = supabase.table("articles").select("id").eq("headline", headline.strip()).execute()
            if len(res_title.data) > 0:
                return True

        return False
    except Exception as e:
        print(f"[!] Supabase Select Error: {e}")
        return True

def save_article_draft(url: str, headline: str, draft: str, status: str = "published"):
    """Saves article record to Supabase using normalized URL."""
    if not supabase:
        return
    try:
        clean_url = url.strip().rstrip('/')
        supabase.table("articles").insert({
            "url": clean_url,
            "headline": headline.strip(),
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
