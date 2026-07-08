import streamlit as st
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv

from constants import (
    APP_TITLE,
    ARRAY_CONFIG_OPTIONS,
    INPUT_MODE,
    LOCATION_TEXT,
    MANUAL_INPUT_TEXT,
    MONTH_LABELS,
    PANEL_DEFAULT_SPECS,
    PVMAPS_RUN_TEXT,
    QUESTIONNAIRE_UI_TEXT,
    GOAL_FOLLOW_UP_UI_TEXT,
    GENERAL_CHAT_UI_TEXT,
    RESULT_TEXT,
    USER_PROFILE_TEXT,
    USER_TYPE_OPTIONS,
    SOLAR_EXPERIENCE_OPTIONS,
    DATASHEET_UPLOAD_TEXT,
    PROJECT_GOAL_OPTIONS,
    TRACE_UI_TEXT
)
from pvmaps.input_builder import create_default_pvmaps_input
from pvmaps.input_validator import validate_pvmaps_input
from pvmaps.matlab_runner import run_pvmaps
from services.location_geocoder import geocode_location
from services.panel_specs import get_panel_models, get_panel_specs
from questionnaire.parser import parse_questionnaire_answer
from questionnaire.state import apply_questionnaire_defaults, get_next_question, initialize_questionnaire_state, update_questionnaire_state
from questionnaire.to_pvmaps import build_pvmaps_input_from_questionnaire
from llm.parameter_extractor import extract_questionnaire_parameter
from llm.question_generator import generate_question
from llm.consultation_planner import plan_next_consultation_step
from llm.output_generator import explain_output
from llm.intent_classifier import classify_intent
from llm.general_agpv_answerer import answer_general_agpv_question
from llm.recommended_pvmaps_config import generate_recommended_pvmaps_config
from llm.candidate_config_validator import validate_candidate_config
from services.llm_trace import add_llm_trace
from services.pvmaps_estimate_service import run_recommended_pvmaps_estimate

load_dotenv()
api_key = os.getenv("PURDUE_GENAI_KEY")

st.title(APP_TITLE)


with st.sidebar.expander(TRACE_UI_TEXT["header"], expanded=False):
    if not st.session_state.get("llm_trace"):
        st.write(TRACE_UI_TEXT["empty_message"])
    else:
        for index, trace in enumerate(st.session_state["llm_trace"], start=1):
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


if "user_profile" not in st.session_state:
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

            st.session_state["location_context"] = location_context
            if datasheet:
                st.session_state["datasheet"] = {
                    "name": datasheet.name,
                    "type": datasheet.type,
                    "bytes": datasheet.getvalue(),
                }
            st.session_state["user_profile"] = {
                "user_type": user_type,
                "user_role_details": user_role_details,
                "solar_experience": solar_experience,
                "project_goal": project_goal,
                "goal_details": goal_details,
            }
            st.rerun()
    st.stop()

location_context = st.session_state.get("location_context", {})
lat = location_context.get("latitude")
lon = location_context.get("longitude")
address = location_context.get("confirmed_address")

if address:
    st.success(f"Using location: {address}")
else:
    st.info("No site selected yet. I can answer general questions, but I will need a location before running PVMAPS.")

if "datasheet" in st.session_state:
    st.success(DATASHEET_UPLOAD_TEXT["success"])
    st.write(f"{DATASHEET_UPLOAD_TEXT['uploaded_file_label']}: {st.session_state['datasheet']['name']}")

if "goal_follow_up_complete" not in st.session_state:
    st.session_state["goal_follow_up_complete"] = False

