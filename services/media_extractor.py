import re
import requests

def extract_article_image(entry, link: str = None) -> str:
    """Extracts a valid article image URL from RSS metadata or OpenGraph tags."""
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

    # 4. Scrape og:image tag from article webpage
    if link:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            res = requests.get(link, headers=headers, timeout=8)
            if res.status_code == 200:
                match = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', res.text, re.IGNORECASE)
                if not match:
                    match = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', res.text, re.IGNORECASE)
                if match:
                    candidate_urls.append(match.group(1).strip())
        except Exception as e:
            print(f"[!] Could not scrape og:image from {link}: {e}")

    # Prioritize JPEG/JPG files
    for url in candidate_urls:
        if not url or not url.startswith('http'):
            continue
        clean_path = url.split('?')[0].lower()
        if clean_path.endswith('.jpg') or clean_path.endswith('.jpeg'):
            return url

    # Fallback to PNG or other valid HTTP images (excluding webp)
    for url in candidate_urls:
        if url and url.startswith('http') and not url.split('?')[0].lower().endswith('.webp'):
            return url

    return None
