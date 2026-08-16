import json

from llm.client import call_llm
from llm.prompts import LLM_SYSTEM_OUTPUT_EXPLANATION_PROMPT
from llm.rag_formatting import format_retrieved_context


def explain_output(pvmaps_output, api_key, user_profile=None, pvmaps_input=None, retrieved_context=None):
    context_text = format_retrieved_context(retrieved_context)
    context_section = (
        f"Retrieved source excerpts (reference briefly if they help explain this result; "
        f"only attribute a specific claim to a source if the excerpt actually supports it):\n{context_text}\n\n"
        if context_text
        else ""
    )

    messages = [
        {"role": "system", "content": LLM_SYSTEM_OUTPUT_EXPLANATION_PROMPT},
        {
            "role": "user",
            "content": (
                f"PVMAPS output:\n{json.dumps(pvmaps_output, indent=2)}\n\n"
                f"Full PVMAPS input (the configuration that was actually run):\n{json.dumps(pvmaps_input, indent=2)}\n\n"
                f"User Profile:\n{json.dumps(user_profile, indent=2)}\n\n"
                f"{context_section}"
                "Generate a clear, simple explanation of the PVMAPS output that can be easily understood by the user."
            ),
        },
    ]

    llm_explanation = call_llm(messages, api_key)
    return llm_explanation.strip()
