import json
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_API_KEY_2

def get_authorized_models() -> list:
    """Returns a list of active Gemini model instances configured across available API keys."""
    models = []
    keys = [k.strip() for k in [GEMINI_API_KEY, GEMINI_API_KEY_2] if k and k.strip()]
    for key in keys:
        try:
            genai.configure(api_key=key)
            models.append(genai.GenerativeModel("gemini-1.5-flash"))
        except Exception as e:
            print(f"[!] Failed to initialize Gemini model instance: {e}")
    return models

def generate_ai_draft(title: str, snippet: str, link: str, recent_topics: list = None) -> tuple:
    """Generates platform-tailored social media captions using multi-key Gemini failover."""
    keys = [k.strip() for k in [GEMINI_API_KEY, GEMINI_API_KEY_2] if k and k.strip()]
    if not keys:
        return None, "No Gemini API keys configured."

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

    for idx, key in enumerate(keys):
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            clean_text = response.text.strip()
            
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]

            drafts = json.loads(clean_text.strip())
            return drafts, None
        except Exception as e:
            print(f"[!] Gemini Key {idx+1} failed: {e}")
            if "429" in str(e) and idx < len(keys) - 1:
                print(f"[*] Rotating to Gemini Key {idx+2}...")
                continue
            return None, str(e)

    return None, "All Gemini API keys exhausted or failed."
