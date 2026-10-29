"""
Career LangChain Agent — LangChain 1.x + LangGraph
Uses create_react_agent from langgraph.prebuilt
"""
import os
import json
import logging
import re
import importlib.util
from agents.career_agent import _classify_career_intent
from core.career_rag_context import use_career_rag_context
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from core.config import settings

load_dotenv()
logger = logging.getLogger(__name__)

# ── LLM ──────────────────────────────────────────────────────
llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model=settings.GROQ_MODEL,
    temperature=0.7
)

# ── Tools ─────────────────────────────────────────────────────
@tool
def skill_gap_tool(current_skills: list, target_role: str) -> dict:
    """Analyzes skill gap between current skills and target role.
    Returns match percentage and missing skills.
    Use when user wants to switch roles or learn new skills."""
    from tools.career_tools import skill_gap_analyzer
    return skill_gap_analyzer(current_skills, target_role)

@tool
def job_search_tool(
    target_role: str,
    current_skills: list,
    location: str,
    experience_level: str,
) -> dict:
    """Finds job matches based on skills, location and experience.
    Use when user asks about job opportunities or market demand."""
    from tools.career_tools import job_search
    return job_search(
        target_role=target_role,
        skills=current_skills,
        location=location,
        experience_level=experience_level,
    )

@tool
def salary_benchmark_tool(target_role: str, location: str, years_experience: int) -> dict:
    """Returns salary benchmarks for a role in a location.
    Use when user asks about salary expectations or negotiation."""
    from tools.calculators import salary_benchmark
    return salary_benchmark(target_role, location, years_experience)

@tool
def learning_path_tool(target_role: str, current_level: str, timeline_months: int) -> dict:
    """Generates structured learning path to reach a target role.
    Use when user asks how to learn or transition into a role."""
    from tools.career_tools import learning_path_generator
    return learning_path_generator(target_role, current_level, timeline_months)

# ── System prompt ─────────────────────────────────────────────
SYSTEM_PROMPT = """You are a specialist career advisor inside a TriDomain AI system.
You have tools for skill gap analysis, job search, salary benchmarking and learning paths.

RULES:
1. Answer the user's query directly.
2. For technical concept questions, explain the requested concept and do not
   call career tools or add an unrelated roadmap.
3. Use a tool only when the query requires that tool. Do not claim a tool ran
   unless its result is present in the conversation.
4. Never invent profile values, achievements, job listings, sources, or
   confidence scores.
5. Never recommend quitting without a financial safety plan.
6. Tailor advice to the Indian job market only when location or market advice
   is relevant.
7. If the user requests a four-week daily schedule, produce 28 daily entries
   with approximately the requested daily time. Do not choose C++, Java, or
   another language unless the user explicitly requests it or validated profile
   data requires it. Keep weekly topics and durations consistent with the
   requested schedule.

GROUNDING AND SOURCE ATTRIBUTION RULES:
1. Use retrieved context as the primary evidence for claims about the career
   knowledge base.
2. Cite the exact document title shown in retrieved text for each
   knowledge-base-supported claim.
3. Do not invent source names, statistics, quotations, or document contents.
4. If retrieved documents do not specify role-specific skills, state that
   limitation clearly.
5. Separate retrieved evidence from general recommendations. Label
   recommendations not directly supported by retrieved context as
   "General guidance, not explicitly stated in the knowledge base."
6. Never attribute a claim to a document unless the retrieved text from that
   document supports it.
7. If retrieval status is empty, failed, or disabled, or no relevant context is
   provided, state that the knowledge base does not contain sufficient
   evidence. Do not imply retrieval succeeded merely because a source filename
   is available.

After using tools, respond ONLY with valid JSON:
{
    "recommendation": "specific actionable advice",
    "reason": "why this fits this user based on tool results"
}"""

# ── Agent ─────────────────────────────────────────────────────
tools = [skill_gap_tool, job_search_tool, salary_benchmark_tool, learning_path_tool]
career_agent = create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)


