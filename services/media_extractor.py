import re
import requests
from urllib.parse import quote_plus

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

# Domains and keywords to reject (generic logos, placeholders, UI icons)
BLOCKED_DOMAINS = [
    "googleusercontent.com", "gstatic.com", "google.com",
    "favicon", "avatar", "logo-small", "default-brand", "s0-w300",
    "unsplash.com/photo-1451187580459"
]

def is_valid_news_image(url: str) -> bool:
    """Filters out generic placeholders, icons, and Google News logos."""
    if not url or not url.startswith("http"):
        return False
    lower_url = url.lower()
    return not any(blocked in lower_url for blocked in BLOCKED_DOMAINS)

def resolve_google_news_url(url: str) -> str:
    """Unwraps Google News RSS links to extract the actual publisher website URL."""
    if not url or "news.google.com" not in url:
        return url
    try:
        res = requests.get(url, headers=HEADERS, timeout=5, allow_redirects=True)
        if res.status_code == 200:
            # Extract real publisher link inside Google News redirect HTML
            links = re.findall(r'href=["\'](https?://[^"\']+)["\']', res.text, re.IGNORECASE)
            for link in links:
                if not any(b in link.lower() for b in ["google.com", "gstatic.com", "googleusercontent.com"]):
                    return link
    except Exception as e:
        print(f"[!] Google News unwrap error for {url[:30]}: {e}")
    return url

def generate_ai_news_image(title: str) -> str:
    """Fallback ONLY: Generates a realistic, photojournalistic AI news image via Pollinations FLUX."""
    clean_title = re.sub(r'[^a-zA-Z0-9 ]', '', title).strip()
    
    # Strictly journalistic visual prompt to avoid surreal or fantasy artwork
    prompt = f"Photojournalism photograph of {clean_title[:90]}, authentic news press picture, documentary style, realistic 35mm photography, natural ambient lighting, no text, no fantasy elements"
    
    encoded_prompt = quote_plus(prompt)
    seed = abs(hash(title)) % 100000
    
    ai_image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1080&model=flux&nologo=true&seed={seed}"
    print(f"[*] Real image not found. Generated AI news photo for '{title[:30]}...': {ai_image_url}")
    return ai_image_url

def extract_article_image(entry: dict, article_url: str) -> str:
    """Primary: Extracts real lead photo from news site. Secondary: Fallback to AI photo."""
    
    # 1. Check RSS feed media content or enclosures (Amnesty, HRW, CPJ, UN provide direct images)
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

    # 2. Resolve final publisher URL (unwrapping Google News if applicable)
    real_url = resolve_google_news_url(article_url)
    
    # 3. Scrape OpenGraph / Twitter lead photo directly from publisher webpage
    if real_url and real_url.startswith("http"):
        try:
            res = requests.get(real_url, headers=HEADERS, timeout=6, allow_redirects=True)
            if res.status_code == 200:
                html_text = res.text
                
                # Check meta og:image or twitter:image
                patterns = [
                    r'<meta\s+[^>]*?(?:property|name)=["\'](?:og:image|twitter:image)["\']\s+[^>]*?content=["\']([^"\']+)["\']',
                    r'<meta\s+[^>]*?content=["\']([^"\']+)["\']\s+[^>]*?(?:property|name)=["\'](?:og:image|twitter:image)["\']'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, html_text, re.IGNORECASE)
                    if match:
                        img_src = match.group(1).strip()
                        if is_valid_news_image(img_src):
                            print(f"[+] Scraped real news photo from webpage: {img_src[:40]}...")
                            return img_src
        except Exception as e:
            print(f"[!] Webpage image scraping error for {real_url[:30]}: {e}")

    # 4. Fallback ONLY if no real photo could be found anywhere on the news site
    return generate_ai_news_image(entry.get('title', 'human rights news report'))
