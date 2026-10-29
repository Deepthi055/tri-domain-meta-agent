from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
from functools import lru_cache
from pathlib import Path
from typing import Any
from core.career_rag_context import get_active_career_rag_context

import requests
from dotenv import load_dotenv

try:
    from sentence_transformers import SentenceTransformer, util
except ImportError:
    SentenceTransformer = None
    util = None

logger = logging.getLogger(__name__)

_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(_ENV_FILE, override=True)
 
from tools.job_preprocessor import prepare_jobs_for_ranking
 

# =========================================================
# CONFIGURATION
# =========================================================

EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL",
    "all-MiniLM-L6-v2",
)

JSEARCH_URL = "https://jsearch.p.rapidapi.com/search-v2"
JSEARCH_HOST = "jsearch.p.rapidapi.com"

JSEARCH_CACHE_DIR = Path(os.getenv("JSEARCH_CACHE_DIR", ".cache/jsearch"))
JSEARCH_CACHE_TTL_SECONDS = int(os.getenv("JSEARCH_CACHE_TTL_SECONDS", "21600"))  # 6h default


def _rag_enabled() -> bool:
    return os.getenv("USE_RAG", "true").strip().lower() == "true"


# =========================================================
# EMBEDDING MODEL
# =========================================================

def get_embedding_model() -> SentenceTransformer | None:
    """
    Load the embedding model once and reuse it via the shared singleton.
    Returns None if loading fails.
    """
    try:
        from core.embeddings import get_shared_embedding_model

        return get_shared_embedding_model(EMBEDDING_MODEL_NAME)

    except Exception:
        logger.exception(
            "Unable to load embedding model: %s",
            EMBEDDING_MODEL_NAME,
        )
        return None


# =========================================================
# BASIC TEXT UTILITIES
# =========================================================

def _normalize_skill_name(value: Any) -> str:
    """
    Light text normalization.

    This function does not map specific skills to a fixed list.
    It only normalizes whitespace, case, and punctuation.
    """
    if value is None:
        return ""

    text = str(value).strip().lower()

    text = re.sub(r"[\u2012\u2013\u2014\u2212]", "-", text)
    text = re.sub(r"[^\w\s+/#.&-]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip(" -.,;:")


# FIX: _normalize_text was called throughout the file (in _role_matches_text
# and _job_identity) but never defined anywhere, which raised NameError at
# runtime the moment either function ran. It does the same normalization job
# as _normalize_skill_name, so it's aliased here rather than duplicated.
_normalize_text = _normalize_skill_name


def _as_text(value: Any) -> str:
    """Convert API/LLM values into readable text."""
    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    if isinstance(value, (list, tuple, set)):
        return ", ".join(
            str(item).strip()
            for item in value
            if str(item).strip()
        )

    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)

    return str(value)


def _unique_strings(values: list[Any]) -> list[str]:
    """Normalize strings and remove duplicates without hardcoded vocabularies."""
    result: list[str] = []

    for value in values:
        if not isinstance(value, str):
            continue

        normalized = _normalize_skill_name(value)

        if normalized and normalized not in result:
            result.append(normalized)

    return result


# =========================================================
# REQUIRED-SKILL COERCION
# =========================================================

def _coerce_required_skills(value: object) -> list[str]:
    """
    Convert an LLM/API skill response into a normalized list.

    No role-specific skill dictionary is used.
    """
    if value is None:
        return []

    if isinstance(value, str):
        candidates = re.split(r"[,;\n]+", value)

    elif isinstance(value, (list, tuple, set)):
        candidates = list(value)

    elif isinstance(value, dict):
        preferred_keys = (
            "required_skills",
            "skills",
            "core_skills",
            "essential_skills",
            "technical_skills",
        )

        for key in preferred_keys:
            if key in value:
                return _coerce_required_skills(value[key])

        candidates = []

        for nested in value.values():
            if isinstance(nested, (list, tuple, set, str, dict)):
                candidates.extend(
                    _coerce_required_skills(nested)
                )

    else:
        return []

    parsed: list[str] = []

    for item in candidates:

        if isinstance(item, dict):
            for key in ("skill", "name", "title", "value"):
                if isinstance(item.get(key), str):
                    normalized = _normalize_skill_name(item[key])

                    if normalized and normalized not in parsed:
                        parsed.append(normalized)

                    break

            continue

        if not isinstance(item, str):
            continue

        for raw_skill in re.split(r"[\n,;]+", item):
            normalized = _normalize_skill_name(raw_skill)

            if normalized and normalized not in parsed:
                parsed.append(normalized)

    return parsed


# =========================================================
# RAG ROLE RELEVANCE
# =========================================================

