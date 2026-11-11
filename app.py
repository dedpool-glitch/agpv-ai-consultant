import streamlit as st
import copy
import json
import os
import time
import uuid
from datetime import date
from dotenv import load_dotenv
import pandas as pd

import traceback 

from constants import (
    ACCESS_PASSCODE_ENV_VAR,
    ACCESS_PASSCODE_TEXT,
    SESSION_KEY_ACCESS_PASSCODE_OK,
    API_KEY_TEXT,
    APP_TITLE,
    LOCATION_TEXT,
    CHAT_UI_TEXT,
    EXPERT_MODE_TEXT,
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
    PROCESSING_STATUS_TEXT,
    SESSION_KEY_API_KEY,
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
    UNAVAILABLE_ARRAY_CONFIGS,
)


from services.location_geocoder import geocode_location
from llm.consultation_planner import route_conversation_turn
from llm.client import DEFAULT_MODEL
from llm.expert_followup_answerer import answer_expert_followup_question
from llm.general_agpv_answerer import answer_general_agpv_question
from llm.rag_source_router import decide_rag_source, plan_expert_retrieval
from models.pvmaps.descriptor import (
    build_pvmaps_input_from_descriptor_values,
    get_pvmaps_input_descriptors,
    validate_pvmaps_descriptor_input,
)
from models.simple.crops import CROP_FILES
from rag.pipeline import retrieve_for_source, summarize_retrieved_chunks
from services.conversation_log import log_conversation_turn
from services.expert_estimate_service import run_expert_pvmaps_estimate
from services.combined_estimate_service import run_combined_estimate
from services.llm_trace import add_llm_trace
from services.guided_crop_request import resolve_crop_analysis, resolve_crop_inputs
from services.guided_simple_estimate_service import run_guided_open_sky_estimate
from services.run_context import compact_run
from services.simulation_log import log_simulation_run
from services.pvmaps_estimate_service import run_recommended_pvmaps_estimate
from ui.simulation_result import render_simulation_result
from ui.simulation_comparison import distinct_solar_runs, render_simulation_comparison
from ui.simulation_export import render_simulation_exports
from ui.conversation_export import render_conversation_export
from ui.crop_visualization import render_crop_with_pv
from ui.crop_comparison import render_crop_comparison
from ui.personal_library import render_personal_library, render_retrieved_sources
from services.personal_library import search_documents

load_dotenv()
st.set_page_config(layout="wide", initial_sidebar_state="collapsed")

PENDING_CHAT_QUESTION_KEY = "pending_chat_question"
PENDING_CROP_REQUEST_KEY = "pending_crop_request"

# One id per browser session, used only to group conversation_log.jsonl rows
# back into a single conversation later -- not tied to any account/identity.
st.session_state.setdefault("session_id", uuid.uuid4().hex)

# Access passcode: only active when AGPV_ACCESS_PASSCODE is set in the
# environment (e.g. for an ngrok-tunneled demo). Local development with no
# such env var never sees this screen. Not real per-student authentication --
# just a lightweight filter for a link that's reachable by anyone who has it.
_access_passcode = os.getenv(ACCESS_PASSCODE_ENV_VAR)
if _access_passcode:
    st.session_state.setdefault(SESSION_KEY_ACCESS_PASSCODE_OK, False)
    if not st.session_state[SESSION_KEY_ACCESS_PASSCODE_OK]:
        st.title(APP_TITLE)
        st.subheader(ACCESS_PASSCODE_TEXT["header"])
        st.write(ACCESS_PASSCODE_TEXT["description"])
        entered_passcode = st.text_input(ACCESS_PASSCODE_TEXT["label"], type="password")
        if st.button(ACCESS_PASSCODE_TEXT["submit_button"]):
            if not entered_passcode:
                st.error(ACCESS_PASSCODE_TEXT["missing_code_error"])
            elif entered_passcode == _access_passcode:
                st.session_state[SESSION_KEY_ACCESS_PASSCODE_OK] = True
                st.rerun()
            else:
                st.error(ACCESS_PASSCODE_TEXT["wrong_code_error"])
        st.stop()

# API key: prefer the env var (so a locally-configured deployment, e.g. for
# rehearsals, never sees this screen), otherwise fall back to a key entered
# by the user for this session only.
st.session_state.setdefault(SESSION_KEY_API_KEY, None)
api_key = os.getenv(GENAI_API_KEY_ENV_VAR) or st.session_state[SESSION_KEY_API_KEY]

if not api_key:
    st.title(APP_TITLE)
    st.subheader(API_KEY_TEXT["header"])
    st.write(API_KEY_TEXT["description"])
    entered_api_key = st.text_input(API_KEY_TEXT["label"], type="password")
    if st.button(API_KEY_TEXT["submit_button"]):
        if entered_api_key:
            st.session_state[SESSION_KEY_API_KEY] = entered_api_key
            st.rerun()
        else:
            st.error(API_KEY_TEXT["missing_key_error"])
    st.stop()


def _descriptor_label(field):
    unit = field.get("unit")
    return f"{field['name']} ({unit})" if unit and unit != "1" else field["name"]


def _chat_api_error_message(error):
    response = getattr(error, "response", None)
    status_code = getattr(response, "status_code", None)
    if status_code in (401, 403):
        return "The AI service rejected the API key. Please check your Purdue GenAI API key and try again."
    if status_code == 429:
        return "The AI service rate limit was reached. Please wait briefly and try again."
    return "The AI service could not respond. Your message has been kept; please try again shortly."


def _requests_crop_estimate(message):
    normalized = " ".join(str(message or "").casefold().split())
    crop_topic = (
        "crop yield" in normalized or "grain yield" in normalized
        or "simple model" in normalized
        or ("yield" in normalized and any(crop in normalized for crop in CROP_FILES))
    )
    new_estimate = any(phrase in normalized for phrase in (
        "estimate", "calculate", "predict", "simulate", "run ",
        "what would", "what will", "how much", "what is my", "give me",
    ))
    return crop_topic and new_estimate

