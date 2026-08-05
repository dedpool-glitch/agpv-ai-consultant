import streamlit as st
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv

from constants import (
    APP_TITLE,
    LOCATION_TEXT,
    MONTH_LABELS,
    CHAT_UI_TEXT,
    RESULT_TEXT,
    USER_PROFILE_TEXT,
    USER_TYPE_OPTIONS,
    SOLAR_EXPERIENCE_OPTIONS,
    DATASHEET_UPLOAD_TEXT,
    PROJECT_GOAL_OPTIONS,
    TRACE_UI_TEXT
)
from services.location_geocoder import geocode_location
from llm.consultation_planner import route_conversation_turn
from llm.general_agpv_answerer import answer_general_agpv_question
from llm.rag_source_router import decide_rag_source
from rag.pipeline import retrieve_for_source, summarize_retrieved_chunks
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
            st.session_state["chat_messages"] = [{
                "role": "assistant",
                "content": CHAT_UI_TEXT["opening_message"],
            }]
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

st.session_state.setdefault("chat_messages", [{
    "role": "assistant",
    "content": CHAT_UI_TEXT["opening_message"],
}])
st.session_state.setdefault("pvmaps_runs", [])

if CHAT_UI_TEXT["description"]:
    st.write(CHAT_UI_TEXT["description"])

for message in st.session_state["chat_messages"]:
    if message.get("type") == "pvmaps_run":
        run_index = message["run_index"]
        pvmaps_runs = st.session_state.get("pvmaps_runs", [])
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
    st.session_state["chat_messages"].append({
        "role": "user",
        "content": question,
    })

    plan = route_conversation_turn(
        api_key,
        user_profile=st.session_state.get("user_profile"),
        location_context=location_context,
        conversation_history=st.session_state["chat_messages"],
        pvmaps_runs=st.session_state.get("pvmaps_runs", []),
    )
    add_llm_trace(
        st.session_state,
        "turn_router",
        input_summary={
            "user_profile": st.session_state.get("user_profile"),
            "location_context": location_context,
            "conversation_history": st.session_state["chat_messages"],
            "pvmaps_runs": st.session_state.get("pvmaps_runs", []),
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
            st.session_state["location_context"] = location_context
            add_llm_trace(
                st.session_state,
                "location_geocoder",
                input_summary={"mentioned_location": plan["mentioned_location"]},
                output=location_context,
                decision="location_updated",
            )
        except Exception as error:
            st.session_state["chat_messages"].append({
                "role": "assistant",
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

    if plan["turn_type"] == "gather_info" and plan.get("question"):
        st.session_state["chat_messages"].append({
            "role": "assistant",
            "content": plan["question"],
        })

    elif plan["turn_type"] == "run_pvmaps":
        try:
            run_recommended_pvmaps_estimate(
                st.session_state,
                api_key,
                location_context,
                latest_user_message=question,
            )
        except Exception as error:
            st.session_state["chat_messages"].append({
                "role": "assistant",
                "content": "I tried to run a solar-yield estimate, but PVMAPS could not complete the simulation. We can keep discussing the setup and assumptions.",
            })
            add_llm_trace(
                st.session_state,
                "pvmaps_background_tool",
                input_summary={"location_context": location_context},
                output={"error": str(error)},
                decision="estimate_failed",
            )

    else:
        pvmaps_runs = st.session_state.get("pvmaps_runs", [])
        latest_pvmaps_output = pvmaps_runs[-1]["output"] if pvmaps_runs else None

        retrieved_context = []
        try:
            rag_plan = decide_rag_source(
                question,
                api_key,
                conversation_history=st.session_state["chat_messages"],
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
            user_profile=st.session_state.get("user_profile"),
            location_context=location_context,
            pvmaps_state=st.session_state.get("questionnaire_state"),
            latest_pvmaps_output=latest_pvmaps_output,
            conversation_history=st.session_state["chat_messages"],
            retrieved_context=retrieved_context,
        )
        add_llm_trace(
            st.session_state,
            "general_agpv_answerer",
            input_summary={
                "question": question,
                "user_profile": st.session_state.get("user_profile"),
                "location_context": location_context,
                "conversation_history": st.session_state["chat_messages"],
                "retrieved_context_count": len(retrieved_context),
            },
            output={"answer": answer},
            decision="answered_general_question",
        )
        st.session_state["chat_messages"].append({
            "role": "assistant",
            "content": answer,
        })

    st.rerun()
