import re
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

# Strict filter blocking Google logos, generic thumbnails, and UI icons
BLOCKED_DOMAINS = [
    "googleusercontent.com", "gstatic.com", "google.com",
    "favicon", "avatar", "logo-small", "default-brand", "s0-w300"
]

def is_valid_news_image(url: str) -> bool:
    """Rejects Google News thumbnails, generic logos, and placeholder icons."""
    if not url or not url.startswith("http"):
        return False
    lower_url = url.lower()
    return not any(blocked in lower_url for blocked in BLOCKED_DOMAINS)

def get_topic_fallback(text: str) -> str:
    """Returns a high-quality Unsplash image matched to article keywords."""
    clean = re.sub(r'[^a-zA-Z0-9 ]', '', text.lower())
    if any(k in clean for k in ["court", "trial", "legal", "law", "judge"]):
        return "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?q=80&w=1080&auto=format&fit=crop"
    elif any(k in clean for k in ["protest", "demonstrat", "march", "activist"]):
        return "https://images.unsplash.com/photo-1531206715517-5c0ba140b2b8?q=80&w=1080&auto=format&fit=crop"
    elif any(k in clean for k in ["press", "media", "journal", "reporter", "speech"]):
        return "https://images.unsplash.com/photo-1585829365295-ab7cd400c167?q=80&w=1080&auto=format&fit=crop"
    elif any(k in clean for k in ["war", "conflict", "refugee", "civilian", "strike"]):
        return "https://images.unsplash.com/photo-1541872703-74c5e44368f9?q=80&w=1080&auto=format&fit=crop"
    return "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1080&auto=format&fit=crop"

def extract_article_image(entry: dict, article_url: str) -> str:
    """Extracts genuine news lead photo, filtering out Google News thumbnails."""
    # 1. Check RSS media content / enclosures
    if "media_content" in entry and entry["media_content"]:
        for media in entry["media_content"]:
            u = media.get("url", "")
            if is_valid_news_image(u):
                return u
                
    if "enclosures" in entry and entry["enclosures"]:
        for enc in entry["enclosures"]:
            u = enc.get("href", "")
            if is_valid_news_image(u):
                return u

    # 2. Scrape OpenGraph image directly from webpage HTML
    if article_url and article_url.startswith("http"):
        try:
            res = requests.get(article_url, headers=HEADERS, timeout=6, allow_redirects=True)
            if res.status_code == 200:
                html_text = res.text
                pattern = r'<meta\s+[^>]*?(?:property|name)=["\'](?:og:image|twitter:image)["\']\s+[^>]*?content=["\']([^"\']+)["\']'
                match = re.search(pattern, html_text, re.IGNORECASE)
                
                if not match:
                    pattern_alt = r'<meta\s+[^>]*?content=["\']([^"\']+)["\']\s+[^>]*?(?:property|name)=["\'](?:og:image|twitter:image)["\']'
                    match = re.search(pattern_alt, html_text, re.IGNORECASE)

                if match:
                    img_src = match.group(1).strip()
                    if is_valid_news_image(img_src):
                        return img_src
        except Exception:
            pass

    # 3. Keyword Topic Fallback
    return get_topic_fallback(f"{entry.get('title', '')} {entry.get('summary', '')}")
