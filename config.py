import os

# --- Supabase Database Credentials ---
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

# --- Google Gemini AI Credentials (Multi-Key Rotation) ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_API_KEY_2 = os.getenv("GEMINI_API_KEY_2", "").strip()

# --- Telegram Bot & Channel Credentials ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# --- Meta API (Instagram, Threads, Facebook) Credentials ---
# Supports both IG_USER_ID and INSTAGRAM_ACCOUNT_ID variable names
IG_USER_ID = (os.getenv("IG_USER_ID") or os.getenv("INSTAGRAM_ACCOUNT_ID", "")).strip()
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "").strip()

# Facebook Credentials
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "").strip()
FB_PAGE_ACCESS_TOKEN = (os.getenv("FB_PAGE_ACCESS_TOKEN") or META_ACCESS_TOKEN).strip()

# Threads Credentials (Auto-falls back to IG_USER_ID)
THREADS_USER_ID = (os.getenv("THREADS_USER_ID") or IG_USER_ID).strip()
THREADS_ACCESS_TOKEN = (os.getenv("THREADS_ACCESS_TOKEN") or META_ACCESS_TOKEN).strip()

# --- 11 Hybrid RSS Feeds Monitoring List ---
RSS_FEEDS = [
    # Major Human Rights Watchdogs
    "https://freedomhouse.org/rss.xml",
    "https://www.hrw.org/rss/news",
    "https://www.amnesty.org/en/feed/",
    
    # UN Bodies & International Organizations
    "https://news.un.org/feed/subscribe/en/news/topic/human-rights/feed/rss.xml",
    "https://www.ohchr.org/en/rss.xml",
    
    # Press Freedom & Civil Liberties Watchdogs
    "https://cpj.org/feed/",
    "https://rsf.org/en/rss.xml",
    
    # Targeted Google News Keyword Feeds
    "https://news.google.com/rss/search?q=%22Human+Rights%22+OR+%22Civil+Liberties%22&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=%22Political+Prisoners%22+OR+%22Press+Freedom%22&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=%22War+Crimes%22+OR+%22Crimes+Against+Humanity%22&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=%22Transnational+Repression%22+OR+%22Authoritarianism%22&hl=en-US&gl=US&ceid=US:en"
]
