import json

from llm.prompts import LLM_SYSTEM_TURN_ROUTER_PROMPT
from llm.client import call_llm
from llm.json_utils import parse_json_response


def route_conversation_turn(
    api_key,
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
    messages = [
        {"role": "system", "content": LLM_SYSTEM_TURN_ROUTER_PROMPT},
        {
            "role": "user",
            "content": (
                f"User profile:\n{json.dumps(user_profile, indent=2)}\n\n"
                f"Location context:\n{json.dumps(location_context, indent=2)}\n\n"
                f"Conversation history:\n{json.dumps(conversation_history, indent=2)}\n\n"
                f"Prior PVMAPS runs this session:\n{json.dumps(pvmaps_runs, indent=2)}\n\n"
                "Classify the next turn."
            ),
        },
    ]

    response = call_llm(messages, api_key)
    plan = parse_json_response(response)

    if plan is None:
        return {
            "turn_type": "general_chat",
            "question": None,
            "known_facts": [],
            "reason": "Fallback to general chat because the router returned invalid JSON.",
            "mentioned_location": None,
        }

    turn_type = plan.get("turn_type")
    if turn_type not in ("general_chat", "gather_info", "run_pvmaps"):
        turn_type = "general_chat"

    return {
        "turn_type": turn_type,
        "question": plan.get("question"),
        "known_facts": plan.get("known_facts", []),
        "reason": plan.get("reason"),
        "mentioned_location": plan.get("mentioned_location") or None,
    }
