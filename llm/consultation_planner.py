import json

from constants import TURN_TYPE_GENERAL_CHAT, TURN_TYPES
from llm.prompts import LLM_SYSTEM_TURN_ROUTER_PROMPT
from llm.client import call_llm
from llm.json_utils import parse_json_response


_DIRECT_QUESTION_STARTS = (
    "what ", "why ", "how ", "when ", "where ", "who ", "which ",
    "can ", "could ", "would ", "should ", "does ", "do ", "did ",
    "is ", "are ", "will ", "explain ", "describe ", "list ",
)


def _latest_user_message(conversation_history):
    for message in reversed(conversation_history or []):
        if message.get("role") == "user":
            return str(message.get("content") or "")
    return ""


def _is_direct_question(message):
    normalized = " ".join(str(message or "").casefold().split())
    return bool(normalized) and (
        "?" in normalized
        or normalized.startswith(_DIRECT_QUESTION_STARTS)
    )


def route_conversation_turn(
    api_key,
    latest_user_message=None,
    user_profile=None,
    location_context=None,
    conversation_history=None,
    pvmaps_runs=None,
):
    """
    Classify the next conversation turn as general_chat, gather_info, or
    run_pvmaps, so the app can respond flexibly instead of forcing every
    conversation down a single fixed path toward a PVMAPS estimate.
    """
    latest_user_message = (
        str(latest_user_message).strip()
        if latest_user_message is not None
        else _latest_user_message(conversation_history).strip()
    )

    messages = [
        {"role": "system", "content": LLM_SYSTEM_TURN_ROUTER_PROMPT},
        {
            "role": "user",
            "content": (
                f"User profile:\n{json.dumps(user_profile, indent=2)}\n\n"
                f"Location context:\n{json.dumps(location_context, indent=2)}\n\n"
                f"Conversation history:\n{json.dumps(conversation_history, indent=2)}\n\n"
                f"Prior PVMAPS runs this session:\n{json.dumps(pvmaps_runs, indent=2)}\n\n"
                f"Latest user message to classify:\n{latest_user_message}\n\n"
                "Classify the latest user message."
            ),
        },
    ]

    response = call_llm(messages, api_key)
    plan = parse_json_response(response)

    if plan is None:
        return {
            "turn_type": TURN_TYPE_GENERAL_CHAT,
            "question": None,
            "known_facts": [],
            "reason": "Fallback to general chat because the router returned invalid JSON.",
            "mentioned_location": None,
        }

    turn_type = plan.get("turn_type")
    if turn_type not in TURN_TYPES:
        turn_type = TURN_TYPE_GENERAL_CHAT
    if turn_type == "gather_info" and _is_direct_question(latest_user_message):
        turn_type = TURN_TYPE_GENERAL_CHAT
        plan["question"] = None
        plan["reason"] = (
            "Direct user question must be answered before optional project discovery."
        )

    return {
        "turn_type": turn_type,
        "question": plan.get("question"),
        "known_facts": plan.get("known_facts", []),
        "reason": plan.get("reason"),
        "mentioned_location": plan.get("mentioned_location") or None,
    }
