import json

from constants import PVMAPS_FIELD_SCHEMA
from llm.prompts import LLM_SYSTEM_RECOMMENDED_PVMAPS_CONFIG_PROMPT
from llm.client import call_llm
from llm.json_utils import parse_json_response


def format_retrieved_context(retrieved_context):
    if not retrieved_context:
        return "None available."

    context_blocks = []
    for index, chunk in enumerate(retrieved_context, start=1):
        metadata = chunk.get("metadata", {})
        title = metadata.get("title", "Unknown source")
        page = metadata.get("page", "unknown page")
        context_blocks.append(f"Excerpt {index} ({title}, page {page}):\n{chunk['text']}")

    return "\n---\n".join(context_blocks)


def generate_recommended_pvmaps_config(
    api_key,
    user_profile=None,
    location_context=None,
    consultation_history=None,
    current_pvmaps_state=None,
    latest_user_message=None,
    retrieved_context=None,
):
    schema_text = json.dumps(PVMAPS_FIELD_SCHEMA, indent=2)
    context_text = format_retrieved_context(retrieved_context)

    messages = [
        {"role": "system", "content": LLM_SYSTEM_RECOMMENDED_PVMAPS_CONFIG_PROMPT},
        {
            "role": "user",
            "content": (
                f"User profile:\n{json.dumps(user_profile, indent=2)}\n\n"
                f"Location context:\n{json.dumps(location_context, indent=2)}\n\n"
                f"Consultation history:\n{json.dumps(consultation_history, indent=2)}\n\n"
                f"Current PVMAPS state:\n{json.dumps(current_pvmaps_state, indent=2)}\n\n"
                f"Latest user message:\n{json.dumps(latest_user_message)}\n\n"
                f"Relevant research context:\n{context_text}\n\n"
                f"Allowed field schema:\n{schema_text}\n\n"
                "Generate a recommended PVMAPS setup. Only change an already-set field if the "
                "latest user message explicitly asks for a different value for that specific field."
            ),
        },
    ]

    response = call_llm(messages, api_key)

    parsed_response = parse_json_response(response)

    if parsed_response is None:
        return {
            "_parse_error": "LLM did not return valid JSON.",
            "_raw_response": response,
        }

    return parsed_response

