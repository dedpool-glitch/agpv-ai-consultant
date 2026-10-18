import json

from constants import RAG_SOURCE_BOTH, RAG_SOURCE_NONE, RAG_SOURCES
from llm.prompts import LLM_SYSTEM_RAG_SOURCE_ROUTER_PROMPT
from llm.client import call_llm
from llm.json_utils import parse_json_response


def decide_rag_source(question, api_key, conversation_history=None):
    """
    Decide whether a general_chat question should be answered with help from
    the papers collection, the books collection, both, or neither.

    Falls back to "none" on any parsing failure -- same as the general
    answerer's existing behavior with no retrieval, so a router hiccup never
    breaks the turn.
    """
    messages = [
        {"role": "system", "content": LLM_SYSTEM_RAG_SOURCE_ROUTER_PROMPT},
        {
            "role": "user",
            "content": (
                f"Question:\n{question}\n\n"
                f"Conversation history:\n{json.dumps(conversation_history, indent=2)}\n\n"
                "Decide the source."
            ),
        },
    ]

    response = call_llm(messages, api_key)
    plan = parse_json_response(response)

    if plan is None:
        return {
            "source": RAG_SOURCE_NONE,
            "reason": "Fallback to none because the router returned invalid JSON.",
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
    }
