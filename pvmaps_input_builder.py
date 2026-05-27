def create_default_pvmaps_input(
    lat,
    lon,
    cell_tech="AL_BSF",
    module_height=4.8,
    stc_eff_direct=21.8,
    stc_eff_diffuse=21.8,
    tcoeff=0.0041,
    array_config="tracking",
    tilt=25,
    azimuth=90,
    albedo=0.3,
    pitch=11.0,
    gs_height=0.5,
    array_elevation=3.0,
):
    return {
        "lat": lat,
        "lon": lon,
        "module": {
            "cell_tech": cell_tech,
            "height": module_height,
            "stc_eff": {
                "direct": stc_eff_direct,
                "diffuse": stc_eff_diffuse,
            },
            "tcoeff": tcoeff,
        },
        "array": {
            "config": array_config,
            "tilt": tilt,
            "azimuth": azimuth,
            "albedo": albedo,
            "pitch": pitch,
            "gsHeight": gs_height,
            "elevation": array_elevation,
        },
    }