def _role_matches_text(text: str, role: str) -> bool:
    text_normalized = _normalize_text(text)
    role_normalized = _normalize_text(role)

    if not text_normalized or not role_normalized:
        return False

    role_tokens = role_normalized.split()

    if len(role_tokens) == 1 and len(role_tokens[0]) <= 3:
        return re.search(
            rf"\b{re.escape(role_tokens[0])}\b",
            text_normalized,
        ) is not None

    meaningful_tokens = [
        token for token in role_tokens
        if len(token) >= 3
    ]

    if not meaningful_tokens:
        return role_normalized in text_normalized

    return all(
        token in text_normalized
        for token in meaningful_tokens
    )


def _clean_skill_candidate(candidate: str) -> str:
    """Clean an extracted skill without applying role-specific mappings."""
    if not candidate:
        return ""

    candidate = candidate.strip()

    candidate = re.sub(
        r"^(experience\s+with|proficiency\s+in|knowledge\s+of|"
        r"strong\s+understanding\s+of|familiarity\s+with|"
        r"expertise\s+in|skills?\s+in|ability\s+to\s+use)\s+",
        "",
        candidate,
        flags=re.IGNORECASE,
    )

    candidate = re.split(
        r"\s+[—–-]\s+(?:required|preferred|important|"
        r"recommended|valued|useful|needed)",
        candidate,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]

    candidate = re.split(
        r"\s*—?\s*required\s+by\s+\d+%",
        candidate,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]

    return candidate.strip(" .:-")





def _extract_skills_from_career_knowledge(
    knowledge_text: str,
    target_role: str,
) -> list[str]:
    """
    Extract role-specific skills from career knowledge.

    Only blocks whose ROLE field matches the requested target role
    are considered. If no matching role is found in career_kb.txt,
    this returns an empty list.
    """

    if not knowledge_text or not target_role:
        return []

    target_role_normalized = target_role.strip().lower()

    blocks = re.split(
        r"\n\s*---\s*\n",
        knowledge_text,
    )

    exact_role_blocks: list[str] = []
    related_role_blocks: list[str] = []

    for block in blocks:
        block = block.strip()

        if not block:
            continue

        role_match = re.search(
            r"(?im)^\s*ROLE\s*:\s*(.+?)\s*$",
            block,
        )

        if not role_match:
            continue

        block_role = role_match.group(1).strip().lower()

        if block_role == target_role_normalized:
            exact_role_blocks.append(block)

        elif (
            target_role_normalized in block_role
            or block_role in target_role_normalized
        ):
            related_role_blocks.append(block)

    if exact_role_blocks:
        selected_blocks = exact_role_blocks

    elif related_role_blocks:
        selected_blocks = related_role_blocks

    else:
        return []

    selected_text = "\n".join(selected_blocks)

    candidates: list[str] = []

    # Numbered lists:
    # 1. SQL
    # 2. Python
    candidates.extend(
        re.findall(
            r"(?m)^\s*\d+[.)]\s*(.+?)\s*$",
            selected_text,
        )
    )

    # Bullet lists:
    # - SQL
    # - Python
    candidates.extend(
        re.findall(
            r"(?m)^\s*[-*•]\s*(.+?)\s*$",
            selected_text,
        )
    )

    parsed: list[str] = []

    for candidate in candidates:
        cleaned = _clean_skill_candidate(candidate)

        if not cleaned:
            continue

        skill = _normalize_skill_name(cleaned)

        if skill and skill not in parsed:
            parsed.append(skill)

    return parsed[:20]


# =========================================================
# LLM ACCESS
# =========================================================

def _call_llm(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 1200,
) -> dict:
    from core.llm_client import call_llm

    return call_llm(
        system_prompt,
        user_prompt,
        temperature=temperature,
    )


# =========================================================
# REQUIRED-SKILL EXTRACTION FROM TEXT
# =========================================================

def _extract_skills_with_llm(
    target_role: str,
    source_text: str = "",
    resume_text: str | None = None,
) -> list[str]:
    """
    Ask the LLM to infer the required skills for a target role.

    The fallback should not receive KB text as input; the model itself
    should infer the role requirements from the target role name.
    """
    if not target_role or not str(target_role).strip():
        return []

    schema = '{"required_skills": ["skill1", "skill2", "skill3"]}'

    prompt_template = (
        "Extract the technical and professional skills required for the target role.\n\n"
        f"Target role:\n{target_role}\n\n"
        "Return ONLY valid JSON in this exact format and nothing else:\n"
        f"{schema}\n\n"
        "Critical output rules:\n"
        '- The JSON must contain exactly one top-level key: "required_skills".\n'
        '- "required_skills" must be a JSON array of short strings.\n'
        '- Do not output any other top-level keys such as "summary", "recommendation", or "error".\n'
        '- Do not include explanations, markdown, comments, or whitespace outside JSON.\n'
        '- If the role is missing or no skills can be confidently extracted, return '
        '{"required_skills": []}\n'
    )

    for attempt in range(2):
        result = _call_llm(
            system_prompt=(
                "You are a strict JSON extraction assistant. "
                "Your response must be valid JSON with a top-level "
                "required_skills array only."
            ),
            user_prompt=prompt_template,
            temperature=0.0,
            max_tokens=500,
        )

        if isinstance(result, dict):
            required_skills = result.get("required_skills", [])

            if isinstance(required_skills, list):
                normalized = [
                    str(skill).strip()
                    for skill in required_skills
                    if str(skill).strip()
                ]

                if normalized:
                    return normalized

        if attempt == 0:
            prompt_template = (
                "You are a strict extractor.\n\n"
                "Extract only the required skills for this target role.\n\n"
                f"Target role:\n{target_role}\n\n"
                "Return EXACTLY this JSON structure:\n"
                f"{schema}\n\n"
                "Rules:\n"
                '- Output only JSON.\n'
                '- required_skills must be a list of strings.\n'
                '- Do not include summary, explanation, markdown, or additional fields.\n'
                '- Use empty array [] if nothing can be confidently derived.\n'
            )

    return []


