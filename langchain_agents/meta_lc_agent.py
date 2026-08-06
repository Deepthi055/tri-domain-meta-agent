"""
Meta LangChain Agent
Routes queries to the correct LangChain domain agents.
Drop-in replacement for the existing meta_agent in main.py.
"""
import agents.career_agent as career_original
import agents.health_agent as health_original
import agents.finance_agent as finance_original
from langchain_agents.career_lc_agent import run as career_run
from langchain_agents.health_lc_agent import run as health_run
from langchain_agents.finance_lc_agent import run as finance_run
from core.intent_detector import detect_intent
from core.safety_layer import check_safety, check_relevance
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=3)

FALLBACK_AGENTS = {
    "career": career_original.run,
    "health": health_original.run,
    "finance": finance_original.run,
}

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
            print(f"[LangChain Meta] {domain} agent failed: {result}")
            fallback_fn = FALLBACK_AGENTS.get(domain)
            if fallback_fn:
                fallback = fallback_fn(request)
                fallback["agent_type"] = "fallback"
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