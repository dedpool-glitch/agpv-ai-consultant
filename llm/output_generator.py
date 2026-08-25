import json

from constants import MONTH_LABELS
from llm.client import call_llm
from llm.prompts import LLM_SYSTEM_OUTPUT_EXPLANATION_PROMPT
from llm.rag_formatting import format_retrieved_context
from models.pvmaps.descriptor import (
    describe_output_shape,
    get_pvmaps_input_descriptors,
    get_pvmaps_output_descriptors,
)

# Low, not zero -- keeps answers close to deterministic without making every
# response byte-identical, since this is meant to read as a written
# explanation rather than a templated one.
EXPLANATION_TEMPERATURE = 0.2


def format_output_field_descriptions(pvmaps_output):
    """
    Describe each field actually present in pvmaps_output using the model
    descriptor (models/pvmaps/pvmaps.json) -- name, unit, shape, and
    description -- so the LLM is told what a field means instead of having
    to infer it from the field name alone. Restricted to fields the
    descriptor documents with a real unit, and to keys that are actually
    present in this run's output, so nothing gets stated about fields
    (e.g. opt_power, power_mat) the descriptor doesn't yet document reliably.
    """
    if not isinstance(pvmaps_output, dict):
        return ""

    lines = []
    for field in get_pvmaps_output_descriptors():
        field_id = field["id"]
        if field_id not in pvmaps_output:
            continue
        if field_id != "yield_unit" and not field.get("unit"):
            # Undocumented unit (opt_power, power_mat, opt_p, ...) -- skip
            # rather than let the LLM say anything confident about it.
            continue

        unit = field.get("unit")
        unit_text = f", unit: {unit}" if unit else ""
        shape_text = describe_output_shape(field)
        lines.append(
            f"- {field_id} ({field['name']}): {field['description']} "
            f"[shape: {shape_text}{unit_text}]"
        )

    if not lines:
        return ""

    return (
        "Field definitions for this output (use these, not the field names, to "
        "understand what each value means -- an array shaped as "
        "'simulation_block' has exactly 12 entries, one per calendar month, "
        "never one per day; do not state or imply a specific calendar day's "
        "value from a 12-entry array):\n" + "\n".join(lines)
    )


def _get_nested_input_value(pvmaps_input, field_id):
    value = pvmaps_input
    for part in field_id.split("."):
        if not isinstance(value, dict) or part not in value:
            return None, False
        value = value[part]
    return value, True


def format_input_field_descriptions(pvmaps_input):
    """
    Describe each input field's meaning and current value using the model
    descriptor -- mirrors format_output_field_descriptions, but for the
    input side. Without this, the LLM only sees a bare nested JSON dump
    with no explanation of what a field means or when it's actually
    relevant. Concretely, this is what let the LLM falsely claim gsHeight
    "isn't a parameter in this simulation" when it's present in every run
    -- it's just not physically meaningful unless array.config is GSVBF,
    and nothing told the model that distinction.
    """
    if not isinstance(pvmaps_input, dict):
        return ""

    lines = []
    for field in get_pvmaps_input_descriptors():
        field_id = field["id"]
        value, present = _get_nested_input_value(pvmaps_input, field_id)
        if not present:
            continue
        unit = field.get("unit")
        unit_text = f" {unit}" if unit else ""
        lines.append(f"- {field_id} ({field['name']}) = {value}{unit_text}: {field['description']}")

    if not lines:
        return ""

    return (
        "Field definitions for this input (every field is always present, "
        "even ones that aren't physically relevant to this run's "
        "array.config -- e.g. gsHeight is only used for GSVBF arrays but is "
        "still submitted as a value for fixed/tracking runs; never claim a "
        "field is missing or absent just because it isn't used for this "
        "config -- say it isn't used for this configuration instead):\n"
        + "\n".join(lines)
    )


def describe_monthly_extremes(pvmaps_output):
    """
    Compute the highest/lowest month directly from monthly_yield in Python,
    instead of asking the LLM to correctly read the right index out of a
    12-element array itself -- that's exactly the kind of arithmetic-over-
    an-array task the model can (and has) gotten wrong, including inventing
    a "two simulation blocks" framing that doesn't exist in the data at all.
    Handed to the LLM as a stated fact, not something to re-derive.
    """
    if not isinstance(pvmaps_output, dict):
        return ""

    monthly_yield = pvmaps_output.get("monthly_yield")
    if not isinstance(monthly_yield, list) or len(monthly_yield) != 12:
        return ""

    yield_unit = pvmaps_output.get("yield_unit", "")
    max_index = max(range(12), key=lambda i: monthly_yield[i])
    min_index = min(range(12), key=lambda i: monthly_yield[i])

    return (
        "Computed facts about monthly_yield (use these exact values and month "
        "names verbatim if asked about the highest/lowest month -- do not "
        "recompute or re-derive this yourself, and do not describe any month "
        "as having multiple values or \"blocks\"; each month is exactly one "
        "number):\n"
        f"- Highest: {MONTH_LABELS[max_index]}, {monthly_yield[max_index]:.2f} {yield_unit}\n"
        f"- Lowest: {MONTH_LABELS[min_index]}, {monthly_yield[min_index]:.2f} {yield_unit}"
    )


def explain_output(pvmaps_output, api_key, user_profile=None, pvmaps_input=None, retrieved_context=None):
    context_text = format_retrieved_context(retrieved_context)
    context_section = (
        f"Retrieved source excerpts (reference briefly if they help explain this result; "
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
        {"role": "system", "content": LLM_SYSTEM_OUTPUT_EXPLANATION_PROMPT},
        {
            "role": "user",
            "content": (
                f"PVMAPS output:\n{json.dumps(pvmaps_output, indent=2)}\n\n"
                f"{field_section}"
                f"{extremes_section}"
                f"Full PVMAPS input (the configuration that was actually run):\n{json.dumps(pvmaps_input, indent=2)}\n\n"
                f"{input_field_section}"
                f"User Profile:\n{json.dumps(user_profile, indent=2)}\n\n"
                f"{context_section}"
                "Generate a clear, simple explanation of the PVMAPS output that can be easily understood by the user."
            ),
        },
    ]

    llm_explanation = call_llm(messages, api_key, temperature=EXPLANATION_TEMPERATURE)
    return llm_explanation.strip()
