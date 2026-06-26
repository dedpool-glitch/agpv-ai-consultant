# Model Interface Design

## Purpose

This document defines how simulation models should connect to the AgPV AI consultant.

The project currently supports PVMAPS, but the long-term goal is to support additional models such as SIMPLE for crop yield. The code should therefore treat PVMAPS as the first model module, not as the only possible model.

## Core Idea

Each model should follow the same controlled boundary:

```text
user conversation
-> structured inputs
-> validation
-> model runner
-> structured output
-> user-facing explanation
```

The LLM may help collect inputs and explain outputs, but it should not invent model inputs, bypass validation, or calculate scientific outputs itself.

The experimental candidate-generation flow allows the LLM to propose inputs,
but every proposed value must still pass the same deterministic validators
before it can reach a simulation model.

## Current PVMAPS Interface

PVMAPS currently follows this pattern:

```text
questionnaire/manual inputs
-> PVMAPS input dictionary
-> validate_pvmaps_input(...)
-> run_pvmaps(...)
-> PVMAPS output dictionary
-> explain_pvmaps_result(...)
```

Important files:

```text
pvmaps/input_builder.py
pvmaps/input_validator.py
pvmaps/matlab_runner.py
pvmaps/mock_runner.py
pvmaps/result_explainer.py
```

An experimental alternative input path is:

```text
location
-> NASA climate summary
-> LLM candidate configuration + concise justifications
-> validate_candidate_config(...)
-> build_pvmaps_input_from_questionnaire(...)
-> validate_pvmaps_input(...)
-> PVMAPS-ready input
```

The candidate is a baseline proposal, not a proven optimized configuration.

## Recommended Pattern For Future Models

A future model package should have a similar structure:

```text
models/simple/
  input_builder.py
  input_validator.py
  matlab_runner.py
  mock_runner.py
  result_explainer.py
```

or, if the project keeps model folders at the top level:

```text
simple/
  input_builder.py
  input_validator.py
  matlab_runner.py
  mock_runner.py
  result_explainer.py
```

The exact folder name can change later. The important part is the interface.

## Required Model Functions

Each model should expose these responsibilities:

```text
build input
validate input
run model
normalize output
explain output
```

For example:

```python
build_simple_input(...)
validate_simple_input(simple_input)
run_simple(simple_input, script_path)
explain_simple_result(simple_output)
```

## Why This Helps

This avoids rewriting the whole app when a new model is added.

The app should only need to know:

```text
which model is being used
what inputs that model needs
how to call the model runner
how to display the model result
```

The model-specific details should stay inside that model's package.

## LLM Role With Multiple Models

As more models are added, the LLM can help with:

```text
asking model-specific questions
extracting structured inputs from conversation
explaining validated model outputs in plain language
helping route a user request to the correct model
proposing candidate inputs when the application requests a design suggestion
```

The backend should still control:

```text
required fields
validation rules
defaults
model execution
scientific output values
acceptance or rejection of LLM-generated candidates
```

## LLM-Generated Output Summaries

A useful next feature is to let the LLM generate the final user-facing explanation from structured model output.

The safe pattern is:

```text
PVMAPS output dictionary
-> code selects key numbers
-> LLM receives only validated output + assumptions
-> LLM writes a clear explanation
```

The LLM should not change the numbers. It should only explain them.

Example input to the LLM:

```json
{
  "model": "PVMAPS",
  "yearly_yield": 1918.7,
  "yield_unit": "kWh/m^2",
  "monthly_yield": [102.1, 115.8, 171.1],
  "assumptions": [
    "array.config was defaulted to tracking"
  ]
}
```

Expected LLM role:

```text
Summarize the result clearly.
Mention important assumptions.
Avoid inventing additional claims.
Avoid presenting the result as financial or crop-yield advice.
```

## Future SIMPLE Integration

SIMPLE will likely need different inputs than PVMAPS, such as crop type, planting date, weather variables, and crop-management assumptions.

That means SIMPLE should have its own:

```text
questionnaire fields
input validator
runner
result explainer
```

But the overall app architecture can stay similar:

```text
conversation -> structured state -> model input -> model output -> explanation
```

## Current Design Decision

PVMAPS remains the first stable scientific model. The next experiment is:

```text
general-LLM candidate
vs.
research-paper/RAG-guided candidate
```

Both paths should use the same validation, PVMAPS execution, and result
reporting interfaces so only the source of the proposed configuration changes.
