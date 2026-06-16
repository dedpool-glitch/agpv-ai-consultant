# PVMAPS Questionnaire Guide

## Purpose

This document guides the LLM questionnaire that collects PVMAPS inputs from a non-expert user.

The app handles location before the questionnaire starts:

```text
user enters location
-> LLM questionnaire collects remaining PVMAPS inputs
```

## Core Principle

```text
LLM handles conversation and intent.
Code handles numeric defaults, validation, and PVMAPS execution.
PVMAPS handles the solar simulation.
```

The LLM should collect information, ask clarifying questions, summarize assumptions, and return structured output. It should not invent simulation values.

## Conversation Rules

- Ask one question at a time.
- Avoid technical jargon when talking to farmers or non-expert users.
- Use short explanations to explain terms unfamiliar to the user.
- Do not invent numeric values.
- If the user does not know a value, mark it as unknown and use an approved default later.
- Confirm all assumptions before running PVMAPS.
- Separate user-provided values from assumed/default values.
- If a user gives a vague answer, ask one clarifying follow-up.
- If the user gives a panel company but no model, ask for the model number or datasheet.
- If the user does not have a datasheet/model, ask whether a representative/default module should be used.


## Inputs To Collect

### Panel / Module Inputs

These are the first module parameters:

```text
module.cell_tech
module.height
module.stc_eff.direct
module.stc_eff.diffuse
module.tcoeff
```

Preferred source:

```text
solar panel datasheet
```

Ask the user:

```text
Do you know the solar panel company and model number, or do you have a datasheet?
```

If the user provides a company/model or datasheet, extract:

```text
cell technology
module height
module efficiency
temperature coefficient of Pmax
```

Notes:

- `module.stc_eff.direct` and `module.stc_eff.diffuse` should use module efficiency as a percent.
- If only one module efficiency is available, use it for both direct and diffuse efficiency unless researchers specify otherwise.
- Datasheets often list temperature coefficient as `%/deg C`, such as `-0.35 %/deg C`.
- PVMAPS currently uses positive magnitude for `tcoeff`, so `-0.35 %/deg C` becomes `0.0035`.
- `module.cell_tech` must map to one of the PVMAPS-supported technology labels.

Supported PVMAPS technology labels:

```text
AL_BSF
BI_PERC
SHJ
PVK_SI_2T
PVK_SI_4T
SHJ_NN
```

### Array / Design Inputs

These fields describe the solar farm layout:

```text
array.config
array.tilt
array.azimuth
array.albedo
array.pitch
array.gsHeight
array.elevation
```

Ask about these in user-friendly language.

#### `array.config`

Meaning:

```text
solar array configuration
```

Allowed values:

```text
fixed
tracking
GSVBF
```

Ask:

```text
Do you know whether the panels are fixed, tracking, or vertical bifacial with ground sculpting?
```

If the user is unsure, mark as unknown and use a researcher-approved default later.

#### `array.tilt`

Meaning:

```text
panel angle relative to the ground
```

Ask:

```text
Do you know the panel tilt angle in degrees?
```

If unknown, mark as defaulted.

#### `array.azimuth`

Meaning:

```text
panel orientation
```

Current PVMAPS note:

```text
90 = east/west facing
180 = north/south facing
```

Ask:

```text
Do you know whether the panel rows are oriented east-west or north-south?
```

If unknown, mark as defaulted.

#### `array.albedo`

Meaning:

```text
ground reflectiveness under/around the panels
```

Ask only if needed:

```text
Do you know the ground surface type under the panels, such as soil, grass, gravel, or reflective material?
```

If unknown, use a researcher-approved default.

#### `array.pitch`

Meaning:

```text
distance between rows of panels in meters
```

Ask:

```text
Do you know the row spacing between panel rows?
```

If the user gives feet, convert to meters before simulation.

If unknown, mark as defaulted.

#### `array.gsHeight`

Meaning:

```text
ground sculpting height
```

Ask only if `array.config = GSVBF` or if the user mentions ground sculpting:

```text
Does this design include ground sculpting? If yes, do you know the sculpting height?
```

If not applicable, default to `0` unless researchers specify otherwise.

#### `array.elevation`

Meaning:

```text
height at which panels are mounted above ground
```

Ask:

```text
Do you know how high the panels are mounted above the ground?
```

If unknown, mark as defaulted.

## Recommended Question Flow

After the app has already collected location:

