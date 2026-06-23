from questionnaire.parser import parse_questionnaire_answer


def validate_candidate_config(candidate):
    errors = []

    if candidate is None:
        return None, ["LLM did not return valid JSON."]

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

    return parsed_inputs, []