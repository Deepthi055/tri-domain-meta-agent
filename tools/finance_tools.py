"""
tools/finance_tools.py
----------------------
Five Finance Agent tools for the TriDomain Meta-Agent system.
Each tool is a standalone callable with typed inputs, structured dict output,
and edge-case handling consistent with the existing codebase style.
"""

from __future__ import annotations
from typing import Any


# ─────────────────────────────────────────────────────────────────────────────
# 1. Budget Planner Tool
# ─────────────────────────────────────────────────────────────────────────────

# Recommended maximum share of gross income per category (50/30/20 rule variant)
BUDGET_LIMITS: dict[str, float] = {
    "housing":       0.30,   # rent / EMI
    "food":          0.15,
    "transport":     0.10,
    "utilities":     0.08,
    "entertainment": 0.05,
    "healthcare":    0.05,
    "education":     0.05,
    "miscellaneous": 0.05,
}


def budget_planner(
    income: float,
    expenses: dict[str, float],
    use_rule_limits: bool = False,
    savings_goal: float | None = None,
) -> dict[str, Any]:
    """
    Analyse monthly income vs categorised expenses.

    Args:
        income:   Gross monthly income (₹). Must be > 0.
        expenses: Dict mapping category name → monthly amount spent.
                  Example: {"housing": 15000, "food": 6000, ...}

    Returns:
        {
            "income":             float,
            "total_expenses":     float,
            "disposable_income":  float,
            "savings_rate_pct":   float,
            "category_breakdown": [ {category, amount, share_pct,
                                      recommended_pct, status}, ... ],
            "overspending":       [category, ...],
            "savings_status":     "healthy" | "tight" | "overspent",
            "summary":            str,
        }
    """
    # ── Edge cases ────────────────────────────────────────────────────
    if income <= 0:
        return {
            "error": "Income must be greater than zero.",
            "income": income,
        }

    if not expenses:
        return {
            "income":            income,
            "total_expenses":    0.0,
            "disposable_income": income,
            "savings_rate_pct":  100.0,
            "category_breakdown": [],
            "overspending":      [],
            "savings_status":    "healthy",
            "summary":           "No expenses recorded — full income is disposable.",
        }

    total_expenses = sum(expenses.values())
    disposable     = income - total_expenses
    savings_rate   = (disposable / income) * 100

    breakdown: list[dict] = []
    overspending: list[str] = []

    if use_rule_limits and len(expenses) > 1:
        for category, amount in expenses.items():
            if amount < 0:
                # Negative expense is a data error — skip gracefully
                continue

            share_pct = round((amount / income) * 100, 1)
            recommended_pct = None
            status = "recorded"
            if use_rule_limits:
                recommended_pct = round(
                    BUDGET_LIMITS.get(category.lower(), 0.10) * 100, 1
                )
                over = share_pct > recommended_pct
                status = "over budget" if over else "within budget"
                if over:
                    overspending.append(category)

            entry: dict[str, Any] = {
                "category":  category,
                "amount":    round(amount, 2),
                "share_pct": share_pct,
                "status":    status,
            }
            if recommended_pct is not None:
                entry["recommended_pct"] = recommended_pct
            breakdown.append(entry)
    else:
        for category, amount in expenses.items():
            if amount < 0:
                continue
            share_pct = round((amount / income) * 100, 1)
            breakdown.append({
                "category": category,
                "amount": round(amount, 2),
                "share_pct": share_pct,
                "status": "recorded",
            })

    if use_rule_limits:
        breakdown.sort(
            key=lambda x: x["share_pct"] - x.get("recommended_pct", 0),
            reverse=True,
        )
    else:
        breakdown.sort(key=lambda x: x["share_pct"], reverse=True)

    if savings_rate >= 20:
        savings_status = "healthy"
    elif savings_rate >= 5:
        savings_status = "tight"
    else:
        savings_status = "overspent"

    goal_diff = None
    if savings_goal is not None and savings_goal > 0:
        goal_diff = round(disposable - float(savings_goal), 2)

    summary = (
        f"Monthly income: ₹{round(income):,}. "
        f"Monthly expenses: ₹{round(total_expenses):,}. "
        f"Remaining amount: ₹{round(disposable):,}."
    )
    if savings_goal is not None and savings_goal > 0:
        if goal_diff is not None and goal_diff >= 0:
            summary += f" You exceed your savings goal by ₹{goal_diff:,}."
        elif goal_diff is not None:
            summary += f" You are ₹{abs(goal_diff):,} short of your savings goal."
    if use_rule_limits and overspending:
        summary += f" Overspending in: {', '.join(overspending)}."

    steps: list[str] = [
        f"Monthly Income = ₹{income:,.0f}",
        f"Monthly Expenses = ₹{total_expenses:,.0f}",
        "",
        "Remaining Amount",
        f"= ₹{income:,.0f} − ₹{total_expenses:,.0f}",
        f"= ₹{disposable:,.0f}",
    ]
    if savings_goal is not None and savings_goal > 0:
        steps.extend([
            "",
            f"Savings Goal = ₹{float(savings_goal):,.0f}",
            "",
            "Difference (Remaining − Savings Goal)",
            f"= ₹{disposable:,.0f} − ₹{float(savings_goal):,.0f}",
            f"= ₹{goal_diff:,.0f}",
        ])

    recommendation = summary
    if savings_goal is not None and savings_goal > 0 and goal_diff is not None:
        if goal_diff >= 0:
            recommendation = (
                f"Monthly income: ₹{income:,.0f}. Monthly expenses: ₹{total_expenses:,.0f}. "
                f"Remaining amount: ₹{disposable:,.0f}. Savings goal: ₹{float(savings_goal):,.0f}. "
                f"Difference: ₹{goal_diff:,.0f}."
            )
        else:
            recommendation = (
                f"Monthly income: ₹{income:,.0f}. Monthly expenses: ₹{total_expenses:,.0f}. "
                f"Remaining amount: ₹{disposable:,.0f}. Savings goal: ₹{float(savings_goal):,.0f}. "
                f"Difference: ₹{abs(goal_diff):,.0f} short."
            )
    else:
        recommendation = (
            f"Monthly income: ₹{income:,.0f}. Monthly expenses: ₹{total_expenses:,.0f}. "
            f"Remaining amount: ₹{disposable:,.0f}."
        )

    return {
        "income":             round(income, 2),
        "total_expenses":     round(total_expenses, 2),
        "disposable_income":  round(disposable, 2),
        "remaining_amount":   round(disposable, 2),
        "savings_goal":       round(float(savings_goal), 2) if savings_goal else None,
        "goal_difference":    goal_diff,
        "savings_rate_pct":   round(savings_rate, 1),
        "category_breakdown": breakdown,
        "overspending":       overspending,
        "savings_status":     savings_status,
        "calculation_steps":  steps,
        "recommendation":     recommendation,
        "summary":            summary,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2. Savings Calculator Tool
# ─────────────────────────────────────────────────────────────────────────────

def savings_calculator(
    income: float,
    expenses: float,
    savings_goal: float | None = None,
    current_savings: float = 0,
    goal_mode: str = "monthly",
    include_benchmark: bool = False,
) -> dict[str, Any]:
    """
    Compute monthly savings, savings rate, and time-to-goal with step-by-step math.

    Args:
        income:          Monthly gross income (₹).
        expenses:        Total monthly expenses (₹).
        savings_goal:    Target amount (₹). Interpretation depends on goal_mode.
        current_savings: Amount already saved toward a corpus goal (₹).
        goal_mode:       "monthly" = savings_goal is monthly savings target;
                         "corpus" = savings_goal is total amount to accumulate.

    Returns:
        Structured result with calculation_steps list and summary.
    """
    steps: list[str] = []

    if income <= 0:
        return {"error": "Income must be greater than zero.", "income": income}

    monthly_savings = round(income - expenses, 2)
    steps.append(f"Income = ₹{income:,.0f}")
    steps.append(f"Expenses = ₹{expenses:,.0f}")
    steps.append("")
    steps.append("Available Savings")
    steps.append(f"= ₹{income:,.0f} − ₹{expenses:,.0f}")
    steps.append(f"= ₹{monthly_savings:,.0f}")

    savings_rate = round((monthly_savings / income) * 100, 1) if income > 0 else 0.0
    steps.append("")
    steps.append(f"Savings Rate = ({monthly_savings:,.0f} / {income:,.0f}) × 100 = {savings_rate}%")

    remaining = None
    months_to_goal = None
    shortfall = None

    if savings_goal is not None and savings_goal > 0:
        if goal_mode == "corpus":
            remaining = round(max(0.0, float(savings_goal) - float(current_savings)), 2)
            steps.append("")
            steps.append(f"Savings Goal (corpus) = ₹{savings_goal:,.0f}")
            if current_savings > 0:
                steps.append(f"Current Savings = ₹{current_savings:,.0f}")
                steps.append(f"Remaining = ₹{savings_goal:,.0f} − ₹{current_savings:,.0f} = ₹{remaining:,.0f}")
            else:
                steps.append(f"Remaining = ₹{remaining:,.0f}")

            if monthly_savings > 0 and remaining > 0:
                import math
                months_to_goal = math.ceil(remaining / monthly_savings)
                steps.append("")
                steps.append("Time to Goal")
                steps.append(f"= ₹{remaining:,.0f} ÷ ₹{monthly_savings:,.0f}/month")
                steps.append(f"= {months_to_goal} months (~{round(months_to_goal / 12, 1)} years)")
            elif remaining == 0:
                months_to_goal = 0
                steps.append("")
                steps.append("Goal already achieved.")
            elif monthly_savings <= 0:
                shortfall = remaining
                steps.append("")
                steps.append(f"Shortfall = ₹{remaining:,.0f} (no monthly surplus to allocate)")
        else:
            # Monthly savings target
            steps.append("")
            steps.append(f"Savings Goal (monthly target) = ₹{savings_goal:,.0f}")
            if monthly_savings >= savings_goal:
                steps.append(f"Current monthly savings (₹{monthly_savings:,.0f}) meet or exceed the target.")
            else:
                shortfall = round(float(savings_goal) - monthly_savings, 2)
                steps.append("")
                steps.append("Shortfall")
                steps.append(f"= ₹{savings_goal:,.0f} − ₹{monthly_savings:,.0f}")
                steps.append(f"= ₹{shortfall:,.0f}")

    recommendation_parts: list[str] = []
    if monthly_savings < 0:
        recommendation_parts.append(
            f"You are overspending by ₹{abs(monthly_savings):,.0f}/month. "
            f"Reduce expenses by at least ₹{abs(monthly_savings):,.0f} to break even."
        )
    elif savings_goal and shortfall and shortfall > 0:
        recommendation_parts.append(
            f"Your current monthly savings are ₹{monthly_savings:,.0f} while your "
            f"target is ₹{savings_goal:,.0f}. Increase savings by "
            f"₹{shortfall:,.0f}/month or reduce expenses accordingly."
        )
    elif months_to_goal is not None and months_to_goal > 0:
        recommendation_parts.append(
            f"At ₹{monthly_savings:,.0f}/month, you will reach your "
            f"₹{savings_goal:,.0f} goal in {months_to_goal} months."
        )
    elif include_benchmark and savings_rate >= 20:
        recommendation_parts.append(
            f"Your savings rate of {savings_rate}% exceeds the recommended 20% threshold."
        )
    elif include_benchmark:
        needed = round(income * 0.20 - monthly_savings, 2)
        recommendation_parts.append(
            f"Your savings rate is {savings_rate}%. To reach the 20% benchmark, "
            f"save ₹{needed:,.0f} more per month (target: ₹{round(income * 0.20, 2):,.0f}/month)."
        )
    elif monthly_savings >= 0:
        recommendation_parts.append(
            f"Your monthly savings are ₹{monthly_savings:,.0f} ({savings_rate}% of income)."
        )

    return {
        "income":              round(income, 2),
        "expenses":            round(expenses, 2),
        "monthly_savings":     monthly_savings,
        "savings_rate_pct":    savings_rate,
        "savings_goal":        savings_goal,
        "current_savings":     round(current_savings, 2),
        "remaining_to_goal":   remaining,
        "months_to_goal":      months_to_goal,
        "shortfall":           shortfall,
        "calculation_steps":   steps,
        "recommendation":      " ".join(recommendation_parts),
        "summary": (
            f"Monthly savings: ₹{monthly_savings:,.0f} ({savings_rate}% rate)."
            + (f" Time to ₹{savings_goal:,.0f} goal: {months_to_goal} months." if months_to_goal else "")
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3. Financial Analysis Tool
# ─────────────────────────────────────────────────────────────────────────────

def financial_analysis(
    income: float,
    expenses: float,
    savings_goal: float | None = None,
    risk_tolerance: str = "moderate",
    investment_experience: str = "beginner",
    financial_goals: str | None = None,
) -> dict[str, Any]:
    """
    Assess financial strengths and weaknesses from profile values.

    Returns strengths, weaknesses, health_score, and personalised recommendations.
    """
    if income <= 0:
        return {"error": "Income must be greater than zero.", "income": income}

    monthly_savings = round(income - expenses, 2)
    savings_rate = round((monthly_savings / income) * 100, 1) if income > 0 else 0.0
    expense_ratio = round((expenses / income) * 100, 1)

    strengths: list[str] = []
    weaknesses: list[str] = []
    steps: list[str] = []

    steps.append(f"Income = ₹{income:,.0f}")
    steps.append(f"Expenses = ₹{expenses:,.0f}")
    steps.append(f"Monthly Surplus = ₹{income:,.0f} − ₹{expenses:,.0f} = ₹{monthly_savings:,.0f}")
    steps.append(f"Savings Rate = {savings_rate}%")
    steps.append(f"Expense Ratio = {expense_ratio}%")

    # Savings rate assessment
    if savings_rate >= 20:
        strengths.append(f"Healthy savings rate of {savings_rate}% (≥ 20% benchmark)")
    elif savings_rate >= 10:
        weaknesses.append(
            f"Savings rate of {savings_rate}% is below the 20% benchmark — "
            f"need ₹{round(income * 0.20 - monthly_savings, 2):,.0f} more/month"
        )
    else:
        weaknesses.append(
            f"Critical savings rate of {savings_rate}% — "
            f"only ₹{monthly_savings:,.0f}/month saved from ₹{income:,.0f} income"
        )

    # Expense ratio
    if expense_ratio <= 70:
        strengths.append(f"Controlled expense ratio at {expense_ratio}% of income")
    elif expense_ratio <= 85:
        weaknesses.append(f"Expenses consume {expense_ratio}% of income — limited room for goals")
    else:
        weaknesses.append(
            f"Expenses at {expense_ratio}% exceed income capacity — "
            f"deficit of ₹{abs(monthly_savings):,.0f}/month"
        )

    # Emergency fund (3–6 months expenses)
    emergency_target = round(expenses * 3, 2)
    steps.append(f"Emergency Fund Target (3× expenses) = ₹{emergency_target:,.0f}")
    if monthly_savings > 0:
        months_to_emergency = round(emergency_target / monthly_savings, 1)
        if months_to_emergency <= 12:
            strengths.append(
                f"Can build 3-month emergency fund (₹{emergency_target:,.0f}) in {months_to_emergency} months"
            )
        else:
            weaknesses.append(
                f"3-month emergency fund (₹{emergency_target:,.0f}) would take {months_to_emergency} months at current savings"
            )

    # Savings goal progress
    if savings_goal and savings_goal > 0:
        steps.append(f"Savings Goal = ₹{savings_goal:,.0f}")
        if monthly_savings >= savings_goal:
            strengths.append(f"Monthly surplus (₹{monthly_savings:,.0f}) meets or exceeds savings goal")
        else:
            gap = round(savings_goal - monthly_savings, 2)
            weaknesses.append(
                f"Monthly savings (₹{monthly_savings:,.0f}) fall ₹{gap:,.0f} short of "
                f"₹{savings_goal:,.0f} goal"
            )

    # Risk / experience alignment
    risk = risk_tolerance.lower()
    exp = investment_experience.lower()
    if risk in ("aggressive", "high") and exp in ("beginner",):
        weaknesses.append(
            f"Risk appetite ({risk_tolerance}) exceeds experience level ({investment_experience}) — "
            "consider starting with balanced funds"
        )
    elif risk in ("conservative", "low") and exp in ("advanced", "intermediate"):
        strengths.append(
            f"Conservative risk profile aligns with {investment_experience} experience"
        )

    if financial_goals:
        strengths.append(f"Defined financial goals: {financial_goals}")

    # Health score (0–100)
    score = 50
    score += min(25, savings_rate)
    score -= max(0, expense_ratio - 70)
    score += len(strengths) * 5
    score -= len(weaknesses) * 5
    score = max(0, min(100, round(score)))

    if score >= 75:
        health_status = "strong"
    elif score >= 50:
        health_status = "moderate"
    else:
        health_status = "needs improvement"

    rec_parts: list[str] = []
    if weaknesses:
        top = weaknesses[0]
        rec_parts.append(f"Priority: {top}")
    if savings_rate < 20 and monthly_savings > 0:
        needed = round(income * 0.20 - monthly_savings, 2)
        rec_parts.append(
            f"Increase monthly savings by ₹{needed:,.0f} to reach the 20% savings benchmark."
        )

    return {
        "health_score":        score,
        "health_status":       health_status,
        "monthly_savings":     monthly_savings,
        "savings_rate_pct":    savings_rate,
        "expense_ratio_pct":   expense_ratio,
        "strengths":           strengths,
        "weaknesses":          weaknesses,
        "calculation_steps":   steps,
        "recommendation":      " ".join(rec_parts) if rec_parts else "Your financial profile is well-balanced.",
        "summary": (
            f"Financial health score: {score}/100 ({health_status}). "
            f"{len(strengths)} strength(s), {len(weaknesses)} area(s) to improve."
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4. Investment Analysis Tool
# ─────────────────────────────────────────────────────────────────────────────

# Target allocation bands by risk profile and age bracket
# Structure: risk_profile → age_bracket → {asset: target_pct}
_TARGET_ALLOCATIONS: dict[str, dict[str, dict[str, float]]] = {
    "conservative": {
        "young":  {"equity": 40, "debt": 45, "gold": 10, "cash": 5},
        "mid":    {"equity": 25, "debt": 60, "gold": 10, "cash": 5},
        "senior": {"equity": 10, "debt": 70, "gold": 10, "cash": 10},
    },
    "moderate": {
        "young":  {"equity": 60, "debt": 30, "gold": 7,  "cash": 3},
        "mid":    {"equity": 45, "debt": 45, "gold": 7,  "cash": 3},
        "senior": {"equity": 25, "debt": 60, "gold": 10, "cash": 5},
    },
    "aggressive": {
        "young":  {"equity": 80, "debt": 12, "gold": 5,  "cash": 3},
        "mid":    {"equity": 65, "debt": 25, "gold": 7,  "cash": 3},
        "senior": {"equity": 40, "debt": 45, "gold": 10, "cash": 5},
    },
}


def _age_bracket(age: int) -> str:
    if age < 35:
        return "young"
    elif age < 55:
        return "mid"
    return "senior"


def investment_analysis(
    portfolio: dict[str, float],
    risk_tolerance: str,
    age: int,
    investment_experience: str | None = None,
    financial_goals: str | None = None,
    income: float | None = None,
    rag_context: str = "",
) -> dict[str, Any]:
    """
    Evaluate current portfolio and recommend rebalancing.

    Args:
        portfolio:      Dict mapping asset class → current value (₹).
                        Recognised classes: equity, debt, gold, cash.
                        Unknown classes are lumped into 'other'.
        risk_tolerance: "conservative" | "moderate" | "aggressive"
        age:            Investor's current age (years).

    Returns:
        {
            "portfolio_value":    float,
            "current_allocation": {asset: pct},
            "target_allocation":  {asset: pct},
            "rebalancing_deltas": [{asset, current_pct, target_pct,
                                    action, amount_inr}],
            "risk_profile":       str,
            "age_bracket":        str,
            "recommendation":     str,
        }
    """
    # ── Normalise risk label ──────────────────────────────────────────
    valid_risk = {"conservative", "moderate", "aggressive"}
    risk = risk_tolerance.lower()
    if risk not in valid_risk:
        risk = "moderate"   # safe default

    # ── Edge cases ────────────────────────────────────────────────────
    if age < 18:
        return {"error": "Age must be at least 18."}
    if age > 100:
        return {"error": "Please provide a realistic age value."}

    total_value = sum(portfolio.values()) if portfolio else 0.0

    steps: list[str] = [
        f"Risk Tolerance = {risk}",
        f"Age = {age} ({_age_bracket(age)} bracket)",
    ]
    if investment_experience:
        steps.append(f"Investment Experience = {investment_experience}")
    if financial_goals:
        steps.append(f"Financial Goals = {financial_goals}")
    if income is not None and income > 0:
        steps.append(f"Monthly Income = ₹{income:,.0f}")

    if total_value <= 0:
        bracket = _age_bracket(age)
        target  = _TARGET_ALLOCATIONS[risk][bracket]
        steps.append("")
        steps.append("Target Allocation (from risk profile + age)")
        for asset, pct in target.items():
            steps.append(f"  {asset}: {pct}%")
        rec = (
            f"As a {risk} investor aged {age}"
            + (f" with {investment_experience} experience" if investment_experience else "")
            + f", target allocation: "
            + ", ".join(f"{a} {p}%" for a, p in target.items())
            + "."
        )
        if financial_goals:
            rec += f" Align investments with your goal: {financial_goals}."
        if rag_context:
            rec += f" Reference: {rag_context[:300].strip()}."
        return {
            "portfolio_value":    0.0,
            "current_allocation": {},
            "target_allocation":  target,
            "rebalancing_deltas": [],
            "risk_profile":       risk,
            "age_bracket":        bracket,
            "calculation_steps":  steps,
            "recommendation":     rec,
        }

    bracket = _age_bracket(age)
    target  = _TARGET_ALLOCATIONS[risk][bracket]

    # ── Current allocation as percentages ─────────────────────────────
    current_alloc: dict[str, float] = {}
    for asset, value in portfolio.items():
        pct = round((value / total_value) * 100, 1)
        current_alloc[asset.lower()] = pct

    # ── Rebalancing deltas ────────────────────────────────────────────
    deltas: list[dict] = []
    all_assets = set(target.keys()) | set(current_alloc.keys())

    for asset in sorted(all_assets):
        cur_pct = current_alloc.get(asset, 0.0)
        tgt_pct = float(target.get(asset, 0.0))
        diff    = tgt_pct - cur_pct

        if abs(diff) < 1.0:          # within 1% → no action needed
            action = "hold"
        elif diff > 0:
            action = "buy"
        else:
            action = "sell"

        amount_inr = round(abs(diff / 100) * total_value, 2)

        deltas.append({
            "asset":       asset,
            "current_pct": cur_pct,
            "target_pct":  tgt_pct,
            "diff_pct":    round(diff, 1),
            "action":      action,
            "amount_inr":  amount_inr,
        })

    # Sort: biggest moves first
    deltas.sort(key=lambda x: abs(x["diff_pct"]), reverse=True)

    buy_actions  = [d["asset"] for d in deltas if d["action"] == "buy"]
    sell_actions = [d["asset"] for d in deltas if d["action"] == "sell"]

    steps.extend([
        f"Portfolio Value = ₹{round(total_value):,}",
        "",
        "Current vs Target Allocation",
    ])
    for asset in sorted(set(target.keys()) | set(current_alloc.keys())):
        cur = current_alloc.get(asset, 0.0)
        tgt = float(target.get(asset, 0.0))
        steps.append(f"  {asset}: current {cur}% → target {tgt}%")

    recommendation = (
        f"Portfolio value: ₹{round(total_value):,}. "
        f"As a {risk} investor in the {bracket} bracket, "
    )
    if buy_actions or sell_actions:
        parts = []
        if buy_actions:
            parts.append(f"increase {', '.join(buy_actions)}")
        if sell_actions:
            parts.append(f"reduce {', '.join(sell_actions)}")
        recommendation += "rebalance by: " + "; ".join(parts) + "."
    else:
        recommendation += "your portfolio is well-balanced — no rebalancing needed."
    if financial_goals:
        recommendation += f" Goal context: {financial_goals}."

    return {
        "portfolio_value":    round(total_value, 2),
        "current_allocation": current_alloc,
        "target_allocation":  target,
        "rebalancing_deltas": deltas,
        "risk_profile":       risk,
        "age_bracket":        bracket,
        "calculation_steps":  steps,
        "recommendation":     recommendation,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3. Debt Management Tool
# ─────────────────────────────────────────────────────────────────────────────

def _simulate_payoff(
    debts: list[dict],  # each: {name, balance, interest_rate, min_payment}
    monthly_payment: float,
    priority_key: str,  # "interest_rate" (avalanche) or "balance" (snowball)
    reverse: bool,      # True = highest first
) -> dict[str, Any]:
    """
    Simulate month-by-month debt payoff for a given ordering strategy.
    Returns total months, total interest paid, and per-debt sequence.
    """
    import copy

    remaining = copy.deepcopy(debts)
    total_interest = 0.0
    month = 0
    payoff_order: list[str] = []

    # Sort debts by chosen priority
    remaining.sort(key=lambda d: d[priority_key], reverse=reverse)

    while any(d["balance"] > 0 for d in remaining):
        month += 1
        if month > 600:          # 50-year safety cap
            break

        # Apply interest to all active debts
        for d in remaining:
            if d["balance"] > 0:
                monthly_rate = d["interest_rate"] / 100 / 12
                interest     = d["balance"] * monthly_rate
                total_interest += interest
                d["balance"]   += interest

        # Pay minimums on all debts
        available = monthly_payment
        for d in remaining:
            if d["balance"] > 0:
                pay       = min(d["min_payment"], d["balance"])
                d["balance"] = max(0, d["balance"] - pay)
                available -= pay

        # Apply extra payment to priority debt
        for d in remaining:
            if d["balance"] > 0 and available > 0:
                pay          = min(available, d["balance"])
                d["balance"] = max(0, d["balance"] - pay)
                available   -= pay
                if d["balance"] == 0 and d["name"] not in payoff_order:
                    payoff_order.append(d["name"])
                break

        # Mark newly paid off debts (catch ones paid via minimum)
        for d in remaining:
            if d["balance"] == 0 and d["name"] not in payoff_order:
                payoff_order.append(d["name"])

    return {
        "months":          month,
        "total_interest":  round(total_interest, 2),
        "payoff_order":    payoff_order,
    }


def debt_management(
    debts: list[dict[str, Any]],
    monthly_payment: float,
) -> dict[str, Any]:
    """
    Compare avalanche vs snowball payoff strategies and recommend the best.

    Args:
        debts: List of debt dicts, each containing:
               - name (str)
               - balance (float) — outstanding principal (₹)
               - interest_rate (float) — annual rate in percent (e.g. 18.0)
               - min_payment (float) — minimum monthly payment (₹)
        monthly_payment: Total monthly amount available for debt repayment (₹).

    Returns:
        {
            "total_debt":          float,
            "monthly_payment":     float,
            "avalanche":           {months, total_interest, payoff_order},
            "snowball":            {months, total_interest, payoff_order},
            "recommended_strategy": "avalanche" | "snowball",
            "interest_savings":    float,
            "time_difference_months": int,
            "summary":             str,
        }
    """
    # ── Edge cases ────────────────────────────────────────────────────
    if not debts:
        return {
            "error": "No debts provided.",
            "total_debt": 0.0,
        }

    if monthly_payment <= 0:
        return {"error": "Monthly payment must be greater than zero."}

    # Validate each debt entry
    required_keys = {"name", "balance", "interest_rate", "min_payment"}
    for i, d in enumerate(debts):
        missing = required_keys - set(d.keys())
        if missing:
            return {
                "error": f"Debt at index {i} is missing fields: {missing}"
            }

    total_min = sum(d["min_payment"] for d in debts)
    if monthly_payment < total_min:
        return {
            "error": (
                f"Monthly payment ₹{monthly_payment:,.0f} is less than the "
                f"sum of minimum payments ₹{total_min:,.0f}. "
                "Increase your monthly budget."
            ),
            "minimum_required": round(total_min, 2),
        }

    total_debt = sum(d["balance"] for d in debts)

    # ── Simulate both strategies ──────────────────────────────────────
    avalanche = _simulate_payoff(
        debts, monthly_payment, priority_key="interest_rate", reverse=True
    )
    snowball = _simulate_payoff(
        debts, monthly_payment, priority_key="balance", reverse=False
    )

    # Avalanche saves more money; snowball is faster at clearing first debt
    interest_savings   = round(snowball["total_interest"] - avalanche["total_interest"], 2)
    time_diff          = avalanche["months"] - snowball["months"]
    # Usually avalanche finishes at same time or slightly different
    recommended        = "avalanche" if interest_savings >= 0 else "snowball"

    summary = (
        f"Total debt: ₹{round(total_debt):,}. "
        f"Avalanche saves ₹{interest_savings:,} in interest over snowball "
        f"({avalanche['months']} vs {snowball['months']} months). "
        f"Recommended: {recommended.upper()} method."
    )

    return {
        "total_debt":               round(total_debt, 2),
        "monthly_payment":          round(monthly_payment, 2),
        "avalanche":                avalanche,
        "snowball":                 snowball,
        "recommended_strategy":     recommended,
        "interest_savings":         interest_savings,
        "time_difference_months":   abs(time_diff),
        "summary":                  summary,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4. Retirement Planner Tool
# ─────────────────────────────────────────────────────────────────────────────

# Conservative real rate of return assumptions (post-inflation)
_RETURN_RATE      = 0.07   # 7% nominal annual return on corpus
_INFLATION_RATE   = 0.06   # 6% annual inflation (India context)
_WITHDRAWAL_RATE  = 0.04   # 4% safe withdrawal rate


def retirement_planner(
    current_age:    int,
    retirement_age: int,
    savings:        float,
    monthly_contribution: float,
    monthly_expenses: float | None = None,
) -> dict[str, Any]:
    """
    Project retirement corpus and assess funding gap or surplus.

    Args:
        current_age:          Investor's current age (years).
        retirement_age:       Target retirement age (years).
        savings:              Current retirement savings / investments (₹).
        monthly_contribution: Monthly SIP / contribution towards retirement (₹).

    Returns:
        {
            "years_to_retirement":      int,
            "current_savings":          float,
            "monthly_contribution":     float,
            "projected_corpus":         float,
            "corpus_needed":            float,
            "gap_or_surplus":           float,
            "status":                   "on track" | "gap" | "surplus",
            "required_monthly_contrib": float,
            "summary":                  str,
        }
    """
    # ── Edge cases ────────────────────────────────────────────────────
    if current_age <= 0 or current_age >= 100:
        return {"error": "Please provide a valid current age (1–99)."}

    if retirement_age <= current_age:
        return {
            "error": (
                f"Retirement age ({retirement_age}) must be greater than "
                f"current age ({current_age})."
            )
        }

    if savings < 0:
        return {"error": "Current savings cannot be negative."}

    if monthly_contribution < 0:
        return {"error": "Monthly contribution cannot be negative."}

    years          = retirement_age - current_age
    months         = years * 12
    monthly_rate   = _RETURN_RATE / 12

    # ── Future value of existing savings ─────────────────────────────
    # FV = PV × (1 + r)^n
    fv_existing = savings * ((1 + monthly_rate) ** months)

    # ── Future value of monthly contributions (annuity) ──────────────
    # FV_annuity = PMT × [((1+r)^n − 1) / r]
    if monthly_rate > 0 and monthly_contribution > 0:
        fv_contributions = monthly_contribution * (
            ((1 + monthly_rate) ** months - 1) / monthly_rate
        )
    else:
        fv_contributions = monthly_contribution * months

    projected_corpus = fv_existing + fv_contributions

    # ── Estimate corpus needed from profile expenses (never invent) ───
    if not monthly_expenses or monthly_expenses <= 0:
        return {
            "error": (
                "Monthly expenses are required to estimate retirement corpus needs. "
                "Please add your monthly expenses to your profile."
            ),
        }

    inflation_factor = (1 + _INFLATION_RATE) ** years
    annual_need_at_retirement = monthly_expenses * 12 * inflation_factor
    corpus_needed = annual_need_at_retirement / _WITHDRAWAL_RATE

    gap_or_surplus = projected_corpus - corpus_needed
    status = (
        "surplus" if gap_or_surplus > 0
        else ("on track" if gap_or_surplus >= -corpus_needed * 0.05
              else "gap")
    )

    # ── Required monthly contribution to close any gap ────────────────
    if gap_or_surplus < 0 and monthly_rate > 0:
        required_monthly = (abs(gap_or_surplus) * monthly_rate) / (
            (1 + monthly_rate) ** months - 1
        )
        required_monthly = round(monthly_contribution + required_monthly, 2)
    else:
        required_monthly = monthly_contribution

    summary = (
        f"In {years} years you will accumulate ~₹{round(projected_corpus):,}. "
        f"Estimated corpus needed: ₹{round(corpus_needed):,}. "
    )
    if status == "surplus":
        summary += f"You have a projected surplus of ₹{round(gap_or_surplus):,}. Well done!"
    elif status == "gap":
        summary += (
            f"Shortfall: ₹{round(abs(gap_or_surplus)):,}. "
            f"Increase monthly SIP to ₹{round(required_monthly):,} to close the gap."
        )
    else:
        summary += "You are broadly on track for retirement."

    assumption_note = (
        f"Assumptions: {_RETURN_RATE * 100:.0f}% annual return, "
        f"{_INFLATION_RATE * 100:.0f}% inflation, "
        f"{_WITHDRAWAL_RATE * 100:.0f}% safe withdrawal rate."
    )
    steps = [
        f"Current Age = {current_age}",
        f"Retirement Age = {retirement_age}",
        f"Years to Retirement = {years}",
        f"Current Savings = ₹{savings:,.0f}",
        f"Monthly Contribution = ₹{monthly_contribution:,.0f}",
        f"Monthly Expenses (today) = ₹{monthly_expenses:,.0f}",
        "",
        "Projected Corpus",
        f"FV(existing) + FV(contributions) = ₹{round(projected_corpus):,.0f}",
        "",
        "Corpus Needed at Retirement",
        f"Inflated annual expenses ÷ withdrawal rate = ₹{round(corpus_needed):,.0f}",
        "",
        f"Gap/Surplus = ₹{round(gap_or_surplus):,.0f}",
        "",
        assumption_note,
    ]

    return {
        "years_to_retirement":      years,
        "current_savings":          round(savings, 2),
        "monthly_contribution":     round(monthly_contribution, 2),
        "projected_corpus":         round(projected_corpus, 2),
        "corpus_needed":            round(corpus_needed, 2),
        "gap_or_surplus":           round(gap_or_surplus, 2),
        "status":                   status,
        "required_monthly_contrib": required_monthly,
        "assumptions": {
            "annual_return_rate_pct": _RETURN_RATE * 100,
            "inflation_rate_pct":     _INFLATION_RATE * 100,
            "safe_withdrawal_rate_pct": _WITHDRAWAL_RATE * 100,
        },
        "calculation_steps":        steps,
        "recommendation":           summary,
        "summary":                  summary,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 5. Tax Optimizer Tool
# ─────────────────────────────────────────────────────────────────────────────

# Indian new-regime tax slabs (FY 2024-25)
_NEW_REGIME_SLABS = [
    (300_000,   0.00),
    (600_000,   0.05),
    (900_000,   0.10),
    (1_200_000, 0.15),
    (1_500_000, 0.20),
    (float("inf"), 0.30),
]

# Indian old-regime tax slabs (below 60 years)
_OLD_REGIME_SLABS = [
    (250_000,   0.00),
    (500_000,   0.05),
    (1_000_000, 0.20),
    (float("inf"), 0.30),
]

# Common Section 80C + 80D limits
_80C_LIMIT  = 150_000
_80D_LIMIT  = 25_000   # self + family (non-senior)
_NPS_LIMIT  = 50_000   # 80CCD(1B)
_HRA_PROXY  = 0.40     # rough HRA exemption = 40% of basic (non-metro)
_STD_DEDUCTION = 75_000  # Standard deduction FY 2024-25 (new regime)


def _compute_tax(taxable_income: float, slabs: list[tuple]) -> float:
    """Apply progressive tax slabs and return total tax (before cess)."""
    tax        = 0.0
    prev_limit = 0.0

    for limit, rate in slabs:
        if taxable_income <= prev_limit:
            break
        slab_income = min(taxable_income, limit) - prev_limit
        tax        += slab_income * rate
        prev_limit  = limit

    # Add 4% health & education cess
    return round(tax * 1.04, 2)


def tax_optimizer(
    income: float,
    deductions: dict[str, float],
) -> dict[str, Any]:
    """
    Estimate tax liability under both regimes and surface optimisation tips.

    Args:
        income:     Annual gross income (₹).
        deductions: Dict of deduction types → amounts actually utilised (₹).
                    Recognised keys (case-insensitive):
                    80c, 80d, nps, hra, home_loan_interest, other

    Returns:
        {
            "gross_income":             float,
            "old_regime": {
                "taxable_income":  float,
                "deductions_used": float,
                "tax_liability":   float,
            },
            "new_regime": {
                "taxable_income":  float,
                "tax_liability":   float,
            },
            "recommended_regime":       "old" | "new",
            "tax_savings_vs_other":     float,
            "optimisation_tips":        [str],
            "untapped_deductions":      {deduction_type: headroom_inr},
            "summary":                  str,
        }
    """
    # ── Edge cases ────────────────────────────────────────────────────
    if income <= 0:
        return {"error": "Annual income must be greater than zero."}

    # Normalise deduction keys to lowercase
    ded = {k.lower(): max(0, v) for k, v in (deductions or {}).items()}

    # ── Old regime ────────────────────────────────────────────────────
    d_80c  = min(ded.get("80c",  0), _80C_LIMIT)
    d_80d  = min(ded.get("80d",  0), _80D_LIMIT)
    d_nps  = min(ded.get("nps",  0), _NPS_LIMIT)
    d_hra  = ded.get("hra",  0)
    d_home = ded.get("home_loan_interest", 0)   # 80C already capped; this is separate sec 24b
    d_other = ded.get("other", 0)
    std_deduction_old = 50_000   # old regime standard deduction

    total_old_deductions = (
        std_deduction_old + d_80c + d_80d + d_nps
        + d_hra + min(d_home, 200_000) + d_other
    )
    taxable_old = max(0, income - total_old_deductions)
    tax_old     = _compute_tax(taxable_old, _OLD_REGIME_SLABS)

    # Section 87A rebate (old regime): full rebate if taxable ≤ 5L
    if taxable_old <= 500_000:
        tax_old = 0.0

    # ── New regime ────────────────────────────────────────────────────
    taxable_new = max(0, income - _STD_DEDUCTION)
    tax_new     = _compute_tax(taxable_new, _NEW_REGIME_SLABS)

    # Section 87A rebate (new regime): full rebate if taxable ≤ 7L
    if taxable_new <= 700_000:
        tax_new = 0.0

    # ── Recommendation ────────────────────────────────────────────────
    if tax_old <= tax_new:
        recommended_regime = "old"
        savings_vs_other   = round(tax_new - tax_old, 2)
    else:
        recommended_regime = "new"
        savings_vs_other   = round(tax_old - tax_new, 2)

    # ── Optimisation tips ─────────────────────────────────────────────
    tips: list[str] = []
    untapped: dict[str, float] = {}

    headroom_80c = _80C_LIMIT - d_80c
    if headroom_80c > 0:
        tips.append(
            f"Invest ₹{headroom_80c:,.0f} more in 80C instruments "
            f"(ELSS, PPF, life insurance) to exhaust the ₹1.5L limit."
        )
        untapped["80c"] = headroom_80c

    headroom_80d = _80D_LIMIT - d_80d
    if headroom_80d > 0:
        tips.append(
            f"Add ₹{headroom_80d:,.0f} in health insurance premiums "
            f"(Section 80D) for additional old-regime relief."
        )
        untapped["80d"] = headroom_80d

    headroom_nps = _NPS_LIMIT - d_nps
    if headroom_nps > 0:
        tips.append(
            f"Contribute ₹{headroom_nps:,.0f} to NPS under 80CCD(1B) "
            f"for an exclusive ₹50,000 deduction."
        )
        untapped["nps"] = headroom_nps

    if d_home == 0 and income > 600_000:
        tips.append(
            "If you have a home loan, deduct up to ₹2,00,000 in interest "
            "paid under Section 24(b) in the old regime."
        )

    if recommended_regime == "new":
        tips.append(
            "Under the new regime you benefit from the ₹75,000 standard "
            "deduction but most itemised deductions are not available."
        )

    if not tips:
        tips.append("Your deduction utilisation appears optimised already.")

    summary = (
        f"Old regime tax: ₹{round(tax_old):,} | "
        f"New regime tax: ₹{round(tax_new):,}. "
        f"Recommended: {recommended_regime.upper()} regime "
        f"(saves ₹{round(savings_vs_other):,})."
    )

    steps = [
        f"Annual Income = ₹{income:,.0f}",
        f"Old Regime Taxable = ₹{round(taxable_old):,.0f}",
        f"Old Regime Tax = ₹{round(tax_old):,.0f}",
        f"New Regime Taxable = ₹{round(taxable_new):,.0f}",
        f"New Regime Tax = ₹{round(tax_new):,.0f}",
        f"Recommended = {recommended_regime.upper()} regime",
        f"Tax Savings vs Other = ₹{round(savings_vs_other):,.0f}",
    ]

    return {
        "gross_income":         round(income, 2),
        "old_regime": {
            "taxable_income":   round(taxable_old, 2),
            "deductions_used":  round(total_old_deductions, 2),
            "tax_liability":    round(tax_old, 2),
        },
        "new_regime": {
            "taxable_income":   round(taxable_new, 2),
            "deductions_used":  round(_STD_DEDUCTION, 2),
            "tax_liability":    round(tax_new, 2),
        },
        "recommended_regime":   recommended_regime,
        "tax_savings_vs_other": savings_vs_other,
        "optimisation_tips":    tips,
        "untapped_deductions":  untapped,
        "calculation_steps":    steps,
        "recommendation":       summary,
        "summary":              summary,
    }