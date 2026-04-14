BLOCKED_KEYWORDS = [
    # Violence
    "hurt", "kill", "harm", "attack", "weapon", "bomb", "poison",
    # Illegal financial
    "money laundering", "tax evasion", "insider trading",
    "fake invoice", "bribe", "black money",
  
    # Fraud
    "fake resume", "fake certificate", "fake degree",
    "fake my resume", "fake the resume", "falsify resume",
    "cheat", "plagiarize", "forge", "fabricate",
    "lie on resume", "lie in resume", "lie about experience",
    # Self harm
    "suicide", "self harm", "end my life", "kill myself",
    # Hate
    "hate", "racist", "discriminate"
]

SENSITIVE_TOPICS = [
    "depression", "anxiety", "mental health",
    "burnout", "overwhelmed", "hopeless"
]

DOMAIN_KEYWORDS = {
    "career": [
        "job", "work", "career", "skill", "resume", "cv",
        "interview", "promotion", "switch", "role", "hire",
        "scientist", "developer", "engineer", "analyst",
        "learn", "course", "salary", "linkedin", "data science",
        "placement", "internship", "fresher", "experience"
    ],
    "health": [
        "health", "weight", "bmi", "fitness", "exercise",
        "diet", "sick", "doctor", "sleep", "tired", "gym",
        "calories", "overweight", "fat", "muscle", "mental",
        "eat", "food", "nutrition", "lose weight", "gain weight",
        "workout", "stress", "anxiety", "mood"
    ],
    "finance": [
        "money", "saving", "invest", "debt", "loan", "budget",
        "expense", "income", "tax", "emi", "rent", "insurance",
        "sip", "ppf", "stock", "mutual fund", "earning",
        "spend", "finance", "bank", "credit", "debit", "salary"
    ]
}


def check_safety(query: str) -> dict:
    """
    Checks query against blocked keywords and sensitive topics.
    Returns:
        is_safe      → True if query can proceed
        is_sensitive → True if needs careful handling
        reason       → why it was blocked
        message      → message to show user
    """
    query_lower = query.lower()

    # Hard block — never proceed
    for keyword in BLOCKED_KEYWORDS:
        if keyword in query_lower:
            return {
                "is_safe":      False,
                "is_sensitive": False,
                "reason":       f"Query contains restricted content: '{keyword}'",
                "message":      "I can only help with Career, Health, and Finance queries. Please rephrase your question."
            }

    # Sensitive — proceed but flag it
    for topic in SENSITIVE_TOPICS:
        if topic in query_lower:
            return {
                "is_safe":      True,
                "is_sensitive": True,
                "reason":       f"Sensitive topic detected: '{topic}'",
                "message":      "I noticed your query touches on a sensitive topic. I will do my best to help, but please consult a professional for personal support."
            }

    # All clear
    return {
        "is_safe":      True,
        "is_sensitive": False,
        "reason":       None,
        "message":      None
    }


def check_relevance(query: str) -> dict:
    """
    Checks if query is related to Career, Health, or Finance.
    Blocks completely off-topic queries.
    """
    query_lower = query.lower()
    matched     = []

    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(kw in query_lower for kw in keywords):
            matched.append(domain)

    if not matched:
        return {
            "is_relevant":     False,
            "matched_domains": [],
            "message":         "Your query does not seem related to Career, Health, or Finance. Please ask something in one of these areas."
        }

    return {
        "is_relevant":     True,
        "matched_domains": matched,
        "message":         None
    }