def _build_career_explainability(request, result: dict) -> dict:
    """Build Career Explainability strictly from the execution record."""
    query = getattr(request, "query", "")
    tools_used = result.get("tools_used") or []
    tool_outputs = result.get("tool_outputs") or {}
    profile_fields = {
        "Target role": getattr(request, "target_role", None),
        "Current skills": getattr(request, "current_skills", None),
        "Experience level": getattr(request, "experience_level", None),
        "Location": getattr(request, "location", None),
        "Timeline": getattr(request, "timeline_months", None),
    }
    tool_profile_fields = {
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
        *(tool_profile_fields.get(tool_name, set()) for tool_name in tools_used)
    )
    derived_profile_values = {
        label: value
        for label, value in profile_fields.items()
        if label in fields_used and value not in (None, "", [], {})
    }
    profile_values_used = result.get(
        "profile_values_used",
        derived_profile_values,
    ) or {}
    failed_tools = [
        tool_name
        for tool_name, output in tool_outputs.items()
        if isinstance(output, dict) and output.get("status") == "failed"
    ]
    sources = result.get("sources") or []
    raw_retrieved_sources = result.get("retrieved_sources")
    if raw_retrieved_sources is None:
        raw_retrieved_sources = []
    retrieved_sources = [
        {
            "doc_title": source.get("doc_title"),
            "chunk_id": source.get("chunk_id"),
            "score": source.get("score"),
        }
        for source in raw_retrieved_sources
        if isinstance(source, dict)
    ]
    context_in_prompt = bool(result.get("context_in_prompt", False))
    query_facts = _extract_career_query_facts(query)
    data_used = [f"Original query: {query}"]
    data_used.extend(f"{label}: {value}" for label, value in query_facts.items())
    data_used.extend(
        f"{label}: {value}" for label, value in profile_values_used.items()
    )
    limitations = []
    retrieval_status = result.get("retrieval_status", "not_attempted")
    if retrieval_status == "success" and not (
        context_in_prompt and retrieved_sources
    ):
        retrieval_status = (
            "disabled" if result.get("rag_enabled") is False else "empty"
        )
    retrieval_error = result.get("retrieval_error")
    if not tools_used:
        limitations.append("No Career tools were executed for this answer.")
    if retrieval_status == "failed":
        limitations.append("Career knowledge retrieval failed; the answer used the LLM fallback.")
        if retrieval_error:
            limitations.append(f"Retrieval error: {retrieval_error}")
    elif retrieval_status == "empty":
        limitations.append("Career knowledge retrieval returned no documents.")
    elif retrieval_status == "unavailable":
        limitations.append("Career knowledge retrieval is unavailable.")
    elif retrieval_status == "not_used":
        limitations.append("No retrieved Career context was included in the prompt.")
    elif retrieval_status == "not_attempted" and not sources:
        limitations.append("No retrieved Career sources were recorded.")
    if failed_tools:
        limitations.append(
            f"Tool execution failed: {', '.join(failed_tools)}."
        )
    if retrieval_status == "success":
        decision_factors = [
            "The answer was generated by the LangChain Career LLM using retrieved Career documents."
        ]
    elif tools_used:
        decision_factors = [
            "The answer reflects the Career tools recorded in the execution trace."
        ]
    else:
        decision_factors = [
            "The answer was generated directly by the LangChain Career LLM."
        ]
    decision_factors.extend(
        f"{label} was taken from the user's query."
        for label in query_facts
    )
    if failed_tools:
        decision_factors.append("Failed tool outputs were not treated as successful evidence.")

    missing_profile_fields = [
        label
        for label, value in profile_fields.items()
        if value in (None, "", [], {})
        and label in (
            {"Target role", "Current skills", "Experience level"}
            if query_facts.get("Placement goal")
            else fields_used
        )
    ]
    explanation = {
        "original_query": query,
        "selected_agent": result.get("agent_type", "langchain"),
        "domain": "career",
        "data_used": data_used,
        "profile_values_used": profile_values_used,
        "decision_factors": decision_factors,
        "tools_invoked": tools_used,
        "tool_statuses": {
            tool_name: output.get("status")
            for tool_name, output in tool_outputs.items()
            if isinstance(output, dict)
        },
        "retrieved_sources": retrieved_sources,
        "retrieval_status": retrieval_status,
        "rag_enabled": result.get("rag_enabled"),
        "rag_available": result.get("rag_available"),
        "context_in_prompt": context_in_prompt,
        "intent_class": result.get("intent_class"),
        "selected_agent_reason": result.get(
            "selected_agent_reason",
            result.get("fallback_reason"),
        ),
        "tool_selected": result.get("tool_selected"),
        "tool_selected_reason": result.get("tool_selected_reason"),
        "fallback_reason": result.get("fallback_reason"),
        "fallback_stage": result.get("fallback_stage"),
        "retrieval_status_before_fallback": result.get(
            "retrieval_status_before_fallback", retrieval_status
        ),
        "missing_profile_fields": missing_profile_fields,
        "limitations": limitations,
        "next_steps": [
            "Review the recommendation against the original Career question."
        ],
        "confidence_explanation": (
            "No confidence score was reported."
            if result.get("confidence") is None
            else f"The Career agent reported confidence of {result['confidence']}."
        ),
    }
    processing_steps = [
        f"Used {label.lower()} from the query."
        for label in query_facts
    ]
    if processing_steps:
        explanation["processing_steps"] = processing_steps
    confidence_level = result.get("confidence_level")
    if confidence_level not in (None, ""):
        explanation["confidence_level"] = confidence_level
    calculation_steps = {
        tool_name: output["calculation_steps"]
        for tool_name, output in tool_outputs.items()
        if isinstance(output, dict) and output.get("calculation_steps")
    }
    if calculation_steps:
        explanation["calculation_steps"] = calculation_steps
    return explanation


