import re
import requests
from urllib.parse import quote_plus

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

# Domains and keywords to reject (placeholders, generic logos, Google News wrappers)
BLOCKED_DOMAINS = [
    "googleusercontent.com", "gstatic.com", "google.com",
    "favicon", "avatar", "logo-small", "default-brand", "s0-w300",
    "unsplash.com/photo-1451187580459"  # Blocks old generic space fallback
]

def is_valid_news_image(url: str) -> bool:
    """Filters out generic placeholders, icons, and Google News logos."""
    if not url or not url.startswith("http"):
        return False
    lower_url = url.lower()
    return not any(blocked in lower_url for blocked in BLOCKED_DOMAINS)

def resolve_final_url(url: str) -> str:
    """Unwraps Google News redirect URLs to get the true news article webpage."""
    if not url:
        return ""
    if "news.google.com" in url:
        try:
            res = requests.head(url, headers=HEADERS, allow_redirects=True, timeout=4)
            return res.url
        except Exception:
            return url
    return url

def generate_ai_news_image(title: str) -> str:
    """Generates a custom, highly relevant AI news image for free using Pollinations FLUX engine."""
    clean_title = re.sub(r'[^a-zA-Z0-9 ]', '', title).strip()
    
    # Construct an editorial visual prompt
    prompt = f"Editorial photo for news story: {clean_title[:110]}, documentary style, dramatic lighting, detailed, high resolution"
    
    encoded_prompt = quote_plus(prompt)
    seed = abs(hash(title)) % 100000
    
    # Pure URL string formatting (instant <1ms execution in Python)
    ai_image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1080&model=flux&nologo=true&seed={seed}"
    print(f"[*] Generated Free AI Image URL for '{title[:30]}...': {ai_image_url}")
    return ai_image_url

def extract_article_image(entry: dict, article_url: str) -> str:
    """Extracts true news lead photo or falls back to a custom, relevant AI image."""
    # 1. Check RSS feed media content or enclosures
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

    # 2. Unwrap Google redirects and scrape OpenGraph lead photo from destination webpage
    real_url = resolve_final_url(article_url)
    if real_url and real_url.startswith("http"):
        try:
            res = requests.get(real_url, headers=HEADERS, timeout=5, allow_redirects=True)
            if res.status_code == 200:
                html_text = res.text
                pattern = r'<meta\s+[^>]*?(?:property|name)=["\'](?:og:image|twitter:image)["\']\s+[^>]*?content=["\']([^"\']+)["\']'
                match = re.search(pattern, html_text, re.IGNORECASE)
                
                if not match:
                    pattern_alt = r'<meta\s+[^>]*?content=["\']([^"\']+)["\']\s+[^>]*?(?:property|name)=["\'](?:og:image|twitter:image)["\']'
                    match = re.search(pattern_alt, html_text, re.IGNORECASE)

                if match:
                    img_src = match.group(1).strip()
                    if is_valid_news_image(img_src):
                        return img_src
        except Exception as e:
            print(f"[!] Scraping fallback skipped for {real_url[:30]}: {e}")

    # 3. Dynamic Free AI Image Fallback
    return generate_ai_news_image(entry.get('title', 'human rights news report'))
