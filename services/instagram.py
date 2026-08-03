import requests
import time
import random
from config import INSTAGRAM_ACCOUNT_ID, FB_PAGE_ACCESS_TOKEN

DEFAULT_IG_IMAGE = "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=1080&q=80"

def post_to_instagram(caption: str, image_url: str = None) -> bool:
    """Posts an image card and caption to Instagram with container status polling."""
    if not INSTAGRAM_ACCOUNT_ID or not FB_PAGE_ACCESS_TOKEN:
        print("[!] Instagram credentials missing.")
        return False

    # Preserve exact article URL; only add cache-buster if using the default image
    if image_url:
        final_media_url = image_url
    else:
        rand_id = random.randint(1, 100000)
        final_media_url = f"{DEFAULT_IG_IMAGE}&rand={rand_id}"

    try:
        # Step 1: Create Container
        container_endpoint = f"https://graph.facebook.com/v20.0/{INSTAGRAM_ACCOUNT_ID}/media"
        c_payload = {
            "image_url": final_media_url,
            "caption": caption[:2200],
            "access_token": FB_PAGE_ACCESS_TOKEN
        }
        c_res = requests.post(container_endpoint, data=c_payload, timeout=20).json()
        container_id = c_res.get("id")

        if not container_id:
            print(f"[!] Instagram Container Creation Error: {c_res}")
            if image_url:
                print("[*] Article image failed on Instagram. Retrying with fallback...")
                return post_to_instagram(caption, image_url=None)
            return False

        # Step 2: Poll Container Status until Meta finishes processing
        status_url = f"https://graph.facebook.com/v20.0/{container_id}"
        status_payload = {
            "fields": "status_code,status",
            "access_token": FB_PAGE_ACCESS_TOKEN
        }

        ready = False
        for _ in range(10):  # Poll every 2s for up to 20 seconds
            time.sleep(2)
            s_res = requests.get(status_url, params=status_payload, timeout=10).json()
            status_code = s_res.get("status_code")

            if status_code == "FINISHED":
                ready = True
                break
            elif status_code == "ERROR":
                print(f"[!] Instagram Processing Error: {s_res}")
                break

        if not ready:
            print("[!] Instagram container processing timed out. Attempting fallback...")
            if image_url:
                return post_to_instagram(caption, image_url=None)
            return False

        # Step 3: Publish Container
        publish_endpoint = f"https://graph.facebook.com/v20.0/{INSTAGRAM_ACCOUNT_ID}/media_publish"
        p_payload = {
            "creation_id": container_id,
            "access_token": FB_PAGE_ACCESS_TOKEN
        }
        p_res = requests.post(publish_endpoint, data=p_payload, timeout=20).json()

        if "id" in p_res:
            print(f"[+] Published to Instagram: {p_res['id']}")
            return True
        else:
            print(f"[!] Instagram Publish Error: {p_res}")
            return False

    except Exception as e:
        print(f"[!] Instagram API Exception: {e}")
        return False
