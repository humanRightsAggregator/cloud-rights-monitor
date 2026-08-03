import requests
import time
import random
from config import INSTAGRAM_ACCOUNT_ID, FB_PAGE_ACCESS_TOKEN

DEFAULT_IG_IMAGE = "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=1080&q=80"

def post_to_instagram(caption: str, image_url: str = None) -> bool:
    """Posts an image card and caption to the Instagram Business account."""
    if not INSTAGRAM_ACCOUNT_ID or not FB_PAGE_ACCESS_TOKEN:
        print("[!] Instagram credentials missing.")
        return False

    target_image = image_url if image_url else DEFAULT_IG_IMAGE
    
    # Add unique parameter to bypass Instagram's duplicate image cache
    rand_param = f"rand={random.randint(1, 100000)}"
    final_media_url = f"{target_image}&{rand_param}" if "?" in target_image else f"{target_image}?{rand_param}"

    try:
        # Step 1: Create Container
        container_endpoint = f"https://graph.facebook.com/v20.0/{INSTAGRAM_ACCOUNT_ID}/media"
        c_payload = {
            "image_url": final_media_url,
            "caption": caption[:2200],
            "access_token": FB_PAGE_ACCESS_TOKEN
        }
        c_res = requests.post(container_endpoint, data=c_payload, timeout=15).json()
        container_id = c_res.get("id")

        if not container_id:
            print(f"[!] Instagram Container Error: {c_res}")
            # If the article image failed, retry once with fallback image
            if image_url:
                print("[*] Retrying Instagram with default fallback image...")
                return post_to_instagram(caption, image_url=None)
            return False

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
