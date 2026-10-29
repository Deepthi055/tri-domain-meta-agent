"""
tests/test_finance_agent.py
---------------------------
Automated tests for the finance reasoning pipeline.
"""

from __future__ import annotations

import asyncio
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


@pytest.fixture(autouse=True)
def mock_external_finance_services(monkeypatch):
    monkeypatch.setenv("USE_RAG", "false")
    monkeypatch.setattr(finance_agent, "RAG_AVAILABLE", False)

    def format_deterministic_response(system_prompt, user_message, temperature):
        response = user_message.split(
            "\n\nUSER QUERY:", 1
        )[0].split("PRE-COMPUTED RESPONSE (use as basis — do NOT recalculate):\n", 1)[-1]
        return {"recommendation": response}

    monkeypatch.setattr(
        finance_agent,
        "call_llm",
        format_deterministic_response,
    )


class TestIntentDetection:
    def test_formatter_prompt_has_finance_grounding_rules(self):
        prompt = " ".join(finance_agent.LLM_FORMATTER_PROMPT.split())

        assert "Use retrieved context as the primary evidence" in prompt
        assert "Cite the exact document title shown in retrieved text" in prompt
        assert "Do not invent source names, statistics, quotations, or document contents" in prompt
        assert "General guidance, not explicitly stated in the knowledge base." in prompt
        assert "knowledge base does not contain sufficient evidence" in prompt

    def test_budget_intent(self):
        assert finance_agent._detect_tools("Help me create a monthly budget") == "budget"

    def test_debt_intent(self):
        assert finance_agent._detect_tools("How do I pay off my credit card debt?") == "debt"

    def test_retirement_intent(self):
        assert finance_agent._detect_tools("How much should I save for retirement?") == "retirement"

    def test_tax_intent(self):
        assert finance_agent._detect_tools("Which tax regime is better for me?") == "tax"

    def test_investment_intent(self):
        assert finance_agent._detect_tools("How should I invest my savings in SIP?") == "investments"

    def test_savings_intent(self):
        assert finance_agent._detect_tools("How long to reach my savings goal?") == "savings"

    def test_exactly_one_tool(self):
        tools = finance_agent._detect_tools("I have debt and want a budget")
        assert tools == "debt"

    def test_finance_knowledge_queries_do_not_select_a_tool(self):
        assert finance_agent._detect_tools("Explain the 50-30-20 budgeting rule.") is None
        assert finance_agent._detect_tools(
            "How big should my emergency fund be, and where should I keep it?"
        ) is None


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


def _rag_chunk(text: str, chunk_id: int = 1) -> dict:
    return {
        "source": "finance_kb.txt",
        "chunk_id": chunk_id,
        "relevance_score": 0.91,
        "text": text,
    }


def test_knowledge_query_with_missing_profile_uses_rag_and_llm(monkeypatch):
    retrieved = []
    prompts = []
    monkeypatch.setenv("USE_RAG", "true")
    monkeypatch.setattr(finance_agent, "RAG_AVAILABLE", True)
    monkeypatch.setattr(
        finance_agent,
        "retrieve",
        lambda query: retrieved.append(query) or [
            _rag_chunk(
                "DOCUMENT: Personal Finance Fundamentals\n"
                "The recommended budgeting rule is the 50-30-20 rule."
            )
        ],
    )
    monkeypatch.setattr(
        finance_agent,
        "call_llm",
        lambda system_prompt, user_message, temperature: (
            prompts.append(user_message)
            or {
                "recommendation": (
                    "The 50-30-20 rule allocates income to needs, wants, "
                    "and savings."
                )
            }
        ),
    )

    result = finance_agent.run(_req(
        query="Explain the 50-30-20 budgeting rule.",
        monthly_income=None,
        monthly_expenses=None,
    ))

    assert retrieved == ["Explain the 50-30-20 budgeting rule."]
    assert "The recommended budgeting rule is the 50-30-20 rule." in prompts[0]
    assert "I need your income and expense details" not in result["recommendation"]
    assert result["explainability"]["tool_selected"] is None
    assert result["explainability"]["retrieval_status"] == "success"
    assert result["explainability"]["retrieved_sources"] == [{
        "doc_title": "Personal Finance Fundamentals",
        "chunk_id": 1,
        "score": 0.91,
    }]


def test_emergency_fund_query_uses_context_without_budget_tool(monkeypatch):
    prompts = []
    monkeypatch.setenv("USE_RAG", "true")
    monkeypatch.setattr(finance_agent, "RAG_AVAILABLE", True)
    monkeypatch.setattr(
        finance_agent,
        "retrieve",
        lambda query: [
            _rag_chunk(
                "DOCUMENT: Emergency Fund Guide\n"
                "Students: 3 months of expenses\n"
                "Salaried employees: 6 months of expenses\n"
                "Freelancers or business owners: 9–12 months of expenses."
            )
        ],
    )
    monkeypatch.setattr(
        finance_agent,
        "_run_budget",
        lambda request, query="": pytest.fail("Budget tool must not run"),
    )
    monkeypatch.setattr(
        finance_agent,
        "call_llm",
        lambda system_prompt, user_message, temperature: (
            prompts.append(user_message)
            or {"recommendation": "Use a liquid account for emergency savings."}
        ),
    )

    result = finance_agent.run(_req(
        query="How big should my emergency fund be, and where should I keep it?"
    ))

    assert "Students: 3 months of expenses" in prompts[0]
    assert "Salaried employees: 6 months of expenses" in prompts[0]
    assert "9–12 months of expenses" in prompts[0]
    assert result["explainability"]["tool_selected"] is None
    assert result["tools_used"] == []


