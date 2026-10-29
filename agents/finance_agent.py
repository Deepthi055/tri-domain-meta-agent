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
import os
import re
from typing import Any

from core.llm_client import call_llm
from core.intent_detector import detect_intent
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
    from rag.finance_retriever import retrieve
    RAG_AVAILABLE = True
except Exception:
    RAG_AVAILABLE = False

logger = logging.getLogger("finance_agent")

# ── Tool display names (LangChain tool labels) ────────────────────────────────

TOOL_LABELS: dict[str, str] = {
    "budget":             "Budget Planner",
    "savings":            "Savings Calculator",
    "investments":        "Investment Advisor",
    "investment":         "Investment Advisor",
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
        "reach my goal", "save for", "save up", "save money", "save",
    ],
    "investments": [
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
    "savings":            ["income", "expenses", "savings_goal"],
    "debt":               ["total_debt", "monthly_repayment"],
    "retirement":         ["age", "monthly_income", "savings", "retirement_age"],
    "tax":                ["annual_income"],
    "investments":        ["risk_tolerance", "investment_experience", "financial_goals"],
    "financial_analysis": ["monthly_income", "monthly_expenses"],
}

_TOOL_FIELD_LABELS: dict[str, str] = {
    "monthly_income":         "Monthly income",
    "monthly_expenses":       "Monthly expenses",
    "income":                 "Income",
    "expenses":               "Expenses",
    "total_debt":             "Total debt",
    "monthly_repayment":      "Current monthly repayment",
    "monthly_debt_payment":   "Current monthly repayment",
    "age":                    "Age",
    "savings_goal":           "Savings goal",
    "savings":                "Current savings",
    "retirement_age":         "Retirement age",
    "annual_income":          "Annual income",
    "risk_tolerance":         "Risk tolerance",
    "investment_experience":  "Investment experience",
    "financial_goals":        "Financial goals",
    "portfolio":              "Portfolio values",
}

_MISSING_FIELD_MESSAGES: dict[str, str] = {
    "budget": (
        "I need your income and expense details to build a budget.\n"
        "Please provide:\n"
        "• Monthly income\n"
        "• Monthly expenses"
    ),
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
        "• Monthly income\n"
        "• Current savings\n"
        "• Target retirement age\n"
        "• Monthly expenses"
    ),
    "tax": (
        "I need your annual income to calculate tax.\n"
        "Please provide:\n"
        "• Annual income (or monthly income to derive it)"
    ),
    "investment": (
        "I need your investment profile to give allocation advice.\n"
        "Please provide:\n"
        "• Monthly income\n"
        "• Age\n"
        "• Risk tolerance\n"
        "• Investment experience"
    ),
    "savings": (
        "I need your savings details to calculate time-to-goal.\n"
        "Please provide:\n"
        "• Monthly income\n"
        "• Monthly expenses\n"
        "• Savings goal amount"
    ),
}

LLM_FORMATTER_PROMPT = """You are a finance response formatter inside the TriDomain AI system.

CRITICAL RULES:
1. You MUST NOT perform any calculations — all numbers are pre-computed below.
2. You MUST NOT give generic advice like "increase savings" or "reduce expenses"
   without citing the exact ₹ amounts provided.
3. Use ONLY the profile values, tool outputs, and retrieved context given to you.
4. Format the recommendation with these sections (use bullet headers):
   • Profile Data Used
   • Selected Tool
   • Calculation Steps
   • Final Recommendation
   • Confidence
5. Use retrieved context as the primary evidence for claims about the finance
   knowledge base.
6. Cite the exact document title shown in retrieved text for each
   knowledge-base-supported claim.
7. Do not invent source names, statistics, quotations, or document contents.
8. If retrieved documents do not specify relevant finance guidance, state that
   limitation clearly.
9. Separate retrieved evidence from general recommendations. Label
   recommendations not directly supported by retrieved context as
   "General guidance, not explicitly stated in the knowledge base."
10. Never attribute a claim to a document unless the retrieved text from that
    document supports it.
11. If no relevant RAG context is provided, state that the knowledge base does
    not contain sufficient evidence. Do not imply retrieval succeeded merely
    because a source filename is available.

Respond ONLY with valid JSON — no markdown fences:
{
    "recommendation": "full formatted response with all sections above",
    "reason": "one sentence on why this advice fits this user",
    "confidence": 0.88
}"""

# ── Finance domain fallback ───────────────────────────────────────────────────

