from services.panel_specs import get_panel_specs
from models.pvmaps.input_builder import create_default_pvmaps_input


def build_pvmaps_input_from_questionnaire(state, lat, lon):
    panel_model = state["panel_model"]
    panel_specs = get_panel_specs(panel_model)

    return create_default_pvmaps_input(
        lat=lat,
        lon=lon,
        cell_tech=panel_specs["cell_tech"],
        module_height=panel_specs["module_height"],
        stc_eff_direct=panel_specs["stc_eff_direct"],
        stc_eff_diffuse=panel_specs["stc_eff_diffuse"],
        tcoeff=panel_specs["tcoeff"],
        array_config=state["array_config"],
        tilt=state["tilt"],
        azimuth=state["azimuth"],
        albedo=state["albedo"],
        pitch=state["pitch"],
        gs_height=state["gs_height"],
        array_elevation=state["array_elevation"],
    )
