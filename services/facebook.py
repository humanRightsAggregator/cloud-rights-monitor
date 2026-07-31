import requests
from config import FB_PAGE_ID, FB_PAGE_ACCESS_TOKEN

def post_to_facebook(text: str, link: str = None) -> bool:
    """Publishes a text post (with optional link preview) to the Facebook Page."""
    if not FB_PAGE_ID or not FB_PAGE_ACCESS_TOKEN:
        print("[!] Facebook credentials missing.")
        return False

    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/feed"
    payload = {
        "message": text,
        "access_token": FB_PAGE_ACCESS_TOKEN
    }
    if link:
        payload["link"] = link

    try:
        res = requests.post(url, data=payload, timeout=15)
        data = res.json()
        if "id" in data:
            print(f"[+] Published to Facebook Page: {data['id']}")
            return True
        else:
            print(f"[!] Facebook Publish Error: {data}")
            return False
    except Exception as e:
        print(f"[!] Facebook API Exception: {e}")
        return False
