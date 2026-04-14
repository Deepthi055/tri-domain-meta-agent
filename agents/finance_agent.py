# from core.llm_client import call_llm
# from tools.calculators import calculate_savings, calculate_debt_ratio

# FINANCE_SYSTEM_PROMPT = """You are a specialist financial advisor inside a 
# TriDomain AI system. You have deep expertise in:
# - Personal savings and budgeting strategy
# - Debt management and reduction
# - Investment basics for salaried professionals
# - Financial planning for career transitions

# YOUR RULES:
# 1. Always reference the user's actual numbers in your advice
# 2. Never recommend high-risk investments without flagging the risk
# 3. Always consider debt-to-income ratio before suggesting investments
# 4. Tailor advice to Indian financial context (SIP, PPF, etc.) unless stated

# CRITICAL: Respond ONLY with valid JSON in exactly this format:
# {
#     "recommendation": "specific actionable advice here",
#     "reason": "why this fits this specific user",
#     "confidence": 0.85
# }"""

# def run(request) -> dict:
#     savings_data = calculate_savings(request.monthly_income, request.monthly_expenses)
#     debt_data = calculate_debt_ratio(request.monthly_income, request.monthly_expenses)

#     user_message = f"""User profile:
# - Name: {request.name}
# - Age: {request.age}
# - Monthly Income: ₹{request.monthly_income}
# - Monthly Expenses: ₹{request.monthly_expenses}
# - Savings: ₹{savings_data['savings']} ({savings_data['rate_pct']}% rate)
# - Debt-to-Income Ratio: {debt_data['debt_to_income_ratio']} ({debt_data['status']})
# - Query: {request.query}

# Give specific financial advice for this person."""

#     llm_response = call_llm(FINANCE_SYSTEM_PROMPT, user_message, temperature=0.3)
#     return {
#         "domain": "finance",
#         "savings": savings_data,
#         "debt_ratio": debt_data,
#         **llm_response
#     }


"""
agents/finance_agent.py
-----------------------
Finance domain specialist for the TriDomain Meta-Agent system.

Integrates five financial tools:
  1. budget_planner         — income vs expense breakdown + savings rate
  2. investment_analysis    — portfolio allocation + rebalancing advice
  3. debt_management        — avalanche / snowball payoff strategy
  4. retirement_planner     — corpus projection + gap analysis
  5. tax_optimizer          — old vs new regime comparison + tips

The agent auto-selects which tools to run based on the user's query,
passes computed metrics to the LLM for narrative advice, and returns
a structured response consistent with the rest of the TriDomain system.
"""

from __future__ import annotations

import re
from typing import Any

from core.llm_client import call_llm
from tools.finance_tools import (
    budget_planner,
    debt_management,
    investment_analysis,
    retirement_planner,
    tax_optimizer,
)

# ─────────────────────────────────────────────────────────────────────────────
# System prompt
# ─────────────────────────────────────────────────────────────────────────────

FINANCE_SYSTEM_PROMPT = """You are a specialist personal finance advisor inside
the TriDomain AI system. You have deep expertise in:
- Budgeting, savings, and expense optimisation
- Debt elimination strategies (avalanche / snowball)
- Equity and debt investment allocation for Indian investors
- Retirement planning and corpus projection
- Indian income tax optimisation (old vs new regime, 80C/80D/NPS)

YOUR RULES:
1. Always reference the user's ACTUAL numbers in your advice — never be vague.
2. Never recommend high-risk investments without flagging the risk explicitly.
3. Always consider debt-to-income ratio before suggesting investment actions.
4. Tailor advice to the Indian financial context (SIP, PPF, NPS, ELSS, etc.)
   unless the user specifies a different country.
5. If data is insufficient for a tool, acknowledge the assumption made.
6. Never recommend quitting a job or making irreversible decisions without a
   thorough financial safety analysis.

CRITICAL: Respond ONLY with valid JSON in exactly this format — no preamble,
no markdown fences, no trailing text:
{
    "recommendation": "specific, multi-sentence actionable advice here",
    "reason": "one concise sentence explaining why this fits this user",
    "confidence": 0.88
}"""


