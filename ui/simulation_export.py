"""Download the exact saved simulation data without an LLM request."""

from services.simulation_workbook import build_simulation_workbook


def render_simulation_exports(runs, key_prefix):
    if not runs:
        return
    import streamlit as st

    st.download_button(
        "Download results",
        data=build_simulation_workbook(runs),
        file_name="pvmaps_results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        icon=":material/download:",
        key=f"{key_prefix}_results_workbook",
    )
