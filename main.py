# import os
# from fastapi import FastAPI
# from pydantic import BaseModel
# from dotenv import load_dotenv
# from fastapi.middleware.cors import CORSMiddleware
# import agents.career_agent as career
# import agents.health_agent as health
# import agents.finance_agent as finance
# from core.intent_detector import detect_intent

# load_dotenv()

# app = FastAPI(title="TriDomain Meta-Agent", version="0.4.0")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ── Input Model ───────────────────────────────────────────────────────
# class QueryRequest(BaseModel):
#     name: str
#     age: int
#     query: str
#     domain: str = "auto"
#     weight_kg: float = 70.0
#     height_cm: float = 170.0
#     monthly_income: float = 50000.0
#     monthly_expenses: float = 35000.0
#     current_savings: float = 0.0
#     current_skills: list = []
#     target_role: str = "data scientist"
#     location: str = "Bangalore"
#     experience_level: str = "mid"
#     years_experience: int = 3
#     current_level: str = "beginner"
#     timeline_months: int = 6
#     resume_text: str = ""
#     # ── Health fields ──────────────────────────
#     gender: str = "male"
#     fitness_goal: str = "general fitness"
#     fitness_experience: str = "beginner"
#     available_days: int = 3
#     meals: list = ["rice", "dal", "vegetables"]
#     nutritional_goal: str = "general health"
#     sleep_hours: float = 7.0
#     bedtime: str = "23:00"
#     wakeup_time: str = "06:00"
#     sleep_quality: int = 7
#     mood_score: int = 7
#     stress_level: int = 5
#     anxiety_level: int = 4
#     last_checkup_months_ago: int = 12
# # ── Meta-Agent ────────────────────────────────────────────────────────
# def meta_agent(request: QueryRequest) -> dict:

#     if request.domain == "auto":
#         intent = detect_intent(request.query)
#         domains = intent["domains"]
#     else:
#         intent = {
#             "domains": [request.domain],
#             "confidence": 1.0,
#             "reasoning": "Manual domain selection"
#         }
#         domains = [request.domain]

#     responses = []
#     for domain in domains:
#         if domain == "career":
#             responses.append(career.run(request))
#         elif domain == "health":
#             responses.append(health.run(request))
#         elif domain == "finance":
#             responses.append(finance.run(request))
#         elif domain == "general":
#             responses.append({
#                 "domain": "general",
#                 "message": "Please specify a domain.",
#                 "options": ["career", "health", "finance"]
#             })

#     return {
#         "intent": intent,
#         "responses": responses,
#         "domains_activated": domains
#     }

# # ── Routes ────────────────────────────────────────────────────────────
# @app.get("/")
# def root():
#     return {"status": "live", "system": "TriDomain Meta-Agent v0.4"}

# @app.post("/query")
# def handle_query(request: QueryRequest):
#     return meta_agent(request)

# @app.get("/domains")
# def get_domains():
#     return {
#         "domains": [
#             {"name": "career", "description": "Career guidance, skill gaps, job switching advice"},
#             {"name": "health", "description": "BMI analysis, fitness, and wellness recommendations"},
#             {"name": "finance", "description": "Savings rate, debt ratio, and budget planning"}
#         ]
#     }

# @app.get("/health-check")
# def health_check():
#     return {"status": "ok"}



import os
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import agents.career_agent as career
import agents.health_agent as health
import agents.finance_agent as finance
from core.intent_detector import detect_intent
from core.safety_layer import check_safety, check_relevance

load_dotenv()

