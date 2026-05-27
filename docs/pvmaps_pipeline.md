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

### `pvmaps_input_builder.py`

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

### `pvmaps_input_validator.py`

Defines:

```python
validate_pvmaps_input(data)
```

Checks bounds and allowed values for PVMAPS inputs, including latitude, longitude, tilt, azimuth, albedo, pitch, module efficiency, temperature coefficient, and tracking configuration.

### `pvmaps_mock_runner.py`

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

### `pvmaps_result_explainer.py`

Defines:

```python
explain_pvmaps_result(output)
```

Converts PVMAPS output into readable text for the user.

### `demo_mock_pipeline.py`

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

## MATLAB Integration Demo

The project now includes a real MATLAB PVMAPS runner and a Streamlit technical demo.

### Files

- `pvmaps_matlab_runner.py`
- `demo_matlab_pipeline.py`
- `app.py`

### Flow

```text
Streamlit/demo script
-> create PVMAPS input dictionary
-> validate input
-> start MATLAB Engine
-> set MATLAB path
-> input = initiate()
-> overwrite input fields
-> output = simulate(input)
-> extract yearly/monthly/daily yield
-> explain result
```

### Path Detail

`script_path` should point to the project root:

```text
D:/agpv-ai-consultant/PV-MAPS-main
```

not directly to:

```text
D:/agpv-ai-consultant/PV-MAPS-main/pvmaps
```

The MATLAB runner constructs the PVMAPS subpaths internally:

```text
script_path/pvmaps
script_path/pvmaps/data
script_path/pvmaps/lib/...
```

### Current Demo Defaults

The known-working demo configuration currently uses:

```text
array.config = tracking
module.cell_tech = AL_BSF
module.height = 4.8
module.stc_eff.direct = 21.8
module.stc_eff.diffuse = 21.8
module.tcoeff = 0.0041
array.tilt = 25
array.azimuth = 90
array.albedo = 0.3
array.pitch = 11
array.gsHeight = 0.5
array.elevation = 3
```

### Known Issue

The `fixed` configuration produced an internal PVMAPS error with the current default input set:

```text
Unrecognized function or variable 'I_gnd_x'
```

This does not necessarily mean fixed systems are unsupported. It means fixed systems need separate testing and possibly different compatible defaults.

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
