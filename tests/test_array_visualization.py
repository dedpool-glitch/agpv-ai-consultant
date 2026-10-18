import matplotlib

matplotlib.use("Agg")

from ui.array_visualization import (
    _azimuth_vector,
    configuration_caption,
    create_array_configuration_figure,
)


def sample_input(config="fixed"):
    return {
        "module": {"height": 4.8},
        "array": {
            "config": config,
            "tilt": 30,
            "azimuth": 90,
            "albedo": 0.3,
            "pitch": 11,
            "elevation": 3,
            "gsHeight": 0.5,
        },
    }


def test_fixed_caption_includes_fixed_tilt():
    caption = configuration_caption(sample_input()["array"])

    assert "30 degree tilt" in caption
    assert "11 m pitch" in caption
    assert "0.3 ground albedo" in caption


def test_tracking_caption_does_not_present_recorded_tilt_as_operating_tilt():
    caption = configuration_caption(sample_input("tracking")["array"])

    assert "degree tilt" not in caption
    assert "Tracking array" in caption


def test_all_supported_configurations_render():
    for config in ("fixed", "tracking", "GSVBF"):
        figure = create_array_configuration_figure(sample_input(config))
        try:
            assert len(figure.axes) == 3
            assert figure.axes[0].get_title(loc="left")
            assert any("adjacent rows" in text.get_text()
                       for text in figure.axes[0].texts)
            assert any("Azimuth: 90 degrees" in text.get_text()
                       for text in figure.axes[1].texts)
            assert any("Albedo 0.3" in text.get_text()
                       for text in figure.axes[2].texts)
            assert any("30% of incident light reflected" in text.get_text()
                       for text in figure.axes[2].texts)
        finally:
            figure.clear()


def test_azimuth_vector_uses_clockwise_degrees_from_north():
    east_x, east_y = _azimuth_vector(90)
    south_x, south_y = _azimuth_vector(180)

    assert round(east_x, 6) == 1
    assert round(east_y, 6) == 0
    assert round(south_x, 6) == 0
    assert round(south_y, 6) == -1
