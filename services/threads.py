import requests
import time
from config import THREADS_USER_ID, THREADS_ACCESS_TOKEN

def post_to_threads(caption: str, image_url: str = None) -> bool:
    """Publishes text or image post to Threads Graph API with strict 500-char truncation."""
    token = THREADS_ACCESS_TOKEN.strip() if THREADS_ACCESS_TOKEN else ""
    user_id = THREADS_USER_ID.strip() if THREADS_USER_ID else ""

    if not user_id or not token or not caption:
        print(f"[!] Threads Skipped. Missing required fields: user_id={bool(user_id)}, token={bool(token)}, caption={bool(caption)}")
        return False

    # Enforce strict 500-character limit for Threads API
    clean_caption = caption.strip()
    if len(clean_caption) > 490:
        clean_caption = clean_caption[:485].rstrip() + "..."

    headers = {"Authorization": f"Bearer {token}"}

    try:
        # Step 1: Create Container
        container_url = f"https://graph.threads.net/v1.0/{user_id}/threads"
        params = {
            "media_type": "IMAGE" if image_url else "TEXT",
            "text": clean_caption
        }
        if image_url:
            params["image_url"] = image_url

        res = requests.post(container_url, headers=headers, params=params, timeout=15)
        res_data = res.json()

        if "id" not in res_data:
            print(f"[!] Threads Container Error: {res_data}")
            return False

        creation_id = res_data["id"]
        time.sleep(5)  # Wait for container processing

        # Step 2: Publish Container
        publish_url = f"https://graph.threads.net/v1.0/{user_id}/threads_publish"
        pub_res = requests.post(publish_url, headers=headers, params={"creation_id": creation_id}, timeout=15)
        pub_data = pub_res.json()

        if "id" in pub_data:
            print(f"[+] Published to Threads Post ID: {pub_data['id']}")
            return True
        else:
            print(f"[!] Threads Publish Error: {pub_data}")
            return False

    except Exception as e:
        print(f"[!] Threads Exception: {e}")
        return False
