from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

# Clean strings to strip out hidden linebreaks (\n) or trailing spaces from copy-pasting
CLEAN_URL = SUPABASE_URL.strip() if SUPABASE_URL else ""
CLEAN_KEY = SUPABASE_KEY.replace('\n', '').replace('\r', '').replace(' ', '').strip() if SUPABASE_KEY else ""

supabase: Client = None

# Print exact diagnostic details during server startup
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL.strip(), SUPABASE_KEY.strip())
        print("[+] Supabase client successfully initialized.")
    except Exception as e:
        print(f"[!] EXPLICIT SUPABASE INIT ERROR: {type(e).__name__} - {e}")
else:
    print(f"[!] Config Check -> URL Present: {bool(SUPABASE_URL)}, Key Present: {bool(SUPABASE_KEY)}")

if CLEAN_URL and CLEAN_KEY:
    try:
        supabase = create_client(CLEAN_URL, CLEAN_KEY)
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
