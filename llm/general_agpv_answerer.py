import json

from llm.prompts import LLM_SYSTEM_GENERAL_AGPV_PROMPT
from llm.client import call_llm


def format_retrieved_context(retrieved_context):
    if not retrieved_context:
        return None

    context_blocks = []
    for index, chunk in enumerate(retrieved_context, start=1):
        metadata = chunk.get("metadata", {})
        title = metadata.get("title", "Unknown source")
        page = metadata.get("page", "unknown page")
        context_blocks.append(f"Excerpt {index} ({title}, page {page}):\n{chunk['text']}")

    return "\n---\n".join(context_blocks)


def answer_general_agpv_question(
    user_question,
    api_key,
    user_profile=None,
    location_context=None,
    pvmaps_state=None,
    latest_pvmaps_output=None,
    conversation_history=None,
    retrieved_context=None,
):
    context_text = format_retrieved_context(retrieved_context)
    context_section = (
        f"Retrieved source excerpts (ground specific facts/figures in these where relevant; "
        f"don't force it if they're not actually relevant):\n{context_text}\n\n"
        if context_text
        else ""
    )

    messages = [
        {"role": "system", "content": LLM_SYSTEM_GENERAL_AGPV_PROMPT},
        {
            "role": "user",
            "content": (
                f"User question:\n{user_question}\n\n"
                f"User profile:\n{json.dumps(user_profile, indent=2)}\n\n"
                f"Location context:\n{json.dumps(location_context, indent=2)}\n\n"
                f"Current PVMAPS state:\n{json.dumps(pvmaps_state, indent=2)}\n\n"
                f"Latest PVMAPS output:\n{json.dumps(latest_pvmaps_output, indent=2)}\n\n"
                f"Conversation history:\n{json.dumps(conversation_history, indent=2)}\n\n"
                f"{context_section}"
                "Answer the user's question using the available context."
            ),
        },
    ]

    response = call_llm(messages, api_key)
    return response.strip()

