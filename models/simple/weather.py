"""Fetch and validate daily NASA POWER weather for SIMPLE."""

from datetime import date, timedelta
import math

import requests


POWER_DAILY_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
PARAMETERS = ("T2M", "T2M_MAX", "ALLSKY_SFC_SW_DWN")


def _radiation_to_mj(value, units):
    normalized = str(units).lower().replace(" ", "").replace("²", "2").replace("^", "")
    if normalized in {"mj/m2/day", "mj/m2/d"}:
        return value
    if normalized in {"kwh/m2/day", "kwh/m2/d"}:
        return value * 3.6
    raise ValueError(f"Unsupported NASA POWER solar radiation unit: {units!r}")


def parse_daily_weather(payload, year):
    """Return one dated row per day, with radiation in MJ/m²/day."""
    if not isinstance(year, int) or year < 1981:
        raise ValueError("Weather year must be an integer from 1981 onward.")

    try:
        series = payload["properties"]["parameter"]
        information = payload["parameters"]
        radiation_unit = information["ALLSKY_SFC_SW_DWN"]["units"]
        mean_temperature_unit = information["T2M"]["units"]
        max_temperature_unit = information["T2M_MAX"]["units"]
    except (KeyError, TypeError) as exc:
        raise ValueError("NASA POWER response is missing weather data or unit metadata.") from exc

    for unit in (mean_temperature_unit, max_temperature_unit):
        if str(unit).strip().lower() not in {"c", "°c", "deg c", "degc"}:
            raise ValueError(f"Unsupported temperature unit: {unit!r}")

    first_day = date(year, 1, 1)
    last_day = date(year + 1, 1, 1)
    fill_value = payload.get("header", {}).get("fill_value", -999)
    rows = []
    current_day = first_day
    while current_day < last_day:
        day_key = current_day.strftime("%Y%m%d")
        values = {}
        for name in PARAMETERS:
            try:
                raw = float(series[name][day_key])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"NASA POWER is missing {name} for {day_key}.") from exc
            if not math.isfinite(raw) or raw == fill_value or raw == -999:
                raise ValueError(f"NASA POWER has no valid {name} for {day_key}.")
            values[name] = raw

        rows.append({
            "date": current_day.isoformat(),
            "doy": current_day.timetuple().tm_yday,
            "t2m_c": values["T2M"],
            "t2m_max_c": values["T2M_MAX"],
            "solar_radiation_mj_m2": _radiation_to_mj(
                values["ALLSKY_SFC_SW_DWN"], radiation_unit
            ),
        })
        current_day += timedelta(days=1)
    return rows


def fetch_daily_weather(latitude, longitude, year, session=None):
    """Request a complete site-specific year from the NASA POWER daily API."""
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("Latitude or longitude is outside its valid range.")
    if not isinstance(year, int) or year < 1981:
        raise ValueError("Weather year must be an integer from 1981 onward.")

    client = session or requests
    response = client.get(
        POWER_DAILY_URL,
        params={
            "parameters": ",".join(PARAMETERS),
            "community": "AG",
            "longitude": longitude,
            "latitude": latitude,
            "start": f"{year}0101",
            "end": f"{year}1231",
            "format": "JSON",
            "time-standard": "LST",
        },
        timeout=30,
    )
    response.raise_for_status()
    return parse_daily_weather(response.json(), year)
