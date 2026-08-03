import re
import requests
from urllib.parse import quote

def extract_article_image(entry, link: str = None) -> str:
    """Extracts an article image from RSS entry, direct scrape, or Microlink API."""
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

    # 4. Check HTML <img> tags in RSS summary
    summary_html = entry.get('summary', '') or entry.get('description', '')
    if summary_html:
        img_matches = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', summary_html, re.IGNORECASE)
        for img in img_matches:
            candidate_urls.append(img)

    # Return valid RSS image if found
    for url in candidate_urls:
        if url and isinstance(url, str) and url.startswith('http'):
            if not any(bad in url.lower() for bad in ['icon', 'avatar', 'logo', 'pixel', '1x1']):
                print(f"[+] Found Image via RSS Feed: {url}")
                return url

    # 5. Use Microlink API to bypass Cloudflare/403 blocks on article page
    if link:
        try:
            micro_url = f"https://api.microlink.io?url={quote(link)}"
            res = requests.get(micro_url, timeout=8).json()
            if res.get('status') == 'success':
                image_data = res.get('data', {}).get('image', {})
                if image_data and 'url' in image_data:
                    img_url = image_data['url']
                    print(f"[+] Successfully Extracted Image via Microlink: {img_url}")
                    return img_url
        except Exception as e:
            print(f"[!] Microlink extraction error for {link}: {e}")

    print(f"[-] No image could be extracted for: {link}")
    return None
