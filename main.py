import os
import asyncio
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from concurrent.futures import ThreadPoolExecutor
import agents.career_agent as career
import agents.health_agent as health
import agents.finance_agent as finance
from core.intent_detector import detect_intent
from core.safety_layer import check_safety, check_relevance

load_dotenv()

BASE_DIR   = Path(__file__).resolve().parent
INDEX_FILE = BASE_DIR / "index.html"

app = FastAPI(title="TriDomain Meta-Agent", version="0.6.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thread pool — one thread per agent max
executor = ThreadPoolExecutor(max_workers=3)

# ── Input Model ───────────────────────────────────────────────
class QueryRequest(BaseModel):
    name:  str
    age:   int
    query: str
    domain: str = "auto"
    current_skills:   list  = []
    target_role:      str   = "data scientist"
    location:         str   = "Bangalore"
    experience_level: str   = "mid"
    years_experience: int   = 3
    current_level:    str   = "beginner"
    timeline_months:  int   = 6
    resume_text:      str   = ""
    weight_kg:          float = 70.0
    height_cm:          float = 170.0
    gender:             str   = "male"
    fitness_goal:       str   = "general fitness"
    fitness_experience: str   = "beginner"
    available_days:     int   = 3
    meals:              list  = ["rice", "dal", "vegetables"]
    nutritional_goal:   str   = "general health"
    sleep_hours:        float = 7.0
    bedtime:            str   = "23:00"
    wakeup_time:        str   = "06:00"
    sleep_quality:      int   = 7
    mood_score:         int   = 7
    stress_level:       int   = 5
    anxiety_level:      int   = 4
    last_checkup_months_ago: int = 12
    monthly_income:       float = 50_000.0
    monthly_expenses:     float = 35_000.0
    current_savings:      float = 0.0
    expenses:             dict  = {}
    portfolio:            dict  = {}
    risk_tolerance:       str   = "moderate"
    debts:                list  = []
    monthly_debt_payment: float = 0.0
    retirement_age:       int   = 60
    retirement_savings:   float = 0.0
    monthly_contribution: float = 0.0
    annual_income:        float = 0.0
    tax_deductions:       dict  = {}

# ── Parallel agent runner ─────────────────────────────────────
async def run_agents_parallel(domains: list, request: QueryRequest) -> list:
    """
    Runs all active domain agents simultaneously using threads.
    Each agent runs in its own thread — truly parallel.
    """
    agent_map = {
        "career":  career.run,
        "health":  health.run,
        "finance": finance.run,
    }

    loop = asyncio.get_event_loop()

    def run_one(domain):
        """Runs a single agent — called in thread pool."""
        try:
            fn = agent_map.get(domain)
            if fn:
                return fn(request)
            return {
                "domain":  domain,
                "message": "Please specify a domain.",
                "options": ["career", "health", "finance"]
            }
        except Exception as exc:
            return {
                "domain":  domain,
                "error":   "agent_failure",
                "message": f"{domain} agent failed",
                "reason":  str(exc)
            }

    # Submit all agents to thread pool simultaneously
    futures = [
        loop.run_in_executor(executor, run_one, domain)
        for domain in domains
    ]

    # Wait for ALL to finish (not one by one)
    results = await asyncio.gather(*futures)
    return list(results)

# ── Meta-Agent ────────────────────────────────────────────────
async def meta_agent(request: QueryRequest) -> dict:

    # Step 1 — Safety
    safety = check_safety(request.query)
    if not safety["is_safe"]:
        return {
            "status":            "blocked",
            "reason":            safety["reason"],
            "message":           safety["message"],
            "domains_activated": []
        }

    # Step 2 — Relevance
    relevance = check_relevance(request.query)
    if not relevance["is_relevant"]:
        return {
            "status":            "out_of_scope",
            "message":           relevance["message"],
            "domains_activated": []
        }

    # Step 3 — Intent
    if request.domain == "auto":
        intent  = detect_intent(request.query)
        domains = intent["domains"]
    else:
        intent = {
            "domains":    [request.domain],
            "confidence": 1.0,
            "reasoning":  "Manual domain selection"
        }
        domains = [request.domain]

    # Step 4 — Run agents in parallel ─────────────────────────
    responses = await run_agents_parallel(domains, request)

    # Step 5 — Build response
    result = {
        "status":            "success",
        "intent":            intent,
        "responses":         responses,
        "domains_activated": domains
    }

    if safety.get("is_sensitive"):
        result["warning"] = safety["message"]

    return result

# ── Routes ────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
def root():
    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE)
    return {"status": "live", "system": "TriDomain Meta-Agent v0.6"}

@app.get("/api-status")
def api_status():
    return {"status": "live", "system": "TriDomain Meta-Agent v0.6"}

@app.post("/query")
async def handle_query(request: QueryRequest):
    return await meta_agent(request)

@app.get("/domains")
def get_domains():
    return {
        "domains": [
            {"name": "career",  "description": "Career guidance, skill gaps, job switching advice"},
            {"name": "health",  "description": "BMI analysis, fitness, and wellness recommendations"},
            {"name": "finance", "description": "Budgeting, investments, debt, retirement, and tax planning"},
        ]
    }

@app.get("/health-check")
def health_check():
    return {"status": "ok"}