def _extract_career_query_facts(query: str) -> dict[str, str]:
    """Extract explicit Career constraints used by the prompt, not model claims."""
    facts: dict[str, str] = {}
    lowered = query.casefold()
    duration = re.search(r"\b(\d+)\s*-\s*week(?:s)?\b", lowered)
    days = re.search(r"\b(?:next|over the next|within)\s+(\d+)\s+days?\b", lowered)
    daily_time = re.search(
        r"\b(\d+(?:\.\d+)?|one|a)\s*(?:hours?|hrs?)"
        r"(?:\s+of\s+\w+)?\s*(?:per|a)\s*day\b",
        lowered,
    )
    if duration:
        facts["Requested duration"] = f"{duration.group(1)} weeks"
    elif days:
        facts["Requested duration"] = f"{days.group(1)} days"
    if daily_time:
        amount = "1" if daily_time.group(1) in {"one", "a"} else daily_time.group(1)
        unit = "hour" if amount == "1" else "hours"
        facts["Daily study limit"] = f"{amount} {unit} per day"
    if "placement" in lowered:
        facts["Placement goal"] = "software engineering placements"
    language = re.search(
        r"\b(?:learning|learn|using|use)\s+"
        r"(java|python|javascript|typescript|c\+\+|c#|go|rust)\b",
        lowered,
    )
    if language:
        language_name = language.group(1)
        facts["Requested language"] = language_name
    else:
        basic_language = re.search(
            r"\bbasic\s+(java|python|javascript|typescript|c\+\+|c#|go|rust)\b",
            lowered,
        )
        if basic_language:
            facts["Requested language"] = basic_language.group(1)
    return facts