# Render the forms based on model description provided in pvmaps.json 
def _render_descriptor_input(field, container=st, disabled=False):
    constraints = field.get("constraints") or {}
    metadata = field.get("metadata") or {}
    allowed_values = constraints.get("allowed_values")
    label = _descriptor_label(field)
    if disabled:
        label += " (not used for this setup)"
    help_text = field.get("description") or None
    default = field.get("default")

    if allowed_values:
        if field["id"] == "array.config":
            allowed_values = [
                value for value in allowed_values
                if value not in UNAVAILABLE_ARRAY_CONFIGS
            ]
        default_index = allowed_values.index(default) if default in allowed_values else 0
        return container.selectbox(
            label,
            options=allowed_values,
            index=default_index,
            help=help_text,
            key=f"expert_{field['id']}",
        )

    if field.get("element_type") == "boolean":
        return container.checkbox(
            label,
            value=bool(default),
            help=help_text,
            key=f"expert_{field['id']}",
        )

    number_type = int if field.get("element_type") == "integer" else float
    step = number_type(
        metadata.get("step", 1 if field.get("element_type") == "integer" else 0.1)
    )
    number_options = {
        "label": label,
        "value": number_type(default),
        "step": step,
        "help": help_text,
        "key": f"expert_{field['id']}",
        "disabled": disabled,
    }
    if metadata.get("format"):
        number_options["format"] = metadata["format"]
    if constraints.get("min") is not None:
        minimum = number_type(constraints["min"])
        number_options["min_value"] = (
            minimum + step if constraints.get("exclusive_min") else minimum
        )
    if constraints.get("max") is not None:
        number_options["max_value"] = number_type(constraints["max"])
    return container.number_input(**number_options)


st.session_state.setdefault(SESSION_KEY_APP_MODE, None)

if st.session_state[SESSION_KEY_APP_MODE] is None:
    _, landing_column, _ = st.columns([1, 4, 1])
    with landing_column:
        st.title(APP_TITLE)
        st.subheader(EXPERT_MODE_TEXT["mode_selector_header"])
        guided_column, expert_column = st.columns([1, 1], gap="medium")
        with guided_column, st.container(border=True, width="stretch", height=260):
            st.markdown("#### Guided mode")
            st.write(EXPERT_MODE_TEXT["non_expert_description"])
            st.caption("Ask about solar yield, crop yield without panels, or both together.")
            if st.button(EXPERT_MODE_TEXT["non_expert_button"], type="primary", width="stretch"):
                st.session_state[SESSION_KEY_APP_MODE] = APP_MODE_NON_EXPERT
                st.rerun()
        with expert_column, st.container(border=True, width="stretch", height=260):
            st.markdown("#### Expert mode")
            st.write(EXPERT_MODE_TEXT["expert_description"])
            st.caption("Run and compare solar or combined estimates.")
            if st.button(EXPERT_MODE_TEXT["expert_button"], type="primary", width="stretch"):
                st.session_state[SESSION_KEY_APP_MODE] = APP_MODE_EXPERT
                st.rerun()
    st.stop()

def render_trace_details():
    traces = st.session_state.get(SESSION_KEY_LLM_TRACE) or []
    if not traces:
        st.write(TRACE_UI_TEXT["empty_message"])
        return
    st.caption("How the assistant handled this session. Open a step to inspect its technical details.")
    show_all = st.toggle("Show all activity", value=False) if len(traces) > 8 else False
    visible_traces = traces if show_all else traces[-8:]
    if len(traces) > 8 and not show_all:
        st.caption(f"Showing the latest 8 of {len(traces)} steps.")
    stage_labels = {
        "turn_router": "Interpreting the request",
        "recommendation_context_retrieval": "Checking research for PV recommendations",
        "recommended_pvmaps_config": "Choosing PV inputs",
        "pvmaps_background_tool": "PV-MAPS solar simulation",
        "combined_simulation": "PV-MAPS + SIMPLE simulation",
        "guided_simple_run": "SIMPLE crop simulation",
        "expert_mode_pvmaps_run": "PV-MAPS solar simulation",
        "expert_combined_run": "PV-MAPS + SIMPLE simulation",
    }
    first_index = len(traces) - len(visible_traces) + 1
    for index, trace in enumerate(visible_traces, start=first_index):
        label = stage_labels.get(trace['stage'], trace['stage'].replace('_', ' ').title())
        with st.expander(f"{index}. {label} · {trace['time']}", expanded=False):
            if trace.get("decision"):
                st.write("Decision:", trace["decision"].replace("_", " "))
            if trace.get("input") is not None:
                st.caption("Input")
                st.json(trace["input"], expanded=False)
            if trace.get("output") is not None:
                st.caption("Output")
                st.json(trace["output"], expanded=False)


@st.dialog(TRACE_UI_TEXT["header"], width="large")
def show_trace_dialog():
    render_trace_details()


def retrieve_personal_context(query):
    try:
        chunks = search_documents(query, n_results=3)
    except Exception as error:
        st.warning("My library could not be searched for this question.")
        add_llm_trace(
            st.session_state, "personal_library_retrieval",
            input_summary={"query": query}, output={"error": str(error)},
            decision="personal_retrieval_failed",
        )
        return []
    if chunks:
        add_llm_trace(
            st.session_state, "personal_library_retrieval",
            input_summary={"query": query},
            output={"retrieved_count": len(chunks),
                    "sources": summarize_retrieved_chunks(chunks)},
            decision="personal_chunks_retrieved",
        )
    return chunks