if not st.session_state["goal_follow_up_complete"]:
    if "goal_follow_up_started" not in st.session_state:
        st.session_state["goal_follow_up_started"] = False

    if not st.session_state["goal_follow_up_started"]:
        st.write(GOAL_FOLLOW_UP_UI_TEXT["start_description"])

        if st.button(GOAL_FOLLOW_UP_UI_TEXT["start_button"]):
            plan = plan_next_consultation_step(
                api_key,
                user_profile=st.session_state.get("user_profile"),
                location_context=location_context,
                consultation_history=[],
            )
            add_llm_trace(
                st.session_state,
                "consultation_planner",
                input_summary={
                    "user_profile": st.session_state.get("user_profile"),
                    "location_context": location_context,
                    "consultation_history": [],
                },
                output=plan,
                decision="ready_for_pvmaps" if plan["ready_for_pvmaps"] else "ask_follow_up",
            )
            st.session_state["goal_follow_up_started"] = True
            st.session_state["consultation_messages"] = []
            st.session_state["consultation_plan_history"] = [plan]

            if plan["ready_for_pvmaps"]:
                st.session_state["goal_follow_up_complete"] = True
                st.session_state["post_consultation_route"] = "general_chat"
                try:
                    run_recommended_pvmaps_estimate(st.session_state, api_key, location_context)
                except Exception as error:
                    st.session_state.setdefault("general_chat_messages", [])
                    st.session_state["general_chat_messages"].append({
                        "role": "assistant",
                        "content": "I tried to run a background solar-yield estimate, but PVMAPS could not complete the simulation. We can keep discussing the setup and assumptions.",
                    })
                    add_llm_trace(
                        st.session_state,
                        "pvmaps_background_tool",
                        input_summary={"location_context": location_context},
                        output={"error": str(error)},
                        decision="background_estimate_failed",
                    )
                st.rerun()

            st.session_state["goal_follow_up_messages"] = [
                {
                    "role": "assistant",
                    "content": plan["question"],
                }
            ]
            st.rerun()
    else:
        for message in st.session_state.get("goal_follow_up_messages", []):
            with st.chat_message(message["role"]):
                st.write(message["content"])

        answer = st.chat_input(GOAL_FOLLOW_UP_UI_TEXT["answer_label"], key="goal_follow_up_input")
        if answer:
            st.session_state["goal_follow_up_messages"].append({
                "role": "user",
                "content": answer,
            })
            st.session_state.setdefault("consultation_messages", [])
            st.session_state["consultation_messages"].append({
                "role": "user",
                "content": answer,
            })

            plan = plan_next_consultation_step(
                api_key,
                user_profile=st.session_state.get("user_profile"),
                location_context=location_context,
                consultation_history=st.session_state["consultation_messages"],
            )
            add_llm_trace(
                st.session_state,
                "consultation_planner",
                input_summary={
                    "user_profile": st.session_state.get("user_profile"),
                    "location_context": location_context,
                    "consultation_history": st.session_state["consultation_messages"],
                },
                output=plan,
                decision="ready_for_pvmaps" if plan["ready_for_pvmaps"] else "ask_follow_up",
            )
            st.session_state.setdefault("consultation_plan_history", [])
            st.session_state["consultation_plan_history"].append(plan)

            if plan["ready_for_pvmaps"]:
                st.session_state["goal_follow_up_complete"] = True
                st.session_state["post_consultation_route"] = "general_chat"
                st.session_state["goal_follow_up_messages"].append({
                    "role": "assistant",
                    "content": "Thanks. I have enough context to prepare a solar-yield estimate in the background.",
                })
                try:
                    run_recommended_pvmaps_estimate(st.session_state, api_key, location_context)
                except Exception as error:
                    st.session_state.setdefault("general_chat_messages", [])
                    st.session_state["general_chat_messages"].append({
                        "role": "assistant",
                        "content": "I tried to run a background solar-yield estimate, but PVMAPS could not complete the simulation. We can keep discussing the setup and assumptions.",
                    })
                    add_llm_trace(
                        st.session_state,
                        "pvmaps_background_tool",
                        input_summary={"location_context": location_context},
                        output={"error": str(error)},
                        decision="background_estimate_failed",
                    )
            else:
                st.session_state["goal_follow_up_messages"].append({
                    "role": "assistant",
                    "content": plan["question"],
                })
            st.rerun()

    st.stop()

if "consultation_messages" in st.session_state:
    with st.expander(GOAL_FOLLOW_UP_UI_TEXT["context_header"]):
        st.json(st.session_state["consultation_messages"])

if "post_consultation_route" not in st.session_state:
    st.session_state["post_consultation_route"] = "general_chat"

