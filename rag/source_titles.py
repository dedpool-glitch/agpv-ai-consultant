"""Stable user-facing titles for sources with legacy ingestion names."""

SOURCE_TITLE_ALIASES = {
    "alam book": "Principles of Solar Cells — M. A. Alam and M. R. Khan",
}


def display_source_title(title):
    """Return a polished title without changing stored Chroma metadata."""
    if not isinstance(title, str) or not title.strip():
        return "Unknown source"

    clean_title = title.strip()
    return SOURCE_TITLE_ALIASES.get(clean_title.casefold(), clean_title)