# =========================================================
# EMBEDDING HELPERS
# =========================================================

def _encode_texts(texts: list[str]):
    """Encode texts into normalized embeddings."""
    model = get_embedding_model()
    if model is None:
        raise RuntimeError(f"Embedding model '{EMBEDDING_MODEL_NAME}' is unavailable")

    return model.encode(
        texts,
        convert_to_tensor=True,
        normalize_embeddings=True,
    )


def calculate_embedding_similarity(
    text_a: str,
    text_b: str,
) -> float:
    """
    Return cosine similarity as a 0-100 semantic similarity score.
    """
    if not text_a.strip() or not text_b.strip():
        return 0.0

    embeddings = _encode_texts(
        [
            text_a,
            text_b,
        ]
    )

    similarity = util.cos_sim(
        embeddings[0],
        embeddings[1],
    ).item()

    score = max(0.0, min(100.0, ((similarity + 1.0) / 2.0) * 100.0))

    return round(score, 1)


def _best_skill_matches(
    current_skills: list[str],
    required_skills: list[str],
    similarity_threshold: float,
) -> tuple[list[dict], list[str]]:
    """
    Match each required skill to the most semantically similar
    current skill.

    If semantic embeddings are unavailable, gracefully fall back to
    treating every required skill as missing rather than crashing the
    entire analyzer.
    """
    if not current_skills or not required_skills:
        return [], list(required_skills)

    current = _unique_strings(current_skills)
    required = _unique_strings(required_skills)

    try:
        current_embeddings = _encode_texts(current)
        required_embeddings = _encode_texts(required)

        similarity_matrix = util.cos_sim(
            required_embeddings,
            current_embeddings,
        )

    except Exception:
        return [], list(required)

    matched: list[dict] = []
    missing: list[str] = []

    for required_index, required_skill in enumerate(required):

        row = similarity_matrix[required_index]

        best_index = int(row.argmax().item())
        best_similarity = float(row[best_index].item())

        if best_similarity >= similarity_threshold:

            matched.append(
                {
                    "required_skill": required_skill,
                    "matched_with": current[best_index],
                    "similarity": round(best_similarity, 3),
                }
            )

        else:
            missing.append(required_skill)

    return matched, missing


# =========================================================
# SKILL GAP ANALYZER
# =========================================================

