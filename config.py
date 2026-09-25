import os

# Environment Variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

FB_PAGE_ID = os.getenv("FB_PAGE_ID", "")
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN", "")

IG_USER_ID = os.getenv("IG_USER_ID", "")
THREADS_USER_ID = os.getenv("THREADS_USER_ID", "")

# Expanded Hybrid RSS Feed Strategy (Watchdogs + UN/Crisis + Trending Search)
RSS_FEEDS = [
    # Core Watchdogs (High Importance)
    "https://www.amnesty.org/en/rss/",
    "https://www.hrw.org/rss/news",
    "https://cpj.org/feed/",
    "https://rsf.org/en/rss.xml",
    "https://freedomhouse.org/rss.xml",
    "https://www.crisisgroup.org/rss",
    "https://ipi.media/feed/",

    # UN & Crisis Journalism (Authority & Emergencies)
    "https://news.un.org/feed/subscribe/en/news/topic/human-rights/feed/rss.xml",
    "https://www.thenewhumanitarian.org/rss.xml",

    # Dynamic Google News Keywords (Popularity & Reach Boost)
    "https://news.google.com/rss/search?q=%22Human+Rights%22+OR+%22Civil+Liberties%22&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=%22Political+Prisoners%22+OR+%22Press+Freedom%22&hl=en-US&gl=US&ceid=US:en"
]
