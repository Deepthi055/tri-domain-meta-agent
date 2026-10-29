from __future__ import annotations

import re
import logging
from typing import Any
from contextlib import nullcontext

from core.llm_client import call_llm
from core.career_rag_context import use_career_rag_context

from tools.calculators import (
    salary_benchmark,
)

from tools.career_tools import (
    skill_gap_analyzer,
    job_search,
    resume_optimizer,
    learning_path_generator,
)


_CAREER_ANALYSIS_TERMS = (
    "career",
    "job",
    "role",
    "salary",
    "resume",
    "cv",
    "interview",
    "placement",
    "skill gap",
    "roadmap",
    "learning plan",
    "upskill",
    "switch",
    "promotion",
    "hire",
)
_KNOWN_LOCATIONS = {
    "ahmedabad",
    "bengaluru",
    "bangalore",
    "bhubaneswar",
    "chandigarh",
    "chennai",
    "coimbatore",
    "delhi",
    "gurgaon",
    "hyderabad",
    "jaipur",
    "kochi",
    "kolkata",
    "mumbai",
    "noida",
    "pune",
    "remote",
    "india",
    "anywhere",
}

logger = logging.getLogger(__name__)


def _classify_career_intent(
    query: str,
    resume_text: str = "",
) -> dict[str, Any]:
    """Choose only the career tools explicitly needed by a personalized request."""
    normalized = " ".join(query.casefold().split())
    selected: list[str] = []

    if re.search(
        r"\b(find|search|look for|show me|list)\b.{0,45}"
        r"\b(jobs?|openings?|positions?|opportunities)\b"
        r"|\b(job search|matching jobs|jobs matching)\b",
        normalized,
    ):
        selected.append("job_search")

    if re.search(
        r"\b(my|for me|based on my|given my)\b.{0,35}"
        r"\b(salary|pay|compensation|earnings)\b"
        r"|\b(benchmark|compare)\b.{0,30}\bmy salary\b",
        normalized,
    ):
        selected.append("salary_benchmark")

    personal_skill_gap = re.search(
        r"\bmy\b.{0,25}\b(skill gaps?|missing skills?)\b"
        r"|\b(analy[sz]e|assess|compare|identify)\b.{0,35}"
        r"\bmy (?:current )?skills\b",
        normalized,
    )
    if personal_skill_gap:
        selected.append("skill_gap_analyzer")

    personal_learning_plan = re.search(
        r"\b(?:my|personalized|personalised)\b.{0,25}"
        r"\b(?:learning plan|study plan|roadmap|learning path)\b"
        r"|\b(?:create|build|design|make)\b.{0,45}"
        r"\b(?:learning|study) plan\b.{0,25}"
        r"\b(?:for me|based on my|using my)\b",
        normalized,
    )
    if personal_learning_plan or (
        personal_skill_gap
        and re.search(r"\b(close|address|overcome|fix)\b", normalized)
    ):
        selected.append("learning_path_generator")

    if resume_text:
        selected.append("resume_optimizer")

    selected = list(dict.fromkeys(selected))
    personalized_profile_intro = (
        re.search(r"\b(?:introduction|intro|professional summary|about me)\b", normalized)
        and re.search(
            r"\b(?:my career profile|my profile|my background|according to my)\b",
            normalized,
        )
    )
    profile_fields = (
        [
            "current_skills",
            "target_role",
            "experience_level",
            "years_experience",
            "location",
        ]
        if personalized_profile_intro
        else []
    )
    if personalized_profile_intro:
        intent_class = "HYBRID"
        reason = "The request asks for a response based on the user's career profile."
    elif not selected:
        intent_class = "KNOWLEDGE_ONLY"
        reason = "No personalized career-tool intent was detected."
    elif any(
        name in selected
        for name in ("skill_gap_analyzer", "learning_path_generator")
    ):
        intent_class = "HYBRID"
        reason = "The request needs profile-based analysis and career guidance."
    else:
        intent_class = "TOOL_REQUIRED"
        reason = "The request explicitly requires personalized career-tool results."

    return {
        "intent_class": intent_class,
        "tools": selected,
        "reason": reason,
        "profile_fields": profile_fields,
    }


