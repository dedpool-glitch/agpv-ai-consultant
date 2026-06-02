PANEL_SPECS = {
    "CST100P6-24": {
        "cell_type_raw": "polycrystalline",
        "module_height": 0.665,
        "stc_eff_direct": 15.04,
        "stc_eff_diffuse": 15.04,
        "tcoeff": 0.0040,
        "source": "Solar-Panel-Datasheets-COLLECTION.pdf",
    },
    "CST200P6-24": {
        "cell_type_raw": "polycrystalline",
        "module_height": 0.992,
        "stc_eff_direct": 15.16,
        "stc_eff_diffuse": 15.16,
        "tcoeff": 0.0040,
        "source": "Solar-Panel-Datasheets-COLLECTION.pdf",
    },
    "CST280M6-20": {
        "cell_type_raw": "monocrystalline",
        "module_height": 0.992,
        "stc_eff_direct": 17.21,
        "stc_eff_diffuse": 17.21,
        "tcoeff": 0.0040,
        "source": "Solar-Panel-Datasheets-COLLECTION.pdf",
    },
    "CST320M6-60H": {
        "cell_type_raw": "monocrystalline",
        "module_height": 1.002,
        "stc_eff_direct": 19.0,
        "stc_eff_diffuse": 19.0,
        "tcoeff": 0.0040,
        "source": "Solar-Panel-Datasheets-COLLECTION.pdf",
    },
    "CST220P6(90)": {
        "cell_type_raw": "polycrystalline",
        "module_height": 0.992,
        "stc_eff_direct": 16.19,
        "stc_eff_diffuse": 16.19,
        "tcoeff": 0.0040,
        "source": "Solar-Panel-Datasheets-COLLECTION.pdf",
    },
}


def get_panel_specs(model):
    if model not in PANEL_SPECS:
        raise ValueError(f"Unknown panel model: {model}")

    return PANEL_SPECS[model]


def get_panel_models():
    return list(PANEL_SPECS.keys())
