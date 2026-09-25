import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send_telegram_message(text: str) -> bool:
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
    errors_text = "\n".join([f"• {e}" for e in run_errors]) if run_errors else "• No errors. All systems optimal."
    
    # Format Queued Items
    top_queued = stats.get("top_queued", [])
    queued_lines = []
    for idx, item in enumerate(top_queued[:3], 1):
        queued_lines.append(f"{idx}. \"{item.get('title', 'Untitled')[:45]}...\"\n   └ 💡 Imp: {item.get('importance_score', 0)} | ⭐ Score: {item.get('combined_score', 0)}")
    queued_str = "\n".join(queued_lines) if queued_lines else "• No new prime items added to queue."

    # Format Fast-Tracked
    fast_tracked = stats.get("fast_tracked", [])
    ft_lines = [f"• \"{title[:45]}...\"" for title in fast_tracked]
    ft_str = "\n".join(ft_lines) if ft_lines else "• None"

    # Format Low-Tier Drip
    low_tier = stats.get("low_tier_items", [])
    lt_lines = [f"• \"{item.get('title', '')[:45]}...\"" for item in low_tier]
    lt_str = "\n".join(lt_lines) if lt_lines else "• None"

    message = (
        f"📥 *FEED INGESTION & QUEUE REPORT*\n\n"
        f"📊 *Summary (4-Tier Routing):*\n"
        f"• Evaluated: {stats.get('evaluated_count', 0)}\n"
        f"• Purged (<5.5): {stats.get('purged_count', 0)}\n"
        f"• Expired (>48h): {stats.get('expired_count', 0)}\n"
        f"• Low-Tier Drip (5.5-6.7): {stats.get('low_tier_count', 0)}\n"
        f"• Prime Queued (6.8-8.4): {stats.get('queued_count', 0)}\n"
        f"• Fast-Tracked (>=8.5): {len(fast_tracked)}\n\n"
        f"📥 *Newly Queued Prime Articles:*\n{queued_str}\n\n"
        f"⚡ *Fast-Tracked (Published Instantly):*\n{ft_str}\n\n"
        f"🕒 *Low-Tier (Drip-Publishing in Background):*\n{lt_str}\n\n"
        f"📦 *Queue Status:*\n"
        f"• Total Pending Prime Articles: {stats.get('total_pending_queue', 0)}\n\n"
        f"⚠️ *Diagnostics Log:*\n{errors_text}"
    )
    return send_telegram_message(message)

def send_publishing_summary(published_items: list, remaining_queue_count: int, next_up_title: str, run_errors: list = None) -> bool:
    errors_text = "\n".join([f"• {e}" for e in run_errors]) if run_errors else "• No errors reported."
    pub_lines = []
    for item in published_items:
        title = item.get("title", "Untitled")[:40]
        res_str = " | ".join([f"{k}: {'✅' if v else '❌'}" for k, v in item.get("results", {}).items()])
        pub_lines.append(f"• \"{title}...\"\n   └ Score: {item.get('combined_score', 0)}\n   └ {res_str}")

    message = (
        f"🚀 *PEAK PUBLISHING SLOT COMPLETE*\n\n"
        f"✅ *Articles Published ({len(published_items)}):*\n"
        f"{chr(10).join(pub_lines) if pub_lines else '• No queued articles were due.'}\n\n"
        f"📊 *Queue Status Remaining:*\n"
        f"• Items Still in Queue: {remaining_queue_count}\n"
        f"• Next Up: {next_up_title[:45] if next_up_title else 'Queue empty'}\n\n"
        f"⚠️ *Diagnostics Log:*\n{errors_text}"
    )
    return send_telegram_message(message)
