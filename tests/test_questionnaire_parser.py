import pytest
from questionnaire.parser import parse_questionnaire_answer

def test_empty_questionnaire_answer():
    with pytest.raises(ValueError):
        parse_questionnaire_answer("field","")

def test_tilt_numeric_string_becomes_float():
    result = parse_questionnaire_answer("tilt", "25")
    assert result == 25.0


def test_tilt_rejects_non_numeric_text():
    with pytest.raises(ValueError):
        parse_questionnaire_answer("tilt", "abc")


def test_tilt_rejects_value_above_90():
    with pytest.raises(ValueError):
        parse_questionnaire_answer("tilt", "100")


def test_array_config_accepts_tracking():
    result = parse_questionnaire_answer("array_config", "tracking")
    assert result == "tracking"

def test_array_config_rejects_invalid_value():
    with pytest.raises(ValueError):
        parse_questionnaire_answer("array_config", ".")


def test_azimuth_accepts_90():
    result = parse_questionnaire_answer("azimuth", "90")
    assert result == 90.0


def test_azimuth_rejects_45():
    with pytest.raises(ValueError):
        parse_questionnaire_answer("azimuth", "45")


def test_albedo_rejects_value_above_1():
    with pytest.raises(ValueError):
        parse_questionnaire_answer("albedo", "2")


def test_pitch_rejects_zero():
    with pytest.raises(ValueError):
        parse_questionnaire_answer("pitch", "0")