_FINANCE_DOMAIN_PATTERNS = (
    r"\bfinance\b",
    r"\bfinancial\b",
    r"\bmoney\b",
    r"\bincome\b",
    r"\bsalary\b",
    r"\bear(n|ning|s)?\b",
    r"\bexpense(s)?\b",
    r"\bspend(ing)?\b",
    r"\bbudget\b",
    r"\bsav(e|ing|ings)?\b",
    r"\bemergency fund\b",
    r"\binvest(ment|ing|or)?s?\b",
    r"\bportfolio\b",
    r"\bstocks?\b",
    r"\bmutual funds?\b",
    r"\bsip\b",
    r"\bequity\b",
    r"\bdebt\b",
    r"\bloan\b",
    r"\bemi\b",
    r"\bcredit card\b",
    r"\bretirement\b",
    r"\bpension\b",
    r"\btax(able|ation)?\b",
    r"\bitr\b",
    r"\bdeduction(s)?\b",
    r"\bfinancial goals?\b",
    r"\bwealth\b",
    r"\bcompound interest\b",
)


def _looks_like_finance_query(query: str) -> bool:
    """
    Lightweight fallback used only when the global intent detector
    returns 'general' for a clearly Finance-related query.
    """
    q = query.lower().strip()

    if not q:
        return False

    return any(re.search(pattern, q) for pattern in _FINANCE_DOMAIN_PATTERNS)
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


def _parse_investments(investments: Any, monthly_income: float | None) -> dict[str, float]:
    """Parse investments field into portfolio dict when explicit values exist."""
    if not investments:
        return {}
    if isinstance(investments, dict):
        return {k: float(v) for k, v in investments.items() if v is not None}
    if isinstance(investments, str):
        try:
            parsed = json.loads(investments)
            if isinstance(parsed, dict):
                return {k: float(v) for k, v in parsed.items() if v is not None}
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
    return {}


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

    if field in {"monthly_repayment", "monthly_debt_payment"}:
        val = getattr(request, "monthly_repayment", None)

        if val is None:
            val = getattr(request, "monthly_debt_payment", None)

        return float(val) if val is not None and float(val) > 0 else None

    if field in {"income", "monthly_income"}:
        val = getattr(request, "income", None)

        if val is None:
            val = getattr(request, "monthly_income", None)

        return float(val) if val is not None and float(val) > 0 else None

    if field in {"expenses", "monthly_expenses"}:
        val = getattr(request, "expenses", None)

        # If detailed expenses are provided as a dictionary,
        # use their total. If the dictionary is empty, fall back
        # to the monthly_expenses field.
        if isinstance(val, dict):
            if val:
                return float(sum(val.values()))

        # If expenses is provided directly as a number
        elif val is not None and float(val) > 0:
            return float(val)

        # Fall back to monthly_expenses
        monthly_expenses = getattr(request, "monthly_expenses", None)

        if monthly_expenses is not None and float(monthly_expenses) > 0:
            return float(monthly_expenses)

        return None

    if field == "annual_income":
        annual = getattr(request, "annual_income", None)

        if annual is not None and float(annual) > 0:
            return float(annual)

        monthly = getattr(request, "monthly_income", None)

        if monthly is not None and float(monthly) > 0:
            return float(monthly) * 12

        return None

    if field == "savings":
        for attr in ("retirement_savings", "current_savings", "savings"):
            val = getattr(request, attr, None)

            if val is not None and float(val) >= 0:
                return float(val)

        return None

    if field == "retirement_age":
        val = getattr(request, "retirement_age", None)

        return int(val) if val is not None and int(val) > 0 else None

    if field == "financial_goals":
        return getattr(request, "financial_goals", None)

    if field == "portfolio":
        pf = _parse_portfolio(request)
        return pf if pf else None

    if field == "risk_tolerance":
        return (
            getattr(request, "risk_tolerance", None)
            or getattr(request, "risk_appetite", None)
        )

    if field == "investment_experience":
        val = getattr(request, "investment_experience", None)

        return (
            val.strip()
            if isinstance(val, str) and val.strip()
            else val
        )

    val = getattr(request, field, None)

    if field in ("monthly_income", "monthly_expenses", "savings_goal") and val is not None:
        return float(val) if float(val) > 0 else None

    if field == "age" and val is not None:
        return int(val) if int(val) > 0 else None

    return val


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

    missing: list[str] = []
    values: dict[str, Any] = {}
    explicit_budget_values = _extract_explicit_budget_values(query) if tool == "budget" else {}

    for field in required:
        val = explicit_budget_values.get(field)
        if val is None:
            val = _resolve_field(request, field)
        values[field] = val
        if val is None:
            missing.append(field)
        elif field == "monthly_debt_payment" and isinstance(val, (int, float)) and val <= 0:
            missing.append(field)

    return missing, values


