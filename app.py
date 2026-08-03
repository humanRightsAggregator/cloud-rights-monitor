import time
import feedparser
from fastapi import FastAPI
from config import RSS_FEEDS
from services.database import (
    supabase, check_article_exists, save_article_draft, get_recent_articles
)
from services.ai_engine import generate_ai_draft
from services.media_extractor import extract_article_image
from services.telegram import send_telegram_notification
from services.threads import post_to_threads
from services.facebook import post_to_facebook
from services.instagram import post_to_instagram

app = FastAPI()

@app.api_route("/", methods=["GET", "HEAD"])
def health_check():
    """Lightweight endpoint for wake-up calls (supports GET and HEAD)."""
    return {"status": "System Online", "service": "Global Human Rights Monitor"}

@app.api_route("/run-monitor", methods=["GET", "HEAD"])
def run_monitor():
    """Main execution pipeline."""
    if not supabase:
        return {"error": "Supabase client not initialized"}

    recent_topics = get_recent_articles(limit=15)
    processed_count = 0

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:2]:
                link = entry.get('link', '')
                title = entry.get('title', '')
                snippet = entry.get('summary', '') or entry.get('description', '')

                if not link or check_article_exists(link):
                    continue

                article_image = extract_article_image(entry, link)
                draft, _ = generate_ai_draft(title, snippet, link, recent_topics)

                if draft and draft != "SKIP":
                    threads_ok = post_to_threads(draft, article_image)
                    fb_ok = post_to_facebook(draft, link, article_image)
                    ig_ok = post_to_instagram(draft, article_image)

                    platform_results = {
                        "Threads": threads_ok,
                        "Facebook": fb_ok,
                        "Instagram": ig_ok
                    }

                    save_article_draft(link, title, draft, "published")
                    send_telegram_notification(draft, title, platform_results)

                    processed_count += 1
                    recent_topics.insert(0, {"headline": title, "draft_text": draft})

                time.sleep(4)
        except Exception as e:
            print(f"[!] Feed processing exception: {e}")

    return {"status": "Complete", "items_published": processed_count}
