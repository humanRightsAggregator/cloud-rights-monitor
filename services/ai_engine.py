import json
import re
import requests
import google.generativeai as genai
from config import GROQ_API_KEY, GEMINI_API_KEY, GEMINI_API_KEY_2

# Verified active Model IDs directly from GroqCloud Docs
GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "openai/gpt-oss-20b",
    "qwen/qwen3.8-27b"
]

# Active models on Gemini
GEMINI_MODELS = [
    "gemini-1.5-flash",
    "gemini-2.0-flash"
]

def get_authorized_models() -> list:
    """Returns list of active AI scoring functions."""
    return [calculate_ai_score_groq, calculate_ai_score_gemini]

def calculate_ai_score_groq(title: str, snippet: str) -> float:
    """Calculates news urgency score using verified Groq model IDs."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not configured")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    prompt = f"Rate the human rights news urgency of this item from 1.0 to 10.0. Return ONLY a single numeric float.\nTitle: {title}\nSnippet: {snippet}"
    
    for model in GROQ_MODELS:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        }
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=8)
            if res.status_code == 200:
                data = res.json()
                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"].strip()
                    match = re.search(r'\d+(\.\d+)?', content)
                    if match:
                        return float(match.group(0))
        except Exception:
            continue
            
    raise RuntimeError("All Groq models failed or returned invalid response.")

def calculate_ai_score_gemini(title: str, snippet: str) -> float:
    """Calculates news urgency score using Gemini API fallback."""
    keys = [k for k in [GEMINI_API_KEY, GEMINI_API_KEY_2] if k]
    if not keys:
        raise ValueError("No Gemini keys configured")

    prompt = f"Rate the human rights news urgency of this item from 1.0 to 10.0. Return ONLY a single numeric float.\nTitle: {title}\nSnippet: {snippet}"
    for key in keys:
        genai.configure(api_key=key)
        for model_name in GEMINI_MODELS:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                match = re.search(r'\d+(\.\d+)?', response.text.strip())
                if match:
                    return float(match.group(0))
            except Exception:
                continue
    raise RuntimeError("All Gemini keys/models failed")

def generate_ai_draft(title: str, snippet: str, link: str, recent_topics: list = None) -> tuple:
    """Generates drafts via Groq (Primary) with Gemini Fallback across model aliases."""
    prompt = f"""You are a human rights journalist crafting engaging social media posts.

Article Title: {title}
Snippet: {snippet}
Link: {link}

Generate JSON output with exact keys: "facebook", "instagram", "threads".

Rules:
- "threads": Short, compelling, max 400 characters, no hashtags.
- "facebook": Concise overview with call to action, max 800 characters.
- "instagram": Engaging narrative with 3-5 relevant hashtags at the bottom.

Return ONLY raw JSON in this format:
{{
  "facebook": "text...",
  "instagram": "text...",
  "threads": "text..."
}}"""

    # 1. Try Groq Primary Engine across active verified model IDs
    if GROQ_API_KEY:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        for model in GROQ_MODELS:
            try:
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.3
                }
                res = requests.post(url, headers=headers, json=payload, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        content = data["choices"][0]["message"]["content"].strip()
                        drafts = json.loads(content)
                        return drafts, None
            except Exception as e:
                print(f"[!] Groq model '{model}' failed: {e}")

    # 2. Try Gemini Fallback Engine
    gemini_keys = [k for k in [GEMINI_API_KEY, GEMINI_API_KEY_2] if k]
    for idx, key in enumerate(gemini_keys):
        genai.configure(api_key=key)
        for model_name in GEMINI_MODELS:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                clean_text = response.text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]

                drafts = json.loads(clean_text.strip())
                return drafts, None
            except Exception as e:
                print(f"[!] Gemini Key {idx+1} model '{model_name}' failed: {e}")

    return None, "All AI drafting engines (Groq & Gemini) failed."
