import time
import html
import re
import feedparser
from urllib.parse import quote_plus
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import Response
from config import RSS_FEEDS
from services.database import (
    supabase, check_article_exists, save_article_draft, get_recent_articles
)
from services.ai_engine import generate_ai_draft
from services.media_extractor import extract_article_image
from services.story_generator import create_story_card
from services.telegram import send_telegram_notification, send_run_summary
from services.threads import post_to_threads
from services.facebook import post_to_facebook, post_story_to_facebook
from services.instagram import post_to_instagram, post_story_to_instagram

app = FastAPI()

def clean_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    clean_text = re.sub(r'<[^>]+>', ' ', raw_html)
    clean_text = html.unescape(clean_text)
    return re.sub(r'\s+', ' ', clean_text).strip()

@app.get("/generate-story-card")
def generate_story_card_endpoint(title: str = "Human Rights Report", img: str = ""):
    """Dynamic route serving generated 9:16 graphic cards with burned headline text."""
    img_buf = create_story_card(title, img)
    return Response(content=img_buf.getvalue(), media_type="image/jpeg")

def process_feeds_task():
    """Background worker publishing feed posts and headline graphic stories."""
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
            for entry in feed.entries[:5]:
                title = clean_html(entry.get('title', 'Unknown Title'))
                try:
                    link = entry.get('link', '').strip()
                    raw_snippet = entry.get('summary', '') or entry.get('description', '')
                    snippet = clean_html(raw_snippet)

                    if not link or check_article_exists(link, title):
                        continue

                    article_image = extract_article_image(entry, link)
                    
                    # Generate graphic card URL with headline baked onto the image
                    story_image_url = None
                    if article_image:
                        base_service_url = "https://cloud-rights-monitor.onrender.com"
                        story_image_url = f"{base_service_url}/generate-story-card?title={quote_plus(title)}&img={quote_plus(article_image)}"

                    drafts, ai_err = generate_ai_draft(title, snippet, link, recent_topics)
                    
                    if ai_err:
                        run_errors.append(f"AI Warning for '{title[:25]}': {ai_err}")

                    if drafts and isinstance(drafts, dict):
                        threads_text = drafts.get("threads", "")
                        fb_text = drafts.get("facebook", "")
                        ig_text = drafts.get("instagram", "")

                        save_article_draft(link, title, fb_text, "processing")

                        # 1. Feed Posts
                        threads_ok = post_to_threads(threads_text, article_image)
                        fb_ok = post_to_facebook(fb_text, link, article_image)
                        ig_ok = post_to_instagram(ig_text, article_image)

                        time.sleep(3)

                        # 2. Graphic Story Posts (Instagram & Facebook)
                        ig_story_ok = post_story_to_instagram(story_image_url) if story_image_url else False
                        fb_story_ok = post_story_to_facebook(story_image_url) if story_image_url else False

                        platform_results = {
                            "Threads": threads_ok,
                            "Facebook": fb_ok,
                            "Instagram": ig_ok,
                            "IG Story": ig_story_ok,
                            "FB Story": fb_story_ok
                        }

                        if not all([threads_ok, fb_ok, ig_ok, ig_story_ok, fb_story_ok]):
                            run_errors.append(f"Partial publish fail for '{title[:25]}'.")

                        send_telegram_notification(fb_text, title, platform_results)

                        processed_count += 1
                        recent_topics.insert(0, {"headline": title, "draft_text": fb_text})

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
