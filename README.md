# AgPV AI Consultant

An AI-assisted agrivoltaic planning prototype built around Purdue's MATLAB
PVMAPS solar-yield simulator.

## Goal

Help farmers and researchers explore solar-farm configurations through
farmer-friendly input collection, climate context, validated PVMAPS
simulations, and plain-language explanations.

The current prototype estimates solar yield. Crop-yield modeling and combined
solar/crop decision support are future extensions.

## Current Flows

### Guided Input

```text
location and user profile
-> manual input or LLM-assisted questionnaire
-> answer and full-input validation
-> MATLAB PVMAPS
-> monthly/yearly yield
-> LLM-generated explanation
```

### Experimental Candidate Generation

```text
natural-language location
-> geocoding
-> nearest NASA climate grid lookup
-> LLM proposes one PVMAPS candidate configuration with justifications
-> deterministic validation
-> PVMAPS-ready input
-> append candidate and location to CSV history
```

The candidate is a model-generated proposal, not a proven optimum.

## Technology

- Python and Streamlit
- Purdue GenAI Studio API
- MATLAB Engine and PVMAPS
- pandas and SciPy
- geopy
- pytest

## Project Structure

```text
app.py          Streamlit interface
pvmaps/         PVMAPS builders, validators, runners, and result explanation
questionnaire/  state, answer parsing, and PVMAPS conversion
llm/            API client, extraction, questions, output, and candidates
services/       geocoding, panel specs, NASA lookup, and CSV reporting
demos/          isolated command-line pipelines
tests/          unit and integration tests
docs/           design and progress documentation
```
### Updates:
- revamped UI flow, questions can be asked after PVMAPS too.
- allowed LLMs to decide on parameter values on their own (with appropriate justification)
- LLMs can answer AGPV related questions more freely now.
- PVMAPS can run only once. 
- refactored main app script
- made UI changes
