import json

from llm.client import call_llm
from llm.output_generator import (
    EXPLANATION_TEMPERATURE,
    describe_monthly_extremes,
    format_input_field_descriptions,
    format_output_field_descriptions,
)
from llm.prompts import LLM_SYSTEM_EXPERT_FOLLOWUP_PROMPT
from llm.rag_formatting import format_retrieved_context


def answer_expert_followup_question(
    user_question,
    api_key,
    pvmaps_input,
    pvmaps_output,
    explanation,
    conversation_history=None,
    retrieved_context=None,
):
    """
    Answer a follow-up question about one specific expert-mode run -- unlike
    explain_output (which dropped RAG for reliability reasons), this is a
    live conversation the user can push back on, so grounding it with
    retrieved context is worth the same risk that a one-shot explanation
    isn't: a wrong citation here can be immediately questioned, not just
    read as authoritative.
    """
    context_text = format_retrieved_context(retrieved_context)
    context_section = (
        f"Retrieved source excerpts (ground specific facts/figures in these where relevant; "
        f"only attribute a specific claim to a source if the excerpt actually supports it):\n{context_text}\n\n"
        if context_text
        else ""
    )

    field_descriptions = format_output_field_descriptions(pvmaps_output)
    field_section = f"{field_descriptions}\n\n" if field_descriptions else ""

    monthly_extremes = describe_monthly_extremes(pvmaps_output)
    extremes_section = f"{monthly_extremes}\n\n" if monthly_extremes else ""

    input_field_descriptions = format_input_field_descriptions(pvmaps_input)
    input_field_section = f"{input_field_descriptions}\n\n" if input_field_descriptions else ""

    messages = [
        {"role": "system", "content": LLM_SYSTEM_EXPERT_FOLLOWUP_PROMPT},
        {
            "role": "user",
            "content": (
                f"PVMAPS input (the configuration that was run):\n{json.dumps(pvmaps_input, indent=2)}\n\n"
                f"{input_field_section}"
                f"PVMAPS output:\n{json.dumps(pvmaps_output, indent=2)}\n\n"
                f"{field_section}"
                f"{extremes_section}"
                f"Explanation already given to the user:\n{explanation}\n\n"
                f"Conversation so far:\n{json.dumps(conversation_history, indent=2)}\n\n"
                f"{context_section}"
                f"User's follow-up question:\n{user_question}\n\n"
                "Answer the user's follow-up question."
            ),
        },
    ]

    response = call_llm(messages, api_key, temperature=EXPLANATION_TEMPERATURE)
    return response.strip()
