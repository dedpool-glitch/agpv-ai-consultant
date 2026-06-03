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
    "panel_model": "Enter the solar panel model number if you know it. If not, type 'default values'.",
    "array_config": "Enter one array configuration: fixed, tracking, or GSVBF.",
    "tilt": "Enter the panel tilt angle as a number in degrees. Example: 25",
    "azimuth": "Enter the azimuth as a number in degrees. Use 90 for east/west facing or 180 for north/south facing.",
    "albedo": "Enter the ground albedo as a number between 0 and 1. Example: 0.3",
    "pitch": "Enter the row spacing/pitch as a number in meters. Example: 11",
    "gs_height": "Enter the ground sculpting height as a number in meters. If not applicable, enter 0.",
    "array_elevation": "Enter the panel mounting height above ground as a number in meters. Example: 3",
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

NUMERIC_QUESTIONNAIRE_FIELDS = {
    "tilt",
    "azimuth",
    "albedo",
    "pitch",
    "gs_height",
    "array_elevation",
}
