"""Compare completed SIMPLE estimates saved in the current app session."""

import math
from datetime import date
from numbers import Real

from ui.simulation_result import run_location


def crop_runs(runs):
    """Keep runs with a usable final crop yield."""
    valid = []
    for run in runs:
        value = (run.get("crop_result") or {}).get("mean_grain_yield_t_ha")
        if isinstance(value, Real) and not isinstance(value, bool) and math.isfinite(value):
            valid.append(run)
    return valid


def crop_run_name(run, index):
    crop = run["crop_result"]
    setting = "with PV" if (run.get("output") or {}).get("yearly_yield") is not None else "without PV"
    return f"Run {index + 1} | {crop.get('crop', 'Crop').title()} | {crop.get('sowing_date', 'date unknown')} | {setting}"


def _pv_setup(run):
    if (run.get("output") or {}).get("yearly_yield") is None:
        return "No PV"
    array = (run.get("input") or {}).get("array") or {}
    config = array.get("config") or "Configuration unknown"
    pitch = array.get("pitch")
    return f"{config}, {pitch} m pitch" if pitch is not None else config


def crop_comparison_cautions(runs, selected):
    """Identify differences that affect interpretation of a yield difference."""
    chosen = [runs[index] for index in selected]
    crops = [run["crop_result"] for run in chosen]
    cautions = []
    if len({crop.get("crop") for crop in crops}) > 1:
        cautions.append("Crops differ; their yield values are not a like-for-like crop comparison.")
    if len({crop.get("sowing_date") for crop in crops}) > 1:
        cautions.append("Sowing dates differ; weather and growing-season timing may affect the difference.")
    sites = [((run.get("input") or {}).get("lat"), (run.get("input") or {}).get("lon")) for run in chosen]
    if any(lat is None or lon is None for lat, lon in sites):
        cautions.append("A site is missing for a selected run; a same-site comparison cannot be confirmed.")
    elif len(set(sites)) > 1:
        cautions.append("Sites differ; local weather may affect the difference.")
    pv_runs = [(run.get("output") or {}).get("yearly_yield") is not None for run in chosen]
    if len(set(pv_runs)) > 1:
        cautions.append("Some runs include PV shade and others do not; the difference may also reflect other changed inputs.")
    elif all(pv_runs):
        setups = [run.get("input") or {} for run in chosen]
        if any(any(item.get(key) != setups[0].get(key) for key in ("array", "module", "sim"))
               for item in setups[1:]):
            cautions.append("PV layouts, modules, or simulation settings differ; the crop difference cannot be attributed to one change unless other inputs match.")
    return cautions


def crop_comparison_rows(runs, selected, reference):
    baseline = runs[reference]["crop_result"]["mean_grain_yield_t_ha"]
    rows = []
    for index in selected:
        crop = runs[index]["crop_result"]
        value = crop["mean_grain_yield_t_ha"]
        sowing, maturity = crop.get("sowing_date"), crop.get("maturity_date")
        try:
            days = (date.fromisoformat(maturity) - date.fromisoformat(sowing)).days
        except (TypeError, ValueError):
            days = None
        rows.append({
            "Run": crop_run_name(runs[index], index) + (" (reference)" if index == reference else ""),
            "Site": run_location(runs[index]),
            "PV setup": _pv_setup(runs[index]),
            "Grain yield (t/ha)": round(value, 2),
            "Difference (t/ha)": round(value - baseline, 2),
            "Difference (%)": round(100 * (value - baseline) / baseline, 1) if baseline else None,
            "Estimated maturity": maturity or "Not available",
            "Days to maturity": days,
        })
    return rows


