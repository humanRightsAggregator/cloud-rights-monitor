import requests
import time
from config import THREADS_USER_ID, META_ACCESS_TOKEN

def post_to_threads(text: str, image_url: str = None) -> bool:
    """Publishes a post to Threads, enforcing the 500-character limit."""
    if not THREADS_USER_ID or not META_ACCESS_TOKEN:
        print("[!] Threads credentials missing.")
        return False

    # Enforce strict 500-character Threads limit
    if len(text) > 495:
        text = text[:490].rsplit(' ', 1)[0] + "..."

    try:
        create_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"
        payload = {
            "text": text,
            "access_token": META_ACCESS_TOKEN
        }

        if image_url:
            payload["media_type"] = "IMAGE"
            payload["image_url"] = image_url
        else:
            payload["media_type"] = "TEXT"

        res = requests.post(create_url, data=payload, timeout=15)
        data = res.json()

        container_id = data.get("id")
        if not container_id:
            print(f"[!] Threads Container Error: {data}")
            return False

        time.sleep(5)

        publish_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish"
        pub_payload = {
            "creation_id": container_id,
            "access_token": META_ACCESS_TOKEN
        }
        pub_res = requests.post(publish_url, data=pub_payload, timeout=15)
        pub_data = pub_res.json()

        if "id" in pub_data:
            print(f"[+] Published to Threads: {pub_data['id']}")
            return True
        else:
            print(f"[!] Threads Publish Error: {pub_data}")
            return False

    except Exception as e:
        print(f"[!] Threads API Exception: {e}")
        return False
