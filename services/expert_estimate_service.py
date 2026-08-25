from models.pvmaps.matlab_runner import run_pvmaps
from constants import PVMAPS_SCRIPT_PATH
from llm.output_generator import explain_output
from services.explainer_context import log_expert_explanation_result
from services.llm_trace import add_llm_trace


def run_expert_pvmaps_estimate(session_state, pvmaps_input, api_key):
    """
    Run PVMAPS on an expert-supplied, already-validated input and explain the
    result -- no Recommender, no baseline/diff logic, since the parameters
    are entirely under the expert's control. The explanation is grounded in
    the PVMAPS output/input descriptor field definitions (units, shapes),
    not RAG retrieval -- retrieval was dropped here because it was proving
    unreliable (silent backend failures indistinguishable from "no relevant
    match"), so explain_output no longer receives retrieved_context from
    this path. Every run still gets logged to a CSV (params, explanation,
    yield metrics) so results can be reviewed across many real runs, not
    just a handful of hardcoded test cases.
    """
    output = run_pvmaps(pvmaps_input, PVMAPS_SCRIPT_PATH)

    explanation = explain_output(
        output,
        api_key,
        pvmaps_input=pvmaps_input,
    )

    add_llm_trace(
        session_state,
        "expert_mode_pvmaps_run",
        input_summary={"pvmaps_input": pvmaps_input},
        output={
            "pvmaps_output": output,
            "explanation": explanation,
        },
        decision="expert_estimate_completed",
    )

    try:
        log_expert_explanation_result(pvmaps_input, output, None, [], explanation)
    except Exception:
        pass

    return output, explanation
