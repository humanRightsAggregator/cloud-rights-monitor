import os

# API Credentials
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Threads Credentials
THREADS_USER_ID = os.getenv("THREADS_USER_ID")
THREADS_ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN") or os.getenv("THREADS_ACCESS_TOKEN")

# Facebook Credentials
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")

# Instagram Credentials (aliases both variable names)
IG_USER_ID = os.getenv("IG_USER_ID") or os.getenv("INSTAGRAM_ACCOUNT_ID")
INSTAGRAM_ACCOUNT_ID = IG_USER_ID

# Master List of Global Human Rights RSS Feeds
RSS_FEEDS = [
    # Global Watchdogs
    "https://www.amnesty.org/en/rss/",
    "https://www.hrw.org/rss/news",
    # UN Agencies
    "https://www.ohchr.org/en/rss.xml",
    "https://www.unhcr.org/news/rss.xml",
    # Press Freedom
    "https://cpj.org/feed/",
    "https://rsf.org/en/rss.xml",
    # Crisis & Humanitarian
    "https://www.crisisgroup.org/rss",
    "https://reliefweb.int/updates/rss.xml",
    # Corporate & Environmental Rights
    "https://www.globalwitness.org/en/rss.xml"
]
