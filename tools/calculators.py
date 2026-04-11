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
def job_search(skills: list, location: str, experience_level: str) -> dict:
    job_database = [
        {
            "title": "Data Scientist",
            "company": "TechCorp India",
            "location": "Bangalore",
            "required_skills": ["python", "machine learning", "sql", "statistics"],
            "experience": "mid",
            "salary_range": "12-18 LPA"
        },
        {
            "title": "Data Analyst",
            "company": "Analytics Co",
            "location": "Hyderabad",
            "required_skills": ["sql", "excel", "python", "data visualization"],
            "experience": "junior",
            "salary_range": "6-10 LPA"
        },
        {
            "title": "ML Engineer",
            "company": "AI Startup",
            "location": "Bangalore",
            "required_skills": ["python", "machine learning", "docker", "aws"],
            "experience": "mid",
            "salary_range": "15-25 LPA"
        },
        {
            "title": "Business Analyst",
            "company": "Consulting Firm",
            "location": "Mumbai",
            "required_skills": ["sql", "excel", "communication", "data visualization"],
            "experience": "junior",
            "salary_range": "8-12 LPA"
        },
        {
            "title": "Senior Data Scientist",
            "company": "FinTech Ltd",
            "location": "Pune",
            "required_skills": ["python", "machine learning", "statistics", "sql", "leadership"],
            "experience": "senior",
            "salary_range": "25-40 LPA"
        },
        {
            "title": "Python Developer",
            "company": "SoftwareCo",
            "location": "Chennai",
            "required_skills": ["python", "django", "sql", "rest api"],
            "experience": "mid",
            "salary_range": "10-16 LPA"
        }
    ]

    user_skills   = [s.lower() for s in skills]
    user_location = location.lower()
    user_exp      = experience_level.lower()
    matched_jobs  = []

    for job in job_database:
        required = job["required_skills"]
        matched  = [s for s in required if s in user_skills]
        score    = round((len(matched) / len(required)) * 100, 1)

        if user_location in job["location"].lower():
            score = min(100, score + 10)
        if user_exp == job["experience"]:
            score = min(100, score + 10)

        if score >= 30:
            matched_jobs.append({
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "match_score": score,
                "matched_skills": matched,
                "missing_skills": [s for s in required if s not in user_skills],
                "salary_range": job["salary_range"],
                "experience_level": job["experience"]
            })

    matched_jobs.sort(key=lambda x: x["match_score"], reverse=True)

    return {
        "location_searched": location,
        "experience_level": experience_level,
        "total_matches": len(matched_jobs),
        "jobs": matched_jobs[:5]
    }
