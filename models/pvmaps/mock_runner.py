def run_mock_pvmaps(pvmaps_input):
    return {
        "yearly_yield": 1918.7,
        "monthly_yield": [
            102.1223, 115.7989, 171.0809, 199.4501,
            227.1593, 222.8955, 204.0386, 177.6009,
            157.3944, 136.3557, 109.8208, 95.0015
        ],
        "daily_yield": [
            3.2943, 4.1357, 5.5187, 6.6483,
            7.3277, 7.4299, 6.5819, 5.7291,
            5.2465, 4.3986, 3.6607, 3.0646
        ],
        "yield_unit": "kWh/m",
        "warnings": [],
        "assumptions": {
            "model": "mock_pvmaps",
            "lat": pvmaps_input["lat"],
            "lon": pvmaps_input["lon"],
            "panel_type": pvmaps_input["module"]["cell_tech"],
            "tracking": pvmaps_input["array"]["config"],
            "tilt": pvmaps_input["array"]["tilt"],
            "pitch": pvmaps_input["array"]["pitch"],
        },
    }