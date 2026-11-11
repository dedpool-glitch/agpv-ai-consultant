"""Compact saved simulation runs before placing them in LLM prompts."""


def compact_run(run):
    if not run:
        return None
    output = run.get("output") or {}
    compact = {key: run.get(key) for key in (
        "label", "input", "input_provenance", "assumptions", "overrides",
        "user_request", "location_context",
    )}
    compact["output"] = {key: output.get(key) for key in (
        "yearly_yield", "yield_unit", "monthly_yield", "warnings",
    ) if output.get(key) is not None}
    crop = run.get("crop_result")
    if crop:
        compact["crop_result"] = {key: crop.get(key) for key in (
            "crop", "sowing_date", "maturity_date", "mean_grain_yield_t_ha",
            "open_sky_grain_yield_t_ha", "difference_from_open_sky_t_ha",
            "difference_from_open_sky_percent", "assumptions", "light_source",
        ) if crop.get(key) is not None}
        yields = crop.get("grain_yield_t_ha_by_position") or []
        if yields:
            low = min(range(len(yields)), key=yields.__getitem__)
            high = max(range(len(yields)), key=yields.__getitem__)
            compact["crop_result"].update({
                "lowest_position_index": low, "lowest_yield_t_ha": yields[low],
                "highest_position_index": high, "highest_yield_t_ha": yields[high],
                "position_note": "Ordered model indices; exact panel-relative coordinates are not verified.",
            })
    return compact
