def create_default_pvmaps_input(lat, lon):
    return {
        "lat": lat,
        "lon": lon,
        "module": {
            "cell_tech": "AL_BSF",
            "height": 4.8,
            "stc_eff": {
                "direct": 21.8,
                "diffuse": 21.8,
            },
            "tcoeff": 0.0041,
        },
        "array": {
            "config": "tracking",
            "tilt": 25,
            "azimuth": 90,
            "albedo": 0.3,
            "pitch": 11.0,
            "gsHeight": 0.5,
            "elevation": 3.0,
        },
    }
