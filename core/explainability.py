def build_explainability(domain: str, agent_response: dict, request) -> dict:
    """
    Builds an explainability block for any agent response.
    Takes the domain, agent response, and original request.
    Returns a structured explanation dict.
    """

    data_used        = []
    decision_factors = []
    next_steps       = []

    # ── CAREER ────────────────────────────────────────────────────────
    if domain == "career":

        if "skill_gap" in agent_response:
            sg = agent_response["skill_gap"]
            data_used.append(f"Skill match: {sg['match_percentage']}% for {sg['target_role']}")
            data_used.append(f"Missing skills: {', '.join(sg['missing_skills'])}")

        if "job_matches" in agent_response:
            jm = agent_response["job_matches"]
            if jm["jobs"]:
                top = jm["jobs"][0]
                data_used.append(f"Top job match: {top['title']} at {top['match_score']}%")

        if "salary_benchmark" in agent_response:
            sb = agent_response["salary_benchmark"]
            data_used.append(f"Salary range: Rs.{sb['market_range_lpa']['min']}-{sb['market_range_lpa']['max']} LPA")

        if "learning_path" in agent_response:
            lp = agent_response["learning_path"]
            data_used.append(f"Learning path: {lp['total_weeks_required']} weeks required")

        # Decision factors
        if "skill_gap" in agent_response:
            sg = agent_response["skill_gap"]
            if sg["match_percentage"] < 40:
                decision_factors.append("Significant skill gap — learning is top priority")
            elif sg["match_percentage"] < 70:
                decision_factors.append("Moderate skill gap — targeted upskilling needed")
            else:
                decision_factors.append("Strong skill match — focus on portfolio and interviews")

        if "job_matches" in agent_response:
            jm = agent_response["job_matches"]
            if jm["total_matches"] > 3:
                decision_factors.append(f"Good job market demand — {jm['total_matches']} matching roles found")
            else:
                decision_factors.append("Limited job matches — more skills needed")

        # Next steps
        if "skill_gap" in agent_response:
            sg = agent_response["skill_gap"]
            for skill in sg["missing_skills"][:3]:
                next_steps.append(f"Learn {skill}")
        if "learning_path" in agent_response:
            lp = agent_response["learning_path"]
            if lp["phases"]:
                next_steps.append(f"Start with: {lp['phases'][0]['focus']}")
        next_steps.append("Build 2 portfolio projects before applying")
        next_steps.append("Update LinkedIn and GitHub profiles")

    # ── HEALTH ────────────────────────────────────────────────────────
    elif domain == "health":

        if "bmi" in agent_response:
            bmi = agent_response["bmi"]
            data_used.append(f"BMI: {bmi['bmi']} ({bmi['category']})")

        if "fitness" in agent_response:
            ft = agent_response["fitness"]
            data_used.append(f"Fitness score: {ft['fitness_score']}/100 ({ft['fitness_level']})")
            data_used.append(f"Weight to lose: {ft['weight_to_lose_kg']} kg")

        if "sleep" in agent_response:
            sl = agent_response["sleep"]
            data_used.append(f"Sleep score: {sl['sleep_score']}/100 ({sl['sleep_level']})")

        if "mental_health" in agent_response:
            mh = agent_response["mental_health"]
            data_used.append(f"Wellness score: {mh['wellness_score']}/100")
            data_used.append(f"Stress level: {mh['stress_level']}/10")

        # Decision factors
        if "bmi" in agent_response:
            bmi = agent_response["bmi"]
            if bmi["category"] == "Obese":
                decision_factors.append("BMI in obese range — weight loss is urgent priority")
            elif bmi["category"] == "Overweight":
                decision_factors.append("BMI in overweight range — gradual weight loss recommended")
            else:
                decision_factors.append("BMI in healthy range — focus on maintaining fitness")

        if "sleep" in agent_response:
            sl = agent_response["sleep"]
            if sl["sleep_score"] < 60:
                decision_factors.append("Poor sleep detected — sleep improvement is critical")

        if "mental_health" in agent_response:
            mh = agent_response["mental_health"]
            if mh["stress_level"] >= 7:
                decision_factors.append("High stress detected — stress management needed")

        # Next steps
        if "workout_plan" in agent_response:
            wp = agent_response["workout_plan"]
            next_steps.append(f"Follow {wp['days_per_week']}-day workout plan consistently")
        if "sleep" in agent_response:
            sl = agent_response["sleep"]
            if sl["sleep_score"] < 70:
                next_steps.append("Fix sleep schedule — aim for 7-9 hours before midnight")
        if "screenings" in agent_response:
            sc = agent_response["screenings"]
            if sc["overdue_for_checkup"]:
                next_steps.append("Book a full health checkup this week")
        next_steps.append("Track meals daily for 2 weeks")
        next_steps.append("Practice 10 min meditation daily")

    # ── FINANCE ───────────────────────────────────────────────────────
    elif domain == "finance":

        if "savings" in agent_response:
            sv = agent_response["savings"]
            data_used.append(f"Savings rate: {sv['rate_pct']}%")
            data_used.append(f"Monthly savings: Rs.{sv['savings']}")

        if "debt_ratio" in agent_response:
            dr = agent_response["debt_ratio"]
            data_used.append(f"Debt-to-income ratio: {dr['debt_to_income_ratio']} ({dr['status']})")

        # Decision factors
        if "savings" in agent_response:
            sv = agent_response["savings"]
            if sv["rate_pct"] < 10:
                decision_factors.append("Critical savings rate — immediate budget review needed")
            elif sv["rate_pct"] < 20:
                decision_factors.append("Below recommended 20% savings rate — needs improvement")
            else:
                decision_factors.append("Good savings rate — focus on investment strategy")

        if "debt_ratio" in agent_response:
            dr = agent_response["debt_ratio"]
            if dr["status"] == "concerning":
                decision_factors.append("High debt ratio — debt reduction is top priority")

        # Next steps
        next_steps.append("Create a monthly budget spreadsheet")
        next_steps.append("Set up automatic SIP of at least Rs.2000/month")
        next_steps.append("Build 3-6 month emergency fund first")
        next_steps.append("Review and cut unnecessary subscriptions")

    # ── Confidence explanation ─────────────────────────────────────────
    confidence = agent_response.get("confidence", 0.0)
    if confidence >= 0.9:
        confidence_explanation = "Very high confidence — strong data signals available"
    elif confidence >= 0.75:
        confidence_explanation = "High confidence — most key data points present"
    elif confidence >= 0.5:
        confidence_explanation = "Moderate confidence — some data missing"
    else:
        confidence_explanation = "Low confidence — limited data available"

    return {
        "data_used":              data_used,
        "decision_factors":       decision_factors,
        "confidence_explanation": confidence_explanation,
        "next_steps":             next_steps,
        "disclaimer":             "This is AI-generated advice for informational purposes only. Please consult a qualified professional before making major decisions."
    }