import os
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import agents.career_agent as career
import agents.health_agent as health
import agents.finance_agent as finance
from core.intent_detector import detect_intent

load_dotenv()

app = FastAPI(title="TriDomain Meta-Agent", version="0.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Input Model ───────────────────────────────────────────────────────
class QueryRequest(BaseModel):
    name: str
    age: int
    query: str
    domain: str = "auto"
    weight_kg: float = 70.0
    height_cm: float = 170.0
    monthly_income: float = 50000.0
    monthly_expenses: float = 35000.0
    current_savings: float = 0.0
    current_skills: list = []
    target_role: str = "data scientist"
    location: str = "Bangalore"
    experience_level: str = "mid"
    years_experience: int = 3
    current_level: str = "beginner"
    timeline_months: int = 6
    resume_text: str = ""
    # ── Health fields ──────────────────────────
    gender: str = "male"
    fitness_goal: str = "general fitness"
    fitness_experience: str = "beginner"
    available_days: int = 3
    meals: list = ["rice", "dal", "vegetables"]
    nutritional_goal: str = "general health"
    sleep_hours: float = 7.0
    bedtime: str = "23:00"
    wakeup_time: str = "06:00"
    sleep_quality: int = 7
    mood_score: int = 7
    stress_level: int = 5
    anxiety_level: int = 4
    last_checkup_months_ago: int = 12
# ── Meta-Agent ────────────────────────────────────────────────────────
def meta_agent(request: QueryRequest) -> dict:

    if request.domain == "auto":
        intent = detect_intent(request.query)
        domains = intent["domains"]
    else:
        intent = {
            "domains": [request.domain],
            "confidence": 1.0,
            "reasoning": "Manual domain selection"
        }
        domains = [request.domain]

    responses = []
    for domain in domains:
        if domain == "career":
            responses.append(career.run(request))
        elif domain == "health":
            responses.append(health.run(request))
        elif domain == "finance":
            responses.append(finance.run(request))
        elif domain == "general":
            responses.append({
                "domain": "general",
                "message": "Please specify a domain.",
                "options": ["career", "health", "finance"]
            })

    return {
        "intent": intent,
        "responses": responses,
        "domains_activated": domains
    }

# ── Routes ────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "live", "system": "TriDomain Meta-Agent v0.4"}

@app.post("/query")
def handle_query(request: QueryRequest):
    return meta_agent(request)

@app.get("/domains")
def get_domains():
    return {
        "domains": [
            {"name": "career", "description": "Career guidance, skill gaps, job switching advice"},
            {"name": "health", "description": "BMI analysis, fitness, and wellness recommendations"},
            {"name": "finance", "description": "Savings rate, debt ratio, and budget planning"}
        ]
    }

@app.get("/health-check")
def health_check():
    return {"status": "ok"}