from core.llm_client import call_llm
from tools.calculators import (
    skill_gap_analyzer,
    job_search,
    resume_optimizer,
    salary_benchmark,
    learning_path_generator
)

CAREER_SYSTEM_PROMPT = """You are a specialist career advisor inside a
TriDomain AI system. You have deep expertise in:
- Career transitions and skill gap analysis
- Job market trends and in-demand skills
- Resume and portfolio strategy
- Salary negotiation and market benchmarks
- Learning roadmaps for new fields

YOUR RULES:
1. Always give specific, actionable advice — never generic tips
2. Never recommend quitting a job without a financial safety plan
3. Always consider the user's age and current stage
4. Tailor advice to the Indian job market unless stated otherwise
5. Always reference the tool data provided — do not ignore it

CRITICAL: Respond ONLY with valid JSON in exactly this format:
{
    "recommendation": "specific actionable advice here",
    "reason": "why this fits this specific user",
    "confidence": 0.85
}"""


def run(request) -> dict:
    current_skills   = getattr(request, 'current_skills', [])
    target_role      = getattr(request, 'target_role', 'data scientist')
    location         = getattr(request, 'location', 'Bangalore')
    experience_level = getattr(request, 'experience_level', 'mid')
    years_experience = getattr(request, 'years_experience', 3)
    current_level    = getattr(request, 'current_level', 'beginner')
    timeline_months  = getattr(request, 'timeline_months', 6)
    resume_text      = getattr(request, 'resume_text', '')

    # Run all tools
    gap_data    = skill_gap_analyzer(current_skills, target_role)
    jobs_data   = job_search(current_skills, location, experience_level)
    salary_data = salary_benchmark(target_role, location, years_experience)
    path_data   = learning_path_generator(target_role, current_level, timeline_months)

    # Resume only runs if user provided resume text
    resume_data = None
    if resume_text:
        resume_data = resume_optimizer(resume_text, target_role)

    top_job = jobs_data['jobs'][0] if jobs_data['jobs'] else None

    user_message = f"""User profile:
- Name: {request.name}, Age: {request.age}
- Query: {request.query}
- Target Role: {target_role}
- Current Skills: {current_skills}
- Skill Gap: {gap_data['match_percentage']}% match | Missing: {gap_data['missing_skills']}
- Top Job Match: {top_job['title'] + ' at ' + str(top_job['match_score']) + '%' if top_job else 'None found'}
- Salary Range: Rs.{salary_data['market_range_lpa']['min']}-{salary_data['market_range_lpa']['max']} LPA
- Learning Path: {path_data['total_weeks_required']} weeks needed | Feasible: {path_data['feasible']}
{f'- Resume ATS Score: {resume_data["ats_score"]}/100' if resume_data else ''}

Give specific career advice based on ALL this data."""

    llm_response = call_llm(CAREER_SYSTEM_PROMPT, user_message, temperature=0.7)

    result = {
        "domain": "career",
        "skill_gap": gap_data,
        "job_matches": jobs_data,
        "salary_benchmark": salary_data,
        "learning_path": path_data,
        **llm_response
    }

    if resume_data:
        result["resume_analysis"] = resume_data

    return result