def skill_gap_analyzer(
    current_skills: list,
    target_role: str,
    similarity_threshold: float = 0.65,
    rag_context: str | None = None,
) -> dict:
    """
    Determine the user's skill gaps for a target role.

    Required skills are dynamically obtained from:
    1. Career RAG knowledge
    2. Local career knowledge base
    3. Grounded LLM extraction as a fallback

    Current-vs-required matching uses embeddings.
    """
    if target_role is None or not str(target_role).strip():
        return {
            "error": (
                "Please provide or clarify the target role "
                "before assessing career skills."
            )
        }

    role = " ".join(
        str(target_role).strip().lower().split()
    )

    current = _unique_strings(
        current_skills or []
    )

    if not current:
        return {
            "error": (
                "Please add at least one current skill "
                "before assessing a target role."
            )
        }

    knowledge_text = ""

    # -----------------------------------------------------
    # RAG / KB load may fail or be slow. Keep the analyzer
    # resilient by falling back to an empty knowledge set and
    # allowing later graceful handling below.
    # -----------------------------------------------------

    # -----------------------------------------------------
    # RAG
    # -----------------------------------------------------
    if rag_context is None:
        rag_context = get_active_career_rag_context()

    if rag_context is not None:
        knowledge_text = rag_context
    elif _rag_enabled():
        try:
            from rag.retriever import retrieve_as_context

            knowledge_text = retrieve_as_context(
                (
                    "required skills, competencies, qualifications, "
                    f"tools and technologies for the {role} role. "
                    f"Only return career knowledge specifically "
                    f"relevant to the {role} role."
                ),
                domain="career",
                top_k=8,
            ) or ""

        except Exception:
            knowledge_text = ""

    # -----------------------------------------------------
    # LOCAL KB FALLBACK
    # -----------------------------------------------------
    if not knowledge_text:

        try:
            kb_path = (
                Path(__file__).resolve().parent.parent
                / "rag"
                / "knowledge_base"
                / "career_kb.txt"
            )

            knowledge_text = kb_path.read_text(
                encoding="utf-8"
            )

        except Exception:
            knowledge_text = ""

    # -----------------------------------------------------
    # EXTRACT REQUIRED SKILLS
    # -----------------------------------------------------
    required_skills = _extract_skills_from_career_knowledge(
        knowledge_text,
        target_role=target_role,
    )

    # -----------------------------------------------------
    # LLM FALLBACK
    # -----------------------------------------------------
    if not required_skills:
        required_skills = _extract_skills_with_llm(
            target_role=role,
        )

    if not required_skills:
        return {
            "error": (
                f"I couldn't reliably determine the required "
                f"skills for '{target_role}'."
            ),
            "target_role": role,
            "current_skills": current,
        }

    # -----------------------------------------------------
    # EMBEDDING-BASED SKILL MATCHING
    # -----------------------------------------------------
    skill_matches, missing_skills = _best_skill_matches(
        current_skills=current,
        required_skills=required_skills,
        similarity_threshold=similarity_threshold,
    )

    matched_skills = [
        item["required_skill"]
        for item in skill_matches
    ]

    total_required = len(
        _unique_strings(required_skills)
    )

    match_percentage = (
        round(
            (len(matched_skills) / total_required) * 100,
            1,
        )
        if total_required
        else 0.0
    )

    return {
        "target_role": role,
        "current_skills": current,
        "required_skills": _unique_strings(required_skills),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "total_required_skills": total_required,
        "match_percentage": match_percentage,
        "skill_matches": skill_matches,
        "similarity_threshold": similarity_threshold,
    }

# =========================================================
# LEARNING PATH GENERATOR
# =========================================================

LEARNING_PATH_SCHEMA = (
    '{"phases": [{"phase": 1, "focus": "string", '
    '"topics": ["string"], "resources": ["string"], '
    '"duration_weeks": 4}]}'
)


def _build_learning_path_prompt(
    target_role: str,
    current_level: str,
    timeline_months: int,
    missing_skills: list[str],
    grounding_context: str = "",
) -> str:
    """
    Build the prompt used to shape a learning path — whether the
    grounding_context came from RAG, the local KB, or is empty
    (pure LLM generation).
    """
    skills_text = _as_text(missing_skills) or "not specified"

    context_block = (
        f"\nReference context (use if relevant, ignore if not):\n{grounding_context[:2000]}\n"
        if grounding_context
        else ""
    )

    return f"""
Create a realistic, phased learning roadmap for someone moving toward
the target role below.

Target role: {target_role}
Current level: {current_level}
Timeline: {timeline_months} months
Skills they are currently missing: {skills_text}
{context_block}
Rules:
- Prioritize phases around the missing skills listed above, in a sensible learning order.
- Each phase needs: phase number, a short focus title, 2-5 topics, 1-3 resources (real, well-known, prefer free ones), and a realistic duration_weeks.
- Keep the whole plan realistic for the given timeline.
- Return ONLY valid JSON, no markdown, no extra text.

Return exactly this structure:
{LEARNING_PATH_SCHEMA}
""".strip()


