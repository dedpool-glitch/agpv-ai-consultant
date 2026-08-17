def explain_pvmaps_result(output):
    final_simulation_inputs = output["final_inputs"]

    return f"""
Estimated annual solar yield: {output["yearly_yield"]:.1f} {output["yield_unit"]}

This estimate uses:
- Panel type: {final_simulation_inputs["panel_type"]}
- Tracking: {final_simulation_inputs["tracking"]}
- Tilt: {final_simulation_inputs["tilt"]} degrees
- Row spacing: {final_simulation_inputs["pitch"]} meters
- Location: {final_simulation_inputs["lat"]}, {final_simulation_inputs["lon"]}

Highest monthly yield: {max(output["monthly_yield"]):.1f} {output["yield_unit"]}
Lowest monthly yield: {min(output["monthly_yield"]):.1f} {output["yield_unit"]}
"""