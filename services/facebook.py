import requests
from config import FB_PAGE_ID, FB_PAGE_ACCESS_TOKEN

def post_to_facebook(message: str, link: str = None, image_url: str = None) -> bool:
    """Posts regular photo/feed content to Facebook Page."""
    if not FB_PAGE_ID or not FB_PAGE_ACCESS_TOKEN:
        return False

    if image_url:
        try:
            photo_endpoint = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
            payload = {
                "url": image_url,
                "caption": message,
                "access_token": FB_PAGE_ACCESS_TOKEN
            }
            res = requests.post(photo_endpoint, data=payload, timeout=15).json()
            if "id" in res:
                return True
        except Exception as e:
            print(f"[!] FB Photo Exception: {e}")

    try:
        feed_endpoint = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed"
        payload = {"message": message, "access_token": FB_PAGE_ACCESS_TOKEN}
        if link:
            payload["link"] = link
        res = requests.post(feed_endpoint, data=payload, timeout=15).json()
        return "id" in res
    except Exception as e:
        print(f"[!] FB Feed Exception: {e}")
        return False


def post_story_to_facebook(image_url: str) -> bool:
    """Publishes a photo story to the Facebook Page."""
    if not FB_PAGE_ID or not FB_PAGE_ACCESS_TOKEN or not image_url:
        return False

    try:
        # Step 1: Upload photo as unpublished
        upload_endpoint = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
        upload_res = requests.post(upload_endpoint, data={
            "url": image_url,
            "published": "false",
            "access_token": FB_PAGE_ACCESS_TOKEN
        }, timeout=15).json()

        if "id" not in upload_res:
            print(f"[!] FB Story Photo Upload Error: {upload_res}")
            return False

        # Step 2: Publish photo to Page Stories
        story_endpoint = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photo_stories"
        story_res = requests.post(story_endpoint, data={
            "photo_id": upload_res["id"],
            "access_token": FB_PAGE_ACCESS_TOKEN
        }, timeout=15).json()

        if story_res.get("success") or "id" in story_res:
            print(f"[+] Published Facebook Page Story.")
            return True
        return False
    except Exception as e:
        print(f"[!] FB Story Exception: {e}")
        return False
