import json

from services import conversation_log


def _read_single_row(path):
    rows = path.read_text(encoding="utf-8").splitlines()
    assert len(rows) == 1
    return json.loads(rows[0])


def test_log_uses_stable_schema_without_retrieval(tmp_path, monkeypatch):
    log_path = tmp_path / "conversation_log.jsonl"
    monkeypatch.setattr(conversation_log, "CONVERSATION_LOG_PATH", log_path)
    monkeypatch.setattr(conversation_log, "REMOTE_LOG_ENDPOINT_URL", "")

    conversation_log.log_conversation_turn(
        "session-1",
        "guided",
        "general_question",
        "What is agrivoltaics?",
        "It combines agriculture and solar generation.",
    )

    row = _read_single_row(log_path)
    assert row["rag_enabled"] is False
    assert row["rag_source"] == "none"
    assert row["retrieved_count"] == 0
    assert row["retrieved_chunks"] == []
    assert row["retrieval_query"] is None
    assert row["model_name"] is None
    assert row["error"] is None


def test_log_records_retrieval_and_evaluation_metadata(tmp_path, monkeypatch):
    log_path = tmp_path / "conversation_log.jsonl"
    monkeypatch.setattr(conversation_log, "CONVERSATION_LOG_PATH", log_path)
    monkeypatch.setattr(conversation_log, "REMOTE_LOG_ENDPOINT_URL", "")
    chunk = {
        "text": "A source passage about vertical bifacial arrays.",
        "metadata": {"title": "Example paper", "page": 7},
        "distance": 0.42,
    }

    conversation_log.log_conversation_turn(
        "session-2",
        "guided",
        "general_question",
        "How does row spacing affect yield?",
        "Row spacing changes shading and land use.",
        retrieved_chunks=[chunk],
        extra={
            "model_name": "llama4:latest",
            "user_profile": {"user_type": "Researcher"},
            "location_context": {"site_location": "Lafayette, Indiana"},
            "rag_enabled": True,
            "rag_source": "papers",
            "rag_router_reason": "The question asks for research evidence.",
            "retrieval_query": "row spacing bifacial solar farm yield",
            "response_time_ms": 1250,
        },
    )

    row = _read_single_row(log_path)
    assert row["rag_enabled"] is True
    assert row["rag_source"] == "papers"
    assert row["retrieved_count"] == 1
    assert row["retrieved_chunks"][0]["title"] == "Example paper"
    assert row["retrieved_chunks"][0]["page"] == 7
    assert row["retrieval_query"] == "row spacing bifacial solar farm yield"
    assert row["response_time_ms"] == 1250