def _extract_explicit_budget_values(query: str) -> dict[str, float]:
    """Extract monthly budget figures explicitly stated in the user's query."""
    values: dict[str, float] = {}
    for field, label in (
        ("monthly_income", "income"),
        ("monthly_expenses", "expenses"),
    ):
        match = re.search(
            rf"\b{label}\s*(?:is|of|:|=)?\s*(?:₹|rs\.?\s*)?([\d,]+(?:\.\d+)?)",
            query,
            re.IGNORECASE,
        )
        if match:
            values[field] = float(match.group(1).replace(",", ""))
    return values


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
                "current_savings": "current_savings",
                "savings_goal": "savings_goal",
                "investments": "investments",
                "portfolio": "portfolio",
                "investment_experience": "investment_experience",
                "financial_goals": "financial_goals",
                "budget": "budget",
                "debts": "debts",
                "total_debt": "total_debt",
                "monthly_debt_payment": "monthly_debt_payment",
                "retirement_age": "retirement_age",
                "retirement_savings": "retirement_savings",
                "monthly_contribution": "monthly_contribution",
                "annual_income": "annual_income",
                "tax_deductions": "tax_deductions",
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
        "monthly_debt_payment": getattr(request, "monthly_debt_payment", None)
        or getattr(request, "monthly_repayment", None),
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


def _profile_display_label(key: str) -> str:
    labels = {
        "monthly_income": "Monthly Income",
        "monthly_expenses": "Monthly Expenses",
        "savings_goal": "Savings Goal",
        "financial_goals": "Financial Goal",
    }
    return labels.get(key, key.replace("_", " ").title())


# ── Intent detection ──────────────────────────────────────────────────────────

# Tie-break order when keyword scores are equal
_TOOL_PRIORITY = [
    "debt",
    "tax",
    "retirement",
    "investments",
    "budget",
    "savings",
    "financial_analysis",
]

_META_PATTERNS = [
    r"which (profile|langchain|tool)",
    r"show (every|all) calculation",
    r"what (profile|values) did you use",
]

_BUDGET_INTENT_PATTERNS = (
    "create a budget",
    "create budget",
    "monthly budget",
    "budget plan",
    "spending plan",
    "budgeting",
    "expense breakdown",
    "budget using",
    "budget for",
    "monthly spending plan",
)


def _is_budget_query(query: str) -> bool:
    q = query.lower()
    if any(kw in q for kw in ("debt", "loan", "emi", "credit card", "repay", "owe")):
        return False
    if any(pattern in q for pattern in _BUDGET_INTENT_PATTERNS):
        return True
    return any(
        phrase in q
        for phrase in (
            "calculate my budget",
            "plan my budget",
            "make a budget",
            "create my budget",
            "my savings rate",
            "my expense ratio",
        )
    )


def _detect_tools(query: str) -> str | None:
    """Return the primary tool for actionable queries, or None for knowledge questions."""
    q = query.lower()

    if "emergency fund" in q or any(
        phrase in q
        for phrase in (
            "explain",
            "what is",
            "how does",
            "how big should",
            "where should i keep",
        )
    ):
        return None

    if _is_budget_query(query):
        return "budget"

    if any(re.search(p, q) for p in _META_PATTERNS):
        return "financial_analysis"

    matched: list[str] = []
    for tool, keywords in _TOOL_KEYWORDS.items():
        if any(kw in q for kw in keywords):
            matched.append(tool)

    if not matched:
        return None

    for tool in _TOOL_PRIORITY:
        if tool in matched:
            return tool

    return matched[0]


# ── Tool runners ──────────────────────────────────────────────────────────────