app = FastAPI(title="TriDomain Meta-Agent", version="0.5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Input Model ───────────────────────────────────────────────────────────────
class QueryRequest(BaseModel):

    # ── Core identity (always required) ──────────────────────────────────────
    name:  str
    age:   int
    query: str
    domain: str = "auto"          # "auto" → intent detection; or force a domain

    # ── Career fields ─────────────────────────────────────────────────────────
    current_skills:   list = []
    target_role:      str  = "data scientist"
    location:         str  = "Bangalore"
    experience_level: str  = "mid"
    years_experience: int  = 3
    current_level:    str  = "beginner"
    timeline_months:  int  = 6
    resume_text:      str  = ""

    # ── Health fields ─────────────────────────────────────────────────────────
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

    # ── Finance — basic (always present) ─────────────────────────────────────
    monthly_income:   float = 50_000.0
    monthly_expenses: float = 35_000.0
    current_savings:  float = 0.0

    # ── Finance — Budget Planner ──────────────────────────────────────────────
    # Categorised expenses dict. If supplied, used instead of monthly_expenses.
    # Example: {"housing": 15000, "food": 6000, "transport": 3000}
    expenses: dict = {}

    # ── Finance — Investment Analysis ─────────────────────────────────────────
    # Example: {"equity": 200000, "debt": 100000, "gold": 50000}
    portfolio:      dict = {}
    risk_tolerance: str  = "moderate"    # conservative | moderate | aggressive

    # ── Finance — Debt Management ─────────────────────────────────────────────
    # Each item: {name, balance, interest_rate (annual %), min_payment}
    # Example: [{"name": "credit card", "balance": 50000,
    #            "interest_rate": 36, "min_payment": 2000}]
    debts:                list  = []
    monthly_debt_payment: float = 0.0    # total monthly budget for all debts

    # ── Finance — Retirement Planner ─────────────────────────────────────────
    retirement_age:       int   = 60
    retirement_savings:   float = 0.0    # existing corpus / EPF / PF balance
    monthly_contribution: float = 0.0    # monthly SIP / EPF contribution

    # ── Finance — Tax Optimizer ───────────────────────────────────────────────
    annual_income:  float = 0.0          # overrides monthly_income × 12 if > 0
    # Example: {"80c": 120000, "80d": 20000, "nps": 50000, "hra": 60000}
    tax_deductions: dict  = {}


# ── Meta-Agent ────────────────────────────────────────────────────────────────
def meta_agent(request: QueryRequest) -> dict:

    # ── Step 1: Safety Check ──────────────────────────────────────────
    safety = check_safety(request.query)

    if not safety["is_safe"]:
        return {
            "status":            "blocked",
            "reason":            safety["reason"],
            "message":           safety["message"],
            "domains_activated": []
        }

    # ── Step 2: Relevance Check ───────────────────────────────────────
    relevance = check_relevance(request.query)

    if not relevance["is_relevant"]:
        return {
            "status":            "out_of_scope",
            "message":           relevance["message"],
            "domains_activated": []
        }

    # ── Step 3: Intent Detection ──────────────────────────────────────
    if request.domain == "auto":
        intent  = detect_intent(request.query)
        domains = intent["domains"]
    else:
        intent = {
<<<<<<< HEAD
            "domains":    [request.domain],
            "confidence": 1.0,
            "reasoning":  "Manual domain selection"
=======
            "domains":   [request.domain],
            "confidence": 1.0,
            "reasoning":  "Manual domain selection",
>>>>>>> 913d84b (Update QueryRequest model with detailed fields for career, health, and finance domains, enhance finance-related features, and increment API version to 0.5.0)
        }
        domains = [request.domain]

    # ── Step 4: Route to Agents ───────────────────────────────────────
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
                "domain":  "general",
                "message": "Please specify a domain.",
                "options": ["career", "health", "finance"],
            })

<<<<<<< HEAD
    # ── Step 5: Build Response ────────────────────────────────────────
    result = {
        "status":            "success",
        "intent":            intent,
        "responses":         responses,
        "domains_activated": domains
    }

    # Add warning for sensitive topics
    if safety["is_sensitive"]:
        result["warning"] = safety["message"]

    return result
# ── Routes ────────────────────────────────────────────────────────────
=======
    return {
        "intent":           intent,
        "responses":        responses,
        "domains_activated": domains,
    }


# ── Routes ────────────────────────────────────────────────────────────────────
>>>>>>> 913d84b (Update QueryRequest model with detailed fields for career, health, and finance domains, enhance finance-related features, and increment API version to 0.5.0)
@app.get("/")
def root():
    return {"status": "live", "system": "TriDomain Meta-Agent v0.5"}


@app.post("/query")
def handle_query(request: QueryRequest):
    return meta_agent(request)


@app.get("/domains")
def get_domains():
    return {
        "domains": [
            {
                "name":        "career",
                "description": "Career guidance, skill gaps, job switching advice",
            },
            {
                "name":        "health",
                "description": "BMI analysis, fitness, and wellness recommendations",
            },
            {
                "name":        "finance",
                "description": "Budgeting, investments, debt, retirement, and tax planning",
            },
        ]
    }


@app.get("/health-check")
def health_check():
    return {"status": "ok"}