def learning_path_generator(
    target_role: str,
    current_level: str,
    timeline_months: int,
    missing_skills: list[str] | None = None,
    rag_context: str | None = None,
) -> dict:
    """
    Generate a phased learning roadmap for any target role.

    No hardcoded role dictionary. Follows the same RAG -> local KB ->
    LLM fallback chain as skill_gap_analyzer(), and never silently
    substitutes a different role's data - if nothing usable can be
    generated, returns an explicit error instead.
    """
    if not target_role or not str(target_role).strip():
        return {
            "error": "Please provide a target role before generating a learning path."
        }

    role = " ".join(str(target_role).strip().lower().split())
    missing_skills = missing_skills or []
    source = None
    grounding_context = (
        rag_context
        if rag_context is not None
        else get_active_career_rag_context() or ""
    )

    # -----------------------------------------------------
    # 1. Try RAG
    # -----------------------------------------------------
    if not grounding_context and get_active_career_rag_context() is None and rag_context is None and _rag_enabled():
        try:
            from rag.retriever import retrieve_as_context

            grounding_context = retrieve_as_context(
                f"learning roadmap, skill-building order, courses and resources for becoming a {role}",
                domain="career",
                top_k=8,
            ) or ""

            if grounding_context:
                source = "rag"

        except Exception:
            grounding_context = ""

    # -----------------------------------------------------
    # 2. Local KB fallback
    # -----------------------------------------------------
    if not grounding_context:
        try:
            kb_path = (
                Path(__file__).resolve().parent.parent
                / "rag"
                / "knowledge_base"
                / "career_kb.txt"
            )
            knowledge_text = kb_path.read_text(encoding="utf-8")

            extracted = _extract_skills_from_career_knowledge(
                knowledge_text,
                target_role=role,
            )

            if extracted:
                grounding_context = (
                    f"Known relevant skills/topics for {role}: {_as_text(extracted)}"
                )
                source = "local_kb"

        except Exception:
            grounding_context = ""

    # -----------------------------------------------------
    # 3. LLM shaping (runs in every branch — RAG/KB context,
    #    if any, is passed in as grounding; empty otherwise)
    # -----------------------------------------------------
    if source is None:
        source = "llm_estimate"

    prompt = _build_learning_path_prompt(
        target_role=role,
        current_level=current_level,
        timeline_months=timeline_months,
        missing_skills=missing_skills,
        grounding_context=grounding_context,
    )

    llm_result = _call_llm(
        system_prompt=(
            "You are a strict JSON-generating career learning-path planner. "
            "Respond with valid JSON only, matching the exact requested schema."
        ),
        user_prompt=prompt,
        temperature=0.3,
        max_tokens=1200,
    )

    phases = llm_result.get("phases") if isinstance(llm_result, dict) else None

    if not phases or not isinstance(phases, list):
        return {
            "error": (
                f"I couldn't generate a reliable learning path for '{target_role}'."
            ),
            "target_role": role,
        }

    total_weeks = sum(
        int(p.get("duration_weeks", 0)) for p in phases if isinstance(p, dict)
    )
    available_weeks = timeline_months * 4
    feasible = available_weeks >= total_weeks
    weekly_hours = (
        round((total_weeks * 10) / available_weeks, 1)
        if available_weeks > 0
        else 0
    )

    return {
        "target_role": role,
        "current_level": current_level,
        "timeline_months": timeline_months,
        "phases": phases,
        "total_weeks_required": total_weeks,
        "feasible": feasible,
        "weekly_hours_needed": weekly_hours,
        "advice": (
            "Your timeline is achievable. Stay consistent."
            if feasible
            else f"Timeline is tight. You need ~{weekly_hours} hrs/week, or consider extending to {round(total_weeks / 4)} months."
        ),
        "source": source,
    }
# =========================================================
# JOB API
# =========================================================

def _get_jsearch_headers() -> dict[str, str]:
    """
    Build JSearch request headers from environment variables.

    Standardized on RAPIDAPI_KEY across the whole project (this is the
    account-level key from RapidAPI, not JSearch-specific - the same
    variable name is used in job_recommendation_tool.py).
    """
    api_key = os.getenv("RAPIDAPI_KEY")

    if not api_key:
        raise RuntimeError(
            "RAPIDAPI_KEY is not configured."
        )

    return {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": JSEARCH_HOST,
    }


def _normalize_job(raw_job: dict) -> dict:
    required_experience = raw_job.get("job_required_experience") or {}

    city = str(raw_job.get("job_city") or "").strip()
    state = str(raw_job.get("job_state") or "").strip()
    country = str(raw_job.get("job_country") or "").strip()

    location = ", ".join(
        part for part in (city, state, country)
        if part
    )

    experience_months = required_experience.get(
        "required_experience_in_months"
    )
    no_experience_required = required_experience.get(
        "no_experience_required"
    )

    if no_experience_required is True:
        experience_level = "entry"
    elif isinstance(experience_months, (int, float)):
        if experience_months < 24:
            experience_level = "entry"
        elif experience_months < 60:
            experience_level = "mid"
        else:
            experience_level = "senior"
    else:
        experience_level = ""

    required_skills = raw_job.get("job_required_skills") or []
    if isinstance(required_skills, str):
        required_skills = [required_skills]

    return {
        "id": raw_job.get("job_id", ""),
        "title": raw_job.get("job_title", ""),
        "company": raw_job.get("employer_name", ""),
        "location": location,
        "city": city,
        "state": state,
        "country": country,
        "description": raw_job.get("job_description", ""),
        "required_skills": required_skills,
        "experience_level": experience_level,
        "required_experience_months": experience_months,
        "no_experience_required": no_experience_required,
        "employment_type": raw_job.get("job_employment_type", ""),
        "is_remote": bool(raw_job.get("job_is_remote", False)),
        "apply_link": (
            raw_job.get("job_apply_link")
            or raw_job.get("job_google_link")
            or ""
        ),
        "publisher": raw_job.get("job_publisher", ""),
        "posted_at": raw_job.get("job_posted_at_datetime_utc", ""),
    }


