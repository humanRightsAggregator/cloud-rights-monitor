import requests
import time
from config import THREADS_USER_ID, META_ACCESS_TOKEN

def post_to_threads(text: str) -> bool:
    """Publishes a text post to the Threads account using the official API."""
    if not THREADS_USER_ID or not META_ACCESS_TOKEN:
        print("[!] Threads credentials missing.")
        return False

    try:
        # Step 1: Create Container
        create_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"
        payload = {
            "text": text,
            "media_type": "TEXT",
            "access_token": META_ACCESS_TOKEN
        }
        res = requests.post(create_url, data=payload, timeout=15)
        data = res.json()

        container_id = data.get("id")
        if not container_id:
            print(f"[!] Threads Container Error: {data}")
            return False

        # DELAY: Give Meta's servers 5 seconds to process the text container
        time.sleep(5)

        # Step 2: Publish Container
        publish_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish"
        publish_payload = {
            "creation_id": container_id,
            "access_token": META_ACCESS_TOKEN
        }
        pub_res = requests.post(publish_url, data=publish_payload, timeout=15)
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
