import copy

from llm.candidate_config_validator import validate_candidate_config
from llm.output_generator import explain_output
from llm.recommended_pvmaps_config import generate_recommended_pvmaps_config
from pvmaps.input_validator import validate_pvmaps_input
from pvmaps.matlab_runner import run_pvmaps
from questionnaire.state import initialize_questionnaire_state, update_questionnaire_state
from questionnaire.to_pvmaps import build_pvmaps_input_from_questionnaire
from rag.pipeline import retrieve_for_source, summarize_retrieved_chunks
from services.llm_trace import add_llm_trace


def retrieve_recommendation_context(session_state, latest_user_message):
    """
    Best-effort retrieval to ground the Recommender's parameter choices in
    the actual research corpus. Any failure here just means the Recommender
    falls back to its own general knowledge, same as before this existed.
    """
    query = latest_user_message
    if not query:
        user_profile = session_state.get("user_profile") or {}
        goal = user_profile.get("project_goal", "solar farm design")
        query = f"PVMAPS solar farm design recommendations for {goal}"

    try:
        return retrieve_for_source("both", query, n_results=2)
    except Exception:
        return []


def run_recommended_pvmaps_estimate(
    session_state,
    api_key,
    location_context,
    latest_user_message=None,
    run_label=None,
):
    """
    Run one PVMAPS solar-yield estimate and append it to session_state["pvmaps_runs"].

    Can be called multiple times in one conversation. Any field changes for a
    variant run (e.g. trying tracking instead of fixed-tilt) are decided by
    the recommendation step itself, grounded in the user's profile, goal,
    land context, and their actual latest message — not guessed blindly
    upstream. A one-off change only affects this run; it does not overwrite
    the session's baseline questionnaire state.
    """
    lat = location_context.get("latitude")
    lon = location_context.get("longitude")

    session_state.setdefault("chat_messages", [])
    session_state.setdefault("pvmaps_runs", [])

    if lat is None or lon is None:
        session_state["chat_messages"].append({
            "role": "assistant",
            "content": "I can discuss agrivoltaics generally, but I need a site location before I can run a solar-yield estimate.",
        })
        return False

    baseline_state = session_state.get("questionnaire_state") or initialize_questionnaire_state()
    run_state = copy.deepcopy(baseline_state)

    conversation_history = {
        "chat_messages": session_state.get("chat_messages", []),
    }

    retrieved_context = retrieve_recommendation_context(session_state, latest_user_message)
    add_llm_trace(
        session_state,
        "recommendation_context_retrieval",
        input_summary={"latest_user_message": latest_user_message},
        output={
            "retrieved_count": len(retrieved_context),
            "chunks": summarize_retrieved_chunks(retrieved_context),
        },
        decision="context_retrieved" if retrieved_context else "no_context_found",
    )

    recommendation = generate_recommended_pvmaps_config(
        api_key,
        user_profile=session_state.get("user_profile"),
        location_context=location_context,
        consultation_history=conversation_history,
        current_pvmaps_state=run_state,
        latest_user_message=latest_user_message,
        retrieved_context=retrieved_context,
    )
    parsed_recommendation, recommendation_errors = validate_candidate_config(recommendation)
    add_llm_trace(
        session_state,
        "recommended_pvmaps_config",
        input_summary={
            "user_profile": session_state.get("user_profile"),
            "location_context": location_context,
            "conversation_history": conversation_history,
            "current_pvmaps_state": run_state,
            "latest_user_message": latest_user_message,
            "retrieved_context_count": len(retrieved_context),
        },
        output={
            "recommendation": recommendation,
            "validation_errors": recommendation_errors,
        },
        decision="run_estimate_with_recommendation" if not recommendation_errors else "recommendation_failed",
    )

    if recommendation_errors:
        session_state["chat_messages"].append({
            "role": "assistant",
            "content": "I tried to prepare a solar-yield estimate, but the recommended setup did not pass validation yet. I can still discuss the assumptions or ask a few setup questions.",
        })
        return False

    justifications = recommendation.get("justifications", {})
    newly_confirmed = {}
    changed_fields = {}
    for field, value in parsed_recommendation.items():
        baseline_value = baseline_state.get(field)

        if baseline_value is None:
            update_questionnaire_state(run_state, field, value, assumed=True)
            if field in justifications:
                run_state["assumptions"].append(f"{field}: {justifications[field]}")
            newly_confirmed[field] = value
        elif value != baseline_value:
            # The recommender explicitly changed an already-set field based on
            # the user's latest message -- treat this as a one-off variant for
            # this run only, not a change to the session's baseline.
            update_questionnaire_state(run_state, field, value, assumed=False)
            if field in justifications:
                run_state["assumptions"].append(f"{field}: {justifications[field]}")
            changed_fields[field] = value

    # Only fold newly-filled fields back into the shared baseline, so a
    # one-off "what if" variant doesn't become the new default for future
    # runs in this session.
    for field, value in newly_confirmed.items():
        if baseline_state.get(field) is None:
            update_questionnaire_state(baseline_state, field, value, assumed=True)
    session_state["questionnaire_state"] = baseline_state

    pvmaps_input = build_pvmaps_input_from_questionnaire(run_state, lat, lon)
    errors = validate_pvmaps_input(pvmaps_input)
    if errors:
        session_state["chat_messages"].append({
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

    run_record = {
        "label": run_label or ("Variant estimate" if changed_fields else "Solar-yield estimate"),
        "input": pvmaps_input,
        "output": output,
        "explanation": explanation,
        "overrides": changed_fields,
    }
    session_state["pvmaps_runs"].append(run_record)
    session_state["chat_messages"].append({
        "role": "assistant",
        "type": "pvmaps_run",
        "run_index": len(session_state["pvmaps_runs"]) - 1,
    })
    session_state["chat_messages"].append({
        "role": "assistant",
        "content": explanation,
    })
    add_llm_trace(
        session_state,
        "pvmaps_background_tool",
        input_summary={
            "pvmaps_input": pvmaps_input,
            "recommendation_justifications": justifications,
            "changed_fields": changed_fields,
        },
        output={
            "pvmaps_output": output,
            "explanation": explanation,
        },
        decision="estimate_completed_and_stored",
    )
    return True
