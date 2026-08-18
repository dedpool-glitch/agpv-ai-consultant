from models.pvmaps.descriptor import (
    PVMAPS_DESCRIPTOR_PATH,
    build_pvmaps_input_from_descriptor_values,
    get_expert_form_descriptors,
    get_pvmaps_input_descriptors,
    validate_pvmaps_descriptor_input,
)


EXPERT_FIELD_IDS = {
    "array.config",
    "array.tilt",
    "array.azimuth",
    "array.albedo",
    "array.pitch",
    "array.gsHeight",
    "array.elevation",
}


def test_descriptor_is_model_local():
    assert PVMAPS_DESCRIPTOR_PATH.name == "pvmaps.json"
    assert PVMAPS_DESCRIPTOR_PATH.parent.name == "pvmaps"
    assert PVMAPS_DESCRIPTOR_PATH.parent.parent.name == "models"


def test_expert_form_contains_every_descriptor_input():
    descriptor_ids = {field["id"] for field in get_expert_form_descriptors()}
    all_input_ids = {field["id"] for field in get_pvmaps_input_descriptors()}
    assert descriptor_ids == all_input_ids
    assert EXPERT_FIELD_IDS <= descriptor_ids


def test_all_input_fields_define_form_metadata():
    for field in get_pvmaps_input_descriptors():
        assert field["name"]
        assert field["description"]
        assert field["element_type"] in {"float", "integer", "string", "boolean"}
        assert field["default"] is not None
        assert isinstance(field.get("constraints"), dict)


def test_descriptor_defaults_build_complete_nested_input():
    defaults = {
        field["id"]: field["default"]
        for field in get_pvmaps_input_descriptors()
    }
    pvmaps_input = build_pvmaps_input_from_descriptor_values(defaults)

    assert pvmaps_input["module"]["cell_tech"] == "AL_BSF"
    assert pvmaps_input["array"]["config"] == "tracking"
    assert pvmaps_input["lat"] == 32.692
    assert pvmaps_input["lon"] == -114.627
    assert pvmaps_input["sim"]["quickSim"] is True
    assert validate_pvmaps_descriptor_input(pvmaps_input) == []


def _default_descriptor_input():
    return build_pvmaps_input_from_descriptor_values({
        field["id"]: field["default"]
        for field in get_pvmaps_input_descriptors()
    })


def test_descriptor_constraints_reject_invalid_scalar_values():
    pvmaps_input = _default_descriptor_input()
    pvmaps_input["array"]["azimuth"] = 361
    pvmaps_input["array"]["pitch"] = 0
    pvmaps_input["module"]["tcoeff"] = 0.02

    errors = validate_pvmaps_descriptor_input(pvmaps_input)

    assert any("Array Azimuth must be at most" in error for error in errors)
    assert any("Array Pitch must be greater than" in error for error in errors)
    assert any("Temperature Coefficient must be at most" in error for error in errors)


def test_descriptor_cross_field_rule_is_applied():
    pvmaps_input = _default_descriptor_input()
    pvmaps_input["array"]["elevation"] = pvmaps_input["module"]["height"] / 2

    errors = validate_pvmaps_descriptor_input(pvmaps_input)

    assert "Array Elevation must be greater than half the Module Height." in errors
