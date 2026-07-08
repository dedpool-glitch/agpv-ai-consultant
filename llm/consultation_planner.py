import json

from llm.prompts import LLM_SYSTEM_CONSULTATION_PLANNER_PROMPT
from llm.client import call_llm


def plan_next_consultation_step(
    api_key,
    user_profile=None,
    location_context=None,
    consultation_history=None,
):
    messages = [
        {"role": "system", "content": LLM_SYSTEM_CONSULTATION_PLANNER_PROMPT},
        {
            "role": "user",
            "content": (
                f"User profile:\n{json.dumps(user_profile, indent=2)}\n\n"
                f"Location context:\n{json.dumps(location_context, indent=2)}\n\n"
                f"Consultation history:\n{json.dumps(consultation_history, indent=2)}\n\n"
                "Plan the next consultation step."
            ),
        },
    ]

    response = call_llm(messages, api_key)

    try:
        plan = json.loads(response)
    except json.JSONDecodeError:
        return {
            "question": "What would you like to understand before we move toward a solar-yield estimate?",
            "known_facts": [],
            "reason": "Fallback question because the planner returned invalid JSON.",
            "ready_for_pvmaps": False,
        }

    return {
        "question": plan.get("question"),
        "known_facts": plan.get("known_facts", []),
        "reason": plan.get("reason"),
        "ready_for_pvmaps": bool(plan.get("ready_for_pvmaps")),
    }

