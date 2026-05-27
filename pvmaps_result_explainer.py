def explain_pvmaps_result(output):
    assumptions = output["assumptions"]

    return f"""
Estimated annual solar yield: {output["yearly_yield"]:.1f} {output["yield_unit"]}

This estimate uses:
- Panel type: {assumptions["panel_type"]}
- Tracking: {assumptions["tracking"]}
- Tilt: {assumptions["tilt"]} degrees
- Row spacing: {assumptions["pitch"]} meters
- Location: {assumptions["lat"]}, {assumptions["lon"]}

Highest monthly yield: {max(output["monthly_yield"]):.1f} {output["yield_unit"]}
Lowest monthly yield: {min(output["monthly_yield"]):.1f} {output["yield_unit"]}
"""