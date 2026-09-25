import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send_telegram_message(text: str) -> bool:
    """Generic helper to send Telegram messages with disabled link previews."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[!] Telegram credentials missing.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        res = requests.post(url, data=payload, timeout=10)
        return res.status_code == 200
    except Exception as e:
        print(f"[!] Telegram Exception: {e}")
        return False

def send_telegram_notification(caption: str, title: str, platform_results: dict) -> bool:
    """Individual post notification summary."""
    status_lines = []
    for platform, ok in platform_results.items():
        icon = "✅" if ok else "❌"
        status_lines.append(f"{icon} {platform}")
    
    status_text = "\n".join(status_lines)
    
    message = (
        f"📣 *AUTO-PUBLISH SUMMARY*\n\n"
        f"📌 *Headline:* {title}\n\n"
        f"📊 *Platform Status:*\n{status_text}\n\n"
        f"📝 *Post Preview:*\n{caption[:250]}..."
    )
    return send_telegram_message(message)

def send_ingestion_summary(stats: dict, run_errors: list = None) -> bool:
    """Rich report generated after Stage 1 Feed Ingestion & Scoring."""
    errors_text = "\n".join([f"• {e}" for e in run_errors]) if run_errors else "• No errors. All systems optimal."
    
    top_queued = stats.get("top_queued", [])
    queued_lines = []
    for idx, item in enumerate(top_queued[:3], 1):
        title = item.get("title", "Untitled")[:45]
        imp = item.get("importance_score", 0.0)
        pop = item.get("popularity_score", 0.0)
        score = item.get("combined_score", 0.0)
        queued_lines.append(f"{idx}. \"{title}...\"\n   └ 💡 Imp: {imp} | 🔥 Pop: {pop} | ⭐ Score: {score}")

    queued_str = "\n".join(queued_lines) if queued_lines else "• No new items added to queue."

    fast_tracked = stats.get("fast_tracked", [])
    ft_lines = [f"• \"{title[:45]}...\"" for title in fast_tracked]
    ft_str = "\n".join(ft_lines) if ft_lines else "• None"

    message = (
        f"📥 *FEED INGESTION & QUEUE REPORT*\n\n"
        f"📊 *Summary:*\n"
        f"• Feeds Processed: {stats.get('feeds_scanned', 0)}\n"
        f"• Articles Evaluated: {stats.get('evaluated_count', 0)}\n"
        f"• Auto-Purged (<5.5): {stats.get('purged_count', 0)}\n"
        f"• Added to Queue (5.5-8.9): {stats.get('queued_count', 0)}\n"
        f"• Fast-Tracked (>=9.0): {len(fast_tracked)}\n\n"
        f"📥 *Newly Queued Top Articles:*\n{queued_str}\n\n"
        f"⚡ *Fast-Tracked (Published Immediately):*\n{ft_str}\n\n"
        f"📦 *Queue Status:*\n"
        f"• Total Pending Articles in Queue: {stats.get('total_pending_queue', 0)}\n\n"
        f"⚠️ *Diagnostics Log:*\n{errors_text}"
    )
    return send_telegram_message(message)

def send_publishing_summary(published_items: list, remaining_queue_count: int, next_up_title: str, run_errors: list = None) -> bool:
    """Rich report generated after Stage 2 Peak Publishing Slot."""
    errors_text = "\n".join([f"• {e}" for e in run_errors]) if run_errors else "• No errors reported."
    
    pub_lines = []
    for item in published_items:
        title = item.get("title", "Untitled")[:40]
        score = item.get("combined_score", 0.0)
        results = item.get("results", {})
        res_str = " | ".join([f"{k}: {'✅' if v else '❌'}" for k, v in results.items()])
        pub_lines.append(f"• \"{title}...\"\n   └ Score: {score}\n   └ {res_str}")

    published_str = "\n".join(pub_lines) if pub_lines else "• No queued articles were due for publication."
    next_up_str = f"\"{next_up_title[:45]}...\"" if next_up_title else "Queue empty"

    message = (
        f"🚀 *PEAK PUBLISHING SLOT COMPLETE*\n\n"
        f"✅ *Articles Published ({len(published_items)}):*\n{published_str}\n\n"
        f"📊 *Queue Status Remaining:*\n"
        f"• Items Still in Queue: {remaining_queue_count}\n"
        f"• Next Up: {next_up_str}\n\n"
        f"⚠️ *Diagnostics Log:*\n{errors_text}"
    )
    return send_telegram_message(message)