def resume_optimizer(resume_text: str, target_job: str) -> dict:
    ats_keywords = {
        "data scientist": [
            "python", "machine learning", "sql", "statistics",
            "deep learning", "tensorflow", "pandas", "numpy",
            "data visualization", "model deployment", "a/b testing"
        ],
        "web developer": [
            "javascript", "react", "nodejs", "html", "css",
            "rest api", "git", "responsive design", "typescript", "testing"
        ],
        "data analyst": [
            "sql", "excel", "python", "tableau", "power bi",
            "data visualization", "reporting", "kpi", "dashboard", "etl"
        ],
        "ml engineer": [
            "python", "machine learning", "docker", "kubernetes",
            "mlops", "aws", "model deployment", "ci/cd", "tensorflow", "pytorch"
        ]
    }

    resume_lower = resume_text.lower()
    job_lower    = target_job.lower()

    best_match = "data scientist"
    for job_type in ats_keywords:
        if job_type in job_lower:
            best_match = job_type
            break

    keywords      = ats_keywords[best_match]
    found         = [k for k in keywords if k in resume_lower]
    missing       = [k for k in keywords if k not in resume_lower]
    keyword_score = round((len(found) / len(keywords)) * 100, 1)

    structure_checks = {
        "has_email":        any(x in resume_lower for x in ["@gmail", "@yahoo", "@outlook", "@"]),
        "has_linkedin":     "linkedin" in resume_lower,
        "has_github":       "github" in resume_lower,
        "has_experience":   any(x in resume_lower for x in ["experience", "worked", "employed"]),
        "has_education":    any(x in resume_lower for x in ["education", "degree", "university", "college", "b.tech", "b.e", "mba"]),
        "has_projects":     any(x in resume_lower for x in ["project", "built", "developed", "created"]),
        "has_skills":       "skills" in resume_lower,
        "has_achievements": any(x in resume_lower for x in ["achieved", "improved", "reduced", "increased", "%"])
    }

    structure_score   = round((sum(structure_checks.values()) / len(structure_checks)) * 100, 1)
    overall_ats_score = round((keyword_score * 0.6) + (structure_score * 0.4), 1)

    suggestions = []
    if missing:
        suggestions.append(f"Add these missing keywords: {', '.join(missing[:5])}")
    if not structure_checks["has_github"]:
        suggestions.append("Add your GitHub profile link — critical for tech roles")
    if not structure_checks["has_achievements"]:
        suggestions.append("Add quantified achievements e.g. Reduced load time by 40%")
    if not structure_checks["has_linkedin"]:
        suggestions.append("Add your LinkedIn profile URL")
    if keyword_score < 50:
        suggestions.append("Rewrite your summary to include more role-specific keywords")

    return {
        "target_job": target_job,
        "ats_score": overall_ats_score,
        "keyword_score": keyword_score,
        "structure_score": structure_score,
        "keywords_found": found,
        "keywords_missing": missing,
        "structure_checks": structure_checks,
        "suggestions": suggestions,
        "verdict": (
            "Strong resume" if overall_ats_score >= 75 else
            "Needs improvement" if overall_ats_score >= 50 else
            "Significant rewrite needed"
        )
    }
def salary_benchmark(role: str, location: str, years_experience: int) -> dict:
    salary_data = {
        "data scientist": {
            "bangalore": (8, 16, 30),
            "hyderabad": (7, 14, 26),
            "mumbai":    (8, 15, 28),
            "pune":      (7, 13, 25),
            "chennai":   (6, 12, 22),
            "delhi":     (7, 14, 26),
            "default":   (6, 12, 22)
        },
        "ml engineer": {
            "bangalore": (10, 20, 38),
            "hyderabad": (9,  18, 34),
            "mumbai":    (10, 19, 36),
            "default":   (8,  16, 30)
        },
        "data analyst": {
            "bangalore": (5, 10, 18),
            "hyderabad": (4,  9, 16),
            "mumbai":    (5, 10, 17),
            "default":   (4,  8, 14)
        },
        "software engineer": {
            "bangalore": (6, 14, 28),
            "hyderabad": (5, 12, 24),
            "mumbai":    (6, 13, 26),
            "default":   (5, 11, 22)
        },
        "web developer": {
            "bangalore": (5, 11, 20),
            "hyderabad": (4,  9, 18),
            "default":   (4,  8, 16)
        }
    }

    role_lower     = role.lower()
    location_lower = location.lower()

    matched_role = "data scientist"
    for r in salary_data:
        if r in role_lower or role_lower in r:
            matched_role = r
            break

    role_salaries       = salary_data[matched_role]
    location_key        = location_lower if location_lower in role_salaries else "default"
    junior, mid, senior = role_salaries[location_key]

    if years_experience <= 2:
        band       = "junior"
        min_salary = junior
        max_salary = round(junior * 1.4, 1)
    elif years_experience <= 6:
        band       = "mid"
        min_salary = mid
        max_salary = round(mid * 1.35, 1)
    else:
        band       = "senior"
        min_salary = senior
        max_salary = round(senior * 1.3, 1)

    return {
        "role": matched_role,
        "location": location,
        "years_experience": years_experience,
        "experience_band": band,
        "market_range_lpa": {"min": min_salary, "max": max_salary},
        "market_median_lpa": round((min_salary + max_salary) / 2, 1),
        "negotiation_tips": [
            f"Market range for {role} in {location} at your level: Rs.{min_salary}-{max_salary} LPA",
            "Always negotiate — 80% of offers have room for 10-20% increase",
            "Anchor high: start your ask 15-20% above your target",
            "Ask about ESOPs in startups — they can double your effective CTC",
            "Negotiate joining bonus if base salary is fixed"
        ]
    }
