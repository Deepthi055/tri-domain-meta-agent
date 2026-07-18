"""
app/utils/intent_detector.py

Keyword-based domain detection (same approach as the original prototype's
core/intent_detector.py) — fast, dependency-free, and good enough to route
a query to career/health/finance before the LLM call.
"""

KEYWORD_MAP = {
    "career": [
        "job", "work", "career", "skill", "resume", "cv", "interview",
        "promotion", "switch", "role", "hire", "scientist", "developer",
        "engineer", "analyst", "learn", "course", "salary", "linkedin",
        "certification", "placement", "internship", "fresher",
    ],
    "health": [
        "health", "weight", "bmi", "fitness", "exercise", "diet", "sick",
        "doctor", "sleep", "tired", "gym", "calories", "overweight",
        "muscle", "mental", "eat", "food", "nutrition", "workout", "stress",
    ],
    "finance": [
        "money", "saving", "invest", "debt", "loan", "budget", "expense",
        "income", "tax", "emi", "rent", "insurance", "sip", "ppf", "stock",
        "mutual fund", "salary", "bank", "credit", "finance",
    ],
}


def detect_domain(query: str, fallback: str = "career") -> str:
    query_lower = query.lower()
    scores = {
        domain: sum(1 for kw in keywords if kw in query_lower)
        for domain, keywords in KEYWORD_MAP.items()
    }
    best_domain = max(scores, key=scores.get)
    if scores[best_domain] == 0:
        return fallback
    return best_domain
