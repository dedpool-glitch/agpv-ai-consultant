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
- RAG pipeline for CEED paper retrieval and paper-grounded answers.
- Background PVMAPS simulation when a solar-yield estimate is useful.
- Deterministic validation before MATLAB/PVMAPS is called.
- Simple result visualization and explanation.

The prototype currently combines solar-yield estimation with an early CEED
paper RAG pipeline. Crop-yield modeling, economic analysis, multi-run
simulation comparison, and multi-model decision support are planned extensions.

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
models/pvmaps/  PVMAPS input builders, validators, runner, and bundled runtime
questionnaire/  questionnaire state, parsing, and PVMAPS conversion helpers
llm/            LLM client, prompts, extraction, questions, and candidate config
services/       geocoding, panel specs, NASA lookup, reporting, and app services
demos/          isolated command-line demo pipelines
tests/          unit and integration tests
docs/           design notes, progress notes, and project documentation
rag/            document loading, chunking, Chroma retrieval, and RAG answering
```

## Prerequisites

**MATLAB and MATLAB Engine for Python are required just to launch this app --
not only to run a PVMAPS simulation.** `models/pvmaps/matlab_runner.py` does
`import matlab.engine` at module load time, and that module is imported
eagerly as soon as `app.py` starts, before any mode is even selected. Without
a working MATLAB Engine for Python install, the app will fail on startup.

- Install a licensed copy of MATLAB.
- Install the matching `matlabengine` PyPI package for your exact MATLAB
  release (each `matlabengine` version supports exactly one MATLAB release --
  see the pin note in `requirements.txt`, and check the "Required MathWorks
  Products" on each release's PyPI page if your MATLAB version differs).
- A Purdue GenAI Studio API key (see `docs/AgPV_Student_How_To_Guide.docx` for
  how to get one) -- this can be entered directly in the app on first launch,
  no `.env` file required.

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

Optionally, create a `.env` file in the repository root if you don't want to
re-enter your API key every time you launch the app:

```text
PURDUE_GENAI_KEY=your_api_key_here
```

The `.env` file should not be committed. If you skip this, the app will ask
for your API key in the browser on first launch instead.

## Running the App

```powershell
streamlit run app.py
```

See Prerequisites above -- MATLAB and a matching MATLAB Engine for Python
install are required for the app to start at all, not just to run PVMAPS.

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

## Development Targets

- Integrate the CEED paper RAG pipeline into the app through a routing step, so
  RAG is used only for research/background questions.
- Refactor the chat flow so PVMAPS is one optional tool, not the required end
  point of every conversation.
- Extend the backend so the app can run and compare multiple PVMAPS simulations
  during one consultation.
- Prepare for a quick solar-yield ML model as a second estimate tool.
- Deploy the prototype for lab access, preferably through Purdue RCAC or a lab
  server.
