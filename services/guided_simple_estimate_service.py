"""Save a Guided SIMPLE crop estimate without running PV-MAPS."""

import copy

from constants import MESSAGE_ROLE_ASSISTANT, MESSAGE_TYPE_PVMAPS_RUN
from services.combined_estimate_service import run_open_sky_crop_estimate
from services.llm_trace import add_llm_trace
from services.run_context import compact_run
from services.simulation_log import log_simulation_run


def run_guided_open_sky_estimate(session_state, location_context, crop, sowing_date):
    latitude = location_context["latitude"]
    longitude = location_context["longitude"]
    crop_result = run_open_sky_crop_estimate(latitude, longitude, crop, sowing_date)
    explanation = (
        f"SIMPLE estimates {crop_result['mean_grain_yield_t_ha']:.2f} t/ha "
        f"mean {crop} grain yield without PV shade, with maturity on "
        f"{crop_result['maturity_date']}. This uses site weather and is a "
        "modeled estimate, not a measured harvest."
    )
    run = {
        "analysis": "crop_open_sky",
        "label": "Crop yield without PV",
        "location_context": copy.deepcopy(location_context),
        "input": {"lat": latitude, "lon": longitude},
        "output": {},
        "crop_result": crop_result,
        "explanation": explanation,
    }
    runs = session_state.setdefault("pvmaps_runs", [])
    runs.append(run)
    messages = session_state.setdefault("chat_messages", [])
    messages.append({
        "role": MESSAGE_ROLE_ASSISTANT,
        "type": MESSAGE_TYPE_PVMAPS_RUN,
        "run_index": len(runs) - 1,
    })
    messages.append({"role": MESSAGE_ROLE_ASSISTANT, "content": explanation})
    add_llm_trace(
        session_state, "guided_simple_run",
        input_summary={"crop": crop, "sowing_date": str(sowing_date),
                       "location_context": location_context},
        output=compact_run(run), decision="crop_estimate_completed",
    )
    log_simulation_run(session_state.get("session_id"), "guided", run)
    return True
