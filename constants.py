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

APP_TITLE = "PVMAPS Solar Yield Demo"

LOCATION_TEXT = {
    "input_label": "Farm Location (City, State)",
    "geocode_button": "Retrieve coordinates",
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
    "defaults_button": "Use defaults for remaining answers",
    "complete_message": "Questionnaire complete!",
    "not_ready_message": "Complete the questionnaire or use defaults before running PVMAPS.",
    "start_first_error": "Please start the questionnaire before running PVMAPS.",
    "defaults_applied_message": "Defaults have been applied for the remaining answers. You can now run PVMAPS.",
    "assumptions_header": "Assumptions",
}

PVMAPS_RUN_TEXT = {
    "run_button": "Run PVMAPS",
    "validation_error": "Input validation failed:",
    "spinner": "Running MATLAB PVMAPS...",
    "simulation_error": "PVMAPS simulation failed.",
    "simulation_error_detail": (
        "The selected configuration may not be supported by the current PVMAPS setup, "
        "or MATLAB could not complete the simulation."
    ),
}

RESULT_TEXT = {
    "result_header": "Result",
    "monthly_yield_header": "Monthly Yield",
    "chart_x_label": "Month",
    "chart_title": "Monthly PVMAPS Yield",
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
    "solar_experience_label":"How would you describe your experience with solar farm design?",
    "submit_button":"Submit profile",
}

USER_TYPE_OPTIONS = [
    "Farmer",
    "Landowner",
    "Researcher",
    "Solar developer",
    "Policymaker",
    "Other",
]

SOLAR_EXPERIENCE_OPTIONS = [
    "I am new to solar farm design",
    "I know basic solar terms but have not worked on a project",
    "I have evaluated solar options as a landowner, farmer, or decision-maker",
    "I have technical experience designing or modeling solar systems",
]

DATASHEET_UPLOAD_TEXT = {
    "label": "Upload a solar panel datasheet",
    "help": "Optional PDF upload.",
    "success": "Datasheet uploaded successfully.",
    "uploaded_file_label": "Uploaded datasheet",
}

LLM_SYSTEM_EXTRACTION_PROMPT = """
You are a strict extraction assistant for a PVMAPS questionnaire.

Extract only the requested field from the user's response.

Return only raw JSON. Do not use markdown, code fences, explanations, or extra text.

Required JSON format:
{
  "field": "<requested_field_name>",
  "value": <extracted_value_or_null>,
  "status": "extracted" | "needs_clarification",
  "follow_up_question": <question_string_or_null>
}

Rules:
- Extract only the requested field.
- Do not invent values or defaults.
- If the value is clear, set status to "extracted" and follow_up_question to null.
- If the value is unknown, unclear, or belongs to another field, set value to null, status to "needs_clarification", and ask one short follow-up question about the same field.
- Numeric values must be numbers, not strings.
- Convert units only when obvious. If uncertain, ask a follow-up.

Field rules:
- panel_model: return model name as a string, or "default values" if requested.
- array_config: return only "fixed", "tracking", or "GSVBF".
- tilt: return panel tilt angle in degrees.
- azimuth: return 90 for east-west, 180 for north-south.
- albedo: return ground reflectiveness from 0 to 1.
- pitch: return row spacing in meters.
- gs_height: return ground sculpting height in meters.
- array_elevation: return panel mounting height above ground in meters.

Examples:
Requested field: pitch
User response: Rows are around 10 meters apart.
Output: {"field": "pitch", "value": 10, "status": "extracted", "follow_up_question": null}

Requested field: tilt
User response: I'm not sure.
Output: {"field": "tilt", "value": null, "status": "needs_clarification", "follow_up_question": "Do you know the panel tilt angle in degrees, or should we use a default?"}
"""

LLM_SYSTEM_QUESTION_GENERATOR_PROMPT = """
You are a friendly questionnaire assistant for a PVMAPS solar farm simulator.

Your job is to ask one clear, farmer-friendly question for the requested PVMAPS input field.

Rules:
- Ask exactly one question.
- Focus only on the requested field.
- Use simple, non-technical language.
- Do not ask for multiple fields at once.
- Do not invent or assume values.
- Do not assume the user knows solar engineering details.
- For technical fields, ask whether they know the value or would like to use a typical/default value.
- Keep the question short.

Field guidance:
- panel_model: Ask whether they know the solar panel model number, have a datasheet, or want to use default panel specs.
- array_config: Ask whether the panels will be fixed in place, track the sun, or use a vertical bifacial ground-sculpting setup.
- tilt: Ask whether they know the panel angle relative to the ground, or want to use a typical/default value.
- azimuth: Ask whether the panel rows run east-west or north-south, or whether they are unsure.
- albedo: Ask what ground surface will be under the panels, such as soil, grass, gravel, or reflective material.
- pitch: Ask whether they know roughly how far apart the panel rows will be.
- gs_height: Ask whether the design includes ground sculpting; if yes, ask whether they know the height.
- array_elevation: Ask whether they know how high the panels will be mounted above the ground.

Profile adaptation:
- Use the user profile to adjust wording and technical depth.
- For users new to solar farm design, avoid jargon and mention that a typical/default value can be used.
- For technical users, you may use precise solar design terms.
- For farmers or landowners, frame questions around practical project details.
- The profile should affect wording only, not the requested field.

Return only the question text. Do not include extra formatting or explanation.
"""

LLM_SYSTEM_OUTPUT_EXPLANATION_PROMPT = """
You are an assistant that explains PVMAPS solar-yield simulation results to a non-expert user.

Your job:
- Explain the simulation result in simple, clear language.
- Use only the values provided in the input.
- Highlight the most important solar-yield insights.
- Mention any assumptions or default values used.
- Keep the explanation concise.

Rules:
- Do not invent numbers.
- Do not change units.
- Do not estimate crop yield.
- Do not estimate cost, profit, payback, or financial return.
- Do not make recommendations beyond what the simulation output supports.
- If something is not provided, say it is not available instead of guessing.

Profile adaptation:
- Use the user profile to choose the explanation style.
- If the user is new to solar farm design, explain terms simply and avoid jargon.
- If the user has technical/modeling experience, include slightly more technical detail.
- If the user is a farmer or landowner, focus on practical interpretation of the solar-yield result.
- Do not change, reinterpret, or invent simulation numbers based on the profile.
"""

LLM_SYSTEM_CANDIDATE_CONFIG_PROMPT = """
You generate one candidate configuration for a PVMAPS solar-yield simulation.

Return only raw JSON.
Do not use markdown.
Do not include text before or after the JSON.

Required JSON format:
{
  "candidate_name": "<short descriptive name>",
  "pvmaps_inputs": {
    "panel_model": "<allowed value>",
    "array_config": "<allowed value>",
    "tilt": <number>,
    "azimuth": <number>,
    "albedo": <number>,
    "pitch": <number>,
    "gs_height": <number>,
    "array_elevation": <number>
  },
  "justifications": {
    "panel_model": "<justification>",
    "array_config": "<justification>",
    "tilt": "<justification>",
    "azimuth": "<justification>",
    "albedo": "<justification>",
    "pitch": "<justification>",
    "gs_height": "<justification>",
    "array_elevation": "<justification>"
  }
}

Rules:
- Use the provided field schema for allowed values, bounds, and units.
- Use the provided climate summary as context, if needed.
- Use "default values" for panel_model unless a specific validated panel model is available.
- Do not invent unsupported fields.
"""