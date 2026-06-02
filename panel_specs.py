import json
from pathlib import Path

PANEL_SPECS_PATH = Path(__file__).parent / "data" / "panel_specs.json"

def load_panel_specs():
    with open(PANEL_SPECS_PATH, "r") as file:
        return json.load(file)

def get_panel_specs(model):
    specs = load_panel_specs()
    if model not in specs:
        raise ValueError(f"Unknown panel model: {model}")
    return specs[model]

def get_panel_models():
    return list(load_panel_specs().keys())
