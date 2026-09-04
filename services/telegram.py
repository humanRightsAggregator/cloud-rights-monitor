import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send_telegram_notification(draft_text: str, title: str, platform_results: dict):
    """Sends a notification for an individual published article."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    status_lines = []
    for platform, success in platform_results.items():
        icon = "✅" if success else "❌"
        status_lines.append(f"{icon} {platform}")
    
    status_text = "\n".join(status_lines)

    message = (
        f"📢 AUTO-PUBLISH SUMMARY\n\n"
        f"📌 Headline: {title}\n\n"
        f"📊 Platform Status:\n{status_text}\n\n"
        f"📝 Post Content:\n{draft_text}"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "disable_web_page_preview": True}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"[!] Telegram Post Notification Error: {e}")

def send_run_summary(published_count: int, errors: list):
    """Sends an end-of-run summary including success count and any system errors."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    if errors:
        # Show up to 10 errors to avoid hitting Telegram message length limits
        error_text = "\n".join([f"⚠️ {err}" for err in errors[:10]])
        if len(errors) > 10:
            error_text += f"\n...and {len(errors) - 10} more errors."
    else:
        error_text = "✅ No errors. System healthy."

    message = (
        f"⚙️ MONITOR RUN COMPLETE\n\n"
        f"📈 New Articles Published: {published_count}\n"
        f"🛠️ System Log:\n{error_text}"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"[!] Telegram Summary Error: {e}")
