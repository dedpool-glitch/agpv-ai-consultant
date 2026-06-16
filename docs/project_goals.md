# Project Goals

This document captures the project goals and engineering requirements discussed so far for the PVMAPS-focused AgPV AI consultant demo.

## Current Scope

The current system is a PVMAPS solar-yield demo. It should collect or infer the inputs needed by PVMAPS, validate them, run the MATLAB PVMAPS simulator, and show the output in a farmer-readable interface.

The current focus is not full agrivoltaic decision support yet. Crop-yield modeling, optimization, report generation, maps, and RAG over research papers are future extensions.

## Mandatory Requirements

### User Input Flow

- The user must be able to enter a farm location in natural language.
- The app must convert the location into latitude and longitude using the geocoder.
- The matched address must be displayed separately from the coordinates.
- The user must choose an input mode before running PVMAPS.
- The app must support manual input mode.
- The app must support guided questionnaire mode.

### PVMAPS Input Coverage

The system must collect or fill these PVMAPS inputs:

- `module.cell_tech`
- `module.height`
- `module.stc_eff.direct`
- `module.stc_eff.diffuse`
- `module.tcoeff`
- `array.config`
- `array.tilt`
- `array.azimuth`
- `array.albedo`
- `array.pitch`
- `array.gsHeight`
- `array.elevation`
- `lat`
- `lon`

### Panel Specs

- Panel model information must come from structured stored specs when available.
- If the user does not know the panel model, the system may use explicit default panel specs.
- Defaults must not be hidden from the user.
- Datasheet-derived panel specs should be stored in `panel_specs.json`.
- For now, direct and diffuse efficiency can both use the datasheet module efficiency, based on Jabir's guidance.
- For now, `AL_BSF` can be used as the default cell technology, based on Jabir's guidance.

### Questionnaire Behavior

- The questionnaire must collect one missing field at a time.
- The questionnaire must track state across Streamlit reruns using `st.session_state`.
- The app must not run PVMAPS from questionnaire mode until either all required fields are answered or the user explicitly applies defaults.
- The user must be able to use defaults for remaining unanswered fields.
- Any defaulted fields must be shown as assumptions.

### Validation

- Individual questionnaire answers must be validated before being stored.
- Numeric questionnaire answers must be parsed into numbers before entering state.
- Invalid answers like `.` must not be accepted for fields such as `array_config`.
- The final PVMAPS input dictionary must still be validated before MATLAB runs.
- Validation constants and messages should come from shared constants where possible.
- The questionnaire parser should catch single-answer errors before questionnaire state is updated.

### Current Validation Rules

- `array.config` must be one of `fixed`, `tracking`, or `GSVBF`.
- `tilt` must be between 0 and 90 degrees.
- `azimuth` is currently restricted to 90 or 180 for this demo.
- `albedo` must be between 0 and 1.
- `pitch` must be positive.
- `gsHeight` must be non-negative.
- `array.elevation` must be non-negative.
- Latitude must be between -90 and 90.
- Longitude must be between -180 and 180.

### MATLAB / PVMAPS Integration

- The app must call PVMAPS through MATLAB Engine.
- The PVMAPS path must point to the local `PV-MAPS-main` folder.
- The runner must add required PVMAPS folders to the MATLAB path before simulation.
- PVMAPS output must be converted into a Python-readable structure.

### Output Display

- The app must display the matched location.
- The app must display a natural-language result summary.
- The app must display monthly yield values in a readable chart.
- Month labels should be readable.

## Advisory Requirements

### Code Organization

- Keep static values, labels, defaults, options, and messages in `constants.py`.
- Keep PVMAPS-related logic in `pvmaps/`.
- Keep questionnaire state, parsing, and conversion logic in `questionnaire/`.
- Keep LLM API/client and extraction logic in `llm/`.
- Keep helper services such as geocoding and panel specs lookup in `services/`.
- Keep demo scripts in `demos/`.
- Avoid placing too much logic inside `app.py`.

### Engineering Principles

- Prefer one source of truth for validation ranges and messages.
- Keep validation layered:
  - questionnaire answer validation first
  - final full-input validation before MATLAB
- Keep default assumptions explicit.
- Keep functions small and explainable.
- Keep docs updated as the project changes.
- Commit stable checkpoints after testing.

### Testing

- Start testing pure backend functions before Streamlit or MATLAB.
- Use `pytest` for unit tests.
- Prioritize tests for `questionnaire_parser.py`, `questionnaire_state.py`, and `pvmaps_input_validator.py`.
- Test both valid and invalid values.
- Avoid MATLAB-dependent tests until the smaller functions are stable.
- Mark live API tests as `integration` so normal tests do not depend on the Purdue GenAI API.

### LLM Safety Principle

- The LLM should not invent simulation values silently.
- The LLM should not directly run MATLAB.
- The LLM should not decide whether a value is valid.
- The controlled backend should own validation, defaults, state, and PVMAPS execution.
- The LLM may help make questions more conversational, but code should still decide which required field is being requested.

## Future Requirements

### LLM Intake

- Use the LLM for extraction and question phrasing, not simulation.
- The LLM should convert messy user language into structured field-value pairs.
- The LLM should phrase required-field questions in simple, nontechnical language.
- Extracted values must still pass through the questionnaire parser and validators.
- The backend must remain responsible for state, validation, defaults, and PVMAPS execution.

Example:

```json
{
  "pitch": 10,
  "azimuth": 90
}
```

### Datasheet Extraction

- Allow users to upload or reference a solar panel datasheet.
- Use an LLM or parser to extract panel specs from the datasheet.
- Store extracted specs in a structured dictionary before using them.
- Validate extracted specs before using them in PVMAPS.

### Researcher Input Needed

- Ask researchers which input combinations are invalid or unsupported.
- Ask researchers which array configurations are realistic for different goals.
- Ask researchers what defaults are scientifically acceptable.
- Ask researchers how to handle panel orientation and module height consistently.

### Later Extensions

- RAG over project documents and research papers.
- Goal-based configuration suggestions.
- NASA POWER integration beyond geocoding, if needed.
- Crop-yield model integration.
- Map visualization.
- PDF report generation.

## Current Non-Goals

- The app does not yet optimize solar farm configuration.
- The app does not yet predict crop yield.
- The app does not yet use RAG.
- The app does not yet use a full LLM agent.
- The app does not yet handle all possible real-world solar design constraints.
