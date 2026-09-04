import time
import html
import re
import feedparser
from fastapi import FastAPI, BackgroundTasks
from config import RSS_FEEDS
from services.database import (
    supabase, check_article_exists, save_article_draft, get_recent_articles
)
from services.ai_engine import generate_ai_draft
from services.media_extractor import extract_article_image
from services.telegram import send_telegram_notification, send_run_summary
from services.threads import post_to_threads
from services.facebook import post_to_facebook
from services.instagram import post_to_instagram

app = FastAPI()

def clean_html(raw_html: str) -> str:
    """Strips HTML tags (<p>, <em>) and decodes HTML entities (&nbsp;, &amp;)."""
    if not raw_html:
        return ""
    # Remove HTML tags
    clean_text = re.sub(r'<[^>]+>', ' ', raw_html)
    # Decode HTML entities
    clean_text = html.unescape(clean_text)
    # Collapse multiple whitespaces
    return re.sub(r'\s+', ' ', clean_text).strip()

def process_feeds_task():
    """Background worker processing RSS feeds with HTML sanitization and strict deduplication."""
    print("[*] Starting background feed monitor run...")
    run_errors = []
    processed_count = 0
    
    try:
        recent_topics = get_recent_articles(limit=15)
    except Exception as e:
        run_errors.append(f"Database Fetch Error: {e}")
        recent_topics = []

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:2]:
                title = clean_html(entry.get('title', 'Unknown Title'))
                try:
                    link = entry.get('link', '').strip()
                    raw_snippet = entry.get('summary', '') or entry.get('description', '')
                    snippet = clean_html(raw_snippet)

                    # Deduplication check
                    if not link or check_article_exists(link, title):
                        continue

                    article_image = extract_article_image(entry, link)
                    drafts, ai_err = generate_ai_draft(title, snippet, link, recent_topics)
                    
                    if ai_err:
                        run_errors.append(f"AI Generation Warning for '{title[:25]}': {ai_err}")

                    if drafts and isinstance(drafts, dict):
                        threads_text = drafts.get("threads", "")
                        fb_text = drafts.get("facebook", "")
                        ig_text = drafts.get("instagram", "")

                        # Claim entry in database immediately before posting
                        save_article_draft(link, title, fb_text, "processing")

                        # Post across social channels
                        threads_ok = post_to_threads(threads_text, article_image)
                        fb_ok = post_to_facebook(fb_text, link, article_image)
                        ig_ok = post_to_instagram(ig_text, article_image)

                        platform_results = {
                            "Threads": threads_ok,
                            "Facebook": fb_ok,
                            "Instagram": ig_ok
                        }

                        if not all([threads_ok, fb_ok, ig_ok]):
                            run_errors.append(f"Partial publish failure for '{title[:25]}'.")

                        send_telegram_notification(fb_text, title, platform_results)

                        processed_count += 1
                        recent_topics.insert(0, {"headline": title, "draft_text": fb_text})

                    # Rate-limit delay
                    time.sleep(15)
                except Exception as e:
                    run_errors.append(f"Error processing '{title[:25]}': {e}")
        except Exception as e:
            run_errors.append(f"Feed error for ({feed_url}): {e}")

    send_run_summary(processed_count, run_errors)
    print(f"[+] Background monitor run complete. Items published: {processed_count}")

@app.api_route("/", methods=["GET", "HEAD"])
def health_check():
    return {"status": "System Online", "service": "Global Human Rights Monitor"}

@app.api_route("/run-monitor", methods=["GET", "HEAD"])
def run_monitor(background_tasks: BackgroundTasks):
    background_tasks.add_task(process_feeds_task)
    return {
        "status": "Accepted",
        "message": "Monitor task launched in background",
        "timestamp": time.time()
    }