def render_workspace_header(mode, location_context=None):
    """Keep mode, site, and library controls together below the app title."""
    st.title(APP_TITLE)
    # One control per concept, and the control is its own label: a mode toggle,
    # a site chip, and the library chip. Session context (mode, site) sits on
    # the left; the library tool sits alone on the right. Every item here is a
    # content-width widget -- no bare text elements, which stretch to fill the
    # row and push neighbors apart.
    left_column, right_column = st.columns([8, 1.7], gap="small", vertical_alignment="center")
    toolbar = left_column.container(horizontal=True, gap="small", vertical_alignment="center")
    library_slot = right_column.container(horizontal=True, horizontal_alignment="right")

    mode_labels = {APP_MODE_NON_EXPERT: "Guided", APP_MODE_EXPERT: "Expert"}
    with toolbar:
        selected_mode = st.segmented_control(
            "Mode", options=list(mode_labels), default=mode,
            format_func=mode_labels.get, required=True,
            key=f"{mode}_mode_switch", label_visibility="collapsed",
        )
    if selected_mode and selected_mode != mode:
        st.session_state[SESSION_KEY_APP_MODE] = selected_mode
        st.rerun()

    def render_header_tools(key_prefix):
        with library_slot:
            render_personal_library(key_prefix)
            if st.session_state.get(SESSION_KEY_LLM_TRACE):
                if st.button("Activity", icon=":material/history:", key=f"{key_prefix}_activity"):
                    show_trace_dialog()

    if mode == APP_MODE_EXPERT:
        render_header_tools("expert")
        return

    location_context = location_context or {}
    lat = location_context.get("latitude")
    lon = location_context.get("longitude")
    address = location_context.get("confirmed_address")
    if address:
        site_label = location_context.get("site_location") or ", ".join(address.split(",")[:2])
        site_help = "Change site"
    else:
        site_label = "Add site"
        site_help = None

    with toolbar, st.popover(site_label, icon=":material/location_on:", help=site_help):
        if address:
            st.write(f"Matched address: {address}")
            st.write(f"Latitude: {lat:.6f}° · Longitude: {lon:.6f}°")
            st.caption("The map pin shows the matched location, not a verified farm boundary.")
            st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}), zoom=12, height=240)
        with st.form("guided_site_change_form"):
            new_site = st.text_input(
                "Search for a site", value=location_context.get("site_location") or "",
                placeholder="City, state or region",
            )
            change_site = st.form_submit_button("Use this site")
        if change_site:
            try:
                coordinates = geocode_location(new_site)
            except Exception:
                st.error("I could not confirm that location. Try a more specific city or region.")
            else:
                st.session_state[SESSION_KEY_LOCATION_CONTEXT] = {
                    "site_location": new_site.strip(),
                    "confirmed_address": coordinates["address"],
                    "latitude": coordinates["latitude"],
                    "longitude": coordinates["longitude"],
                }
                st.session_state.pop(SESSION_KEY_QUESTIONNAIRE_STATE, None)
                st.rerun()
    render_header_tools("guided")


