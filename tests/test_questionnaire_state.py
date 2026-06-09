import pytest
from questionnaire_state import (
    initialize_questionnaire_state,
    update_questionnaire_state,
    get_next_question,
    apply_questionnaire_defaults
)

def test_initial_questionnaire_state():
    state = initialize_questionnaire_state()
    assert state == {
        "panel_model": None,
        "array_config": None,
        "tilt": None,
        "azimuth": None,
        "albedo": None,
        "pitch": None,
        "gs_height": None,
        "array_elevation": None,
        "assumptions": []
    }

def test_first_question():
    state=initialize_questionnaire_state()
    first_question=get_next_question(state)
    assert first_question["field"]=="panel_model"

def test_update_questionnaire_state():
    state=initialize_questionnaire_state()
    state=update_questionnaire_state(state, "panel_model", "default values")
    assert state["panel_model"] == "default values"

def test_blank_answer():
    state=initialize_questionnaire_state()
    with pytest.raises(ValueError):
        update_questionnaire_state(state, "panel_model", "")

def test_defaults_fill_missing_fields():
    state = initialize_questionnaire_state()
    update_questionnaire_state(state, "panel_model", "default values")
    apply_questionnaire_defaults(state)
    assert state["panel_model"] == "default values"
    assert state["array_config"] == "tracking"
    assert state["tilt"] == 25.0
    assert state["azimuth"] == 90.0
    assert state["albedo"] == 0.3
    assert state["pitch"] == 11.0
    assert state["gs_height"] == 0.5
    assert state["array_elevation"] == 3.0
