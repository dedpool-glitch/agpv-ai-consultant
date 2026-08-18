"""
Standalone test: run the full explain_output pipeline (query -> retrieval ->
LLM explanation) against sample PVMAPS configs, using mock PVMAPS output
instead of the real MATLAB engine -- so this can be tested in isolation from
the app, without needing MATLAB/PVMAPS installed.

For each sample config and each query style (narrow vs expanded), this:
1. Builds a retrieval query from the config.
2. Retrieves chunks from the papers/books collections.
3. Runs run_mock_pvmaps to get realistically-shaped (but static) output.
4. Calls explain_output with the full input, mock output, and retrieved context.
5. Writes params, query, retrieved chunk titles, and the generated explanation
   to a CSV so different prompt/query versions can be compared side by side.

Run with: python -m demos.test_output_explainer_retrieval

Requires PURDUE_GENAI_KEY in the environment (loaded via .env), since this
makes real LLM calls.
"""

import csv
import os
from pathlib import Path

from dotenv import load_dotenv

from llm.output_generator import explain_output
from models.pvmaps.input_builder import create_default_pvmaps_input
from models.pvmaps.mock_runner import run_mock_pvmaps
from rag.pipeline import retrieve_for_source


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "output_explainer_retrieval_results.csv"

# A fixed test location so results are comparable across runs.
TEST_LAT = 40.42
TEST_LON = -86.91

SAMPLE_RUNS = [
    {
        "label": "Fixed-tilt, tight pitch",
        "panel_model": "default values",
        "array_config": "fixed",
        "tilt": 30,
        "azimuth": 180,
        "pitch": 2,
        "albedo": 0.3,
        "gs_height": 0.5,
        "array_elevation": 3.0,
    },
    {
        "label": "Tracking, wide pitch",
        "panel_model": "default values",
        "array_config": "tracking",
        "tilt": 25,
        "azimuth": 90,
        "pitch": 11,
        "albedo": 0.3,
        "gs_height": 0.5,
        "array_elevation": 3.0,
    },
    {
        "label": "GSVBF (ground-sculpted vertical bifacial)",
        "panel_model": "default values",
        "array_config": "GSVBF",
        "tilt": 90,
        "azimuth": 90,
        "pitch": 4,
        "albedo": 0.5,
        "gs_height": 1.5,
        "array_elevation": 1.0,
    },
]


def build_narrow_query(run):
    return (
        f"solar farm energy yield for a {run['array_config']} array "
        f"with {run['tilt']} degree tilt and {run['pitch']}m row spacing"
    )


def build_expanded_query(run):
    bifacial_note = "bifacial vertical modules with ground sculpting" if run["array_config"] == "GSVBF" else ""
    return (
        f"solar farm energy yield for a {run['array_config']} array "
        f"with {run['tilt']} degree tilt, {run['azimuth']} degree azimuth, "
        f"{run['pitch']}m row spacing, {run['albedo']} ground albedo, "
        f"{run['gs_height']}m ground sculpting height, and {run['array_elevation']}m array elevation. "
        f"{bifacial_note}"
    ).strip()


QUERY_BUILDERS = {
    "narrow": build_narrow_query,
    "no_rag": None,  # baseline: no retrieval at all, for comparison
    "expanded": build_expanded_query,
}


def build_pvmaps_input(run):
    return create_default_pvmaps_input(
        lat=TEST_LAT,
        lon=TEST_LON,
        array_config=run["array_config"],
        tilt=run["tilt"],
        azimuth=run["azimuth"],
        albedo=run["albedo"],
        pitch=run["pitch"],
        gs_height=run["gs_height"],
        array_elevation=run["array_elevation"],
    )


def collect_rows(api_key):
    rows = []

    for run in SAMPLE_RUNS:
        pvmaps_input = build_pvmaps_input(run)
        mock_output = run_mock_pvmaps(pvmaps_input)

        for query_type, build_query in QUERY_BUILDERS.items():
            if build_query is None:
                query = None
                chunks = []
            else:
                query = build_query(run)
                chunks = retrieve_for_source("both", query, n_results=2)

            explanation = explain_output(
                mock_output,
                api_key,
                pvmaps_input=pvmaps_input,
                retrieved_context=chunks,
            )

            source_titles = "; ".join(
                f"{c.get('metadata', {}).get('title', 'Unknown')} (p.{c.get('metadata', {}).get('page', '?')}, d={c.get('distance'):.3f})"
                for c in chunks
            ) if chunks else None

            rows.append({
                "run_label": run["label"],
                "panel_model": run["panel_model"],
                "array_config": run["array_config"],
                "tilt": run["tilt"],
                "azimuth": run["azimuth"],
                "pitch": run["pitch"],
                "albedo": run["albedo"],
                "gs_height": run["gs_height"],
                "array_elevation": run["array_elevation"],
                "query_type": query_type,
                "query_text": query,
                "retrieved_sources": source_titles,
                "yearly_yield": mock_output["yearly_yield"],
                "yield_unit": mock_output["yield_unit"],
                "explanation": explanation,
            })

            print(f"Done: {run['label']} / {query_type}")

    return rows


def main():
    load_dotenv()
    api_key = os.getenv("PURDUE_GENAI_KEY")
    if not api_key:
        raise ValueError("PURDUE_GENAI_KEY is missing from the environment.")

    rows = collect_rows(api_key)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "run_label", "panel_model", "array_config", "tilt", "azimuth", "pitch",
        "albedo", "gs_height", "array_elevation",
        "query_type", "query_text", "retrieved_sources",
        "yearly_yield", "yield_unit", "explanation",
    ]

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
