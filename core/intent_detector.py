import math

from core.llm_client import call_llm
from core.safety_layer import (
    DOMAIN_KEYWORDS,
    extract_domain_signals,
    has_keyword,
    normalize_query,
)


def _is_ambiguous_query(query: str) -> bool:
    """Identify short symptom-only queries that need clarification."""
    normalized = query.strip().lower().strip(" .!?")
    return normalized in {"tired", "i am tired", "i'm tired", "i feel tired"}


def calculate_confidence(match_scores: dict) -> float:
    """Calculate confidence from the concentration of domain match scores."""
    domains = ["career", "health", "finance"]
    scores = [
        max(0.0, float(match_scores.get(domain, 0)))
        for domain in domains
    ]
    total = sum(scores)
    if total == 0:
        return 0.0

    probabilities = [score / total for score in scores]
    entropy = -sum(
        probability * math.log(probability)
        for probability in probabilities
        if probability > 0
    )
    confidence = 1 - entropy / math.log(len(domains))
    return round(confidence, 3)


def detect_intent(query: str) -> dict:
    """
    Detects which domain(s) a query belongs to.
    Uses DOMAIN_KEYWORDS and phrase-aware negation handling from safety_layer.
    No duplicate keyword lists.
    """
    query_lower = normalize_query(query)

    if not query_lower:
        return {
            "domains":    ["general"],
            "confidence": 0.0,
            "reasoning":  "Empty query"
        }

    if _is_ambiguous_query(query_lower):
        return {
            "domains": ["general"],
            "confidence": 0.2,
            "ambiguous": True,
            "reasoning": "The query is too vague to select a domain safely",
        }

    # ── Phrase-aware domain extraction with explicit negation handling ──
    active_domains, match_scores, negated_domains = extract_domain_signals(query_lower)
    matched = [d for d in active_domains if match_scores.get(d, 0) > 0]

    # ── No match fallback ─────────────────────────────────────
    if not matched:
        return {
            "domains":    ["general"],
            "confidence": 0.5,
            "reasoning":  "No clear domain detected"
        }

    # ── Sort by match strength ────────────────────────────────
    # Prefer finance when a finance query is tied with career language such as
    # "salary". This keeps investment questions from being routed to career.
    domain_priority = {"finance": 2, "health": 1, "career": 0}
    matched = sorted(
        matched,
        key=lambda d: (match_scores[d], domain_priority.get(d, 0)),
        reverse=True,
    )

    confidence = calculate_confidence(match_scores)

    reasoning = f"Detected domains: {', '.join(matched)} based on keyword matches"

    return {
        "domains":    matched,
        "confidence": confidence,
        "reasoning":  reasoning
    }