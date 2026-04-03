import os
import json
from fastapi import FastAPI
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="TriDomain Meta-Agent", version="0.2.0")

# ── LLM Client (shared across all agents) ─────────────────────────────
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

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

# ── LLM Helper ────────────────────────────────────────────────────────
def call_llm(system_prompt: str, user_message: str, temperature: float = 0.7):
    """
    Single function all agents use to call the LLM.
    Returns parsed JSON dict or error dict.
    """
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=temperature,
            max_tokens=500
        )
        raw = response.choices[0].message.content

        # Strip markdown code fences if LLM wraps response in ```json
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]

        return json.loads(clean)

    except json.JSONDecodeError:
        return {
            "recommendation": raw,
            "reason": "LLM returned unstructured text",
            "confidence": 0.5
        }
    except Exception as e:
        return {
            "recommendation": "Service temporarily unavailable",
            "reason": str(e),
            "confidence": 0.0
        }

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
    system_prompt = """You are an expert career advisor inside a multi-agent AI system.
Your job is to give specific, actionable career guidance.

CRITICAL: Respond ONLY with valid JSON in exactly this format, nothing else:
{
    "recommendation": "specific actionable advice here",
    "reason": "why this advice fits this specific user",
    "confidence": 0.85
}"""

    user_message = f"""User profile:
- Name: {request.name}
- Age: {request.age}
- Query: {request.query}

Give career advice based on this profile."""

    llm_response = call_llm(system_prompt, user_message, temperature=0.7)
    return {"domain": "career", **llm_response}


def health_agent(request: QueryRequest):
    bmi_data = calculate_bmi(request.weight_kg, request.height_cm)

    system_prompt = """You are an expert health advisor inside a multi-agent AI system.
Your job is to give specific, actionable health guidance based on the user's metrics.

CRITICAL: Respond ONLY with valid JSON in exactly this format, nothing else:
{
    "recommendation": "specific actionable advice here",
    "reason": "why this advice fits this specific user",
    "confidence": 0.85
}"""

    user_message = f"""User profile:
- Name: {request.name}
- Age: {request.age}
- Weight: {request.weight_kg}kg
- Height: {request.height_cm}cm
- BMI: {bmi_data['bmi']} ({bmi_data['category']})
- Query: {request.query}

Give health advice based on this profile."""

    llm_response = call_llm(system_prompt, user_message, temperature=0.3)
    return {"domain": "health", "bmi": bmi_data, **llm_response}


def finance_agent(request: QueryRequest):
    savings_data = calculate_savings(request.monthly_income, request.monthly_expenses)
    debt_data = calculate_debt_ratio(request.monthly_income, request.monthly_expenses)

    system_prompt = """You are an expert financial advisor inside a multi-agent AI system.
Your job is to give specific, actionable financial guidance based on the user's numbers.

CRITICAL: Respond ONLY with valid JSON in exactly this format, nothing else:
{
    "recommendation": "specific actionable advice here",
    "reason": "why this advice fits this specific user",
    "confidence": 0.85
}"""

    user_message = f"""User profile:
- Name: {request.name}
- Age: {request.age}
- Monthly Income: ₹{request.monthly_income}
- Monthly Expenses: ₹{request.monthly_expenses}
- Savings: ₹{savings_data['savings']} ({savings_data['rate_pct']}% rate)
- Debt-to-Income Ratio: {debt_data['debt_to_income_ratio']} ({debt_data['status']})
- Query: {request.query}

Give financial advice based on this profile."""

    llm_response = call_llm(system_prompt, user_message, temperature=0.3)
    return {
        "domain": "finance",
        "savings": savings_data,
        "debt_ratio": debt_data,
        **llm_response
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
    return {"status": "live", "system": "TriDomain Meta-Agent v0.2"}

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