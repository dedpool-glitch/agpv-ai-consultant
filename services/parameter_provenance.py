"""Keep parameter origins separate from the values sent to PVMAPS."""

import copy

from constants import MANUAL_INPUT_TEXT


def build_parameter_provenance(values, recommendation, baseline, messages):
    sources = recommendation.get("parameter_sources")
    sources = sources if isinstance(sources, dict) else {}
    reasons = recommendation.get("justifications")
    reasons = reasons if isinstance(reasons, dict) else {}
    previous = baseline.get("parameter_provenance", {})
    previous = previous if isinstance(previous, dict) else {}
    user_texts = [
        message["content"] for message in messages
        if message.get("role") == "user" and isinstance(message.get("content"), str)
    ]
    provenance = {}

    for field, value in values.items():
        # Preserve the original reason for unchanged values across variant runs.
        if baseline.get(field) == value and isinstance(previous.get(field), dict):
            provenance[field] = copy.deepcopy(previous[field])
            continue

        reason = reasons.get(field)
        reason = reason.strip() if isinstance(reason, str) else ""
        claim = sources.get(field)
        claim = claim if isinstance(claim, dict) else {}
        quote = claim.get("user_quote")
        quote = quote.strip() if isinstance(quote, str) else ""
        source = "llm_recommended"
        evidence = None

        if field == "panel_model" and value == MANUAL_INPUT_TEXT["default_panel_model"]:
            source = "application_default"
            reason = "Module specifications come from the stored default PVMAPS panel record."
        elif baseline.get(field) == value:
            source = "unknown"
            reason = "Retained from an earlier state without recorded parameter origin."
        elif claim.get("source") == "user_provided" and quote and any(
            quote in text for text in user_texts
        ):
            source = "user_provided"
            evidence = quote

        provenance[field] = {
            "value": value,
            "source": source,
            "justification": reason or "No selection rationale was recorded.",
            "user_quote": evidence,
            "attribution": (
                "LLM interpretation; supporting quote matched a user message."
                if evidence else None
            ),
        }

    return provenance


def describe_assumptions(provenance):
    return [
        f"{field} = {item['value']} ({item['source']}): {item['justification']}"
        for field, item in provenance.items()
        if item["source"] != "user_provided"
    ]


def build_report_provenance(parameter_provenance, pvmaps_input):
    """Also account for module data and simulator defaults supplied by code."""
    panel = parameter_provenance["panel_model"]
    return {
        "parameters": copy.deepcopy(parameter_provenance),
        "module": {
            "value": copy.deepcopy(pvmaps_input["module"]),
            "source": (
                "application_default" if panel["source"] == "application_default"
                else "stored_panel_specs"
            ),
            "panel_model": panel["value"],
            "justification": "Loaded from data/panel_specs.json, not independently entered module values.",
        },
        "sim": {
            "value": copy.deepcopy(pvmaps_input["sim"]),
            "source": "application_default",
            "justification": "Simulator settings supplied by the guided input builder.",
        },
        "location": {
            "value": {"lat": pvmaps_input["lat"], "lon": pvmaps_input["lon"]},
            "source": "geocoder",
            "justification": "Coordinates resolved from the site's location text.",
        },
    }
