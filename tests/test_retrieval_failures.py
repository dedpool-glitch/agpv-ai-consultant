import pytest

from rag.pipeline import retrieve_for_source


def test_all_collection_failures_raise_diagnostic(monkeypatch):
    def fail(collection_name, *_args, **_kwargs):
        raise OSError(f"cannot query {collection_name}")

    monkeypatch.setattr("rag.pipeline.search_collection_adaptive", fail)

    with pytest.raises(RuntimeError) as error:
        retrieve_for_source("both", "temperature efficiency")

    message = str(error.value)
    assert "ceed_group_papers_equations_v1" in message
    assert "ceed_group_books_equations_v1" in message
    assert "OSError" in message


def test_one_collection_failure_keeps_other_results(monkeypatch):
    def query(collection_name, *_args, **_kwargs):
        if "papers" in collection_name:
            raise OSError("papers unavailable")
        return [{"text": "book result", "metadata": {}}]

    monkeypatch.setattr("rag.pipeline.search_collection_adaptive", query)

    assert retrieve_for_source("both", "temperature efficiency") == [
        {"text": "book result", "metadata": {}}
    ]
