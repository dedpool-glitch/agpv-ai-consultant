import streamlit as st
import matplotlib.pyplot as plt

from constants import NUMERIC_QUESTIONNAIRE_FIELDS
from pvmaps_input_builder import create_default_pvmaps_input
from pvmaps_input_validator import validate_pvmaps_input
from pvmaps_matlab_runner import run_pvmaps
from pvmaps_result_explainer import explain_pvmaps_result
from location_geocoder import geocode_location
from panel_specs import get_panel_models, get_panel_specs
from questionnaire_state import apply_questionnaire_defaults, get_next_question, initialize_questionnaire_state, update_questionnaire_state
from questionnaire_to_pvmaps import build_pvmaps_input_from_questionnaire

st.title("PVMAPS Solar Yield Demo")

location_text = st.text_input("Farm Location (City, State)", value="Lafayette, Indiana, USA")

if st.button("Retrieve coordinates"):
    try:
        st.session_state["coordinates"] = geocode_location(location_text)
    except Exception as error:
        st.error("Could not retrieve coordinates.")
        st.code(str(error))

if "coordinates" in st.session_state:
    coordinates = st.session_state["coordinates"]

    lat=coordinates["latitude"]
    lon=coordinates["longitude"]
    address=coordinates["address"]

    st.subheader("Matched Location")
    st.write(f"Latitude: {lat}, Longitude: {lon}")

    mode=st.radio("Choose input method", options=["Questionnaire", "Manual Input"], index=None)

    if mode=="Manual Input":
        st.write("Fill in the parameters below to run the PVMAPS simulation. Default values are provided for convenience, but you can adjust them as needed.")

        #define input fields for solar panel parameters
        panel_model_options = ["default values"] + get_panel_models()
        panel_model = st.selectbox("Panel model from datasheet", options=panel_model_options)

        if panel_model == "default values":
            panel_specs = {
                "cell_type_raw": "not specified",
                "cell_tech": "AL_BSF",
                "module_height": 4.8,
                "stc_eff_direct": 21.8,
                "stc_eff_diffuse": 21.8,
                "tcoeff": 0.0041,
                "source": "default PVMAPS example",
            }
        else:
            panel_specs = get_panel_specs(panel_model)
            st.write(f"Datasheet cell type: {panel_specs['cell_type_raw']}")
            st.write(f"Source: {panel_specs['source']}")
            st.write(f"PVMAPS cell technology: {panel_specs['cell_tech']}")

        cell_tech = panel_specs["cell_tech"]
        height=st.number_input("Panel Height(metres)", value=float(panel_specs["module_height"]), format="%.3f")
        direct_eff=st.number_input("Direct Efficiency", value=float(panel_specs["stc_eff_direct"]), format="%.2f")
        diffuse_eff=st.number_input("Diffuse Efficiency", value=float(panel_specs["stc_eff_diffuse"]), format="%.2f")
        tcoeff=st.number_input("Temperature Coefficient", value=float(panel_specs["tcoeff"]), format="%.4f")

        #define input fields for array parameters
        config=st.selectbox("Array Configuration",options=["fixed","tracking","GSVBF"],index=1)
        tilt=st.number_input("Tilt angle(degrees)", value=25.0) #have set default values for now incase users don't know something. this is something we can change.
        azimuth=st.number_input("Azimuth angle(degrees)", value=90.0)
        albedo=st.number_input("Albedo", value=0.3)
        pitch=st.number_input("Row Spacing(metres)", value=11.0)
        gsHeight=st.number_input("Ground Sculpting Height(metres)", value=0.5)
        elevation=st.number_input("Elevation(metres)", value=3.0)

    elif mode=="Questionnaire":
        if "questionnaire_started" not in st.session_state:
            st.session_state["questionnaire_started"] = False

        if not st.session_state["questionnaire_started"]:
            st.write("Start the guided questionnaire when you are ready to provide the remaining PVMAPS inputs.")

            if st.button("Start questionnaire"):
                st.session_state["questionnaire_state"] = initialize_questionnaire_state()
                st.session_state["questionnaire_started"] = True
                st.session_state["questionnaire_ready_to_run"] = False
                st.rerun()
        else:
            state=st.session_state["questionnaire_state"]
            next_question = get_next_question(state)

            if next_question:
                field=next_question["field"]
                question=next_question["question"]

                st.write(question)
                answer=st.text_input("Your answer", key=f"answer_{field}")

                if st.button("Submit answer", key=f"submit_{field}"):
                  try:
                    if field in NUMERIC_QUESTIONNAIRE_FIELDS:
                        answer=float(answer)
                    update_questionnaire_state(state, field, answer)
                    st.session_state["questionnaire_state"]=state
                    st.rerun()
                  except ValueError:
                    st.error(f"Invalid input for {field}. Please enter a valid number.")
                if st.button("Use defaults for remaining answers"):
                    apply_questionnaire_defaults(state)
                    st.session_state["questionnaire_state"] = state
                    st.session_state["questionnaire_ready_to_run"] = True
                    st.rerun()
            else:
                st.write("Questionnaire complete!")
                st.session_state["questionnaire_ready_to_run"] = True

    can_run_pvmaps = (
        mode == "Manual Input"
        or (
            mode == "Questionnaire"
            and st.session_state.get("questionnaire_ready_to_run", False)
        )
    )

    if mode == "Questionnaire" and not st.session_state.get("questionnaire_ready_to_run", False):
        st.write("Complete the questionnaire or use defaults before running PVMAPS.")

    if can_run_pvmaps and st.button("Run PVMAPS"):
        if mode=="Manual Input":
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
                st.error("Please start the questionnaire before running PVMAPS.")
                st.stop()

            state=st.session_state["questionnaire_state"]
            pvmaps_input=build_pvmaps_input_from_questionnaire(state, lat, lon)

        errors = validate_pvmaps_input(pvmaps_input)
        if errors:
            st.error("Input validation failed:")
            for error in errors:
                st.write("-", error)
        else:
            try:
                with st.spinner("Running MATLAB PVMAPS..."):
                    output = run_pvmaps(
                        pvmaps_input,
                        r"D:/agpv-ai-consultant/PV-MAPS-main"
                    )
            except Exception as error:
                st.error("PVMAPS simulation failed.")
                st.write(
                    "The selected configuration may not be supported by the current PVMAPS setup, "
                    "or MATLAB could not complete the simulation."
                )
                st.code(str(error))
                st.stop()

            st.subheader("Location")
            st.write(address)

            st.subheader("Result")
            st.write(explain_pvmaps_result(output))

            st.subheader("Monthly Yield")
            months = ["January", "February", "March", "April","May", "June", "July", "August","September", "October", "November", "December"]

            fig, ax = plt.subplots(figsize=(10, 5))
            ax.bar(months, output["monthly_yield"])
            ax.set_xlabel("Month")
            ax.set_ylabel(f"Yield ({output['yield_unit']})")
            ax.set_title("Monthly PVMAPS Yield")
            ax.tick_params(axis="x", labelrotation=45)
            st.pyplot(fig)
