import time
import feedparser
from fastapi import FastAPI, BackgroundTasks
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

def process_feeds_task():
    """Background worker processing RSS feeds and handling multi-platform posting."""
    print("[*] Starting background feed monitor run...")
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
                drafts, err = generate_ai_draft(title, snippet, link, recent_topics)

                if drafts and isinstance(drafts, dict):
                    threads_text = drafts.get("threads", "")
                    long_text = drafts.get("long", "")

                    threads_ok = post_to_threads(threads_text, article_image)
                    fb_ok = post_to_facebook(long_text, link, article_image)
                    ig_ok = post_to_instagram(long_text, article_image)

                    platform_results = {
                        "Threads": threads_ok,
                        "Facebook": fb_ok,
                        "Instagram": ig_ok
                    }

                    save_article_draft(link, title, long_text, "published")
                    send_telegram_notification(long_text, title, platform_results)

                    processed_count += 1
                    recent_topics.insert(0, {"headline": title, "draft_text": long_text})

                # 15-second delay between items to avoid Meta anti-spam rate limits
                time.sleep(15)
        except Exception as e:
            print(f"[!] Feed processing exception: {e}")

    print(f"[+] Background monitor run complete. Items published: {processed_count}")

@app.api_route("/", methods=["GET", "HEAD"])
def health_check():
    """Lightweight health check endpoint for uptime monitoring."""
    return {"status": "System Online", "service": "Global Human Rights Monitor"}

@app.api_route("/run-monitor", methods=["GET", "HEAD"])
def run_monitor(background_tasks: BackgroundTasks):
    """Responds immediately to avoid HTTP timeouts, delegating processing to a background task."""
    background_tasks.add_task(process_feeds_task)
    return {
        "status": "Accepted",
        "message": "Monitor task launched in background",
        "timestamp": time.time()
    }
