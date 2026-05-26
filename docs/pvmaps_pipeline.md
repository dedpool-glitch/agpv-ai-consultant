# PVMAPS Pipeline

## Current Goal

Build a small Python pipeline that prepares PVMAPS inputs, validates them, runs a mock PVMAPS simulation, and explains the result.

This is the controlled backend skeleton that will later sit underneath the LLM agent.

## Current Flow

```text
create_default_pvmaps_input()
-> validate_pvmaps_input()
-> run_mock_pvmaps()
-> explain_pvmaps_result()
```

## Files

### `pvmaps_default_input.py`

Defines:

```python
create_default_pvmaps_input(lat, lon)
```

Creates a default PVMAPS-style input dictionary.

The dictionary includes:

```text
lat
lon
module.cell_tech
module.height
module.stc_eff.direct
module.stc_eff.diffuse
module.tcoeff
array.config
array.tilt
array.azimuth
array.albedo
array.pitch
array.gsHeight
array.elevation
```

### `pvmaps_validators.py`

Defines:

```python
validate_pvmaps_input(data)
```

Checks bounds and allowed values for PVMAPS inputs, including latitude, longitude, tilt, azimuth, albedo, pitch, module efficiency, temperature coefficient, and tracking configuration.

### `pvmaps_mock_run.py`

Defines:

```python
run_mock_pvmaps(pvmaps_input)
```

Returns mock PVMAPS output shaped like the real MATLAB output.

Current output fields:

```text
yearly_yield
monthly_yield
daily_yield
yield_unit
warnings
assumptions
```

### `pvmaps_explain_output.py`

Defines:

```python
explain_pvmaps_result(pvmaps_input, output)
```

Converts PVMAPS output into readable text for the user.

### `pvmaps_input_example.py`

Runs the full example pipeline.

It creates default input, validates it, runs the mock PVMAPS function, and prints a readable explanation.

## Current Assumptions

- PVMAPS input is represented as a nested Python dictionary.
- MATLAB PVMAPS is not connected yet.
- Mock output is used until the real simulator is available.
- PVMAPS is treated as the trusted model.
- We validate inputs before simulation.
- We are not scientifically validating PVMAPS outputs yet.
- Later, the final LLM/RAG response should be checked before it is shown to the user.

## Design Principle

```text
LLM handles conversation.
Code handles numeric mapping and validation.
PVMAPS handles solar calculation.
Explanation layer turns results into readable output.
```

## Next Steps

- Add farmer-friendly input mapping.
- Add NASA POWER data lookup.
- Replace mock runner with MATLAB PVMAPS runner.
- Add LLM-guided conversation.
- Add RAG-based support for research claims and assumptions.