# Expert mode interface 
if st.session_state[SESSION_KEY_APP_MODE] == APP_MODE_EXPERT:
    render_workspace_header(APP_MODE_EXPERT)
    st.subheader(EXPERT_MODE_TEXT["form_header"])
    st.session_state.setdefault("expert_runs", [])
    expert_analysis = st.radio(
        "Analysis", ["Solar yield", "Solar + crop yield"], horizontal=True,
        key="expert_analysis",
    )
    st.caption(
        "Runs PV-MAPS for solar output and SIMPLE for crop yield using modeled ground light."
        if expert_analysis == "Solar + crop yield"
        else "Runs PV-MAPS for solar output."
    )

    # Fields render in a grid, this many per row, grouped under each
    # section header -- uses the full page width instead of a narrow
    # single column, and keeps related fields (e.g. tilt/azimuth) side
    # by side instead of scattered across a long vertical scroll.
    FIELDS_PER_ROW = 3

    # Lat/lon are part of the descriptor like any other input, but nobody
    # actually knows their site's decimal coordinates -- render these two
    # specially as a location lookup instead of raw number fields.
    st.markdown("### 1. Site location")
    st.caption("Enter the farm or project site and confirm the resolved address before running.")
    expert_site_location = st.text_input(
        LOCATION_TEXT["input_label"], key="expert_site_location"
    )
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
    if (expert_location_context and
            expert_location_context["site_location"] != expert_site_location):
        expert_location_context = None
        st.session_state["expert_location_context"] = None
        st.warning("The location text changed. Confirm the new site to use its coordinates.")
    if expert_location_context:
        st.success(f"Using location: {expert_location_context['confirmed_address']}")

    crop_name = None
    sowing_date = None
    if expert_analysis == "Solar + crop yield":
        st.markdown("### 2. Crop and planting")
        crop_name = st.selectbox(
            "Crop type", list(CROP_FILES),
            format_func=str.title,
        )
        st.caption(
            "These four crops have specification files in the supplied SIMPLE model. "
            "Maize uses its calibrated specification."
        )
        sowing_date = st.date_input("Sowing date", value=date(2024, 5, 15))
        st.info(
            "Model assumptions: fixed soil settings and no water stress. "
            "If maturity crosses December, the sowing year's weather and ground light repeat. "
            "PV-MAPS supplies a representative light profile for each month."
        )

    st.markdown("### 3. PV configuration" if expert_analysis == "Solar + crop yield"
                else "### 2. PV configuration")

    expert_form_values = {}
    expert_field_groups = {}
    for field in get_pvmaps_input_descriptors():
        if field["id"] in ("lat", "lon"):
            continue
        field_group = field["id"].split(".", 1)[0] if "." in field["id"] else "location"
        expert_field_groups.setdefault(field_group, []).append(field)

    for group_name, group_fields in expert_field_groups.items():
        st.markdown(f"### {group_name.replace('_', ' ').title()}")
        if group_name == "array":
            st.caption(
                "GSVBF is temporarily unavailable with the bundled PVMAPS "
                "simulator; fixed and tracking configurations remain available."
            )

        # Checkboxes render as compact inline controls while number/select
        # fields render as full bordered boxes below their label -- mixing
        # the two in one row looks uneven, so render each kind in its own
        # rows instead of interleaving them.
        toggle_fields = [f for f in group_fields if f.get("element_type") == "boolean"]
        other_fields = [f for f in group_fields if f.get("element_type") != "boolean"]

        for fields_of_one_kind in (other_fields, toggle_fields):
            for row_start in range(0, len(fields_of_one_kind), FIELDS_PER_ROW):
                row_fields = fields_of_one_kind[row_start:row_start + FIELDS_PER_ROW]
                row_columns = st.columns(FIELDS_PER_ROW)
                for column, field in zip(row_columns, row_fields):
                    expert_form_values[field["id"]] = _render_descriptor_input(
                        field, column,
                        disabled=(
                            field["id"] == "array.tilt"
                            and expert_form_values.get("array.config") in ("tracking", "GSVBF")
                        ),
                    )

    expert_action_label = (
        "Estimate solar + crop yield" if expert_analysis == "Solar + crop yield"
        else EXPERT_MODE_TEXT["run_button"]
    )
    if st.button(expert_action_label, type="primary"):
        if not expert_location_context:
            st.error(EXPERT_MODE_TEXT["missing_location_error"])
        else:
            expert_status = st.status(
                PROCESSING_STATUS_TEXT["validation"],
                expanded=False,
            )
            expert_form_values["lat"] = expert_location_context["latitude"]
            expert_form_values["lon"] = expert_location_context["longitude"]
            expert_pvmaps_input = build_pvmaps_input_from_descriptor_values(
                expert_form_values
            )
            print("PVMAPS input:\n" + json.dumps(expert_pvmaps_input, indent=2))

            expert_errors = validate_pvmaps_descriptor_input(expert_pvmaps_input)
            if expert_errors:
                expert_status.update(
                    label=PROCESSING_STATUS_TEXT["failed"],
                    state="error",
                )
                st.error(EXPERT_MODE_TEXT["validation_error_header"])
                for expert_error in expert_errors:
                    st.write(f"- {expert_error}")
            else:
                try:
                    crop_result = None
                    if expert_analysis == "Solar + crop yield":
                        expert_status.update(label="Running PV-MAPS and SIMPLE...")
                        combined = run_combined_estimate(
                            expert_pvmaps_input, crop_name, sowing_date,
                        )
                        expert_output = combined["pv"]
                        crop_result = combined["crop"]
                        expert_explanation = (
                            f"SIMPLE estimates {crop_result['mean_grain_yield_t_ha']:.2f} t/ha "
                            f"mean {crop_name} grain yield, with maturity on "
                            f"{crop_result['maturity_date']}. The PV and crop estimates use "
                            "the site and inputs shown above. Crop assumptions are listed below."
                        )
                    else:
                        expert_output, expert_explanation = run_expert_pvmaps_estimate(
                            st.session_state,
                            expert_pvmaps_input,
                            api_key,
                            status_callback=lambda message: expert_status.update(
                                label=message
                            ),
                        )
                    st.session_state["expert_last_run"] = {
                        "analysis": "solar_and_crop" if crop_result else "solar",
                        "label": "Solar + crop estimate" if crop_result else "Solar-yield estimate",
                        "location_context": copy.deepcopy(expert_location_context),
                        "input_provenance": {"source": "expert_form"},
                        "input": expert_pvmaps_input,
                        "output": expert_output,
                        "explanation": expert_explanation,
                        "crop_result": crop_result,
                    }
                    st.session_state["expert_runs"].append(
                        copy.deepcopy(st.session_state["expert_last_run"])
                    )
                    log_simulation_run(
                        st.session_state["session_id"], "expert",
                        st.session_state["expert_last_run"],
                    )
                    log_conversation_turn(
                        st.session_state["session_id"], "expert", "run_model",
                        expert_analysis, expert_explanation,
                        extra={
                            "analysis": "solar_and_crop" if crop_result else "solar",
                            "location_context": expert_location_context,
                            "crop": crop_name if crop_result else None,
                            "sowing_date": sowing_date.isoformat() if crop_result else None,
                            "solar_yield": expert_output.get("yearly_yield"),
                            "solar_yield_unit": expert_output.get("yield_unit"),
                            "mean_grain_yield_t_ha": (
                                crop_result["mean_grain_yield_t_ha"] if crop_result else None
                            ),
                        },
                    )
                    if crop_result:
                        add_llm_trace(
                            st.session_state, "expert_combined_run",
                            input_summary={
                                "crop": crop_name, "sowing_date": sowing_date.isoformat(),
                                "pvmaps_input": expert_pvmaps_input,
                            },
                            output={
                                "solar_yield": expert_output.get("yearly_yield"),
                                "solar_unit": expert_output.get("yield_unit"),
                                "mean_crop_yield_t_ha": crop_result["mean_grain_yield_t_ha"],
                                "maturity_date": crop_result["maturity_date"],
                            },
                            decision="combined_estimate_completed",
                        )
                    # A new run means any previous follow-up chat no longer
                    # applies to what's on screen -- start fresh.
                    st.session_state["expert_chat_messages"] = []
                    expert_status.update(
                        label=PROCESSING_STATUS_TEXT["complete"],
                        state="complete",
                    )
                except Exception as error:
                    expert_status.update(
                        label=PROCESSING_STATUS_TEXT["failed"],
                        state="error",
                    )
                    st.error(
                        "The PV-MAPS + SIMPLE estimate could not complete."
                        if expert_analysis == "Solar + crop yield"
                        else "The PV-MAPS estimate could not complete."
                    )
                    add_llm_trace(
                        st.session_state,
                        "expert_combined_run" if expert_analysis == "Solar + crop yield"
                        else "expert_mode_pvmaps_run",
                        input_summary={"pvmaps_input": expert_pvmaps_input},
                        output={"error": str(error)},
                        decision="expert_estimate_failed",
                    )
                    log_conversation_turn(
                        st.session_state["session_id"], "expert", "run_model",
                        expert_analysis, "Simulation failed",
                        extra={"analysis": "solar_and_crop" if expert_analysis == "Solar + crop yield"
                               else "solar", "error": str(error)},
                    )
                    st.error(traceback.format_exc())

    expert_last_run = st.session_state.get("expert_last_run")

    # Visualize the PVMAPS' output -- below the form, full width.
    if expert_last_run:
        render_simulation_result(expert_last_run)
        if expert_last_run.get("crop_result"):
            render_crop_with_pv(expert_last_run)
        else:
            st.subheader(EXPERT_MODE_TEXT["explanation_header"])
            st.write(expert_last_run["explanation"])

        render_crop_comparison(st.session_state["expert_runs"], "expert")

        # Follow-up chat about this specific run, grounded in the same
        # input/output plus RAG context -- resets whenever a new run
        # happens (see the reset next to expert_last_run above).
        st.subheader("Ask about this result")
        st.session_state.setdefault("expert_chat_messages", [])
        for expert_chat_message in st.session_state["expert_chat_messages"]:
            with st.chat_message(expert_chat_message["role"]):
                st.write(expert_chat_message["content"])
                render_retrieved_sources(expert_chat_message.get("retrieved_sources"))

        expert_export_messages = [
            {
                "role": MESSAGE_ROLE_ASSISTANT,
                "type": MESSAGE_TYPE_PVMAPS_RUN,
                "run_index": 0,
            },
            {
                "role": MESSAGE_ROLE_ASSISTANT,
                "content": expert_last_run["explanation"],
            },
            *st.session_state["expert_chat_messages"],
        ]
        with st.expander("Downloads", expanded=False):
            render_simulation_exports([expert_last_run], "expert")
            render_conversation_export(
                expert_export_messages, [expert_last_run], "expert"
            )

        expert_followup_question = st.chat_input(
            "Ask a question about this result", key="expert_chat_input"
        )
        if expert_followup_question:
            st.session_state["expert_chat_messages"].append({
                "role": MESSAGE_ROLE_USER,
                "content": expert_followup_question,
            })

            with st.chat_message(MESSAGE_ROLE_USER):
                st.write(expert_followup_question)

            with st.status(
                PROCESSING_STATUS_TEXT["retrieval"],
                expanded=False,
            ) as expert_followup_status:
                expert_turn_started_at = time.perf_counter()
                expert_retrieval_error = None
                try:
                    expert_query_plan = plan_expert_retrieval(
                        expert_followup_question, api_key,
                        st.session_state["expert_chat_messages"],
                    )
                    expert_followup_context = retrieve_for_source(
                        "both", expert_query_plan["retrieval_query"]
                    )
                except Exception as error:
                    expert_followup_context = []
                    expert_retrieval_error = str(error)
                    expert_query_plan = {"retrieval_query": expert_followup_question, "query_mode": "fallback"}

                expert_followup_context = (
                    retrieve_personal_context(expert_query_plan["retrieval_query"])
                    + expert_followup_context
                )

                expert_followup_status.update(
                    label=PROCESSING_STATUS_TEXT["answer"]
                )
                try:
                    expert_followup_answer = answer_expert_followup_question(
                        expert_followup_question,
                        api_key,
                        expert_last_run["input"],
                        expert_last_run["output"],
                        expert_last_run["explanation"],
                        conversation_history=st.session_state["expert_chat_messages"],
                        retrieved_context=expert_followup_context,
                    )
                except Exception:
                    expert_followup_status.update(
                        label=PROCESSING_STATUS_TEXT["failed"],
                        state="error",
                    )
                    raise
                st.session_state["expert_chat_messages"].append({
                    "role": MESSAGE_ROLE_ASSISTANT,
                    "content": expert_followup_answer,
                    "retrieved_sources": expert_followup_context,
                })

                add_llm_trace(
                    st.session_state,
                    "expert_mode_followup_chat",
                    input_summary={
                        "question": expert_followup_question,
                        "query_plan": expert_query_plan,
                        "retrieved_count": len(expert_followup_context),
                    },
                    output={"answer": expert_followup_answer},
                    decision="expert_followup_answered",
                )
                log_conversation_turn(
                    st.session_state["session_id"], "expert_followup", "expert_followup",
                    expert_followup_question, expert_followup_answer,
                    retrieved_chunks=expert_followup_context,
                    extra={
                        "model_name": DEFAULT_MODEL,
                        "user_profile": None,
                        "location_context": expert_last_run.get("location_context"),
                        "rag_enabled": True,
                        "rag_source": "both",
                        "retrieval_query": expert_query_plan["retrieval_query"],
                        "retrieval_query_mode": expert_query_plan["query_mode"],
                        "response_time_ms": round(
                            (time.perf_counter() - expert_turn_started_at) * 1000
                        ),
                        "error": expert_retrieval_error,
                    },
                )
                expert_followup_status.update(
                    label=PROCESSING_STATUS_TEXT["complete"],
                    state="complete",
                )
            st.rerun()

    st.stop()


