import json

from llm.prompts import LLM_SYSTEM_GENERAL_AGPV_PROMPT
from llm.client import call_llm


def answer_general_agpv_question(
    user_question,
    api_key,
    user_profile=None,
    location_context=None,
    pvmaps_state=None,
    latest_pvmaps_output=None,
    conversation_history=None,
):
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
                "Answer the user's question using the available context."
            ),
        },
    ]

    response = call_llm(messages, api_key)
    return response.strip()

