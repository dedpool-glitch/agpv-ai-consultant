from questionnaire_state import (
    initialize_questionnaire_state,
    update_questionnaire_state,
    apply_questionnaire_defaults,
)
from questionnaire_to_pvmaps import build_pvmaps_input_from_questionnaire
from pvmaps_input_validator import validate_pvmaps_input
from pvmaps_mock_runner import run_mock_pvmaps
from pvmaps_result_explainer import explain_pvmaps_result

state = initialize_questionnaire_state()

update_questionnaire_state(state, "panel_model", "CST320M6-60H")
update_questionnaire_state(state, "array_config", "tracking")
update_questionnaire_state(state, "pitch", 11.0)
update_questionnaire_state(state, "array_elevation", 3.0)

apply_questionnaire_defaults(state)

pvmaps_input = build_pvmaps_input_from_questionnaire(
    state,
    lat=40.4237,
    lon=-86.9212,
)

errors = validate_pvmaps_input(pvmaps_input)

if errors:
    print("Input validation failed:")
    for error in errors:
        print("-", error)
else:
    output = run_mock_pvmaps(pvmaps_input)
    print(explain_pvmaps_result(output))
    print("Assumptions:")
    for assumption in state["assumptions"]:
        print("-", assumption)