import streamlit as st
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv

from constants import (
    APP_TITLE,
    LOCATION_TEXT,
    MONTH_LABELS,
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
from services.location_geocoder import geocode_location
from llm.consultation_planner import plan_next_consultation_step
from llm.general_agpv_answerer import answer_general_agpv_question
from services.llm_trace import add_llm_trace
from services.pvmaps_estimate_service import run_recommended_pvmaps_estimate

load_dotenv()
api_key = os.getenv("PURDUE_GENAI_KEY")

st.title(APP_TITLE)


def start_consultation(location_context):
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
        return

    st.session_state["goal_follow_up_messages"] = [
        {
            "role": "assistant",
            "content": plan["question"],
        }
    ]


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
            start_consultation(location_context)
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
        start_consultation(location_context)
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

if "post_consultation_route" not in st.session_state:
    st.session_state["post_consultation_route"] = "general_chat"

# Legacy route kept for reference.
# Current app flow triggers PVMAPS from general chat using run_recommended_pvmaps_estimate.
# if st.session_state["post_consultation_route"] == "pvmaps_setup":
#     try:
#         run_recommended_pvmaps_estimate(st.session_state, api_key, location_context)
#     except Exception as error:
#         st.session_state.setdefault("general_chat_messages", [])
#         st.session_state["general_chat_messages"].append({
#             "role": "assistant",
#             "content": "I tried to run a background solar-yield estimate, but PVMAPS could not complete the simulation. We can keep discussing the setup and assumptions.",
#         })
#         add_llm_trace(
#             st.session_state,
#             "pvmaps_background_tool",
#             input_summary={"location_context": location_context},
#             output={"error": str(error)},
#             decision="background_estimate_failed",
#         )
#     st.session_state["post_consultation_route"] = "general_chat"
#     st.rerun()

if st.session_state["post_consultation_route"] == "general_chat":
    if GENERAL_CHAT_UI_TEXT["description"]:
        st.write(GENERAL_CHAT_UI_TEXT["description"])

    if "latest_pvmaps_output" in st.session_state:
        latest_output = st.session_state["latest_pvmaps_output"]
        with st.expander(RESULT_TEXT["latest_estimate_header"], expanded=False):
            st.subheader(LOCATION_TEXT["result_location_header"])
            st.write(address or "No confirmed site location")

            st.subheader(RESULT_TEXT["monthly_yield_header"])
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.bar(MONTH_LABELS, latest_output["monthly_yield"])
            ax.set_xlabel(RESULT_TEXT["chart_x_label"])
            ax.set_ylabel(f"Yield ({latest_output['yield_unit']})")
            ax.set_title(RESULT_TEXT["chart_title"])
            ax.tick_params(axis="x", labelrotation=45)
            st.pyplot(fig)

    if "general_chat_messages" not in st.session_state:
        st.session_state["general_chat_messages"] = list(st.session_state.get("goal_follow_up_messages", []))

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
