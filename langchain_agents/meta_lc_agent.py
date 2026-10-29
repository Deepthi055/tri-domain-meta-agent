"""
Meta LangChain Agent
Routes queries to the correct LangChain domain agents.
Drop-in replacement for the existing meta_agent in main.py.
"""
import agents.career_agent as career_original
import agents.health_agent as health_original
import agents.finance_agent as finance_original
import logging
import os
from sqlalchemy.orm import Session
from types import SimpleNamespace
from langchain_agents.career_lc_agent import (
    _build_career_explainability,
    run as career_run,
)
from langchain_agents.health_lc_agent import run as health_run
from langchain_agents.finance_lc_agent import run as finance_run
from core.intent_detector import detect_intent
from core.safety_layer import check_safety, check_relevance, is_uncertainty_request
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=3)
logger = logging.getLogger(__name__)

FALLBACK_AGENTS = {
    "career": career_original.run,
    "health": health_original.run,
    "finance": finance_original.run,
}


def _build_chat_explainability(domain: str, request, result: dict) -> dict:
    """Build explainability from values and executions present in the result."""
    data_used = [f"Original query: {getattr(request, 'query', '')}"]
    decision_factors = []

    if domain == "career":
        profile_fields = {
            "Target role": getattr(request, "target_role", None),
            "Current skills": getattr(request, "current_skills", None),
            "Experience level": getattr(request, "experience_level", None),
            "Location": getattr(request, "location", None),
            "Timeline": getattr(request, "timeline_months", None),
        }
        tools_used = result.get("tools_used") or []
        used_profile_fields = {
            "skill_gap_tool": {"Current skills", "Target role"},
            "skill_gap_analyzer": {"Current skills", "Target role"},
            "job_search_tool": {"Current skills", "Location", "Experience level"},
            "job_search": {"Current skills", "Location", "Experience level"},
            "salary_benchmark_tool": {"Target role", "Location"},
            "salary_benchmark": {"Target role", "Location"},
            "learning_path_tool": {"Target role", "Experience level", "Timeline"},
            "learning_path_generator": {"Target role", "Experience level", "Timeline"},
            "resume_optimizer": {"Target role"},
        }
        fields_used = set().union(
            *(used_profile_fields.get(tool, set()) for tool in tools_used)
        )
        data_used.extend(
            f"{label}: {value}"
            for label, value in profile_fields.items()
            if label in fields_used and value not in (None, "", [], {})
        )
        next_steps = [
            "Review the recommendation against the question and evidence used."
        ]
        if not tools_used:
            decision_factors.append(
                "The answer was generated without career-tool execution."
            )
        else:
            decision_factors.append(
                "The answer used only the career tools listed in the execution trace."
            )
    elif domain == "health":
        profile_fields = {
            "Age": getattr(request, "age", None),
            "Weight": getattr(request, "weight_kg", None),
            "Height": getattr(request, "height_cm", None),
            "Fitness goal": getattr(request, "fitness_goal", None),
            "Sleep hours": getattr(request, "sleep_hours", None),
        }
        data_used.extend(
            f"{label}: {value}"
            for label, value in profile_fields.items()
            if value not in (None, "", [], {})
        )
        next_steps = [
            "Use the recommendation alongside your current health profile.",
            "Provide specific symptoms, goals, or medical context for a more tailored answer.",
        ]
    else:
        data_used.append("Persisted finance profile data available to the finance agent")
        next_steps = [
            "Review the recommendation against your income, expenses, and financial goals.",
            "Update your finance profile if any values are missing or outdated.",
        ]

    reason = result.get("reason")
    if reason:
        decision_factors.append(str(reason))

    confidence = result.get("confidence")
    has_defensible_confidence = (
        isinstance(confidence, (int, float)) and 0 <= confidence <= 1
    )
    confidence_text = (
        f"The {domain} agent reported confidence of {confidence}."
        if has_defensible_confidence
        else "No confidence score was reported."
    )
    tool_outputs = result.get("tool_outputs", {})
    failed_tools = list(result.get("failed_tools", []))
    if isinstance(tool_outputs, dict):
        failed_tools.extend(
            tool_name
            for tool_name, output in tool_outputs.items()
            if isinstance(output, dict) and output.get("status") == "failed"
        )
    failed_tools = list(dict.fromkeys(failed_tools))
    limitations = []
    if failed_tools:
        limitations.append(f"Tools that failed: {', '.join(map(str, failed_tools))}.")
    if not result.get("sources"):
        limitations.append("No retrieved sources were recorded.")
    if not result.get("tools_used"):
        limitations.append("No career-tool evidence was recorded.")
    profile_values_used = {}
    if domain == "career":
        profile_values_used = {
            label: getattr(request, attribute, None)
            for label, attribute in {
                "Target role": "target_role",
                "Current skills": "current_skills",
                "Experience level": "experience_level",
                "Location": "location",
                "Timeline": "timeline_months",
            }.items()
            if label in fields_used
            and getattr(request, attribute, None) not in (None, "", [], {})
        }
    return {
        "original_query": getattr(request, "query", ""),
        "selected_agent": result.get("agent_type", f"{domain}_agent"),
        "data_used": data_used,
        "profile_values_used": profile_values_used,
        "decision_factors": decision_factors,
        "next_steps": next_steps,
        "confidence_explanation": confidence_text,
        "tools_invoked": result.get("tools_used", []),
        "tool_statuses": {
            tool_name: output.get("status")
            for tool_name, output in tool_outputs.items()
            if isinstance(output, dict)
        } if isinstance(tool_outputs, dict) else {},
        "retrieved_sources": (
            result.get("retrieved_sources", [])
            if domain == "career"
            else result.get("sources", [])
        ),
        "limitations": limitations,
    }