def _run_budget(request: Any, query: str = "") -> dict:
    explicit_values = _extract_explicit_budget_values(query)
    explicit_expenses = getattr(request, "expenses", None)
    if explicit_expenses:
        expenses = explicit_expenses
    elif explicit_values.get("monthly_expenses") is not None:
        expenses = {"total": explicit_values["monthly_expenses"]}
    else:
        expenses = _parse_budget(
            getattr(request, "budget", None),
            getattr(request, "monthly_expenses", None),
        )

    if not expenses and hasattr(request, "monthly_expenses"):
        expenses = {"total": float(request.monthly_expenses or 0)}

    savings_goal = getattr(request, "savings_goal", None)
    result = budget_planner(
        income=float(
            explicit_values.get("monthly_income")
            or getattr(request, "monthly_income", 0)
        ),
        expenses=expenses,
        use_rule_limits=_wants_50_30_20_rule(query),
        savings_goal=float(savings_goal) if savings_goal else None,
    )
    return result


def _run_savings(request: Any) -> dict:
    query = getattr(request, "query", "") or ""
    income = _resolve_field(request, "income")
    expenses = _resolve_field(request, "expenses")
    savings_goal = _resolve_field(request, "savings_goal")
    if income is None or expenses is None or savings_goal is None:
        return {
            "error": "Income, expenses, and savings goal are required for savings calculation.",
            "calculation_steps": [
                "Income = required",
                "Expenses = required",
                "Savings Goal = required",
            ],
            "recommendation": "I need your income, expenses, and savings goal to calculate time-to-goal.",
        }
    return savings_calculator(
        income=float(income),
        expenses=float(expenses),
        savings_goal=float(_resolve_field(request, "savings_goal")),
        current_savings=float(getattr(request, "current_savings", 0) or 0),
        goal_mode=_savings_goal_mode(query),
    )


def _run_investments(request: Any, rag_context: str = "") -> dict:
    portfolio = _parse_portfolio(request) or _parse_investments(
        getattr(request, "investments", None),
        getattr(request, "monthly_income", None),
    )
    return investment_analysis(
        portfolio=portfolio,
        risk_tolerance=_normalize_risk(getattr(request, "risk_tolerance", None)),
        age=int(getattr(request, "age")),
        investment_experience=getattr(request, "investment_experience", None),
        financial_goals=getattr(request, "financial_goals", None),
        income=float(getattr(request, "monthly_income", 0)),
        rag_context=rag_context,
    )


def _run_debt(request: Any) -> dict:
    total_debt = _get_total_debt(request)
    monthly_payment = float(getattr(request, "monthly_repayment", 0) or getattr(request, "monthly_debt_payment", 0) or 0)
    debts = getattr(request, "debts", None) or []

    if not debts and (total_debt is None or monthly_payment <= 0):
        steps = [
            "I don't have your debt information yet.",
            "Please provide:",
            "• Total debt",
            "• Current monthly repayment",
        ]
        return {
            "total_debt": total_debt,
            "monthly_payment": monthly_payment,
            "calculation_steps": steps,
            "recommendation": (
                "I don't have your debt information yet.\n"
                "Please provide:\n"
                "• Total debt\n"
                "• Current monthly repayment"
            ),
            "summary": "Debt information is incomplete; no payoff estimate was made.",
        }

    if debts:
        result = debt_management(debts=debts, monthly_payment=monthly_payment)
        if "error" not in result:
            result["calculation_steps"] = [
                f"Total Debt = {_format_inr(result.get('total_debt'))}",
                f"Monthly Repayment = {_format_inr(monthly_payment)}",
                f"Recommended Strategy = {result.get('recommended_strategy', 'N/A').upper()}",
                f"Avalanche Payoff = {result.get('avalanche', {}).get('months', 'N/A')} months",
                f"Snowball Payoff = {result.get('snowball', {}).get('months', 'N/A')} months",
            ]
            result["recommendation"] = result.get("summary", "")
        return result

    steps = [
        f"Total Debt = {_format_inr(total_debt)}",
        f"Monthly Repayment = {_format_inr(monthly_payment)}",
    ]
    return {
        "total_debt": total_debt,
        "monthly_payment": monthly_payment,
        "calculation_steps": steps,
        "recommendation": (
            f"Your total debt is {_format_inr(total_debt)} with a monthly repayment of "
            f"{_format_inr(monthly_payment)}. Add individual debt details (balance, "
            "interest rate, minimum payment) for payoff strategy analysis."
        ),
        "summary": (
            f"Total debt {_format_inr(total_debt)}; monthly repayment {_format_inr(monthly_payment)}."
        ),
    }


