import json
import google.generativeai as genai
from config import GEMINI_API_KEY

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"[!] Gemini config warning: {e}")

MASTER_HASHTAGS = ["#HumanRights", "#HumanDignity", "#JusticeNow", "#RightsWatch"]

def generate_ai_draft(title: str, snippet: str, link: str, recent_topics: list) -> tuple:
    """Generates platform-tailored posts with human POV and master hashtags."""
    if not GEMINI_API_KEY:
        return None, "Gemini API Key missing"

    # Use supported model identifier with fallback handling
    model_names = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash-latest']
    model = None

    for name in model_names:
        try:
            model = genai.GenerativeModel(name)
            break
        except Exception:
            continue

    if not model:
        model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = f"""
    You are an empathetic human rights journalist writing for an international monitoring network.
    Analyze this report:
    - Headline: {title}
    - Summary: {snippet}
    - Source: {link}

    Instructions:
    1. Emphasize human impact, civil rights, and affected communities.
    2. Output ONLY valid raw JSON (no markdown fences or code blocks):
    {{
      "threads_draft": "Concise summary under 420 chars including link and key human impact.",
      "long_draft": "Expanded narrative (2 paragraphs) with human perspective, report findings, and link."
    }}
    """

    try:
        response = model.generate_content(prompt)
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(clean_text)

        tags_string = " ".join(MASTER_HASHTAGS)
        threads_post = f"{data.get('threads_draft', '')}\n\n{tags_string}"
        long_post = f"{data.get('long_draft', '')}\n\n{tags_string}"

        return {"threads": threads_post, "long": long_post}, None

    except Exception as e:
        print(f"[!] Gemini generation error: {e}")
        fallback_tags = " ".join(MASTER_HASHTAGS)
        fallback = f"[CW: Human Rights Report]\n\n{title}\n\nSource: {link}\n\n{fallback_tags}"
        return {"threads": fallback, "long": fallback}, str(e)