def _build_chat_request(db: Session, user_id: str, query: str) -> SimpleNamespace:
    """Adapt persisted profile data to the LangChain agent request contract."""
    from services.profile_service import get_full_profile

    profile = get_full_profile(db, user_id)
    general = profile.get("general")
    career = profile.get("career")
    health = profile.get("health")
    finance = profile.get("finance")

    request = SimpleNamespace(
        name="User",
        age=getattr(general, "age", 25) or 25,
        query=query,
        current_query=query,
        current_skills=getattr(career, "current_skills", None) or [],
        target_role=getattr(career, "target_role", None),
        location=getattr(general, "location", None),
        experience_level=getattr(career, "experience_level", None),
        years_experience=0,
        timeline_months=None,
        current_level=getattr(career, "experience_level", None),
        weight_kg=getattr(general, "weight_kg", None) or 70,
        height_cm=getattr(general, "height_cm", None) or 170,
        sleep_hours=getattr(health, "sleep_hours", None) or 7,
        sleep_quality=getattr(health, "sleep_quality", None) or 7,
        stress_level=getattr(health, "stress_level", None) or 5,
        mood_score=getattr(health, "mood_score", None) or 7,
        anxiety_level=getattr(health, "anxiety_level", None) or 4,
        fitness_goal=getattr(health, "fitness_goal", None) or "general fitness",
        available_days=getattr(health, "active_days_per_week", None) or 3,
        fitness_experience="beginner",
        monthly_income=getattr(finance, "monthly_income", None),
        monthly_expenses=getattr(finance, "monthly_expenses", None),
        current_savings=getattr(finance, "current_savings", None),
        risk_tolerance=getattr(finance, "risk_appetite", None),
        investment_experience=getattr(finance, "investment_experience", None),
        financial_goals=getattr(finance, "financial_goals", None),
        portfolio=getattr(finance, "portfolio", None) or {},
        debts=getattr(finance, "debts", None) or [],
        total_debt=getattr(finance, "total_debt", None),
        monthly_debt_payment=getattr(finance, "monthly_debt_payment", None),
        retirement_age=getattr(finance, "retirement_age", None),
        retirement_savings=getattr(finance, "retirement_savings", None),
        monthly_contribution=getattr(finance, "monthly_contribution", None),
        annual_income=getattr(finance, "annual_income", None),
        tax_deductions=getattr(finance, "tax_deductions", None) or {},
    )
    return request


def _states_no_income(query: str) -> bool:
    normalized = query.lower().replace("-", " ")
    return any(
        phrase in normalized
        for phrase in (
            "no income",
            "dont have income",
            "don't have income",
            "do not have income",
            "without income",
            "not earning",
        )
    )


