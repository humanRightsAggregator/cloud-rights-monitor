import json
import google.generativeai as genai
from config import GEMINI_API_KEY

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"[!] Gemini config warning: {e}")

MASTER_HASHTAGS = ["#HumanRights", "#HumanDignity", "#JusticeNow"]

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

    for candidate in ['gemini-2.0-flash', 'gemini-1.5-flash-latest']:
        try:
            return genai.GenerativeModel(candidate)
        except Exception:
            continue

    return genai.GenerativeModel('gemini-2.0-flash')

def generate_ai_draft(title: str, snippet: str, link: str, recent_topics: list) -> tuple:
    fallback_threads = f"{title}\n\n{snippet[:200]}...\n\nSource: {link}\n\n#HumanRights"
    fallback_long = f"{title}\n\n{snippet}\n\nSource: {link}\n\n#HumanRights #HumanDignity #JusticeNow"

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
    3. DYNAMIC HASHTAG EXTRACTION: Analyze the story context and extract specific entity hashtags based on:
       - Locations/Countries (e.g., #Austria, #Israel, #Palestine, #Sudan, #Haiti)
       - Key Entities/Organizations (e.g., #UEFA, #AmnestyInternational, #UN, #CPJ, #UNHCR)
       - Specific Human Rights Themes (e.g., #FreePress, #RefugeeRights, #ProtestRights, #EndGenocide)

    PLATFORM HASHTAG & POLICY CONSTRAINTS:
    - Threads: Max 400 total characters. Clean hook + summary + link + EXACTLY 1-2 hashtags (e.g., #HumanRights + 1 primary topic/country tag).
    - Facebook: Deep-dive 3-paragraph narrative (Para 1: Human hook, Para 2: Findings, Para 3: Call for justice). End with full link and 3-4 targeted hashtags combining country, key organization, and broad theme.
    - Instagram: Deep narrative formatted with clean line breaks, tasteful emojis, non-clickable link notice ("🔗 Source Link: [URL]"), and a block of 5-7 targeted hashtags at the very bottom (combining specific story tags + #HumanRights #HumanDignity #JusticeNow).

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
