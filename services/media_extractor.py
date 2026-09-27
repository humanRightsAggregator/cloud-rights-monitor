import re
import requests
from urllib.parse import quote_plus

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5"
}

# Domains and keywords to reject (generic logos, placeholders, UI icons)
BLOCKED_DOMAINS = [
    "googleusercontent.com", "gstatic.com", "google.com", "googletagmanager",
    "favicon", "avatar", "logo-small", "default-brand", "s0-w300", "icon",
    "unsplash.com/photo-1451187580459"
]

def is_valid_news_image(url: str) -> bool:
    """Filters out generic placeholders, icons, and Google News logos."""
    if not url or not url.startswith("http"):
        return False
    lower_url = url.lower()
    return not any(blocked in lower_url for blocked in BLOCKED_DOMAINS)

def resolve_google_news_url(url: str) -> str:
    """Unwraps Google News RSS redirect links to extract the actual publisher website URL."""
    if not url or "news.google.com" not in url:
        return url
    try:
        res = requests.get(url, headers=HEADERS, timeout=6, allow_redirects=True)
        if res.status_code == 200:
            # Extract all HTTP/HTTPS links from the Google News HTML payload
            found_urls = re.findall(r'https?://[^\s<>"\'\\]+', res.text)
            for link in found_urls:
                lower_link = link.lower()
                # Skip Google internal domains and technical tracking assets
                if not any(b in lower_link for b in ["google.com", "gstatic.com", "googleusercontent.com", "schema.org", "w3.org", "youtube.com", "doubleclick"]):
                    print(f"[+] Unwrapped Google News link to real publisher: {link[:50]}...")
                    return link
    except Exception as e:
        print(f"[!] Google News unwrap error for {url[:30]}: {e}")
    return url

def extract_image_from_html_summary(summary_html: str) -> str:
    """Scrapes embedded <img> tags from RSS HTML summaries if available."""
    if not summary_html:
        return ""
    img_matches = re.findall(r'<img\s+[^>]*?src=["\']([^"\']+)["\']', summary_html, re.IGNORECASE)
    for img_url in img_matches:
        if is_valid_news_image(img_url):
            return img_url
    return ""

def generate_ai_news_image(title: str) -> str:
    """Fallback ONLY: Generates a realistic, photojournalistic AI news image via Pollinations FLUX."""
    clean_title = re.sub(r'[^a-zA-Z0-9 ]', '', title).strip()
    
    # Realistic 35mm photojournalism prompt (avoids surreal, fantasy, or cinematic 3D renders)
    prompt = f"Editorial press photo for news agency report about {clean_title[:90]}. Professional photojournalism, authentic documentary style, natural lighting, candid 35mm news photograph, realistic scene, no text, no CGI, no fantasy art"
    
    encoded_prompt = quote_plus(prompt)
    seed = abs(hash(title)) % 100000
    
    ai_image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1080&model=flux&nologo=true&seed={seed}"
    print(f"[*] Real news image unavailable. Generated documentary AI fallback for '{title[:30]}...': {ai_image_url}")
    return ai_image_url

def extract_article_image(entry: dict, article_url: str) -> str:
    """Primary: Extracts authentic publisher photo from RSS or Webpage. Secondary: AI Fallback."""
    
    # 1. Check RSS feed media content or enclosures (Amnesty, HRW, CPJ, UN)
    if "media_content" in entry and entry["media_content"]:
        for media in entry["media_content"]:
            u = media.get("url", "")
            if is_valid_news_image(u):
                print(f"[+] Found real photo in RSS media_content: {u[:40]}...")
                return u
                
    if "enclosures" in entry and entry["enclosures"]:
        for enc in entry["enclosures"]:
            u = enc.get("href", "")
            if is_valid_news_image(u):
                print(f"[+] Found real photo in RSS enclosures: {u[:40]}...")
                return u

    # 2. Check embedded <img> tags in RSS summary/description
    summary_img = extract_image_from_html_summary(entry.get('summary', '') or entry.get('description', ''))
    if summary_img:
        print(f"[+] Found real photo in RSS summary HTML: {summary_img[:40]}...")
        return summary_img

    # 3. Resolve final publisher URL (unwrapping Google News links)
    real_url = resolve_google_news_url(article_url)
    
    # 4. Scrape OpenGraph / Twitter lead photo directly from destination webpage
    if real_url and real_url.startswith("http"):
        try:
            res = requests.get(real_url, headers=HEADERS, timeout=7, allow_redirects=True)
            if res.status_code == 200:
                html_text = res.text
                
                # Check meta og:image, twitter:image, or link rel="image_src"
                patterns = [
                    r'<meta\s+[^>]*?(?:property|name)=["\'](?:og:image|twitter:image)["\']\s+[^>]*?content=["\']([^"\']+)["\']',
                    r'<meta\s+[^>]*?content=["\']([^"\']+)["\']\s+[^>]*?(?:property|name)=["\'](?:og:image|twitter:image)["\']',
                    r'<link\s+[^>]*?rel=["\'](?:image_src|thumbnail)["\']\s+[^>]*?href=["\']([^"\']+)["\']'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, html_text, re.IGNORECASE)
                    if match:
                        img_src = match.group(1).strip()
                        if is_valid_news_image(img_src):
                            print(f"[+] Scraped real news lead photo from webpage: {img_src[:40]}...")
                            return img_src
        except Exception as e:
            print(f"[!] Webpage image scraping error for {real_url[:30]}: {e}")

    # 5. Fallback ONLY if no authentic news photo exists anywhere
    return generate_ai_news_image(entry.get('title', 'human rights news report'))