def learning_path_generator(goal: str, current_level: str, timeline_months: int) -> dict:
    learning_paths = {
        "data scientist": {
            "beginner": [
                {
                    "phase": 1,
                    "focus": "Python Fundamentals",
                    "topics": ["Python basics", "NumPy", "Pandas", "Matplotlib"],
                    "resources": ["Kaggle Python course (free)", "Python.org docs"],
                    "duration_weeks": 4
                },
                {
                    "phase": 2,
                    "focus": "Statistics and SQL",
                    "topics": ["Descriptive stats", "Probability", "SQL queries", "Joins"],
                    "resources": ["Khan Academy Statistics (free)", "Mode SQL Tutorial (free)"],
                    "duration_weeks": 4
                },
                {
                    "phase": 3,
                    "focus": "Machine Learning",
                    "topics": ["Scikit-learn", "Regression", "Classification", "Clustering"],
                    "resources": ["Coursera ML by Andrew Ng", "Kaggle ML course (free)"],
                    "duration_weeks": 6
                },
                {
                    "phase": 4,
                    "focus": "Projects and Portfolio",
                    "topics": ["Kaggle competitions", "GitHub portfolio", "End-to-end projects"],
                    "resources": ["Kaggle.com", "GitHub"],
                    "duration_weeks": 4
                }
            ],
            "intermediate": [
                {
                    "phase": 1,
                    "focus": "Deep Learning",
                    "topics": ["Neural networks", "TensorFlow", "PyTorch", "CNNs", "RNNs"],
                    "resources": ["fast.ai (free)", "Deep Learning Specialization Coursera"],
                    "duration_weeks": 6
                },
                {
                    "phase": 2,
                    "focus": "MLOps and Deployment",
                    "topics": ["Docker", "FastAPI", "Model serving", "CI/CD"],
                    "resources": ["MLOps Zoomcamp (free)", "Made With ML"],
                    "duration_weeks": 4
                },
                {
                    "phase": 3,
                    "focus": "Advanced Topics",
                    "topics": ["NLP", "Computer Vision", "A/B testing", "Feature stores"],
                    "resources": ["Hugging Face course (free)", "Evidently AI blog"],
                    "duration_weeks": 4
                }
            ]
        },
        "web developer": {
            "beginner": [
                {
                    "phase": 1,
                    "focus": "HTML and CSS",
                    "topics": ["HTML5", "CSS3", "Flexbox", "Grid", "Responsive design"],
                    "resources": ["freeCodeCamp (free)", "The Odin Project (free)"],
                    "duration_weeks": 3
                },
                {
                    "phase": 2,
                    "focus": "JavaScript",
                    "topics": ["JS fundamentals", "DOM", "ES6+", "Fetch API"],
                    "resources": ["javascript.info (free)", "Eloquent JavaScript (free)"],
                    "duration_weeks": 5
                },
                {
                    "phase": 3,
                    "focus": "React and Backend",
                    "topics": ["React", "Node.js", "Express", "REST APIs", "MongoDB"],
                    "resources": ["React docs", "The Odin Project Node path (free)"],
                    "duration_weeks": 6
                }
            ],
            "intermediate": [
                {
                    "phase": 1,
                    "focus": "TypeScript and Testing",
                    "topics": ["TypeScript", "Jest", "React Testing Library"],
                    "resources": ["TypeScript docs", "Testing Library docs"],
                    "duration_weeks": 3
                },
                {
                    "phase": 2,
                    "focus": "System Design and DevOps",
                    "topics": ["Docker", "AWS basics", "System design", "CI/CD"],
                    "resources": ["roadmap.sh", "AWS free tier"],
                    "duration_weeks": 5
                }
            ]
        }
    }

    goal_lower  = goal.lower()
    level_lower = current_level.lower()

    matched_goal = "data scientist"
    for g in learning_paths:
        if g in goal_lower or goal_lower in g:
            matched_goal = g
            break

    matched_level   = "beginner" if level_lower in ["beginner", "fresher", "no experience"] else "intermediate"
    path            = learning_paths[matched_goal].get(matched_level, learning_paths[matched_goal]["beginner"])
    total_weeks     = sum(p["duration_weeks"] for p in path)
    available_weeks = timeline_months * 4
    feasible        = available_weeks >= total_weeks
    weekly_hours    = round((total_weeks * 10) / available_weeks, 1) if available_weeks > 0 else 0

    return {
        "goal": matched_goal,
        "current_level": matched_level,
        "timeline_months": timeline_months,
        "total_weeks_required": total_weeks,
        "feasible": feasible,
        "weekly_hours_needed": weekly_hours,
        "phases": path,
        "advice": (
            "Your timeline is achievable. Stay consistent — 2 hrs/day is enough."
            if feasible else
            f"Timeline is tight. You need {weekly_hours} hrs/week. Consider extending to {round(total_weeks/4)} months."
        )
    }
