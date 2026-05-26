def create_default_pvmaps_input(lat,lon):
    return {
        "lat": lat,
        "lon": lon,
        "module": {
            "cell_tech": "bifacial",
            "height": 2.0,  #replace with any default value that is acceptable
            "stc_eff": {
                "direct": 0.20,
                "diffuse": 0.18, #change this
            },
            "tcoeff": -0.004,
        },
        "array": {
            "config": "single_axis",
            "tilt": 25,
            "azimuth": 180,
            "albedo": 0.25,
            "pitch": 8.0,
            "gsHeight": 0.0,
            "elevation": 3.0,
        },
    }