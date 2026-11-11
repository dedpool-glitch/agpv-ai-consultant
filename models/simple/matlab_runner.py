"""Bridge dated daily Python inputs to Jabir's SIMPLE MATLAB model."""

from datetime import date, timedelta
from pathlib import Path
import math

import matlab
import matlab.engine
from models.simple.crops import CROP_FILES


def run_simple(weather_rows, ground_light, crop, sowing_date, open_sky_light=None):
    """Run SIMPLE, repeating the supplied year if maturity crosses December."""
    if isinstance(sowing_date, str):
        sowing_date = date.fromisoformat(sowing_date)
    if crop not in CROP_FILES:
        raise ValueError(f"Unsupported crop: {crop!r}")
    year = sowing_date.year
    start = date(year, 1, 1)
    expected_dates = [(start + timedelta(days=i)).isoformat()
                      for i in range((date(year + 1, 1, 1) - start).days)]
    if [row["date"] for row in weather_rows] != expected_dates:
        raise ValueError("Weather must contain every day of the sowing year in calendar order.")
    if ground_light["dates"] != expected_dates:
        raise ValueError("Ground light must contain every day of the sowing year in calendar order.")
    light = ground_light["light_mj_m2"]
    if len(light) != len(expected_dates) or any(len(row) != 101 for row in light):
        raise ValueError("Ground light must have one row per day and 101 positions.")
    if ground_light.get("unit") != "MJ/m²/day":
        raise ValueError("Ground light must be in MJ/m²/day.")
    if any(not math.isfinite(float(value)) or value < 0 for row in light for value in row):
        raise ValueError("Ground light contains invalid values.")
    if open_sky_light is not None:
        if (open_sky_light.get("dates") != expected_dates or
                open_sky_light.get("unit") != "MJ/m²/day"):
            raise ValueError("Open-sky light must align with the sowing year in MJ/m²/day.")
        open_values = open_sky_light.get("light_mj_m2") or []
        if len(open_values) != len(expected_dates) or any(
            not math.isfinite(float(value)) or value < 0 for value in open_values
        ):
            raise ValueError("Open-sky light must contain one valid value per day.")

    root = Path(__file__).resolve().parent
    eng = matlab.engine.start_matlab()
    try:
        eng.addpath(str(root), nargout=0)
        eng.eval("set(groot,'defaultFigureVisible','off');", nargout=0)
        eng.workspace["crop_t2m"] = matlab.double([row["t2m_c"] for row in weather_rows])
        eng.workspace["crop_tmax"] = matlab.double([row["t2m_max_c"] for row in weather_rows])
        eng.workspace["crop_rad"] = matlab.double([row["solar_radiation_mj_m2"] for row in weather_rows])
        eng.workspace["crop_doy"] = matlab.double([row["doy"] for row in weather_rows])
        eng.eval(
            "crop_weather=table(crop_t2m(:),crop_tmax(:),crop_rad(:),crop_doy(:),"
            "'VariableNames',{'T2M','T2M_MAX','ALLSKY_SFC_SW_DWN','DOY'});",
            nargout=0,
        )
        eng.workspace["crop_lightmap"] = matlab.double(light)
        eng.workspace["crop_spec_path"] = str(root / "crop_specs" / CROP_FILES[crop])
        eng.eval("crop_file=load(crop_spec_path,'crop_spec');", nargout=0)
        eng.workspace["crop_sowing_iso"] = sowing_date.isoformat()
        eng.eval(
            "crop_result=core_simple(crop_weather,crop_file.crop_spec,"
            "datetime(crop_sowing_iso,'InputFormat','yyyy-MM-dd'),crop_lightmap);",
            nargout=0,
        )
        eng.eval("crop_maturity_iso=char(string(crop_result.mature_date,'yyyy-MM-dd'));", nargout=0)
        result = eng.workspace["crop_result"]
        crop_output = {
            "crop": crop,
            "sowing_date": sowing_date.isoformat(),
            "maturity_date": str(eng.workspace["crop_maturity_iso"]),
            "mean_grain_yield_t_ha": float(result["grain_yield_thec_mean"]),
            "grain_yield_t_ha_by_position": list(result["grain_yield_thec_segments"][0]),
            "assumptions": ["No water stress", "Fixed soil parameters in supplied SIMPLE core",
                            "Sowing-year weather and light repeat if maturity crosses December"],
        }
        if open_sky_light is not None:
            eng.workspace["crop_open_light"] = matlab.double(open_values)
            eng.eval(
                "crop_baseline=core_simple(crop_weather,crop_file.crop_spec,"
                "datetime(crop_sowing_iso,'InputFormat','yyyy-MM-dd'),"
                "crop_open_light(:));",
                nargout=0,
            )
            baseline = float(eng.workspace["crop_baseline"]["grain_yield_thec_mean"])
            difference = crop_output["mean_grain_yield_t_ha"] - baseline
            crop_output["open_sky_grain_yield_t_ha"] = baseline
            crop_output["difference_from_open_sky_t_ha"] = difference
            crop_output["difference_from_open_sky_percent"] = (
                100 * difference / baseline if baseline > 0 else None
            )
        return crop_output
    finally:
        eng.quit()
