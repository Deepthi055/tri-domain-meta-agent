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

    for category, amount in expenses.items():
        if amount < 0:
            # Negative expense is a data error — skip gracefully
            continue

        share_pct       = round((amount / income) * 100, 1)
        recommended_pct = round(
            BUDGET_LIMITS.get(category.lower(), 0.10) * 100, 1
        )
        over = share_pct > recommended_pct

        if over:
            overspending.append(category)

        breakdown.append({
            "category":         category,
            "amount":           round(amount, 2),
            "share_pct":        share_pct,
            "recommended_pct":  recommended_pct,
            "status":           "over budget" if over else "within budget",
        })

    # Sort: worst offenders first
    breakdown.sort(key=lambda x: x["share_pct"] - x["recommended_pct"], reverse=True)

    if savings_rate >= 20:
        savings_status = "healthy"
    elif savings_rate >= 5:
        savings_status = "tight"
    else:
        savings_status = "overspent"

    summary = (
        f"You spend ₹{round(total_expenses):,} of your ₹{round(income):,} income "
        f"({round(100 - savings_rate, 1)}% expense ratio). "
        f"Savings rate is {round(savings_rate, 1)}% — {savings_status}."
    )
    if overspending:
        summary += f" Overspending in: {', '.join(overspending)}."

    return {
        "income":             round(income, 2),
        "total_expenses":     round(total_expenses, 2),
        "disposable_income":  round(disposable, 2),
        "savings_rate_pct":   round(savings_rate, 1),
        "category_breakdown": breakdown,
        "overspending":       overspending,
        "savings_status":     savings_status,
        "summary":            summary,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2. Investment Analysis Tool
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

    if total_value <= 0:
        # No portfolio yet — just return target allocation as a guide
        bracket = _age_bracket(age)
        target  = _TARGET_ALLOCATIONS[risk][bracket]
        return {
            "portfolio_value":    0.0,
            "current_allocation": {},
            "target_allocation":  target,
            "rebalancing_deltas": [],
            "risk_profile":       risk,
            "age_bracket":        bracket,
            "recommendation": (
                "No portfolio data provided. "
                f"As a {risk} investor aged {age}, target the allocation above "
                "when you begin investing."
            ),
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

    return {
        "portfolio_value":    round(total_value, 2),
        "current_allocation": current_alloc,
        "target_allocation":  target,
        "rebalancing_deltas": deltas,
        "risk_profile":       risk,
        "age_bracket":        bracket,
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

    # ── Estimate corpus needed ────────────────────────────────────────
    # Assume current monthly expenses ≈ 40% of monthly contribution as proxy;
    # better: caller should supply expenses — we use a 25× annual rule here.
    # Corpus needed = Annual expenses at retirement / withdrawal_rate
    # Proxy annual expenses = 12 × monthly_contribution × 2 (inflation-adj.)
    # This is a simplification; the LLM prompt can add nuance.
    inflation_factor   = (1 + _INFLATION_RATE) ** years
    # Use monthly contribution as a rough proxy for current monthly spend
    estimated_monthly_need_today = max(monthly_contribution, 10_000)
    annual_need_at_retirement    = (
        estimated_monthly_need_today * 12 * inflation_factor
    )
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
        "summary":              summary,
    }