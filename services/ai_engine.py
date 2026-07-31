import requests
from config import GEMINI_API_KEY

def clean_draft_text(raw_text: str) -> str:
    """Strips internal scratchpad reasoning and extracts strictly the [CW: ...] section."""
    if "[CW:" in raw_text:
        idx = raw_text.rfind("[CW:")
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

def generate_ai_draft(title: str, snippet: str, link: str) -> tuple:
    """Attempts candidate models to generate a clean summary draft.
    Returns (clean_text_or_none, debug_dict).
    """
    models_to_try = get_candidate_models()
    last_debug = {}

    prompt = f"""You are an empathetic, non-partisan human rights advocate.
Title: {title}
Snippet: {snippet}

Task:
Write a neutral 2-sentence summary highlighting the impact on human dignity.
Format STRICTLY as:
[CW: Human Rights Report]
<2-sentence factual summary>

Source: {link}

CRITICAL RULE: Do NOT include any internal reasoning, scratchpad text, or bullet points. Output ONLY the final draft block.
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
