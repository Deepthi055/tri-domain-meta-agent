from fastapi import FastAPI
from pydantic import BaseModel
import json

app = FastAPI(title="TriDomain Meta-Agent", version="0.1.0")

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

# ── Tool Functions ────────────────────────────────────────────────────
def calculate_bmi(weight_kg, height_cm):
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"
    return {"bmi": round(bmi, 1), "category": category}

def calculate_savings(income, expenses):
    savings = income - expenses
    rate = (savings / income) * 100
    return {"savings": savings, "rate_pct": round(rate, 1)}

def calculate_debt_ratio(income, expenses):
    ratio = expenses / income
    status = "healthy" if ratio < 0.5 else "concerning"
    return {"debt_to_income_ratio": round(ratio, 2), "status": status}

# ── Agents ────────────────────────────────────────────────────────────
def career_agent(request: QueryRequest):
    return {
        "domain": "career",
        "recommendation": "PLACEHOLDER",
        "reason": "LLM response in Phase 2",
        "confidence": 0.0
    }

def health_agent(request: QueryRequest):
    bmi_data = calculate_bmi(request.weight_kg, request.height_cm)
    return {
        "domain": "health",
        "bmi": bmi_data,
        "recommendation": "PLACEHOLDER",
        "confidence": 0.0
    }

def finance_agent(request: QueryRequest):
    savings_data = calculate_savings(
        request.monthly_income,
        request.monthly_expenses
    )
    debt_data = calculate_debt_ratio(
        request.monthly_income,
        request.monthly_expenses
    )
    return {
        "domain": "finance",
        "savings": savings_data,
        "debt_ratio": debt_data,
        "recommendation": "PLACEHOLDER",
        "confidence": 0.0
    }

# ── Meta-Agent ────────────────────────────────────────────────────────
def meta_agent(request: QueryRequest):
    if request.domain == "career":
        return career_agent(request)
    elif request.domain == "health":
        return health_agent(request)
    elif request.domain == "finance":
        return finance_agent(request)
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
    return {"status": "live", "system": "TriDomain Meta-Agent v0.1"}

@app.post("/query")
def handle_query(request: QueryRequest):
    result = meta_agent(request)
    return result

@app.get("/health-check")
def health_check():
    return {"status": "ok"}

@app.get("/domains")
def get_domains():
    return {
        "domains": [
            {"name": "career", "description": "Career guidance, skill gaps, job switching advice"},
            {"name": "health", "description": "BMI analysis, fitness, and wellness recommendations"},
            {"name": "finance", "description": "Savings rate, debt ratio, and budget planning"}
        ]
    }