import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

# Diverse, high-quality category fallback images to keep Instagram visual and varied
TOPIC_FALLBACKS = {
    "press": "https://images.unsplash.com/photo-1585829365295-ab7cd400c167?q=80&w=1080&auto=format&fit=crop",      # Journalists / Press Freedom
    "court": "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?q=80&w=1080&auto=format&fit=crop",      # Justice / Scales
    "protest": "https://images.unsplash.com/photo-1531206715517-5c0ba140b2b8?q=80&w=1080&auto=format&fit=crop",    # Demonstration / Rights
    "war": "https://images.unsplash.com/photo-1541872703-74c5e44368f9?q=80&w=1080&auto=format&fit=crop",        # Conflict / Refugees
    "global": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1080&auto=format&fit=crop"      # Global / UN / Earth
}

def get_fallback_by_topic(text: str) -> str:
    """Selects a topic-matched fallback image based on article content."""
    clean = text.lower()
    if any(k in clean for k in ["press", "journal", "media", "speech", "reporter"]):
        return TOPIC_FALLBACKS["press"]
    elif any(k in clean for k in ["court", "trial", "nazi", "crime", "legal", "law"]):
        return TOPIC_FALLBACKS["court"]
    elif any(k in clean for k in ["protest", "demonstrat", "activist", "dissident"]):
        return TOPIC_FALLBACKS["protest"]
    elif any(k in clean for k in ["war", "conflict", "civilian", "refugee", "kill"]):
        return TOPIC_FALLBACKS["war"]
    return TOPIC_FALLBACKS["global"]

def extract_article_image(entry: dict, article_url: str) -> str:
    """Extracts article image from RSS metadata, webpage tags, or returns a topic fallback."""
    # 1. Check RSS feed enclosure / media:content
    if "media_content" in entry and entry["media_content"]:
        for media in entry["media_content"]:
            if media.get("url") and "image" in media.get("type", "image"):
                return media["url"]
                
    if "enclosures" in entry and entry["enclosures"]:
        for enc in entry["enclosures"]:
            if enc.get("href") and "image" in enc.get("type", "image"):
                return enc["href"]

    # 2. Scrape OpenGraph / Twitter metadata directly from the webpage
    if article_url and article_url.startswith("http"):
        try:
            res = requests.get(article_url, headers=HEADERS, timeout=6)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                
                # Check og:image or twitter:image tags
                og_img = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
                if og_img and og_img.get("content"):
                    img_src = og_img["content"].strip()
                    if img_src.startswith("http"):
                        return img_src
        except Exception:
            pass  # Fall through to dynamic fallback if scraping times out or is blocked

    # 3. Dynamic Topic Fallback
    title_snippet = f"{entry.get('title', '')} {entry.get('summary', '')}"
    return get_fallback_by_topic(title_snippet)