def _should_run_career_analysis(query: str, resume_text: str) -> bool:
    """Preserve the legacy predicate while basing it on detected tool intent."""
    return bool(_classify_career_intent(query, resume_text)["tools"])


def _as_optional_text(value: Any) -> str | None:
    """Return usable text without turning missing profile data into a fact."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def _validated_location(value: Any) -> str | None:
    location = _as_optional_text(value)
    if location and location.casefold() in _KNOWN_LOCATIONS:
        return location
    return None


def _schedule_constraints(query: str) -> str:
    """Describe explicit schedule constraints for the summary model."""
    normalized = query.casefold()
    weeks_match = re.search(r"\b(\d+)\s*[- ]?\s*week", normalized)
    hours_match = re.search(
        r"\b(?:only\s*)?(\d+(?:\.\d+)?)\s*hours?\s*(?:per|a|/)\s*day\b",
        normalized,
    )
    constraints = []
    if weeks_match:
        weeks = int(weeks_match.group(1))
        constraints.append(
            f"Use exactly {weeks} weeks ({weeks * 7} daily entries) "
            "when a daily schedule is requested."
        )
    if hours_match:
        constraints.append(
            f"Plan for approximately {hours_match.group(1)} hour(s) per day."
        )
    language_match = re.search(
        r"\b(?:in|using|with)\s+(java|python|c\+\+|javascript|typescript|go|rust)\b"
        r"|\b(java|python|c\+\+|javascript|typescript|go|rust)\s+"
        r"(?:placement|schedule|roadmap|plan)\b",
        normalized,
    )
    if language_match:
        language = next(
            group for group in language_match.groups() if group is not None
        )
        constraints.append(f"Use the requested language: {language}.")
    else:
        constraints.append(
            "Do not choose or force a programming language unless the user "
            "requests one or validated profile data makes it necessary."
        )
    return " ".join(constraints)


def _requested_timeline_months(query: str) -> int | None:
    match = re.search(r"\b(\d+)\s*[- ]?\s*week", query.casefold())
    if not match:
        return None
    return max(1, round(int(match.group(1)) / 4))


def _get_request_value(
    request: Any,
    field_name: str,
    default: Any,
) -> Any:
    """
    Safely read a value from either an object or dictionary.
    """

    if isinstance(request, dict):
        value = request.get(field_name, default)
    else:
        value = getattr(request, field_name, default)

    return default if value is None else value


def _format_skills(skills: list) -> str:
    """
    Convert the skills list into readable text.
    """

    if not skills:
        return "No skills provided"

    return ", ".join(str(skill) for skill in skills)


def _format_top_job(jobs_data: dict) -> str:
    """
    Format the highest-ranked job returned by job_search().

    FIX: distinguishes "search ran, found nothing" from "search failed"
    so the LLM (and eventually the user) isn't told the same generic
    message for both cases.
    """

    if jobs_data.get("error"):
        return f"Job search could not be completed: {jobs_data['error']}"

    jobs = jobs_data.get("jobs", [])

    if not jobs:
        return "No matching jobs found"

    top_job = jobs[0]

    title = top_job.get("title", "Unknown role")
    company = top_job.get("company", "Unknown company")
    location = top_job.get("location", "Location not specified")
    score = top_job.get("embedding_match_score", 0)

    return (
        f"{title} at {company}, "
        f"Location: {location}, "
        f"Embedding match score: {score}%"
    )


def _format_resume_result(resume_data: dict | None) -> str:
    """
    Format the resume_optimizer() result.
    """

    if not resume_data:
        return "Resume analysis was not requested"

    if resume_data.get("error"):
        return f"Resume analysis could not be completed: {resume_data['error']}"

    semantic_score = resume_data.get("semantic_match_score", 0)

    required_skills = resume_data.get("required_skills", [])
    skills_not_evidenced = resume_data.get("skills_not_evidenced", [])
    suggestions = resume_data.get("suggestions", [])

    return (
        f"Resume semantic match score: {semantic_score}%\n"
        f"Required skills: {_format_skills(required_skills)}\n"
        f"Skills not evidenced: {_format_skills(skills_not_evidenced)}\n"
        f"Suggestions: {suggestions}"
    )


CAREER_ADVISOR_SYSTEM_PROMPT = """
You are a practical and honest assistant in the Career domain.