def run_chat_agent(db: Session, user_id: str, domain: str, query: str) -> dict:
    """Run the official LangChain domain agent for an authenticated chat."""
    safety = check_safety(query)
    if not safety["is_safe"]:
        return {
            "status": "blocked",
            "domain": domain,
            "tools_used": [],
            "message": safety["message"],
            "reason": safety["reason"],
            "confidence": 1.0,
            "confidence_level": "High",
        }

    # Intent detection uses "general" when a query does not match any of the
    # supported domains. Keep that result in the normal chat response flow
    # rather than trying to look up a non-existent domain agent.
    if domain == "general":
        relevance = check_relevance(query)
        intent = detect_intent(query)
        if intent.get("ambiguous"):
            return {
                "status": "clarification_needed",
                "domain": domain,
                "tools_used": [],
                "message": (
                    "Could you clarify what you mean by feeling tired? "
                    "Are you asking about sleep, physical fatigue, stress, "
                    "or something else?"
                ),
                "reason": intent["reasoning"],
                "confidence": intent["confidence"],
                "confidence_level": "Low",
            }
        return {
            "status": "out_of_scope",
            "domain": domain,
            "tools_used": [],
            "message": (
                relevance.get("message")
                or "Please ask a question about Career, Health, or Finance."
            ),
            "reason": "No supported chat domain was detected",
            "confidence": 0.0,
            "confidence_level": "Low",
        }

    if domain == "finance" and _states_no_income(query):
        return {
            "status": "success",
            "domain": "finance",
            "tools_used": [],
            "message": (
                "Because you currently have no income, do not commit to "
                "investments that require regular contributions. First cover "
                "essential college costs, keep a small cash buffer, and build "
                "an emergency fund from scholarships, family support, or "
                "future earnings. Once you have stable income and a defined "
                "goal, we can compare suitable low-risk options."
            ),
            "reason": "The current query states that the user has no income",
            "confidence": 0.9,
            "confidence_level": "High",
        }

    request = _build_chat_request(db, user_id, query)
    agent = {
        "career": career_run,
        "health": health_run,
        "finance": finance_run,
    }.get(domain)
    if agent is None:
        raise ValueError(f"Unsupported chat domain: {domain}")
    started_at = time.perf_counter()
    result = agent(request)
    latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
    if not isinstance(result, dict):
        raise TypeError(f"{domain} agent returned an invalid response")

    if domain == "career":
        # Complete partial metadata without replacing values recorded by the
        # Career agent. Empty values remain meaningful execution evidence.
        generated = _build_career_explainability(request, result)
        existing = result.get("explainability")
        if isinstance(existing, dict):
            generated.update({
                key: value
                for key, value in existing.items()
                if value not in (None, "", {}, [])
            })
        result["explainability"] = generated
    elif not result.get("explainability"):
        result["explainability"] = _build_chat_explainability(
            domain, request, result
        )
    explainability = result.get("explainability")
    if not isinstance(explainability, dict):
        explainability = {}
    explainability["latency_ms"] = latency_ms
    result["explainability"] = explainability
    return result


def run_chat_agents(
    db: Session, user_id: str, domains: list[str], query: str
) -> dict:
    """Run each detected domain agent and combine their chat responses."""
    if is_uncertainty_request(query):
        return {
            "status": "success",
            "domain": domains[0] if domains else "general",
            "domains": domains,
            "message": (
                "No one can reliably guarantee an exact future salary or "
                "investment return. Salary depends on role, skills, location, "
                "employer, and market conditions. Investment returns vary with "
                "the asset, time horizon, fees, and market risk; past "
                "performance is not a guarantee. I can help estimate a salary "
                "range and compare conservative, moderate, or aggressive "
                "scenarios instead."
            ),
            "reason": "The request asks for unknowable exact future outcomes",
            "tools_used": [],
            "confidence": 0.2,
            "confidence_level": "Low",
        }
    results = [run_chat_agent(db, user_id, domain, query) for domain in domains]
    if not results:
        return run_chat_agent(db, user_id, "general", query)

    answers = []
    tools_used = []
    explainability = []
    reported_confidences = []
    for result in results:
        answer = (
            result.get("recommendation")
            or result.get("message")
            or result.get("summary")
            or result.get("content")
        )
        if answer:
            label = result.get("domain", "Domain").title()
            answers.append(f"{label} perspective:\n{answer}")
        tools_used.extend(result.get("tools_used", []))
        if result.get("explainability"):
            explainability.append(result["explainability"])
        confidence = result.get("confidence")
        if isinstance(confidence, (int, float)) and 0 <= confidence <= 1:
            reported_confidences.append(float(confidence))

    combined = {
        "status": "success",
        "domain": domains[0],
        "domains": domains,
        "message": "\n\n".join(answers),
        "tools_used": list(dict.fromkeys(tools_used)),
        "confidence": (
            sum(reported_confidences) / len(reported_confidences)
            if reported_confidences
            else None
        ),
        "confidence_level": "High" if all(
            result.get("confidence_level") == "High" for result in results
        ) else ("Medium" if reported_confidences else None),
    }
    if explainability:
        combined["explainability"] = {
            "domain_explanations": dict(zip(domains, explainability))
        }
    return combined


