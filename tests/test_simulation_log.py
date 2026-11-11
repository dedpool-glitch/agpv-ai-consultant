import json

from services import simulation_log


def test_completed_simple_run_is_logged_without_large_arrays(tmp_path, monkeypatch):
    path = tmp_path / "simulation_log.jsonl"
    monkeypatch.setattr(simulation_log, "SIMULATION_LOG_PATH", path)
    run = {
        "analysis": "crop_open_sky",
        "label": "Crop yield without PV",
        "input": {"lat": 40.4, "lon": -86.9},
        "output": {"ground_light": {"light_mj_m2": [[7.0] * 101] * 365}},
        "crop_result": {
            "crop": "maize", "sowing_date": "2024-05-15",
            "maturity_date": "2024-10-05", "mean_grain_yield_t_ha": 12.4,
            "grain_yield_t_ha_by_position": [12.4] * 101,
        },
    }
    assert simulation_log.log_simulation_run("session-1", "guided", run)
    row = json.loads(path.read_text(encoding="utf-8").strip())
    assert row["analysis"] == "crop_open_sky"
    assert row["run"]["crop_result"]["mean_grain_yield_t_ha"] == 12.4
    assert row["run"]["input"]["lat"] == 40.4
    assert "ground_light" not in row["run"]["output"]
    assert len(row["run"]["crop_result"]["grain_yield_t_ha_by_position"]) == 101
