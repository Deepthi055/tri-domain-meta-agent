"""
Finance LangChain Agent — thin wrapper around the profile-grounded tool pipeline.

All calculations run in tools/finance_tools.py via agents/finance_agent.py.
The ReAct LangChain agent was replaced to guarantee mandatory tool execution.
"""
from __future__ import annotations

import agents.finance_agent as finance_agent


def run(request) -> dict:
    """Run the canonical finance pipeline (profile → tools → structured response)."""
    result = finance_agent.run(request)
    result["agent_type"] = "tool_pipeline"
    return result
