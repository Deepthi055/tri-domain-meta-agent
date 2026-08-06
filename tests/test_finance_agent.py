"""
tests/test_finance_agent.py
---------------------------
Automated tests for the finance reasoning pipeline.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from agents import finance_agent
from core.intent_detector import detect_intent


def _req(**kwargs) -> SimpleNamespace:
    defaults = {
        "query": "",
        "user_id": None,
        "monthly_income": 80_000.0,
        "monthly_expenses": 55_000.0,
        "savings_goal": 200_000.0,
        "age": 32,
        "risk_tolerance": "moderate",
        "investment_experience": "intermediate",
        "financial_goals": "Buy a home in 5 years",
        "retirement_age": 60,
        "retirement_savings": 500_000.0,
        "current_savings": 100_000.0,
        "monthly_contribution": 10_000.0,
        "total_debt": 300_000.0,
        "monthly_debt_payment": 12_000.0,
        "debts": [],
        "portfolio": {},
        "investments": {},
        "annual_income": 0.0,
        "tax_deductions": {},
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class TestIntentDetection:
    def test_budget_intent(self):
        assert finance_agent._detect_tools("Help me create a monthly budget")[0] == "budget"

    def test_debt_intent(self):
        assert finance_agent._detect_tools("How do I pay off my credit card debt?")[0] == "debt"

    def test_retirement_intent(self):
        assert finance_agent._detect_tools("How much should I save for retirement?")[0] == "retirement"

    def test_tax_intent(self):
        assert finance_agent._detect_tools("Which tax regime is better for me?")[0] == "tax"

    def test_investment_intent(self):
        assert finance_agent._detect_tools("How should I invest my savings in SIP?")[0] == "investments"

    def test_savings_intent(self):
        assert finance_agent._detect_tools("How long to reach my savings goal?")[0] == "savings"

    def test_exactly_one_tool(self):
        tools = finance_agent._detect_tools("I have debt and want a budget")
        assert len(tools) == 1
        assert tools[0] == "debt"


class TestBudgetPipeline:
    def test_budget_generation_shows_calculations(self):
        result = finance_agent.run(_req(
            query="Create a monthly budget for me",
            savings_goal=15_000.0,
        ))
        text = result["recommendation"]
        assert result["tools_used"] == ["budget"]
        assert "Profile Data Used" in text
        assert "Tool Selected" in text
        assert "Budget Planner" in text
        assert "Calculation Steps" in text
        assert "Recommendation" in text
        assert "Confidence Level" in text
        assert "₹" in text
        assert "Monthly Income" in text or "80,000" in text
        assert result["tool_outputs"]["budget"].get("remaining_amount") == 25_000.0

    def test_budget_prompt_uses_budget_planner_only(self):
        result = finance_agent.run(_req(
            query="Create a monthly budget using my profile.",
            monthly_income=35_000.0,
            monthly_expenses=28_000.0,
            savings_goal=10_000.0,
            financial_goals="Save for a down payment",
        ))
        text = result["recommendation"]

        assert result["tools_used"] == ["budget"]
        assert "budget" in result["tool_outputs"]
        assert result["tool_outputs"]["budget"].get("remaining_amount") == 7_000.0
        assert "Budget Planner" in text
        assert "Calculation Steps" in text
        assert "Monthly Income" in text
        assert "Monthly Expenses" in text
        assert "Savings Goal" in text
        assert "Financial Goal" in text
        assert "₹35,000" in text or "₹35,000" in text
        assert "₹28,000" in text or "₹28,000" in text
        assert "₹7,000" in text or "₹7,000" in text
        assert "50-30-20" not in text
        assert "diabetes" not in text.lower()
        assert "sedentary" not in text.lower()
        assert "sleep" not in text.lower()
        assert "BMI" not in text
        assert "percentage" not in text.lower()

    def test_missing_budget_fields(self):
        result = finance_agent.run(_req(
            query="Create my budget",
            monthly_income=None,
            monthly_expenses=None,
        ))
        assert result["confidence_level"] == "Low"
        assert "Missing fields" in result["recommendation"]
        assert "Monthly income" in result["recommendation"]
        assert result["tool_outputs"] == {}


class TestDebtPipeline:
    def test_missing_debt_fields_exact_message(self):
        result = finance_agent.run(_req(
            query="How do I reduce my debt?",
            total_debt=None,
            monthly_debt_payment=0,
        ))
        assert "I don't have your debt information yet." in result["recommendation"]
        assert "Total debt" in result["recommendation"]
        assert "Current monthly repayment" in result["recommendation"]

    def test_debt_without_breakdown_no_duration_estimate(self):
        result = finance_agent.run(_req(
            query="Tell me about my debt",
            total_debt=250_000.0,
            monthly_debt_payment=10_000.0,
            debts=[],
        ))
        out = result["tool_outputs"]["debt"]
        assert out["total_debt"] == 250_000.0
        assert "avalanche" not in out
        assert "months" not in out.get("recommendation", "").lower() or "payoff strategy" in out["recommendation"]


class TestRetirementPipeline:
    def test_retirement_estimation_with_assumptions(self):
        result = finance_agent.run(_req(
            query="Am I on track for retirement?",
            retirement_savings=400_000.0,
            monthly_contribution=8_000.0,
        ))
        out = result["tool_outputs"]["retirement"]
        assert "projected_corpus" in out
        assert "assumptions" in out
        assert "Assumptions" in " ".join(out.get("calculation_steps", []))
        assert result["tools_used"] == ["retirement"]


class TestSavingsPipeline:
    def test_savings_calculation(self):
        result = finance_agent.run(_req(
            query="How long to reach my savings goal?",
            savings_goal=600_000.0,
            current_savings=100_000.0,
        ))
        out = result["tool_outputs"]["savings"]
        assert out["months_to_goal"] is not None
        assert out["months_to_goal"] > 0
        assert result["tools_used"] == ["savings"]

    def test_missing_savings_goal(self):
        result = finance_agent.run(_req(
            query="How much should I save?",
            savings_goal=None,
        ))
        assert "Savings goal" in result["recommendation"]


class TestTaxPipeline:
    def test_tax_calculation(self):
        result = finance_agent.run(_req(
            query="Which tax regime should I choose?",
            annual_income=1_200_000.0,
            tax_deductions={"80c": 120_000, "80d": 15_000},
        ))
        out = result["tool_outputs"]["tax"]
        assert "old_regime" in out
        assert "new_regime" in out
        assert "recommended_regime" in out
        assert result["tools_used"] == ["tax"]

    def test_tax_from_monthly_income(self):
        result = finance_agent.run(_req(
            query="Calculate my income tax",
            annual_income=0.0,
            monthly_income=100_000.0,
        ))
        assert result["tool_outputs"]["tax"]["gross_income"] == 1_200_000.0


class TestInvestmentPipeline:
    def test_investment_recommendation_grounded(self):
        result = finance_agent.run(_req(
            query="How should I allocate my portfolio?",
            portfolio={"equity": 300_000, "debt": 200_000, "gold": 50_000},
            investment_experience="intermediate",
        ))
        out = result["tool_outputs"]["investment"]
        assert "target_allocation" in out
        assert "moderate" in out["recommendation"].lower()
        assert result["tools_used"] == ["investments"]

    def test_missing_investment_experience(self):
        result = finance_agent.run(_req(
            query="Should I invest in mutual funds?",
            investment_experience=None,
        ))
        assert "Investment experience" in result["recommendation"]


class TestMultiDomainRouting:
    def test_pure_finance_stays_finance(self):
        intent = detect_intent("How should I invest my savings?")
        assert intent["domains"] == ["finance"]
        assert "career" not in intent["domains"]
        assert "health" not in intent["domains"]

    def test_multi_domain_detects_multiple(self):
        intent = detect_intent("I want to quit my job and start a business but have debt")
        assert "finance" in intent["domains"]
        assert "career" in intent["domains"]
        assert len(intent["domains"]) >= 2

    def test_finance_agent_does_not_invoke_other_domains(self):
        result = finance_agent.run(_req(query="How do I reduce my credit card debt?"))
        assert result["domain"] == "finance"
        assert "health" not in result
        assert "career" not in result
