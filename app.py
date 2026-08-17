import streamlit as st
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv

import traceback 

from constants import (
    APP_TITLE,
    ARRAY_CONFIG_OPTIONS,
    LOCATION_TEXT,
    MANUAL_INPUT_TEXT,
    MONTH_LABELS,
    CHAT_UI_TEXT,
    EXPERT_MODE_TEXT,
    PVMAPS_VALIDATION_LIMITS,
    PVMAPS_VALIDATION_MESSAGES,
    RESULT_TEXT,
    USER_PROFILE_TEXT,
    USER_TYPE_OPTIONS,
    SOLAR_EXPERIENCE_OPTIONS,
    DATASHEET_UPLOAD_TEXT,
    PROJECT_GOAL_OPTIONS,
    TRACE_UI_TEXT,
    APP_MODE_EXPERT,
    APP_MODE_NON_EXPERT,
    GENAI_API_KEY_ENV_VAR,
    MESSAGE_ROLE_ASSISTANT,
    MESSAGE_ROLE_USER,
    MESSAGE_TYPE_PVMAPS_RUN,
    SESSION_KEY_APP_MODE,
    SESSION_KEY_CHAT_MESSAGES,
    SESSION_KEY_DATASHEET,
    SESSION_KEY_LLM_TRACE,
    SESSION_KEY_LOCATION_CONTEXT,
    SESSION_KEY_PVMAPS_RUNS,
    SESSION_KEY_QUESTIONNAIRE_STATE,
    SESSION_KEY_USER_PROFILE,
    TURN_TYPE_GATHER_INFO,
    TURN_TYPE_RUN_PVMAPS,
)


from services.location_geocoder import geocode_location
from services.panel_specs import get_panel_models, get_panel_specs
from llm.consultation_planner import route_conversation_turn
from llm.general_agpv_answerer import answer_general_agpv_question
from llm.rag_source_router import decide_rag_source
from models.pvmaps.input_validator import validate_pvmaps_input
from questionnaire.to_pvmaps import build_pvmaps_input_from_questionnaire
from rag.pipeline import retrieve_for_source, summarize_retrieved_chunks
from services.expert_estimate_service import run_expert_pvmaps_estimate
from services.llm_trace import add_llm_trace
from services.pvmaps_estimate_service import run_recommended_pvmaps_estimate

load_dotenv()
api_key = os.getenv(GENAI_API_KEY_ENV_VAR)
if not api_key:
    raise RuntimeError(f"{GENAI_API_KEY_ENV_VAR} is missing from the environment.")
st.title(APP_TITLE)


st.session_state.setdefault(SESSION_KEY_APP_MODE, None)

if st.session_state[SESSION_KEY_APP_MODE] is None:
    st.subheader(EXPERT_MODE_TEXT["mode_selector_header"])
    mode_col1, mode_col2 = st.columns(2)
    with mode_col1:
        st.write(EXPERT_MODE_TEXT["non_expert_description"])
        if st.button(EXPERT_MODE_TEXT["non_expert_button"]):
            st.session_state[SESSION_KEY_APP_MODE] = APP_MODE_NON_EXPERT
            st.rerun()
    with mode_col2:
        st.write(EXPERT_MODE_TEXT["expert_description"])
        if st.button(EXPERT_MODE_TEXT["expert_button"]):
            st.session_state[SESSION_KEY_APP_MODE] = APP_MODE_EXPERT
            st.rerun()
    st.stop()

with st.sidebar:
    if st.button(EXPERT_MODE_TEXT["switch_mode_button"]):
        st.session_state[SESSION_KEY_APP_MODE] = None
        st.rerun()

