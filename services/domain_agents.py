"""
app/services/domain_agents.py

Runs the appropriate domain expert (career/health/finance).

Pipeline:
User Query
      ↓
Profile Context
      ↓
Memory Context
      ↓
Conversation History
      ↓
Retrieve Knowledge Base Chunks (RAG)
      ↓
Groq LLM
      ↓
Structured JSON Response
"""

from sqlalchemy.orm import Session

from services.context_builder import (
    build_profile_context,
    build_memory_context,
)
from services.conversation_service import format_history_for_prompt

from rag.retriever import retrieve

from utils.groq_client import call_llm_json
from utils.calculators import (
    calculate_bmi,
    calculate_savings,
    calculate_debt_ratio,
    skill_gap_analyzer,
)

from models.profile import (
    UserProfile,
    CareerProfile,
    FinanceProfile,
    HealthProfile,
)


SYSTEM_PROMPTS = {
    "career": """
You are an expert Career Advisor.

Use:
- User profile
- Long-term memory
- Conversation history
- Retrieved career knowledge

Give practical advice.

Respond ONLY as JSON.

{
    "recommendation":"...",
    "reason":"...",
    "confidence":0.92
}
""",

    "health": """
You are an expert Health Advisor.

Use:
- User profile
- BMI
- Sleep
- Fitness goals
- Retrieved health knowledge

Never diagnose diseases.

Respond ONLY as JSON.

{
    "recommendation":"...",
    "reason":"...",
    "confidence":0.90
}
""",

    "finance": """
You are an expert Personal Finance Advisor.

Use:
- Income
- Expenses
- Savings
- User goals
- Retrieved finance knowledge

Do not recommend risky investments.

Respond ONLY as JSON.

{
    "recommendation":"...",
    "reason":"...",
    "confidence":0.91
}
"""
}


def build_metrics(db: Session, user_id: str, domain: str) -> str:
    """
    Runs deterministic calculations before sending prompt to LLM.
    """

    if domain == "career":
        profile = (
            db.query(CareerProfile)
            .filter(CareerProfile.user_id == user_id)
            .first()
        )

        if profile and profile.target_role:
            result = skill_gap_analyzer(
                profile.current_skills or [],
                profile.target_role,
            )

            if "error" not in result:
                return (
                    f"Skill Match: {result['match_percentage']}%\n"
                    f"Missing Skills: {', '.join(result['missing_skills'])}"
                )

    elif domain == "health":

        general = (
            db.query(UserProfile)
            .filter(UserProfile.user_id == user_id)
            .first()
        )

        if (
            general
            and general.height_cm
            and general.weight_kg
        ):
            bmi = calculate_bmi(
                general.weight_kg,
                general.height_cm,
            )

            return (
                f"BMI = {bmi['bmi']}\n"
                f"Category = {bmi['category']}"
            )

    elif domain == "finance":

        profile = (
            db.query(FinanceProfile)
            .filter(FinanceProfile.user_id == user_id)
            .first()
        )

        if profile and profile.monthly_income:

            savings = calculate_savings(
                profile.monthly_income,
                profile.monthly_expenses or 0,
            )

            debt = calculate_debt_ratio(
                profile.monthly_income,
                profile.monthly_expenses or 0,
            )

            return (
                f"Monthly Savings = ₹{savings['savings']}\n"
                f"Savings Rate = {savings['rate_pct']}%\n"
                f"Debt Ratio = {debt['debt_to_income_ratio']}\n"
                f"Debt Status = {debt['status']}"
            )

    return ""


def run_domain_agent(
    db: Session,
    user_id: str,
    domain: str,
    query: str,
    conversation_messages: list,
):
    """
    Returns

    {
        recommendation,
        reason,
        confidence,
        sources
    }
    """

    profile_context = build_profile_context(
        db,
        user_id,
        domain,
    )

    memory_context = build_memory_context(
        db,
        user_id,
        domain,
    )

    history_context = format_history_for_prompt(
        conversation_messages
    )

    metrics = build_metrics(
        db,
        user_id,
        domain,
    )

    retrieved_chunks = retrieve(
        query=query,
        domain=domain,
        top_k=3,
    )

    rag_context = ""

    sources = []

    for chunk in retrieved_chunks:

        rag_context += chunk["text"] + "\n\n"

        sources.append(chunk["source"])

    final_prompt = f"""
USER PROFILE
-------------
{profile_context}

LONG TERM MEMORY
----------------
{memory_context}

CONVERSATION HISTORY
--------------------
{history_context}

CALCULATED METRICS
------------------
{metrics}

KNOWLEDGE BASE
--------------
{rag_context}

USER QUESTION
-------------
{query}
"""

    response = call_llm_json(
        system_prompt=SYSTEM_PROMPTS[domain],
        user_prompt=final_prompt,
        temperature=0.4,
    )

    response["sources"] = list(set(sources))

    return response