def _run_retirement(request: Any) -> dict:
    current_age = int(getattr(request, "age"))
    retirement_age = int(getattr(request, "retirement_age"))
    savings = float(
        getattr(request, "retirement_savings", None)
        or getattr(request, "current_savings", 0)
        or 0
    )
    monthly_contrib = float(getattr(request, "monthly_contribution", 0) or 0)
    monthly_expenses = float(getattr(request, "monthly_expenses", 0) or 0)

    return retirement_planner(
        current_age=current_age,
        retirement_age=retirement_age,
        savings=savings,
        monthly_contribution=monthly_contrib,
        monthly_expenses=monthly_expenses,
    )


def _run_tax(request: Any) -> dict:
    annual_income = _resolve_field(request, "annual_income")
    if annual_income is None:
        return {"error": "Annual income is required for tax calculation."}

    deductions: dict[str, float] = getattr(request, "tax_deductions", None) or {}
    return tax_optimizer(income=float(annual_income), deductions=deductions)


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
    "investments":        _run_investments,
    "investment":         _run_investments,
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
    tool_selected: str | None = None,
) -> str:
    """Build fully structured recommendation from tool outputs — no generic advice."""
    lines: list[str] = []

    # Profile Data Used
    lines.append("Profile Data Used:")
    for key, val in profile.items():
        if val is not None:
            label = _profile_display_label(key)
            if isinstance(val, (int, float)) and key in ("monthly_income", "monthly_expenses", "savings_goal"):
                lines.append(f"  {label}: {_format_inr(float(val))}")
            else:
                lines.append(f"  {label}: {val}")
    if missing:
        lines.append(f"  Missing fields: {', '.join(missing)}")

    # Selected Tool
    lines.append("")
    lines.append("Tool Selected:")
    if tool_selected:
        suffix = " (not executed — incomplete profile)" if missing else ""
        lines.append(f"  • {TOOL_LABELS.get(tool_selected, tool_selected)}{suffix}")
    else:
        lines.append("  • None (general finance knowledge question)")

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
    primary = active_tools[0] if active_tools else None
    primary_out = tool_outputs.get(primary, {}) if primary else {}
    rec = primary_out.get("recommendation") or primary_out.get("summary") or ""

    if missing and not rec:
        rec = (
            f"Cannot provide full personalised advice. "
            f"Please update your profile with: {', '.join(missing)}."
        )
    elif not rec:
        rec = "No personalized calculation was run."

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
    lines.append(f"Confidence Level: {confidence_label}")

    return "\n".join(lines)


def _build_missing_tool_response(
    profile: dict,
    tool: str,
    missing: list[str],
    resolved: dict[str, Any],
) -> dict[str, Any]:
    """Return structured follow-up when tool-specific profile fields are missing."""
    missing_labels = [_TOOL_FIELD_LABELS.get(f, f.replace("_", " ").title()) for f in missing]
    custom_message = _MISSING_FIELD_MESSAGES.get(tool)
    if custom_message:
        follow_up = custom_message
    else:
        follow_up = (
            "I need more profile information before I can run this calculation.\n"
            "Please provide:\n"
            + "\n".join(f"• {label}" for label in missing_labels)
        )

    lines = [
        "Profile Data Used:",
    ]
    for key, val in profile.items():
        if val is not None:
            label = _profile_display_label(key)
            if isinstance(val, (int, float)) and key in (
                "monthly_income", "monthly_expenses", "savings_goal",
            ):
                lines.append(f"  {label}: {_format_inr(float(val))}")
            else:
                lines.append(f"  {label}: {val}")
    for field, val in resolved.items():
        if val is not None and profile.get(field) is None:
            label = _TOOL_FIELD_LABELS.get(field, field.replace("_", " ").title())
            if isinstance(val, (int, float)):
                lines.append(f"  {label}: {_format_inr(float(val))}")
            else:
                lines.append(f"  {label}: {val}")
    lines.append(f"  Missing fields: {', '.join(missing_labels)}")
    lines.append("")
    lines.append("Tool Selected:")
    lines.append(f"  • {TOOL_LABELS.get(tool, tool)} (not executed — incomplete profile)")
    lines.append("")
    lines.append("Calculation Steps:")
    lines.append("  Cannot compute — required profile values are missing.")
    lines.append("")
    lines.append("Recommendation:")
    for line in follow_up.split("\n"):
        lines.append(f"  {line}" if line else "")
    lines.append("")
    lines.append("Confidence Level: Low")

    recommendation = "\n".join(lines)
    return {
        "domain":           "finance",
        "tools_used":       [tool],
        "tool_outputs":     {},
        "recommendation":   recommendation,
        "reason":           f"Missing fields for {TOOL_LABELS.get(tool, tool)}: {', '.join(missing_labels)}",
        "confidence":       0.45,
        "confidence_level": "Low",
        "savings":          None,
        "debt_ratio":       None,
        "allocation_50_30_20": None,
        "months_to_goal":   None,
        "investment_advice": None,
        "missing_fields":   missing,
        "explainability": {
            "profile_values_used":    profile,
            "tools_invoked":          [TOOL_LABELS.get(tool, tool)],
            "missing_profile_fields": missing,
            "confidence_level":       "Low",
            "calculation_steps":      {},
            "data_used":              list(resolved.keys()),
            "decision_factors":       [f"Missing: {', '.join(missing_labels)}"],
            "next_steps":             [f"Add {label}" for label in missing_labels],
            "confidence_explanation": "Low confidence — required tool inputs missing",
            "disclaimer": (
                "This is AI-generated advice for informational purposes only. "
                "Please consult a qualified professional before making major decisions."
            ),
        },
    }


