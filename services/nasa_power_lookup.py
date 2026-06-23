from pathlib import Path
import pandas as pd

NASA_CSV_PATH= (
    Path(__file__).resolve().parents[1] / "PV-MAPS-main" / "pvmaps" / "data" / "NASA_Data.csv"
)

def get_climate_summary(lat,lon,csv_path=NASA_CSV_PATH):
    df=pd.read_csv(csv_path)
    df["distance"]=(df["lat"]-lat)**2 + (df["lon"]-lon)**2
    nearest_row=df.loc[df["distance"].idxmin()]

    return {
        "input_location":{
            "lat":lat,
            "lon":lon,
        },
        "nearest_grid_location":{
            "lat":float(nearest_row["lat"]),
            "lon":float(nearest_row["lon"]),
        },
        "elevation_m": float(nearest_row["elevation_m"]),
        "annual": {
            "ghi": float(nearest_row["ghi_annual"]),
            "air_temp_c": float(nearest_row["air_temp_c_annual"]),
            "wind_speed": float(nearest_row["wind_speed_annual"]),
            "relative_humidity_pct": float(nearest_row["relative_humidity_pct_annual"]),
        },
        "monthly_ghi": {
            "jan": float(nearest_row["ghi_jan"]),
            "feb": float(nearest_row["ghi_feb"]),
            "mar": float(nearest_row["ghi_mar"]),
            "apr": float(nearest_row["ghi_apr"]),
            "may": float(nearest_row["ghi_may"]),
            "jun": float(nearest_row["ghi_jun"]),
            "jul": float(nearest_row["ghi_jul"]),
            "aug": float(nearest_row["ghi_aug"]),
            "sep": float(nearest_row["ghi_sep"]),
            "oct": float(nearest_row["ghi_oct"]),
            "nov": float(nearest_row["ghi_nov"]),
            "dec": float(nearest_row["ghi_dec"]),
        },

    }