def _execution_reason(result: dict) -> str:
    """Describe observable execution when the model supplied a generic reason."""
    reason = str(result.get("reason") or "")
    generic_reason = "no structured execution metadata was returned"
    if generic_reason not in reason.casefold():
        return reason

    retrieval_status = result.get("retrieval_status", "not_attempted")
    tools_used = result.get("tools_used") or []
    if retrieval_status == "success":
        evidence = "retrieved Career documents"
        if tools_used:
            evidence += " and recorded Career tool execution"
        else:
            evidence += "; no Career tools were executed"
        return f"The answer used {evidence}."
    if tools_used:
        return "The answer used recorded Career tool execution; no retrieval was used."
    if retrieval_status == "empty":
        return "The answer used the Career LLM fallback after retrieval returned no documents."
    if retrieval_status == "failed":
        return "The answer used the Career LLM fallback because Career retrieval failed."
    return "The answer was generated directly by the Career LLM; no tools or retrieval were used."


def _should_retrieve_career_context(query: str) -> bool:
    """Retrieve KB context for planning questions, not standalone concepts."""
    lowered = query.casefold()
    planning_terms = (
        "placement",
        "prepare for",
        "preparation",
        "study plan",
        "daily plan",
        "roadmap",
        "learning plan",
        "coding problems",
        "aptitude",
        "technical interview",
    )
    return any(term in lowered for term in planning_terms)


def _retrieve_career_context(
    query: str,
    rag_enabled: bool | None = None,
) -> dict:
    """Return retrieval evidence without hiding empty or failed execution."""

    use_rag = (
        rag_enabled
        if rag_enabled is not None
        else os.getenv("USE_RAG", "true").strip().lower() == "true"
    )

    if not use_rag:
        try:
            rag_available = importlib.util.find_spec("rag.retriever") is not None
        except ModuleNotFoundError:
            rag_available = False
        return {
            "status": "disabled",
            "rag_enabled": use_rag,
            "rag_available": rag_available,
            "context": "",
            "sources": [],
            "retrieved_sources": [],
        }
    try:
        from rag.retriever import retrieve

        documents = retrieve(query, domain="career", top_k=5) or []
        context_documents = [
            document
            for document in documents
            if isinstance(document, dict)
            and isinstance(document.get("text"), str)
            and document["text"].strip()
        ]
        retrieved_sources = []
        for document in context_documents:
            text = document["text"]
            title_match = re.search(
                r"^\s*DOCUMENT:\s*(.+?)\s*$",
                text,
                re.MULTILINE,
            )
            retrieved_sources.append({
                "doc_title": (
                    title_match.group(1).strip()
                    if title_match
                    else document.get("doc_title") or document.get("source")
                ),
                "chunk_id": document.get("chunk_id"),
                "score": document.get(
                    "relevance_score",
                    document.get("score"),
                ),
            })
        sources = list(dict.fromkeys(
            document.get("source")
            for document in context_documents
            if document.get("source")
        ))
        context = "\n\nRELEVANT CAREER KNOWLEDGE:\n" + "\n\n".join(
            f"[Source: {document.get('source', 'unknown')}]\n"
            f"{document.get('text', '')}"
            for document in context_documents
        )
        return {
            "status": "success" if context_documents else "empty",
            "rag_enabled": use_rag,
            "context": context if context_documents else "",
            "sources": sources,
            "retrieved_sources": retrieved_sources,
            "rag_available": True,
        }
    except (ImportError, ModuleNotFoundError, FileNotFoundError) as exc:
        logger.exception("Career RAG is unavailable: %s", exc)
        return {
            "status": "unavailable",
            "rag_enabled": use_rag,
            "rag_available": False,
            "context": "",
            "sources": [],
            "retrieved_sources": [],
            "error": str(exc),
        }
    except Exception as exc:
        logger.exception("Career RAG retrieval failed: %s", exc)
        return {
            "status": "failed",
            "rag_enabled": use_rag,
            "rag_available": True,
            "context": "",
            "sources": [],
            "retrieved_sources": [],
            "error": str(exc),
        }


def _request_value(request, key: str, default=None):
    if isinstance(request, dict):
        value = request.get(key, default)
    else:
        value = getattr(request, key, default)
    return default if value is None else value


def _set_request_value(request, key: str, value) -> None:
    if isinstance(request, dict):
        request[key] = value
    else:
        setattr(request, key, value)


