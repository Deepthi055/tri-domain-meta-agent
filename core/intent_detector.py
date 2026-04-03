import json
from core.llm_client import call_llm

INTENT_SYSTEM_PROMPT = """You are an intent detection engine inside a 
TriDomain AI system that handles Career, Health, and Finance queries.

Your ONLY job is to analyze a user query and determine which domain(s) 
it belongs to.

DOMAINS:
- career: job switching, skills, interviews, promotions, work stress
- health: BMI, fitness, diet, illness, energy levels, mental health
- finance: savings, debt, salary, investments, budgeting, expenses

RULES:
1. A query can belong to ONE or MULTIPLE domains
2. Look for explicit AND implicit signals
3. Minimum confidence is 0.6 — below that, default to general
4. Never return more than 2 domains

CRITICAL: Respond ONLY with valid JSON in exactly this format:
{
    "domains": ["career"],
    "confidence": 0.92,
    "reasoning": "one line explaining your decision"
}"""

def detect_intent(query: str) -> dict:
    user_message = f"Analyze this query and detect the domain(s): '{query}'"
    result = call_llm(INTENT_SYSTEM_PROMPT, user_message, temperature=0.1)

    if "domains" not in result:
        return {
            "domains": ["general"],
            "confidence": 0.0,
            "reasoning": "Intent detection failed — defaulting to general"
        }

    valid_domains = {"career", "health", "finance", "general"}
    result["domains"] = [
        d for d in result["domains"]
        if d in valid_domains
    ]

    if not result["domains"]:
        result["domains"] = ["general"]

    return result