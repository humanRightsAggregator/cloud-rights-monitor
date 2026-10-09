def publish_single_article(article_data: dict, recent_topics: list) -> dict:
    title = article_data["title"]
    snippet = article_data["snippet"]
    link = article_data["url"]
    feed_image = article_data.get("image_url") or DEFAULT_BRAND_IMAGE

    mark_article_status(article_data, "processing")

    drafts, ai_err = generate_ai_draft(title, snippet, link, recent_topics)
    if not drafts or not isinstance(drafts, dict):
        mark_article_status(article_data, "failed_retry")
        return {}

    save_article_draft(link, title, drafts.get("threads", ""), "processing")

    # Strictly Threads + Instagram (No Facebook Page or Story)
    results = {"Threads": False, "Instagram": False}

    try:
        results["Threads"] = post_to_threads(
            drafts.get("threads", ""), 
            feed_image if feed_image != DEFAULT_BRAND_IMAGE else None
        )
    except Exception as e:
        print(f"[!] Threads exception: {e}")

    try:
        results["Instagram"] = post_to_instagram(
            drafts.get("instagram", ""), 
            feed_image
        )
    except Exception as e:
        print(f"[!] Instagram exception: {e}")

    if any(results.values()):
        mark_article_status(article_data, "published")
        send_telegram_notification(drafts.get("threads", ""), title, results)
    else:
        mark_article_status(article_data, "failed_retry")

    return results
