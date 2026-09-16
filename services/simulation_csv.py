"""CSV exports of saved PVMAPS runs for independent analysis."""

import csv
from io import StringIO

from constants import MONTH_LABELS
from models.pvmaps.descriptor import get_pvmaps_input_descriptors
from ui.simulation_result import PARAMETER_KEYS


def _input_value(inputs, field_id):
    value = inputs
    for part in field_id.split("."):
        value = value.get(part) if isinstance(value, dict) else None
    return value


def _input_origin(run, field_id):
    provenance = run.get("input_provenance") or {}
    group = field_id.split(".")[0]
    if field_id in PARAMETER_KEYS:
        origin = (provenance.get("parameters") or {}).get(PARAMETER_KEYS[field_id]) or {}
    else:
        origin = provenance.get("location" if group in ("lat", "lon") else group) or {}
    return origin.get("source") or provenance.get("source") or ""


def _csv_bytes(fieldnames, rows):
    buffer = StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8-sig")


def run_summary_rows(runs):
    """One row per run, with raw inputs and annual/monthly output values."""
    fields = get_pvmaps_input_descriptors()
    fieldnames = ["run_id", "run_label", "location", "yearly_yield", "yield_unit"]
    fieldnames.extend(f"monthly_yield_{month.lower()}" for month in MONTH_LABELS)
    for field in fields:
        prefix = f"input_{field['id'].replace('.', '_')}"
        fieldnames.extend((prefix, f"{prefix}_unit", f"{prefix}_origin"))
    fieldnames.extend(("input_array_tilt_used", "input_array_gsHeight_used"))

    rows = []
    for index, run in enumerate(runs, start=1):
        inputs, output = run.get("input") or {}, run.get("output") or {}
        location = run.get("location_context") or {}
        row = {
            "run_id": index,
            "run_label": run.get("label") or "Solar-yield estimate",
            "location": location.get("confirmed_address") or location.get("site_location") or "",
            "yearly_yield": output.get("yearly_yield"),
            "yield_unit": output.get("yield_unit") or "",
        }
        for month, value in zip(MONTH_LABELS, output.get("monthly_yield") or []):
            row[f"monthly_yield_{month.lower()}"] = value
        for field in fields:
            prefix = f"input_{field['id'].replace('.', '_')}"
            row[prefix] = _input_value(inputs, field["id"])
            row[f"{prefix}_unit"] = field.get("unit") or ""
            row[f"{prefix}_origin"] = _input_origin(run, field["id"])
        config = _input_value(inputs, "array.config")
        row["input_array_tilt_used"] = config == "fixed"
        row["input_array_gsHeight_used"] = config == "GSVBF"
        rows.append(row)
    return fieldnames, rows


def build_run_summary_csv(runs):
    return _csv_bytes(*run_summary_rows(runs))


def daily_yield_rows(runs):
    """One row per saved day; index is ordered, not a calendar date."""
    rows = []
    for run_id, run in enumerate(runs, start=1):
        output = run.get("output") or {}
        for day_index, value in enumerate(output.get("daily_yield") or [], start=1):
            rows.append({
                "run_id": run_id,
                "day_index": day_index,
                "daily_yield": value,
                "yield_unit": output.get("yield_unit") or "",
            })
    return ["run_id", "day_index", "daily_yield", "yield_unit"], rows


def build_daily_yield_csv(runs):
    return _csv_bytes(*daily_yield_rows(runs))
