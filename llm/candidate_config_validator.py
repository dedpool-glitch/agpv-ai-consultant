from questionnaire.parser import parse_questionnaire_answer
from constants import UNAVAILABLE_ARRAY_CONFIGS


def validate_candidate_config(candidate):
    errors = []

    if candidate is None:
        return None, ["LLM did not return valid JSON."]

    if not isinstance(candidate, dict):
        return None, ["Candidate response must be a JSON object, not a list or other type."]

    if candidate.get("_parse_error"):
        return None, [candidate["_parse_error"]]

    if "pvmaps_inputs" not in candidate:
        return None, ["Candidate is missing pvmaps_inputs."]

    raw_inputs = candidate["pvmaps_inputs"]
    parsed_inputs = {}

    required_fields = [
        "panel_model",
        "array_config",
        "tilt",
        "azimuth",
        "albedo",
        "pitch",
        "gs_height",
        "array_elevation",
    ]

    for field in required_fields:
        if field not in raw_inputs:
            errors.append(f"Missing field: {field}")
            continue

        try:
            parsed_inputs[field] = parse_questionnaire_answer(
                field,
                raw_inputs[field],
            )
        except ValueError as error:
            errors.append(f"{field}: {error}")

    if errors:
        return None, errors

    if parsed_inputs["array_config"] in UNAVAILABLE_ARRAY_CONFIGS:
        return None, [UNAVAILABLE_ARRAY_CONFIGS[parsed_inputs["array_config"]]]

    if parsed_inputs["array_config"] == "GSVBF" and parsed_inputs["gs_height"] <= 0:
        return None, ["gs_height: Ground sculpting height must be greater than zero for GSVBF arrays."]

    return parsed_inputs, []
