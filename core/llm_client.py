import os
import json
import re
from groq import Groq
from dotenv import load_dotenv

# Force reload .env every time
load_dotenv(override=True)

MODEL = "llama-3.3-70b-versatile"


def get_client():
    """Creates a fresh Groq client every time — avoids stale key issues."""
    load_dotenv(override=True)
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in .env file")
    return Groq(api_key=api_key)


def extract_json(text: str):
    """Tries multiple strategies to extract JSON from LLM output."""
    if not text:
        return None

    # Strategy 1 — direct parse
    try:
        return json.loads(text.strip())
    except:
        pass

    # Strategy 2 — strip markdown fences
    try:
        clean = re.sub(r'```json\s*', '', text)
        clean = re.sub(r'```\s*', '', clean)
        return json.loads(clean.strip())
    except:
        pass

    # Strategy 3 — find first { } block
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except:
        pass

    return None


def call_llm(system_prompt: str, user_message: str, temperature: float = 0.7) -> dict:
    """
    Shared LLM caller used by all agents.
    Always returns a dict — never crashes the server.
    """
    try:
        client   = get_client()
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message}
            ],
            temperature=temperature,
            max_tokens=800
        )

        raw    = response.choices[0].message.content
        parsed = extract_json(raw)

        if parsed:
            return parsed

        # JSON extraction failed — return raw text
        return {
            "recommendation": raw.strip(),
            "reason": "LLM returned unstructured text",
            "confidence": 0.5
        }

    except Exception as e:
        return {
            "recommendation": "Service temporarily unavailable",
            "reason": str(e),
            "confidence": 0.0
        }