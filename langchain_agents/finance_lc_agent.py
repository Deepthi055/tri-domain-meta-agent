"""
Finance LangChain Agent — LangChain 1.x + LangGraph
"""
import os
import json
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

load_dotenv()

llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.3-70b-versatile",
    temperature=0.3
)

@tool
def budget_tool(income: float, expenses: dict) -> dict:
    """Analyzes income vs expenses and savings rate.
    Always use this first as baseline for any finance query."""
    from tools.finance_tools import budget_planner
    return budget_planner(income, expenses)

@tool
def investment_tool(portfolio: dict, risk_tolerance: str, age: int) -> dict:
    """Analyzes portfolio and suggests rebalancing.
    Use when user asks about investing, stocks, or mutual funds."""
    from tools.finance_tools import investment_analysis
    return investment_analysis(portfolio, risk_tolerance, age)

@tool
def debt_tool(debts: list, monthly_payment: float) -> dict:
    """Calculates debt payoff using avalanche and snowball methods.
    Use when user mentions loans, EMIs, or credit card debt."""
    from tools.finance_tools import debt_management
    return debt_management(debts, monthly_payment)

@tool
def retirement_tool(current_age: int, retirement_age: int,
                     savings: float, monthly_contribution: float) -> dict:
    """Projects retirement corpus and identifies savings gap.
    Use when user asks about retirement or long-term savings."""
    from tools.finance_tools import retirement_planner
    return retirement_planner(current_age, retirement_age,
                               savings, monthly_contribution)

@tool
def tax_tool(income: float, deductions: dict) -> dict:
    """Compares old vs new tax regime and finds untapped deductions.
    Use when user asks about taxes, ITR, or tax saving."""
    from tools.finance_tools import tax_optimizer
    return tax_optimizer(income, deductions)

SYSTEM_PROMPT = """You are a specialist financial advisor inside a TriDomain AI system.
You have tools for budget planning, investment analysis, debt management,
retirement planning and tax optimization.

RULES:
1. Always use budget_tool first as baseline
2. Use debt_tool when user mentions loans or EMIs
3. Use retirement_tool when user asks about future planning
4. Use tax_tool when user asks about taxes
5. Never recommend high-risk investments without flagging the risk
6. Tailor advice to Indian context — SIP, PPF, NPS, ELSS

After using tools, respond ONLY with valid JSON:
{
    "recommendation": "specific actionable advice",
    "reason": "why this fits this user based on tool results",
    "confidence": 0.85
}"""

tools = [budget_tool, investment_tool, debt_tool, retirement_tool, tax_tool]
finance_agent = create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)

def run(request) -> dict:
    user_input = f"""User profile:
- Name: {request.name}, Age: {request.age}
- Monthly income: Rs.{getattr(request, 'monthly_income', 50000)}
- Monthly expenses: Rs.{getattr(request, 'monthly_expenses', 35000)}
- Risk tolerance: {getattr(request, 'risk_tolerance', 'moderate')}
- Retirement age: {getattr(request, 'retirement_age', 60)}
- Existing savings: Rs.{getattr(request, 'retirement_savings', 0)}
- Monthly SIP: Rs.{getattr(request, 'monthly_contribution', 0)}
- Query: {request.query}

Use your tools and give specific financial advice."""

    try:
        result = finance_agent.invoke({
            "messages": [{"role": "user", "content": user_input}]
        })

        last_msg = result["messages"][-1].content
        match = re.search(r'\{[^{}]*"recommendation"[^{}]*\}', last_msg, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
        else:
            parsed = {
                "recommendation": last_msg,
                "reason": "LangChain agent response",
                "confidence": 0.8
            }

        return {"domain": "finance", "agent_type": "langchain", **parsed}

    except Exception as e:
        print(f"[LangChain Finance] Error: {e} — falling back")
        import agents.finance_agent as original
        result = original.run(request)
        result["agent_type"] = "fallback"
        return result