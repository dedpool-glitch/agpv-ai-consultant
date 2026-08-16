from constants import PVMAPS_SCRIPT_PATH
from llm.output_generator import explain_output
from pvmaps.matlab_runner import run_pvmaps
from services.explainer_context import log_expert_explanation_result, retrieve_output_explanation_context
from services.llm_trace import add_llm_trace


def run_expert_pvmaps_estimate(session_state, pvmaps_input, api_key):
    """
    Run PVMAPS on an expert-supplied, already-validated input, retrieve
    supporting context from the papers/books collections based on that same
    input, and explain the result grounded in it -- no Recommender, no
    baseline/diff logic, since the parameters are entirely under the expert's
    control. Every run also gets logged to a CSV (params, query, retrieved
    sources, explanation, yield metrics) so results can be reviewed across
    many real runs, not just a handful of hardcoded test cases.
    """
    output = run_pvmaps(pvmaps_input, PVMAPS_SCRIPT_PATH)

    query, retrieved_chunks = retrieve_output_explanation_context(pvmaps_input)
    explanation = explain_output(
        output,
        api_key,
        pvmaps_input=pvmaps_input,
        retrieved_context=retrieved_chunks,
    )

    add_llm_trace(
        session_state,
        "expert_mode_pvmaps_run",
        input_summary={"pvmaps_input": pvmaps_input, "retrieval_query": query},
        output={
            "pvmaps_output": output,
            "explanation": explanation,
            "retrieved_count": len(retrieved_chunks),
        },
        decision="expert_estimate_completed",
    )

    try:
        log_expert_explanation_result(pvmaps_input, output, query, retrieved_chunks, explanation)
    except Exception:
        pass

    return output, explanation
