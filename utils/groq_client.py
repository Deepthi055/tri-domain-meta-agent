"""
Wrapper around the existing core/llm_client.py
so teammate's services can import from utils.groq_client
"""
from core.llm_client import call_llm
import json

def call_llm_json(system_prompt: str, user_prompt: str, temperature: float = 0.4) -> dict:
    """
    Calls LLM and returns parsed JSON dict.
    Wrapper around existing call_llm() in core/llm_client.py
    """
    result = call_llm(system_prompt, user_prompt, temperature)
    if isinstance(result, dict):
        return result
    try:
        return json.loads(result)
    except Exception:
        return {
            "recommendation": str(result),
            "reason": "Could not parse response",
            "confidence": 0.5
        }