"""Load and query the PVMAPS model descriptor."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


PVMAPS_DESCRIPTOR_PATH = Path(__file__).with_name("pvmaps.json")


@lru_cache(maxsize=1)
def load_pvmaps_descriptor() -> dict:
    """Load the model-local PVMAPS descriptor once per Python process."""
    with PVMAPS_DESCRIPTOR_PATH.open("r", encoding="utf-8") as descriptor_file:
        descriptor = json.load(descriptor_file)

    inputs = descriptor.get("inputs")
    if not isinstance(inputs, list):
        raise ValueError("PVMAPS descriptor must contain an 'inputs' list.")

    input_ids = [field.get("id") for field in inputs]
    if any(not field_id for field_id in input_ids):
        raise ValueError("Every PVMAPS input descriptor must have an id.")
    if len(input_ids) != len(set(input_ids)):
        raise ValueError("PVMAPS input descriptor ids must be unique.")

    return descriptor


def get_pvmaps_input_descriptor(field_id: str) -> dict:
    """Return one input definition by its model field id."""
    for field in load_pvmaps_descriptor()["inputs"]:
        if field["id"] == field_id:
            return field
    raise KeyError(f"Unknown PVMAPS input field: {field_id}")


def get_pvmaps_input_descriptors() -> list[dict]:
    """Return every model input definition, preserving JSON order."""
    return load_pvmaps_descriptor()["inputs"]


def get_expert_form_descriptors() -> list[dict]:
    """Return every PVMAPS input because expert mode exposes the full model."""
    return get_pvmaps_input_descriptors()


def build_pvmaps_input_from_descriptor_values(field_values: dict) -> dict:
    """Convert a complete dotted-id value map into the nested model input."""
    expected_ids = {field["id"] for field in get_pvmaps_input_descriptors()}
    received_ids = set(field_values)
    if received_ids != expected_ids:
        missing = sorted(expected_ids - received_ids)
        unexpected = sorted(received_ids - expected_ids)
        raise ValueError(
            f"Descriptor input ids do not match; missing={missing}, "
            f"unexpected={unexpected}."
        )

    pvmaps_input = {}
    for field_id, value in field_values.items():
        path = field_id.split(".")
        target = pvmaps_input
        for path_part in path[:-1]:
            target = target.setdefault(path_part, {})
        target[path[-1]] = value
    return pvmaps_input


def _get_nested_value(data: dict, field_id: str):
    value = data
    for path_part in field_id.split("."):
        value = value[path_part]
    return value


def validate_pvmaps_descriptor_input(pvmaps_input: dict) -> list[str]:
    """Validate a nested input using constraints declared in pvmaps.json."""
    errors = []

    for field in get_pvmaps_input_descriptors():
        field_id = field["id"]
        try:
            value = _get_nested_value(pvmaps_input, field_id)
        except (KeyError, TypeError):
            if field.get("required"):
                errors.append(f"{field['name']} is required.")
            continue

        constraints = field.get("constraints") or {}
        allowed_values = constraints.get("allowed_values")
        if allowed_values is not None and value not in allowed_values:
            errors.append(
                f"{field['name']} must be one of: "
                f"{', '.join(map(str, allowed_values))}."
            )

        minimum = constraints.get("min")
        if minimum is not None:
            if constraints.get("exclusive_min") and value <= minimum:
                errors.append(f"{field['name']} must be greater than {minimum}.")
            elif not constraints.get("exclusive_min") and value < minimum:
                errors.append(f"{field['name']} must be at least {minimum}.")

        maximum = constraints.get("max")
        if maximum is not None and value > maximum:
            errors.append(f"{field['name']} must be at most {maximum}.")

    for rule in load_pvmaps_descriptor().get("validation_rules", []):
        if rule["type"] == "greater_than_scaled_field":
            value = _get_nested_value(pvmaps_input, rule["field"])
            comparison = _get_nested_value(pvmaps_input, rule["other_field"])
            if value <= comparison * rule["factor"]:
                errors.append(rule["message"])
        else:
            raise ValueError(f"Unsupported PVMAPS validation rule: {rule['type']}")

    return errors
