import time
import html
import re
import feedparser
from urllib.parse import quote_plus
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import Response
from config import RSS_FEEDS
from services.database import check_article_exists, save_article_draft, get_recent_articles, supabase
from services.ai_engine import generate_ai_draft
from services.media_extractor import extract_article_image
from services.story_generator import create_story_card
from services.queue_manager import (
    process_and_queue_article, get_top_prioritized_queue, get_queue_status_metrics,
    rescore_discarded_or_pending_articles
)
from services.telegram import (
    send_telegram_notification, send_ingestion_summary, send_publishing_summary, send_telegram_message
)
from services.threads import post_to_threads
from services.facebook import post_to_facebook, post_story_to_facebook
from services.instagram import post_to_instagram, post_story_to_instagram

app = FastAPI()

DEFAULT_BRAND_IMAGE = "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?q=80&w=1080&auto=format&fit=crop"

def clean_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    clean_text = re.sub(r'<[^>]+>', ' ', raw_html)
    clean_text = html.unescape(clean_text)
    return re.sub(r'\s+', ' ', clean_text).strip()

def publish_single_article(article_data: dict, recent_topics: list) -> dict:
    title = article_data["title"]
    snippet = article_data["snippet"]
    link = article_data["url"]
    extracted_img = article_data.get("image_url")
    feed_image = extracted_img if extracted_img else DEFAULT_BRAND_IMAGE

    base_service_url = "https://cloud-rights-monitor.onrender.com"
    story_image_url = f"{base_service_url}/generate-story-card?title={quote_plus(title)}&img={quote_plus(feed_image)}"

    drafts, ai_err = generate_ai_draft(title, snippet, link, recent_topics)
    
    if drafts and isinstance(drafts, dict):
        threads_text = drafts.get("threads", "")
        fb_text = drafts.get("facebook", "")
        ig_text = drafts.get("instagram", "")

        save_article_draft(link, title, fb_text, "processing")

        threads_ok = post_to_threads(threads_text, extracted_img)
        fb_ok = post_to_facebook(fb_text, link, extracted_img)
        ig_ok = post_to_instagram(ig_text, feed_image)

        time.sleep(3)

        ig_story_ok = post_story_to_instagram(story_image_url)
        fb_story_ok = post_story_to_facebook(story_image_url)

        results = {
            "Threads": threads_ok,
            "Facebook": fb_ok,
            "Instagram": ig_ok,
            "IG Story": ig_story_ok,
            "FB Story": fb_story_ok
        }

        send_telegram_notification(fb_text, title, results)
        return results
    return {}

def ingest_feeds_task():
    print("[*] Starting feed ingestion and scoring run...")
    recent_topics = get_recent_articles(limit=15)
    run_errors = []
    
    stats = {
        "feeds_scanned": len(RSS_FEEDS),
        "evaluated_count": 0,
        "purged_count": 0,
        "queued_count": 0,
        "top_queued": [],
        "fast_tracked": [],
        "total_pending_queue": 0
    }

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:
                title = clean_html(entry.get('title', 'Unknown Title'))
                link = entry.get('link', '').strip()
                raw_snippet = entry.get('summary', '') or entry.get('description', '')
                snippet = clean_html(raw_snippet)

                if not link or check_article_exists(link, title):
                    continue

                stats["evaluated_count"] += 1
                article_image = extract_article_image(entry, link)
                res = process_and_queue_article(title, snippet, link, article_image, feed_url)

                if res["action"] == "discarded":
                    stats["purged_count"] += 1
                elif res["action"] == "queued":
                    stats["queued_count"] += 1
                    if res.get("data"):
                        stats["top_queued"].append(res["data"])
                elif res["action"] == "fast_tracked":
                    stats["fast_tracked"].append(title)
                    print(f"[!] Fast-Tracking Breaking News (Score {res['score']}): {title}")
                    publish_single_article(res["data"], recent_topics)
                    supabase.table("article_queue").update({"status": "published"}).eq("url", link).execute()
                elif res["action"] == "needs_rescore":
                    run_errors.append(f"AI Score Failed for '{title[:25]}': {res.get('error')}")

        except Exception as e:
            run_errors.append(f"Feed error for {feed_url}: {e}")

    total_pending, _ = get_queue_status_metrics()
    stats["total_pending_queue"] = total_pending
    stats["top_queued"].sort(key=lambda x: x.get("combined_score", 0), reverse=True)

    send_ingestion_summary(stats, run_errors)
    print(f"[+] Ingestion complete. Evaluated: {stats['evaluated_count']}")

def publish_queue_task():
    print("[*] Starting scheduled peak-window publication...")
    recent_topics = get_recent_articles(limit=15)
    batch = get_top_prioritized_queue(limit=2)
    run_errors = []
    published_items = []

    for article in batch:
        try:
            results = publish_single_article(article, recent_topics)
            if any(results.values()):
                supabase.table("article_queue").update({"status": "published"}).eq("id", article["id"]).execute()
                article["results"] = results
                published_items.append(article)
            else:
                run_errors.append(f"Failed to publish '{article['title'][:25]}'.")
            time.sleep(15)
        except Exception as e:
            run_errors.append(f"Error publishing '{article['title'][:25]}': {e}")

    remaining_count, next_up_title = get_queue_status_metrics()
    send_publishing_summary(published_items, remaining_count, next_up_title, run_errors)
    print(f"[+] Peak publishing complete. Published: {len(published_items)}")

def rescore_task():
    res = rescore_discarded_or_pending_articles()
    
    error_details = ""
    if res["errors"]:
        error_lines = "\n".join([f"• {e}" for e in res["errors"][:3]])
        error_details = f"\n\n⚠️ *Sample Errors:*\n{error_lines}"

    msg = (
        f"🔄 *RE-SCORE RECOVERY RUN COMPLETE*\n\n"
        f"• Articles Rescored: {res['rescored_total']}\n"
        f"• Rescued to Queue (>=5.5): {res['newly_queued']}\n"
        f"• Fast-Tracked (>=9.0): {res['fast_tracked']}\n"
        f"• Failed/Errors: {len(res['errors'])}{error_details}"
    )
    send_telegram_message(msg)

@app.get("/generate-story-card")
def generate_story_card_endpoint(title: str = "Human Rights Report", img: str = ""):
    img_buf = create_story_card(title, img)
    return Response(content=img_buf.getvalue(), media_type="image/jpeg")

@app.api_route("/", methods=["GET", "HEAD"])
def health_check():
    return {"status": "System Online", "service": "Global Human Rights Monitor Queue Engine"}

@app.api_route("/ingest-feeds", methods=["GET", "HEAD"])
def trigger_ingestion(background_tasks: BackgroundTasks):
    background_tasks.add_task(ingest_feeds_task)
    return {"status": "Accepted", "task": "Ingestion & Scoring"}

@app.api_route("/publish-queue", methods=["GET", "HEAD"])
def trigger_publishing(background_tasks: BackgroundTasks):
    background_tasks.add_task(publish_queue_task)
    return {"status": "Accepted", "task": "Peak Publishing"}

@app.api_route("/rescore-queue", methods=["GET", "HEAD"])
def trigger_rescore(background_tasks: BackgroundTasks):
    background_tasks.add_task(rescore_task)
    return {"status": "Accepted", "task": "Queue Rescore Recovery"}
