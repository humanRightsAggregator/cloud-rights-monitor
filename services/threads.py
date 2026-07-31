import requests
from config import META_ACCESS_TOKEN, THREADS_USER_ID

def post_to_threads(text: str) -> bool:
    """Posts published content to Meta Threads via Graph API."""
    try:
        container_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"
        c_payload = {"media_type": "TEXT", "text": text[:500], "access_token": META_ACCESS_TOKEN}
        c_res = requests.post(container_url, data=c_payload, timeout=15).json()
        container_id = c_res.get("id")

        if not container_id:
            return False

        publish_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish"
        p_res = requests.post(publish_url, data={"creation_id": container_id, "access_token": META_ACCESS_TOKEN}, timeout=15).json()
        return "id" in p_res
    except Exception as e:
        print(f"[!] Threads Publish Error: {e}")
        return False
