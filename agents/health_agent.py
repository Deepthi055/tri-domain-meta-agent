from core.llm_client import call_llm
from tools.calculators import (
    calculate_bmi,
    fitness_score,
    workout_planner,
    nutrition_tracker,
    sleep_analysis,
    mental_health_tracker,
    health_screening_reminder
)

HEALTH_SYSTEM_PROMPT = """You are a specialist health advisor inside a
TriDomain AI system. You have deep expertise in:
- BMI analysis and healthy weight management
- Exercise planning for different fitness levels
- Nutrition and dietary guidance
- Sleep optimization
- Mental wellness and stress management
- Preventive health screenings

YOUR RULES:
1. Always reference the user's actual BMI and fitness score in your advice
2. Never recommend extreme diets or dangerous exercise regimens
3. Always suggest consulting a doctor for medical conditions
4. Keep recommendations realistic for a working professional
5. If risk_flag is True in mental health data, always recommend professional help

CRITICAL: Respond ONLY with valid JSON in exactly this format:
{
    "recommendation": "specific actionable advice here",
    "reason": "why this fits this specific user",
    "confidence": 0.85
}"""


def run(request) -> dict:
    # Core tools — always run
    bmi_data     = calculate_bmi(request.weight_kg, request.height_cm)
    fitness_data = fitness_score(request.age, request.weight_kg, request.height_cm)

    # Workout planner
    workout_data = workout_planner(
        getattr(request, 'fitness_goal', 'general fitness'),
        getattr(request, 'fitness_experience', 'beginner'),
        getattr(request, 'available_days', 3)
    )

    # Nutrition tracker
    nutrition_data = nutrition_tracker(
        getattr(request, 'meals', ['rice', 'dal', 'vegetables']),
        getattr(request, 'nutritional_goal', 'general health')
    )

    # Sleep analysis
    sleep_data = sleep_analysis(
        getattr(request, 'sleep_hours', 7.0),
        getattr(request, 'bedtime', '23:00'),
        getattr(request, 'wakeup_time', '06:00'),
        getattr(request, 'sleep_quality', 7)
    )

    # Mental health tracker
    mental_data = mental_health_tracker(
        getattr(request, 'mood_score', 7),
        getattr(request, 'stress_level', 5),
        getattr(request, 'anxiety_level', 4)
    )

    # Health screening reminder
    screening_data = health_screening_reminder(
        request.age,
        getattr(request, 'gender', 'male'),
        getattr(request, 'last_checkup_months_ago', 12)
    )

    user_message = f"""User profile:
- Name: {request.name}, Age: {request.age}
- Weight: {request.weight_kg}kg, Height: {request.height_cm}cm
- BMI: {bmi_data['bmi']} ({bmi_data['category']})
- Fitness Score: {fitness_data['fitness_score']}/100 ({fitness_data['fitness_level']})
- Weight to lose: {fitness_data['weight_to_lose_kg']} kg
- Fitness Goal: {workout_data['fitness_goal']}
- Workout: {workout_data['days_per_week']} days/week, {workout_data['total_mins_per_week']} mins total
- Nutrition Goal: {nutrition_data['nutritional_goal']}
- Calories today: {nutrition_data['totals']['calories']} / {nutrition_data['daily_targets']['calories']}
- Protein today: {nutrition_data['totals']['protein']}g / {nutrition_data['daily_targets']['protein']}g
- Sleep Score: {sleep_data['sleep_score']}/100 ({sleep_data['sleep_level']})
- Sleep Hours: {sleep_data['sleep_hours']} hours
- Wellness Score: {mental_data['wellness_score']}/100 ({mental_data['wellness_level']})
- Stress Level: {mental_data['stress_level']}/10
- Risk Flag: {mental_data['risk_flag']}
- Screenings overdue: {screening_data['overdue_for_checkup']}
- Query: {request.query}

Give specific health advice based on ALL this data."""

    llm_response = call_llm(HEALTH_SYSTEM_PROMPT, user_message, temperature=0.3)

    return {
        "domain":           "health",
        "bmi":              bmi_data,
        "fitness":          fitness_data,
        "workout_plan":     workout_data,
        "nutrition":        nutrition_data,
        "sleep":            sleep_data,
        "mental_health":    mental_data,
        "screenings":       screening_data,
        **llm_response
    }