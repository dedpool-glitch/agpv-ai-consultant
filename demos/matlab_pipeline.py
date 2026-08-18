from constants import PVMAPS_SCRIPT_PATH
from models.pvmaps.input_builder import create_default_pvmaps_input
from models.pvmaps.input_validator import validate_pvmaps_input
from models.pvmaps.matlab_runner import run_pvmaps
from models.pvmaps.result_explainer import explain_pvmaps_result

pvmaps_input = create_default_pvmaps_input(32.692, -114.627)

errors = validate_pvmaps_input(pvmaps_input)

if errors:
    print("Input validation failed:")
    for error in errors:
        print("-", error)
else:
    output = run_pvmaps(pvmaps_input, PVMAPS_SCRIPT_PATH)
    explanation = explain_pvmaps_result(output)
    print(explanation)
