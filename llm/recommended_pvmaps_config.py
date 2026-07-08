import json

from constants import PVMAPS_FIELD_SCHEMA
from llm.prompts import LLM_SYSTEM_RECOMMENDED_PVMAPS_CONFIG_PROMPT
from llm.client import call_llm


def parse_json_response(response):
    if response is None:
        return None

    cleaned_response = response.strip()
    if cleaned_response.startswith("```json"):
        cleaned_response = cleaned_response.removeprefix("```json").strip()
    if cleaned_response.startswith("```"):
        cleaned_response = cleaned_response.removeprefix("```").strip()
    if cleaned_response.endswith("```"):
        cleaned_response = cleaned_response.removesuffix("```").strip()

    try:
        return json.loads(cleaned_response)
    except json.JSONDecodeError:
        json_start = cleaned_response.find("{")
        json_end = cleaned_response.rfind("}")
        if json_start == -1 or json_end == -1 or json_end <= json_start:
            return None
        return json.loads(cleaned_response[json_start:json_end + 1])


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
                f"User profile:\n{json.dumps(user_profile, indent=2)}\n\n"
                f"Location context:\n{json.dumps(location_context, indent=2)}\n\n"
                f"Consultation history:\n{json.dumps(consultation_history, indent=2)}\n\n"
                f"Current PVMAPS state:\n{json.dumps(current_pvmaps_state, indent=2)}\n\n"
                f"Allowed field schema:\n{schema_text}\n\n"
                "Generate a recommended PVMAPS setup."
            ),
        },
    ]

    response = call_llm(messages, api_key)

    try:
        parsed_response = parse_json_response(response)
    except json.JSONDecodeError:
        parsed_response = None

    if parsed_response is None:
        return {
            "_parse_error": "LLM did not return valid JSON.",
            "_raw_response": response,
        }

    return parsed_response

