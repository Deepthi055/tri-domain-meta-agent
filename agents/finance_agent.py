from core.llm_client import call_llm
from tools.calculators import calculate_savings, calculate_debt_ratio

FINANCE_SYSTEM_PROMPT = """You are a specialist financial advisor inside a 
TriDomain AI system. You have deep expertise in:
- Personal savings and budgeting strategy
- Debt management and reduction
- Investment basics for salaried professionals
- Financial planning for career transitions

YOUR RULES:
1. Always reference the user's actual numbers in your advice
2. Never recommend high-risk investments without flagging the risk
3. Always consider debt-to-income ratio before suggesting investments
4. Tailor advice to Indian financial context (SIP, PPF, etc.) unless stated

CRITICAL: Respond ONLY with valid JSON in exactly this format:
{
    "recommendation": "specific actionable advice here",
    "reason": "why this fits this specific user",
    "confidence": 0.85
}"""

def run(request) -> dict:
    savings_data = calculate_savings(request.monthly_income, request.monthly_expenses)
    debt_data = calculate_debt_ratio(request.monthly_income, request.monthly_expenses)

    user_message = f"""User profile:
- Name: {request.name}
- Age: {request.age}
- Monthly Income: ₹{request.monthly_income}
- Monthly Expenses: ₹{request.monthly_expenses}
- Savings: ₹{savings_data['savings']} ({savings_data['rate_pct']}% rate)
- Debt-to-Income Ratio: {debt_data['debt_to_income_ratio']} ({debt_data['status']})
- Query: {request.query}

Give specific financial advice for this person."""

    llm_response = call_llm(FINANCE_SYSTEM_PROMPT, user_message, temperature=0.3)
    return {
        "domain": "finance",
        "savings": savings_data,
        "debt_ratio": debt_data,
        **llm_response
    }