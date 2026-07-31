import os
import time
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

# Initialize Supabase Client
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

def get_available_gemini_model():
    """Queries Google AI Studio to find a model supported by your API key."""
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    try:
        res = requests.get(list_url, timeout=10)
        if res.status_code == 200:
            models = res.json().get("models", [])
            # Prioritize fast/flash models that support generateContent
            for m in models:
                name = m.get("name", "").replace("models/", "")
                methods = m.get("supportedGenerationMethods", [])
                if "generateContent" in methods and "flash" in name.lower():
                    return name
            # Fallback to any model that supports generateContent
            for m in models:
                name = m.get("name", "").replace("models/", "")
                methods = m.get("supportedGenerationMethods", [])
                if "generateContent" in methods:
                    return name
    except Exception as e:
        print(f"[!] Dynamic Model Lookup Error: {e}")
    return "gemini-1.5-flash"  # Default fallback

def generate_ai_draft_debug(title, snippet, link):
    model_name = get_available_gemini_model()
    
    prompt = f"""You are an objective human rights archivist. Analyze this item:
Title: {title}
Snippet: {snippet}

Task:
1. Write a neutral 2-sentence summary (Who, What, Where, When). Avoid emotional language.
2. Format strictly as:
[CW: Human Rights Report]
<2-sentence factual summary>

Source: {link}
"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
    
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15)
        
        if res.status_code == 200:
            data = res.json()
            if "candidates" in data and len(data["candidates"]) > 0:
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                return text, {"status_code": 200, "active_model": model_name}
            return None, {"status_code": 200, "active_model": model_name, "message": "No candidates returned", "raw": res.text}
        else:
            return None, {"status_code": res.status_code, "active_model": model_name, "error_body": res.text}
            
    except Exception as e:
        return None, {"status_code": "exception", "active_model": model_name, "error_message": str(e)}

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
        res = requests.post(url, json=payload, timeout=10)
        return res.status_code == 200
    except Exception as e:
        print(f"[!] Telegram Error: {e}")
        return False

def post_to_threads(text):
    try:
        container_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"
        c_payload = {"media_type": "TEXT", "text": text[:500], "access_token": META_ACCESS_TOKEN}
        c_res = requests.post(container_url, data=c_payload, timeout=15).json()
        container_id = c_res.get("id")

        if not container_id:
            return False

        publish_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish"
        p_res = requests.post(publish_url, data={"creation_id": container_id, "access_token": META_ACCESS_TOKEN}, timeout=15).json()
        return "id" in p_res
    except Exception as e:
        return False

# ================= ENDPOINTS =================

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

    draft, debug_info = generate_ai_draft_debug(title, snippet, link)
    if draft:
        if supabase:
            supabase.table("processed_articles").upsert({
                "url": link, "headline": title, "draft_text": draft, "status": "pending"
            }).execute()
        
        sent = send_telegram_draft(draft, link)
        return {"status": "Success", "telegram_sent": sent, "headline": title, "draft": draft, "gemini_info": debug_info}
    
    return {
        "status": "Failed",
        "reason": "Gemini API did not return a summary",
        "gemini_debug": debug_info
    }

@app.get("/run-monitor")
def run_monitor():
    if not supabase:
        return {"error": "Supabase client not initialized"}

    processed_count = 0
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:2]:
                link = entry.get('link', '')
                title = entry.get('title', '')
                snippet = entry.get('summary', '') or entry.get('description', '')

                if not link:
                    continue

                existing = supabase.table("processed_articles").select("url").eq("url", link).execute()
                if len(existing.data) > 0:
                    continue

                draft, _ = generate_ai_draft_debug(title, snippet, link)
                if draft:
                    supabase.table("processed_articles").insert({
                        "url": link, "headline": title, "draft_text": draft, "status": "pending"
                    }).execute()
                    
                    send_telegram_draft(draft, link)
                    processed_count += 1
                
                time.sleep(4)
        except Exception as e:
            print(f"[!] Feed error: {e}")

    return {"status": "Complete", "items_queued": processed_count}

@app.post("/telegram-webhook")
async def telegram_webhook(request: Request):
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
