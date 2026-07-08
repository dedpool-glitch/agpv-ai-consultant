from constants import LLM_SYSTEM_GENERAL_AGPV_PROMPT
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
                f"User profile:\n{user_profile}\n\n"
                f"Location context:\n{location_context}\n\n"
                f"Current PVMAPS state:\n{pvmaps_state}\n\n"
                f"Latest PVMAPS output:\n{latest_pvmaps_output}\n\n"
                f"Conversation history:\n{conversation_history}\n\n"
                "Answer the user's question using the available context."
            ),
        },
    ]

    response = call_llm(messages, api_key)
    return response.strip()
