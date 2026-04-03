import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

def call_llm(system_prompt: str, user_message: str, temperature: float = 0.7):
    """
    Shared LLM caller used by all agents.
    Always returns a dict — never crashes the server.
    """
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=temperature,
            max_tokens=500
        )
        raw = response.choices[0].message.content

        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]

        return json.loads(clean)

    except json.JSONDecodeError:
        return {
            "recommendation": raw,
            "reason": "LLM returned unstructured text",
            "confidence": 0.5
        }
    except Exception as e:
        return {
            "recommendation": "Service temporarily unavailable",
            "reason": str(e),
            "confidence": 0.0
        }