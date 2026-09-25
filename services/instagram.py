import time
import requests
from config import IG_USER_ID, META_ACCESS_TOKEN

def post_to_instagram(caption: str, image_url: str) -> bool:
    """Publishes an image post to Instagram Feed via Meta Graph API."""
    user_id = IG_USER_ID.strip() if IG_USER_ID else ""
    token = META_ACCESS_TOKEN.strip() if META_ACCESS_TOKEN else ""

    if not user_id or not token or not image_url:
        print(f"[!] IG Feed Skipped: Missing user_id ({bool(user_id)}), token ({bool(token)}), or image_url ({bool(image_url)})")
        return False

    try:
        # Step 1: Create Container
        container_url = f"https://graph.facebook.com/v19.0/{user_id}/media"
        payload = {
            "image_url": image_url,
            "caption": caption,
            "access_token": token
        }
        res = requests.post(container_url, data=payload, timeout=15)
        data = res.json()

        if "id" not in data:
            print(f"[!] IG Feed Container Error: {data}")
            return False

        creation_id = data["id"]
        time.sleep(5)  # Allow Meta processing time

        # Step 2: Publish Container
        publish_url = f"https://graph.facebook.com/v19.0/{user_id}/media_publish"
        pub_res = requests.post(publish_url, data={"creation_id": creation_id, "access_token": token}, timeout=15)
        pub_data = pub_res.json()

        if "id" in pub_data:
            print(f"[+] Published to Instagram Feed ID: {pub_data['id']}")
            return True
        else:
            print(f"[!] IG Feed Publish Error: {pub_data}")
            return False

    except Exception as e:
        print(f"[!] IG Feed Exception: {e}")
        return False

def post_story_to_instagram(image_url: str) -> bool:
    """Publishes an image story to Instagram via Meta Graph API."""
    user_id = IG_USER_ID.strip() if IG_USER_ID else ""
    token = META_ACCESS_TOKEN.strip() if META_ACCESS_TOKEN else ""

    if not user_id or not token or not image_url:
        print(f"[!] IG Story Skipped: Missing user_id ({bool(user_id)}), token ({bool(token)}), or image_url ({bool(image_url)})")
        return False

    try:
        # Step 1: Create Story Container
        container_url = f"https://graph.facebook.com/v19.0/{user_id}/media"
        payload = {
            "image_url": image_url,
            "media_type": "STORIES",
            "access_token": token
        }
        res = requests.post(container_url, data=payload, timeout=15)
        data = res.json()

        if "id" not in data:
            print(f"[!] IG Story Container Error: {data}")
            return False

        creation_id = data["id"]
        time.sleep(5)  # Allow Meta processing time

        # Step 2: Publish Container
        publish_url = f"https://graph.facebook.com/v19.0/{user_id}/media_publish"
        pub_res = requests.post(publish_url, data={"creation_id": creation_id, "access_token": token}, timeout=15)
        pub_data = pub_res.json()

        if "id" in pub_data:
            print(f"[+] Published to Instagram Story ID: {pub_data['id']}")
            return True
        else:
            print(f"[!] IG Story Publish Error: {pub_data}")
            return False

    except Exception as e:
        print(f"[!] IG Story Exception: {e}")
        return False
