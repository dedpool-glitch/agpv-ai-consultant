"""Streamlit control for downloading a readable conversation transcript."""

from services.conversation_export import build_conversation_markdown


def render_conversation_export(messages, pvmaps_runs, key_prefix):
    if not messages:
        return
    import streamlit as st

    st.download_button(
        "Download conversation",
        data=build_conversation_markdown(messages, pvmaps_runs),
        file_name="agpv_conversation.md",
        mime="text/markdown",
        icon=":material/download:",
        key=f"{key_prefix}_conversation_markdown",
    )
