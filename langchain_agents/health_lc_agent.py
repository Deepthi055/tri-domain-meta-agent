"""
Health LangChain Agent — LangChain 1.x + LangGraph
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
def bmi_tool(weight_kg: float, height_cm: float) -> dict:
    """Calculates BMI and health category.
    Always use this first for any health query."""
    from tools.calculators import calculate_bmi
    return calculate_bmi(weight_kg, height_cm)

@tool
def fitness_score_tool(age: int, weight_kg: float, height_cm: float,
                        sleep_quality: int, stress_level: int,
                        mood_score: int, available_days: int) -> dict:
    """Calculates overall fitness score out of 100.
    Use for fitness assessment queries."""
    from tools.calculators import fitness_score
    return fitness_score(age, weight_kg, height_cm,
                         sleep_quality, stress_level, mood_score, available_days)

@tool
def sleep_analysis_tool(sleep_hours: float, bedtime: str,
                         wakeup_time: str, sleep_quality: int) -> dict:
    """Analyzes sleep patterns and gives sleep score.
    Use when user mentions tiredness or sleep issues."""
    from tools.calculators import sleep_analysis
    return sleep_analysis(sleep_hours, bedtime, wakeup_time, sleep_quality)

@tool
def mental_health_tool(mood_score: int, stress_level: int,
                        anxiety_level: int) -> dict:
    """Assesses mental wellness and flags high risk.
    Use when user mentions stress, anxiety, or burnout."""
    from tools.calculators import mental_health_tracker
    return mental_health_tracker(mood_score, stress_level, anxiety_level)

@tool
def workout_planner_tool(fitness_goal: str, experience_level: str,
                          available_days: int) -> dict:
    """Creates personalized workout plan.
    Use when user asks about exercise routines."""
    from tools.calculators import workout_planner
    return workout_planner(fitness_goal, experience_level, available_days)

SYSTEM_PROMPT = """You are a specialist health advisor inside a TriDomain AI system.
You have tools for BMI, fitness, sleep, mental health and workout planning.

RULES:
1. Always use bmi_tool first
2. Use sleep_analysis_tool when user mentions tiredness
3. Use mental_health_tool when user mentions stress or anxiety
4. Never recommend extreme diets or dangerous exercise
5. Always suggest consulting a doctor for medical conditions
6. If mental health risk_flag is True, recommend professional help

After using tools, respond ONLY with valid JSON:
{
    "recommendation": "specific actionable advice",
    "reason": "why this fits this user based on tool results",
    "confidence": 0.85
}"""

tools = [bmi_tool, fitness_score_tool, sleep_analysis_tool,
         mental_health_tool, workout_planner_tool]
health_agent = create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)

def run(request) -> dict:
    user_input = f"""User profile:
- Name: {request.name}, Age: {request.age}
- Weight: {getattr(request, 'weight_kg', 70)}kg
- Height: {getattr(request, 'height_cm', 170)}cm
- Sleep hours: {getattr(request, 'sleep_hours', 7)}
- Sleep quality: {getattr(request, 'sleep_quality', 7)}/10
- Stress level: {getattr(request, 'stress_level', 5)}/10
- Mood score: {getattr(request, 'mood_score', 7)}/10
- Anxiety level: {getattr(request, 'anxiety_level', 4)}/10
- Fitness goal: {getattr(request, 'fitness_goal', 'general fitness')}
- Available days: {getattr(request, 'available_days', 3)}
- Query: {request.query}

Use your tools and give specific health advice."""

    try:
        result = health_agent.invoke({
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

        return {"domain": "health", "agent_type": "langchain", **parsed}

    except Exception as e:
        print(f"[LangChain Health] Error: {e} — falling back")
        import agents.health_agent as original
        result = original.run(request)
        result["agent_type"] = "fallback"
        return result