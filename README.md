This project contains code related to creating an AI consultant for farmers in the AGPV domain.

# AgPV AI Consultant

AI-powered decision support tool for agrivoltaic planning.

## Goal

Help farmers and researchers estimate solar/crop tradeoffs for agrivoltaic systems using climate data, PVMAPS-style solar modeling, crop modeling, and LLM-based explanation.

## Core Flow

User input
→ validate inputs
→ fetch NASA POWER climate data
→ prepare PVMAPS inputs
→ run/lookup solar model
→ validate outputs
→ explain results

## Planned Components

- Streamlit UI
- Input schemas and validators
- NASA POWER data access
- PVMAPS runner
- Output validator
- LLM explanation layer
- RAG over papers/notes
- Report generation

## MVP

- Farmer-friendly input form
- Location to latitude/longitude
- NASA climate lookup
- Mock PVMAPS output
- Plain-English explanation