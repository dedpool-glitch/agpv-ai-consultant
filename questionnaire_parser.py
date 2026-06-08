from constants import (
    ARRAY_CONFIG_OPTIONS,
    MANUAL_INPUT_TEXT,
    NUMERIC_QUESTIONNAIRE_FIELDS,
    PVMAPS_VALIDATION_LIMITS,
    PVMAPS_VALIDATION_MESSAGES,
    QUESTIONNAIRE_FIELD_LIMITS,
)
from panel_specs import get_panel_models


def parse_questionnaire_answer(field, answer):
    if isinstance(answer, str):
        answer = answer.strip()

    if answer == "":
        raise ValueError(f"{field} cannot be empty.")

    if field in NUMERIC_QUESTIONNAIRE_FIELDS:
        answer = parse_number(field, answer)
        validate_numeric_questionnaire_answer(field, answer)
        return answer

    if field == "array_config":
        return parse_array_config(answer)

    if field == "panel_model":
        return parse_panel_model(answer)

    return answer


def parse_number(field, answer):
    try:
        return float(answer)
    except ValueError as error:
        raise ValueError(f"{field} must be a number.") from error


def validate_numeric_questionnaire_answer(field, answer):
    if field in QUESTIONNAIRE_FIELD_LIMITS:
        min_key, max_key, message_key = QUESTIONNAIRE_FIELD_LIMITS[field]
        minimum = PVMAPS_VALIDATION_LIMITS[min_key]
        maximum = PVMAPS_VALIDATION_LIMITS[max_key]

        if not (minimum <= answer <= maximum):
            raise ValueError(PVMAPS_VALIDATION_MESSAGES[message_key])
    if field=="azimuth" and answer not in [PVMAPS_VALIDATION_LIMITS["azimuth_ew"], PVMAPS_VALIDATION_LIMITS["azimuth_ns"]]:
        raise ValueError(PVMAPS_VALIDATION_MESSAGES["azimuth_range"])

    if field == "pitch" and answer <= 0:
        raise ValueError(PVMAPS_VALIDATION_MESSAGES["pitch_positive"])

    if field == "gs_height" and answer < 0:
        raise ValueError(PVMAPS_VALIDATION_MESSAGES["gs_height_nonnegative"])

    if field == "array_elevation" and answer < 0:
        raise ValueError(PVMAPS_VALIDATION_MESSAGES["array_elevation_nonnegative"])


def parse_array_config(answer):
    options_by_lowercase = {option.lower(): option for option in ARRAY_CONFIG_OPTIONS}
    clean_answer = answer.lower()

    if clean_answer not in options_by_lowercase:
        raise ValueError(PVMAPS_VALIDATION_MESSAGES["invalid_array_config"])

    return options_by_lowercase[clean_answer]


def parse_panel_model(answer):
    allowed_models = [MANUAL_INPUT_TEXT["default_panel_model"]] + get_panel_models()
    models_by_lowercase = {model.lower(): model for model in allowed_models}
    clean_answer = answer.lower()

    if clean_answer not in models_by_lowercase:
        raise ValueError("Unknown panel model. Enter a known panel model or default values.")

    return models_by_lowercase[clean_answer]