@pytest.mark.parametrize(
    "query",
    [
        "Explain the 50-30-20 budgeting rule.",
        "How big should my emergency fund be, and where should I keep it?",
    ],
)
def test_rag_toggle_does_not_change_knowledge_query_tool_selection(
    monkeypatch, query
):
    retrieved = []
    prompts = []
    monkeypatch.setattr(finance_agent, "RAG_AVAILABLE", True)
    monkeypatch.setattr(
        finance_agent,
        "retrieve",
        lambda value: retrieved.append(value) or [
            _rag_chunk("DOCUMENT: Finance Guide\nKnown retrieved sentence.")
        ],
    )
    monkeypatch.setattr(
        finance_agent,
        "call_llm",
        lambda system_prompt, user_message, temperature: (
            prompts.append(user_message) or {"recommendation": "Knowledge answer."}
        ),
    )

    monkeypatch.setenv("USE_RAG", "true")
    enabled = finance_agent.run(_req(query=query))
    monkeypatch.setenv("USE_RAG", "false")
    disabled = finance_agent.run(_req(query=query))

    assert retrieved == [query]
    assert enabled["explainability"]["tool_selected"] is None
    assert disabled["explainability"]["tool_selected"] is None
    assert enabled["explainability"]["tool_selected"] == disabled["explainability"]["tool_selected"]
    assert "Known retrieved sentence." in prompts[0]
    assert "Known retrieved sentence." not in prompts[1]
    assert not disabled["explainability"]["context_in_prompt"]
    assert disabled["explainability"]["retrieval_status"] == "disabled"


def test_budget_tool_and_retrieved_context_both_reach_llm(monkeypatch):
    prompts = []
    monkeypatch.setenv("USE_RAG", "true")
    monkeypatch.setattr(finance_agent, "RAG_AVAILABLE", True)
    monkeypatch.setattr(
        finance_agent,
        "retrieve",
        lambda query: [
            _rag_chunk("DOCUMENT: Budget Guide\nRetrieved budgeting guidance.")
        ],
    )
    monkeypatch.setattr(
        finance_agent,
        "call_llm",
        lambda system_prompt, user_message, temperature: (
            prompts.append(user_message)
            or {"recommendation": "Budget result was reviewed."}
        ),
    )

    result = finance_agent.run(_req(
        query="Make a monthly budget: income 60000, expenses 40000",
        monthly_income=None,
        monthly_expenses=None,
    ))

    assert result["tools_used"] == ["budget"]
    assert result["tool_outputs"]["budget"]["income"] == 60000.0
    assert result["tool_outputs"]["budget"]["total_expenses"] == 40000.0
    assert "Retrieved budgeting guidance." in prompts[0]
    assert '"total_expenses": 40000.0' in prompts[0]


def test_budget_expense_ratio_is_not_reported_as_debt_ratio(monkeypatch):
    monkeypatch.setenv("USE_RAG", "false")

    result = finance_agent.run(_req(
        query="Make a monthly budget",
        monthly_income=30_000.0,
        monthly_expenses=20_000.0,
        monthly_debt_payment=None,
        total_debt=None,
    ))

    assert result["debt_ratio"] is None
    assert result["expense_ratio"] == 66.7
    assert "Expense Ratio: 66.7%" in result["recommendation"]
    assert "Debt-to-Income Ratio" not in result["recommendation"]
    assert "concerning" not in result["recommendation"].lower()


def test_finance_fallback_receives_retrieved_context(monkeypatch):
    from langchain_agents import meta_lc_agent

    prompts = []
    monkeypatch.setenv("USE_RAG", "true")
    monkeypatch.setattr(finance_agent, "RAG_AVAILABLE", True)
    monkeypatch.setattr(
        finance_agent,
        "retrieve",
        lambda query: [
            _rag_chunk("DOCUMENT: Finance Guide\nFallback prompt context.")
        ],
    )
    monkeypatch.setattr(
        meta_lc_agent,
        "finance_run",
        lambda request: (_ for _ in ()).throw(RuntimeError("primary failed")),
    )
    monkeypatch.setattr(
        finance_agent,
        "call_llm",
        lambda system_prompt, user_message, temperature: (
            prompts.append(user_message)
            or {"recommendation": "Fallback answer based on finance context."}
        ),
    )

    response = asyncio.run(meta_lc_agent.meta_lc_agent(SimpleNamespace(
        query="Explain the 50-30-20 rule.",
        domain="finance",
        user_id=None,
        monthly_income=None,
        monthly_expenses=None,
    )))

    assert response["responses"][0]["agent_type"] == "fallback"
    assert "Fallback prompt context." in prompts[0]


def test_five_queries_have_same_tool_selection_with_rag_on_and_off(monkeypatch):
    monkeypatch.setattr(finance_agent, "RAG_AVAILABLE", True)
    monkeypatch.setattr(
        finance_agent,
        "retrieve",
        lambda query: [_rag_chunk("DOCUMENT: Finance Guide\nContext.")],
    )
    queries = [
        "Explain the 50-30-20 rule.",
        "How big should my emergency fund be?",
        "Make a monthly budget",
        "How long to reach my savings goal?",
        "How should I invest my savings in SIP?",
    ]

    for query in queries:
        monkeypatch.setenv("USE_RAG", "true")
        with_rag = finance_agent.run(_req(query=query))
        monkeypatch.setenv("USE_RAG", "false")
        without_rag = finance_agent.run(_req(query=query))
        assert (
            with_rag["explainability"]["tool_selected"]
            == without_rag["explainability"]["tool_selected"]
        )


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
