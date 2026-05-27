import streamlit as st

from pvmaps_input_builder import create_default_pvmaps_input
from pvmaps_input_validator import validate_pvmaps_input
from pvmaps_matlab_runner import run_pvmaps
from pvmaps_result_explainer import explain_pvmaps_result

st.title("PVMAPS Solar Yield Demo")
#take coordinates as inputs
lat=st.number_input("Latitude", value=32.692, format="%.6f")
lon=st.number_input("Longitude", value=-114.627, format="%.6f")

#define input fields for solar panel parameters
cell_tech=st.selectbox("Cell Technology", options=["AL_BSF", "BI_PERC","SHJ","PVK_SI_2T","PVK_SI_4T","SHJ_NN"])
height=st.number_input("Panel Height(metres)", value=4.8, format="%.2f")
direct_eff=st.number_input("Direct Efficiency", value=21.8, format="%.2f")
diffuse_eff=st.number_input("Diffuse Efficiency", value=21.8, format="%.2f")
tcoeff=st.number_input("Temperature Coefficient", value=0.0041, format="%.4f")

#define input fields for array parameters
config=st.selectbox("Array Configuration",options=["fixed","tracking","GSVBF"],index=1)
tilt=st.number_input("Tilt angle(degrees)", value=25.0) #have set default values for now incase users don't know something. this is something we can change.
azimuth=st.number_input("Azimuth angle(degrees)", value=90.0)
albedo=st.number_input("Albedo", value=0.3)
pitch=st.number_input("Row Spacing(metres)", value=11.0)
gsHeight=st.number_input("Ground Sculpting Height(metres)", value=0.5)
elevation=st.number_input("Elevation(metres)", value=3.0)

if st.button("Run PVMAPS"):
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

        """st.subheader("PVMAPS Input")
        st.json(pvmaps_input)"""

        st.subheader("Result")
        st.write(explain_pvmaps_result(output))

        st.subheader("Monthly Yield")
        st.bar_chart(output["monthly_yield"])
