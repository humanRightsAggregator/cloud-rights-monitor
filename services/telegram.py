import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send_telegram_draft(draft_text: str, article_id: int) -> tuple:
    """Delivers draft card to Telegram review channel with action buttons under the 64-byte limit."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": draft_text,
        "reply_markup": {
            "inline_keyboard": [[
                {"text": "✅ Approve & Post", "callback_data": f"approve|{article_id}"},
                {"text": "❌ Reject", "callback_data": f"reject|{article_id}"}
            ]]
        }
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.status_code == 200, {"status_code": res.status_code, "response": res.json() if res.status_code == 200 else res.text}
    except Exception as e:
        return False, {"error": str(e)}

def edit_telegram_message(chat_id: int, message_id: int, updated_text: str):
    """Updates Telegram card text when a user approves or rejects an item."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": updated_text
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"[!] Telegram Edit Error: {e}")