# ─────────────────────────────────────────────────────────────────────────────
# Intent helpers — decide which tools to activate
# ─────────────────────────────────────────────────────────────────────────────

_TOOL_KEYWORDS: dict[str, list[str]] = {
    "budget":     ["budget", "spend", "expense", "saving", "money", "income", "afford"],
    "investment": ["invest", "portfolio", "stock", "equity", "mutual fund", "sip",
                   "asset", "allocat", "rebalanc"],
    "debt":       ["debt", "loan", "emi", "credit card", "borrow", "repay",
                   "owe", "pay off", "liability"],
    "retirement": ["retire", "pension", "corpus", "old age", "future", "60",
                   "epf", "nps", "ppf"],
    "tax":        ["tax", "itr", "deduction", "80c", "80d", "regime", "tds",
                   "income tax", "refund"],
}


def _detect_tools(query: str) -> list[str]:
    """
    Return a list of tool names relevant to the user's query.
    Falls back to ["budget"] if no strong signal is found.
    """
    q = query.lower()
    matched: list[str] = []

    for tool, keywords in _TOOL_KEYWORDS.items():
        if any(kw in q for kw in keywords):
            matched.append(tool)

    return matched if matched else ["budget"]


# ─────────────────────────────────────────────────────────────────────────────
# Per-tool runners
# ─────────────────────────────────────────────────────────────────────────────

def _run_budget(request: Any) -> dict:
    """Pull expense data from request and run budget_planner."""
    expenses: dict[str, float] = getattr(request, "expenses", {}) or {}

    # Backward-compat: if only monthly_expenses total is provided, wrap it
    if not expenses and hasattr(request, "monthly_expenses"):
        expenses = {"total": float(request.monthly_expenses)}

    return budget_planner(
        income=float(getattr(request, "monthly_income", 0)),
        expenses=expenses,
    )


def _run_investment(request: Any) -> dict:
    """Pull portfolio data from request and run investment_analysis."""
    portfolio: dict[str, float] = getattr(request, "portfolio", {}) or {}
    risk       = getattr(request, "risk_tolerance", "moderate") or "moderate"
    age        = int(getattr(request, "age", 30))

    return investment_analysis(
        portfolio=portfolio,
        risk_tolerance=risk,
        age=age,
    )


def _run_debt(request: Any) -> dict:
    """Pull debt list from request and run debt_management."""
    debts          = getattr(request, "debts", []) or []
    monthly_payment = float(getattr(request, "monthly_debt_payment", 0))

    # If debts list is empty but monthly_expenses exists, return a placeholder
    if not debts:
        return {
            "note": (
                "No debt breakdown provided. "
                "Supply a 'debts' list with name, balance, "
                "interest_rate, and min_payment for detailed analysis."
            )
        }

    return debt_management(debts=debts, monthly_payment=monthly_payment)


def _run_retirement(request: Any) -> dict:
    """Pull retirement data from request and run retirement_planner."""
    current_age   = int(getattr(request, "age", 30))
    retirement_age = int(getattr(request, "retirement_age", 60))
    savings       = float(getattr(request, "retirement_savings", 0))
    monthly_contrib = float(getattr(request, "monthly_contribution", 0))

    # If no contribution specified, assume 20% of income as proxy
    if monthly_contrib == 0 and hasattr(request, "monthly_income"):
        monthly_contrib = float(request.monthly_income) * 0.20

    return retirement_planner(
        current_age=current_age,
        retirement_age=retirement_age,
        savings=savings,
        monthly_contribution=monthly_contrib,
    )


def _run_tax(request: Any) -> dict:
    """Pull income + deductions from request and run tax_optimizer."""
    # Annual income — try dedicated field first, else annualise monthly
    annual_income = float(getattr(request, "annual_income", 0))
    if annual_income == 0 and hasattr(request, "monthly_income"):
        annual_income = float(request.monthly_income) * 12

    deductions: dict[str, float] = getattr(request, "tax_deductions", {}) or {}

    return tax_optimizer(income=annual_income, deductions=deductions)