if SESSION_KEY_USER_PROFILE not in st.session_state:
    _, profile_column, _ = st.columns([1, 3, 1])
    with profile_column:
        if st.button("Back to modes"):
            st.session_state[SESSION_KEY_APP_MODE] = None
            st.rerun()
        st.title(APP_TITLE)
        st.subheader(USER_PROFILE_TEXT["header"])
        st.caption("Your answers help tailor explanations and PV recommendations.")
        with st.form("user_profile_form", border=True):
            st.markdown("**Project site**")
            site_location = st.text_input(
                USER_PROFILE_TEXT["site_location_label"],
                value=USER_PROFILE_TEXT["site_location_placeholder"],
                help="Use the suggested site, replace it with yours, or clear it to ask general questions first.",
            )
            st.markdown("**About you**")
            role_column, experience_column = st.columns(2)
            with role_column:
                user_type = st.selectbox(USER_PROFILE_TEXT["user_type_label"], options=USER_TYPE_OPTIONS)
            with experience_column:
                solar_experience = st.selectbox(USER_PROFILE_TEXT["solar_experience_label"], options=SOLAR_EXPERIENCE_OPTIONS)
            project_goal = st.selectbox(USER_PROFILE_TEXT["project_goal_label"], options=PROJECT_GOAL_OPTIONS)
            with st.expander("Add more context (optional)"):
                user_role_details = st.text_input(USER_PROFILE_TEXT["user_role_label"])
                goal_details = st.text_area(USER_PROFILE_TEXT["goal_details_label"])
                datasheet = st.file_uploader(DATASHEET_UPLOAD_TEXT["label"], type=["pdf"], help=DATASHEET_UPLOAD_TEXT["help"])
            submit_button = st.form_submit_button(USER_PROFILE_TEXT["submit_button"], type="primary")

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
render_workspace_header(APP_MODE_NON_EXPERT, location_context)

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
            render_simulation_result(run, show_crop=True)
        continue

    with st.chat_message(message["role"]):
        st.write(message["content"])
        render_retrieved_sources(message.get("retrieved_sources"))

