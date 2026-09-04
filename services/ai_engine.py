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
    """Generates three tailored posts (Threads, Facebook, Instagram) adhering to platform rules."""
    tags_string = " ".join(MASTER_HASHTAGS)

    # Emergency fallbacks if AI processing fails
    fallback_threads = f"[CW: Human Rights Report]\n\n{title}\n\n{snippet[:200]}...\n\nSource: {link}\n\n#HumanRights"
    fallback_long = f"[CW: Human Rights Report]\n\n{title}\n\n{snippet}\n\nSource: {link}\n\n{tags_string}"

    if not GEMINI_API_KEY:
        return {
            "threads": fallback_threads,
            "facebook": fallback_long,
            "instagram": fallback_long
        }, "No API Key"

    model = None
    for model_name in ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']:
        try:
            model = genai.GenerativeModel(model_name)
            break
        except Exception:
            continue

    if not model:
        model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = f"""
    You are an expert human rights journalist and social media growth strategist.
    Write multi-platform posts for this report:
    - Headline: {title}
    - Report Context: {snippet}
    - Link: {link}

    CORE WRITING RULES:
    1. Human POV: Lead with the human impact—who is affected, civil liberty violations, suffering, or community resilience. Avoid dry policy tone.
    2. Detailed Description: Provide deep, multi-angle context explaining what happened, watchdog findings, and accountability demands.

    PLATFORM SPECIFIC REQUIREMENTS:
    - Threads: Punchy human hook + concise summary + link + max 2 hashtags. STRICTLY under 400 total characters.
    - Facebook: Deep-dive 3-paragraph narrative. 
        - Para 1: Human-POV hook & immediate civilian impact.
        - Para 2: In-depth watchdog findings & systemic context.
        - Para 3: Call for justice & international accountability.
        - Include full link and master hashtags.
    - Instagram: Deep narrative similar to Facebook, but formatted with clean line breaks, tasteful emojis for readability, non-clickable link notice ("🔗 Source Link: [URL]"), and hashtag block.

    Output STRICTLY raw valid JSON without markdown code blocks:
    {{
      "threads": "Text for Threads",
      "facebook": "Text for Facebook",
      "instagram": "Text for Instagram"
    }}
    """

    try:
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