if st.session_state["post_consultation_route"] == "pvmaps_setup":
    try:
        run_recommended_pvmaps_estimate(st.session_state, api_key, location_context)
    except Exception as error:
        st.session_state.setdefault("general_chat_messages", [])
        st.session_state["general_chat_messages"].append({
            "role": "assistant",
            "content": "I tried to run a background solar-yield estimate, but PVMAPS could not complete the simulation. We can keep discussing the setup and assumptions.",
        })
        add_llm_trace(
            st.session_state,
            "pvmaps_background_tool",
            input_summary={"location_context": location_context},
            output={"error": str(error)},
            decision="background_estimate_failed",
        )
    st.session_state["post_consultation_route"] = "general_chat"
    st.rerun()

if st.session_state["post_consultation_route"] == "general_chat":
    st.write(GENERAL_CHAT_UI_TEXT["description"])

    if "latest_pvmaps_output" in st.session_state:
        latest_output = st.session_state["latest_pvmaps_output"]
        with st.expander(RESULT_TEXT["latest_estimate_header"], expanded=False):
            st.subheader(LOCATION_TEXT["result_location_header"])
            st.write(address or "No confirmed site location")

            st.subheader(RESULT_TEXT["result_header"])
            st.write(st.session_state.get("latest_pvmaps_explanation"))

            st.subheader(RESULT_TEXT["monthly_yield_header"])
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.bar(MONTH_LABELS, latest_output["monthly_yield"])
            ax.set_xlabel(RESULT_TEXT["chart_x_label"])
            ax.set_ylabel(f"Yield ({latest_output['yield_unit']})")
            ax.set_title(RESULT_TEXT["chart_title"])
            ax.tick_params(axis="x", labelrotation=45)
            st.pyplot(fig)

    if "general_chat_messages" not in st.session_state:
        st.session_state["general_chat_messages"] = []

    for message in st.session_state["general_chat_messages"]:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    question = st.chat_input(GENERAL_CHAT_UI_TEXT["answer_label"], key="general_agpv_input")
    if question:
        st.session_state["general_chat_messages"].append({
            "role": "user",
            "content": question,
        })
        combined_chat_history = {
            "consultation_messages": st.session_state.get("consultation_messages", []),
            "general_chat_messages": st.session_state["general_chat_messages"],
            "post_result_messages": st.session_state.get("post_result_messages", []),
        }

        plan = plan_next_consultation_step(
            api_key,
            user_profile=st.session_state.get("user_profile"),
            location_context=location_context,
            consultation_history=combined_chat_history,
        )
        add_llm_trace(
            st.session_state,
            "consultation_planner",
            input_summary={
                "user_profile": st.session_state.get("user_profile"),
                "location_context": location_context,
                "consultation_history": combined_chat_history,
            },
            output=plan,
            decision="run_background_estimate" if plan["ready_for_pvmaps"] else "continue_chat",
        )

        if plan["ready_for_pvmaps"] and "latest_pvmaps_output" not in st.session_state:
            try:
                run_recommended_pvmaps_estimate(st.session_state, api_key, location_context)
            except Exception as error:
                st.session_state["general_chat_messages"].append({
                    "role": "assistant",
                    "content": "I tried to run a background solar-yield estimate, but PVMAPS could not complete the simulation. We can keep discussing the setup and assumptions.",
                })
                add_llm_trace(
                    st.session_state,
                    "pvmaps_background_tool",
                    input_summary={"location_context": location_context},
                    output={"error": str(error)},
                    decision="background_estimate_failed",
                )
            st.rerun()

        answer = answer_general_agpv_question(
            question,
            api_key,
            user_profile=st.session_state.get("user_profile"),
            location_context=location_context,
            pvmaps_state=st.session_state.get("questionnaire_state"),
            latest_pvmaps_output=st.session_state.get("latest_pvmaps_output"),
            conversation_history=combined_chat_history,
        )
        add_llm_trace(
            st.session_state,
            "general_agpv_answerer",
            input_summary={
                "question": question,
                "user_profile": st.session_state.get("user_profile"),
                "location_context": location_context,
                "conversation_history": combined_chat_history,
            },
            output={"answer": answer},
            decision="answered_general_question",
        )
        st.session_state["general_chat_messages"].append({
            "role": "assistant",
            "content": answer,
        })
        st.rerun()

    st.stop()

