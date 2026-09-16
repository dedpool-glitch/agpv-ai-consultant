"""Display saved simulation facts independently of the LLM explanation."""

import math
from numbers import Real

from constants import MONTH_LABELS
from models.pvmaps.descriptor import get_pvmaps_input_descriptors


PARAMETER_KEYS = {
    "array.config": "array_config",
    "array.tilt": "tilt",
    "array.azimuth": "azimuth",
    "array.albedo": "albedo",
    "array.pitch": "pitch",
    "array.gsHeight": "gs_height",
    "array.elevation": "array_elevation",
}
SOURCE_LABELS = {
    "user_provided": "User-provided (interpreted from chat)",
    "llm_recommended": "LLM recommendation",
    "application_default": "Application default",
    "stored_panel_specs": "Stored panel specifications",
    "geocoder": "Location lookup",
    "expert_form": "Submitted through expert form",
}


def format_value(value):
    if value is None:
        return "Not available"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, Real):
        if not math.isfinite(value):
            return "Not available"
        if value != 0 and abs(value) < 0.01:
            return f"{value:.3g}"
        return f"{value:,.2f}".rstrip("0").rstrip(".")
    return str(value)


def configuration_rows(run):
    """Values come from actual model inputs; provenance supplies origins only."""
    inputs = run.get("input") or {}
    provenance = run.get("input_provenance") or {}
    parameters = provenance.get("parameters") or {}
    rows = []
    for field in get_pvmaps_input_descriptors():
        field_id = field["id"]
        value = inputs
        for key in field_id.split("."):
            value = value.get(key) if isinstance(value, dict) else None
        if value is None:
            continue
        group = field_id.split(".")[0]
        if field_id in PARAMETER_KEYS:
            origin = parameters.get(PARAMETER_KEYS[field_id]) or {}
        else:
            origin = provenance.get("location" if group in ("lat", "lon") else group) or {}
        source = origin.get("source") or provenance.get("source")
        notes = origin.get("justification") or ""
        if field_id == "array.gsHeight" and inputs.get("array", {}).get("config") != "GSVBF":
            notes = "Not used for this array configuration."
        if field_id == "array.tilt" and inputs.get("array", {}).get("config") in ("tracking", "GSVBF"):
            notes = "Recorded input; not used for this array configuration."
        rows.append({
            "Parameter": field["name"],
            "Value": format_value(value),
            "Unit": "unitless" if field.get("unit") == "1" else field.get("unit") or "",
            "Origin": SOURCE_LABELS.get(source, "Origin not recorded"),
            "Recorded rationale / notes": notes,
        })
    return rows


def run_location(run):
    location = run.get("location_context") or {}
    address = location.get("confirmed_address") or location.get("site_location")
    if address:
        return address
    inputs = run.get("input") or {}
    if inputs.get("lat") is not None and inputs.get("lon") is not None:
        return f"Latitude {format_value(inputs['lat'])}, longitude {format_value(inputs['lon'])}"
    return "Location not recorded"


def render_simulation_result(run):
    import matplotlib.pyplot as plt
    import streamlit as st

    output = run.get("output") or {}
    unit = output.get("yield_unit") or "unit unavailable"
    st.markdown(f"### {run.get('label') or 'Solar-yield estimate'}")
    st.write(run_location(run))
    st.metric("Simulated annual yield", f"{format_value(output.get('yearly_yield'))} {unit}")
    if unit == "kWh/m":
        st.caption("Annual electricity generated per meter of solar-panel row, not per square meter or for the whole farm.")

    monthly = output.get("monthly_yield")
    if isinstance(monthly, list) and len(monthly) == 12 and all(
        isinstance(value, Real) and not isinstance(value, bool) and math.isfinite(value)
        for value in monthly
    ):
        st.markdown("#### Monthly yield")
        fig, ax = plt.subplots(figsize=(9, 3.5), layout="constrained")
        ax.bar(MONTH_LABELS, monthly, color="#268477")
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
        ax.set_ylabel(f"Energy ({unit})")
        ax.set_ylim(bottom=0)
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_axisbelow(True)
        ax.grid(axis="y", alpha=0.2)
        try:
            st.pyplot(fig, use_container_width=True)
        finally:
            plt.close(fig)
    else:
        st.info("A complete monthly-yield series is not available for this run.")

    warnings = output.get("warnings") or []
    if isinstance(warnings, str):
        warnings = [warnings]
    for warning in warnings:
        st.warning(str(warning))

    with st.expander("Configuration and assumptions", expanded=False):
        rows = configuration_rows(run)
        if rows:
            st.dataframe(rows, hide_index=True, use_container_width=True)
        else:
            st.write("Configuration not recorded for this run.")
        st.caption("Values are from the configuration submitted to PVMAPS. Selection rationales are recorded explanations, not proof of optimality or farming suitability.")
        if (run.get("input_provenance") or {}).get("source") == "expert_form":
            st.caption("The expert form may include retained prefilled values; individual edits were not tracked.")
