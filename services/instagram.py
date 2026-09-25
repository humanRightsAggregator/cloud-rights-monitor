import requests
import time
from config import IG_USER_ID, META_ACCESS_TOKEN

DEFAULT_BRAND_IMAGE = "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?q=80&w=1080&auto=format&fit=crop"

def post_to_instagram(caption: str, image_url: str) -> bool:
    """Publishes a photo post to Instagram Feed with explicit missing-variable diagnostics."""
    final_image = image_url if (image_url and image_url.strip()) else DEFAULT_BRAND_IMAGE

    # Explicit diagnostic check
    missing = []
    if not IG_USER_ID: missing.append("IG_USER_ID")
    if not META_ACCESS_TOKEN: missing.append("META_ACCESS_TOKEN")
    if not final_image: missing.append("image_url")

    if missing:
        print(f"[!] Instagram Feed Skipped. Missing required fields: {', '.join(missing)}")
        return False

    try:
        # Step 1: Create Container
        container_url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media"
        payload = {
            "image_url": final_image,
            "caption": caption,
            "access_token": META_ACCESS_TOKEN
        }
        res = requests.post(container_url, data=payload, timeout=15)
        res_data = res.json()

        if "id" not in res_data:
            print(f"[!] Instagram Container Error: {res_data}")
            return False

        creation_id = res_data["id"]
        time.sleep(5)  # Wait for Meta image processing

        # Step 2: Publish Container
        publish_url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish"
        pub_payload = {
            "creation_id": creation_id,
            "access_token": META_ACCESS_TOKEN
        }
        pub_res = requests.post(publish_url, data=pub_payload, timeout=15)
        pub_data = pub_res.json()

        if "id" in pub_data:
            print(f"[+] Published to Instagram Feed ID: {pub_data['id']}")
            return True
        else:
            print(f"[!] Instagram Publish Error: {pub_data}")
            return False

    except Exception as e:
        print(f"[!] Instagram Feed Exception: {e}")
        return False

def post_story_to_instagram(story_image_url: str) -> bool:
    """Publishes a 9:16 story card to Instagram Stories."""
    missing = []
    if not IG_USER_ID: missing.append("IG_USER_ID")
    if not META_ACCESS_TOKEN: missing.append("META_ACCESS_TOKEN")
    if not story_image_url: missing.append("story_image_url")

    if missing:
        print(f"[!] Instagram Story Skipped. Missing required fields: {', '.join(missing)}")
        return False

    try:
        container_url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media"
        payload = {
            "image_url": story_image_url,
            "media_type": "STORIES",
            "access_token": META_ACCESS_TOKEN
        }
        res = requests.post(container_url, data=payload, timeout=15)
        res_data = res.json()

        if "id" not in res_data:
            print(f"[!] Instagram Story Container Error: {res_data}")
            return False

        creation_id = res_data["id"]
        time.sleep(5)

        publish_url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish"
        pub_res = requests.post(publish_url, data={"creation_id": creation_id, "access_token": META_ACCESS_TOKEN}, timeout=15)
        pub_data = pub_res.json()

        if "id" in pub_data:
            print(f"[+] Published to Instagram Story ID: {pub_data['id']}")
            return True
        else:
            print(f"[!] Instagram Story Publish Error: {pub_data}")
            return False

    except Exception as e:
        print(f"[!] Instagram Story Exception: {e}")
        return False
