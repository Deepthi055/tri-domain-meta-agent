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

import json
from types import SimpleNamespace

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
import agents.finance_agent as finance_agent


def _normalize_risk_appetite(risk: str | None) -> str | None:
    if not risk:
        return None
    mapping = {
        "low": "conservative",
        "medium": "moderate",
        "high": "aggressive",
    }
    return mapping.get(risk.lower(), risk)


def _build_finance_request(
    db: Session,
    user_id: str,
    query: str,
    rag_context: str,
    conversation_messages: list,
) -> SimpleNamespace:
    """Build a fully populated finance agent request from stored profile."""
    general = (
        db.query(UserProfile)
        .filter(UserProfile.user_id == user_id)
        .first()
    )
    finance = (
        db.query(FinanceProfile)
        .filter(FinanceProfile.user_id == user_id)
        .first()
    )

    req = SimpleNamespace()
    req.user_id = user_id
    req.query = query
    req.rag_context = rag_context
    req.conversation_messages = conversation_messages

    if general:
        req.age = general.age

    if finance:
        req.monthly_income = finance.monthly_income
        req.monthly_expenses = finance.monthly_expenses
        req.savings_goal = finance.savings_goal
        req.investments = finance.investments
        req.investment_experience = finance.investment_experience
        req.financial_goals = finance.financial_goals
        req.budget = finance.budget
        req.risk_tolerance = _normalize_risk_appetite(finance.risk_appetite)

        # Parse categorized expenses from budget field
        if finance.budget:
            try:
                parsed = json.loads(finance.budget)
                if isinstance(parsed, dict):
                    req.expenses = {k: float(v) for k, v in parsed.items()}
            except (json.JSONDecodeError, ValueError, TypeError):
                pass

        if not getattr(req, "expenses", None) and finance.monthly_expenses:
            req.expenses = {"total": float(finance.monthly_expenses)}

    return req


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

# Generic fallback system prompt used when intent detector returns 'general'
SYSTEM_PROMPTS["general"] = """
You are a helpful multi-domain advisor. When the user's intent is unclear, provide a concise, balanced response
that covers career, health, and finance as relevant. Prefer asking a clarifying question if necessary.

Respond ONLY as JSON.

{
    "recommendation":"...",
    "reason":"...",
    "confidence":0.75
}
"""


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

    # Finance always uses the tool pipeline — never fall back to generic LLM advice
    if domain == "finance":
        req = _build_finance_request(
            db, user_id, query, rag_context, conversation_messages,
        )
        try:
            response = finance_agent.run(req)
            response["sources"] = list(set(sources))
            return response
        except Exception as exc:
            print(f"[Finance Agent] run failed: {exc}")
            return {
                "recommendation": (
                    "Finance analysis could not be completed. "
                    f"Error: {exc}. Please ensure your finance profile is complete and try again."
                ),
                "reason": str(exc),
                "confidence": 0.0,
                "confidence_level": "Low",
                "sources": list(set(sources)),
                "tools_used": [],
            }

    # Fallback LLM path (career/health/general only)
    response = call_llm_json(
        system_prompt=SYSTEM_PROMPTS[domain],
        user_prompt=final_prompt,
        temperature=0.4,
    )

    response["sources"] = list(set(sources))

    return response