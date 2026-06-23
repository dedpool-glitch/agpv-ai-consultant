from datetime import datetime
from pathlib import Path
import pandas as pd


def append_candidate_to_csv(candidate, location, lat, lon, output_path):
    output_path = Path(output_path)
    run_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    inputs = candidate.get("pvmaps_inputs", {})
    justifications = candidate.get("justifications", {})

    rows = []

    for field, value in inputs.items():
        rows.append({
            "run_id": run_id,
            "location": location,
            "latitude": lat,
            "longitude": lon,
            "candidate_name": candidate.get("candidate_name", ""),
            "field": field,
            "selected_value": value,
            "justification": justifications.get(field, ""),
        })

    dataframe = pd.DataFrame(rows)

    dataframe.to_csv(
        output_path,
        mode="a",
        header=not output_path.exists(),
        index=False,
    )