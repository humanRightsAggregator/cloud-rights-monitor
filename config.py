import os

# --- Supabase Database Credentials ---
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# --- Google Gemini AI Credentials (Multi-Key Rotation) ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_API_KEY_2 = os.getenv("GEMINI_API_KEY_2", "")

# --- Telegram Bot & Channel Credentials ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# --- Meta API (Instagram, Threads, Facebook) Credentials ---
# Supports both IG_USER_ID and INSTAGRAM_ACCOUNT_ID variable names
IG_USER_ID = os.getenv("IG_USER_ID") or os.getenv("INSTAGRAM_ACCOUNT_ID", "")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "")

# Facebook Credentials
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "")
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN") or META_ACCESS_TOKEN

# Threads Credentials
THREADS_USER_ID = os.getenv("THREADS_USER_ID", "")
THREADS_ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN") or META_ACCESS_TOKEN

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
