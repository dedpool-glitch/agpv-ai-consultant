from constants import QUESTION_MAP, QUESTIONNAIRE_DEFAULTS, REQUIRED_QUESTIONNAIRE_FIELDS

def initialize_questionnaire_state():
    return {
        "panel_model": None,
        "array_config": None,
        "tilt": None,
        "azimuth": None,
        "albedo": None,
        "pitch": None,
        "gs_height": None,
        "array_elevation": None,
        "assumptions": []
    }

def update_questionnaire_state(state, field, value, assumed=False):
    if field not in REQUIRED_QUESTIONNAIRE_FIELDS:
        raise ValueError(f"Unknown questionnaire field: {field}")

    state[field] = value

    if assumed:
        state["assumptions"].append(f"{field} was assumed/defaulted to {value}.")

    return state

def get_missing_fields(state):
    return [field for field in REQUIRED_QUESTIONNAIRE_FIELDS if state.get(field) is None]

def is_questionnaire_complete(state):
    return len(get_missing_fields(state)) == 0

def get_next_question(state):
    missing_fields = get_missing_fields(state)

    if not missing_fields:
        return None
    next_field = missing_fields[0]

    return {
        "field": next_field,
        "question": QUESTION_MAP[next_field],
    }

def apply_questionnaire_defaults(state):
    for field, default_value in QUESTIONNAIRE_DEFAULTS.items():
        if state.get(field) is None:
            state[field] = default_value
            state["assumptions"].append(
                f"{field} was not provided; defaulted to {default_value}."
            )

    return state