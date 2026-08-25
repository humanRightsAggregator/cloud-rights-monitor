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

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        You are an empathetic human rights journalist writing for an international monitoring network.
        Analyze this report:
        - Headline: {title}
        - Summary: {snippet}
        - Source: {link}

        Instructions:
        1. Emphasize the human cost, civil rights violated, and impact on real people.
        2. Generate 3 to 4 specific topic hashtags relevant to this report.
        3. Output ONLY raw valid JSON (no markdown formatting or code blocks) using this schema:
        {{
          "threads_draft": "Concise post under 420 chars including source link and key human impact.",
          "long_draft": "Expanded multi-paragraph writeup with detailed narrative, human impact, key facts, and link."
        }}
        """

        response = model.generate_content(prompt)
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(clean_text)

        tags_string = " ".join(MASTER_HASHTAGS)
        threads_post = f"{data.get('threads_draft', '')}\n\n{tags_string}"
        long_post = f"{data.get('long_draft', '')}\n\n{tags_string}"

        return {
            "threads": threads_post,
            "long": long_post
        }, None

    except Exception as e:
        print(f"[!] Gemini draft generation error: {e}")
        # Fallback draft if AI formatting fails
        fallback_tags = " ".join(MASTER_HASHTAGS)
        fallback = f"[CW: Human Rights Report]\n\n{title}\n\nSource: {link}\n\n{fallback_tags}"
        return {"threads": fallback, "long": fallback}, str(e)
