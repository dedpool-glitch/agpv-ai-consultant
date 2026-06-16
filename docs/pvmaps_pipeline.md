# PVMAPS Pipeline

## Purpose

This document describes the controlled PVMAPS pipeline used by the Streamlit demo and future LLM-assisted questionnaire.

The key idea is:

```text
LLM helps collect/interpret inputs
Python validates and structures inputs
MATLAB PVMAPS performs the solar simulation
Python explains the result
```

## Current Package

PVMAPS-related Python code now lives in:

```text
pvmaps/
```

Files:

```text
pvmaps/input_builder.py
pvmaps/input_validator.py
pvmaps/mock_runner.py
pvmaps/matlab_runner.py
pvmaps/result_explainer.py
```

## Main Flow

```text
create_default_pvmaps_input(...)
-> validate_pvmaps_input(...)
-> run_pvmaps(...) or run_mock_pvmaps(...)
-> explain_pvmaps_result(...)
```

In the app, questionnaire mode adds earlier steps:

```text
questionnaire state selects next required field
-> llm.question_generator.generate_question(...)
user natural-language answer
-> llm.parameter_extractor.extract_questionnaire_parameter(...)
-> questionnaire.parser.parse_questionnaire_answer(...)
-> questionnaire.state.update_questionnaire_state(...)
-> questionnaire.to_pvmaps.build_pvmaps_input_from_questionnaire(...)
-> validate_pvmaps_input(...)
-> run_pvmaps(...)
```

## Input Builder

File:

```text
pvmaps/input_builder.py
```

Defines:

```python
create_default_pvmaps_input(...)
```

Creates a nested Python dictionary that mirrors the MATLAB PVMAPS input struct.

## Input Validator

File:

```text
pvmaps/input_validator.py
```

Defines:

```python
validate_pvmaps_input(data)
```

Checks the final complete PVMAPS input dictionary before MATLAB runs.

Current checks:

```text
allowed cell technology
allowed array configuration
module height > 0
efficiency ranges
temperature coefficient range
tilt range
azimuth allowed values
albedo range
pitch > 0
ground sculpting height >= 0
array elevation >= 0
latitude/longitude ranges
```

Current azimuth assumption:

```text
90 = east-west
180 = north-south
```

## Mock Runner

File:

```text
pvmaps/mock_runner.py
```

Returns mock PVMAPS output shaped like the real MATLAB output.

Purpose:

```text
test pipeline behavior without launching MATLAB
```

## MATLAB Runner

File:

```text
pvmaps/matlab_runner.py
```

Defines:

```python
run_pvmaps(pvmaps_input, script_path)
```

Flow:

```text
start MATLAB Engine
set MATLAB working folder/path
call initiate()
overwrite selected input fields
call simulate(input)
extract yearly/monthly/daily yield
return Python dictionary
```

Important path:

```text
script_path = D:/agpv-ai-consultant/PV-MAPS-main
```

## Result Explainer

File:

```text
pvmaps/result_explainer.py
```

Turns PVMAPS output into readable text using:

```text
yearly_yield
monthly_yield
yield_unit
assumptions
```

## Current Demo Defaults

Known-working configuration:

```text
module.cell_tech = AL_BSF
module.height = 4.8
module.stc_eff.direct = 21.8
module.stc_eff.diffuse = 21.8
module.tcoeff = 0.0041
array.config = tracking
array.tilt = 25
array.azimuth = 90
array.albedo = 0.3
array.pitch = 11
array.gsHeight = 0.5
array.elevation = 3
```

## Known Issue

The `fixed` configuration produced:

```text
Unrecognized function or variable 'I_gnd_x'
```

This does not necessarily mean fixed systems are unsupported. It means:

```text
fixed + current defaults
```

is not yet confirmed as a valid input combination.

## Demo Scripts

Command-line demos now live in:

```text
demos/
```

Examples:

```powershell
python -m demos.mock_pipeline
python -m demos.questionnaire_pipeline
python -m demos.matlab_pipeline
```

Use the MATLAB demo only when MATLAB and PV-MAPS paths are available.

## Design Boundary

```text
LLM = question phrasing and language extraction
questionnaire code = state and answer validation
PVMAPS code = input construction, final validation, simulation
MATLAB PVMAPS = scientific solar calculation
```

This boundary is intentional so the LLM does not silently invent or approve simulation values.
