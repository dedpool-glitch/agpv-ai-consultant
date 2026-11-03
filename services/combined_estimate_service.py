"""Orchestrate the first validated PV + crop analysis path."""

from datetime import date

from constants import PVMAPS_SCRIPT_PATH
from models.pvmaps.matlab_runner import run_pvmaps
from models.simple.matlab_runner import run_simple
from models.simple.weather import fetch_daily_weather


def run_combined_estimate(pvmaps_input, crop, sowing_date):
    if isinstance(sowing_date, str):
        sowing_date = date.fromisoformat(sowing_date)
    year = sowing_date.year
    weather = fetch_daily_weather(pvmaps_input["lat"], pvmaps_input["lon"], year)
    pv = run_pvmaps(pvmaps_input, PVMAPS_SCRIPT_PATH, include_ground_light=True, light_year=year)
    crop_result = run_simple(
        weather, pv["ground_light"], crop, sowing_date, pv["open_sky_light"]
    )
    return {"pv": pv, "crop": crop_result}
