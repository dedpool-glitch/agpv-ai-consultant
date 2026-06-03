from constants import (
    ALLOWED_CELL_TECH,
    ARRAY_CONFIG_OPTIONS,
    PVMAPS_VALIDATION_LIMITS,
    PVMAPS_VALIDATION_MESSAGES,
)


def validate_pvmaps_input(data):
    errors = []

    if data["module"]["cell_tech"] not in ALLOWED_CELL_TECH:
        errors.append(PVMAPS_VALIDATION_MESSAGES["invalid_cell_tech"])

    if data["module"]["height"] <= 0:
        errors.append(PVMAPS_VALIDATION_MESSAGES["module_height_positive"])

    if not (PVMAPS_VALIDATION_LIMITS["efficiency_min"] <= data["module"]["stc_eff"]["direct"] <= PVMAPS_VALIDATION_LIMITS["efficiency_max"]):
        errors.append(PVMAPS_VALIDATION_MESSAGES["direct_efficiency_range"])

    if not (PVMAPS_VALIDATION_LIMITS["efficiency_min"] <= data["module"]["stc_eff"]["diffuse"] <= PVMAPS_VALIDATION_LIMITS["efficiency_max"]):
        errors.append(PVMAPS_VALIDATION_MESSAGES["diffuse_efficiency_range"])

    if not (PVMAPS_VALIDATION_LIMITS["tcoeff_min"] <= data["module"]["tcoeff"] <= PVMAPS_VALIDATION_LIMITS["tcoeff_max"]):
        errors.append(PVMAPS_VALIDATION_MESSAGES["tcoeff_range"])

    if data["array"]["config"] not in ARRAY_CONFIG_OPTIONS:
        errors.append(PVMAPS_VALIDATION_MESSAGES["invalid_array_config"])

    if not (PVMAPS_VALIDATION_LIMITS["tilt_min"] <= data["array"]["tilt"] <= PVMAPS_VALIDATION_LIMITS["tilt_max"]):
        errors.append(PVMAPS_VALIDATION_MESSAGES["tilt_range"])

    if not (PVMAPS_VALIDATION_LIMITS["azimuth_min"] <= data["array"]["azimuth"] <= PVMAPS_VALIDATION_LIMITS["azimuth_max"]):
        errors.append(PVMAPS_VALIDATION_MESSAGES["azimuth_range"])

    if not (PVMAPS_VALIDATION_LIMITS["albedo_min"] <= data["array"]["albedo"] <= PVMAPS_VALIDATION_LIMITS["albedo_max"]):
        errors.append(PVMAPS_VALIDATION_MESSAGES["albedo_range"])

    if data["array"]["pitch"] <= 0:
        errors.append(PVMAPS_VALIDATION_MESSAGES["pitch_positive"])

    if data["array"]["gsHeight"] < 0:
        errors.append(PVMAPS_VALIDATION_MESSAGES["gs_height_nonnegative"])

    if data["array"]["elevation"] < 0:
        errors.append(PVMAPS_VALIDATION_MESSAGES["array_elevation_nonnegative"])
    
    if not (PVMAPS_VALIDATION_LIMITS["lat_min"] <= data["lat"] <= PVMAPS_VALIDATION_LIMITS["lat_max"]):
        errors.append(PVMAPS_VALIDATION_MESSAGES["lat_range"])

    if not (PVMAPS_VALIDATION_LIMITS["lon_min"] <= data["lon"] <= PVMAPS_VALIDATION_LIMITS["lon_max"]):
        errors.append(PVMAPS_VALIDATION_MESSAGES["lon_range"])

    return errors
