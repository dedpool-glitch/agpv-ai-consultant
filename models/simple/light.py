"""Convert representative PV-MAPS ground light into dated SIMPLE inputs.

PV-MAPS simulates one representative day per month. Its ground-light curves
are integrated by the MATLAB runner into MJ/m²/day at each ground position.
SIMPLE expects one row per calendar day and one column per position.
"""

from calendar import monthrange
from datetime import date
import math


def expand_monthly_ground_light(monthly_mj_m2, year):
    """Return dated daily rows (365 or 366 by 101) in MJ/m²/day.

    This preserves the reference driver's monthly repetition. It does not
    claim to reconstruct daily cloud variation within a month.
    """
    if not isinstance(year, int) or isinstance(year, bool) or year < 1:
        raise ValueError("Year must be a positive integer.")
    if len(monthly_mj_m2) != 12:
        raise ValueError("PV-MAPS must provide exactly 12 monthly light profiles.")

    daily = []
    dates = []
    for month, profile in enumerate(monthly_mj_m2, start=1):
        if len(profile) != 101:
            raise ValueError(f"Month {month} must contain 101 ground positions.")
        values = [float(value) for value in profile]
        if any(not math.isfinite(value) or value < 0 for value in values):
            raise ValueError(f"Month {month} contains invalid ground light.")
        for day in range(1, monthrange(year, month)[1] + 1):
            dates.append(date(year, month, day).isoformat())
            daily.append(values.copy())
    return {"dates": dates, "light_mj_m2": daily, "unit": "MJ/m²/day"}

