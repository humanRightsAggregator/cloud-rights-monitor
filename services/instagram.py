import requests
import time
import random
from config import INSTAGRAM_ACCOUNT_ID, FB_PAGE_ACCESS_TOKEN

# Base image URL
DEFAULT_IG_IMAGE = "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=1080&q=80"

def post_to_instagram(caption: str, image_url: str = None) -> bool:
    """Posts an image card and caption to the Instagram Business account."""
    if not INSTAGRAM_ACCOUNT_ID or not FB_PAGE_ACCESS_TOKEN:
        print("[!] Instagram credentials missing.")
        return False

    # Add a random cache-buster to bypass Instagram's duplicate image spam filter
    random_id = random.randint(1, 100000)
    media_url = f"{image_url}&rand={random_id}" if image_url else f"{DEFAULT_IG_IMAGE}&rand={random_id}"

    try:
        # Step 1: Create Media Container
        container_endpoint = f"https://graph.facebook.com/v20.0/{INSTAGRAM_ACCOUNT_ID}/media"
        c_payload = {
            "image_url": media_url,
            "caption": caption[:2200],  # Instagram caption limit
            "access_token": FB_PAGE_ACCESS_TOKEN
        }
        c_res = requests.post(container_endpoint, data=c_payload, timeout=15).json()
        container_id = c_res.get("id")

        if not container_id:
            print(f"[!] Instagram Container Creation Error: {c_res}")
            return False

        # DELAY: Give Meta's servers 5 seconds to download and process the image
        time.sleep(5)

        # Step 2: Publish Container
        publish_endpoint = f"https://graph.facebook.com/v20.0/{INSTAGRAM_ACCOUNT_ID}/media_publish"
        p_payload = {
            "creation_id": container_id,
            "access_token": FB_PAGE_ACCESS_TOKEN
        }
        p_res = requests.post(publish_endpoint, data=p_payload, timeout=15).json()

        if "id" in p_res:
            print(f"[+] Published to Instagram: {p_res['id']}")
            return True
        else:
            print(f"[!] Instagram Publish Error: {p_res}")
            return False

    except Exception as e:
        print(f"[!] Instagram API Exception: {e}")
        return False
