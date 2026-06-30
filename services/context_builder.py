"""
app/services/context_builder.py

Builds the personalization context loaded before every Groq request:
  1. User Profile (general + the relevant domain sub-profile)
  2. User Memories (top-N by importance, filtered to the active domain
     plus general "preference"/"goal" memories)
  3. Recent Chat History (last few turns of the active conversation)

This is the piece that fulfils "user enters profile once, system
remembers and personalizes" — domain_agents.py and the RAG retriever both
consume the strings this module produces.
"""
from sqlalchemy.orm import Session

from services.profile_service import get_full_profile
from services.memory_service import retrieve_memory


def build_profile_context(db: Session, user_id: str, domain: str) -> str:
    profile = get_full_profile(db, user_id)
    lines = []

    general = profile.get("general")
    if general:
        lines.append("User Profile:")
        if general.age:
            lines.append(f"- Age: {general.age}")
        if general.gender:
            lines.append(f"- Gender: {general.gender}")
        if general.location:
            lines.append(f"- Location: {general.location}")
        if general.height_cm:
            lines.append(f"- Height: {general.height_cm} cm")
        if general.weight_kg:
            lines.append(f"- Weight: {general.weight_kg} kg")

    domain_profile = profile.get(domain)
    if domain_profile:
        lines.append(f"\n{domain.capitalize()} Profile:")
        for key, value in vars(domain_profile).items():
            if key.startswith("_") or key in ("id", "user_id", "updated_at") or value is None:
                continue
            lines.append(f"- {key.replace('_', ' ').title()}: {value}")

    return "\n".join(lines)


def build_memory_context(db: Session, user_id: str, domain: str, limit: int = 5) -> str:
    # Domain-specific memories first, then general preference/goal memories
    domain_memories = retrieve_memory(db, user_id, category=domain, limit=limit)
    general_memories = retrieve_memory(db, user_id, category="preference", limit=3)
    goal_memories = retrieve_memory(db, user_id, category="goal", limit=3)

    seen_ids = set()
    combined = []
    for m in domain_memories + goal_memories + general_memories:
        if m.id not in seen_ids:
            combined.append(m)
            seen_ids.add(m.id)

    if not combined:
        return ""

    lines = ["Memory (things this user has told the system previously):"]
    for m in combined[:limit]:
        lines.append(f"- {m.memory_text}")
    return "\n".join(lines)
