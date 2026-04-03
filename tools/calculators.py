def calculate_bmi(weight_kg: float, height_cm: float) -> dict:
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

def calculate_savings(income: float, expenses: float) -> dict:
    savings = income - expenses
    rate = (savings / income) * 100
    return {"savings": savings, "rate_pct": round(rate, 1)}

def calculate_debt_ratio(income: float, expenses: float) -> dict:
    ratio = expenses / income
    status = "healthy" if ratio < 0.5 else "concerning"
    return {"debt_to_income_ratio": round(ratio, 2), "status": status}

def skill_gap_analyzer(current_skills: list, target_role: str) -> dict:
    required_skills = {
        "data scientist": {
            "python": 4,
            "sql": 3,
            "machine learning": 4,
            "statistics": 3,
            "data visualization": 3
        },
        "web developer": {
            "html": 3,
            "css": 3,
            "javascript": 4,
            "react": 3,
            "nodejs": 3
        },
        "devops engineer": {
            "linux": 4,
            "docker": 3,
            "kubernetes": 3,
            "ci/cd": 3,
            "aws": 3
        }
    }

    role = target_role.lower()
    current = [s.lower() for s in current_skills]

    if role not in required_skills:
        return {
            "error": f"Role '{target_role}' not found",
            "available_roles": list(required_skills.keys())
        }

    required = required_skills[role]

    missing = [skill for skill in required if skill not in current]

    total = len(required)
    matched = total - len(missing)
    match_pct = round((matched / total) * 100, 1)

    if match_pct >= 80:
        status = "strong match"
    elif match_pct >= 50:
        status = "needs work"
    else:
        status = "significant gaps"

    return {
        "target_role": role,
        "current_skills": current,
        "missing_skills": missing,
        "match_percentage": match_pct,
        "status": status
    }