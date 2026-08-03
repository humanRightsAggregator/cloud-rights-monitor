import os

# Cloud Environment Variables
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# Meta APIs (Fallback META_ACCESS_TOKEN to FB_PAGE_ACCESS_TOKEN if omitted)
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN", "")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN", FB_PAGE_ACCESS_TOKEN)
THREADS_USER_ID = os.environ.get("THREADS_USER_ID", "")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID", "")
INSTAGRAM_ACCOUNT_ID = os.environ.get("INSTAGRAM_ACCOUNT_ID", "")

# News Feed Sources
RSS_FEEDS = [
    "https://www.amnesty.org/en/rss/",
    "https://www.hrw.org/rss/news",
    "https://www.ohchr.org/en/rss.xml"
]
