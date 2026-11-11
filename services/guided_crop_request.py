"""Resolve crop simulation inputs from a Guided conversation."""

from datetime import date, datetime
import re

from models.simple.crops import CROP_FILES


_DATE_PATTERNS = (
    (r"\b\d{4}-\d{1,2}-\d{1,2}\b", "%Y-%m-%d"),
    (r"\b\d{4}/\d{1,2}/\d{1,2}\b", "%Y/%m/%d"),
    (r"\b\d{1,2}/\d{1,2}/\d{4}\b", "%m/%d/%Y"),
    (r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b", None),
    (r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b", None),
)


def parse_sowing_date(value):
    if isinstance(value, date):
        return value
    text = str(value or "").strip()
    for pattern, fmt in _DATE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        candidate = match.group().replace(",", "")
        formats = (fmt,) if fmt else ("%B %d %Y", "%d %B %Y")
        for date_format in formats:
            try:
                return datetime.strptime(candidate, date_format).date()
            except ValueError:
                pass
    return None


def resolve_crop_inputs(message, plan, pending=None):
    pending = pending or {}
    text = str(message or "")
    crop_match = re.search(r"\b(?:maize|rice|sorghum|soybean)\b", text, re.IGNORECASE)
    crop = (crop_match.group().lower() if crop_match else None)
    if crop is None:
        candidate = str(plan.get("crop") or "").lower()
        crop = pending.get("crop") or (candidate if candidate in CROP_FILES else None)
    sowing_date = (parse_sowing_date(text) or parse_sowing_date(pending.get("sowing_date"))
                   or parse_sowing_date(plan.get("sowing_date")))
    return {"crop": crop, "sowing_date": sowing_date.isoformat() if sowing_date else None}


def resolve_crop_analysis(message, plan, pending=None):
    text = " ".join(str(message or "").casefold().split())
    if any(phrase in text for phrase in (
        "open sky", "open-sky", "without panels", "without solar panels",
        "without pv", "no panels", "no pv", "unshaded", "crop only", "simple only",
    )):
        return "crop_open_sky"
    if any(phrase in text for phrase in (
        "under panels", "under solar", "with panels", "with pv", "with solar",
        "pv and crop", "solar and crop", "agrivoltaic", "agpv",
    )):
        return "solar_and_crop"
    prior = (pending or {}).get("analysis")
    if prior in ("crop_open_sky", "solar_and_crop"):
        return prior
    candidate = plan.get("analysis")
    return candidate if candidate in ("crop_open_sky", "solar_and_crop") else "crop_unspecified"