def _build_job_query(
    target_role: str,
    location: str = "",
    experience_level: str = "",
) -> str:
    """Build a dynamic search query from the user's request."""
    parts = [target_role.strip()]

    if location.strip():
        parts.append(location.strip())

    if experience_level.strip():
        parts.append(experience_level.strip())

    return " ".join(
        part
        for part in parts
        if part
    )


def _build_embedding_job_text(job: dict) -> str:
    """Create rich natural-language text for job embeddings."""
    return f"""
Job title: {_as_text(job.get("title"))}
Company: {_as_text(job.get("company"))}
Location: {_as_text(job.get("location"))}
Required skills: {_as_text(job.get("required_skills"))}
Experience: {_as_text(job.get("experience_level"))}
Employment type: {_as_text(job.get("employment_type"))}
Remote: {_as_text(job.get("is_remote"))}
Description: {_as_text(job.get("description"))}
""".strip()


def build_user_profile_text(
    target_role: str,
    skills: list[str],
    experience_level: str = "",
    location: str = "",
) -> str:
    """Build semantic text representing the user's job preferences."""
    return f"""
Target role: {_as_text(target_role)}
Current skills: {_as_text(skills)}
Experience level: {_as_text(experience_level)}
Preferred location: {_as_text(location)}
""".strip()


def rank_jobs(
    jobs: list[dict],
    target_role: str,
    skills: list[str],
    experience_level: str = "",
    location: str = "",
) -> list[dict]:
    """
    Rank jobs using semantic embedding similarity only.

    There is no manually assigned role/skill/location/experience weight.
    """
    if not jobs:
        return []

    user_text = build_user_profile_text(
        target_role=target_role,
        skills=skills,
        experience_level=experience_level,
        location=location,
    )

    job_texts = [
        _build_embedding_job_text(job)
        for job in jobs
    ]

    user_embedding = _encode_texts([user_text])[0]
    job_embeddings = _encode_texts(job_texts)

    similarities = util.cos_sim(
        user_embedding,
        job_embeddings,
    )[0]

    ranked_jobs: list[dict] = []

    for index, job in enumerate(jobs):
        similarity = float(
            similarities[index].item()
        )

        score = round(
            max(
                0.0,
                min(
                    100.0,
                    ((similarity + 1.0) / 2.0) * 100.0,
                ),
            ),
            1,
        )

        ranked_jobs.append(
            {
                **job,
                "embedding_match_score": score,
            }
        )

    ranked_jobs.sort(
        key=lambda item: item["embedding_match_score"],
        reverse=True,
    )

    return ranked_jobs


# =========================================================
# JSEARCH RESPONSE CACHE
# =========================================================

def _cache_key(query: str, page: int, num_pages: int) -> str:
    raw_key = f"{query}|{page}|{num_pages}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def _get_cached_response(
    query: str,
    page: int,
    num_pages: int,
) -> dict | None:
    cache_file = (
        JSEARCH_CACHE_DIR
        / f"{_cache_key(query, page, num_pages)}.json"
    )

    if not cache_file.exists():
        return None

    if time.time() - cache_file.stat().st_mtime > JSEARCH_CACHE_TTL_SECONDS:
        return None

    try:
        return json.loads(cache_file.read_text(encoding="utf-8"))
    except Exception:
        return None