def fitness_score(age: int, weight_kg: float, height_cm: float) -> dict:
    height_m = height_cm / 100
    bmi = round(weight_kg / (height_m ** 2), 1)

    # BMI component (0-50 points)
    if 18.5 <= bmi <= 24.9:
        bmi_score = 50
    elif 17.0 <= bmi < 18.5 or 25.0 <= bmi <= 27.0:
        bmi_score = 35
    elif 15.0 <= bmi < 17.0 or 27.0 < bmi <= 30.0:
        bmi_score = 20
    else:
        bmi_score = 5

    # Age component (0-30 points)
    if age < 30:
        age_score = 30
    elif age < 40:
        age_score = 25
    elif age < 50:
        age_score = 20
    else:
        age_score = 15

    # Ideal weight range component (0-20 points)
    ideal_min = round(18.5 * (height_m ** 2), 1)
    ideal_max = round(24.9 * (height_m ** 2), 1)
    in_range  = ideal_min <= weight_kg <= ideal_max
    weight_gap = 0 if in_range else min(
        abs(weight_kg - ideal_min),
        abs(weight_kg - ideal_max)
    )
    range_score = max(0, 20 - int(weight_gap))

    total = bmi_score + age_score + range_score

    if total >= 80:
        level = "excellent"
    elif total >= 60:
        level = "good"
    elif total >= 40:
        level = "average"
    else:
        level = "needs attention"

    return {
        "fitness_score": total,
        "fitness_level": level,
        "bmi": bmi,
        "ideal_weight_range_kg": {"min": ideal_min, "max": ideal_max},
        "weight_to_lose_kg": round(max(0, weight_kg - ideal_max), 1)
    }
