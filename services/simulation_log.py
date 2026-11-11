"""Append compact, completed model runs to a durable local JSONL log."""

import json
from datetime import datetime

from constants import OUTPUT_DIR
from services.run_context import compact_run


SIMULATION_LOG_PATH = OUTPUT_DIR / "simulation_log.jsonl"


def log_simulation_run(session_id, mode, run):
    """Log model inputs and result summaries without large daily arrays."""
    if not session_id:
        return False
    summary = compact_run(run)
    crop_profile = (run.get("crop_result") or {}).get("grain_yield_t_ha_by_position")
    if isinstance(crop_profile, list) and len(crop_profile) <= 101:
        summary["crop_result"]["grain_yield_t_ha_by_position"] = crop_profile
    daily_yield = (run.get("output") or {}).get("daily_yield")
    if isinstance(daily_yield, list) and len(daily_yield) <= 366:
        summary["output"]["daily_yield"] = daily_yield
    row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "session_id": session_id,
        "mode": mode,
        "analysis": run.get("analysis") or (
            "solar_and_crop" if run.get("crop_result") else "solar"
        ),
        "run": summary,
    }
    try:
        SIMULATION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with SIMULATION_LOG_PATH.open("a", encoding="utf-8") as file:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")
    except (OSError, TypeError, ValueError):
        return False
    return True
