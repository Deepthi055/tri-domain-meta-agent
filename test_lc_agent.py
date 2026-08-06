from langchain_agents.career_lc_agent import run as career_run
from langchain_agents.health_lc_agent import run as health_run
from langchain_agents.finance_lc_agent import run as finance_run
import json

class FakeRequest:
    name = "Arjun"
    age = 28
    query = "How do I become a data scientist?"
    current_skills = ["python", "sql"]
    target_role = "data scientist"
    location = "Bangalore"
    experience_level = "mid"
    years_experience = 3
    current_level = "beginner"
    timeline_months = 6
    resume_text = ""
    weight_kg = 75
    height_cm = 175
    sleep_hours = 7
    sleep_quality = 7
    stress_level = 5
    mood_score = 7
    anxiety_level = 4
    fitness_goal = "general fitness"
    available_days = 3
    monthly_income = 50000
    monthly_expenses = 35000
    risk_tolerance = "moderate"
    retirement_age = 60
    retirement_savings = 0
    monthly_contribution = 0

print("=== HEALTH AGENT ===")
req = FakeRequest()
req.query = "I am always tired and stressed at work"
result = health_run(req)
print(json.dumps(result, indent=2))

print("\n=== FINANCE AGENT ===")
req2 = FakeRequest()
req2.query = "How should I manage my debt and plan for retirement?"
result2 = finance_run(req2)
print(json.dumps(result2, indent=2))