if st.session_state[SESSION_KEY_APP_MODE] == APP_MODE_EXPERT:
    st.subheader(EXPERT_MODE_TEXT["form_header"])

    expert_site_location = st.text_input(LOCATION_TEXT["input_label"], key="expert_site_location")
    if st.button(LOCATION_TEXT["geocode_button"], key="expert_geocode_button"):
        try:
            expert_coordinates = geocode_location(expert_site_location)
            st.session_state["expert_location_context"] = {
                "site_location": expert_site_location,
                "confirmed_address": expert_coordinates["address"],
                "latitude": expert_coordinates["latitude"],
                "longitude": expert_coordinates["longitude"],
            }
        except Exception:
            st.session_state["expert_location_context"] = None
            st.error(LOCATION_TEXT["geocode_error"])

    expert_location_context = st.session_state.get("expert_location_context")
    if expert_location_context:
        st.success(f"Using location: {expert_location_context['confirmed_address']}")

    panel_model_options = [MANUAL_INPUT_TEXT["default_panel_model"]] + get_panel_models()
    expert_panel_model = st.selectbox(MANUAL_INPUT_TEXT["panel_model_label"], options=panel_model_options)

    if expert_panel_model == MANUAL_INPUT_TEXT["default_panel_model"]:
        expert_module_height = 4.8
    else:
        expert_module_height = get_panel_specs(expert_panel_model)["module_height"]

    expert_array_config = st.selectbox(MANUAL_INPUT_TEXT["array_config_label"], options=ARRAY_CONFIG_OPTIONS)

    expert_tilt = st.number_input(MANUAL_INPUT_TEXT["tilt_label"], value=25.0, step=1.0)
    if not (PVMAPS_VALIDATION_LIMITS["tilt_min"] <= expert_tilt <= PVMAPS_VALIDATION_LIMITS["tilt_max"]):
        st.error(PVMAPS_VALIDATION_MESSAGES["tilt_range"])

    expert_azimuth = st.selectbox(
        MANUAL_INPUT_TEXT["azimuth_label"],
        options=[PVMAPS_VALIDATION_LIMITS["azimuth_ew"], PVMAPS_VALIDATION_LIMITS["azimuth_ns"]],
        help="90 = east-west, 180 = north-south",
    )

    expert_albedo = st.number_input(MANUAL_INPUT_TEXT["albedo_label"], value=0.3, step=0.05, format="%.2f")
    if not (PVMAPS_VALIDATION_LIMITS["albedo_min"] <= expert_albedo <= PVMAPS_VALIDATION_LIMITS["albedo_max"]):
        st.error(PVMAPS_VALIDATION_MESSAGES["albedo_range"])

    expert_pitch = st.number_input(MANUAL_INPUT_TEXT["pitch_label"], value=11.0, step=0.5)
    if expert_pitch <= 0:
        st.error(PVMAPS_VALIDATION_MESSAGES["pitch_positive"])

    expert_gs_height = st.number_input(MANUAL_INPUT_TEXT["ground_sculpting_height_label"], value=0.5, step=0.1)
    if expert_gs_height < 0:
        st.error(PVMAPS_VALIDATION_MESSAGES["gs_height_nonnegative"])

    expert_array_elevation = st.number_input(MANUAL_INPUT_TEXT["elevation_label"], value=3.0, step=0.5)
    if expert_array_elevation < 0:
        st.error(PVMAPS_VALIDATION_MESSAGES["array_elevation_nonnegative"])
    elif expert_array_elevation <= expert_module_height / 2:
        st.error(PVMAPS_VALIDATION_MESSAGES["array_elevation_height_relation"])

    if st.button(EXPERT_MODE_TEXT["run_button"]):
        if not expert_location_context:
            st.error(EXPERT_MODE_TEXT["missing_location_error"])
        else:
            expert_questionnaire_state = {
                "panel_model": expert_panel_model,
                "array_config": expert_array_config,
                "tilt": expert_tilt,
                "azimuth": expert_azimuth,
                "albedo": expert_albedo,
                "pitch": expert_pitch,
                "gs_height": expert_gs_height,
                "array_elevation": expert_array_elevation,
            }
            expert_pvmaps_input = build_pvmaps_input_from_questionnaire(
                expert_questionnaire_state,
                expert_location_context["latitude"],
                expert_location_context["longitude"],
            )
            expert_errors = validate_pvmaps_input(expert_pvmaps_input)
            if expert_errors:
                st.error(EXPERT_MODE_TEXT["validation_error_header"])
                for expert_error in expert_errors:
                    st.write(f"- {expert_error}")
            else:
                try:
                    expert_output, expert_explanation = run_expert_pvmaps_estimate(
                        st.session_state, expert_pvmaps_input, api_key
                    )
                    st.session_state["expert_last_run"] = {
                        "input": expert_pvmaps_input,
                        "output": expert_output,
                        "explanation": expert_explanation,
                    }
                except Exception as error:
                    
                    st.error(EXPERT_MODE_TEXT["simulation_error"])
                    add_llm_trace(
                        st.session_state,
                        "expert_mode_pvmaps_run",
                        input_summary={"pvmaps_input": expert_pvmaps_input},
                        output={"error": str(error)},
                        decision="expert_estimate_failed",
                    )
                    
                    st.error(traceback.format_exc())

    expert_last_run = st.session_state.get("expert_last_run")
    if expert_last_run:
        st.subheader(RESULT_TEXT["monthly_yield_header"])
        expert_fig, expert_ax = plt.subplots(figsize=(10, 5))
        expert_ax.bar(MONTH_LABELS, expert_last_run["output"]["monthly_yield"])
        expert_ax.set_xlabel(RESULT_TEXT["chart_x_label"])
        expert_ax.set_ylabel(f"Yield ({expert_last_run['output']['yield_unit']})")
        expert_ax.set_title(RESULT_TEXT["chart_title"])
        expert_ax.tick_params(axis="x", labelrotation=45)
        st.pyplot(expert_fig)

        st.subheader(EXPERT_MODE_TEXT["explanation_header"])
        st.write(expert_last_run["explanation"])

    st.stop()