Answer the user's current query directly and prioritize it over any generic
career-readiness workflow. For technical or educational questions, explain
the requested topic and provide requested examples without adding a career
roadmap. For career-guidance questions, use the supplied profile and career
analysis data to give relevant advice. Do not invent facts, job listings,
salary figures, profile details, or confidence scores.

Return ONLY valid JSON.
Return exactly one key named "summary".
The value of "summary" must be a concise answer to the user's current query.
Do not return Markdown outside the JSON object.
Do not add extra keys.
"""


def _build_summary_prompt(
    current_query: str,
    target_role: str,
    current_skills: list,
    gap_data: dict,
    jobs_data: dict,
    salary_data: dict,
    path_data: dict,
    resume_data: dict | None,
    rag_context: str = "",
    profile_values: dict[str, Any] | None = None,
    tool_selected: list[str] | None = None,
) -> str:
    """
    Build the user-message prompt sent to the language model.

    The LLM is instructed to return only one valid JSON object
    containing a single "summary" field.
    """

    top_job_text = _format_top_job(jobs_data)
    resume_text = _format_resume_result(resume_data)
    included_profile = profile_values or {}
    profile_text = (
        "\n".join(
            f"- {name}: {value}"
            for name, value in included_profile.items()
        )
        or "- No stored profile values included for this query"
    )
    selected_tools_text = ", ".join(tool_selected or []) or "None"

    prompt = f"""
    Answer the user's current query directly and concisely.
    Treat the current query as the primary instruction. Do not provide
    unrelated career recommendations or force a career roadmap.

    Current user query:
    {current_query}

    Explicit schedule constraints:
    {_schedule_constraints(current_query)}

    Use the following career information only when it is relevant to the
    current query. For technical questions, answer the requested topic and
    include requested examples. For career-guidance questions, use the
    profile and analysis data below. Use only information supported by the
    provided data; do not invent job listings, salary figures, profile
    details, or confidence scores.

Target role:
{target_role}

Current skills:
{_format_skills(current_skills)}

Profile values included:
{profile_text}

Tools selected for this request:
{selected_tools_text}

Retrieved career context:
{rag_context}

Skill-gap analysis:
{gap_data}

Top matching job:
{top_job_text}

Salary information:
{salary_data}

Learning path:
{path_data}

Resume analysis:
{resume_text}

