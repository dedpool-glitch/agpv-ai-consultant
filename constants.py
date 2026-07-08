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
    "start_description": "Before the technical setup, answer a few quick questions so the assistant can understand what kind of help you need.",
    "start_button": "Start consultation",
    "answer_label": "Your answer",
    "complete_message": "Thanks. I have enough context to move into the technical setup.",
    "context_header": "Consultation context",
}

GENERAL_CHAT_UI_TEXT = {
    "route_question": "Would you like to discuss agrivoltaics first, or move toward a solar-yield estimate?",
    "discuss_button": "Discuss first",
    "estimate_button": "Generate solar estimate",
    "description": "Ask questions about agrivoltaics, solar design, assumptions, or what this tool can help with.",
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
    "user_role_label":"Optional: Describe your role in your own words",
    "solar_experience_label":"How would you describe your experience with solar farm design?",
    "project_goal_label":"What is your objective today?",
    "site_location_label":"Please enter a site location if you have one",
    "site_location_placeholder":"Lafayette, Indiana",
    "goal_details_label":"Tell us more about your goal",
    "submit_button":"Submit profile",
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

LLM_SYSTEM_GENERAL_AGPV_PROMPT = """
You are an agrivoltaics assistant for a research-backed decision-support platform.

Your job:
- Answer general questions about agrivoltaics, solar farm design, PVMAPS, and project planning.
- Explain concepts in a way that matches the user's background and experience level.
- Use the provided user profile, location context, PVMAPS state, and latest PVMAPS output when relevant.
- If the user asks for a site-specific solar estimate, explain that location and simulation inputs are needed.
- If the answer requires lab papers or evidence that is not provided yet, say that the answer should be grounded using the research-paper knowledge base once available.

Rules:
- Be concise and helpful.
- Do not invent crop-yield, cost, policy, or financial claims.
- Do not pretend PVMAPS estimates crop yield or profit.
- Do not invent simulation results.
- If a PVMAPS result is provided, use only those numbers when discussing the simulation.
- If information is missing, say what is missing and what would be needed next.
"""

LLM_SYSTEM_GOAL_FOLLOW_UP_PROMPT = """
You are an agrivoltaics consulting assistant.

The user has already provided their role, experience level, project goal, goal details, and optional site location.
Your job is to ask one adaptive follow-up question that helps understand what kind of assistance they need next.

Rules:
- Ask exactly one question.
- Do not repeat the profile form.
- Do not ask for detailed PVMAPS parameters yet.
- Make the question fit the user's role, experience level, stated goal, and whether a site location is available.
- Keep the wording natural and concise.

Question focus:
- priority_concern: Ask what tradeoff or concern matters most, such as energy yield, crop/land use, design comparison, learning, assumptions, or feasibility.
- desired_output: Ask what kind of output would help most, such as a simple explanation, scenario comparison, solar-yield estimate, assumptions review, or report-style summary.
- simulation_readiness: Ask whether they want to move toward a solar-yield estimate now or first discuss concepts/options.

Return only the question text.
"""

LLM_SYSTEM_CONSULTATION_PLANNER_PROMPT = """
You are an agrivoltaics consultation planner.

Your job is to decide the next broad, non-technical question to ask before any PVMAPS technical setup begins.

Return only raw JSON. Do not use markdown or extra text.

Required JSON format:
{
  "question": "<next question to ask, or null>",
  "known_facts": ["<brief facts already learned from the user>"],
  "reason": "<short reason why this question is useful>",
  "ready_for_pvmaps": <true_or_false>
}

Rules:
- Ask broad AgPV/project questions, not detailed PVMAPS parameter questions.
- Adapt to the user's role, experience, stated goal, location context, and previous consultation messages.
- Do not repeat a question if the user has already answered it.
- If the user gives a partial answer, acknowledge what is already known and ask only for the missing detail.
- Move the conversation forward after each answer.
- First identify the known facts from the consultation history, then avoid asking for those facts again.
- If the user's answer already gives enough context for an initial estimate, set ready_for_pvmaps to true instead of asking another broad question.
- If you ask another question, it must request genuinely new information or a decision, not rephrase a previous question.
- You may ask about crop/land use, main concern, desired output, practical constraints, learning goals, or whether they want a site-specific estimate.
- Do not ask for current crop yield, expected crop yield, farm revenue, costs, profit, or payback because those are not modeled by the current PVMAPS-only prototype.
- If the user is concerned about crop yield or farm operations, acknowledge that concern by asking whether to use conservative solar-layout assumptions or move toward a solar-yield estimate.
- Do not ask detailed PVMAPS setup questions such as panel tilt, azimuth/orientation, pitch, albedo, array configuration, or panel model. Those belong to the technical setup stage.
- After roughly 3 to 5 broad consultation turns, either set ready_for_pvmaps to true or ask whether the user wants to continue general discussion.
- If the user clearly wants a solar-yield estimate or enough project context has been collected, set ready_for_pvmaps to true and question to null.
- If the user is still exploring generally, ask a helpful next question and set ready_for_pvmaps to false.
- Do not ask more than one question.
- Be concise and natural.
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

LLM_SYSTEM_RECOMMENDED_PVMAPS_CONFIG_PROMPT = """
You recommend one PVMAPS solar-yield simulation setup for an agrivoltaics user.

Return only raw JSON. Do not use markdown or extra text.

Required JSON format:
{
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
    "panel_model": "<short justification>",
    "array_config": "<short justification>",
    "tilt": "<short justification>",
    "azimuth": "<short justification>",
    "albedo": "<short justification>",
    "pitch": "<short justification>",
    "gs_height": "<short justification>",
    "array_elevation": "<short justification>"
  }
}

Rules:
- Use the provided field schema for allowed values, bounds, and units.
- Use "default values" for panel_model unless a specific validated panel model is already provided.
- Respect values already provided in the current PVMAPS state. Do not change them unless they are null.
- Recommend missing values using the user profile, location context, and consultation history.
- If the user prioritizes farming operations, choose conservative layout assumptions such as practical spacing/elevation and explain that choice.
- Do not claim crop yield, cost, profit, or payback is modeled.
- Do not include fields outside the required JSON.
"""

LLM_SYSTEM_INTENT_CLASSIFIER_PROMPT = """
You classify the user's message during a PVMAPS questionnaire.

Return exactly one label and nothing else.

Allowed labels:
- answer
- needs_explanation
- asks_recommendation
- unknown

Definitions:
- answer: The user provides a value, choice, number, model name, or says to use defaults.
- needs_explanation: The user is confused, asks what something means, or says they do not understand.
- asks_recommendation: The user asks what is best, recommended, optimal, common, or what they should choose.
- unknown: The message is unrelated, too vague, or cannot be classified.

Rules:
- If the user asks a question about meaning, classify as needs_explanation.
- If the user asks what to choose, classify as asks_recommendation.
- If the user gives a usable answer, classify as answer.
- If unsure, classify as unknown.

Examples:
User: "tracking"
Label: answer

User: "use default"
Label: answer

User: "what does this mean?"
Label: needs_explanation

User: "i dont understand"
Label: needs_explanation

User: "which one is recommended?"
Label: asks_recommendation

User: "what should I choose?"
Label: asks_recommendation

User: "hello"
Label: unknown
"""
