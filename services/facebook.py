import requests
from config import FB_PAGE_ID, FB_PAGE_ACCESS_TOKEN

def post_to_facebook(message: str, link: str = None, image_url: str = None) -> bool:
    """
    Posts to Facebook Page with automatic multi-stage fallback:
    1. Attempts Photo Upload (/photos).
    2. If Photo fails, falls back to Link Feed post (/feed).
    3. If Link fails, falls back to Text Feed post (/feed).
    """
    if not FB_PAGE_ID or not FB_PAGE_ACCESS_TOKEN:
        print("[!] Facebook credentials missing (FB_PAGE_ID or FB_PAGE_ACCESS_TOKEN).")
        return False

    # Attempt 1: Photo Post
    if image_url:
        try:
            photo_endpoint = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
            payload = {
                "url": image_url,
                "caption": message,
                "access_token": FB_PAGE_ACCESS_TOKEN
            }
            res = requests.post(photo_endpoint, data=payload, timeout=15)
            res_data = res.json()

            if "id" in res_data:
                print(f"[+] Published Photo to Facebook Page: {res_data['id']}")
                return True
            else:
                print(f"[!] FB Photo Upload rejected: {res_data}. Trying feed post...")
        except Exception as e:
            print(f"[!] FB Photo Exception: {e}. Trying feed post...")

    # Attempt 2: Link Feed Post (Fallback)
    try:
        feed_endpoint = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed"
        payload = {
            "message": message,
            "access_token": FB_PAGE_ACCESS_TOKEN
        }
        if link:
            payload["link"] = link

        res = requests.post(feed_endpoint, data=payload, timeout=15)
        res_data = res.json()

        if "id" in res_data:
            print(f"[+] Published Feed Post to Facebook Page: {res_data['id']}")
            return True
        else:
            print(f"[!] FB Feed Post Error: {res_data}")
            return False

    except Exception as e:
        print(f"[!] FB Feed Post Exception: {e}")
        return False
