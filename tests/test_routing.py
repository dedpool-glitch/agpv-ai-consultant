import json

import pytest

from constants import (
    TURN_TYPE_GATHER_INFO,
    TURN_TYPE_GENERAL_CHAT,
    TURN_TYPE_RUN_PVMAPS,
)
from llm.consultation_planner import route_conversation_turn
from llm.rag_source_router import decide_rag_source


def _router_response(turn_type, question=None):
    return json.dumps({
        "turn_type": turn_type,
        "question": question,
        "known_facts": [],
        "reason": "test",
        "mentioned_location": None,
    })


def test_latest_message_is_explicit_and_direct_question_cannot_gather(monkeypatch):
    captured = {}

    def fake_call(messages, _api_key):
        captured["prompt"] = messages[-1]["content"]
        return _router_response(TURN_TYPE_GATHER_INFO, "Unrelated follow-up?")

    monkeypatch.setattr("llm.consultation_planner.call_llm", fake_call)
    message = "What matrix equation solves for sky-diffuse and ground irradiance?"
    plan = route_conversation_turn(
        "key",
        latest_user_message=message,
        conversation_history=[{"role": "user", "content": message}],
    )

    assert f"Latest user message to classify:\n{message}" in captured["prompt"]
    assert plan["turn_type"] == TURN_TYPE_GENERAL_CHAT
    assert plan["question"] is None


def test_genuine_project_discovery_can_still_gather(monkeypatch):
    monkeypatch.setattr(
        "llm.consultation_planner.call_llm",
        lambda *_args, **_kwargs: _router_response(
            TURN_TYPE_GATHER_INFO,
            "What outcome matters most for this project?",
        ),
    )
    plan = route_conversation_turn(
        "key",
        latest_user_message="I am beginning to explore agrivoltaics for my farm",
    )
    assert plan["turn_type"] == TURN_TYPE_GATHER_INFO


def test_simulation_request_is_not_downgraded(monkeypatch):
    monkeypatch.setattr(
        "llm.consultation_planner.call_llm",
        lambda *_args, **_kwargs: _router_response(TURN_TYPE_RUN_PVMAPS),
    )
    plan = route_conversation_turn(
        "key",
        latest_user_message="Can you run a new solar-yield estimate for this location?",
    )
    assert plan["turn_type"] == TURN_TYPE_RUN_PVMAPS


def test_rag_source_router_can_choose_both_without_keyword_override(monkeypatch):
    calls = []

    def fake_call(messages, _api_key):
        calls.append(messages)
        return json.dumps({"source": "both", "reason": "Evidence may span both corpora."})

    monkeypatch.setattr("llm.rag_source_router.call_llm", fake_call)
    decision = decide_rag_source(
        "What matrix equation solves for sky-diffuse and ground irradiance?",
        api_key="key",
    )

    assert calls
    assert decision["source"] == "both"


@pytest.mark.parametrize("model_source", ["papers", "books", "both"])
def test_any_research_decision_searches_both_collections(monkeypatch, model_source):
    monkeypatch.setattr(
        "llm.rag_source_router.call_llm",
        lambda *_args, **_kwargs: json.dumps({
            "source": model_source,
            "reason": "Research evidence is useful.",
        }),
    )

    decision = decide_rag_source("Explain this solar concept.", api_key="key")

    assert decision["source"] == "both"


def test_no_rag_decision_remains_none(monkeypatch):
    monkeypatch.setattr(
        "llm.rag_source_router.call_llm",
        lambda *_args, **_kwargs: json.dumps({
            "source": "none",
            "reason": "No research support needed.",
        }),
    )

    decision = decide_rag_source("Hello", api_key="key")

    assert decision["source"] == "none"