mode = st.radio(INPUT_MODE["label"], options=[INPUT_MODE["questionnaire"], INPUT_MODE["manual"]], index=None)

if mode == INPUT_MODE["manual"]:
    st.write(MANUAL_INPUT_TEXT["description"])

    panel_model_options = [MANUAL_INPUT_TEXT["default_panel_model"]] + get_panel_models()
    panel_model = st.selectbox(MANUAL_INPUT_TEXT["panel_model_label"], options=panel_model_options)

    if panel_model == MANUAL_INPUT_TEXT["default_panel_model"]:
        panel_specs = PANEL_DEFAULT_SPECS
    else:
        panel_specs = get_panel_specs(panel_model)
        st.write(f"{MANUAL_INPUT_TEXT['datasheet_cell_type_label']}: {panel_specs['cell_type_raw']}")
        st.write(f"{MANUAL_INPUT_TEXT['source_label']}: {panel_specs['source']}")
        st.write(f"{MANUAL_INPUT_TEXT['pvmaps_cell_tech_label']}: {panel_specs['cell_tech']}")

    cell_tech = panel_specs["cell_tech"]
    height = st.number_input(MANUAL_INPUT_TEXT["panel_height_label"], value=float(panel_specs["module_height"]), format="%.3f")
    direct_eff = st.number_input(MANUAL_INPUT_TEXT["direct_efficiency_label"], value=float(panel_specs["stc_eff_direct"]), format="%.2f")
    diffuse_eff = st.number_input(MANUAL_INPUT_TEXT["diffuse_efficiency_label"], value=float(panel_specs["stc_eff_diffuse"]), format="%.2f")
    tcoeff = st.number_input(MANUAL_INPUT_TEXT["temperature_coefficient_label"], value=float(panel_specs["tcoeff"]), format="%.4f")

    config = st.selectbox(MANUAL_INPUT_TEXT["array_config_label"], options=ARRAY_CONFIG_OPTIONS)
    tilt = st.number_input(MANUAL_INPUT_TEXT["tilt_label"], value=25.0)
    azimuth = st.number_input(MANUAL_INPUT_TEXT["azimuth_label"], value=90.0)
    albedo = st.number_input(MANUAL_INPUT_TEXT["albedo_label"], value=0.3)
    pitch = st.number_input(MANUAL_INPUT_TEXT["pitch_label"], value=11.0)
    gsHeight = st.number_input(MANUAL_INPUT_TEXT["ground_sculpting_height_label"], value=0.5)
    elevation = st.number_input(MANUAL_INPUT_TEXT["elevation_label"], value=3.0)

