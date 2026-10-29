from types import SimpleNamespace

from agents import finance_agent, health_agent


def test_finance_rag_respects_use_rag_environment_variable(monkeypatch):
    retrieved = []
    monkeypatch.setenv("USE_RAG", "false")
    monkeypatch.setattr(finance_agent, "RAG_AVAILABLE", True)
    monkeypatch.setattr(
        finance_agent,
        "retrieve",
        lambda query: retrieved.append(query) or [{
            "source": "finance_kb.txt",
            "chunk_id": 0,
            "relevance_score": 0.9,
            "text": "retrieved finance context",
        }],
    )

    result = finance_agent.run(SimpleNamespace(
        query="How should I invest my savings in SIP?",
        user_id=None,
        monthly_income=80_000.0,
        monthly_expenses=55_000.0,
        savings_goal=200_000.0,
        age=32,
        risk_tolerance="moderate",
        investment_experience="intermediate",
        financial_goals="Buy a home in 5 years",
        retirement_age=60,
        retirement_savings=500_000.0,
        current_savings=100_000.0,
        monthly_contribution=10_000.0,
        total_debt=300_000.0,
        monthly_debt_payment=12_000.0,
        debts=[],
        portfolio={},
        investments={},
        annual_income=0.0,
        tax_deductions={},
    ))

    assert retrieved == []
    assert "rag_context" not in result["tool_outputs"]


def test_health_rag_respects_use_rag_environment_variable(monkeypatch):
    retrieved = []
    llm_messages = []
    monkeypatch.setenv("USE_RAG", "false")
    monkeypatch.setattr(health_agent, "RAG_AVAILABLE", True)
    monkeypatch.setattr(
        health_agent,
        "retrieve_as_context",
        lambda query, top_k: retrieved.append(query) or "retrieved health context",
    )
    monkeypatch.setattr(
        health_agent,
        "call_llm",
        lambda system_prompt, user_message, temperature: (
            llm_messages.append(user_message) or {
                "recommendation": "Rest consistently.",
                "reason": "Sleep supports well-being.",
                "confidence": 0.8,
            }
        ),
    )

    health_agent.run(SimpleNamespace(
        query="How can I improve my sleep?",
        name="Test User",
        age=32,
        weight_kg=70,
        height_cm=170,
    ))

    assert retrieved == []
    assert len(llm_messages) == 1
    assert "retrieved health context" not in llm_messages[0]
