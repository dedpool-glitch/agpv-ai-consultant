from llm.candidate_config_validator import validate_candidate_config
from llm.output_generator import explain_output
from llm.recommended_pvmaps_config import generate_recommended_pvmaps_config
from pvmaps.input_validator import validate_pvmaps_input
from pvmaps.matlab_runner import run_pvmaps
from questionnaire.state import initialize_questionnaire_state, update_questionnaire_state
from questionnaire.to_pvmaps import build_pvmaps_input_from_questionnaire
from services.llm_trace import add_llm_trace


def run_recommended_pvmaps_estimate(session_state, api_key, location_context):
    lat = location_context.get("latitude")
    lon = location_context.get("longitude")

    session_state.setdefault("general_chat_messages", [])

    if lat is None or lon is None:
        session_state["general_chat_messages"].append({
            "role": "assistant",
            "content": "I can discuss agrivoltaics generally, but I need a site location before I can run a solar-yield estimate.",
        })
        return False

    state = session_state.get("questionnaire_state") or initialize_questionnaire_state()
    consultation_history = {
        "consultation_messages": session_state.get("consultation_messages", []),
        "general_chat_messages": session_state.get("general_chat_messages", []),
        "post_result_messages": session_state.get("post_result_messages", []),
    }

    recommendation = generate_recommended_pvmaps_config(
        api_key,
        user_profile=session_state.get("user_profile"),
        location_context=location_context,
        consultation_history=consultation_history,
        current_pvmaps_state=state,
    )
    parsed_recommendation, recommendation_errors = validate_candidate_config(recommendation)
    add_llm_trace(
        session_state,
        "recommended_pvmaps_config",
        input_summary={
            "user_profile": session_state.get("user_profile"),
            "location_context": location_context,
            "consultation_history": consultation_history,
            "current_pvmaps_state": state,
        },
        output={
            "recommendation": recommendation,
            "validation_errors": recommendation_errors,
        },
        decision="run_estimate_with_recommendation" if not recommendation_errors else "recommendation_failed",
    )

    if recommendation_errors:
        session_state["general_chat_messages"].append({
            "role": "assistant",
            "content": "I tried to prepare a solar-yield estimate, but the recommended setup did not pass validation yet. I can still discuss the assumptions or ask a few setup questions.",
        })
        return False

    justifications = recommendation.get("justifications", {})
    for field, value in parsed_recommendation.items():
        if state.get(field) is None:
            update_questionnaire_state(state, field, value, assumed=True)
            if field in justifications:
                state["assumptions"].append(f"{field}: {justifications[field]}")

    session_state["questionnaire_state"] = state
    session_state["recommended_pvmaps_config"] = recommendation

    pvmaps_input = build_pvmaps_input_from_questionnaire(state, lat, lon)
    errors = validate_pvmaps_input(pvmaps_input)
    if errors:
        session_state["general_chat_messages"].append({
            "role": "assistant",
            "content": "I prepared a solar-yield setup, but it failed input validation. The setup needs to be reviewed before running PVMAPS.",
        })
        add_llm_trace(
            session_state,
            "pvmaps_input_validator",
            input_summary={"pvmaps_input": pvmaps_input},
            output={"errors": errors},
            decision="do_not_run_pvmaps",
        )
        return False

    output = run_pvmaps(
        pvmaps_input,
        r"D:/agpv-ai-consultant/PV-MAPS-main"
    )
    explanation = explain_output(
        output,
        api_key,
        session_state.get("user_profile"),
    )

    session_state["latest_pvmaps_input"] = pvmaps_input
    session_state["latest_pvmaps_output"] = output
    session_state["latest_pvmaps_explanation"] = explanation
    session_state.setdefault("post_result_messages", [])
    session_state["general_chat_messages"].append({
        "role": "assistant",
        "content": explanation,
    })
    add_llm_trace(
        session_state,
        "pvmaps_background_tool",
        input_summary={
            "pvmaps_input": pvmaps_input,
            "recommendation_justifications": justifications,
        },
        output={
            "pvmaps_output": output,
            "explanation": explanation,
        },
        decision="estimate_completed_and_stored",
    )
    return True