def _build_missing_profile_response(profile: dict, missing: list[str]) -> dict[str, Any]:
    """Return a structured response when core profile fields are absent."""
    lines = [
        "Profile Data Used:",
    ]
    for key, val in profile.items():
        if val is not None:
            label = _profile_display_label(key)
            if isinstance(val, (int, float)) and key in ("monthly_income", "monthly_expenses", "savings_goal"):
                lines.append(f"  {label}: {_format_inr(float(val))}")
            else:
                lines.append(f"  {label}: {val}")
    lines.append(f"  Missing fields: {', '.join(missing)}")
    lines.append("")
    lines.append("Tool Selected:")
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
    lines.append("Confidence Level: Low")

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
        "Tool Selected",
        "Recommendation",
        "Confidence Level",
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
    query: str = "",
    tool_selected: str | None = None,
    missing_fields: list[str] | None = None,
) -> dict:
    """Ask LLM to reformat pre-computed data — explicitly forbidden from calculating."""
    tool_json = {
        tool: {k: v for k, v in out.items() if k != "calculation_steps"}
        for tool, out in tool_outputs.items()
        if isinstance(out, dict)
    }

    user_message = f"""PRE-COMPUTED RESPONSE (use as basis — do NOT recalculate):
{deterministic_text}

USER QUERY:
{query}

PROFILE VALUES:
{json.dumps(profile, indent=2, default=str)}

TOOL SELECTED: {TOOL_LABELS.get(tool_selected, tool_selected) if tool_selected else 'None'}
TOOLS INVOKED: {[TOOL_LABELS.get(t, t) for t in active_tools]}
MISSING PROFILE FIELDS: {missing_fields or []}

TOOL OUTPUTS:
{json.dumps(tool_json, indent=2, default=str)}

RAG CONTEXT (reference only):
{rag_context[:1500] if rag_context else ''}

Answer the USER QUERY directly. For a conceptual question, explain the concept
using the relevant facts in RAG CONTEXT and name the document title. Do not
replace the answer with an instruction, question, or placeholder. If no tool
was selected, do not present the response as a calculation. If a tool was
selected but required profile fields are missing, answer generally from RAG
CONTEXT first and ask only for the missing fields afterward. When a tool ran,
use its output and retrieved context together. Reformat into the required
sections and use exact ₹ amounts from tool output."""

    logger.info("[Finance] LLM prompt:\n%s", user_message[:2000])

    llm_response = call_llm(LLM_FORMATTER_PROMPT, user_message, temperature=0.1)
    return llm_response


def _format_retrieved_chunks(chunks: list[dict]) -> tuple[str, list[dict]]:
    """Format retrieved finance chunks and expose their source metadata."""
    context_parts = []
    sources = []
    for chunk in chunks:
        text = chunk.get("text")
        if not isinstance(text, str) or not text.strip():
            continue
        title_match = re.search(r"(?:^|\n)DOCUMENT:\s*(.+)", text)
        doc_title = (
            title_match.group(1).strip()
            if title_match
            else str(chunk.get("source") or "unknown")
        )
        chunk_id = chunk.get("chunk_id")
        score = chunk.get("relevance_score", chunk.get("score"))
        sources.append({
            "doc_title": doc_title,
            "chunk_id": chunk_id,
            "score": score,
        })
        context_parts.append(
            f"[Source: {doc_title}; chunk_id: {chunk_id}; score: {score}]\n{text}"
        )
    return "\n\n".join(context_parts), sources


