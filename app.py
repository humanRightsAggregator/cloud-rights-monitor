import os
import requests
import feedparser
from fastapi import FastAPI, Request
from supabase import create_client, Client

app = FastAPI()

# Cloud Environment Variables
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN", "")
THREADS_USER_ID = os.environ.get("THREADS_USER_ID", "")

# Safe Supabase DB Client Initialization
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"[!] Supabase Init Error: {e}")

RSS_FEEDS = [
    "https://www.amnesty.org/en/rss/",
    "https://www.hrw.org/rss/news",
    "https://www.ohchr.org/en/rss.xml"
]

def generate_ai_draft(title, snippet, link):
    prompt = f"""You are an objective, non-partisan human rights archivist. Analyze this news item:
Title: {title}
Snippet: {snippet}

Task:
1. If this details credible conflict events, unlawful actions, or human rights violations, create a neutral 2-sentence summary (Who, What, Where, When). Avoid emotional language.
2. Format strictly as:
[CW: Human Rights Report]
<2-sentence factual summary>

Source: {link}

3. If irrelevant, an opinion piece, or meta-announcement, reply with ONLY: SKIP
"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15)
        if res.status_code != 200:
            print(f"[!] Gemini HTTP Error {res.status_code}: {res.text}")
            return "SKIP"
            
        data = res.json()
        if "candidates" in data and len(data["candidates"]) > 0:
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"[!] Gemini Exception: {e}")
    return "SKIP"

def send_telegram_draft(draft_text, article_url):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": draft_text,
        "reply_markup": {
            "inline_keyboard": [[
                {"text": "✅ Approve & Post", "callback_data": f"approve|{article_url}"},
                {"text": "❌ Reject", "callback_data": f"reject|{article_url}"}
            ]]
        }
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"[!] Telegram Send Error: {e}")

def post_to_threads(text):
    """Publishes text posts to Meta Threads via Graph API."""
    try:
        container_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"
        c_payload = {"media_type": "TEXT", "text": text[:500], "access_token": META_ACCESS_TOKEN}
        c_res = requests.post(container_url, data=c_payload, timeout=15).json()
        container_id = c_res.get("id")

        if not container_id:
            print(f"[!] Container Creation Failed: {c_res}")
            return False

        publish_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish"
        p_res = requests.post(publish_url, data={"creation_id": container_id, "access_token": META_ACCESS_TOKEN}, timeout=15).json()
        return "id" in p_res
    except Exception as e:
        print(f"[!] Threads Publishing Error: {e}")
        return False

# ================= ENDPOINTS =================

@app.get("/")
def health_check():
    return {"status": "System Online", "service": "Global Human Rights Monitor"}

@app.get("/run-monitor")
def run_monitor():
    """Triggered by Cron-Job.org."""
    if not supabase:
        return {"error": "Supabase client not initialized"}

    processed_count = 0
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:
                link = entry.get('link', '')
                title = entry.get('title', '')
                snippet = entry.get('summary', '') or entry.get('description', '')

                # Check database for duplicates
                existing = supabase.table("processed_articles").select("url").eq("url", link).execute()
                if len(existing.data) > 0:
                    continue

                draft = generate_ai_draft(title, snippet, link)
                if draft != "SKIP" and not draft.startswith("SKIP"):
                    # Save pending draft to DB
                    supabase.table("processed_articles").insert({
                        "url": link, "headline": title, "draft_text": draft, "status": "pending"
                    }).execute()
                    
                    # Push draft to mobile approval queue
                    send_telegram_draft(draft, link)
                    processed_count += 1
        except Exception as e:
            print(f"[!] Feed processing error for {feed_url}: {e}")

    return {"status": "Complete", "items_queued": processed_count}

@app.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    """Handles button presses from Telegram."""
    data = await request.json()
    if "callback_query" in data:
        callback = data["callback_query"]
        action, article_url = callback["data"].split("|")
        chat_id = callback["message"]["chat"]["id"]
        message_id = callback["message"]["message_id"]

        if action == "approve":
            record = supabase.table("processed_articles").select("draft_text").eq("url", article_url).execute()
            if len(record.data) > 0:
                draft_text = record.data[0]["draft_text"]
                if post_to_threads(draft_text):
                    supabase.table("processed_articles").update({"status": "published"}).eq("url", article_url).execute()
                    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText", json={
                        "chat_id": chat_id, "message_id": message_id, "text": f"✅ PUBLISHED TO THREADS:\n\n{draft_text}"
                    })
        elif action == "reject":
            supabase.table("processed_articles").update({"status": "rejected"}).eq("url", article_url).execute()
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText", json={
                "chat_id": chat_id, "message_id": message_id, "text": "❌ DISCARDED"
            })

    return {"status": "ok"}
