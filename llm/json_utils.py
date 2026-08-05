import json


def parse_json_response(response):
    """
    Parse a JSON object out of an LLM's raw text response.

    Handles markdown code fences and falls back to extracting the outermost
    {...} block if the response has stray text around the JSON. Returns None
    if no valid JSON object could be found.
    """
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
        try:
            return json.loads(cleaned_response[json_start:json_end + 1])
        except json.JSONDecodeError:
            return None
