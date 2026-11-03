from datetime import date, timedelta

import pytest

from models.simple.matlab_runner import run_simple


def _inputs():
    start = date(2024, 1, 1)
    weather = [
        {"date": (start + timedelta(days=i)).isoformat(), "doy": i + 1,
         "t2m_c": 20.0, "t2m_max_c": 30.0, "solar_radiation_mj_m2": 18.0}
        for i in range(366)
    ]
    light = {"dates": [row["date"] for row in weather],
             "light_mj_m2": [[15.0] * 101 for _ in weather],
             "unit": "MJ/m²/day"}
    return weather, light


def test_rejects_misaligned_light_before_starting_matlab():
    weather, light = _inputs()
    light["dates"][59] = "2024-03-01"
    with pytest.raises(ValueError, match="Ground light must contain every day"):
        run_simple(weather, light, "maize", "2024-05-15")


def test_rejects_weather_from_wrong_year():
    weather, light = _inputs()
    with pytest.raises(ValueError, match="sowing year"):
        run_simple(weather, light, "maize", "2025-05-15")


def test_rejects_open_sky_series_from_wrong_dates_before_matlab():
    weather, light = _inputs()
    open_sky = {"dates": light["dates"][:-1],
                "light_mj_m2": [18.0] * 365, "unit": "MJ/m²/day"}
    with pytest.raises(ValueError, match="Open-sky light must align"):
        run_simple(weather, light, "maize", "2024-05-15", open_sky)
