import csv
from datetime import datetime
from pathlib import Path

from rag.pipeline import retrieve_for_source, summarize_retrieved_chunks


EXPERT_EVAL_LOG_PATH = Path(r"D:\agpv-ai-consultant\outputs\expert_mode_explainer_eval_log.csv")

LOG_FIELDNAMES = [
    "timestamp", "lat", "lon", "panel_model", "cell_tech", "array_config",
    "tilt", "azimuth", "albedo", "pitch", "gs_height", "array_elevation",
    "query", "retrieved_sources", "yearly_yield", "yield_unit", "explanation",
]


def build_output_explanation_query(pvmaps_input):
    """
    Build a retrieval query from a run's actual configuration -- there's no
    user message to work with here (explain_output runs right after a
    simulation completes), so the query is built from the array's own
    parameters instead, the same way retrieve_recommendation_context already
    does for the Recommender when there's no user message.
    """
    array = pvmaps_input["array"]
    bifacial_note = "bifacial vertical modules with ground sculpting" if array["config"] == "GSVBF" else ""
    return (
        f"solar farm energy yield for a {array['config']} array "
        f"with {array['tilt']} degree tilt, {array['azimuth']} degree azimuth, "
        f"{array['pitch']}m row spacing, {array['albedo']} ground albedo, "
        f"{array['gsHeight']}m ground sculpting height, and {array['elevation']}m array elevation. "
        f"{bifacial_note}"
    ).strip()


def retrieve_output_explanation_context(pvmaps_input, n_results=2):
    """
    Best-effort retrieval to ground the output explanation. Any failure here
    just means explain_output falls back to no context, same as before this
    existed -- never breaks the actual run.
    """
    query = build_output_explanation_query(pvmaps_input)
    try:
        chunks = retrieve_for_source("both", query, n_results=n_results)
    except Exception:
        chunks = []
    return query, chunks


def log_expert_explanation_result(pvmaps_input, output, query, retrieved_chunks, explanation):
    """
    Append one row to the expert-mode explainer eval log: every input
    parameter, the retrieval query, which sources were retrieved, the
    resulting explanation, and the yield metrics. Appends (not overwrites)
    so this accumulates across every real expert-mode run over time.
    """
    module = pvmaps_input["module"]
    array = pvmaps_input["array"]

    source_summary = "; ".join(
        f"{c['title']} (p.{c['page']}, d={c['distance']:.3f})"
        for c in summarize_retrieved_chunks(retrieved_chunks)
    ) if retrieved_chunks else None

    row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "lat": pvmaps_input["lat"],
        "lon": pvmaps_input["lon"],
        "panel_model": module.get("cell_tech"),
        "cell_tech": module.get("cell_tech"),
        "array_config": array["config"],
        "tilt": array["tilt"],
        "azimuth": array["azimuth"],
        "albedo": array["albedo"],
        "pitch": array["pitch"],
        "gs_height": array["gsHeight"],
        "array_elevation": array["elevation"],
        "query": query,
        "retrieved_sources": source_summary,
        "yearly_yield": output.get("yearly_yield"),
        "yield_unit": output.get("yield_unit"),
        "explanation": explanation,
    }

    EXPERT_EVAL_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    file_exists = EXPERT_EVAL_LOG_PATH.exists()

    with open(EXPERT_EVAL_LOG_PATH, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=LOG_FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
