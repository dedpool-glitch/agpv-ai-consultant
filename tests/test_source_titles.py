from llm.rag_formatting import format_retrieved_context
from rag.pipeline import summarize_retrieved_chunks
from rag.source_titles import display_source_title


FORMAL_TITLE = "Principles of Solar Cells — M. A. Alam and M. R. Khan"


def test_legacy_book_name_has_formal_display_title():
    assert display_source_title("alam book") == FORMAL_TITLE
    assert display_source_title("  Alam Book  ") == FORMAL_TITLE


def test_unrecognized_title_is_preserved():
    assert display_source_title("Solar Cells") == "Solar Cells"


def test_formatted_context_and_trace_summary_use_display_title():
    chunks = [{
        "text": "Example evidence",
        "metadata": {"title": "alam book", "page": 31},
        "distance": 0.2,
    }]
    assert FORMAL_TITLE in format_retrieved_context(chunks)
    assert summarize_retrieved_chunks(chunks)[0]["title"] == FORMAL_TITLE