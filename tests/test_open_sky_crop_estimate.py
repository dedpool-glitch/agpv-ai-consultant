from unittest.mock import patch

from services.combined_estimate_service import run_open_sky_crop_estimate
from services.guided_simple_estimate_service import run_guided_open_sky_estimate


def test_open_sky_crop_uses_weather_light_without_pvmaps():
    weather = [
        {"date": "2024-01-01", "solar_radiation_mj_m2": 7.5},
        {"date": "2024-01-02", "solar_radiation_mj_m2": 8.0},
    ]
    with patch("services.combined_estimate_service.fetch_daily_weather", return_value=weather), \
         patch("services.combined_estimate_service.run_simple", return_value={"crop": "rice"}) as simple, \
         patch("services.combined_estimate_service.run_pvmaps") as pv:
        result = run_open_sky_crop_estimate(40.4, -86.9, "rice", "2024-05-15")
    ground_light = simple.call_args.args[1]
    assert ground_light["light_mj_m2"] == [[7.5] * 101, [8.0] * 101]
    assert ground_light["unit"] == "MJ/m²/day"
    assert "without PV shade" in result["light_source"]
    assert "daily_surface_light" not in result
    pv.assert_not_called()


def test_guided_open_sky_run_saves_crop_only_result(tmp_path, monkeypatch):
    from services import simulation_log
    monkeypatch.setattr(simulation_log, "SIMULATION_LOG_PATH", tmp_path / "simulation_log.jsonl")
    state = {"session_id": "guided-test", "chat_messages": []}
    crop = {"crop": "rice", "sowing_date": "2024-05-15",
            "maturity_date": "2024-10-01", "mean_grain_yield_t_ha": 5.0}
    with patch("services.guided_simple_estimate_service.run_open_sky_crop_estimate",
               return_value=crop) as run:
        assert run_guided_open_sky_estimate(
            state, {"latitude": 40.4, "longitude": -86.9}, "rice", "2024-05-15"
        )
    run.assert_called_once_with(40.4, -86.9, "rice", "2024-05-15")
    assert state["pvmaps_runs"][0]["analysis"] == "crop_open_sky"
    assert state["pvmaps_runs"][0]["output"] == {}
    assert state["chat_messages"][0]["run_index"] == 0
    assert (tmp_path / "simulation_log.jsonl").exists()