# Map tool name → runner function
_TOOL_RUNNERS = {
    "budget":     _run_budget,
    "investment": _run_investment,
    "debt":       _run_debt,
    "retirement": _run_retirement,
    "tax":        _run_tax,
}


# ─────────────────────────────────────────────────────────────────────────────
# Main agent entry point
# ─────────────────────────────────────────────────────────────────────────────

def run(request: Any) -> dict[str, Any]:
    """
    Finance Agent entry point — called by the meta-agent.

    Args:
        request: QueryRequest instance (Pydantic model from main.py).
                 Expected fields (all optional beyond core profile):
                   monthly_income, monthly_expenses, expenses (dict),
                   portfolio (dict), risk_tolerance, retirement_age,
                   retirement_savings, monthly_contribution,
                   annual_income, tax_deductions (dict),
                   debts (list), monthly_debt_payment.

    Returns:
        Standard agent response dict:
        {
            "domain":         "finance",
            "tools_used":     [str, ...],
            "tool_outputs":   {tool_name: result_dict},
            "recommendation": str,
            "reason":         str,
            "confidence":     float,
            # Plus flattened shortcut keys for UI rendering:
            "savings":        {...} | None,
            "debt_ratio":     {...} | None,
        }
    """
    query = getattr(request, "query", "")

    # ── Determine which tools to run ──────────────────────────────────
    active_tools = _detect_tools(query)

    # Always include budget as baseline context (it's cheap and always useful)
    if "budget" not in active_tools:
        active_tools.insert(0, "budget")

    # ── Execute tools ─────────────────────────────────────────────────
    tool_outputs: dict[str, dict] = {}
    for tool_name in active_tools:
        runner = _TOOL_RUNNERS.get(tool_name)
        if runner:
            try:
                tool_outputs[tool_name] = runner(request)
            except Exception as exc:
                tool_outputs[tool_name] = {"error": str(exc)}

    # ── Build LLM context from tool results ───────────────────────────
    tool_summary_lines: list[str] = []
    for tool_name, result in tool_outputs.items():
        if "error" in result:
            tool_summary_lines.append(
                f"[{tool_name.upper()}] Error: {result['error']}"
            )
        elif "note" in result:
            tool_summary_lines.append(f"[{tool_name.upper()}] {result['note']}")
        elif "summary" in result:
            tool_summary_lines.append(
                f"[{tool_name.upper()}] {result['summary']}"
            )

    tool_context = "\n".join(tool_summary_lines)

    user_message = f"""User profile:
- Name:  {getattr(request, 'name', 'User')}
- Age:   {getattr(request, 'age', 'N/A')}
- Query: {query}

Calculated financial metrics:
{tool_context}

Based on these specific numbers, provide tailored financial advice."""

    # ── Call LLM ─────────────────────────────────────────────────────
    llm_response = call_llm(FINANCE_SYSTEM_PROMPT, user_message, temperature=0.3)

    # ── Assemble final response ───────────────────────────────────────
    # Shortcut fields for UI rendering (backward-compatible with Phase 2/3 UI)
    budget_out = tool_outputs.get("budget", {})

    savings_shortcut = None
    if "savings_rate_pct" in budget_out:
        savings_shortcut = {
            "savings": round(budget_out.get("disposable_income", 0), 2),
            "rate_pct": budget_out.get("savings_rate_pct", 0),
        }

    # debt_ratio — compute from budget figures for UI compatibility
    income   = float(getattr(request, "monthly_income", 0))
    expenses = float(getattr(request, "monthly_expenses", 0))
    debt_ratio_shortcut = None
    if income > 0 and expenses > 0:
        ratio = round(expenses / income, 2)
        debt_ratio_shortcut = {
            "debt_to_income_ratio": ratio,
            "status": "healthy" if ratio < 0.5 else "concerning",
        }

    return {
        "domain":       "finance",
        "tools_used":   active_tools,
        "tool_outputs": tool_outputs,
        **llm_response,           # recommendation, reason, confidence
        # UI shortcut keys (used by index.html renderer)
        "savings":      savings_shortcut,
        "debt_ratio":   debt_ratio_shortcut,
    }