"""
test_finance_tools.py
---------------------
Standalone test for all five finance tools.
Run from the tridomain_agent root:

    python test_finance_tools.py

No server or API key needed — tools are pure Python.
"""

import json
import sys
import os

# Make sure root is on path so `from tools.finance_tools import ...` works
sys.path.insert(0, os.path.dirname(__file__))

from tools.finance_tools import (
    budget_planner,
    investment_analysis,
    debt_management,
    retirement_planner,
    tax_optimizer,
)


def section(title: str) -> None:
    print(f"\n{'═' * 60}")
    print(f"  {title}")
    print('═' * 60)


def show(result: dict) -> None:
    print(json.dumps(result, indent=2, ensure_ascii=False))


# ─── 1. Budget Planner ───────────────────────────────────────────────────────
section("1. Budget Planner")

show(budget_planner(
    income=80_000,
    expenses={
        "housing":       22_000,
        "food":          10_000,
        "transport":      5_000,
        "entertainment":  8_000,   # over the 5% limit → flagged
        "utilities":      4_000,
        "healthcare":     2_000,
        "miscellaneous":  3_000,
    }
))

# Edge case — zero income
section("1b. Budget Planner — zero income (edge case)")
show(budget_planner(income=0, expenses={"food": 5000}))

# Edge case — no expenses
section("1c. Budget Planner — no expenses (edge case)")
show(budget_planner(income=50_000, expenses={}))


# ─── 2. Investment Analysis ──────────────────────────────────────────────────
section("2. Investment Analysis — moderate risk, age 32")

show(investment_analysis(
    portfolio={"equity": 250_000, "debt": 200_000, "gold": 20_000, "cash": 30_000},
    risk_tolerance="moderate",
    age=32,
))

# Edge case — empty portfolio
section("2b. Investment Analysis — no portfolio yet")
show(investment_analysis(portfolio={}, risk_tolerance="aggressive", age=25))

# Edge case — invalid risk tolerance
section("2c. Investment Analysis — unknown risk label → defaults to moderate")
show(investment_analysis(
    portfolio={"equity": 100_000},
    risk_tolerance="ultra-risky",
    age=45,
))


# ─── 3. Debt Management ─────────────────────────────────────────────────────
section("3. Debt Management — two debts")

show(debt_management(
    debts=[
        {"name": "credit_card",    "balance": 80_000, "interest_rate": 36.0, "min_payment": 3_200},
        {"name": "personal_loan",  "balance": 200_000, "interest_rate": 14.0, "min_payment": 4_500},
    ],
    monthly_payment=12_000,
))

# Edge case — payment below minimums
section("3b. Debt Management — insufficient payment (edge case)")
show(debt_management(
    debts=[{"name": "loan", "balance": 100_000, "interest_rate": 12.0, "min_payment": 5_000}],
    monthly_payment=3_000,  # below min_payment
))

# Edge case — no debts
section("3c. Debt Management — empty debts list")
show(debt_management(debts=[], monthly_payment=10_000))


# ─── 4. Retirement Planner ──────────────────────────────────────────────────
section("4. Retirement Planner — age 28, retiring at 60")

show(retirement_planner(
    current_age=28,
    retirement_age=60,
    savings=150_000,           # existing PF / investments
    monthly_contribution=8_000, # monthly SIP
))

# Edge case — retirement age already passed
section("4b. Retirement Planner — retirement age ≤ current age (edge case)")
show(retirement_planner(current_age=62, retirement_age=60, savings=0, monthly_contribution=0))

# Edge case — no savings, no contribution
section("4c. Retirement Planner — starting from zero")
show(retirement_planner(current_age=35, retirement_age=60, savings=0, monthly_contribution=0))


# ─── 5. Tax Optimizer ───────────────────────────────────────────────────────
section("5. Tax Optimizer — ₹12L income, partial deductions")

show(tax_optimizer(
    income=1_200_000,
    deductions={
        "80c":  120_000,   # not fully utilised (limit 1.5L)
        "80d":  15_000,    # not fully utilised (limit 25K)
        "nps":  0,         # untapped
        "hra":  60_000,
    }
))

# Edge case — no deductions at all
section("5b. Tax Optimizer — no deductions (edge case)")
show(tax_optimizer(income=800_000, deductions={}))

# Edge case — income below tax threshold
section("5c. Tax Optimizer — income below 7L (new regime rebate)")
show(tax_optimizer(income=650_000, deductions={}))

# Edge case — zero income
section("5d. Tax Optimizer — zero income (edge case)")
show(tax_optimizer(income=0, deductions={}))


print(f"\n{'═' * 60}")
print("  All tests complete.")
print('═' * 60)