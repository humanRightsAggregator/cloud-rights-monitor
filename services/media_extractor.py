import re
import requests

def extract_article_image(entry, link: str = None) -> str:
    """Extracts a valid article image URL from RSS entry, summary HTML, or web page metadata."""
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

    # 4. Check HTML <img> tags in RSS summary/description
    summary_html = entry.get('summary', '') or entry.get('description', '')
    if summary_html:
        img_matches = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', summary_html, re.IGNORECASE)
        for img in img_matches:
            candidate_urls.append(img)

    # 5. Scrape og:image tag from article webpage
    if link:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
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

    # Return the first valid HTTP image URL found (excluding icons/pixels)
    for url in candidate_urls:
        if not url or not isinstance(url, str):
            continue
        url = url.strip()
        if not url.startswith('http'):
            continue
        if any(ignored in url.lower() for ignored in ['icon', 'avatar', 'logo', 'pixel', '1x1']):
            continue

        print(f"[+] Extracted Article Image: {url}")
        return url

    print("[-] No image extracted for this article.")
    return None
