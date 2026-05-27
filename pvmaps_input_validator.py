def validate_pvmaps_input(data):
    errors = []

    allowed_cell_tech = ["AL_BSF", "BI_PERC", "SHJ", "PVK_SI_2T", "PVK_SI_4T", "SHJ_NN"]
    if data["module"]["cell_tech"] not in allowed_cell_tech:
        errors.append("Invalid cell technology.")

    if data["module"]["height"] <= 0:
        errors.append("Module height must be positive.")

    if not (0 <= data["module"]["stc_eff"]["direct"] <= 100):
        errors.append("Direct efficiency must be between 0 and 100 percent.")

    if not (0 <= data["module"]["stc_eff"]["diffuse"] <= 100):
        errors.append("Diffuse efficiency must be between 0 and 100 percent.")

    if not (0 <= data["module"]["tcoeff"] <= 0.01):
        errors.append("Temperature coefficient should usually be between 0 and 0.01.")

    if data["array"]["config"] not in ["fixed", "tracking", "GSVBF"]:
        errors.append("Invalid tracking configuration.")

    if not (0 <= data["array"]["tilt"] <= 90):
        errors.append("Tilt must be between 0 and 90 degrees.")

    if not (0 <= data["array"]["azimuth"] <= 360):
        errors.append("Azimuth must be between 0 and 360 degrees.")

    if not (0 <= data["array"]["albedo"] <= 1):
        errors.append("Albedo must be between 0 and 1.")

    if data["array"]["pitch"] <= 0:
        errors.append("Pitch must be positive.")

    if data["array"]["gsHeight"] < 0:
        errors.append("Ground sculpting height cannot be negative.")

    if data["array"]["elevation"] < 0:
        errors.append("Array elevation cannot be negative.")
    
    if not (-90 <= data["lat"] <= 90):
        errors.append("Latitude must be between -90 and 90.")

    if not (-180 <= data["lon"] <= 180):
        errors.append("Longitude must be between -180 and 180.")

    return errors