When discussing resume improvements, state only achievements supported by the
resume analysis. If an achievement, certification, metric, or experience is
missing, label it as missing and phrase any example conditionally ("if true,
add evidence") rather than as a fact.

For career-guidance questions, cover the relevant parts of the user's
career position, missing skills, learning order, job readiness, job
opportunities, and resume improvements. For other questions, omit these
career details unless the user asks for them.

Return ONLY valid JSON in this exact format:

{{
  "summary": "A concise advisory summary."
}}

The summary must be no more than 350 words.
Use short sections and concise dash-prefixed bullets.
Do not repeat all input data.
"""

    return prompt.strip()


def run(
    request: Any,
    constraints: str = "",
    rag_context: str | None = None,
    rag_enabled: bool | None = None,
) -> dict:
    """
    Run the complete career advisory workflow.

    Expected request fields:

    - current_skills: list
    - target_role: str
    - location: str
    - experience_level: str
    - years_experience: int or float
    - current_level: str
    - timeline_months: int
    - resume_text: str
    """
    
    current_query = _get_request_value(
        request,
        "current_query",
        _get_request_value(request, "query", ""),
    )

    current_skills = _get_request_value(
        request,
        "current_skills",
        [],
    )

    target_role = _get_request_value(request, "target_role", None)

    location = _get_request_value(
        request,
        "location",
        None,
    )

    experience_level = _get_request_value(
        request,
        "experience_level",
        None,
    )

    years_experience = _get_request_value(
        request,
        "years_experience",
        0,
    )

    current_level = _get_request_value(
        request,
        "current_level",
        None,
    )

    timeline_months = _get_request_value(
        request,
        "timeline_months",
        None,
    )

    resume_text = _get_request_value(
        request,
        "resume_text",
        "",
    )

    if not isinstance(current_skills, list):
        current_skills = [str(current_skills)]

    current_skills = [
        str(skill).strip()
        for skill in current_skills
        if str(skill).strip()
    ]

    target_role = _as_optional_text(target_role)
    location = _validated_location(location)
    experience_level = _as_optional_text(experience_level)
    current_level = _as_optional_text(current_level)
    resume_text = str(resume_text).strip()
    current_query = str(current_query).strip()
    requested_timeline = _requested_timeline_months(current_query)
    if requested_timeline is not None:
        timeline_months = requested_timeline

    intent = _classify_career_intent(current_query, resume_text)
    selected_tools = intent["tools"]
    analysis_requested = bool(selected_tools)
    profile_candidates = {
        "current_skills": current_skills,
        "target_role": target_role,
        "location": location,
        "experience_level": experience_level,
        "years_experience": years_experience,
        "current_level": current_level,
        "timeline_months": timeline_months,
    }
    tool_profile_fields = {
        "skill_gap_analyzer": ("current_skills", "target_role"),
        "job_search": (
            "current_skills", "target_role", "location", "experience_level",
        ),
        "salary_benchmark": ("target_role", "location", "years_experience"),
        "learning_path_generator": (
            "current_skills", "target_role", "current_level", "timeline_months",
        ),
        "resume_optimizer": ("target_role",),
    }
    needed_profile_fields = {
        field
        for name in selected_tools
        for field in tool_profile_fields.get(name, ())
    } | set(intent.get("profile_fields", ()))
    profile_labels = {
        "current_skills": "Current skills",
        "target_role": "Target role",
        "location": "Location",
        "experience_level": "Experience level",
        "years_experience": "Years of experience",
        "current_level": "Current level",
        "timeline_months": "Timeline",
    }
    profile_values_used = {
        profile_labels[field]: profile_candidates[field]
        for field in needed_profile_fields
        if field in profile_candidates
        and profile_candidates[field] not in (None, "", [], {})
    }
    if "target_role" not in needed_profile_fields:
        target_role = None
    if "current_skills" not in needed_profile_fields:
        current_skills = []

    gap_data: dict = {}
    jobs_data: dict = {}
    salary_data: dict = {}
    path_data: dict = {}
    resume_data = None
    tool_results: dict[str, dict[str, Any]] = {}
    tool_functions = {
        "skill_gap_analyzer": (
            skill_gap_analyzer,
            {
                "current_skills": current_skills,
                "target_role": target_role or "",
            },
        ),
        "job_search": (
            job_search,
            {
                "target_role": target_role or "",
                "skills": current_skills,
                "location": location or "",
                "experience_level": experience_level or "",
            },
        ),
        "salary_benchmark": (
            salary_benchmark,
            {
                "role": target_role or "",
                "location": location or "",
                "years_experience": years_experience or 0,
            },
        ),
        "learning_path_generator": (
            learning_path_generator,
            {
                "target_role": target_role or "",
                "current_level": current_level or "",
                "timeline_months": timeline_months or 0,
            },
        ),
        "resume_optimizer": (
            resume_optimizer,
            {
                "resume_text": resume_text,
                "target_job": target_role or "",
            },
        ),
    }

    active_context = (
        rag_context
        if rag_context is not None
        else ("" if rag_enabled is False else None)
    )
    context_scope = (
        use_career_rag_context(active_context)
        if active_context is not None
        else nullcontext()
    )
    with context_scope:
        for tool_name in selected_tools:
            function, kwargs = tool_functions[tool_name]
            if tool_name == "learning_path_generator":
                kwargs["missing_skills"] = (
                    gap_data.get("missing_skills", [])
                    if isinstance(gap_data, dict)
                    else []
                )
            if active_context is not None and tool_name in {
                "skill_gap_analyzer",
                "learning_path_generator",
                "resume_optimizer",
            }:
                kwargs["rag_context"] = active_context
            try:
                output = function(**kwargs)
                failed = (
                    not isinstance(output, dict)
                    or output.get("status") == "failed"
                    or bool(output.get("error"))
                )
                tool_results[tool_name] = {
                    "status": "failed" if failed else "completed",
                    "output": output,
                }
                if failed:
                    logger.warning(
                        "Career tool %s returned an unsuccessful result.",
                        tool_name,
                    )
                    output = {}
            except Exception as exc:
                logger.exception(
                    "Career tool %s failed: %s: %s",
                    tool_name,
                    type(exc).__name__,
                    str(exc),
                )
                tool_results[tool_name] = {
                    "status": "failed",
                    "output": {"error": str(exc)},
                }
                output = {}

            if tool_name == "skill_gap_analyzer":
                gap_data = output
            elif tool_name == "job_search":
                jobs_data = output
            elif tool_name == "salary_benchmark":
                salary_data = output
            elif tool_name == "learning_path_generator":
                path_data = output
            elif tool_name == "resume_optimizer":
                resume_data = output

    # ---------------------------------------------------------
    # 5. Analyze resume if supplied
    # ---------------------------------------------------------

    tool_outputs = {
        name: tool_results[name]
        for name in selected_tools
    }
    tools_used = [
        name for name in selected_tools
    ]
    sources = []
    for tool_result in tool_outputs.values():
        output = tool_result.get("output", {})
        if tool_result.get("status") != "completed" or not isinstance(output, dict):
            continue
        source_values = output.get("sources", output.get("source", []))
        if isinstance(source_values, str):
            source_values = [source_values]
        if isinstance(source_values, list):
            sources.extend(
                source for source in source_values if isinstance(source, str)
            )

    # ---------------------------------------------------------
    # 6. Build the language-model prompt
    # ---------------------------------------------------------

    summary_prompt = _build_summary_prompt(
        current_query=current_query,
        target_role=target_role,
        current_skills=current_skills,
        gap_data=gap_data,
        jobs_data=jobs_data,
        salary_data=salary_data,
        path_data=path_data,
        resume_data=resume_data,
        rag_context=rag_context or "",
        profile_values=profile_values_used,
        tool_selected=selected_tools,
    )

    if constraints:
        summary_prompt += f"""

Additional constraints:
{constraints}
"""

        # ---------------------------------------------------------
    # 7. Generate final career advice
    # ---------------------------------------------------------

    try:
        llm_result = call_llm(
            CAREER_ADVISOR_SYSTEM_PROMPT,
            summary_prompt,
            temperature=0.4,
            max_tokens=2500,
        )
        print("DEBUG - LLM RESULT:")
        print(llm_result)

        if not isinstance(llm_result, dict):
            llm_response = str(llm_result)

        elif llm_result.get("summary"):
            llm_response = str(llm_result["summary"])

        elif llm_result.get("recommendation"):
            llm_response = str(llm_result["recommendation"])

        elif llm_result.get("error"):
            llm_response = (
                "Career analysis was completed, but the final advisory "
                f"response could not be generated: {llm_result['error']}"
            )

        else:
            llm_response = (
                "Career analysis was completed, but the model returned "
                "an unexpected response format."
            )

    except Exception as exc:
        import traceback

        traceback.print_exc()

        llm_response = (
            "Career analysis was completed, but the final advisory "
            f"response could not be generated: {exc}"
        )

    # ---------------------------------------------------------
    # 8. Return structured result
    # ---------------------------------------------------------

    return {
        "target_role": target_role,
        "location": location,
        "experience_level": experience_level,
        "current_skills": current_skills,
        "skill_gap": gap_data,
        "jobs": jobs_data,
        "salary": salary_data,
        "learning_path": path_data,
        "resume_analysis": resume_data,
        "summary": llm_response,
        "tools_used": tools_used if analysis_requested else [],
        "tool_outputs": (
            tool_outputs if analysis_requested else {}
        ),
        "sources": list(dict.fromkeys(sources)) if analysis_requested else [],
        "intent_class": intent["intent_class"],
        "tool_selected": selected_tools or None,
        "tool_selected_reason": intent["reason"] if selected_tools else None,
        "profile_values_used": profile_values_used,
        "rag_enabled": rag_enabled,
        "retrieval_status": (
            "success"
            if rag_context
            else "disabled"
            if rag_enabled is False
            else "empty"
            if rag_context is not None
            else "not_attempted"
        ),
        "context_in_prompt": bool(rag_context),
    }