import requests
from config import IG_USER_ID, FB_PAGE_ACCESS_TOKEN

def post_to_instagram(caption: str, image_url: str = None) -> bool:
    """Publishes a regular feed post to Instagram."""
    if not IG_USER_ID or not FB_PAGE_ACCESS_TOKEN or not image_url:
        print("[!] Instagram credentials or image missing.")
        return False

    try:
        container_endpoint = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media"
        payload = {
            "image_url": image_url,
            "caption": caption,
            "access_token": FB_PAGE_ACCESS_TOKEN
        }
        res = requests.post(container_endpoint, data=payload, timeout=15)
        res_data = res.json()

        if "id" not in res_data:
            print(f"[!] IG Feed Container Error: {res_data}")
            return False

        publish_endpoint = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish"
        pub_res = requests.post(publish_endpoint, data={
            "creation_id": res_data["id"],
            "access_token": FB_PAGE_ACCESS_TOKEN
        }, timeout=15)
        
        return "id" in pub_res.json()
    except Exception as e:
        print(f"[!] Instagram Feed Exception: {e}")
        return False


def post_story_to_instagram(image_url: str) -> bool:
    """Publishes a 9:16 vertical image directly to Instagram Stories."""
    if not IG_USER_ID or not FB_PAGE_ACCESS_TOKEN or not image_url:
        return False

    try:
        # Step 1: Create Story Container (media_type="STORIES")
        container_endpoint = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media"
        payload = {
            "image_url": image_url,
            "media_type": "STORIES",
            "access_token": FB_PAGE_ACCESS_TOKEN
        }
        res = requests.post(container_endpoint, data=payload, timeout=15).json()

        if "id" not in res:
            print(f"[!] IG Story Container Error: {res}")
            return False

        # Step 2: Publish Story
        publish_endpoint = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish"
        pub_res = requests.post(publish_endpoint, data={
            "creation_id": res["id"],
            "access_token": FB_PAGE_ACCESS_TOKEN
        }, timeout=15).json()

        if "id" in pub_res:
            print(f"[+] Published Instagram Story: {pub_res['id']}")
            return True
        return False
    except Exception as e:
        print(f"[!] IG Story Exception: {e}")
        return False
