import os
import json
import re
from groq import Groq
from dotenv import load_dotenv

# Force reload .env every time
load_dotenv(override=True)

# Groq replacement for the retired llama-3.3-70b-versatile
MODEL = "openai/gpt-oss-120b"


def get_client():
    """Creates a fresh Groq client every time."""
    load_dotenv(override=True)

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("GROQ_API_KEY not found in .env file")

    return Groq(api_key=api_key)


def extract_json(text: str):
    """Tries multiple strategies to extract JSON from LLM output."""

    if not text:
        return None

    # Strategy 1 — direct JSON parse
    try:
        return json.loads(text.strip())
    except Exception:
        pass

    # Strategy 2 — remove markdown code fences
    try:
        clean = re.sub(r"```json\s*", "", text, flags=re.IGNORECASE)
        clean = re.sub(r"```\s*", "", clean)

        return json.loads(clean.strip())
    except Exception:
        pass

    # Strategy 3 — find first JSON object
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)

        if match:
            return json.loads(match.group())
    except Exception:
        pass

    return None


def call_llm(
    system_prompt: str,
    user_message: str,
    temperature: float = 0.7
) -> dict:
    """
    Shared LLM caller used by all agents.

    Uses Groq's openai/gpt-oss-120b model and requests
    JSON output so the existing agents can consume the result.
    """

    try:
        client = get_client()

        # Tell the model explicitly that JSON is required.
        json_instruction = """
IMPORTANT:
Return ONLY valid JSON.
Do not use Markdown.
Do not use ```json code fences.
Do not include any text before or after the JSON.

The response must be a valid JSON object.
"""

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt + "\n\n" + json_instruction
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            temperature=temperature,
            max_tokens=800,
            response_format={"type": "json_object"}
        )

        raw = response.choices[0].message.content

        parsed = extract_json(raw)

        if parsed is not None:
            return parsed

        # JSON extraction failed — return raw response safely
        return {
            "recommendation": raw.strip() if raw else "",
            "reason": "LLM returned unstructured text",
            "confidence": 0.5
        }

    except Exception as e:
        return {
            "recommendation": "Service temporarily unavailable",
            "reason": str(e),
            "confidence": 0.0
        }