1. Confirm the matched location.
2. Ask whether the user has a panel company/model or datasheet.
3. Ask the array configuration: fixed, tracking, or GSVBF.
4. Ask for row spacing/pitch if known.
5. Ask for panel mounting height/elevation if known.
6. Ask for tilt/orientation if known.
7. Ask about ground surface/albedo only if needed.
8. Summarize user-provided values and assumptions.
9. Return structured JSON.

## Structured Output

Longer term, the LLM may return a larger structured output before PVMAPS runs.

Example:

```json
{
  "panel": {
    "company": null,
    "model": null,
    "datasheet_available": false,
    "cell_tech": null,
    "module_height": null,
    "stc_eff_direct": null,
    "stc_eff_diffuse": null,
    "tcoeff": null
  },
  "array": {
    "config": "tracking",
    "tilt": null,
    "azimuth": null,
    "albedo": null,
    "pitch": 11.0,
    "gs_height": null,
    "elevation": 3.0
  },
  "assumptions": [
    "Location coordinates were provided by the app geocoder.",
    "Unknown module parameters should be filled using approved defaults."
  ],
  "missing_fields": [
    "module.cell_tech",
    "module.height",
    "module.stc_eff.direct",
    "module.stc_eff.diffuse",
    "module.tcoeff"
  ]
}
```

Current implementation is smaller and safer. Code chooses the next required field, the LLM phrases the question, and the LLM extracts one requested field at a time:

```text
questionnaire state chooses field
-> LLM generates user-friendly question
-> user answers
-> LLM extracts value for that same field
-> parser validates value
-> state updates
```

```json
{
  "field": "pitch",
  "value": 10
}
```

Then Python validates and stores that value.

## Handoff To Code

After the LLM returns structured output:

```text
structured output
-> questionnaire parser validates/parses individual answers
-> code stores validated structured state
-> code fills approved defaults
-> code validates input combinations
-> PVMAPS runs
```

The LLM should not directly run PVMAPS or bypass validation.

## Current Backend Implementation

The questionnaire backend has been started in code and is now organized into packages.

### `questionnaire/state.py`

Tracks what the questionnaire has collected.

Responsibilities:

```text
create empty questionnaire state
track required fields
return the next missing question
update state from user answers
apply defaults for missing values
record assumptions when values are defaulted
```

This acts as the checklist that the future LLM/questionnaire will follow.

### `questionnaire/parser.py`

Validates one submitted answer before it is stored in questionnaire state.

Current responsibilities:

```text
convert numeric text to float
reject invalid array configuration answers
reject unknown panel model answers
check tilt, albedo, pitch, ground sculpting height, and elevation rules
restrict azimuth to 90 or 180 for the current demo
reuse shared validation messages from constants.py where possible
```

This is important because the final PVMAPS validator only runs after a full input dictionary exists. During the chat/questionnaire flow, the app only has one field answer at a time.

### `questionnaire/to_pvmaps.py`

Converts completed questionnaire state into a PVMAPS input dictionary.

Responsibilities:

```text
read selected panel model
load panel specs from panel_specs.json
combine panel specs + array answers + lat/lon
call create_default_pvmaps_input(...)
return model-ready PVMAPS input
```

### `llm/parameter_extractor.py`

Extracts one questionnaire field from a natural-language user response.

Current flow:

```text
field + question + user response
-> Purdue GenAI Studio API
-> JSON-like extraction
-> questionnaire parser validates the extracted value
```

The LLM does not update questionnaire state directly. It only proposes the extracted value.

### `llm/question_generator.py`

Generates a natural-language question for the next required questionnaire field.

Current flow:

```text
field + questionnaire state
-> Purdue GenAI Studio API
-> one short user-friendly question
```

The code still decides which field is needed. The LLM only decides how to phrase the question.

### `demos/questionnaire_pipeline.py`

Tests the questionnaire backend without Streamlit or an LLM.

Current flow:

```text
create questionnaire state
simulate a few user answers
apply defaults for missing fields
convert state to PVMAPS input
validate input
run mock PVMAPS
print explanation and assumptions
```

This proves:

```text
questionnaire answers
-> structured state
-> PVMAPS input dictionary
-> simulation output
```

without depending on the Streamlit UI.

## Open Researcher Questions

- Which module defaults should be used when no datasheet is available?
- How should common datasheet cell technologies map to PVMAPS labels?
- Which array configuration should be the default when the user is unsure?
- What are valid default values for `fixed`, `tracking`, and `GSVBF`?
- Should azimuth always be limited to 90 and 180 for this project, or should the simulator support more orientations later?
- Which input combinations should be blocked?
- Which input combinations should only produce warnings?
- Should `stc_eff.direct` and `stc_eff.diffuse` usually be equal?
- How should albedo be chosen for common ground surfaces?