with st.sidebar.expander(TRACE_UI_TEXT["header"], expanded=False):
    if not st.session_state.get(SESSION_KEY_LLM_TRACE):
        st.write(TRACE_UI_TEXT["empty_message"])
    else:
        for index, trace in enumerate(st.session_state[SESSION_KEY_LLM_TRACE], start=1):
            st.markdown(f"**{index}. {trace['stage']}** `{trace['time']}`")
            if trace.get("decision"):
                st.write("Decision:", trace["decision"])
            if trace.get("input") is not None:
                st.write("Input")
                st.json(trace["input"])
            if trace.get("output") is not None:
                st.write("Output")
                st.json(trace["output"])
            st.divider()


if SESSION_KEY_USER_PROFILE not in st.session_state:
    st.subheader(USER_PROFILE_TEXT["header"])
    with st.form("user_profile_form"):
        user_type = st.selectbox(USER_PROFILE_TEXT["user_type_label"], options=USER_TYPE_OPTIONS)
        user_role_details = st.text_input(USER_PROFILE_TEXT["user_role_label"])
        solar_experience = st.selectbox(USER_PROFILE_TEXT["solar_experience_label"], options=SOLAR_EXPERIENCE_OPTIONS)
        project_goal = st.selectbox(USER_PROFILE_TEXT["project_goal_label"], options=PROJECT_GOAL_OPTIONS)
        goal_details = st.text_area(USER_PROFILE_TEXT["goal_details_label"])
        site_location = st.text_input(
            USER_PROFILE_TEXT["site_location_label"],
            placeholder=USER_PROFILE_TEXT["site_location_placeholder"],
        )
        datasheet = st.file_uploader(DATASHEET_UPLOAD_TEXT["label"], type=["pdf"], help=DATASHEET_UPLOAD_TEXT["help"])
        submit_button = st.form_submit_button(USER_PROFILE_TEXT["submit_button"])

        if submit_button:
            location_context = {
                "site_location": site_location.strip() or None,
                "confirmed_address": None,
                "latitude": None,
                "longitude": None,
            }
            if site_location.strip():
                try:
                    coordinates = geocode_location(site_location)
                    location_context["confirmed_address"] = coordinates["address"]
                    location_context["latitude"] = coordinates["latitude"]
                    location_context["longitude"] = coordinates["longitude"]
                except Exception:
                    st.error("I could not confirm that location. You can leave it blank for now or try a simpler city/state.")
                    st.stop()

            st.session_state[SESSION_KEY_LOCATION_CONTEXT] = location_context
            if datasheet:
                st.session_state[SESSION_KEY_DATASHEET] = {
                    "name": datasheet.name,
                    "type": datasheet.type,
                    "bytes": datasheet.getvalue(),
                }
            st.session_state[SESSION_KEY_USER_PROFILE] = {
                "user_type": user_type,
                "user_role_details": user_role_details,
                "solar_experience": solar_experience,
                "project_goal": project_goal,
                "goal_details": goal_details,
            }
            st.session_state[SESSION_KEY_CHAT_MESSAGES] = [{
                "role": MESSAGE_ROLE_ASSISTANT,
                "content": CHAT_UI_TEXT["opening_message"],
            }]
            st.rerun()
    st.stop()

