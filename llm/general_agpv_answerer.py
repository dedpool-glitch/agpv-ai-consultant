import json

from llm.prompts import LLM_SYSTEM_GENERAL_AGPV_PROMPT
from llm.client import call_llm
from llm.rag_formatting import format_retrieved_context
from llm.output_generator import format_input_field_descriptions


def answer_general_agpv_question(
    user_question,
    api_key,
    user_profile=None,
    location_context=None,
    pvmaps_state=None,
    latest_pvmaps_output=None,
    conversation_history=None,
    retrieved_context=None,
    latest_pvmaps_run=None,
):
    run_section = ""
    if latest_pvmaps_run:
        # Keep inputs, results, and origins tied to the same saved run.
        latest_pvmaps_output = latest_pvmaps_run.get("output")
        run_context = {
            key: latest_pvmaps_run.get(key)
            for key in ("label", "input", "input_provenance", "assumptions",
                        "overrides", "user_request", "location_context")
        }
        definitions = format_input_field_descriptions(latest_pvmaps_run.get("input"))
        run_section = (
            f"Latest completed run (actual inputs and recorded origins):\n"
            f"{json.dumps(run_context, indent=2)}\n\n{definitions}\n\n"
            "For questions about this run, use its inputs rather than the session baseline. "
            "Recorded selection rationales are proposals, not verified equipment clearance, "
            "site conditions, or optimality. If an origin or reason is absent, say it was "
            "not recorded; do not reconstruct it from typical values or earlier assistant claims.\n\n"
        )
    context_text = format_retrieved_context(retrieved_context)
    context_section = (
        f"Retrieved source excerpts (ground specific facts/figures in these where relevant; "
        f"don't force it if they're not actually relevant):\n{context_text}\n\n"
        if context_text
        else ""
    )

    messages = [
        {"role": "system", "content": LLM_SYSTEM_GENERAL_AGPV_PROMPT},
        {
            "role": "user",
            "content": (
                f"User question:\n{user_question}\n\n"
                f"User profile:\n{json.dumps(user_profile, indent=2)}\n\n"
                f"Location context:\n{json.dumps(location_context, indent=2)}\n\n"
                f"Session baseline (may differ from the latest run):\n{json.dumps(pvmaps_state, indent=2)}\n\n"
                f"{run_section}"
                f"Latest PVMAPS output:\n{json.dumps(latest_pvmaps_output, indent=2)}\n\n"
                f"Conversation history:\n{json.dumps(conversation_history, indent=2)}\n\n"
                f"{context_section}"
                "Answer the user's question using the available context."
            ),
        },
    ]

    response = call_llm(messages, api_key)
    return response.strip()