def workout_planner(fitness_goal: str, experience_level: str, available_days: int) -> dict:
    workouts = {
        "weight loss": {
            "beginner": {
                "monday":    {"type": "Cardio",    "exercises": ["30 min brisk walk", "10 min stretching"],                         "duration": 40},
                "wednesday": {"type": "Strength",  "exercises": ["Bodyweight squats 3x15", "Push-ups 3x10", "Plank 3x30sec"],       "duration": 35},
                "friday":    {"type": "Cardio",    "exercises": ["20 min jog", "Jumping jacks 3x20", "Cool down stretch"],          "duration": 35},
            },
            "intermediate": {
                "monday":    {"type": "HIIT",      "exercises": ["Burpees 4x15", "Mountain climbers 4x20", "Jump squats 4x15"],     "duration": 45},
                "tuesday":   {"type": "Strength",  "exercises": ["Dumbbell lunges 4x12", "Push-ups 4x15", "Dumbbell rows 4x12"],    "duration": 50},
                "thursday":  {"type": "Cardio",    "exercises": ["30 min run", "Cycling 20 min"],                                   "duration": 50},
                "saturday":  {"type": "Full Body", "exercises": ["Deadlifts 3x10", "Bench press 3x10", "Pull-ups 3x8"],             "duration": 55},
            }
        },
        "muscle gain": {
            "beginner": {
                "monday":    {"type": "Upper Body", "exercises": ["Push-ups 3x12", "Dumbbell curls 3x12", "Overhead press 3x10"],   "duration": 45},
                "wednesday": {"type": "Lower Body", "exercises": ["Squats 3x15", "Lunges 3x12", "Calf raises 3x20"],                "duration": 45},
                "friday":    {"type": "Full Body",  "exercises": ["Deadlifts 3x8", "Rows 3x10", "Plank 3x45sec"],                   "duration": 50},
            },
            "intermediate": {
                "monday":    {"type": "Chest/Tri",  "exercises": ["Bench press 4x8", "Tricep dips 4x12", "Cable flyes 4x12"],       "duration": 60},
                "tuesday":   {"type": "Back/Bi",    "exercises": ["Pull-ups 4x8", "Barbell rows 4x10", "Hammer curls 4x12"],        "duration": 60},
                "thursday":  {"type": "Legs",       "exercises": ["Squats 4x10", "Leg press 4x12", "Romanian deadlift 4x10"],       "duration": 60},
                "saturday":  {"type": "Shoulders",  "exercises": ["Military press 4x10", "Lateral raises 4x15", "Face pulls 4x15"], "duration": 55},
            }
        },
        "general fitness": {
            "beginner": {
                "monday":    {"type": "Cardio",     "exercises": ["20 min walk", "Light stretching"],                               "duration": 30},
                "wednesday": {"type": "Strength",   "exercises": ["Bodyweight circuit", "Core exercises", "Balance work"],          "duration": 35},
                "friday":    {"type": "Flexibility", "exercises": ["Yoga basics", "Full body stretch", "Breathing exercises"],      "duration": 30},
            },
            "intermediate": {
                "monday":    {"type": "Cardio",     "exercises": ["30 min run", "Agility drills"],                                  "duration": 45},
                "wednesday": {"type": "Strength",   "exercises": ["Compound lifts", "Core circuit", "Functional movements"],       "duration": 50},
                "friday":    {"type": "Mixed",      "exercises": ["Swimming or cycling", "Bodyweight circuit"],                     "duration": 45},
            }
        }
    }

    goal_lower  = fitness_goal.lower()
    level_lower = experience_level.lower()

    matched_goal  = "general fitness"
    for g in workouts:
        if g in goal_lower or goal_lower in g:
            matched_goal = g
            break

    matched_level = "beginner" if level_lower in ["beginner", "new", "starter"] else "intermediate"
    plan          = workouts[matched_goal].get(matched_level, workouts[matched_goal]["beginner"])

    # Limit to available days
    all_days    = list(plan.items())
    limited     = dict(all_days[:available_days])
    total_mins  = sum(v["duration"] for v in limited.values())

    return {
        "fitness_goal":     matched_goal,
        "experience_level": matched_level,
        "days_per_week":    len(limited),
        "total_mins_per_week": total_mins,
        "schedule":         limited,
        "tip": f"Stick to this {len(limited)}-day plan consistently for 4 weeks before increasing intensity."
    }
