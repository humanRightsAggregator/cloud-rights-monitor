import json
import google.generativeai as genai
from config import GEMINI_API_KEY

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Permanent Master Hashtags added to every post
MASTER_HASHTAGS = ["#HumanRights", "#HumanDignity", "#JusticeNow", "#RightsWatch"]

def generate_ai_draft(title: str, snippet: str, link: str, recent_topics: list) -> tuple:
    """Generates platform-tailored posts with a human POV and structured hashtags."""
    if not GEMINI_API_KEY:
        return None, "Gemini API Key missing"

    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
    You are an empathetic human rights journalist writing for an international monitoring network.
    Analyze this report:
    - Headline: {title}
    - Summary: {snippet}
    - Source: {link}

    Instructions:
    1. Human POV Angle: Emphasize the real human cost, affected individuals, rights violated, and civic impact—avoid dry robotic news summaries.
    2. Dynamic Hashtags: Generate 3 to 4 specific topic hashtags relevant ONLY to this country/issue (e.g., #SudanCrisis, #PressFreedom, #WomenRights).
    3. Generate TWO versions formatted strictly as JSON:

    {{
      "threads_draft": "Post text under 450 characters including source link, human POV summary, and max 4 hashtags total.",
      "long_draft": "Richer detailed narrative (2-3 paragraphs) highlighting the human perspective, key report findings, source link, and full hashtag block."
    }}

    Rules:
    - Header must start with: [CW: Human Rights Report]
    - Do NOT include markdown code fences in response. Output ONLY valid raw JSON.
    """

    try:
        response = model.generate_content(prompt)
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(clean_json)

        # Merge dynamic topic hashtags with Master Hashtags
        topic_tags = " ".join(MASTER_HASHTAGS)

        # Final formatting
        threads_post = f"{data['threads_draft']}\n\n{topic_tags}"
        long_post = f"{data['long_draft']}\n\n{topic_tags}"

        return {
            "threads": threads_post,
            "long": long_post
        }, None

    except Exception as e:
        print(f"[!] Gemini generation error: {e}")
        return None, str(e)
