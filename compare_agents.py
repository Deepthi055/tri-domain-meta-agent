"""compare_agents.py — extended for all 3 domains"""
import time
import json
from langchain_agents.career_lc_agent import run as career_lc_run
from langchain_agents.health_lc_agent import run as health_lc_run
from langchain_agents.finance_lc_agent import run as finance_lc_run
import agents.career_agent as career_original
import agents.health_agent as health_original
import agents.finance_agent as finance_original

class FakeRequest:
    name = "Arjun"
    age = 28
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

def compare(domain_name, original_fn, lc_fn, query):
    req = FakeRequest()
    req.query = query

    start = time.time()
    orig = original_fn(req)
    orig_time = round((time.time() - start) * 1000)

    start = time.time()
    lc = lc_fn(req)
    lc_time = round((time.time() - start) * 1000)

    speedup = round(orig_time / lc_time, 1) if lc_time > 0 else 0

    print(f"\n{'='*60}")
    print(f"{domain_name.upper()}")
    print(f"{'='*60}")
    print(f"Original:  {orig_time}ms")
    print(f"LangChain: {lc_time}ms")
    print(f"Speedup:   {speedup}x")

    return {
        "domain": domain_name,
        "original_ms": orig_time,
        "langchain_ms": lc_time,
        "speedup": speedup
    }

results = []
results.append(compare("career", career_original.run, career_lc_run,
                       "How do I become a data scientist?"))
results.append(compare("health", health_original.run, health_lc_run,
                       "I am always tired and stressed"))
results.append(compare("finance", finance_original.run, finance_lc_run,
                       "How should I manage my debt?"))

print(f"\n{'='*60}")
print("SUMMARY")
print(f"{'='*60}")
avg_speedup = sum(r['speedup'] for r in results) / len(results)
print(f"Average speedup: {avg_speedup:.1f}x")

with open("comparison_results.json", "w") as f:
    json.dump(results, f, indent=2)