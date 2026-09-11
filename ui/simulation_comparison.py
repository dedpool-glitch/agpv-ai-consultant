"""Compare saved runs without another simulation or LLM request."""

import math
from numbers import Real

from constants import MONTH_LABELS
from models.pvmaps.descriptor import get_pvmaps_input_descriptors
from ui.simulation_result import format_value, run_location


def _number(value):
    return isinstance(value, Real) and not isinstance(value, bool) and math.isfinite(value)


def _input(run, path):
    value = run.get("input") or {}
    for part in path.split("."):
        value = value.get(part) if isinstance(value, dict) else None
    return value


def run_name(run, index):
    return f"Run {index + 1} | {_input(run, 'array.config') or 'Configuration unknown'} | {format_value(_input(run, 'array.pitch'))} m pitch"


def yield_difference(run, reference):
    output, baseline = run.get("output") or {}, reference.get("output") or {}
    value, base = output.get("yearly_yield"), baseline.get("yearly_yield")
    if not output.get("yield_unit") or output.get("yield_unit") != baseline.get("yield_unit"):
        return None, None
    if not _number(value) or not _number(base):
        return None, None
    difference = value - base
    return difference, (100 * difference / base if base != 0 else None)


def changed_inputs(runs, selected):
    rows = []
    for field in get_pvmaps_input_descriptors():
        values = [_input(runs[index], field["id"]) for index in selected]
        if all(value == values[0] for value in values):
            continue
        row = {"Parameter": field["name"], "Unit": field.get("unit") or ""}
        row.update({f"Run {index + 1}": format_value(value) for index, value in zip(selected, values)})
        rows.append(row)
    return rows


def comparison_cautions(runs, selected):
    inputs = [runs[index].get("input") or {} for index in selected]
    cautions = []
    if any(item.get("lat") is None or item.get("lon") is None for item in inputs):
        cautions.append("Location is missing for a selected run; a same-site comparison cannot be confirmed.")
    elif len({(item["lat"], item["lon"]) for item in inputs}) > 1:
        cautions.append("Selected runs use different locations. Yield differences may reflect location as well as configuration.")
    for group, label in (("module", "Module specifications"), ("sim", "Simulation settings")):
        if any(group not in item for item in inputs):
            cautions.append(f"{label} are missing for a selected run.")
        elif any(item[group] != inputs[0][group] for item in inputs[1:]):
            cautions.append(f"{label} differ between selected runs; this is not an isolated layout comparison.")
    return cautions


def render_simulation_comparison(runs):
    if len(runs) < 2:
        return
    import matplotlib.pyplot as plt
    import streamlit as st

    with st.expander("Compare simulations", expanded=False):
        summary = []
        for index, run in enumerate(runs):
            output = run.get("output") or {}
            summary.append({
                "Run": run_name(run, index), "Location": run_location(run),
                "Annual yield": format_value(output.get("yearly_yield")),
                "Unit": output.get("yield_unit") or "Not recorded",
                "Tilt (degrees)": format_value(_input(run, "array.tilt")),
                "Albedo": format_value(_input(run, "array.albedo")),
            })
        st.dataframe(summary, hide_index=True, use_container_width=True)

        selected = st.multiselect(
            "Runs to compare", options=list(range(len(runs))),
            default=list(range(max(0, len(runs) - 2), len(runs))),
            format_func=lambda index: run_name(runs[index], index),
            max_selections=4, key="comparison_runs",
        )
        if len(selected) < 2:
            st.info("Select at least two runs to compare.")
            return
        reference = st.selectbox(
            "Reference run", options=selected,
            format_func=lambda index: run_name(runs[index], index),
            key="comparison_reference",
        )
        for caution in comparison_cautions(runs, selected):
            st.warning(caution)

        deltas = []
        for index in selected:
            delta, percent = yield_difference(runs[index], runs[reference])
            output = runs[index].get("output") or {}
            deltas.append({
                "Run": f"Run {index + 1}" + (" (reference)" if index == reference else ""),
                "Annual yield": format_value(output.get("yearly_yield")),
                "Unit": output.get("yield_unit") or "Not recorded",
                "Difference from reference": format_value(delta),
                "Difference (%)": format_value(percent),
            })
        st.markdown("#### Annual yield comparison")
        st.dataframe(deltas, hide_index=True, use_container_width=True)
        st.caption("Differences use unrounded saved results. Percentage differences are unavailable for a zero reference yield; incompatible or missing units cannot be compared.")

        units = {(runs[index].get("output") or {}).get("yield_unit") for index in selected}
        if len(units) == 1 and None not in units and "" not in units:
            unit = next(iter(units))
            fig, ax = plt.subplots(figsize=(9, 4), layout="constrained")
            plotted = 0
            colors = ["#268477", "#c45538", "#7358a6", "#2676b6"]
            for position, index in enumerate(selected):
                monthly = (runs[index].get("output") or {}).get("monthly_yield")
                if not isinstance(monthly, list) or len(monthly) != 12 or not all(_number(v) for v in monthly):
                    st.info(f"Run {index + 1} has no complete monthly series; omitted from the chart.")
                    continue
                ax.plot(MONTH_LABELS, monthly, marker="o", color=colors[position],
                        label=f"Run {index + 1}", linestyle=["-", "--", "-.", ":"][position])
                plotted += 1
            if plotted >= 2:
                ax.set_ylabel(f"Monthly energy ({unit})")
                ax.set_ylim(bottom=0)
                ax.legend()
                ax.grid(axis="y", alpha=0.2)
                ax.spines[["top", "right"]].set_visible(False)
                plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
                st.markdown("#### Monthly yield comparison")
                try:
                    st.pyplot(fig, use_container_width=True)
                finally:
                    plt.close(fig)
            else:
                plt.close(fig)
            if unit == "kWh/m":
                st.caption("Energy per meter of solar-panel row. Higher yield here does not establish higher yield per acre, total farm production, or profit.")
        else:
            st.warning("Selected runs have missing or different yield units; no combined chart is shown.")

        st.markdown("#### Changed inputs")
        changes = changed_inputs(runs, selected)
        if changes:
            st.dataframe(changes, hide_index=True, use_container_width=True)
            if len(changes) > 1:
                st.caption("Multiple inputs changed. The yield difference cannot be attributed to one parameter alone.")
        else:
            st.write("No differences in recorded model inputs.")
