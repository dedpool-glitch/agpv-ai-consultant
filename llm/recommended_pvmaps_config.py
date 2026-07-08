import json

from constants import (
    LLM_SYSTEM_RECOMMENDED_PVMAPS_CONFIG_PROMPT,
    PVMAPS_FIELD_SCHEMA,
)
from llm.client import call_llm


def generate_recommended_pvmaps_config(
    api_key,
    user_profile=None,
    location_context=None,
    consultation_history=None,
    current_pvmaps_state=None,
):
    schema_text = json.dumps(PVMAPS_FIELD_SCHEMA, indent=2)

    messages = [
        {"role": "system", "content": LLM_SYSTEM_RECOMMENDED_PVMAPS_CONFIG_PROMPT},
        {
            "role": "user",
            "content": (
                f"User profile:\n{user_profile}\n\n"
                f"Location context:\n{location_context}\n\n"
                f"Consultation history:\n{consultation_history}\n\n"
                f"Current PVMAPS state:\n{current_pvmaps_state}\n\n"
                f"Allowed field schema:\n{schema_text}\n\n"
                "Generate a recommended PVMAPS setup."
            ),
        },
    ]

    response = call_llm(messages, api_key)

    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return None
