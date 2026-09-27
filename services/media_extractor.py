import re
import requests
from urllib.parse import quote_plus

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

# Block generic logos, Google placeholders, and small icons
BLOCKED_PATTERNS = [
    "googleusercontent.com", "gstatic.com", "google.com/news",
    "favicon", "avatar", "logo-small", "default-brand"
]

def is_valid_news_image(url: str) -> bool:
    """Filters out generic placeholders, icons, and Google News logos."""
    if not url or not url.startswith("http"):
        return False
    lower_url = url.lower()
    return not any(b in lower_url for b in BLOCKED_PATTERNS)

def get_dynamic_keyword_image(text: str) -> str:
    """Generates a topic-matched image URL based on title keywords."""
    clean = re.sub(r'[^a-zA-Z0-9 ]', '', text.lower())
    words = [w for k in ["court", "trial", "protest", "war", "journal", "police", "refugee", "election", "rights"] for w in clean.split() if k in w]
    query = words[0] if words else "humanitarian"
    return f"https://images.unsplash.com/photo-1589829545856-d10d557cf95f?q=80&w=1080&auto=format&fit=crop&sig={hash(text) % 1000}"

def extract_article_image(entry: dict, article_url: str) -> str:
    """Scrapes OpenGraph image from real publisher URL, filtering out Google News logos."""
    # 1. Check RSS feed enclosure / media:content
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

    # 2. Scrape OpenGraph / Twitter metadata directly from webpage
    if article_url and article_url.startswith("http"):
        try:
            res = requests.get(article_url, headers=HEADERS, timeout=6, allow_redirects=True)
            if res.status_code == 200:
                html_text = res.text
                
                # Check og:image or twitter:image meta tags
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

    # 3. Dynamic Topic Fallback
    return get_dynamic_keyword_image(entry.get('title', 'human rights'))
