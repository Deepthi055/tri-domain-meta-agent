"""
app/utils/groq_client.py

Single shared Groq caller. Always returns a dict (never raises) when used
in JSON mode, and supports plain-text mode for things like memory
extraction where we don't need a JSON envelope.
"""
import json
import re
from typing import Optional

from groq import Groq

from core.config import settings


def get_client() -> Groq:
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set in environment/.env")
    return Groq(api_key=settings.GROQ_API_KEY)


def extract_json(text: str) -> Optional[dict]:
    if not text:
        return None
    try:
        return json.loads(text.strip())
    except Exception:
        pass
    try:
        clean = re.sub(r"```json\s*", "", text)
        clean = re.sub(r"```\s*", "", clean)
        return json.loads(clean.strip())
    except Exception:
        pass
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    return None


def call_llm_json(system_prompt: str, user_message: str, temperature: float = 0.3) -> dict:
    """Call Groq and parse the response as JSON. Falls back gracefully."""
    try:
        client = get_client()
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            max_tokens=900,
        )
        raw = response.choices[0].message.content
        parsed = extract_json(raw)
        if parsed:
            return parsed
        return {"recommendation": raw.strip(), "reason": "Unstructured LLM output", "confidence": 0.5}
    except Exception as e:
        return {"recommendation": "Service temporarily unavailable", "reason": str(e), "confidence": 0.0}


def call_llm_text(system_prompt: str, user_message: str, temperature: float = 0.2) -> str:
    """Call Groq and return raw text — used for memory extraction / report narration."""
    try:
        client = get_client()
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            max_tokens=600,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return ""
