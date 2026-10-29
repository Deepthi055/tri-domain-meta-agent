import sys
from types import ModuleType

from langchain_agents import health_lc_agent


def test_health_system_prompt_has_grounding_rules():
    prompt = " ".join(health_lc_agent.SYSTEM_PROMPT.split())

    assert "Use retrieved context as the primary evidence" in prompt
    assert "Cite the exact document title shown in retrieved text" in prompt
    assert "Do not invent source names, statistics, quotations, or document contents" in prompt
    assert "General guidance, not explicitly stated in the knowledge base." in prompt
    assert "Never attribute a claim to a document unless the retrieved text" in prompt
    assert "knowledge base does not contain sufficient evidence" in prompt


def test_health_retrieval_without_text_is_reported_empty(monkeypatch):
    retriever = ModuleType("rag.health_retriever")
    retriever.retrieve = lambda query, top_k: [
        {"source": "health_kb.txt", "text": " "}
    ]
    monkeypatch.setitem(sys.modules, "rag.health_retriever", retriever)
    monkeypatch.setenv("USE_RAG", "true")

    result = health_lc_agent._retrieve_health_context("How can I sleep better?")

    assert result == {"status": "empty", "context": "", "sources": []}