def nutrition_tracker(meals: list, nutritional_goal: str) -> dict:
    # Nutrition database (per 100g or per unit)
    nutrition_db = {
        "rice":        {"calories": 130, "protein": 2.7, "carbs": 28, "fat": 0.3},
        "chicken":     {"calories": 165, "protein": 31,  "carbs": 0,  "fat": 3.6},
        "egg":         {"calories": 155, "protein": 13,  "carbs": 1.1,"fat": 11},
        "dal":         {"calories": 116, "protein": 9,   "carbs": 20, "fat": 0.4},
        "roti":        {"calories": 120, "protein": 3.5, "carbs": 25, "fat": 0.4},
        "milk":        {"calories": 61,  "protein": 3.2, "carbs": 4.8,"fat": 3.3},
        "banana":      {"calories": 89,  "protein": 1.1, "carbs": 23, "fat": 0.3},
        "apple":       {"calories": 52,  "protein": 0.3, "carbs": 14, "fat": 0.2},
        "paneer":      {"calories": 265, "protein": 18,  "carbs": 1.2,"fat": 20},
        "oats":        {"calories": 389, "protein": 17,  "carbs": 66, "fat": 7},
        "salad":       {"calories": 20,  "protein": 1.5, "carbs": 3,  "fat": 0.2},
        "bread":       {"calories": 265, "protein": 9,   "carbs": 49, "fat": 3.2},
        "potato":      {"calories": 77,  "protein": 2,   "carbs": 17, "fat": 0.1},
        "fish":        {"calories": 136, "protein": 24,  "carbs": 0,  "fat": 4},
        "vegetables":  {"calories": 35,  "protein": 2,   "carbs": 7,  "fat": 0.3}
    }

    # Daily goals by nutritional target
    goals_db = {
        "weight loss":    {"calories": 1800, "protein": 120, "carbs": 180, "fat": 60},
        "muscle gain":    {"calories": 2800, "protein": 180, "carbs": 320, "fat": 80},
        "general health": {"calories": 2200, "protein": 100, "carbs": 250, "fat": 70},
        "maintenance":    {"calories": 2000, "protein": 100, "carbs": 220, "fat": 65}
    }

    goal_lower    = nutritional_goal.lower()
    matched_goal  = "general health"
    for g in goals_db:
        if g in goal_lower or goal_lower in g:
            matched_goal = g
            break

    daily_goal = goals_db[matched_goal]

    # Calculate totals from meals
    totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
    found_meals  = []
    missed_meals = []

    for meal in meals:
        meal_lower = meal.lower().strip()
        matched = None
        for food in nutrition_db:
            if food in meal_lower or meal_lower in food:
                matched = food
                break

        if matched:
            found_meals.append(matched)
            for key in totals:
                totals[key] += nutrition_db[matched][key]
        else:
            missed_meals.append(meal)

    # Round totals
    totals = {k: round(v, 1) for k, v in totals.items()}

    # Calculate gaps
    gaps = {
        k: round(daily_goal[k] - totals[k], 1)
        for k in daily_goal
    }

    # Build recommendations
    recommendations = []
    if gaps["protein"] > 20:
        recommendations.append(f"Add more protein — you need {gaps['protein']}g more. Try chicken, eggs, or paneer.")
    if gaps["calories"] < -200:
        recommendations.append("You are over your calorie target. Consider reducing rice or bread portions.")
    if gaps["calories"] > 300:
        recommendations.append(f"You need {gaps['calories']} more calories. Add a healthy snack like banana or milk.")
    if totals["fat"] > daily_goal["fat"]:
        recommendations.append("Fat intake is high. Reduce fried foods and paneer portions.")
    if not recommendations:
        recommendations.append("Your nutrition looks balanced. Keep it up!")

    return {
        "nutritional_goal": matched_goal,
        "meals_tracked":    found_meals,
        "meals_not_found":  missed_meals,
        "totals":           totals,
        "daily_targets":    daily_goal,
        "gaps":             gaps,
        "recommendations":  recommendations
    }
