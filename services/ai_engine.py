import json
import google.generativeai as genai
from config import GEMINI_API_KEY

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"[!] Gemini config warning: {e}")

MASTER_HASHTAGS = ["#HumanRights", "#HumanDignity", "#JusticeNow", "#RightsWatch"]

def get_active_model():
    """Dynamically locates an active, supported Gemini model for this API key."""
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                model_name = m.name.replace('models/', '')
                if 'flash' in model_name:
                    return genai.GenerativeModel(model_name)
    except Exception as e:
        print(f"[!] Dynamic model lookup notice: {e}")

    # Active production fallbacks
    for candidate in ['gemini-2.0-flash', 'gemini-1.5-flash-latest']:
        try:
            return genai.GenerativeModel(candidate)
        except Exception:
            continue

    return genai.GenerativeModel('gemini-2.0-flash')

def generate_ai_draft(title: str, snippet: str, link: str, recent_topics: list) -> tuple:
    tags_string = " ".join(MASTER_HASHTAGS)

    fallback_threads = f"{title}\n\n{snippet[:200]}...\n\nSource: {link}\n\n#HumanRights"
    fallback_long = f"{title}\n\n{snippet}\n\nSource: {link}\n\n{tags_string}"

    if not GEMINI_API_KEY:
        return {
            "threads": fallback_threads,
            "facebook": fallback_long,
            "instagram": fallback_long
        }, "No API Key"

    prompt = f"""
    You are an expert human rights journalist and social media growth strategist.
    Write multi-platform posts for this report:
    - Headline: {title}
    - Report Context: {snippet}
    - Link: {link}

    CORE WRITING RULES:
    1. Human POV: Lead with the human impact—who is affected, civil liberty violations, suffering, or community resilience.
    2. Detailed Description: Provide deep, multi-angle context explaining watchdog findings and accountability demands.
    3. DO NOT use content warnings. Start directly with the text/headline.

    PLATFORM SPECIFIC REQUIREMENTS:
    - Threads: Punchy human hook + concise summary + link + max 2 hashtags. STRICTLY under 400 total characters.
    - Facebook: Deep-dive 3-paragraph narrative (Para 1: Human hook, Para 2: Findings, Para 3: Call for justice). Include link & hashtags.
    - Instagram: Deep narrative formatted with clean line breaks, emojis, non-clickable link notice ("🔗 Source Link: [URL]"), and hashtags.

    Output STRICTLY raw valid JSON without markdown code blocks:
    {{
      "threads": "Text for Threads",
      "facebook": "Text for Facebook",
      "instagram": "Text for Instagram"
    }}
    """

    try:
        model = get_active_model()
        response = model.generate_content(prompt)
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(clean_text)

        return {
            "threads": data.get("threads", fallback_threads),
            "facebook": data.get("facebook", fallback_long),
            "instagram": data.get("instagram", fallback_long)
        }, None

    except Exception as e:
        print(f"[!] Gemini generation error: {e}")
        return {
            "threads": fallback_threads,
            "facebook": fallback_long,
            "instagram": fallback_long
        }, str(e)
