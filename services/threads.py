import requests
import time
from config import THREADS_USER_ID, THREADS_ACCESS_TOKEN

def post_to_threads(caption: str, image_url: str = None) -> bool:
    """Publishes text or image post to Threads Graph API with diagnostic logging."""
    if not THREADS_USER_ID or not THREADS_ACCESS_TOKEN:
        print(f"[!] Threads Skipped. Missing credentials: THREADS_USER_ID={bool(THREADS_USER_ID)}, THREADS_ACCESS_TOKEN={bool(THREADS_ACCESS_TOKEN)}")
        return False

    try:
        # Step 1: Create Container
        container_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"
        payload = {
            "media_type": "IMAGE" if image_url else "TEXT",
            "text": caption,
            "access_token": THREADS_ACCESS_TOKEN
        }
        if image_url:
            payload["image_url"] = image_url

        res = requests.post(container_url, data=payload, timeout=15)
        res_data = res.json()

        if "id" not in res_data:
            print(f"[!] Threads Container Error: {res_data}")
            return False

        creation_id = res_data["id"]
        time.sleep(5)  # Wait for processing

        # Step 2: Publish Container
        publish_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish"
        pub_res = requests.post(publish_url, data={"creation_id": creation_id, "access_token": THREADS_ACCESS_TOKEN}, timeout=15)
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
