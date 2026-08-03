import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send_telegram_notification(draft_text: str, headline: str, results: dict) -> bool:
    """Sends a detailed post-publication acknowledgment notification to Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[!] Telegram credentials missing.")
        return False

    status_lines = []
    for platform, success in results.items():
        icon = "✅" if success else "❌"
        status_lines.append(f"{icon} *{platform}*")
    
    status_summary = "\n".join(status_lines)

    message_text = (
        f"📢 *AUTO-PUBLISH SUMMARY*\n\n"
        f"📌 *Headline:* {headline}\n\n"
        f"📊 *Platform Status:*\n{status_summary}\n\n"
        f"📝 *Post Content:*\n{draft_text}"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message_text,
        "parse_mode": "Markdown"
    }

    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.status_code == 200
    except Exception as e:
        print(f"[!] Telegram notification error: {e}")
        return False
