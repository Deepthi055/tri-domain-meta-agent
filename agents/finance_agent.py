"""
agents/finance_agent.py
-----------------------
Finance domain specialist for the TriDomain Meta-Agent system.

Pipeline:
  1. Load user finance profile (mandatory)
  2. Detect query intent → select LangChain tool(s)
  3. Execute tool(s) — all calculations happen here, NOT in the LLM
  4. Build structured response with calculation steps
  5. LLM formats the pre-computed output (no math allowed in LLM)
"""

from __future__ import annotations

import json
import logging
import math
import re
from typing import Any

from core.llm_client import call_llm
from tools.calculators import calculate_debt_ratio, calculate_savings
from tools.finance_tools import (
    budget_planner,
    debt_management,
    financial_analysis,
    investment_analysis,
    retirement_planner,
    savings_calculator,
    tax_optimizer,
)

try:
    from core.database import SessionLocal
    from models.profile import FinanceProfile, UserProfile
    DB_AVAILABLE = True
except Exception:
    DB_AVAILABLE = False

try:
    from rag.finance_retriever import retrieve_as_context
    RAG_AVAILABLE = True
except Exception:
    RAG_AVAILABLE = False

logger = logging.getLogger("finance_agent")

# ── Tool display names (LangChain tool labels) ────────────────────────────────

TOOL_LABELS: dict[str, str] = {
    "budget":             "Budget Planner",
    "savings":            "Savings Calculator",
    "investment":         "Investment Recommendation Tool",
    "debt":               "Debt Management Tool",
    "retirement":         "Retirement Planner",
    "tax":                "Tax Calculator",
    "financial_analysis": "Financial Analysis Tool",
}

# ── Intent keywords ───────────────────────────────────────────────────────────

_TOOL_KEYWORDS: dict[str, list[str]] = {
    "budget": [
        "budget", "spend", "expense", "afford", "monthly budget",
        "create a budget", "spending",
    ],
    "savings": [
        "savings goal", "saving goal", "how much to save", "how long to save",
        "saving", "how long", "achieve my goal", "time to goal", "months to",
        "reach my goal", "save for", "save up", "save money",
    ],
    "investment": [
        "invest", "portfolio", "stock", "equity", "mutual fund", "sip",
        "asset", "allocat", "rebalanc", "ppf", "nps", "elss",
    ],
    "debt": [
        "debt", "loan", "emi", "credit card", "borrow", "repay",
        "owe", "pay off", "liability",
    ],
    "retirement": [
        "retire", "retirement", "pension", "corpus", "old age",
        "when can i retire", "epf", "retirement age", "save for retirement",
    ],
    "tax": [
        "tax", "itr", "deduction", "80c", "80d", "regime", "tds",
        "income tax", "refund",
    ],
    "financial_analysis": [
        "strength", "weakness", "financial health", "financial advice",
        "advice based on my profile", "financial strengths",
        "strengths and weaknesses", "overall finance", "my profile",
        "which profile", "which langchain tool", "which tool",
        "show every calculation", "calculation used",
    ],
}

# Profile fields required for meaningful advice
CORE_PROFILE_FIELDS = [
    "monthly_income",
    "monthly_expenses",
]

EXTENDED_PROFILE_FIELDS = [
    "savings_goal",
    "risk_tolerance",
    "investment_experience",
    "financial_goals",
    "investments",
]

# Required profile fields per tool (validated before execution)
_TOOL_REQUIRED_FIELDS: dict[str, list[str]] = {
    "budget":             ["monthly_income", "monthly_expenses"],
    "savings":            ["monthly_income", "monthly_expenses"],
    "debt":               ["total_debt", "monthly_debt_payment"],
    "retirement":         ["age", "monthly_expenses"],
    "tax":                ["monthly_income"],
    "investment":         ["age", "risk_tolerance"],
    "financial_analysis": ["monthly_income", "monthly_expenses"],
}

_TOOL_FIELD_LABELS: dict[str, str] = {
    "monthly_income":       "Monthly income",
    "monthly_expenses":     "Monthly expenses",
    "total_debt":           "Total debt",
    "monthly_debt_payment": "Current monthly repayment",
    "age":                  "Age",
    "savings_goal":         "Savings goal",
    "risk_tolerance":       "Risk tolerance",
    "portfolio":            "Portfolio values",
}

