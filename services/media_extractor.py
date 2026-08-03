import re
import requests

def extract_article_image(entry, link: str = None) -> str:
    """Extracts a valid article image URL using enhanced browser headers."""
    candidate_urls = []

    # 1. Check RSS media tags
    if hasattr(entry, 'media_content') and entry.media_content:
        for media in entry.media_content:
            if isinstance(media, dict) and 'url' in media:
                candidate_urls.append(media['url'])

    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        for media in entry.media_thumbnail:
            if isinstance(media, dict) and 'url' in media:
                candidate_urls.append(media['url'])

    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enc in entry.enclosures:
            if isinstance(enc, dict) and 'href' in enc:
                candidate_urls.append(enc['href'])

    # 2. Check HTML <img> tags in RSS summary
    summary_html = entry.get('summary', '') or entry.get('description', '')
    if summary_html:
        img_matches = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', summary_html, re.IGNORECASE)
        for img in img_matches:
            candidate_urls.append(img)

    # 3. Scrape webpage using full Chrome headers to bypass 403 blocks
    if link:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            res = requests.get(link, headers=headers, timeout=10)
            if res.status_code == 200:
                # Search for og:image or twitter:image
                match = re.search(r'<meta[^>]+(?:property|name)=["\'](?:og:image|twitter:image)["\'][^>]+content=["\']([^"\']+)["\']', res.text, re.IGNORECASE)
                if not match:
                    match = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\'](?:og:image|twitter:image)["\']', res.text, re.IGNORECASE)
                if match:
                    candidate_urls.append(match.group(1).strip())
            else:
                print(f"[!] Page scrape failed HTTP {res.status_code} for {link}")
        except Exception as e:
            print(f"[!] Scraper exception for {link}: {e}")

    # Select the first valid HTTP image URL
    for url in candidate_urls:
        if not url or not isinstance(url, str):
            continue
        url = url.strip()
        if not url.startswith('http'):
            continue
        if any(bad in url.lower() for bad in ['icon', 'avatar', 'logo', 'pixel', '1x1']):
            continue

        print(f"[+] Successfully Extracted Article Image: {url}")
        return url

    print(f"[-] No image found for: {link}")
    return None
