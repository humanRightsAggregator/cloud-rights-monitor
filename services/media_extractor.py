import re
import requests

def extract_article_image(entry, link: str = None) -> str:
    """Extracts the featured article image URL from RSS media tags or OpenGraph metadata."""
    # 1. Check RSS media:content
    if hasattr(entry, 'media_content') and entry.media_content:
        for media in entry.media_content:
            if isinstance(media, dict) and 'url' in media:
                return media['url']

    # 2. Check RSS media:thumbnail
    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        for media in entry.media_thumbnail:
            if isinstance(media, dict) and 'url' in media:
                return media['url']

    # 3. Check RSS enclosures
    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enc in entry.enclosures:
            if isinstance(enc, dict) and 'href' in enc:
                href = enc['href']
                if any(href.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                    return href

    # 4. Scrape webpage og:image directly from article link
    if link:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            res = requests.get(link, headers=headers, timeout=6)
            if res.status_code == 200:
                match = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', res.text, re.IGNORECASE)
                if not match:
                    match = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', res.text, re.IGNORECASE)
                if match:
                    img_url = match.group(1)
                    if img_url.startswith('http'):
                        return img_url
        except Exception as e:
            print(f"[!] Could not scrape og:image from {link}: {e}")

    return None