location_context = st.session_state.get(SESSION_KEY_LOCATION_CONTEXT, {})
lat = location_context.get("latitude")
lon = location_context.get("longitude")
address = location_context.get("confirmed_address")

if address:
    st.success(f"Using location: {address}")
else:
    st.info("No site selected yet. I can answer general questions, but I will need a location before running PVMAPS.")

if SESSION_KEY_DATASHEET in st.session_state:
    st.success(DATASHEET_UPLOAD_TEXT["success"])
    st.write(f"{DATASHEET_UPLOAD_TEXT['uploaded_file_label']}: {st.session_state[SESSION_KEY_DATASHEET]['name']}")

st.session_state.setdefault(SESSION_KEY_CHAT_MESSAGES, [{
    "role": MESSAGE_ROLE_ASSISTANT,
    "content": CHAT_UI_TEXT["opening_message"],
}])
st.session_state.setdefault(SESSION_KEY_PVMAPS_RUNS, [])

if CHAT_UI_TEXT["description"]:
    st.write(CHAT_UI_TEXT["description"])

for message in st.session_state[SESSION_KEY_CHAT_MESSAGES]:
    if message.get("type") == MESSAGE_TYPE_PVMAPS_RUN:
        run_index = message["run_index"]
        pvmaps_runs = st.session_state.get(SESSION_KEY_PVMAPS_RUNS, [])
        if run_index < len(pvmaps_runs):
            run = pvmaps_runs[run_index]
            with st.expander(f"{RESULT_TEXT['latest_estimate_header']}: {run['label']}", expanded=True):
                st.subheader(LOCATION_TEXT["result_location_header"])
                st.write(address or "No confirmed site location")

                if run.get("overrides"):
                    st.caption(f"Changed from baseline: {run['overrides']}")

                st.subheader(RESULT_TEXT["monthly_yield_header"])
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.bar(MONTH_LABELS, run["output"]["monthly_yield"])
                ax.set_xlabel(RESULT_TEXT["chart_x_label"])
                ax.set_ylabel(f"Yield ({run['output']['yield_unit']})")
                ax.set_title(RESULT_TEXT["chart_title"])
                ax.tick_params(axis="x", labelrotation=45)
                st.pyplot(fig)
        continue

    with st.chat_message(message["role"]):
        st.write(message["content"])

