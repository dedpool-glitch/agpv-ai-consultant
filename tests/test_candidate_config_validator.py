from llm.candidate_config_validator import validate_candidate_config


def candidate(array_config):
    return {
        "pvmaps_inputs": {
            "panel_model": "default values",
            "array_config": array_config,
            "tilt": 25,
            "azimuth": 90,
            "albedo": 0.3,
            "pitch": 11,
            "gs_height": 0.5,
            "array_elevation": 3,
        },
    }


def test_recommender_candidate_rejects_gsvbf_for_bundled_build():
    parsed, errors = validate_candidate_config(candidate("GSVBF"))

    assert parsed is None
    assert any("temporarily unavailable" in error for error in errors)


def test_recommender_candidate_keeps_working_configuration():
    parsed, errors = validate_candidate_config(candidate("tracking"))

    assert errors == []
    assert parsed["array_config"] == "tracking"