elif mode == INPUT_MODE["questionnaire"]:
    if "questionnaire_started" not in st.session_state:
        st.session_state["questionnaire_started"] = False

    if not st.session_state["questionnaire_started"]:
        st.write(QUESTIONNAIRE_UI_TEXT["start_description"])

        if st.button(QUESTIONNAIRE_UI_TEXT["start_button"]):
            state = initialize_questionnaire_state()
            first_question = get_next_question(state)
            field = first_question["field"]
            first_generated_question = generate_question(field, state, api_key, st.session_state.get("user_profile"))
            add_llm_trace(
                st.session_state,
                "pvmaps_question_generator",
                input_summary={
                    "field": field,
                    "state": state,
                    "user_profile": st.session_state.get("user_profile"),
                },
                output={"question": first_generated_question},
                decision="ask_pvmaps_field",
            )
            st.session_state["active_field"] = field
            st.session_state["active_question"] = first_generated_question
            st.session_state["questionnaire_state"] = state
            st.session_state["questionnaire_started"] = True
            st.session_state["questionnaire_ready_to_run"] = False
            st.session_state["chat_messages"] = [
                {
                    "role": "assistant",
                    "content": first_generated_question,
                }
            ]

            st.rerun()
    else:
        state = st.session_state["questionnaire_state"]
        next_question = get_next_question(state)
        for message in st.session_state.get("chat_messages", []):
            with st.chat_message(message["role"]):
                st.write(message["content"])
        if next_question:
            field = st.session_state["active_field"]
            question = st.session_state["active_question"]
            answer = st.chat_input(QUESTIONNAIRE_UI_TEXT["answer_label"], key="questionnaire_input")
            if answer:
                try:
                    raw_answer = answer
                    intent = classify_intent(field, question, raw_answer, api_key)
                    add_llm_trace(
                        st.session_state,
                        "intent_classifier",
                        input_summary={
                            "field": field,
                            "question": question,
                            "user_response": raw_answer,
                        },
                        output={"intent": intent},
                        decision="extract_parameter" if intent == "answer" else "answer_general_question",
                    )

                    if intent != "answer":
                        assistant_answer = answer_general_agpv_question(
                            raw_answer,
                            api_key,
                            user_profile=st.session_state.get("user_profile"),
                            location_context=location_context,
                            pvmaps_state=state,
                            latest_pvmaps_output=st.session_state.get("latest_pvmaps_output"),
                            conversation_history=st.session_state.get("chat_messages", []),
                        )
                        add_llm_trace(
                            st.session_state,
                            "general_agpv_answerer",
                            input_summary={
                                "question": raw_answer,
                                "user_profile": st.session_state.get("user_profile"),
                                "location_context": location_context,
                                "pvmaps_state": state,
                                "conversation_history": st.session_state.get("chat_messages", []),
                            },
                            output={"answer": assistant_answer},
                            decision="answered_question_during_pvmaps_setup",
                        )
                        st.session_state["chat_messages"].append({
                            "role": "user",
                            "content": raw_answer,
                        })
                        st.session_state["chat_messages"].append({
                            "role": "assistant",
                            "content": assistant_answer,
                        })
                        st.rerun()

                    extracted_answer = extract_questionnaire_parameter(field, question, raw_answer, api_key)
                    add_llm_trace(
                        st.session_state,
                        "pvmaps_parameter_extractor",
                        input_summary={
                            "field": field,
                            "question": question,
                            "user_response": raw_answer,
                        },
                        output=extracted_answer,
                        decision="parse_and_update_state" if extracted_answer else "ask_again",
                    )
                    if extracted_answer is None:
                        st.session_state["chat_messages"].append({
                            "role": "user",
                            "content": raw_answer,
                        })

                        st.session_state["chat_messages"].append({
                            "role": "assistant",
                            "content": "I had trouble understanding that. Could you answer again?"
                        })

                        st.rerun()
                    if extracted_answer.get("value") is None:
                        follow_up = extracted_answer.get("follow_up_question") or question
                        st.session_state["active_question"] = follow_up
                        st.session_state["chat_messages"].append({
                            "role": "user",
                            "content": raw_answer,
                        })

                        st.session_state["chat_messages"].append({
                            "role": "assistant",
                            "content": follow_up,
                        })

                        st.rerun()
                    value = extracted_answer["value"]
                    st.write(value)
                    parsed_answer = parse_questionnaire_answer(field, value)
                    update_questionnaire_state(state, field, parsed_answer)
                    st.session_state["questionnaire_state"] = state
                    st.session_state["chat_messages"].append({
                        "role": "user",
                        "content": raw_answer,
                    })

                    next_question = get_next_question(state)
                    if next_question:
                        field = next_question["field"]
                        generated_question = generate_question(field, state, api_key, st.session_state.get("user_profile"))
                        add_llm_trace(
                            st.session_state,
                            "pvmaps_question_generator",
                            input_summary={
                                "field": field,
                                "state": state,
                                "user_profile": st.session_state.get("user_profile"),
                            },
                            output={"question": generated_question},
                            decision="ask_next_pvmaps_field",
                        )
                        st.session_state["active_field"] = field
                        st.session_state["active_question"] = generated_question
                        st.session_state["chat_messages"].append({
                            "role": "assistant",
                            "content": generated_question,
                        })
                    else:
                        st.session_state["questionnaire_ready_to_run"] = True
                        st.session_state["chat_messages"].append({
                            "role": "assistant",
                            "content": QUESTIONNAIRE_UI_TEXT["complete_message"],
                        })
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))
            if st.button(QUESTIONNAIRE_UI_TEXT["defaults_button"]):
                recommendation = generate_recommended_pvmaps_config(
                    api_key,
                    user_profile=st.session_state.get("user_profile"),
                    location_context=location_context,
                    consultation_history=st.session_state.get("consultation_messages", []),
                    current_pvmaps_state=state,
                )
                parsed_recommendation, recommendation_errors = validate_candidate_config(recommendation)
                add_llm_trace(
                    st.session_state,
                    "recommended_pvmaps_config",
                    input_summary={
                        "user_profile": st.session_state.get("user_profile"),
                        "location_context": location_context,
                        "consultation_history": st.session_state.get("consultation_messages", []),
                        "current_pvmaps_state": state,
                    },
                    output={
                        "recommendation": recommendation,
                        "validation_errors": recommendation_errors,
                    },
                    decision="apply_recommendation" if not recommendation_errors else "recommendation_failed",
                )

                if recommendation_errors:
                    st.error(QUESTIONNAIRE_UI_TEXT["recommendation_error"])
                    for error in recommendation_errors:
                        st.write("-", error)
                    st.stop()

                justifications = recommendation.get("justifications", {})
                for field, value in parsed_recommendation.items():
                    if state.get(field) is None:
                        update_questionnaire_state(state, field, value, assumed=True)
                        if field in justifications:
                            state["assumptions"].append(f"{field}: {justifications[field]}")

                st.session_state["questionnaire_state"] = state
                st.session_state["recommended_pvmaps_config"] = recommendation
                st.session_state["questionnaire_ready_to_run"] = True
                st.session_state["chat_messages"].append({
                    "role": "assistant",
                    "content": QUESTIONNAIRE_UI_TEXT["defaults_applied_message"],
                })
                st.rerun()
        else:
            st.session_state["questionnaire_ready_to_run"] = True

        if st.session_state.get("questionnaire_ready_to_run", False):
            assumptions = st.session_state["questionnaire_state"].get("assumptions", [])
            if assumptions:
                st.subheader(QUESTIONNAIRE_UI_TEXT["assumptions_header"])
                for assumption in assumptions:
                    st.write("-", assumption)
            if "recommended_pvmaps_config" in st.session_state:
                st.subheader(QUESTIONNAIRE_UI_TEXT["recommendation_header"])
                st.json(st.session_state["recommended_pvmaps_config"].get("justifications", {}))