async def meta_lc_agent(request) -> dict:
    """
    LangChain powered meta agent.
    Same interface as existing meta_agent() in main.py.
    """
    # Safety check
    safety = check_safety(request.query)
    if not safety["is_safe"]:
        return {
            "status":            "blocked",
            "reason":            safety["reason"],
            "message":           safety["message"],
            "domains_activated": []
        }

    # Relevance check
    relevance = check_relevance(request.query)
    if not relevance["is_relevant"]:
        return {
            "status":            "out_of_scope",
            "message":           relevance["message"],
            "domains_activated": []
        }

    # Intent detection
    if request.domain == "auto":
        intent  = detect_intent(request.query)
        domains = intent["domains"]
    else:
        intent = {
            "domains":    [request.domain],
            "confidence": 1.0,
            "reasoning":  "Manual domain selection"
        }
        domains = [request.domain]

    # Route to LangChain agents
    agent_map = {
        "career":  career_run,
        "health":  health_run,
        "finance": finance_run,
    }

    loop = asyncio.get_event_loop()

    def run_one(domain):
        fn = agent_map.get(domain)
        if fn:
            return fn(request)
        return {"domain": domain, "message": "Unknown domain"}

    futures = [
        loop.run_in_executor(executor, run_one, domain)
        for domain in domains if domain in agent_map
    ]

    results = await asyncio.gather(*futures, return_exceptions=True)
    responses = []
    for domain, result in zip(domains, results):
        if isinstance(result, Exception):
            try:
                raise result
            except Exception as exc:
                logger.exception(
                    "[LangChain Meta] %s fallback at invoke: %s: %s",
                    domain,
                    type(exc).__name__,
                    str(exc),
                )
            fallback_fn = FALLBACK_AGENTS.get(domain)
            if fallback_fn:
                if domain == "career":
                    retrieval_state = (
                        request.get("_career_retrieval_state", {})
                        if isinstance(request, dict)
                        else getattr(request, "_career_retrieval_state", {})
                    ) or {}
                    fallback = fallback_fn(
                        request,
                        rag_context=retrieval_state.get("context"),
                        rag_enabled=retrieval_state.get(
                            "rag_enabled",
                            os.getenv("USE_RAG", "true").strip().lower() == "true",
                        ),
                    )
                    fallback["retrieval_status"] = retrieval_state.get(
                        "status",
                        fallback.get("retrieval_status", "not_attempted"),
                    )
                    fallback["retrieval_status_before_fallback"] = (
                        retrieval_state.get(
                            "status",
                            fallback["retrieval_status"],
                        )
                    )
                    fallback["retrieved_sources"] = retrieval_state.get(
                        "retrieved_sources",
                        fallback.get("retrieved_sources", []),
                    )
                    fallback["rag_available"] = retrieval_state.get(
                        "rag_available",
                        fallback.get("rag_available"),
                    )
                    fallback["context_in_prompt"] = bool(
                        retrieval_state.get("context")
                    )
                    fallback["intent_class"] = retrieval_state.get(
                        "intent_class",
                        fallback.get("intent_class"),
                    )
                    fallback["tool_selected"] = retrieval_state.get(
                        "tool_selected",
                        fallback.get("tool_selected"),
                    )
                    fallback["tool_selected_reason"] = retrieval_state.get(
                        "tool_selected_reason",
                        fallback.get("tool_selected_reason"),
                    )
                else:
                    fallback = fallback_fn(request)
                fallback["agent_type"] = "fallback"
                fallback["fallback_reason"] = (
                    f"{type(result).__name__}: {str(result)[:300]}"
                )
                fallback["fallback_stage"] = "invoke"
                if domain != "career":
                    fallback["rag_enabled"] = (
                        os.getenv("USE_RAG", "true").strip().lower() == "true"
                    )
                    fallback["retrieval_status_before_fallback"] = fallback.get(
                        "retrieval_status", "not_attempted"
                    )
                if domain == "career":
                    fallback["selected_agent_reason"] = (
                        f"Outer fallback was used after invoke: "
                        f"{fallback['fallback_reason']}"
                    )
                    fallback["explainability"] = _build_career_explainability(
                        request, fallback
                    )
                responses.append(fallback)
            else:
                responses.append({
                    "domain": domain,
                    "error": "agent_failure",
                    "message": f"{domain} agent failed and no fallback is available."
                })
        else:
            responses.append(result)

    return {
        "status":            "success",
        "intent":            intent,
        "responses":         responses,
        "domains_activated": domains,
        "agent_framework":   "langchain"
    }