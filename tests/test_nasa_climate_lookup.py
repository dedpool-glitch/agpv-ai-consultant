from services.nasa_power_lookup import get_climate_summary


def test_nasa_power_lookup_returns_expected_keys():
    summary = get_climate_summary(40.42, -86.91)

    assert "input_location" in summary
    assert "nearest_grid_location" in summary
    assert "elevation_m" in summary
    assert "annual" in summary
    assert "monthly_ghi" in summary


def test_nasa_power_lookup_maps_lafayette_to_nearby_grid():
    summary = get_climate_summary(40.42, -86.91)

    assert summary["nearest_grid_location"]["lat"] == 40
    assert summary["nearest_grid_location"]["lon"] == -87


def test_nasa_power_lookup_has_12_monthly_ghi_values():
    summary = get_climate_summary(40.42, -86.91)

    assert len(summary["monthly_ghi"]) == 12