render_simulation_comparison(distinct_solar_runs(
    st.session_state.get(SESSION_KEY_PVMAPS_RUNS, [])
))
render_crop_comparison(st.session_state.get(SESSION_KEY_PVMAPS_RUNS, []), "guided")
if len(st.session_state[SESSION_KEY_CHAT_MESSAGES]) > 1 or st.session_state.get(SESSION_KEY_PVMAPS_RUNS):
    with st.expander("Downloads", expanded=False):
        render_simulation_exports(st.session_state.get(SESSION_KEY_PVMAPS_RUNS, []), "guided")
        render_conversation_export(
            st.session_state[SESSION_KEY_CHAT_MESSAGES],
            st.session_state.get(SESSION_KEY_PVMAPS_RUNS, []),
            "guided",
        )

submitted_question = st.chat_input(CHAT_UI_TEXT["answer_label"], key="chat_input")
if submitted_question:
    st.session_state[SESSION_KEY_CHAT_MESSAGES].append({
        "role": MESSAGE_ROLE_USER,
        "content": submitted_question,
    })
    st.session_state[PENDING_CHAT_QUESTION_KEY] = submitted_question
    st.rerun()

question = st.session_state.get(PENDING_CHAT_QUESTION_KEY)
if question:
    turn_started_at = time.perf_counter()

    with st.status(
        PROCESSING_STATUS_TEXT["routing"],
        expanded=False,
    ) as processing_status:
        processing_failed = False

        def update_processing_status(message):
            processing_status.update(label=message)

        try:
            plan = route_conversation_turn(
                api_key,
                latest_user_message=question,
                user_profile=st.session_state.get(SESSION_KEY_USER_PROFILE),
                location_context=location_context,
                conversation_history=st.session_state[SESSION_KEY_CHAT_MESSAGES],
                pvmaps_runs=st.session_state.get(SESSION_KEY_PVMAPS_RUNS, []),
                pending_crop_request=st.session_state.get(PENDING_CROP_REQUEST_KEY),
            )
        except Exception as error:
            processing_status.update(
                label=PROCESSING_STATUS_TEXT["failed"],
                state="error",
            )
            error_message = _chat_api_error_message(error)
            st.session_state[SESSION_KEY_CHAT_MESSAGES].append({
                "role": MESSAGE_ROLE_ASSISTANT,
                "content": error_message,
            })
            add_llm_trace(
                st.session_state,
                "turn_router",
                input_summary={"question": question},
                output={"error": str(error)},
                decision="router_request_failed",
            )
            st.session_state.pop(PENDING_CHAT_QUESTION_KEY, None)
            st.rerun()
        add_llm_trace(
            st.session_state,
            "turn_router",
            input_summary={
                SESSION_KEY_USER_PROFILE: st.session_state.get(SESSION_KEY_USER_PROFILE),
                SESSION_KEY_LOCATION_CONTEXT: location_context,
                "conversation_history": st.session_state[SESSION_KEY_CHAT_MESSAGES],
                SESSION_KEY_PVMAPS_RUNS: [compact_run(run) for run in st.session_state.get(SESSION_KEY_PVMAPS_RUNS, [])],
            },
            output=plan,
            decision=plan["turn_type"],
        )

        if plan.get("mentioned_location"):
            update_processing_status(PROCESSING_STATUS_TEXT["location"])
            try:
                coordinates = geocode_location(plan["mentioned_location"])
                location_context = {
                    "site_location": plan["mentioned_location"],
                    "confirmed_address": coordinates["address"],
                    "latitude": coordinates["latitude"],
                    "longitude": coordinates["longitude"],
                }
                st.session_state[SESSION_KEY_LOCATION_CONTEXT] = location_context
                st.session_state.pop(SESSION_KEY_QUESTIONNAIRE_STATE, None)
                add_llm_trace(
                    st.session_state,
                    "location_geocoder",
                    input_summary={"mentioned_location": plan["mentioned_location"]},
                    output=location_context,
                    decision="location_updated",
                )
            except Exception as error:
                processing_status.update(
                    label=PROCESSING_STATUS_TEXT["failed"],
                    state="error",
                )
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
                st.session_state.pop(PENDING_CHAT_QUESTION_KEY, None)
                st.rerun()

        if (plan["turn_type"] == TURN_TYPE_GATHER_INFO and plan.get("question")
                and not st.session_state.get(PENDING_CROP_REQUEST_KEY)
                and not _requests_crop_estimate(question)):
            update_processing_status(PROCESSING_STATUS_TEXT["answer"])
            st.session_state[SESSION_KEY_CHAT_MESSAGES].append({
                "role": MESSAGE_ROLE_ASSISTANT,
                "content": plan["question"],
            })
            log_conversation_turn(
                st.session_state["session_id"], "guided", TURN_TYPE_GATHER_INFO,
                question, plan["question"],
                extra={
                    "model_name": DEFAULT_MODEL,
                    "user_profile": st.session_state.get(SESSION_KEY_USER_PROFILE),
                    "location_context": location_context,
                    "response_time_ms": round(
                        (time.perf_counter() - turn_started_at) * 1000
                    ),
                },
            )

        elif (
            (plan["turn_type"] == TURN_TYPE_RUN_PVMAPS and
             plan.get("analysis") in ("solar_and_crop", "crop_open_sky", "crop_unspecified"))
            or _requests_crop_estimate(question)
            or (st.session_state.get(PENDING_CROP_REQUEST_KEY) and
                "solar only" not in question.casefold() and
                "just solar" not in question.casefold() and
                ((plan["turn_type"] == TURN_TYPE_RUN_PVMAPS and
                  plan.get("analysis") in ("solar_and_crop", "crop_open_sky", "crop_unspecified")) or
                 plan.get("mentioned_location") or
                 resolve_crop_analysis(question, {}, {}) != "crop_unspecified" or
                 resolve_crop_inputs(question, {}).get("crop") or
                 resolve_crop_inputs(question, {}).get("sowing_date")))
        ):
            pending_crop = st.session_state.get(PENDING_CROP_REQUEST_KEY) or {}
            crop_inputs = resolve_crop_inputs(question, plan, pending_crop)
            crop_inputs["analysis"] = resolve_crop_analysis(question, plan, pending_crop)
            crop_request = pending_crop.get("user_request") or question
            crop_inputs["user_request"] = crop_request
            st.session_state[PENDING_CROP_REQUEST_KEY] = crop_inputs
            if location_context.get("latitude") is None or location_context.get("longitude") is None:
                response = "What is the site location (city and state or country) for this estimate?"
            elif crop_inputs["analysis"] == "crop_unspecified":
                response = "Should I estimate crop yield under a PV layout or without panels?"
            elif not crop_inputs["crop"]:
                response = "Which crop should I estimate: maize, rice, sorghum, or soybean?"
            elif not crop_inputs["sowing_date"]:
                response = "What is the sowing date? Please include the year, for example May 15, 2024."
            elif date.fromisoformat(crop_inputs["sowing_date"]).year >= date.today().year:
                crop_inputs["sowing_date"] = None
                response = "I need a sowing date from a completed weather year. What date and year should I use?"
            else:
                response = None

            if response:
                update_processing_status(PROCESSING_STATUS_TEXT["answer"])
                st.session_state[SESSION_KEY_CHAT_MESSAGES].append({
                    "role": MESSAGE_ROLE_ASSISTANT, "content": response,
                })
                log_conversation_turn(
                    st.session_state["session_id"], "guided", TURN_TYPE_GATHER_INFO,
                    question, response,
                )
            else:
                try:
                    if crop_inputs["analysis"] == "crop_open_sky":
                        update_processing_status("Running SIMPLE with site weather...")
                        completed = run_guided_open_sky_estimate(
                            st.session_state, location_context,
                            crop_inputs["crop"], crop_inputs["sowing_date"],
                        )
                    else:
                        completed = run_recommended_pvmaps_estimate(
                            st.session_state, api_key, location_context,
                            latest_user_message=f"{crop_request} {question}" if crop_request != question else question,
                            status_callback=update_processing_status,
                            crop=crop_inputs["crop"], sowing_date=crop_inputs["sowing_date"],
                        )
                    processing_failed = not completed
                    if completed:
                        st.session_state.pop(PENDING_CROP_REQUEST_KEY, None)
                    completed_run = (st.session_state[SESSION_KEY_PVMAPS_RUNS][-1]
                                     if completed else {})
                    completed_crop = completed_run.get("crop_result") or {}
                    completed_pv = completed_run.get("output") or {}
                    log_conversation_turn(
                        st.session_state["session_id"], "guided", TURN_TYPE_RUN_PVMAPS,
                        question, completed_run.get("explanation") if completed else "Crop estimate not generated",
                        extra={"analysis": crop_inputs["analysis"], "crop": crop_inputs["crop"],
                               "sowing_date": crop_inputs["sowing_date"],
                               "solar_yield": completed_pv.get("yearly_yield"),
                               "solar_yield_unit": completed_pv.get("yield_unit"),
                               "mean_grain_yield_t_ha": completed_crop.get("mean_grain_yield_t_ha")},
                    )
                except Exception as error:
                    processing_failed = True
                    st.session_state[SESSION_KEY_CHAT_MESSAGES].append({
                        "role": MESSAGE_ROLE_ASSISTANT,
                        "content": "I tried to run the crop estimate, but the simulation could not complete. The inputs are saved so we can retry.",
                    })
                    add_llm_trace(
                        st.session_state,
                        "guided_simple_run" if crop_inputs["analysis"] == "crop_open_sky"
                        else "combined_simulation",
                        input_summary={"crop": crop_inputs["crop"], "sowing_date": crop_inputs["sowing_date"]},
                        output={"error": str(error)}, decision="estimate_failed",
                    )
                    log_conversation_turn(
                        st.session_state["session_id"], "guided", TURN_TYPE_RUN_PVMAPS,
                        question, "Crop simulation failed",
                        extra={"analysis": crop_inputs["analysis"], "crop": crop_inputs["crop"],
                               "sowing_date": crop_inputs["sowing_date"], "error": str(error)},
                    )

        elif plan["turn_type"] == TURN_TYPE_RUN_PVMAPS:
            try:
                st.session_state.pop(PENDING_CROP_REQUEST_KEY, None)
                estimate_completed = run_recommended_pvmaps_estimate(
                    st.session_state,
                    api_key,
                    location_context,
                    latest_user_message=question,
                    status_callback=update_processing_status,
                )
                processing_failed = not estimate_completed
                log_conversation_turn(
                    st.session_state["session_id"], "guided", TURN_TYPE_RUN_PVMAPS,
                    question, "PV-MAPS solar estimate generated",
                    extra={
                        "model_name": DEFAULT_MODEL,
                        "user_profile": st.session_state.get(SESSION_KEY_USER_PROFILE),
                        "location_context": location_context,
                        "response_time_ms": round(
                            (time.perf_counter() - turn_started_at) * 1000
                        ),
                    },
                )
            except Exception as error:
                processing_failed = True
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
                log_conversation_turn(
                    st.session_state["session_id"], "guided", TURN_TYPE_RUN_PVMAPS,
                    question, "PV-MAPS solar simulation failed",
                    extra={
                        "model_name": DEFAULT_MODEL,
                        "user_profile": st.session_state.get(SESSION_KEY_USER_PROFILE),
                        "location_context": location_context,
                        "response_time_ms": round(
                            (time.perf_counter() - turn_started_at) * 1000
                        ),
                        "error": str(error),
                    },
                )

        else:
            pvmaps_runs = st.session_state.get(SESSION_KEY_PVMAPS_RUNS, [])
            latest_pvmaps_output = pvmaps_runs[-1]["output"] if pvmaps_runs else None

            retrieved_context = []
            rag_plan = {"source": "none", "reason": None}
            retrieval_error = None
            try:
                update_processing_status(PROCESSING_STATUS_TEXT["rag_routing"])
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
                if rag_plan["source"] != "none":
                    update_processing_status(PROCESSING_STATUS_TEXT["retrieval"])
                retrieved_context = retrieve_for_source(
                    rag_plan["source"], rag_plan.get("retrieval_query", question)
                )
                add_llm_trace(
                    st.session_state,
                    "rag_retrieval",
                    input_summary={
                        "question": question, "source": rag_plan["source"],
                        "retrieval_query": rag_plan.get("retrieval_query", question),
                        "query_mode": rag_plan.get("query_mode"),
                    },
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
                retrieval_error = str(error)

            retrieved_context = (
                retrieve_personal_context(rag_plan.get("retrieval_query", question))
                + retrieved_context
            )

            answer_error = None
            try:
                update_processing_status(PROCESSING_STATUS_TEXT["answer"])
                answer = answer_general_agpv_question(
                    question,
                    api_key,
                    user_profile=st.session_state.get(SESSION_KEY_USER_PROFILE),
                    location_context=location_context,
                    pvmaps_state=st.session_state.get(SESSION_KEY_QUESTIONNAIRE_STATE),
                    latest_pvmaps_output=latest_pvmaps_output,
                    latest_pvmaps_run=pvmaps_runs[-1] if pvmaps_runs else None,
                    conversation_history=st.session_state[SESSION_KEY_CHAT_MESSAGES],
                    retrieved_context=retrieved_context,
                )
            except Exception as error:
                processing_failed = True
                answer = _chat_api_error_message(error)
                add_llm_trace(
                    st.session_state,
                    "general_agpv_answerer",
                    input_summary={"question": question},
                    output={"error": str(error)},
                    decision="answer_request_failed",
                )
                answer_error = str(error)
            add_llm_trace(
                st.session_state,
                "general_agpv_answerer",
                input_summary={
                    "question": question,
                    SESSION_KEY_USER_PROFILE: st.session_state.get(SESSION_KEY_USER_PROFILE),
                    SESSION_KEY_LOCATION_CONTEXT: location_context,
                    "conversation_history": st.session_state[SESSION_KEY_CHAT_MESSAGES],
                    "retrieved_context_count": len(retrieved_context),
                    "latest_pvmaps_run": compact_run(pvmaps_runs[-1]) if pvmaps_runs else None,
                },
                output={"answer": answer},
                decision="answered_general_question",
            )
            st.session_state[SESSION_KEY_CHAT_MESSAGES].append({
                "role": MESSAGE_ROLE_ASSISTANT,
                "content": answer,
                "retrieved_sources": retrieved_context,
            })
            log_conversation_turn(
                st.session_state["session_id"], "guided", "general_question",
                question, answer, retrieved_chunks=retrieved_context,
                extra={
                    "model_name": DEFAULT_MODEL,
                    "user_profile": st.session_state.get(SESSION_KEY_USER_PROFILE),
                    "location_context": location_context,
                    "rag_enabled": bool(retrieved_context),
                    "rag_source": (
                        ("personal" if rag_plan.get("source", "none") == "none"
                         else f"{rag_plan['source']}+personal")
                        if any((chunk.get("metadata") or {}).get("library") == "My library"
                               for chunk in retrieved_context)
                        else rag_plan.get("source", "none")
                    ),
                    "rag_router_reason": rag_plan.get("reason"),
                    "retrieval_query": (
                        rag_plan.get("retrieval_query", question)
                        if rag_plan.get("source", "none") != "none" else None
                    ),
                    "retrieval_query_mode": rag_plan.get("query_mode"),
                    "response_time_ms": round(
                        (time.perf_counter() - turn_started_at) * 1000
                    ),
                    "error": answer_error or retrieval_error,
                },
            )

        processing_status.update(
            label=(
                PROCESSING_STATUS_TEXT["failed"]
                if processing_failed
                else PROCESSING_STATUS_TEXT["complete"]
            ),
            state="error" if processing_failed else "complete",
        )

    st.session_state.pop(PENDING_CHAT_QUESTION_KEY, None)
    st.rerun()
