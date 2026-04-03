import os
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import agents.career_agent as career
import agents.health_agent as health
import agents.finance_agent as finance

load_dotenv()
app = FastAPI(title="TriDomain Meta-Agent", version="0.3.0")

# ── Input Model ───────────────────────────────────────────────────────
class QueryRequest(BaseModel):
    name: str
    age: int
    domain: str
    query: str
    weight_kg: float = 70.0
    height_cm: float = 170.0
    monthly_income: float = 50000.0
    monthly_expenses: float = 35000.0
    current_skills: list = []          
    target_role: str = "data scientist" 

# ── Meta-Agent Router ─────────────────────────────────────────────────
def meta_agent(request: QueryRequest):
    if request.domain == "career":
        return career.run(request)
    elif request.domain == "health":
        return health.run(request)
    elif request.domain == "finance":
        return finance.run(request)
    elif request.domain == "general":
        return {
            "domain": "general",
            "message": "Please specify a domain.",
            "options": ["career", "health", "finance"]
        }
    else:
        return {"error": f"Unknown domain: '{request.domain}'"}

# ── Routes ────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "live", "system": "TriDomain Meta-Agent v0.3"}

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