from pvmaps_input_builder import create_default_pvmaps_input
from pvmaps_input_validator import validate_pvmaps_input
from pvmaps_matlab_runner import run_pvmaps
from pvmaps_result_explainer import explain_pvmaps_result

pvmaps_input = create_default_pvmaps_input(32.692, -114.627)

errors = validate_pvmaps_input(pvmaps_input)

if errors:
    print("Input validation failed:")
    for error in errors:
        print("-", error)
else:
    pvmaps_folder_path = r"D:/agpv-ai-consultant/PV-MAPS-main"
    output = run_pvmaps(pvmaps_input, pvmaps_folder_path)
    explanation = explain_pvmaps_result(output)
    print(explanation)