can_run_pvmaps = (
    mode == INPUT_MODE["manual"]
    or (
        mode == INPUT_MODE["questionnaire"]
        and st.session_state.get("questionnaire_ready_to_run", False)
    )
)

if mode == INPUT_MODE["questionnaire"] and not st.session_state.get("questionnaire_ready_to_run", False):
    st.write(QUESTIONNAIRE_UI_TEXT["not_ready_message"])

if can_run_pvmaps:
    st.subheader("Review simulation setup")

    if mode == INPUT_MODE["manual"]:
        review_data = {
            "location": address,
            "latitude": lat,
            "longitude": lon,
            "panel_model": panel_model,
            "array_config": config,
            "tilt": tilt,
            "azimuth": azimuth,
            "albedo": albedo,
            "pitch": pitch,
            "ground_sculpting_height": gsHeight,
            "array_elevation": elevation,
        }
    else:
        questionnaire_state = st.session_state["questionnaire_state"]
        review_data = {
            "location": address,
            "latitude": lat,
            "longitude": lon,
            "panel_model": questionnaire_state["panel_model"],
            "array_config": questionnaire_state["array_config"],
            "tilt": questionnaire_state["tilt"],
            "azimuth": questionnaire_state["azimuth"],
            "albedo": questionnaire_state["albedo"],
            "pitch": questionnaire_state["pitch"],
            "ground_sculpting_height": questionnaire_state["gs_height"],
            "array_elevation": questionnaire_state["array_elevation"],
        }

    st.json(review_data)

