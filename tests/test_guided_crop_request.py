from services.guided_crop_request import resolve_crop_analysis, resolve_crop_inputs


def test_one_message_provides_crop_and_sowing_date():
    inputs = resolve_crop_inputs(
        "Estimate maize yield if I sow on May 15, 2024", {"analysis": "solar_and_crop"}
    )
    assert inputs == {"crop": "maize", "sowing_date": "2024-05-15"}


def test_followup_fills_missing_date_without_losing_crop():
    pending = {"crop": "soybean", "sowing_date": None}
    inputs = resolve_crop_inputs("June 1, 2025", {}, pending)
    assert inputs == {"crop": "soybean", "sowing_date": "2025-06-01"}


def test_invalid_date_and_unsupported_crop_are_not_invented():
    inputs = resolve_crop_inputs(
        "Estimate wheat yield on February 30, 2024",
        {"crop": "wheat", "sowing_date": "2024-02-30"},
    )
    assert inputs == {"crop": None, "sowing_date": None}


def test_crop_context_is_explicit_or_clarified():
    assert resolve_crop_analysis("Estimate rice yield", {}, {}) == "crop_unspecified"
    assert resolve_crop_analysis("under panels", {}, {}) == "solar_and_crop"
    assert resolve_crop_analysis("without PV", {}, {"analysis": "solar_and_crop"}) == "crop_open_sky"
    assert resolve_crop_analysis("May 15 2024", {}, {"analysis": "crop_open_sky"}) == "crop_open_sky"
