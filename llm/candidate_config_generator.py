import json

from constants import PVMAPS_FIELD_SCHEMA
from llm.prompts import LLM_SYSTEM_CANDIDATE_CONFIG_PROMPT
from llm.client import call_llm


def generate_candidate_config(lat, lon, climate_summary, api_key):
    schema_text = json.dumps(PVMAPS_FIELD_SCHEMA, indent=2)

    messages = [
        {
            "role": "system",
            "content": LLM_SYSTEM_CANDIDATE_CONFIG_PROMPT,
        },
        {
            "role": "user",
            "content": (
                f"Location: lat={lat}, lon={lon}\n"
                f"Climate summary:\n{json.dumps(climate_summary, indent=2)}\n\n"
                f"Allowed field schema:\n{schema_text}\n\n"
                "Generate one candidate PVMAPS configuration."
            ),
        },
    ]

    llm_response = call_llm(messages, api_key)

    try:
        return json.loads(llm_response)
    except json.JSONDecodeError:
        return None
