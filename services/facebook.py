import requests
from config import FB_PAGE_ID, FB_PAGE_ACCESS_TOKEN

def post_to_facebook(text: str, link: str = None, image_url: str = None) -> bool:
    """Publishes a photo post or text/link post to the Facebook Page."""
    if not FB_PAGE_ID or not FB_PAGE_ACCESS_TOKEN:
        print("[!] Facebook credentials missing.")
        return False

    try:
        # If an article image exists, post as a Photo
        if image_url:
            url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/photos"
            message = text
            if link and link not in text:
                message += f"\n\n🔗 Read full report: {link}"

            payload = {
                "url": image_url,
                "caption": message,
                "access_token": FB_PAGE_ACCESS_TOKEN
            }
            res = requests.post(url, data=payload, timeout=15)
            data = res.json()
            if "id" in data:
                print(f"[+] Published Photo to Facebook Page: {data['id']}")
                return True
            else:
                print(f"[!] Facebook Photo Error (falling back to feed): {data}")

        # Fallback to Feed post
        url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/feed"
        payload = {
            "message": text,
            "access_token": FB_PAGE_ACCESS_TOKEN
        }
        if link:
            payload["link"] = link

        res = requests.post(url, data=payload, timeout=15)
        data = res.json()
        if "id" in data:
            print(f"[+] Published Feed to Facebook Page: {data['id']}")
            return True
        else:
            print(f"[!] Facebook Feed Error: {data}")
            return False

    except Exception as e:
        print(f"[!] Facebook API Exception: {e}")
        return False