# ── Main entry point ──────────────────────────────────────────────────────────

def run(request: Any) -> dict[str, Any]:
    """
    Finance Agent entry point.

    All calculations run in finance tools; the LLM uses retrieved knowledge and
    formats tool output or answers general finance questions.
    """
    query = getattr(request, "query", "")

    # Manual Finance selection must not turn an unrelated question into a
    # Finance request. Guard before loading profile data or selecting tools.
    intent = detect_intent(query)
    domains = intent.get("domains") or ["general"]
    detected_domain = domains[0]

    # The global router may identify Finance alongside another domain. A
    # general result is accepted only when the query has clear Finance intent.
    if "finance" not in domains and not (
        domains == ["general"] and _looks_like_finance_query(query)
    ):
        domain_label = {
            "career": "Career",
            "health": "Health",
        }.get(detected_domain, "the appropriate")
        return {
            "domain": "finance",
            "tools_used": [],
            "tool_outputs": {},
            "recommendation": (
                "This question does not belong to the Finance domain. "
                f"Please switch to the {domain_label} domain."
            ),
            "reason": f"Detected domain: {detected_domain}",
            "confidence": 1.0,
            "confidence_level": "High",
        }

    # Retrieve knowledge before tool validation so general answers remain
    # available even when a selected tool lacks required profile fields.
    rag_enabled = os.getenv("USE_RAG", "true").strip().lower() == "true"
    chunks: list[dict] = []
    retrieval_status = "disabled" if not rag_enabled else "not_used"
    if rag_enabled and RAG_AVAILABLE:
        try:
            chunks = retrieve(query) or []
            retrieval_status = "empty" if not chunks else "not_used"
        except Exception as exc:
            logger.warning("[Finance] RAG retrieval failed: %s", exc)
    elif rag_enabled:
        logger.warning("[Finance] RAG enabled but the finance retriever is unavailable")
    rag_context, retrieved_sources = _format_retrieved_chunks(chunks)

    # 1. Always load latest profile
    user_id = getattr(request, "user_id", None)
    _load_profile_from_db(user_id, request)

    profile, _core_missing = _extract_profile(request)
    explicit_budget_values = _extract_explicit_budget_values(query)
    for field, value in explicit_budget_values.items():
        if profile.get(field) is None:
            profile[field] = value

    # 2. Detect actionable tool intent independently of RAG state.
    tool_selected = _detect_tools(query)
    tool_selected_reason = (
        f"Matched actionable finance intent: {tool_selected}"
        if tool_selected
        else None
    )
    logger.info("[Finance] detected query: %s", query[:120])
    logger.info("[Finance] detected intent → tool: %s", tool_selected)
    logger.info("[Finance] profile values: %s", profile)

    # 3. Validate selected tool inputs; missing fields suppress execution, not
    # retrieval or the general LLM answer.
    missing_fields: list[str] = []
    resolved_values: dict[str, Any] = {}
    if tool_selected:
        missing_fields, resolved_values = _validate_tool_fields(
            tool_selected, request, query
        )
    if missing_fields:
        logger.info(
            "[Finance] missing fields for %s: %s",
            tool_selected,
            missing_fields,
        )

    # 4. Execute a selected tool only when its required profile is complete.
    tool_outputs: dict[str, dict] = {}
    active_tools = [tool_selected] if tool_selected and not missing_fields else []
    primary_tool = active_tools[0] if active_tools else None
    runner = _TOOL_RUNNERS.get(primary_tool) if primary_tool else None
    if runner and primary_tool:
        try:
            if primary_tool == "budget":
                output = runner(request, query)
            elif primary_tool == "investment":
                output = runner(request, rag_context)
            else:
                output = runner(request)
            tool_outputs[primary_tool] = output
            if primary_tool == "investments" and "investment" not in tool_outputs:
                tool_outputs["investment"] = output
            logger.info(
                "[Finance] tool=%s output=%s",
                primary_tool,
                json.dumps(output, default=str)[:500],
            )
        except Exception as exc:
            tool_outputs[primary_tool] = {"error": str(exc)}
            logger.error("[Finance] tool=%s error=%s", primary_tool, exc)

    # 5. Compute supplementary metrics from profile (display only).
    income = float(profile.get("monthly_income") or 0)
    expenses = float(profile.get("monthly_expenses") or 0)
    savings_data = calculate_savings(income, expenses) if income > 0 else None
    monthly_emi = _resolve_field(request, "monthly_repayment")
    debt_data = (
        calculate_debt_ratio(income, float(monthly_emi))
        if income > 0 and monthly_emi is not None
        else None
    )
    expense_ratio = round(expenses / income * 100, 1) if income > 0 else None

    confidence_label, confidence_score = _confidence_level(
        profile, missing_fields, tool_outputs
    )

    # 6. Build deterministic data for the LLM, retaining any missing fields.
    deterministic_text = _build_deterministic_response(
        profile,
        missing_fields,
        active_tools,
        tool_outputs,
        confidence_label,
        tool_selected=tool_selected,
    )
    if expense_ratio is not None:
        deterministic_text += f"\nExpense Ratio: {expense_ratio}%"
    if debt_data is not None:
        deterministic_text += (
            "\nDebt-to-Income Ratio (monthly EMI / monthly income): "
            f"{debt_data['debt_to_income_ratio']:.2f} ({debt_data['status']})"
        )

    recommendation = deterministic_text
    primary_out = tool_outputs.get(primary_tool, {}) if primary_tool else {}
    reason = (
        primary_out.get("recommendation")
        or primary_out.get("summary")
        or (
            f"Missing fields for {TOOL_LABELS.get(tool_selected, tool_selected)}: "
            f"{', '.join(missing_fields)}"
            if missing_fields and tool_selected
            else "General finance answer based on retrieved context."
        )
    )
    confidence = confidence_score

    # Use the same formatter prompt and message structure for all retrieval
    # states; only the RAG CONTEXT section changes.
    llm_response = _format_with_llm(
        deterministic_text,
        profile,
        tool_outputs,
        active_tools,
        rag_context,
        query=query,
        tool_selected=tool_selected,
        missing_fields=missing_fields,
    )
    if isinstance(llm_response, dict):
        llm_recommendation = llm_response.get("recommendation")
        if isinstance(llm_recommendation, str) and llm_recommendation.strip():
            recommendation = llm_recommendation
        if llm_response.get("reason"):
            reason = str(llm_response["reason"])

    if expense_ratio is not None and "Expense Ratio:" not in recommendation:
        recommendation += f"\nExpense Ratio: {expense_ratio}%"
    if debt_data is not None and "Debt-to-Income Ratio" not in recommendation:
        recommendation += (
            "\nDebt-to-Income Ratio (monthly EMI / monthly income): "
            f"{debt_data['debt_to_income_ratio']:.2f} ({debt_data['status']})"
        )

    context_in_prompt = bool(rag_context)
    if chunks and context_in_prompt:
        retrieval_status = "success"

    logger.info("[Finance] final prompt (deterministic):\n%s", deterministic_text[:3000])

    months_to_goal = primary_out.get("months_to_goal")

    allocation = None
    if _wants_50_30_20_rule(query) and income > 0:
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
        "expense_ratio":       expense_ratio,
        "allocation_50_30_20": allocation,
        "months_to_goal":      months_to_goal,
        "investment_advice":   tool_outputs.get("investment", {}).get("recommendation"),
    }

    from core.explainability import build_explainability

    explainability = build_explainability("finance", result, request)
    explainability["profile_values_used"] = profile
    explainability["tools_invoked"] = [TOOL_LABELS.get(t, t) for t in active_tools]
    explainability["missing_profile_fields"] = [
        _TOOL_FIELD_LABELS.get(field, field) for field in missing_fields
    ]
    explainability["confidence_level"] = confidence_label
    explainability["calculation_steps"] = {
        tool: out.get("calculation_steps", [])
        for tool, out in tool_outputs.items()
        if isinstance(out, dict) and out.get("calculation_steps")
    }
    explainability.update({
        "rag_enabled": rag_enabled,
        "retrieval_status": retrieval_status,
        "retrieved_sources": retrieved_sources,
        "tool_selected": tool_selected,
        "tool_selected_reason": tool_selected_reason,
        "context_in_prompt": context_in_prompt,
        "profile_values_in_prompt": profile,
        "expense_ratio": expense_ratio,
    })
    result["explainability"] = explainability

    logger.info(
        "[Finance] final confidence=%s tools=%s",
        confidence_label,
        active_tools,
    )

    return result
