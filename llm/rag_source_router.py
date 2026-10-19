import json

from constants import RAG_SOURCE_BOTH, RAG_SOURCE_NONE, RAG_SOURCES
from llm.prompts import LLM_SYSTEM_RAG_SOURCE_ROUTER_PROMPT
from llm.client import call_llm
from llm.json_utils import parse_json_response
from llm.retrieval_query import QUERY_INSTRUCTIONS, recent_text_history, validate_retrieval_query


def decide_rag_source(question, api_key, conversation_history=None):
    """
    Decide whether a general_chat question should be answered with help from
    the papers collection, the books collection, both, or neither.

    Falls back to "none" on any parsing failure -- same as the general
    answerer's existing behavior with no retrieval, so a router hiccup never
    breaks the turn.
    """
    history = recent_text_history(conversation_history, question)
    messages = [
        {"role": "system", "content": LLM_SYSTEM_RAG_SOURCE_ROUTER_PROMPT + QUERY_INSTRUCTIONS},
        {
            "role": "user",
            "content": (
                f"Question:\n{question}\n\n"
                f"Recent prior conversation:\n{json.dumps(history, indent=2)}\n\n"
                "Decide the source."
            ),
        },
    ]

    response = call_llm(messages, api_key)
    plan = parse_json_response(response)

    if not isinstance(plan, dict):
        return {
            "source": RAG_SOURCE_NONE,
            "reason": "Fallback to none because the router returned invalid JSON.",
            "retrieval_query": question,
            "query_mode": "fallback",
        }

    requested_source = plan.get("source")
    if requested_source not in RAG_SOURCES:
        requested_source = RAG_SOURCE_NONE

    # The collections overlap substantially. Once research support is needed,
    # search both and let retrieval rank the evidence instead of trusting a
    # second LLM decision to guess where a specific passage was indexed.
    source = (
        RAG_SOURCE_NONE
        if requested_source == RAG_SOURCE_NONE
        else RAG_SOURCE_BOTH
    )
    reason = plan.get("reason")
    if source == RAG_SOURCE_BOTH and requested_source != RAG_SOURCE_BOTH:
        reason = (
            f"{reason or 'Research support requested.'} "
            "Searching both overlapping collections for coverage."
        )

    return {
        "source": source,
        "reason": reason,
        **validate_retrieval_query(question, plan, history),
    }


def plan_expert_retrieval(question, api_key, conversation_history=None):
    """Expert chat keeps its existing both-source search even if planning fails."""
    from llm.retrieval_query import contextual_queries_enabled
    fallback = dict(retrieval_query=question, query_mode='standalone')
    if not contextual_queries_enabled() or not recent_text_history(conversation_history, question):
        return fallback
    try:
        plan = decide_rag_source(question, api_key, conversation_history)
        return {key: plan[key] for key in ('retrieval_query', 'query_mode')}
    except Exception:
        return dict(retrieval_query=question, query_mode='fallback')
