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
    RESULT_TEXT,
    USER_PROFILE_TEXT,
    USER_TYPE_OPTIONS,
    SOLAR_EXPERIENCE_OPTIONS,
    DATASHEET_UPLOAD_TEXT,
    PROJECT_GOAL_OPTIONS
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
from llm.output_generator import explain_output

load_dotenv()
api_key = os.getenv("PURDUE_GENAI_KEY")

st.title(APP_TITLE)

location_text = st.text_input(LOCATION_TEXT["input_label"])

if st.button(LOCATION_TEXT["geocode_button"]):
    try:
        st.session_state["coordinates"] = geocode_location(location_text)
    except Exception as error:
        st.error(LOCATION_TEXT["geocode_error"])
        st.code(str(error))

if "coordinates" in st.session_state:
    coordinates = st.session_state["coordinates"]

    lat=coordinates["latitude"]
    lon=coordinates["longitude"]
    address=coordinates["address"]

    if "user_profile" not in st.session_state:
        st.subheader(USER_PROFILE_TEXT["header"])
        with st.form("user_profile_form"):
            user_type = st.selectbox(USER_PROFILE_TEXT["user_type_label"], options=USER_TYPE_OPTIONS)
            user_role_details=st.text_input(USER_PROFILE_TEXT["user_role_label"])
            solar_experience = st.selectbox(USER_PROFILE_TEXT["solar_experience_label"], options=SOLAR_EXPERIENCE_OPTIONS)
            project_goal=st.selectbox(USER_PROFILE_TEXT["project_goal_label"],options=PROJECT_GOAL_OPTIONS)
            goal_details=st.text_area(USER_PROFILE_TEXT["goal_details_label"])
            submit_button=st.form_submit_button(USER_PROFILE_TEXT["submit_button"])
            datasheet=st.file_uploader(DATASHEET_UPLOAD_TEXT["label"], type=["pdf"], help=DATASHEET_UPLOAD_TEXT["help"])


            if submit_button:
                if datasheet:
                    st.session_state["datasheet"]={
                        "name": datasheet.name,
                        "type": datasheet.type,
                        "bytes": datasheet.getvalue(),
                    }
                st.session_state["user_profile"] = {
                    "user_type": user_type,
                    "user_role_details":user_role_details,
                    "solar_experience": solar_experience,
                    "project_goal":project_goal,
                    "goal_details":goal_details
                }
                st.rerun()
        st.stop()

    st.subheader(LOCATION_TEXT["matched_location_header"])
    st.write(f"Latitude: {lat}, Longitude: {lon}")

    if "datasheet" in st.session_state:
        st.success(DATASHEET_UPLOAD_TEXT["success"])
        st.write(f"{DATASHEET_UPLOAD_TEXT['uploaded_file_label']}: {st.session_state['datasheet']['name']}")

    mode=st.radio(INPUT_MODE["label"], options=[INPUT_MODE["questionnaire"], INPUT_MODE["manual"]], index=None)

    if mode==INPUT_MODE["manual"]:
        st.write(MANUAL_INPUT_TEXT["description"])

        #define input fields for solar panel parameters
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
        height=st.number_input(MANUAL_INPUT_TEXT["panel_height_label"], value=float(panel_specs["module_height"]), format="%.3f")
        direct_eff=st.number_input(MANUAL_INPUT_TEXT["direct_efficiency_label"], value=float(panel_specs["stc_eff_direct"]), format="%.2f")
        diffuse_eff=st.number_input(MANUAL_INPUT_TEXT["diffuse_efficiency_label"], value=float(panel_specs["stc_eff_diffuse"]), format="%.2f")
        tcoeff=st.number_input(MANUAL_INPUT_TEXT["temperature_coefficient_label"], value=float(panel_specs["tcoeff"]), format="%.4f")

        #define input fields for array parameters
        config=st.selectbox(MANUAL_INPUT_TEXT["array_config_label"],options=ARRAY_CONFIG_OPTIONS)
        tilt=st.number_input(MANUAL_INPUT_TEXT["tilt_label"], value=25.0) #have set default values for now incase users don't know something. this is something we can change.
        azimuth=st.number_input(MANUAL_INPUT_TEXT["azimuth_label"], value=90.0)
        albedo=st.number_input(MANUAL_INPUT_TEXT["albedo_label"], value=0.3)
        pitch=st.number_input(MANUAL_INPUT_TEXT["pitch_label"], value=11.0)
        gsHeight=st.number_input(MANUAL_INPUT_TEXT["ground_sculpting_height_label"], value=0.5)
        elevation=st.number_input(MANUAL_INPUT_TEXT["elevation_label"], value=3.0)

    elif mode==INPUT_MODE["questionnaire"]:
        if "questionnaire_started" not in st.session_state:
            st.session_state["questionnaire_started"] = False

        if not st.session_state["questionnaire_started"]:
            st.write(QUESTIONNAIRE_UI_TEXT["start_description"])

            if st.button(QUESTIONNAIRE_UI_TEXT["start_button"]):
                state=initialize_questionnaire_state()
                first_question = get_next_question(state)
                field=first_question["field"]
                first_generated_question=generate_question(field, state, api_key, st.session_state.get("user_profile"))
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
            state=st.session_state["questionnaire_state"]
            next_question = get_next_question(state)
            for message in st.session_state.get("chat_messages", []):
                with st.chat_message(message["role"]):
                    st.write(message["content"])
            if next_question:
                field=st.session_state["active_field"]
                question=st.session_state["active_question"]
                answer=st.chat_input(QUESTIONNAIRE_UI_TEXT["answer_label"],key="questionnaire_input")
                if answer:
                  try:
                    raw_answer = answer
                    extracted_answer=extract_questionnaire_parameter(field, question, raw_answer, api_key)
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
                    value=extracted_answer["value"]
                    st.write(value)
                    parsed_answer = parse_questionnaire_answer(field,value)
                    update_questionnaire_state(state, field, parsed_answer)
                    st.session_state["questionnaire_state"]=state
                    st.session_state["chat_messages"].append({
                        "role": "user",
                        "content": raw_answer,
                    })

                    next_question = get_next_question(state)
                    if next_question:
                        field=next_question["field"]
                        generated_question=generate_question(field, state, api_key, st.session_state.get("user_profile"))
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
                    apply_questionnaire_defaults(state)
                    st.session_state["questionnaire_state"] = state
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

    can_run_pvmaps = (
        mode == INPUT_MODE["manual"]
        or (
            mode == INPUT_MODE["questionnaire"]
            and st.session_state.get("questionnaire_ready_to_run", False)
        )
    )

    if mode == INPUT_MODE["questionnaire"] and not st.session_state.get("questionnaire_ready_to_run", False):
        st.write(QUESTIONNAIRE_UI_TEXT["not_ready_message"])

    if can_run_pvmaps and st.button(PVMAPS_RUN_TEXT["run_button"]):
        if mode==INPUT_MODE["manual"]:
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

            state=st.session_state["questionnaire_state"]
            pvmaps_input=build_pvmaps_input_from_questionnaire(state, lat, lon)

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
            except Exception as error:
                st.error(PVMAPS_RUN_TEXT["simulation_error"])
                st.write(PVMAPS_RUN_TEXT["simulation_error_detail"])
                st.code(str(error))
                st.stop()

            st.subheader(LOCATION_TEXT["result_location_header"])
            st.write(address)

            st.subheader(RESULT_TEXT["result_header"])
            st.write(explain_output(output, api_key, st.session_state.get("user_profile")))

            st.subheader(RESULT_TEXT["monthly_yield_header"])

            fig, ax = plt.subplots(figsize=(10, 5))
            ax.bar(MONTH_LABELS, output["monthly_yield"])
            ax.set_xlabel(RESULT_TEXT["chart_x_label"])
            ax.set_ylabel(f"Yield ({output['yield_unit']})")
            ax.set_title(RESULT_TEXT["chart_title"])
            ax.tick_params(axis="x", labelrotation=45)
            st.pyplot(fig)
