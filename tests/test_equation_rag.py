from rag.equations import equation_intent, equation_signals, expected_term_recall
from rag.rag_answerer import format_retrieved_context
from rag.pipeline import _page_ranges, search_collection_adaptive
from rag.vector_db import (
    attach_parent_context,
    clean_metadata,
    create_chunk_id,
    rerank_equation_results,
)


def test_equation_signals_detect_latex_and_symbolic_equality():
    assert equation_signals(r"BG = (Y_b - Y_m) / Y_m")["has_equation"]
    assert equation_signals(r"The model uses \\frac{a}{b}.")["has_equation"]
    assert not equation_signals("Row spacing affects shading and access.")["has_equation"]


def test_equation_intent_is_specific():
    assert equation_intent("What equation defines bifacial gain?")
    assert equation_intent("How is bifacial gain defined mathematically?")
    assert not equation_intent("What is bifacial gain?")


def test_equation_reranking_only_changes_equation_queries():
    results = [
        {"id": "text", "text": "A general explanation.", "metadata": {}, "distance": 0.2},
        {
            "id": "math",
            "text": "BG = (Y_b - Y_m) / Y_m",
            "metadata": {"has_equation": True, "record_type": "equation"},
            "distance": 0.3,
        },
    ]
    reranked = rerank_equation_results(results, "What equation defines bifacial gain?", 2)
    assert reranked[0]["id"] == "math"
    unchanged = rerank_equation_results(results, "What is bifacial gain?", 2)
    assert [item["id"] for item in unchanged] == ["text", "math"]


def test_equation_reranking_uses_distinctive_query_terms():
    results = [
        {
            "id": "dhi-only",
            "text": r"P = h I _ { D H I } (1 - sin(theta))",
            "metadata": {"has_equation": True, "record_type": "equation"},
            "distance": 0.1,
        },
        {
            "id": "unrelated-2",
            "text": "E = m c^2",
            "metadata": {"has_equation": True, "record_type": "equation"},
            "distance": 0.15,
        },
        {
            "id": "unrelated-3",
            "text": "x = y + z",
            "metadata": {"has_equation": True, "record_type": "equation"},
            "distance": 0.18,
        },
        {
            "id": "target",
            "text": r"I _ { G H I } = I _ { D N I } cos(theta) + I _ { D H I }",
            "metadata": {"has_equation": True, "record_type": "equation"},
            "distance": 0.2,
        },
    ]
    results.extend(
        {
            "id": f"unrelated-{index}",
            "text": f"value_{index} = constant_{index}",
            "metadata": {"has_equation": True, "record_type": "equation"},
            "distance": 0.2 + index / 100,
        }
        for index in range(4, 20)
    )

    reranked = rerank_equation_results(
        results,
        "What equation relates GHI to DNI and DHI?",
        2,
    )

    assert reranked[0]["id"] == "target"


def test_expected_term_recall():
    assert expected_term_recall("BG = rear/front", ["BG", "rear", "missing"]) == 2 / 3
    assert expected_term_recall("B G _ { E } = Y _ { B F }", ["BG_E", "Y_BF"]) == 1
    assert expected_term_recall("anything", []) is None


def test_equation_metadata_links_to_stable_parent_id():
    chunk = {
        "source": "papers/example.pdf",
        "title": "Example",
        "page": 4,
        "chunk_index": 2,
        "equation_index": 0,
        "record_key": "equation_2_0",
        "parent_record_key": "chunk_2",
        "record_type": "equation",
        "text": "Equation: E = mc^2",
        "equation_latex": "E = mc^2",
        "headings": ["Theory"],
        "has_equation": True,
        "equation_count": 1,
        "ingestion_profile": "equation_aware",
    }
    assert create_chunk_id(chunk) == "example_equation_2_0"
    metadata = clean_metadata(chunk)
    assert metadata["parent_id"] == "example_chunk_2"
    assert metadata["equation_latex"] == "E = mc^2"


def test_parent_context_is_attached_and_formatted():
    class FakeCollection:
        def get(self, ids, include):
            assert ids == ["example_chunk_2"]
            return {
                "ids": ["example_chunk_2"],
                "documents": ["This paragraph defines each variable."],
                "metadatas": [{"record_type": "context"}],
            }

    results = [{
        "id": "example_equation_2_0",
        "text": "Equation: E = mc^2",
        "metadata": {
            "record_type": "equation",
            "parent_id": "example_chunk_2",
            "title": "Example",
            "page": 4,
            "headings": "Theory",
        },
        "distance": 0.2,
    }]
    enriched = attach_parent_context(FakeCollection(), results)
    assert enriched[0]["parent_context"]["text"] == "This paragraph defines each variable."
    formatted = format_retrieved_context(enriched)
    assert "Equation: E = mc^2" in formatted
    assert "This paragraph defines each variable." in formatted


def test_page_ranges_support_resumable_ingestion(tmp_path):
    from pypdf import PdfWriter

    pdf_path = tmp_path / "sample.pdf"
    writer = PdfWriter()
    for _ in range(5):
        writer.add_blank_page(width=100, height=100)
    with pdf_path.open("wb") as stream:
        writer.write(stream)

    assert _page_ranges(pdf_path, 2) == [(1, 2), (3, 4), (5, 5)]
    assert _page_ranges(pdf_path, None) == [None]


def test_adaptive_search_uses_equation_aware_retrieval(monkeypatch):
    captured = {}

    def fake_search(collection_name, query, n_results, candidate_count=20, db_path=None):
        captured.update({
            "collection_name": collection_name,
            "query": query,
            "n_results": n_results,
            "db_path": db_path,
        })
        return [{"id": "result"}]

    monkeypatch.setattr("rag.pipeline.search_collection_equation_aware", fake_search)

    results = search_collection_adaptive(
        "equation_collection",
        "What equation defines bifacial gain?",
        n_results=4,
        db_path="db",
    )

    assert results == [{"id": "result"}]
    assert captured == {
        "collection_name": "equation_collection",
        "query": "What equation defines bifacial gain?",
        "n_results": 4,
        "db_path": "db",
    }
