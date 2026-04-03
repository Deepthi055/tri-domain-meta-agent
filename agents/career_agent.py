from core.llm_client import call_llm
from tools.calculators import skill_gap_analyzer

CAREER_SYSTEM_PROMPT = """You are a specialist career advisor inside a 
TriDomain AI system. You have deep expertise in:
- Career transitions and skill gap analysis
- Job market trends and in-demand skills
- Resume and portfolio strategy
- Learning roadmaps for new fields

YOUR RULES:
1. Always give specific, actionable advice — never generic tips
2. Never recommend quitting a job without a financial safety plan
3. Always consider the user's age and current stage
4. Tailor advice to the Indian job market unless stated otherwise

CRITICAL: Respond ONLY with valid JSON in exactly this format:
{
    "recommendation": "specific actionable advice here",
    "reason": "why this fits this specific user",
    "confidence": 0.85
}"""

def run(request) -> dict:
    # Run skill gap analysis if skills provided
    gap_data = None
    if hasattr(request, 'current_skills') and request.current_skills:
        gap_data = skill_gap_analyzer(
            request.current_skills,
            request.target_role
        )

    user_message = f"""User profile:
- Name: {request.name}
- Age: {request.age}
- Query: {request.query}
{f"- Skill Gap Analysis: {gap_data}" if gap_data else ""}

Give specific career advice for this person."""

    llm_response = call_llm(CAREER_SYSTEM_PROMPT, user_message, temperature=0.7)
    
    result = {"domain": "career", **llm_response}
    if gap_data:
        result["skill_gap"] = gap_data
    return result