question = st.chat_input(CHAT_UI_TEXT["answer_label"], key="chat_input")
if question:
    st.session_state[SESSION_KEY_CHAT_MESSAGES].append({
        "role": MESSAGE_ROLE_USER,
        "content": question,
    })

    plan = route_conversation_turn(
        api_key,
        user_profile=st.session_state.get(SESSION_KEY_USER_PROFILE),
        location_context=location_context,
        conversation_history=st.session_state[SESSION_KEY_CHAT_MESSAGES],
        pvmaps_runs=st.session_state.get(SESSION_KEY_PVMAPS_RUNS, []),
    )
    add_llm_trace(
        st.session_state,
        "turn_router",
        input_summary={
            SESSION_KEY_USER_PROFILE: st.session_state.get(SESSION_KEY_USER_PROFILE),
            SESSION_KEY_LOCATION_CONTEXT: location_context,
            "conversation_history": st.session_state[SESSION_KEY_CHAT_MESSAGES],
            SESSION_KEY_PVMAPS_RUNS: st.session_state.get(SESSION_KEY_PVMAPS_RUNS, []),
        },
        output=plan,
        decision=plan["turn_type"],
    )

    if plan.get("mentioned_location"):
        try:
            coordinates = geocode_location(plan["mentioned_location"])
            location_context = {
                "site_location": plan["mentioned_location"],
                "confirmed_address": coordinates["address"],
                "latitude": coordinates["latitude"],
                "longitude": coordinates["longitude"],
            }
            st.session_state[SESSION_KEY_LOCATION_CONTEXT] = location_context
            add_llm_trace(
                st.session_state,
                "location_geocoder",
                input_summary={"mentioned_location": plan["mentioned_location"]},
                output=location_context,
                decision="location_updated",
            )
        except Exception as error:
            st.session_state[SESSION_KEY_CHAT_MESSAGES].append({
                "role": MESSAGE_ROLE_ASSISTANT,
                "content": f"I couldn't confirm that location ('{plan['mentioned_location']}'). Could you try a simpler city/state or check the spelling?",
            })
            add_llm_trace(
                st.session_state,
                "location_geocoder",
                input_summary={"mentioned_location": plan["mentioned_location"]},
                output={"error": str(error)},
                decision="location_update_failed",
            )
            st.rerun()

    if plan["turn_type"] == TURN_TYPE_GATHER_INFO and plan.get("question"):
        st.session_state[SESSION_KEY_CHAT_MESSAGES].append({
            "role": MESSAGE_ROLE_ASSISTANT,
            "content": plan["question"],
        })

    elif plan["turn_type"] == TURN_TYPE_RUN_PVMAPS:
        try:
            run_recommended_pvmaps_estimate(
                st.session_state,
                api_key,
                location_context,
                latest_user_message=question,
            )
        except Exception as error:
            st.session_state[SESSION_KEY_CHAT_MESSAGES].append({
                "role": MESSAGE_ROLE_ASSISTANT,
                "content": "I tried to run a solar-yield estimate, but PVMAPS could not complete the simulation. We can keep discussing the setup and assumptions.",
            })
            add_llm_trace(
                st.session_state,
                "pvmaps_background_tool",
                input_summary={SESSION_KEY_LOCATION_CONTEXT: location_context},
                output={"error": str(error)},
                decision="estimate_failed",
            )

    else:
        pvmaps_runs = st.session_state.get(SESSION_KEY_PVMAPS_RUNS, [])
        latest_pvmaps_output = pvmaps_runs[-1]["output"] if pvmaps_runs else None

        retrieved_context = []
        try:
            rag_plan = decide_rag_source(
                question,
                api_key,
                conversation_history=st.session_state[SESSION_KEY_CHAT_MESSAGES],
            )
            add_llm_trace(
                st.session_state,
                "rag_source_router",
                input_summary={"question": question},
                output=rag_plan,
                decision=rag_plan["source"],
            )
            retrieved_context = retrieve_for_source(rag_plan["source"], question)
            add_llm_trace(
                st.session_state,
                "rag_retrieval",
                input_summary={"question": question, "source": rag_plan["source"]},
                output={
                    "retrieved_count": len(retrieved_context),
                    "chunks": summarize_retrieved_chunks(retrieved_context),
                },
                decision="chunks_retrieved" if retrieved_context else "no_chunks_found",
            )
        except Exception as error:
            add_llm_trace(
                st.session_state,
                "rag_source_router",
                input_summary={"question": question},
                output={"error": str(error)},
                decision="rag_skipped_due_to_error",
            )

        answer = answer_general_agpv_question(
            question,
            api_key,
            user_profile=st.session_state.get(SESSION_KEY_USER_PROFILE),
            location_context=location_context,
            pvmaps_state=st.session_state.get(SESSION_KEY_QUESTIONNAIRE_STATE),
            latest_pvmaps_output=latest_pvmaps_output,
            conversation_history=st.session_state[SESSION_KEY_CHAT_MESSAGES],
            retrieved_context=retrieved_context,
        )
        add_llm_trace(
            st.session_state,
            "general_agpv_answerer",
            input_summary={
                "question": question,
                SESSION_KEY_USER_PROFILE: st.session_state.get(SESSION_KEY_USER_PROFILE),
                SESSION_KEY_LOCATION_CONTEXT: location_context,
                "conversation_history": st.session_state[SESSION_KEY_CHAT_MESSAGES],
                "retrieved_context_count": len(retrieved_context),
            },
            output={"answer": answer},
            decision="answered_general_question",
        )
        st.session_state[SESSION_KEY_CHAT_MESSAGES].append({
            "role": MESSAGE_ROLE_ASSISTANT,
            "content": answer,
        })

    st.rerun()
