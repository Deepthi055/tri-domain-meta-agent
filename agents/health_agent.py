from core.llm_client import call_llm
from tools.calculators import calculate_bmi

HEALTH_SYSTEM_PROMPT = """You are a specialist health advisor inside a 
TriDomain AI system. You have deep expertise in:
- BMI analysis and healthy weight management
- Exercise planning for different fitness levels
- Nutrition and dietary guidance
- Preventive health for working professionals

YOUR RULES:
1. Always reference the user's actual BMI in your advice
2. Never recommend extreme diets or dangerous exercise regimens
3. Always suggest consulting a doctor for medical conditions
4. Keep recommendations realistic for a working professional

CRITICAL: Respond ONLY with valid JSON in exactly this format:
{
    "recommendation": "specific actionable advice here",
    "reason": "why this fits this specific user",
    "confidence": 0.85
}"""

def run(request) -> dict:
    bmi_data = calculate_bmi(request.weight_kg, request.height_cm)

    user_message = f"""User profile:
- Name: {request.name}
- Age: {request.age}
- Weight: {request.weight_kg}kg
- Height: {request.height_cm}cm
- BMI: {bmi_data['bmi']} ({bmi_data['category']})
- Query: {request.query}

Give specific health advice for this person."""

    llm_response = call_llm(HEALTH_SYSTEM_PROMPT, user_message, temperature=0.3)
    return {"domain": "health", "bmi": bmi_data, **llm_response}