def _save_cached_response(
    query: str,
    page: int,
    num_pages: int,
    response_data: dict,
) -> None:
    JSEARCH_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    cache_file = (
        JSEARCH_CACHE_DIR
        / f"{_cache_key(query, page, num_pages)}.json"
    )

    cache_file.write_text(
        json.dumps(response_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def job_search(
    target_role: str,
    skills: list,
    location: str,
    experience_level: str,
    page: int = 1,
    num_pages: int = 1,
) -> dict:
    """
    Search live job listings using JSearch and rank them semantically.
 
    No hardcoded job database or role-specific skill list is used.
 
    NOTE (country): intentionally scoped to India ("in") only, by design -
    this project only serves India-region job search. If you later need
    other regions, reintroduce an optional `country` parameter instead of
    hardcoding a different single value here.
 
    FIX (caching): the module previously defined cache helpers
    (_get_cached_response / _save_cached_response) but never called them,
    so every search still hit the live API. Caching is now actually wired
    in here, keyed on (query, page, num_pages), respecting
    JSEARCH_CACHE_TTL_SECONDS. This matters a lot on JSearch's free tier
    (200 requests/month).
 
    NOTE (skills): per-job LLM skill extraction was removed. JSearch's
    job_required_skills field is frequently null, and extracting it via
    LLM for every job (even capped) burned calls on jobs that often didn't
    make the final top-10 anyway. The full job description is already
    part of each job's embedding text (see _build_embedding_job_text), so
    ranking quality against the user's skills doesn't depend on a
    populated required_skills list - it may just come back as [] for jobs
    JSearch didn't tag. LLM-based skill extraction is still used, but only
    at the role level, in skill_gap_analyzer() and resume_optimizer().
 
    NOTE (dedup + filtering): normalized jobs are now deduplicated and
    hard-filtered (experience level, location) by
    services.job_preprocessor.prepare_jobs_for_ranking(), which does
    fuzzy title matching, India-city alias normalization (Bangalore ->
    Bengaluru, etc.), and keeps the most complete/recent duplicate. This
    replaces the simpler exact-match dedup that used to live in this file
    (_job_identity / _deduplicate_jobs, both removed) and adds a
    profile-filter step this file never had.
    """
    if not target_role or not str(target_role).strip():
        return {
            "error": "Target role is required.",
            "jobs": [],
            "total_matches": 0,
        }
 
    query = _build_job_query(
        target_role=target_role,
        location=location or "",
        experience_level=experience_level or "",
    )
 
    try:
        payload = _get_cached_response(query, page, num_pages)
        from_cache = payload is not None
 
        if payload is None:
            params = {
                "query": query,
                "page": page,
                "num_pages": num_pages,
                "date_posted": "all",
                "country": "in",
            }
 
            response = requests.get(
                JSEARCH_URL,
                headers=_get_jsearch_headers(),
                params=params,
                timeout=30,
            )
 
            response.raise_for_status()
            payload = response.json()
 
            _save_cached_response(query, page, num_pages, payload)
 
        raw_jobs = payload.get("data", [])
        # FIX: /search-v2 changed response shape vs the old /search endpoint.
        # v1 returned `data` as a plain list of job objects directly.
        # v2 returns `data` as an object containing a `jobs` array instead,
        # e.g. {"data": {"jobs": [...]}} rather than {"data": [...]}.
        # Without this, `raw_jobs` was a dict and iterating over it yielded
        # its keys (just the string "jobs"), silently producing zero
        # normalized jobs with no error - exactly the "0 results, no
        # exception" symptom this fixes.
        if isinstance(raw_jobs, dict):
            raw_jobs = raw_jobs.get("jobs", [])
 
        normalized_jobs = [
            _normalize_job(job)
            for job in raw_jobs
            if isinstance(job, dict)
        ]
 
        jobs = prepare_jobs_for_ranking(
            normalized_jobs,
            profile={
                "target_role": target_role,
                "skills": skills or [],
                "experience": experience_level or "",
                "location": location or "",
            },
        )
 
        ranked_jobs = rank_jobs(
            jobs=jobs,
            target_role=target_role,
            skills=skills or [],
            experience_level=experience_level or "",
            location=location or "",
        )
 
        return {
            "target_role": target_role,
            "location_searched": location,
            "experience_level": experience_level,
            "total_matches": len(ranked_jobs),
            "jobs": ranked_jobs[:10],
            "from_cache": from_cache,
        }
 
    except requests.RequestException as exc:
 
        return {
            "error": f"Job search request failed: {exc}",
            "target_role": target_role,
            "location_searched": location,
            "experience_level": experience_level,
            "total_matches": 0,
            "jobs": [],
        }
 
    except Exception as exc:
 
        return {
            "error": f"Job search failed: {exc}",
            "target_role": target_role,
            "location_searched": location,
            "experience_level": experience_level,
            "total_matches": 0,
            "jobs": [],
        }
 


# =========================================================
# RESUME ANALYZER
# =========================================================

def _resume_structure_checks(resume_text: str) -> dict[str, bool]:
    """
    Describe common resume sections.

    These checks are informational only and are NOT used as
    manually weighted ATS scoring factors.
    """
    text = resume_text.lower()

    return {
        "has_email": bool(
            re.search(
                r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}",
                resume_text,
                flags=re.IGNORECASE,
            )
        ),
        "has_linkedin": "linkedin" in text,
        "has_github": "github" in text,
        "has_experience_section": bool(
            re.search(r"\bexperience\b", text)
        ),
        "has_education_section": bool(
            re.search(r"\beducation\b", text)
        ),
        "has_projects_section": bool(
            re.search(r"\bprojects?\b", text)
        ),
        "has_skills_section": bool(
            re.search(r"\bskills?\b", text)
        ),
    }


def _resume_text_for_embedding(
    resume_text: str,
) -> str:
    """
    Lightly clean resume text while preserving semantic content.
    """
    text = resume_text.strip()

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text


def resume_optimizer(
    resume_text: str,
    target_job: str,
    rag_context: str | None = None,
) -> dict:
    """
    Analyze a resume semantically against the requested target role.

    Required skills are obtained dynamically rather than from a
    hardcoded ATS keyword dictionary.

    The ATS-style score is the semantic similarity between the
    resume and dynamically retrieved role requirements. Structure
    checks are reported separately and do not alter the score.
    """
    if not resume_text or not resume_text.strip():
        return {
            "error": "Resume text is required."
        }

    if not target_job or not target_job.strip():
        return {
            "error": "Target job is required."
        }

    # -----------------------------------------------------
    # 1. Retrieve role requirements from Career RAG
    # -----------------------------------------------------
    knowledge_text = ""

    if rag_context is None:
        rag_context = get_active_career_rag_context()

    if rag_context is not None:
        knowledge_text = rag_context
    elif _rag_enabled():
        try:
            from rag.retriever import retrieve_as_context

            knowledge_text = retrieve_as_context(
                (
                    "skills, competencies, qualifications, "
                    "tools, technologies, responsibilities and "
                    f"resume requirements for the {target_job} role"
                ),
                domain="career",
                top_k=8,
            ) or ""

        except Exception:
            knowledge_text = ""

    # -----------------------------------------------------
    # 2. Extract required skills dynamically
    # -----------------------------------------------------
    required_skills = _extract_skills_from_career_knowledge(
        knowledge_text,
        target_job,
    )

    if not required_skills:
        required_skills = _extract_skills_with_llm(
            target_role=target_job,
        )

    # -----------------------------------------------------
    # 3. Build target-role requirement text
    # -----------------------------------------------------
    role_requirement_text = f"""
Target job: {target_job}
Required skills: {_as_text(required_skills)}
Role knowledge: {knowledge_text}
""".strip()

    resume_text_clean = _resume_text_for_embedding(
        resume_text
    )

    semantic_match_score = calculate_embedding_similarity(
        resume_text_clean,
        role_requirement_text,
    )

    # -----------------------------------------------------
    # 4. Report structure separately
    # -----------------------------------------------------
    structure_checks = _resume_structure_checks(
        resume_text
    )

    structure_present = [
        key
        for key, present in structure_checks.items()
        if present
    ]

    structure_missing = [
        key
        for key, present in structure_checks.items()
        if not present
    ]

    # -----------------------------------------------------
    # 5. Semantic skill-level analysis
    # -----------------------------------------------------
    resume_skill_matches, resume_missing_skills = (
        _best_skill_matches(
            current_skills=_extract_resume_skill_candidates(
                resume_text,
                required_skills,
            ),
            required_skills=required_skills,
            similarity_threshold=0.65,
        )
    )

    suggestions: list[str] = []

    if resume_missing_skills:
        suggestions.append(
            "Consider adding evidence of these role requirements "
            "when they are genuinely present in your experience: "
            + ", ".join(resume_missing_skills[:10])
        )

    if structure_missing:
        suggestions.append(
            "Review missing resume sections/details: "
            + ", ".join(structure_missing)
        )

    if not suggestions:
        suggestions.append(
            "Resume content is semantically aligned with the "
            "retrieved role requirements."
        )

    return {
        "target_job": target_job,
        "semantic_match_score": semantic_match_score,
        "required_skills": required_skills,
        "skill_matches": resume_skill_matches,
        "skills_not_evidenced": resume_missing_skills,
        "structure_checks": structure_checks,
        "structure_present": structure_present,
        "structure_missing": structure_missing,
        "suggestions": suggestions,
    }


def _extract_resume_skill_candidates(
    resume_text: str,
    required_skills: list[str],
) -> list[str]:
    """
    Find evidence for dynamically retrieved skills in the resume.

    The required skill vocabulary comes from RAG/LLM output,
    not from a hardcoded role dictionary.

    FIX (efficiency, not a correctness bug): the previous version called
    calculate_embedding_similarity() once per skill, which re-encodes the
    full resume text from scratch every single call. For a resume checked
    against N required skills, that's N redundant encodings of the same
    text. This batches the encoding instead: the resume is embedded once,
    all not-yet-matched skills are embedded once as a batch, and similarity
    is computed via a single matrix multiply.
    """
    if not resume_text or not required_skills:
        return []

    resume_normalized = _normalize_skill_name(
        resume_text
    )

    candidates: list[str] = []
    remaining_skills: list[str] = []

    for skill in required_skills:
        normalized_skill = _normalize_skill_name(skill)

        if not normalized_skill:
            continue

        # First check exact normalized phrase - no embedding needed.
        if normalized_skill in resume_normalized:
            candidates.append(normalized_skill)
        else:
            remaining_skills.append(normalized_skill)

    if remaining_skills:
        resume_embedding = _encode_texts([resume_text])[0]
        skill_embeddings = _encode_texts(remaining_skills)

        similarities = util.cos_sim(
            resume_embedding,
            skill_embeddings,
        )[0]

        for skill, similarity in zip(remaining_skills, similarities):
            score = max(0.0, min(100.0, ((float(similarity.item()) + 1.0) / 2.0) * 100.0))
            if score >= 65.0:
                candidates.append(skill)

    return _unique_strings(candidates)