# ── Run ───────────────────────────────────────────────────────
def run(request, rag_enabled: bool | None = None) -> dict:
    query = _request_value(request, "query", "")
    if rag_enabled is None:
        request_rag_enabled = _request_value(request, "rag_enabled", None)
        rag_enabled = (
            request_rag_enabled
            if isinstance(request_rag_enabled, bool)
            else os.getenv("USE_RAG", "true").strip().lower() == "true"
        )
    intent = _classify_career_intent(
        query,
        _request_value(request, "resume_text", "") or "",
    )
    retrieval = _retrieve_career_context(query, rag_enabled=rag_enabled)
    retrieval.setdefault("rag_enabled", rag_enabled)
    retrieval.setdefault("rag_available", False)
    retrieval.setdefault("retrieved_sources", [
        {
            "doc_title": source,
            "chunk_id": None,
            "score": None,
        }
        for source in retrieval.get("sources", [])
        if isinstance(source, str)
    ])
    retrieval_state = {
        **retrieval,
        "intent_class": intent["intent_class"],
        "tool_selected": intent["tools"] or None,
        "tool_selected_reason": intent["reason"] if intent["tools"] else None,
    }
    _set_request_value(request, "_career_retrieval_state", retrieval_state)

    profile_field_names = {
        "skill_gap_analyzer": ("current_skills", "target_role"),
        "job_search": (
            "current_skills", "target_role", "location", "experience_level",
        ),
        "salary_benchmark": ("target_role", "location", "years_experience"),
        "learning_path_generator": (
            "current_skills", "target_role", "current_level", "timeline_months",
        ),
    }
    included_profile_names = {
        name
        for selected_name in intent["tools"]
        for name in profile_field_names.get(selected_name, ())
    } | set(intent.get("profile_fields", ()))
    profile_lines = []
    profile_labels = (
        ("current_skills", "Current skills"),
        ("target_role", "Target role"),
        ("location", "Location"),
        ("experience_level", "Experience level"),
        ("years_experience", "Years of experience"),
        ("current_level", "Current level"),
        ("timeline_months", "Timeline"),
    )
    profile_values_used = {}
    for name, label in profile_labels:
        if name not in included_profile_names:
            continue
        value = _request_value(request, name, None)
        if value not in (None, "", [], {}):
            profile_lines.append(f"- {label}: {value}")
            profile_values_used[label] = value

    profile_text = "\n".join(profile_lines) or (
        "- No stored profile values included for this knowledge-only query"
    )
    selected_tools_text = ", ".join(intent["tools"]) or "None"
    user_input = f"""Answer this query directly:
{query}

Intent classification: {intent["intent_class"]}
Selected tools: {selected_tools_text}
Do not call tools other than the selected tools above.

Validated profile values, to use only when relevant:
{profile_text}

Use a career tool only when the query requires it. For a daily schedule,
use the explicit duration and daily time in the query rather than a default
timeline.

Relevant career context:
{retrieval["context"]}"""

    try:
        fallback_stage = "invoke"
        if intent["tools"]:
            with use_career_rag_context(retrieval["context"]):
                result = career_agent.invoke({
                    "messages": [{"role": "user", "content": user_input}]
                })
        else:
            result = {
                "messages": [
                    llm.invoke([
                        ("system", SYSTEM_PROMPT),
                        ("user", user_input),
                    ])
                ]
            }

        fallback_stage = "message_parse"
        # Get last message content
        last_msg = result["messages"][-1].content
        if isinstance(last_msg, list):
            last_msg = "".join(
                item.get("text", "") if isinstance(item, dict) else str(item)
                for item in last_msg
            )
        last_msg = str(last_msg)

        fallback_stage = "json_parse"
        # Extract JSON
        match = re.search(r'\{[^{}]*"recommendation"[^{}]*\}', last_msg, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
        else:
            parsed = {
                "recommendation": last_msg,
                "reason": (
                    "The answer was generated directly by the Career LLM; "
                    "no structured execution metadata was returned."
                ),
            }
        # The model has no calibrated basis for a numeric confidence score.
        parsed.pop("confidence", None)

        fallback_stage = "tool_processing"
        tool_messages = [
            message for message in result.get("messages", [])
            if getattr(message, "type", "") == "tool"
        ]
        tools_used = list(dict.fromkeys(
            getattr(message, "name", None)
            for message in tool_messages
            if getattr(message, "name", None)
        ))
        tool_outputs = {}
        sources = []
        for message in tool_messages:
            tool_name = getattr(message, "name", "unknown")
            status = getattr(message, "status", None) or "completed"
            content = getattr(message, "content", "")
            if isinstance(content, dict) and content.get("error"):
                status = "failed"
            if isinstance(content, dict):
                message_sources = content.get("sources", content.get("source", []))
                if isinstance(message_sources, str):
                    message_sources = [message_sources]
                if isinstance(message_sources, list):
                    sources.extend(
                        source for source in message_sources if isinstance(source, str)
                    )
            tool_outputs[tool_name] = {
                "status": status,
                "output": content,
            }

        fallback_stage = "response_build"
        response_sources = list(dict.fromkeys(
            [*retrieval["sources"], *sources]
        ))
        response = {
            "domain":      "career",
            "agent_type":  "langchain",
            "tools_used":  tools_used,
            "tool_outputs": tool_outputs,
            "sources": response_sources,
            "retrieval_status": retrieval["status"],
            "retrieval_error": retrieval.get("error"),
            "retrieved_sources": retrieval["retrieved_sources"],
            "rag_available": retrieval["rag_available"],
            "context_in_prompt": bool(retrieval["context"]),
            "intent_class": intent["intent_class"],
            "selected_agent_reason": (
                "The LangChain Career agent completed the request."
            ),
            "tool_selected": intent["tools"] or None,
            "tool_selected_reason": (
                intent["reason"] if intent["tools"] else None
            ),
            "profile_values_used": profile_values_used,
            "fallback_reason": None,
            "fallback_stage": None,
            "rag_enabled": retrieval["rag_enabled"],
            "retrieval_status_before_fallback": retrieval["status"],
            **parsed
        }
        response["reason"] = _execution_reason(response)
        fallback_stage = "explainability"
        response["explainability"] = _build_career_explainability(
            request, response
        )
        return response

    except Exception as e:
        print(f"[LangChain Career] Error: {e} — falling back")
        logger.exception(
            "Career LangChain fallback at %s: %s: %s",
            fallback_stage,
            type(e).__name__,
            str(e),
        )
        import agents.career_agent as original
        result = original.run(
            request,
            rag_context=retrieval["context"],
            rag_enabled=retrieval["rag_enabled"],
        )
        fallback_reason = f"{type(e).__name__}: {str(e)[:300]}"
        result["agent_type"] = "fallback"
        result["fallback_reason"] = fallback_reason
        result["fallback_stage"] = fallback_stage
        result["selected_agent_reason"] = (
            f"Fallback was used after {fallback_stage}: {fallback_reason}"
        )
        result["rag_enabled"] = retrieval["rag_enabled"]
        result["retrieval_status_before_fallback"] = retrieval["status"]
        result["retrieval_status"] = retrieval["status"]
        result["retrieved_sources"] = retrieval["retrieved_sources"]
        result["rag_available"] = retrieval["rag_available"]
        result["context_in_prompt"] = bool(retrieval["context"])
        result["intent_class"] = intent["intent_class"]
        result["tool_selected"] = intent["tools"] or None
        result["tool_selected_reason"] = (
            intent["reason"] if intent["tools"] else None
        )
        result["profile_values_used"] = result.get(
            "profile_values_used",
            profile_values_used,
        )
        if retrieval.get("error"):
            result.setdefault("retrieval_error", retrieval["error"])
        result["explainability"] = _build_career_explainability(
            request, result
        )
        return result