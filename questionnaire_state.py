REQUIRED_QUESTIONNAIRE_FIELDS = [
    "panel_model",
    "array_config",
    "tilt",
    "azimuth",
    "albedo",
    "pitch",
    "gs_height",
    "array_elevation"
]

QUESTION_MAP = {
    "panel_model": "Do you know the solar panel model number, or do you have a datasheet?",
    "array_config": "Do you know whether the panels are fixed, tracking, or vertical bifacial with ground sculpting?",
    "tilt": "Do you know the panel tilt angle in degrees?",
    "azimuth": "Do you know whether the panel rows are oriented east-west or north-south?",
    "albedo": "Do you know the ground surface type under the panels, such as soil, grass, gravel, or reflective material?",
    "pitch": "Do you know the row spacing between panel rows?",
    "gs_height": "Does this design include ground sculpting? If yes, do you know the ground sculpting height?",
    "array_elevation": "Do you know how high the panels are mounted above the ground?",
}

QUESTIONNAIRE_DEFAULTS = {
    "panel_model": "default values",
    "array_config": "tracking",
    "tilt": 25.0,
    "azimuth": 90.0,
    "albedo": 0.3,
    "pitch": 11.0,
    "gs_height": 0.5,
    "array_elevation": 3.0,
}

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