_MISSING_FIELD_MESSAGES: dict[str, str] = {
    "debt": (
        "I don't have your debt information yet.\n"
        "Please provide:\n"
        "• Total debt\n"
        "• Current monthly repayment"
    ),
    "retirement": (
        "I need more information to estimate retirement.\n"
        "Please provide:\n"
        "• Your age\n"
        "• Monthly expenses\n"
        "• Monthly retirement contribution (optional: current retirement savings)"
    ),
    "investment": (
        "I need your investment profile to give allocation advice.\n"
        "Please provide:\n"
        "• Age\n"
        "• Risk tolerance\n"
        "• Current portfolio values (equity, debt, gold, cash)"
    ),
    "savings": (
        "I need your savings goal to calculate time-to-goal.\n"
        "Please provide:\n"
        "• Savings goal amount"
    ),
}

LLM_FORMATTER_PROMPT = """You are a finance response formatter inside the TriDomain AI system.

CRITICAL RULES:
1. You MUST NOT perform any calculations — all numbers are pre-computed below.
2. You MUST NOT give generic advice like "increase savings" or "reduce expenses"
   without citing the exact ₹ amounts provided.
3. Use ONLY the profile values and tool outputs given to you.
4. Format the recommendation with these sections (use bullet headers):
   • Profile Data Used
   • LangChain Tool Used
   • Calculation Steps
   • Recommendation
   • Confidence Level (High/Medium/Low)

Respond ONLY with valid JSON — no markdown fences:
{
    "recommendation": "full formatted response with all sections above",
    "reason": "one sentence on why this advice fits this user",
    "confidence": 0.88
}"""


# ── Profile helpers ───────────────────────────────────────────────────────────

def _normalize_risk(risk: str | None) -> str:
    """Map profile risk_appetite values to tool enum."""
    if not risk:
        return "moderate"
    mapping = {
        "low": "conservative", "conservative": "conservative",
        "medium": "moderate", "moderate": "moderate",
        "high": "aggressive", "aggressive": "aggressive",
    }
    return mapping.get(risk.lower().strip(), "moderate")


def _parse_budget(budget_str: str | None, monthly_expenses: float | None) -> dict[str, float]:
    """Parse budget profile field — JSON dict or fallback to total."""
    if budget_str:
        try:
            parsed = json.loads(budget_str)
            if isinstance(parsed, dict):
                return {k: float(v) for k, v in parsed.items()}
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
    if monthly_expenses:
        return {"total": float(monthly_expenses)}
    return {}


def _parse_portfolio(request: Any) -> dict[str, float]:
    """Return portfolio only when explicit values are provided — never estimate."""
    portfolio = getattr(request, "portfolio", None)
    if isinstance(portfolio, dict) and portfolio:
        return {k: float(v) for k, v in portfolio.items() if v is not None}
    return {}


def _savings_goal_mode(query: str) -> str:
    """Corpus goal for time-to-goal queries; monthly target otherwise."""
    q = query.lower()
    if any(kw in q for kw in ("how long", "time to", "months to", "achieve my goal", "reach my goal")):
        return "corpus"
    return "monthly"


def _get_total_debt(request: Any) -> float | None:
    """Resolve total debt from explicit debts list or total_debt field."""
    total_debt = getattr(request, "total_debt", None)
    if total_debt is not None and float(total_debt) > 0:
        return float(total_debt)
    debts = getattr(request, "debts", None) or []
    if debts:
        return sum(float(d.get("balance", 0) or 0) for d in debts)
    return None


def _wants_50_30_20_rule(query: str) -> bool:
    q = query.lower()
    return any(p in q for p in ("50-30-20", "50/30/20", "503020", "50 30 20", "fifty-thirty-twenty"))


def _resolve_field(request: Any, field: str) -> Any:
    """Resolve a logical required field from the request object."""
    if field == "total_debt":
        return _get_total_debt(request)
    if field == "monthly_debt_payment":
        val = getattr(request, "monthly_debt_payment", None)
        return float(val) if val is not None and float(val) > 0 else None
    if field == "portfolio":
        pf = _parse_portfolio(request)
        return pf if pf else None
    if field == "risk_tolerance":
        return getattr(request, "risk_tolerance", None) or getattr(request, "risk_appetite", None)
    return getattr(request, field, None)


