"""
Career LangChain Agent — LangChain 1.x + LangGraph
Uses create_react_agent from langgraph.prebuilt
"""
import os
import json
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

load_dotenv()

# ── LLM ──────────────────────────────────────────────────────
llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.3-70b-versatile",
    temperature=0.7
)

# ── Tools ─────────────────────────────────────────────────────
@tool
def skill_gap_tool(current_skills: list, target_role: str) -> dict:
    """Analyzes skill gap between current skills and target role.
    Returns match percentage and missing skills.
    Use when user wants to switch roles or learn new skills."""
    from tools.calculators import skill_gap_analyzer
    return skill_gap_analyzer(current_skills, target_role)

@tool
def job_search_tool(current_skills: list, location: str, experience_level: str) -> dict:
    """Finds job matches based on skills, location and experience.
    Use when user asks about job opportunities or market demand."""
    from tools.calculators import job_search
    return job_search(current_skills, location, experience_level)

@tool
def salary_benchmark_tool(target_role: str, location: str, years_experience: int) -> dict:
    """Returns salary benchmarks for a role in a location.
    Use when user asks about salary expectations or negotiation."""
    from tools.calculators import salary_benchmark
    return salary_benchmark(target_role, location, years_experience)

@tool
def learning_path_tool(target_role: str, current_level: str, timeline_months: int) -> dict:
    """Generates structured learning path to reach a target role.
    Use when user asks how to learn or transition into a role."""
    from tools.calculators import learning_path_generator
    return learning_path_generator(target_role, current_level, timeline_months)

# ── System prompt ─────────────────────────────────────────────
SYSTEM_PROMPT = """You are a specialist career advisor inside a TriDomain AI system.
You have tools for skill gap analysis, job search, salary benchmarking and learning paths.

RULES:
1. Always use skill_gap_tool if user mentions a target role
2. Always use salary_benchmark_tool for salary expectations
3. Never recommend quitting without a financial safety plan
4. Tailor advice to the Indian job market

After using tools, respond ONLY with valid JSON:
{
    "recommendation": "specific actionable advice",
    "reason": "why this fits this user based on tool results",
    "confidence": 0.85
}"""

# ── Agent ─────────────────────────────────────────────────────
tools = [skill_gap_tool, job_search_tool, salary_benchmark_tool, learning_path_tool]
career_agent = create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)

# ── Run ───────────────────────────────────────────────────────
def run(request) -> dict:
    user_input = f"""User profile:
- Name: {request.name}, Age: {request.age}
- Query: {request.query}
- Current skills: {getattr(request, 'current_skills', [])}
- Target role: {getattr(request, 'target_role', 'data scientist')}
- Location: {getattr(request, 'location', 'Bangalore')}
- Experience: {getattr(request, 'experience_level', 'mid')} ({getattr(request, 'years_experience', 3)} years)
- Timeline: {getattr(request, 'timeline_months', 6)} months

Use your tools and give specific career advice."""

    try:
        result = career_agent.invoke({
            "messages": [{"role": "user", "content": user_input}]
        })

        # Get last message content
        last_msg = result["messages"][-1].content

        # Extract JSON
        match = re.search(r'\{[^{}]*"recommendation"[^{}]*\}', last_msg, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
        else:
            parsed = {
                "recommendation": last_msg,
                "reason": "LangChain agent response",
                "confidence": 0.8
            }

        return {
            "domain":      "career",
            "agent_type":  "langchain",
            **parsed
        }

    except Exception as e:
        print(f"[LangChain Career] Error: {e} — falling back")
        import agents.career_agent as original
        result = original.run(request)
        result["agent_type"] = "fallback"
        return result