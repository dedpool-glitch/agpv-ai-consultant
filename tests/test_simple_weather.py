from datetime import date, timedelta

import pytest

from models.simple.weather import parse_daily_weather


def _power_payload(year, radiation_unit="MJ/m^2/day"):
    days = (date(year + 1, 1, 1) - date(year, 1, 1)).days
    keys = [
        (date(year, 1, 1) + timedelta(days=offset)).strftime("%Y%m%d")
        for offset in range(days)
    ]
    return {
        "header": {"fill_value": -999},
        "parameters": {
            "T2M": {"units": "C"},
            "T2M_MAX": {"units": "C"},
            "ALLSKY_SFC_SW_DWN": {"units": radiation_unit},
        },
        "properties": {"parameter": {
            "T2M": {key: 20 for key in keys},
            "T2M_MAX": {key: 30 for key in keys},
            "ALLSKY_SFC_SW_DWN": {key: 5 for key in keys},
        }},
    }


def test_leap_year_and_radiation_conversion():
    rows = parse_daily_weather(_power_payload(2024, "kWh/m^2/day"), 2024)
    assert len(rows) == 366
    assert rows[59]["date"] == "2024-02-29"
    assert rows[59]["doy"] == 60
    assert rows[59]["solar_radiation_mj_m2"] == pytest.approx(18.0)


def test_missing_day_is_rejected():
    payload = _power_payload(2025)
    del payload["properties"]["parameter"]["T2M_MAX"]["20250601"]
    with pytest.raises(ValueError, match="T2M_MAX for 20250601"):
        parse_daily_weather(payload, 2025)