def sleep_analysis(sleep_hours: float, bedtime: str, wakeup_time: str, sleep_quality: int) -> dict:
    """
    sleep_quality: 1-10 rating given by user
    bedtime: e.g. "23:00"
    wakeup_time: e.g. "07:00"
    """

    # Score components
    # Hours score (0-40 points)
    if 7 <= sleep_hours <= 9:
        hours_score = 40
    elif 6 <= sleep_hours < 7 or 9 < sleep_hours <= 10:
        hours_score = 28
    elif 5 <= sleep_hours < 6:
        hours_score = 15
    else:
        hours_score = 5

    # Quality score (0-40 points)
    quality_score = round((sleep_quality / 10) * 40, 1)

    # Consistency score based on bedtime (0-20 points)
    try:
        hour = int(bedtime.split(":")[0])
        if 21 <= hour <= 23:
            consistency_score = 20
        elif hour == 0:
            consistency_score = 12
        elif 1 <= hour <= 2:
            consistency_score = 6
        else:
            consistency_score = 10
    except:
        consistency_score = 10

    total_score = round(hours_score + quality_score + consistency_score, 1)

    if total_score >= 80:
        sleep_level = "excellent"
    elif total_score >= 60:
        sleep_level = "good"
    elif total_score >= 40:
        sleep_level = "fair"
    else:
        sleep_level = "poor"

    # Build tips
    tips = []
    if sleep_hours < 7:
        tips.append("You are sleeping less than 7 hours. Aim for 7-9 hours for optimal health.")
    if sleep_hours > 9:
        tips.append("Oversleeping can cause fatigue. Try to limit sleep to 9 hours.")
    if sleep_quality < 6:
        tips.append("Low sleep quality detected. Avoid screens 1 hour before bed.")
        tips.append("Try keeping your room dark and cool — 18-20 degrees is ideal.")
    try:
        hour = int(bedtime.split(":")[0])
        if hour >= 1:
            tips.append("Late bedtime detected. Try sleeping before midnight for better sleep cycles.")
    except:
        pass
    if not tips:
        tips.append("Your sleep habits look healthy. Keep your schedule consistent.")

    return {
        "sleep_hours":      sleep_hours,
        "bedtime":          bedtime,
        "wakeup_time":      wakeup_time,
        "sleep_quality":    sleep_quality,
        "sleep_score":      total_score,
        "sleep_level":      sleep_level,
        "score_breakdown": {
            "hours_score":       hours_score,
            "quality_score":     quality_score,
            "consistency_score": consistency_score
        },
        "tips": tips
    }
def mental_health_tracker(mood_score: int, stress_level: int, anxiety_level: int) -> dict:
    """
    mood_score:    1-10 (10 = very happy)
    stress_level:  1-10 (10 = extremely stressed)
    anxiety_level: 1-10 (10 = extremely anxious)
    """

    # Wellness score (0-100)
    mood_component    = round((mood_score / 10) * 40, 1)
    stress_component  = round(((10 - stress_level) / 10) * 35, 1)
    anxiety_component = round(((10 - anxiety_level) / 10) * 25, 1)
    wellness_score    = round(mood_component + stress_component + anxiety_component, 1)

    if wellness_score >= 80:
        wellness_level = "excellent"
    elif wellness_score >= 60:
        wellness_level = "good"
    elif wellness_score >= 40:
        wellness_level = "fair"
    else:
        wellness_level = "needs attention"

    # Coping strategies
    strategies = []

    if stress_level >= 7:
        strategies.append("High stress detected — try 10 min deep breathing or meditation daily.")
        strategies.append("Break large tasks into smaller steps to reduce overwhelm.")
        strategies.append("Take a 5 min walk every hour if working at a desk.")

    if anxiety_level >= 7:
        strategies.append("High anxiety detected — try the 4-7-8 breathing technique.")
        strategies.append("Limit caffeine intake — it can worsen anxiety symptoms.")
        strategies.append("Consider talking to a mental health professional if anxiety persists.")

    if mood_score <= 4:
        strategies.append("Low mood detected — connect with a friend or family member today.")
        strategies.append("Get at least 20 minutes of sunlight and outdoor activity.")
        strategies.append("Write down 3 things you are grateful for each morning.")

    if not strategies:
        strategies.append("Your mental wellness looks good. Keep up your current routines.")
        strategies.append("Regular exercise and sleep are your best mental health tools.")

    # Risk flag
    risk_flag = False
    risk_message = None
    if mood_score <= 3 and stress_level >= 8:
        risk_flag    = True
        risk_message = "Your scores suggest significant distress. Please consider speaking to a professional or trusted person."

    return {
        "mood_score":      mood_score,
        "stress_level":    stress_level,
        "anxiety_level":   anxiety_level,
        "wellness_score":  wellness_score,
        "wellness_level":  wellness_level,
        "score_breakdown": {
            "mood_component":    mood_component,
            "stress_component":  stress_component,
            "anxiety_component": anxiety_component
        },
        "coping_strategies": strategies,
        "risk_flag":         risk_flag,
        "risk_message":      risk_message
    }
