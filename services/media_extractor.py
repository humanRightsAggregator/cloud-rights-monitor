import re
import requests

def extract_article_image(entry, link: str = None) -> str:
    """Extracts a valid, Instagram-compatible image URL from RSS entry or OpenGraph tags."""
    candidate_urls = []

    # 1. Check RSS media:content
    if hasattr(entry, 'media_content') and entry.media_content:
        for media in entry.media_content:
            if isinstance(media, dict) and 'url' in media:
                candidate_urls.append(media['url'])

    # 2. Check RSS media:thumbnail
    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        for media in entry.media_thumbnail:
            if isinstance(media, dict) and 'url' in media:
                candidate_urls.append(media['url'])

    # 3. Check RSS enclosures
    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enc in entry.enclosures:
            if isinstance(enc, dict) and 'href' in enc:
                candidate_urls.append(enc['href'])

    # 4. Scrape og:image tag from article link
    if link:
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            res = requests.get(link, headers=headers, timeout=6)
            if res.status_code == 200:
                match = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', res.text, re.IGNORECASE)
                if not match:
                    match = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', res.text, re.IGNORECASE)
                if match:
                    candidate_urls.append(match.group(1))
        except Exception as e:
            print(f"[!] Could not scrape og:image from {link}: {e}")

    # Prioritize JPG/JPEG URLs over WebP
    for url in candidate_urls:
        if not url or not url.startswith('http'):
            continue
        clean_url = url.split('?')[0].lower()
        if clean_url.endswith('.jpg') or clean_url.endswith('.jpeg'):
            return url

    # Fallback to any valid HTTP image candidate
    for url in candidate_urls:
        if url and url.startswith('http') and not url.split('?')[0].lower().endswith('.webp'):
            return url

    return None
