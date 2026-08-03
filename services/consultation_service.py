from llm.consultation_planner import plan_next_consultation_step
from services.llm_trace import add_llm_trace
from services.pvmaps_estimate_service import run_recommended_pvmaps_estimate


def start_consultation(session_state, api_key, location_context):
    """
    Kick off the consultation phase: ask the planner whether we already have
    enough context to attempt a PVMAPS estimate, or whether we need to ask
    the user a follow-up question first.
    """
    plan = plan_next_consultation_step(
        api_key,
        user_profile=session_state.get("user_profile"),
        location_context=location_context,
        consultation_history=[],
    )
    add_llm_trace(
        session_state,
        "consultation_planner",
        input_summary={
            "user_profile": session_state.get("user_profile"),
            "location_context": location_context,
            "consultation_history": [],
        },
        output=plan,
        decision="ready_for_pvmaps" if plan["ready_for_pvmaps"] else "ask_follow_up",
    )
    session_state["consultation_started"] = True
    session_state["consultation_llm_history"] = []
    session_state["consultation_plan_history"] = [plan]

    if plan["ready_for_pvmaps"]:
        session_state["ready_for_estimate"] = True
        session_state["post_consultation_route"] = "general_chat"
        try:
            run_recommended_pvmaps_estimate(session_state, api_key, location_context)
        except Exception as error:
            session_state.setdefault("general_chat_messages", [])
            session_state["general_chat_messages"].append({
                "role": "assistant",
                "content": "I tried to run a background solar-yield estimate, but PVMAPS could not complete the simulation. We can keep discussing the setup and assumptions.",
            })
            add_llm_trace(
                session_state,
                "pvmaps_background_tool",
                input_summary={"location_context": location_context},
                output={"error": str(error)},
                decision="background_estimate_failed",
            )
        return

    session_state["consultation_display_messages"] = [
        {
            "role": "assistant",
            "content": plan["question"],
        }
    ]
