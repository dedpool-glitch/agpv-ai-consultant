REQUIRED_QUESTIONNAIRE_FIELDS = [
    "panel_model",
    "array_config",
    "tilt",
    "azimuth",
    "albedo",
    "pitch",
    "gs_height",
    "array_elevation",
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

QUESTIONNAIRE_FIELD_LIMITS = {
    "tilt": ("tilt_min", "tilt_max", "tilt_range"),
    "albedo": ("albedo_min", "albedo_max", "albedo_range"),
}

APP_TITLE = "AgPV Assistant"

LOCATION_TEXT = {
    "input_label": "Farm Location (City, State)",
    "geocode_button": "Use this location",
    "geocode_error": "Could not retrieve coordinates.",
    "matched_location_header": "Matched Location",
    "result_location_header": "Location",
}

INPUT_MODE = {
    "label": "Choose input method",
    "questionnaire": "Questionnaire",
    "manual": "Manual Input",
}

MANUAL_INPUT_TEXT = {
    "description": "Fill in the parameters below to run the PVMAPS simulation. Default values are provided for convenience, but you can adjust them as needed.",
    "panel_model_label": "Panel model from datasheet",
    "default_panel_model": "default values",
    "default_source": "default PVMAPS example",
    "cell_type_unknown": "not specified",
    "datasheet_cell_type_label": "Datasheet cell type",
    "source_label": "Source",
    "pvmaps_cell_tech_label": "PVMAPS cell technology",
    "panel_height_label": "Panel Height(metres)",
    "direct_efficiency_label": "Direct Efficiency",
    "diffuse_efficiency_label": "Diffuse Efficiency",
    "temperature_coefficient_label": "Temperature Coefficient",
    "array_config_label": "Array Configuration",
    "tilt_label": "Tilt angle(degrees)",
    "azimuth_label": "Azimuth angle(degrees)",
    "albedo_label": "Albedo",
    "pitch_label": "Row Spacing(metres)",
    "ground_sculpting_height_label": "Ground Sculpting Height(metres)",
    "elevation_label": "Elevation(metres)",
}

QUESTIONNAIRE_UI_TEXT = {
    "start_description": "Start the guided questionnaire when you are ready to provide the remaining PVMAPS inputs.",
    "start_button": "Start questionnaire",
    "answer_label": "Your answer",
    "submit_button": "Submit answer",
    "numeric_error": "Invalid input for {field}. Please enter a valid number.",
    "defaults_button": "Generate recommended setup",
    "complete_message": "Questionnaire complete!",
    "not_ready_message": "Complete the questionnaire or use defaults before running PVMAPS.",
    "start_first_error": "Please start the questionnaire before running PVMAPS.",
    "defaults_applied_message": "Recommended values have been applied for the remaining answers. You can now review the setup and generate an estimate.",
    "assumptions_header": "Assumptions",
    "recommendation_error": "Could not generate a valid recommended setup.",
    "recommendation_header": "Recommended setup justifications",
}

GOAL_FOLLOW_UP_UI_TEXT = {
    "start_description": "Let's narrow things down with a few quick questions.",
    "start_button": "Start consultation",
    "answer_label": "Your answer",
    "complete_message": "Thanks. I have enough context to move into the technical setup.",
    "context_header": "Consultation context",
}

GENERAL_CHAT_UI_TEXT = {
    "route_question": "Would you like to discuss agrivoltaics first, or move toward a solar-yield estimate?",
    "discuss_button": "Discuss first",
    "estimate_button": "Generate solar estimate",
    "description": "",
    "answer_label": "Ask an AgPV question",
    "start_estimate_button": "Start solar estimate setup",
}

PVMAPS_RUN_TEXT = {
    "run_button": "Generate solar estimate",
    "validation_error": "Input validation failed:",
    "spinner": "Running model",
    "simulation_error": "PVMAPS simulation failed.",
    "simulation_error_detail": (
        "The selected configuration may not be supported by the current PVMAPS setup, "
        "or MATLAB could not complete the simulation."
    ),
}

RESULT_TEXT = {
    "latest_estimate_header": "Latest solar-yield estimate",
    "result_header": "Result",
    "monthly_yield_header": "Monthly Yield",
    "chart_x_label": "Month",
    "chart_title": "Monthly PVMAPS Yield",
    "follow_up_header": "Continue the conversation",
    "follow_up_label": "Ask a follow-up about this estimate",
}

TRACE_UI_TEXT = {
    "header": "LLM Trace",
    "empty_message": "No LLM calls have been logged yet.",
}

PANEL_DEFAULT_SPECS = {
    "cell_type_raw": MANUAL_INPUT_TEXT["cell_type_unknown"],
    "cell_tech": "AL_BSF",
    "module_height": 4.8,
    "stc_eff_direct": 21.8,
    "stc_eff_diffuse": 21.8,
    "tcoeff": 0.0041,
    "source": MANUAL_INPUT_TEXT["default_source"],
}

ALLOWED_CELL_TECH = ["AL_BSF", "BI_PERC", "SHJ", "PVK_SI_2T", "PVK_SI_4T", "SHJ_NN"]
ARRAY_CONFIG_OPTIONS = ["fixed", "tracking", "GSVBF"]

PVMAPS_VALIDATION_LIMITS = {
    "lat_min": -90,
    "lat_max": 90,
    "lon_min": -180,
    "lon_max": 180,
    "efficiency_min": 0,
    "efficiency_max": 100,
    "tcoeff_min": 0,
    "tcoeff_max": 0.01,
    "tilt_min": 0,
    "tilt_max": 90,
    "azimuth_ew": 90,
    "azimuth_ns": 180,
    "albedo_min": 0,
    "albedo_max": 1,
}

PVMAPS_VALIDATION_MESSAGES = {
    "invalid_cell_tech": "Invalid cell technology.",
    "module_height_positive": "Module height must be positive.",
    "direct_efficiency_range": "Direct efficiency must be between 0 and 100 percent.",
    "diffuse_efficiency_range": "Diffuse efficiency must be between 0 and 100 percent.",
    "tcoeff_range": "Temperature coefficient should usually be between 0 and 0.01.",
    "invalid_array_config": "Invalid tracking configuration.",
    "tilt_range": "Tilt must be between 0 and 90 degrees.",
    "azimuth_range": "Azimuth must be either 90 (East-West) or 180 (North-South).",
    "albedo_range": "Albedo must be between 0 and 1.",
    "pitch_positive": "Pitch must be positive.",
    "gs_height_nonnegative": "Ground sculpting height cannot be negative.",
    "array_elevation_nonnegative": "Array elevation cannot be negative.",
    "array_elevation_height_relation": "Array elevation must be greater than half the module height.",
    "lat_range": "Latitude must be between -90 and 90.",
    "lon_range": "Longitude must be between -180 and 180.",
}

PVMAPS_FIELD_SCHEMA = {
    "panel_model": {
        "type": "string",
        "allowed": ["default values"],
        "note": "Use stored panel model name or default values."
    },
    "array_config": {
        "type": "string",
        "allowed": ARRAY_CONFIG_OPTIONS,
    },
    "tilt": {
        "type": "number",
        "min": 0,
        "max": 90,
        "unit": "degrees",
    },
    "azimuth": {
        "type": "number",
        "allowed": [90, 180],
        "unit": "degrees",
    },
    "albedo": {
        "type": "number",
        "min": 0,
        "max": 1,
    },
    "pitch": {
        "type": "number",
        "min_exclusive": 0,
        "unit": "meters",
    },
    "gs_height": {
        "type": "number",
        "min": 0,
        "unit": "meters",
    },
    "array_elevation": {
        "type": "number",
        "min": 0,
        "unit": "meters",
    },
}

#tcoeff=0.004 - default value

MONTH_LABELS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

USER_PROFILE_TEXT={
    "header":"Tell us about yourself and your background to help us tailor the experience.",
    "user_type_label":"Which of these best describes you?",
    "user_role_label":"Describe your role in your own words",
    "solar_experience_label":"How would you describe your experience with solar farm design?",
    "project_goal_label":"What is your objective today?",
    "site_location_label":"Please enter a site location if you have one",
    "site_location_placeholder":"Lafayette, Indiana",
    "goal_details_label":"Tell us more about your goal",
    "submit_button":"Upload profile",
}

USER_TYPE_OPTIONS = [
    "Farmer/Landowner",
    "Researcher",
    "Solar developer",
    "Policymaker",
    "Other",
]

SOLAR_EXPERIENCE_OPTIONS = [
    "Beginner-I am new to solar farm design.",
    "Some experience-I know the basics.",
    "Technical-I understand solar farm design terms.",
    "Expert-I have technical experience designing or modeling solar systems",
]

PROJECT_GOAL_OPTIONS=[
    "Understand if AgPV is feasible for my land",
        "Compare solar farm design options",
        "Estimate solar energy yield",
        "Learn about agrivoltaics",
        "Support research or planning",
        "Other / not sure"
]
DATASHEET_UPLOAD_TEXT = {
    "label": "Upload a solar panel datasheet",
    "help": "Optional PDF upload.",
    "success": "Datasheet uploaded successfully.",
    "uploaded_file_label": "Uploaded datasheet",
}

