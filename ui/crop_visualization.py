"""Shared PV + SIMPLE visuals for Guided and Expert result cards."""

from ui.array_visualization import create_array_configuration_figure


def crop_visualization_data(run):
    """Align the 101 crop positions with annual ground-light totals."""
    crop = run.get("crop_result") or {}
    yields = crop.get("grain_yield_t_ha_by_position") or []
    if not yields:
        return None
    low_yield_index = min(range(len(yields)), key=yields.__getitem__)
    light_days = ((run.get("output") or {}).get("ground_light") or {}).get("light_mj_m2") or []
    annual_light = None
    low_light_index = None
    if light_days and all(len(day) == len(yields) for day in light_days):
        annual_light = [sum(day[index] for day in light_days) for index in range(len(yields))]
        low_light_index = min(range(len(annual_light)), key=annual_light.__getitem__)
    return {
        "yields": yields,
        "lowest_yield_index": low_yield_index,
        "annual_light": annual_light,
        "lowest_light_index": low_light_index,
    }


def render_crop_with_pv(run):
    import matplotlib.pyplot as plt
    import streamlit as st

    crop = run["crop_result"]
    st.subheader("Crop yield with PV")
    st.metric("Mean grain yield", f"{crop['mean_grain_yield_t_ha']:.2f} t/ha")
    st.write(f"{crop['crop'].title()} sown {crop['sowing_date']}; estimated maturity {crop['maturity_date']}.")

    if crop.get("open_sky_grain_yield_t_ha") is not None:
        with st.expander("Optional: compare with modeled open sky"):
            difference = crop.get("difference_from_open_sky_t_ha")
            percent = crop.get("difference_from_open_sky_percent")
            difference_text = f"{difference:+.2f} t/ha" if difference is not None else "not available"
            percent_text = f" ({percent:+.1f}%)" if percent is not None else ""
            st.write(
                f"Open-sky crop yield: {crop['open_sky_grain_yield_t_ha']:.2f} t/ha. "
                f"Difference with PV: {difference_text}{percent_text}."
            )
            st.caption(
                "This isolates the model's light-input effect using the same crop, "
                "temperature, and sowing date. It does not predict every field effect "
                "or decide whether the PV layout is worthwhile."
            )

    st.markdown("#### Array layout and crop response")
    data = crop_visualization_data(run)
    if data is None:
        st.info("A ground-position crop profile is not available for this run.")
        return
    yields = data["yields"]
    low_index = data["lowest_yield_index"]
    annual_light = data["annual_light"]
    light_low = data["lowest_light_index"]

    if annual_light:
        st.info(
            f"PV-MAPS predicts the least annual ground light at index {light_low}; "
            f"SIMPLE predicts the lowest crop yield at index {low_index} "
            f"({yields[low_index]:.2f} t/ha). The uneven light profile helps "
            "explain the uneven crop yield. Index numbers are not mapped to "
            "the exact footprint beneath either drawn panel."
        )
    with st.expander("Array layout", expanded=False):
        layout_fig = create_array_configuration_figure(run["input"])
        layout_fig.set_size_inches(7.8, 2.6)
        try:
            st.pyplot(layout_fig, width="content")
        finally:
            plt.close(layout_fig)
        st.caption("Conceptual PV-MAPS row layout; proportions are not to scale.")

    count = 2 if annual_light else 1
    fig, axes = plt.subplots(count, 1, figsize=(7.8, 4.0 if annual_light else 2.6),
                             sharex=True, layout="constrained")
    if annual_light:
        light_ax, yield_ax = axes
        light_ax.plot(range(len(annual_light)), annual_light, color="#d49b2a", linewidth=2)
        light_ax.set_ylabel("Ground light\n(MJ/m²/year)")
        light_ax.scatter([light_low], [annual_light[light_low]], color="#9b5622")
    else:
        yield_ax = axes
    yield_ax.plot(range(len(yields)), yields, color="#74B9F0", linewidth=2)
    yield_ax.scatter([low_index], [yields[low_index]], color="#c45c4d")
    yield_ax.set_xlim(0, len(yields) - 1)
    yield_ax.set_ylim(bottom=0)
    yield_ax.set_xlabel("Ground position index (0–100; not meters)")
    yield_ax.set_ylabel("Grain yield (t/ha)")
    for ax in (axes if annual_light else [axes]):
        ax.grid(axis="y", alpha=0.2)
        ax.spines[["top", "right"]].set_visible(False)
    try:
        st.pyplot(fig, width="content")
    finally:
        plt.close(fig)
    st.caption(
        "These curves use the same 101 ordered ground positions. The array "
        "drawing explains the row geometry, but PV-MAPS does not provide "
        "verified physical coordinates for the indexed yield positions. "
        "The mean above averages the 101 crop predictions."
    )
    with st.expander("How to read this crop estimate"):
        st.write(
            "Lower parts of the curve indicate positions where the modeled "
            "ground light supports less grain yield. This is a model estimate "
            "for the selected crop, site, sowing date, and PV layout; it is "
            "not a measured field harvest."
        )
        st.write("Model assumptions: " + "; ".join(crop.get("assumptions") or []))
