import time
import feedparser
from fastapi import FastAPI, Request
from config import RSS_FEEDS
from services.database import (
    supabase, check_article_exists, save_article_draft,
    get_draft_by_id, update_article_status, get_recent_articles
)
from services.ai_engine import generate_ai_draft
from services.telegram import send_telegram_draft, edit_telegram_message
from services.threads import post_to_threads

app = FastAPI()

@app.get("/")
def health_check():
    return {"status": "System Online", "service": "Global Human Rights Monitor"}

@app.get("/trigger-sample")
def trigger_sample():
    feed = feedparser.parse(RSS_FEEDS[0])
    if not feed.entries:
        return {"error": "Could not fetch RSS feed"}
        
    entry = feed.entries[0]
    link = entry.get('link', 'https://example.com/test-article')
    title = entry.get('title', 'Human Rights Event Report')
    snippet = entry.get('summary', '') or entry.get('description', '') or title

    recent_topics = get_recent_articles(limit=15)
    draft, gemini_debug = generate_ai_draft(title, snippet, link, recent_topics)
    
    if draft and draft != "SKIP":
        article_id = save_article_draft(link, title, draft, "pending")
        sent, tg_debug = send_telegram_draft(draft, article_id)
        return {
            "status": "Success" if sent else "Telegram Error",
            "telegram_sent": sent,
            "headline": title,
            "clean_draft": draft,
            "telegram_debug": tg_debug,
            "gemini_info": gemini_debug
        }
    
    return {
        "status": "Skipped or Failed",
        "result": draft if draft == "SKIP" else "AI Evaluation Failed",
        "gemini_debug": gemini_debug
    }

@app.get("/run-monitor")
def run_monitor():
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

                draft, _ = generate_ai_draft(title, snippet, link, recent_topics)
                if draft and draft != "SKIP":
                    article_id = save_article_draft(link, title, draft, "pending")
                    send_telegram_draft(draft, article_id)
                    processed_count += 1
                    # Append new draft locally so subsequent feed items in same run don't duplicate it
                    recent_topics.insert(0, {"headline": title, "draft_text": draft})
                
                time.sleep(4)
        except Exception as e:
            print(f"[!] Feed processing error: {e}")

    return {"status": "Complete", "items_queued": processed_count}

@app.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    if "callback_query" in data:
        callback = data["callback_query"]
        action, article_id = callback["data"].split("|")
        chat_id = callback["message"]["chat"]["id"]
        message_id = callback["message"]["message_id"]

        if action == "approve":
            draft_text = get_draft_by_id(article_id)
            if draft_text and post_to_threads(draft_text):
                update_article_status(article_id, "published")
                edit_telegram_message(chat_id, message_id, f"✅ PUBLISHED TO THREADS:\n\n{draft_text}")
        elif action == "reject":
            update_article_status(article_id, "rejected")
            edit_telegram_message(chat_id, message_id, "❌ DISCARDED")

    return {"status": "ok"}
