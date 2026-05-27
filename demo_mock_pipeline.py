from pvmaps_input_validator import validate_pvmaps_input
from pvmaps_input_builder import create_default_pvmaps_input
from pvmaps_mock_runner import run_mock_pvmaps
from pvmaps_result_explainer import explain_pvmaps_result

pvmaps_input = create_default_pvmaps_input(40.4237, -86.9212) #example

errors=validate_pvmaps_input(pvmaps_input)
if errors:
    print("Input validation failed with the following errors:")
    for error in errors:
        print(f"- {error}")
else:
    pvmaps_output=run_mock_pvmaps(pvmaps_input)
    print("PVMAPS Output:")
    print(pvmaps_output)
    explanation = explain_pvmaps_result(pvmaps_output)
    print("\nExplanation:")
    print(explanation)