def health_screening_reminder(age: int, gender: str, last_checkup_months_ago: int) -> dict:
    """
    age: user age
    gender: "male" or "female"
    last_checkup_months_ago: how many months since last checkup
    """

    screenings = []
    gender_lower = gender.lower()

    # Everyone regardless of gender
    if age >= 18:
        screenings.append({
            "test":      "Blood Pressure Check",
            "frequency": "Every 6 months",
            "priority":  "high" if last_checkup_months_ago > 6 else "low",
            "reason":    "Early detection of hypertension"
        })
        screenings.append({
            "test":      "Blood Sugar (Fasting)",
            "frequency": "Once a year",
            "priority":  "high" if last_checkup_months_ago > 12 else "medium",
            "reason":    "Diabetes screening"
        })
        screenings.append({
            "test":      "Full Blood Count (CBC)",
            "frequency": "Once a year",
            "priority":  "high" if last_checkup_months_ago > 12 else "low",
            "reason":    "Detect anaemia and infections"
        })

    if age >= 30:
        screenings.append({
            "test":      "Lipid Profile (Cholesterol)",
            "frequency": "Every 2 years",
            "priority":  "high" if last_checkup_months_ago > 24 else "medium",
            "reason":    "Heart disease risk assessment"
        })
        screenings.append({
            "test":      "Thyroid Function Test",
            "frequency": "Every 2 years",
            "priority":  "medium",
            "reason":    "Thyroid disorders are common after 30"
        })

    if age >= 40:
        screenings.append({
            "test":      "Eye Examination",
            "frequency": "Every year",
            "priority":  "medium",
            "reason":    "Detect glaucoma and vision changes"
        })
        screenings.append({
            "test":      "ECG (Heart)",
            "frequency": "Every year",
            "priority":  "high" if last_checkup_months_ago > 12 else "medium",
            "reason":    "Cardiac health monitoring"
        })

    if age >= 45:
        screenings.append({
            "test":      "Colonoscopy",
            "frequency": "Every 5 years",
            "priority":  "medium",
            "reason":    "Colorectal cancer screening"
        })

    # Gender specific
    if gender_lower == "female":
        if age >= 21:
            screenings.append({
                "test":      "Pap Smear",
                "frequency": "Every 3 years",
                "priority":  "high",
                "reason":    "Cervical cancer screening"
            })
        if age >= 40:
            screenings.append({
                "test":      "Mammogram",
                "frequency": "Every year",
                "priority":  "high",
                "reason":    "Breast cancer screening"
            })
        if age >= 30:
            screenings.append({
                "test":      "Bone Density Test",
                "frequency": "Every 2 years",
                "priority":  "medium",
                "reason":    "Osteoporosis prevention"
            })

    if gender_lower == "male":
        if age >= 40:
            screenings.append({
                "test":      "PSA Test (Prostate)",
                "frequency": "Every year",
                "priority":  "medium",
                "reason":    "Prostate cancer screening"
            })

    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    screenings.sort(key=lambda x: priority_order.get(x["priority"], 3))

    # Overdue flag
    overdue = last_checkup_months_ago > 12

    return {
        "age":                    age,
        "gender":                 gender_lower,
        "last_checkup_months_ago": last_checkup_months_ago,
        "overdue_for_checkup":    overdue,
        "total_screenings":       len(screenings),
        "screenings":             screenings,
        "next_action": (
            "You are overdue for a checkup. Book an appointment this week."
            if overdue else
            "You are up to date. Schedule your next checkup in the coming months."
        )
    }