def _validate_tool_fields(
    tool: str,
    request: Any,
    query: str,
) -> tuple[list[str], dict[str, Any]]:
    """
    Validate tool-specific required fields.
    Returns (missing_field_keys, resolved_values_used).
    """
    required = list(_TOOL_REQUIRED_FIELDS.get(tool, []))
    if tool == "savings" and _savings_goal_mode(query) == "corpus":
        if "savings_goal" not in required:
            required.append("savings_goal")

    missing: list[str] = []
    values: dict[str, Any] = {}

    for field in required:
        val = _resolve_field(request, field)
        values[field] = val
        if val is None:
            missing.append(field)
        elif isinstance(val, (int, float)) and val <= 0 and field not in ("monthly_debt_payment",):
            if field == "age":
                missing.append(field)
            elif field not in ("savings_goal", "monthly_debt_payment"):
                missing.append(field)

    return missing, values


def _load_profile_from_db(user_id: str, request: Any) -> None:
    """Fill missing request fields from stored profile."""
    if not DB_AVAILABLE or not user_id:
        return
    db = SessionLocal()
    try:
        stored = db.query(FinanceProfile).filter(FinanceProfile.user_id == user_id).first()
        general = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

        if stored:
            field_map = {
                "monthly_income": "monthly_income",
                "monthly_expenses": "monthly_expenses",
                "savings_goal": "savings_goal",
                "investments": "investments",
                "investment_experience": "investment_experience",
                "financial_goals": "financial_goals",
                "budget": "budget",
            }
            for db_field, req_field in field_map.items():
                if not getattr(request, req_field, None):
                    val = getattr(stored, db_field, None)
                    if val is not None:
                        setattr(request, req_field, val)
            if not getattr(request, "risk_tolerance", None):
                setattr(request, "risk_tolerance", getattr(stored, "risk_appetite", None))

        if general and not getattr(request, "age", None):
            setattr(request, "age", getattr(general, "age", None))
    finally:
        try:
            db.close()
        except Exception:
            pass


def _extract_profile(request: Any) -> tuple[dict[str, Any], list[str]]:
    """Return profile values dict and list of missing core fields."""
    income = getattr(request, "monthly_income", None)
    expenses = getattr(request, "monthly_expenses", None)

    profile = {
        "monthly_income": income,
        "monthly_expenses": expenses,
        "savings_goal": getattr(request, "savings_goal", None),
        "investments": getattr(request, "investments", None),
        "risk_tolerance": getattr(request, "risk_tolerance", None) or getattr(request, "risk_appetite", None),
        "investment_experience": getattr(request, "investment_experience", None),
        "financial_goals": getattr(request, "financial_goals", None),
        "age": getattr(request, "age", None),
    }

    missing = [f for f in CORE_PROFILE_FIELDS if profile.get(f) is None]
    return profile, missing