if can_run_pvmaps and st.button(PVMAPS_RUN_TEXT["run_button"]):
    if mode == INPUT_MODE["manual"]:
        pvmaps_input = create_default_pvmaps_input(
            lat,
            lon,
            cell_tech,
            height,
            direct_eff,
            diffuse_eff,
            tcoeff,
            config,
            tilt,
            azimuth,
            albedo,
            pitch,
            gsHeight,
            elevation
        )
    else:
        if "questionnaire_state" not in st.session_state:
            st.error(QUESTIONNAIRE_UI_TEXT["start_first_error"])
            st.stop()

        state = st.session_state["questionnaire_state"]
        pvmaps_input = build_pvmaps_input_from_questionnaire(state, lat, lon)

    errors = validate_pvmaps_input(pvmaps_input)
    if errors:
        st.error(PVMAPS_RUN_TEXT["validation_error"])
        for error in errors:
            st.write("-", error)
    else:
        try:
            with st.spinner(PVMAPS_RUN_TEXT["spinner"]):
                output = run_pvmaps(
                    pvmaps_input,
                    r"D:/agpv-ai-consultant/PV-MAPS-main"
                )
                st.session_state["latest_pvmaps_input"] = pvmaps_input
                st.session_state["latest_pvmaps_output"] = output
                st.session_state["latest_pvmaps_explanation"] = explain_output(
                    output,
                    api_key,
                    st.session_state.get("user_profile"),
                )
                add_llm_trace(
                    st.session_state,
                    "pvmaps_output_explainer",
                    input_summary={
                        "pvmaps_output": output,
                        "user_profile": st.session_state.get("user_profile"),
                    },
                    output={"explanation": st.session_state["latest_pvmaps_explanation"]},
                    decision="explain_latest_estimate",
                )
                st.session_state.setdefault("post_result_messages", [])
        except Exception as error:
            st.error(PVMAPS_RUN_TEXT["simulation_error"])
            st.write(PVMAPS_RUN_TEXT["simulation_error_detail"])
            st.code(str(error))
            st.stop()

if "latest_pvmaps_output" in st.session_state:
    latest_output = st.session_state["latest_pvmaps_output"]

    st.subheader(LOCATION_TEXT["result_location_header"])
    st.write(address)

    st.subheader(RESULT_TEXT["result_header"])
    st.write(st.session_state.get("latest_pvmaps_explanation"))

    st.subheader(RESULT_TEXT["monthly_yield_header"])

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(MONTH_LABELS, latest_output["monthly_yield"])
    ax.set_xlabel(RESULT_TEXT["chart_x_label"])
    ax.set_ylabel(f"Yield ({latest_output['yield_unit']})")
    ax.set_title(RESULT_TEXT["chart_title"])
    ax.tick_params(axis="x", labelrotation=45)
    st.pyplot(fig)

    st.subheader(RESULT_TEXT["follow_up_header"])

    if "post_result_messages" not in st.session_state:
        st.session_state["post_result_messages"] = []

    for message in st.session_state["post_result_messages"]:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    follow_up = st.chat_input(RESULT_TEXT["follow_up_label"], key="post_result_input")
    if follow_up:
        full_conversation_history = {
            "consultation_messages": st.session_state.get("consultation_messages", []),
            "questionnaire_messages": st.session_state.get("chat_messages", []),
            "post_result_messages": st.session_state.get("post_result_messages", []),
        }
        answer = answer_general_agpv_question(
            follow_up,
            api_key,
            user_profile=st.session_state.get("user_profile"),
            location_context=location_context,
            pvmaps_state=st.session_state.get("questionnaire_state"),
            latest_pvmaps_output=latest_output,
            conversation_history=full_conversation_history,
        )
        add_llm_trace(
            st.session_state,
            "post_result_answerer",
            input_summary={
                "question": follow_up,
                "user_profile": st.session_state.get("user_profile"),
                "location_context": location_context,
                "latest_pvmaps_output": latest_output,
                "conversation_history": full_conversation_history,
            },
            output={"answer": answer},
            decision="answered_follow_up_after_estimate",
        )
        st.session_state["post_result_messages"].append({
            "role": "user",
            "content": follow_up,
        })
        st.session_state["post_result_messages"].append({
            "role": "assistant",
            "content": answer,
        })
        st.rerun()
