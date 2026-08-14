from constants import PVMAPS_SCRIPT_PATH
from llm.output_generator import explain_output
from pvmaps.matlab_runner import run_pvmaps
from services.llm_trace import add_llm_trace


def run_expert_pvmaps_estimate(session_state, pvmaps_input, api_key):
    """
    Run PVMAPS on an expert-supplied, already-validated input and explain the
    result -- deliberately with no Recommender, no RAG grounding, and no
    baseline/diff logic. This is a controlled path meant to test explain_output
    in isolation: the parameters are entirely under the expert's control, so
    any issue with the resulting explanation is attributable to the explainer
    itself, not to an upstream parameter recommendation.
    """
    output = run_pvmaps(pvmaps_input, PVMAPS_SCRIPT_PATH)
    explanation = explain_output(output, api_key, pvmaps_input=pvmaps_input)

    add_llm_trace(
        session_state,
        "expert_mode_pvmaps_run",
        input_summary={"pvmaps_input": pvmaps_input},
        output={"pvmaps_output": output, "explanation": explanation},
        decision="expert_estimate_completed",
    )

    return output, explanation