def combined_solar_rows(runs, selected, reference):
    """Return solar differences only when every selected crop run has comparable PV output."""
    outputs = [(runs[index].get("output") or {}) for index in selected]
    units = {str(output.get("yield_unit") or "").casefold() for output in outputs}
    if len(units) != 1 or "" in units or any(
        not isinstance(output.get("yearly_yield"), Real)
        or isinstance(output.get("yearly_yield"), bool)
        or not math.isfinite(output["yearly_yield"])
        for output in outputs
    ):
        return None
    baseline = (runs[reference].get("output") or {})["yearly_yield"]
    unit = "kWh/m" if next(iter(units)) == "kwh/m" else outputs[0]["yield_unit"]
    return [{
        "Run": f"Run {index + 1}" + (" (reference)" if index == reference else ""),
        "Annual solar yield": round((runs[index]["output"])["yearly_yield"], 2),
        "Unit": unit,
        "Difference": round(runs[index]["output"]["yearly_yield"] - baseline, 2),
        "Difference (%)": (
            round(100 * (runs[index]["output"]["yearly_yield"] - baseline) / baseline, 1)
            if baseline else None
        ),
    } for index in selected]


def render_crop_comparison(runs, key_prefix="guided"):
    runs = crop_runs(runs)
    if len(runs) < 2:
        return
    import matplotlib.pyplot as plt
    import streamlit as st

    with st.expander("Compare crop estimates", expanded=False):
        selected = st.multiselect(
            "Crop runs to compare", options=list(range(len(runs))),
            default=list(range(max(0, len(runs) - 2), len(runs))),
            format_func=lambda index: crop_run_name(runs[index], index),
            max_selections=4, key=f"{key_prefix}_crop_comparison_runs",
        )
        if len(selected) < 2:
            st.info("Select at least two crop runs to compare.")
            return
        reference = st.selectbox(
            "Reference crop run", options=selected,
            format_func=lambda index: crop_run_name(runs[index], index),
            key=f"{key_prefix}_crop_comparison_reference",
        )
        for caution in crop_comparison_cautions(runs, selected):
            st.warning(caution)
        st.dataframe(crop_comparison_rows(runs, selected, reference), hide_index=True,
                     use_container_width=True)
        st.caption("Differences use unrounded model results. Percentage difference is unavailable when the reference yield is zero. These are modeled grain yields, not measured harvests.")
        fig, ax = plt.subplots(figsize=(7.6, 2.9), layout="constrained")
        labels = [f"Run {index + 1}" for index in selected]
        values = [runs[index]["crop_result"]["mean_grain_yield_t_ha"] for index in selected]
        colors = ["#268477" if index == reference else "#74B9F0" for index in selected]
        ax.bar(labels, values, color=colors)
        ax.set_ylabel("Mean grain yield (t/ha)")
        ax.set_ylim(bottom=0)
        ax.grid(axis="y", alpha=0.2)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)
        try:
            st.pyplot(fig, width="content")
        finally:
            plt.close(fig)

        solar_rows = combined_solar_rows(runs, selected, reference)
        if solar_rows is not None:
            st.markdown("#### Solar output for these crop runs")
            st.dataframe(solar_rows, hide_index=True, use_container_width=True)
            solar_fig, solar_ax = plt.subplots(figsize=(7.6, 2.9), layout="constrained")
            solar_ax.bar(labels, [runs[index]["output"]["yearly_yield"] for index in selected],
                         color=colors)
            solar_ax.set_ylabel(f"Annual solar yield ({solar_rows[0]['Unit']})")
            solar_ax.set_ylim(bottom=0)
            solar_ax.grid(axis="y", alpha=0.2)
            solar_ax.set_axisbelow(True)
            solar_ax.spines[["top", "right"]].set_visible(False)
            try:
                st.pyplot(solar_fig, width="content")
            finally:
                plt.close(solar_fig)
            if solar_rows[0]["Unit"] == "kWh/m":
                st.caption("Solar energy is per meter of panel row, not total farm production. Crop yield is per hectare; the two values have different units and scales.")
        elif any((runs[index].get("output") or {}).get("yearly_yield") is not None
                 for index in selected):
            st.info("Solar yield differences require every selected run to have PV output in the same unit. Crop yields above can still be compared.")
