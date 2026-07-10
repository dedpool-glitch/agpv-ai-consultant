# AgPV AI Consultant

AI-assisted agrivoltaic planning prototype for the CEED group at Purdue.

This repository contains a Streamlit application that combines conversational
intake, validated PVMAPS inputs, MATLAB/PVMAPS simulation, and LLM-generated
plain-language explanations.

## Repository Contents

The current prototype supports:

- A user-facing AgPV consultation flow.
- Location-aware solar-yield estimation.
- LLM-assisted discussion of AgPV planning tradeoffs.
- Background PVMAPS simulation when a solar-yield estimate is useful.
- Deterministic validation before MATLAB/PVMAPS is called.
- Simple result visualization and explanation.

The prototype currently focuses on solar-yield estimation. Crop-yield modeling,
economic analysis, RAG over CEED papers, and multi-model decision support are
planned future extensions.

## Current Application Flow

```text
user profile and optional site location
-> conversational AgPV intake
-> LLM decides whether a PVMAPS estimate is useful
-> LLM proposes a candidate PVMAPS configuration
-> Python validation checks the candidate inputs
-> MATLAB/PVMAPS runs in the background
-> monthly/yearly solar yield is shown
-> conversation continues with the result available as context
```

## Technology Stack

- Python
- Streamlit
- Purdue GenAI Studio API
- MATLAB Engine for Python
- PVMAPS
- pandas
- SciPy
- geopy
- pytest

## Project Structure

```text
app.py          Streamlit application entry point
pvmaps/         PVMAPS input builders, validators, runner, and output handling
questionnaire/  questionnaire state, parsing, and PVMAPS conversion helpers
llm/            LLM client, prompts, extraction, questions, and candidate config
services/       geocoding, panel specs, NASA lookup, reporting, and app services
demos/          isolated command-line demo pipelines
tests/          unit and integration tests
docs/           design notes, progress notes, and project documentation
```

## Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

Install Python dependencies:

```powershell
pip install -r requirements.txt
```

Create a `.env` file in the repository root:

```text
GENAI_STUDIO_API_KEY=your_api_key_here
```

The `.env` file should not be committed.

## Running the App

```powershell
streamlit run app.py
```

PVMAPS requires MATLAB, MATLAB Engine for Python, and the local PVMAPS files to
be available on the machine running the app.

## Testing

Run tests with:

```powershell
pytest
```

## Data and Large Files

Large local datasets, MATLAB data files, generated outputs, API keys, and
environment-specific files should not be committed directly unless they are
small, public, and required for the repository to run.

Use Git LFS or a shared lab storage location for large files when needed.

## Current Status

This is an active research prototype. The main development goal is to turn
PVMAPS into one background tool within a broader AgPV assistant, rather than
making the conversation end after one simulation.
