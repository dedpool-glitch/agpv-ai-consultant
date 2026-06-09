from pvmaps_input_builder import create_default_pvmaps_input
from pvmaps_input_validator import validate_pvmaps_input
from constants import PVMAPS_VALIDATION_MESSAGES


def make_valid_pvmaps_input():
    return create_default_pvmaps_input(
        lat=40.42,
        lon=-86.91,
        cell_tech="AL_BSF",
        module_height=4.8,
        stc_eff_direct=21.8,
        stc_eff_diffuse=21.8,
        tcoeff=0.0041,
        array_config="tracking",
        tilt=25,
        azimuth=90,
        albedo=0.3,
        pitch=11,
        gs_height=0.5,
        array_elevation=3,
    )


def test_valid_pvmaps_input_has_no_errors():
    data = make_valid_pvmaps_input()
    errors = validate_pvmaps_input(data)
    assert errors == []


def test_invalid_tilt_is_rejected():
    data = make_valid_pvmaps_input()
    data["array"]["tilt"] = 100
    errors = validate_pvmaps_input(data)
    assert PVMAPS_VALIDATION_MESSAGES["tilt_range"] in errors


def test_invalid_array_config_is_rejected():
    data = make_valid_pvmaps_input()
    data["array"]["config"] = "bad_config"
    errors = validate_pvmaps_input(data)
    assert PVMAPS_VALIDATION_MESSAGES["invalid_array_config"] in errors


def test_invalid_pitch_is_rejected():
    data = make_valid_pvmaps_input()
    data["array"]["pitch"] = 0
    errors = validate_pvmaps_input(data)
    assert PVMAPS_VALIDATION_MESSAGES["pitch_positive"] in errors


def test_invalid_azimuth_is_rejected():
    data = make_valid_pvmaps_input()
    data["array"]["azimuth"] = 45
    errors = validate_pvmaps_input(data)
    assert PVMAPS_VALIDATION_MESSAGES["azimuth_range"] in errors