def _format_inr(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"₹{value:,.0f}"


# ── Intent detection ──────────────────────────────────────────────────────────

# Tie-break order when keyword scores are equal
_TOOL_PRIORITY = [
    "debt",
    "tax",
    "retirement",
    "investment",
    "budget",
    "savings",
    "financial_analysis",
]

_META_PATTERNS = [
    r"which (profile|langchain|tool)",
    r"show (every|all) calculation",
    r"what (profile|values) did you use",
]


def _detect_tools(query: str) -> list[str]:
    """Return exactly one primary tool for the query."""
    q = query.lower()

    if any(re.search(p, q) for p in _META_PATTERNS):
        return ["financial_analysis"]

    matched: list[str] = []
    for tool, keywords in _TOOL_KEYWORDS.items():
        if any(kw in q for kw in keywords):
            matched.append(tool)

    if not matched:
        return ["financial_analysis"]

    for tool in _TOOL_PRIORITY:
        if tool in matched:
            return [tool]

    return [matched[0]]


# ── Tool runners ──────────────────────────────────────────────────────────────

def _run_budget(request: Any) -> dict:
    expenses = getattr(request, "expenses", None) or _parse_budget(
        getattr(request, "budget", None),
        getattr(request, "monthly_expenses", None),
    )
    if not expenses and hasattr(request, "monthly_expenses"):
        expenses = {"total": float(request.monthly_expenses or 0)}

    result = budget_planner(
        income=float(getattr(request, "monthly_income", 0)),
        expenses=expenses,
    )
    # Append explicit calculation steps
    income = float(getattr(request, "monthly_income", 0))
    total_exp = result.get("total_expenses", 0)
    disposable = result.get("disposable_income", 0)
    steps = [
        f"Income = {_format_inr(income)}",
        f"Total Expenses = {_format_inr(total_exp)}",
        "",
        "Disposable Income",
        f"= {_format_inr(income)} − {_format_inr(total_exp)}",
        f"= {_format_inr(disposable)}",
        "",
        f"Savings Rate = ({disposable:,.0f} / {income:,.0f}) × 100 = {result.get('savings_rate_pct', 0)}%",
    ]
    result["calculation_steps"] = steps
    return result


def _savings_goal_mode(query: str) -> str:
    """Corpus goal for time-to-goal queries; monthly target otherwise."""
    q = query.lower()
    if any(kw in q for kw in ("how long", "time to", "months to", "achieve my goal", "reach my goal")):
        return "corpus"
    return "monthly"


def _run_savings(request: Any) -> dict:
    query = getattr(request, "query", "") or ""
    return savings_calculator(
        income=float(getattr(request, "monthly_income", 0)),
        expenses=float(getattr(request, "monthly_expenses", 0)),
        savings_goal=getattr(request, "savings_goal", None),
        current_savings=float(getattr(request, "current_savings", 0) or 0),
        goal_mode=_savings_goal_mode(query),
    )


def _run_investment(request: Any) -> dict:
    portfolio = getattr(request, "portfolio", None) or _parse_investments(
        getattr(request, "investments", None),
        getattr(request, "monthly_income", None),
    )
    return investment_analysis(
        portfolio=portfolio,
        risk_tolerance=_normalize_risk(getattr(request, "risk_tolerance", None)),
        age=int(getattr(request, "age", 30) or 30),
    )


def _run_debt(request: Any) -> dict:
    debts = getattr(request, "debts", None) or []
    monthly_payment = float(getattr(request, "monthly_debt_payment", 0) or 0)

    if not debts:
        income = float(getattr(request, "monthly_income", 0) or 0)
        expenses = float(getattr(request, "monthly_expenses", 0) or 0)
        surplus = max(0, income - expenses)
        return {
            "note": (
                "No debt breakdown in your profile. To analyse debt payoff, "
                "add debts with name, balance, interest_rate, and min_payment."
            ),
            "available_for_debt_payment": surplus,
            "calculation_steps": [
                f"Income = {_format_inr(income)}",
                f"Expenses = {_format_inr(expenses)}",
                f"Available for debt (surplus) = {_format_inr(surplus)}",
            ],
        }

    if monthly_payment <= 0:
        income = float(getattr(request, "monthly_income", 0) or 0)
        expenses = float(getattr(request, "monthly_expenses", 0) or 0)
        monthly_payment = max(0, (income - expenses) * 0.5)

    return debt_management(debts=debts, monthly_payment=monthly_payment)


def _run_retirement(request: Any) -> dict:
    current_age = int(getattr(request, "age", 30) or 30)
    retirement_age = int(getattr(request, "retirement_age", 60) or 60)
    savings = float(getattr(request, "retirement_savings", 0) or getattr(request, "current_savings", 0) or 0)
    monthly_contrib = float(getattr(request, "monthly_contribution", 0) or 0)

    if monthly_contrib <= 0:
        income = float(getattr(request, "monthly_income", 0) or 0)
        expenses = float(getattr(request, "monthly_expenses", 0) or 0)
        monthly_contrib = max(0, (income - expenses) * 0.20)

    result = retirement_planner(
        current_age=current_age,
        retirement_age=retirement_age,
        savings=savings,
        monthly_contribution=monthly_contrib,
    )
    if "error" not in result:
        years = result.get("years_to_retirement", 0)
        steps = [
            f"Current Age = {current_age}",
            f"Retirement Age = {retirement_age}",
            f"Years to Retirement = {years}",
            f"Current Savings = {_format_inr(savings)}",
            f"Monthly Contribution = {_format_inr(monthly_contrib)}",
            f"Projected Corpus = {_format_inr(result.get('projected_corpus'))}",
            f"Corpus Needed = {_format_inr(result.get('corpus_needed'))}",
            f"Gap/Surplus = {_format_inr(result.get('gap_or_surplus'))}",
        ]
        result["calculation_steps"] = steps
    return result


def _run_tax(request: Any) -> dict:
    annual_income = float(getattr(request, "annual_income", 0) or 0)
    if annual_income <= 0:
        monthly = float(getattr(request, "monthly_income", 0) or 0)
        annual_income = monthly * 12

    deductions: dict[str, float] = getattr(request, "tax_deductions", None) or {}
    result = tax_optimizer(income=annual_income, deductions=deductions)
    if "error" not in result:
        old_tax = result.get("old_regime", {}).get("tax_liability", 0)
        new_tax = result.get("new_regime", {}).get("tax_liability", 0)
        steps = [
            f"Annual Income = {_format_inr(annual_income)}",
            f"Old Regime Tax = {_format_inr(old_tax)}",
            f"New Regime Tax = {_format_inr(new_tax)}",
            f"Recommended Regime = {result.get('recommended_regime', 'N/A').upper()}",
            f"Tax Savings = {_format_inr(result.get('tax_savings_vs_other'))}",
        ]
        result["calculation_steps"] = steps
    return result


def _run_financial_analysis(request: Any) -> dict:
    return financial_analysis(
        income=float(getattr(request, "monthly_income", 0)),
        expenses=float(getattr(request, "monthly_expenses", 0)),
        savings_goal=getattr(request, "savings_goal", None),
        risk_tolerance=_normalize_risk(getattr(request, "risk_tolerance", None)),
        investment_experience=getattr(request, "investment_experience", "beginner") or "beginner",
        financial_goals=getattr(request, "financial_goals", None),
    )


_TOOL_RUNNERS = {
    "budget":             _run_budget,
    "savings":            _run_savings,
    "investment":         _run_investment,
    "debt":               _run_debt,
    "retirement":         _run_retirement,
    "tax":                _run_tax,
    "financial_analysis": _run_financial_analysis,
}


# ── Response builders ─────────────────────────────────────────────────────────

def _confidence_level(profile: dict, missing: list[str], tool_outputs: dict) -> tuple[str, float]:
    """Return (High/Medium/Low label, numeric confidence)."""
    if missing:
        return "Low", 0.45
    errors = sum(1 for v in tool_outputs.values() if isinstance(v, dict) and v.get("error"))
    if errors:
        return "Low", 0.50
    has_core = profile.get("monthly_income") and profile.get("monthly_expenses")
    has_extended = any(profile.get(f) for f in EXTENDED_PROFILE_FIELDS)
    if has_core and has_extended:
        return "High", 0.92
    if has_core:
        return "Medium", 0.78
    return "Low", 0.55


def _build_deterministic_response(
    profile: dict,
    missing: list[str],
    active_tools: list[str],
    tool_outputs: dict,
    confidence_label: str,
) -> str:
    """Build fully structured recommendation from tool outputs — no generic advice."""
    lines: list[str] = []

    # Profile Data Used
    lines.append("Profile Data Used:")
    for key, val in profile.items():
        if val is not None:
            label = key.replace("_", " ").title()
            if isinstance(val, (int, float)) and key in ("monthly_income", "monthly_expenses", "savings_goal"):
                lines.append(f"  {label}: {_format_inr(float(val))}")
            else:
                lines.append(f"  {label}: {val}")
    if missing:
        lines.append(f"  Missing fields: {', '.join(missing)}")

    # LangChain Tool Used
    lines.append("")
    lines.append("LangChain Tool Used:")
    for tool in active_tools:
        lines.append(f"  • {TOOL_LABELS.get(tool, tool)}")

    # Calculation Steps
    lines.append("")
    lines.append("Calculation Steps:")
    for tool in active_tools:
        out = tool_outputs.get(tool, {})
        steps = out.get("calculation_steps")
        if steps:
            lines.append(f"  [{TOOL_LABELS.get(tool, tool)}]")
            for step in steps:
                lines.append(f"    {step}" if step else "")
        elif out.get("summary"):
            lines.append(f"  [{TOOL_LABELS.get(tool, tool)}] {out['summary']}")
        elif out.get("note"):
            lines.append(f"  [{TOOL_LABELS.get(tool, tool)}] {out['note']}")

    # Recommendation — from primary tool
    primary = active_tools[0]
    primary_out = tool_outputs.get(primary, {})
    rec = primary_out.get("recommendation") or primary_out.get("summary") or ""

    if missing and not rec:
        rec = (
            f"Cannot provide full personalised advice. "
            f"Please update your profile with: {', '.join(missing)}."
        )

    lines.append("")
    lines.append("Recommendation:")
    lines.append(f"  {rec}")

    # Append secondary tool recommendations
    for tool in active_tools[1:]:
        out = tool_outputs.get(tool, {})
        secondary_rec = out.get("recommendation") or out.get("summary")
        if secondary_rec:
            lines.append(f"  [{TOOL_LABELS.get(tool, tool)}] {secondary_rec}")

    lines.append("")
    lines.append(f"Confidence: {confidence_label}")

    return "\n".join(lines)


def _build_missing_profile_response(profile: dict, missing: list[str]) -> dict[str, Any]:
    """Return a structured response when core profile fields are absent."""
    lines = [
        "Profile Data Used:",
    ]
    for key, val in profile.items():
        if val is not None:
            label = key.replace("_", " ").title()
            if isinstance(val, (int, float)) and key in ("monthly_income", "monthly_expenses", "savings_goal"):
                lines.append(f"  {label}: {_format_inr(float(val))}")
            else:
                lines.append(f"  {label}: {val}")
    lines.append(f"  Missing fields: {', '.join(missing)}")
    lines.append("")
    lines.append("LangChain Tool Used:")
    lines.append("  • None (insufficient profile data)")
    lines.append("")
    lines.append("Calculation Steps:")
    lines.append("  Cannot compute — required profile values are missing.")
    lines.append("")
    lines.append("Recommendation:")
    lines.append(
        f"  Please update your finance profile with: {', '.join(missing)}. "
        "Personalised calculations require your actual income and expenses."
    )
    lines.append("")
    lines.append("Confidence: Low")

    recommendation = "\n".join(lines)
    return {
        "domain":           "finance",
        "tools_used":       [],
        "tool_outputs":     {},
        "recommendation":   recommendation,
        "reason":           f"Missing profile fields: {', '.join(missing)}",
        "confidence":         0.45,
        "confidence_level": "Low",
        "savings":          None,
        "debt_ratio":       None,
        "allocation_50_30_20": None,
        "months_to_goal":   None,
        "investment_advice": None,
        "explainability": {
            "profile_values_used":    profile,
            "tools_invoked":          [],
            "missing_profile_fields": missing,
            "confidence_level":       "Low",
            "calculation_steps":      {},
            "data_used":              [],
            "decision_factors":       [f"Missing: {', '.join(missing)}"],
            "next_steps":             [f"Add {f} to your finance profile" for f in missing],
            "confidence_explanation": "Low confidence — limited data available",
            "disclaimer": (
                "This is AI-generated advice for informational purposes only. "
                "Please consult a qualified professional before making major decisions."
            ),
        },
    }


def _validate_grounded_response(recommendation: str, deterministic_text: str) -> str:
    """Reject LLM output that drops required sections or numeric grounding."""
    required_sections = (
        "Profile Data Used",
        "LangChain Tool Used",
        "Recommendation",
        "Confidence",
    )
    if not all(section in recommendation for section in required_sections):
        return deterministic_text
    if "₹" not in recommendation:
        return deterministic_text
    return recommendation


def _format_with_llm(
    deterministic_text: str,
    profile: dict,
    tool_outputs: dict,
    active_tools: list[str],
    rag_context: str,
) -> dict:
    """Ask LLM to reformat pre-computed data — explicitly forbidden from calculating."""
    tool_json = {
        tool: {k: v for k, v in out.items() if k != "calculation_steps"}
        for tool, out in tool_outputs.items()
        if isinstance(out, dict)
    }

    user_message = f"""PRE-COMPUTED RESPONSE (use as basis — do NOT recalculate):
{deterministic_text}

PROFILE VALUES:
{json.dumps(profile, indent=2, default=str)}

TOOLS INVOKED: {[TOOL_LABELS.get(t, t) for t in active_tools]}

TOOL OUTPUTS:
{json.dumps(tool_json, indent=2, default=str)}

RAG CONTEXT (reference only):
{rag_context[:1500] if rag_context else 'None'}

Reformat into the required sections. Use exact ₹ amounts from above."""

    logger.info("[Finance] LLM prompt:\n%s", user_message[:2000])

    llm_response = call_llm(LLM_FORMATTER_PROMPT, user_message, temperature=0.1)
    return llm_response


# ── Main entry point ──────────────────────────────────────────────────────────

def run(request: Any) -> dict[str, Any]:
    """
    Finance Agent entry point.

    All calculations run in LangChain tools. The LLM only formats output.
    """
    query = getattr(request, "query", "")

    # 1. Always load latest profile
    user_id = getattr(request, "user_id", None)
    _load_profile_from_db(user_id, request)

    profile, missing = _extract_profile(request)

    logger.info("[Finance] detected query: %s", query[:120])
    logger.info("[Finance] profile values: %s", profile)
    logger.info("[Finance] missing core fields: %s", missing)

    if missing:
        logger.info("[Finance] aborting — incomplete profile")
        return _build_missing_profile_response(profile, missing)

    active_tools = _detect_tools(query)
    logger.info("[Finance] detected intent: %s", active_tools)

    # 3. RAG context (use caller-provided or fetch)
    rag_context = getattr(request, "rag_context", "") or ""
    if not rag_context and RAG_AVAILABLE:
        try:
            rag_context = retrieve_as_context(query, top_k=3)
        except Exception as exc:
            logger.warning("[Finance] RAG retrieval failed: %s", exc)

    # 4. Execute mandatory tool (LLM never calculates)
    tool_outputs: dict[str, dict] = {}
    for tool_name in active_tools:
        runner = _TOOL_RUNNERS.get(tool_name)
        if runner:
            try:
                output = runner(request)
                tool_outputs[tool_name] = output
                logger.info("[Finance] tool=%s output=%s", tool_name, json.dumps(output, default=str)[:500])
            except Exception as exc:
                tool_outputs[tool_name] = {"error": str(exc)}
                logger.error("[Finance] tool=%s error=%s", tool_name, exc)

    if rag_context:
        tool_outputs["rag_context"] = {"text": rag_context[:2000]}

    # 5. Compute supplementary metrics from profile
    income = float(profile.get("monthly_income") or 0)
    expenses = float(profile.get("monthly_expenses") or 0)
    savings_data = calculate_savings(income, expenses) if income > 0 else None
    debt_data = calculate_debt_ratio(income, expenses) if income > 0 else None

    confidence_label, confidence_score = _confidence_level(profile, missing, tool_outputs)

    # 6. Build deterministic response (primary output — all math from tools)
    deterministic_text = _build_deterministic_response(
        profile, missing, active_tools, tool_outputs, confidence_label,
    )

    # 7. Use deterministic response directly; LLM is optional polish only
    recommendation = deterministic_text
    reason = (
        tool_outputs.get(active_tools[0], {}).get("recommendation")
        or tool_outputs.get(active_tools[0], {}).get("summary")
        or "Based on your profile values and calculator tool outputs."
    )
    confidence = confidence_score

    logger.info("[Finance] final prompt (deterministic):\n%s", deterministic_text[:3000])

    # Primary tool shortcuts
    primary_out = tool_outputs.get(active_tools[0], {})
    months_to_goal = primary_out.get("months_to_goal")
    if months_to_goal is None and "savings" in tool_outputs:
        months_to_goal = tool_outputs["savings"].get("months_to_goal")

    allocation = None
    if income > 0:
        allocation = {
            "necessities": round(income * 0.5, 2),
            "wants": round(income * 0.3, 2),
            "savings_target": round(income * 0.2, 2),
        }

    result: dict[str, Any] = {
        "domain":              "finance",
        "tools_used":          active_tools,
        "tool_outputs":        tool_outputs,
        "recommendation":      recommendation,
        "reason":              reason,
        "confidence":          confidence,
        "confidence_level":    confidence_label,
        "savings":             savings_data,
        "debt_ratio":          debt_data,
        "allocation_50_30_20": allocation,
        "months_to_goal":      months_to_goal,
        "investment_advice":   tool_outputs.get("investment", {}).get("recommendation"),
    }

    from core.explainability import build_explainability

    explainability = build_explainability("finance", result, request)
    explainability["profile_values_used"] = profile
    explainability["tools_invoked"] = [TOOL_LABELS.get(t, t) for t in active_tools]
    explainability["missing_profile_fields"] = missing
    explainability["confidence_level"] = confidence_label
    explainability["calculation_steps"] = {
        tool: out.get("calculation_steps", [])
        for tool, out in tool_outputs.items()
        if isinstance(out, dict) and out.get("calculation_steps")
    }
    result["explainability"] = explainability

    logger.info("[Finance] final confidence=%s tools=%s", confidence_label, active_tools)

    return result
