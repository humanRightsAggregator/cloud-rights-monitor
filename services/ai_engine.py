import json
import google.generativeai as genai
from config import GEMINI_API_KEY

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"[!] Gemini config warning: {e}")

MASTER_HASHTAGS = ["#HumanRights", "#HumanDignity", "#JusticeNow", "#RightsWatch"]

def get_available_model():
    """Dynamically retrieves an active, supported Gemini model for this API key."""
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                model_id = m.name.replace('models/', '')
                # Prioritize Flash models
                if 'flash' in model_id:
                    return genai.GenerativeModel(model_id)
    except Exception as e:
        print(f"[!] Dynamic model lookup notice: {e}")

    # Active production fallbacks
    for candidate in ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-2.5-flash-lite']:
        try:
            return genai.GenerativeModel(candidate)
        except Exception:
            continue

    return genai.GenerativeModel('gemini-2.5-flash')

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
    1. Human POV: Lead with the human impact—who is affected, civil liberty violations, suffering, or community resilience. Avoid dry policy tone.
    2. Detailed Description: Provide deep, multi-angle context explaining what happened, watchdog findings, and accountability demands.
    3. DO NOT use content warnings like "[CW: Human Rights Report]". Start directly with the text/headline.

    PLATFORM SPECIFIC REQUIREMENTS:
    - Threads: Punchy human hook + concise summary + link + max 2 hashtags. STRICTLY under 400 total characters.
    - Facebook: Deep-dive 3-paragraph narrative. 
        - Para 1: Human-POV hook & immediate civilian impact.
        - Para 2: In-depth watchdog findings & systemic context.
        - Para 3: Call for justice & international accountability.
        - Include full link and master hashtags.
    - Instagram: Deep narrative similar to Facebook, formatted with clean line breaks, tasteful emojis, non-clickable link notice ("🔗 Source Link: [URL]"), and hashtag block.

    Output STRICTLY raw valid JSON without markdown code blocks:
    {{
      "threads": "Text for Threads",
      "facebook": "Text for Facebook",
      "instagram": "Text for Instagram"
    }}
    """

    try:
        model = get_available_model()
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
