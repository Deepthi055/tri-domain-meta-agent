"""
Wrapper around existing core/intent_detector.py
"""
from core.intent_detector import detect_intent

def detect_domain(query: str) -> str:
    """
    Returns single domain string for routes/chat.py
    """
    result = detect_intent(query)
    domains = result.get("domains", ["career"])
    return domains[0] if domains else "career"