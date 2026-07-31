import re
import requests
from config import GEMINI_API_KEY

def clean_draft_text(raw_text: str) -> str:
    """Extracts strictly what is inside <POST>...</POST> tags or detects SKIP status."""
    if "<STATUS>SKIP</STATUS>" in raw_text or "SKIP" in raw_text and "<POST>" not in raw_text:
        return "SKIP"

    match = re.search(r"<POST>(.*?)</POST>", raw_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    if "[CW:" in raw_text or "[UPDATE:" in raw_text:
        idx = max(raw_text.find("[CW:"), raw_text.find("[UPDATE:"))
        return raw_text[idx:].strip()
        
    return raw_text.strip()

def get_candidate_models() -> list:
    """Queries Google AI Studio for all generateContent-supported models."""
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    candidates = []
    try:
        res = requests.get(list_url, timeout=10)
        if res.status_code == 200:
            models = res.json().get("models", [])
            for m in models:
                name = m.get("name", "").replace("models/", "")
                methods = m.get("supportedGenerationMethods", [])
                if "generateContent" in methods:
                    if "2.0-flash" in name or "1.5-flash" in name or "gemma" in name:
                        candidates.insert(0, name)
                    else:
                        candidates.append(name)
    except Exception as e:
        print(f"[!] Model Listing Exception: {e}")
    
    if not candidates:
        candidates = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.5-flash"]
    return candidates

def generate_ai_draft(title: str, snippet: str, link: str, recent_topics: list = []) -> tuple:
    """Evaluates candidate article against recent topics for duplicates, updates, or new reports."""
    models_to_try = get_candidate_models()
    last_debug = {}

    # Format recent history for comparison
    history_str = "None"
    if recent_topics:
        history_str = "\n".join([f"- {item.get('headline', '')}: {item.get('draft_text', '')[:100]}..." for item in recent_topics[:15]])

    prompt = f"""You are an objective, empathetic global human rights advocate focused on universal human dignity, civilian safety, and fundamental rights.

NEW ARTICLE TO EVALUATE:
Title: {title}
Snippet: {snippet}
Source URL: {link}

RECENTLY COVERED TOPICS (Last 15 Posts):
{history_str}

EVALUATION RULES:
1. **DUPLICATE CHECK**: If this new article covers the EXACT SAME event already present in RECENTLY COVERED TOPICS with NO meaningful new facts or updates, reply strictly with:
<STATUS>SKIP</STATUS>

2. **UPDATE CHECK**: If this article reports a SIGNIFICANT NEW DEVELOPMENT/UPDATE on a previously covered story, format as an update:
<POST>
[UPDATE: Human Rights Report]
<2-sentence update highlighting the new development and human impact>

Source: {link}
#HumanRights #HumanDignity
</POST>

3. **NEW STORY**: If this article is a completely new story/event not covered in the list:
<POST>
[CW: Human Rights Report]
<2-sentence factual, empathetic summary focused on human dignity and civilian safety>

Source: {link}
#HumanRights #HumanDignity
</POST>

STRICT CONSTRAINTS:
- Keep the final post under 450 characters.
- Stay neutral, objective, and non-partisan. Do NOT target or generalize any religion, community, or region.
- Output ONLY the <STATUS>SKIP</STATUS> tag or the <POST>...</POST> block. No extra commentary.
"""

    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        try:
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15)
            
            if res.status_code == 200:
                data = res.json()
                if "candidates" in data and len(data["candidates"]) > 0:
                    raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                    final_draft = clean_draft_text(raw_text)
                    return final_draft, {"status_code": 200, "active_model": model_name}
            else:
                last_debug = {"status_code": res.status_code, "attempted_model": model_name, "error_body": res.text}
        except Exception as e:
            last_debug = {"status_code": "exception", "attempted_model": model_name, "error_message": str(e)}

    return None, last_debug
