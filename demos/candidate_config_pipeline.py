import os
from dotenv import load_dotenv

from services.location_geocoder import geocode_location
from services.nasa_power_lookup import get_climate_summary
from services.candidate_report import append_candidate_to_csv
from llm.candidate_config_generator import generate_candidate_config
from llm.candidate_config_validator import validate_candidate_config
from questionnaire.to_pvmaps import build_pvmaps_input_from_questionnaire
from pvmaps.input_validator import validate_pvmaps_input


load_dotenv()
api_key = os.getenv("PURDUE_GENAI_KEY")


location_text = input("Enter a location: ")

coordinates = geocode_location(location_text)

lat = coordinates["latitude"]
lon = coordinates["longitude"]
address = coordinates["address"]

print("\nMatched location:")
print(address)
print(f"Latitude: {lat}")
print(f"Longitude: {lon}")

climate_summary = get_climate_summary(lat, lon)

print("\nNASA climate summary:")
print(climate_summary)

candidate = generate_candidate_config(lat, lon, climate_summary, api_key)

print("\nLLM candidate:")
print(candidate)

parsed_inputs, errors = validate_candidate_config(candidate)

if errors:
    print("\nCandidate validation errors:")
    for error in errors:
        print("-", error)
else:
    state = {
        **parsed_inputs,
        "assumptions": [],
    }

    pvmaps_input = build_pvmaps_input_from_questionnaire(state, lat, lon)
    pvmaps_errors = validate_pvmaps_input(pvmaps_input)

    if pvmaps_errors:
        print("\nPVMAPS validation errors:")
        for error in pvmaps_errors:
            print("-", error)
    else:
        print("\nValidated PVMAPS input:")
        print(pvmaps_input)

        append_candidate_to_csv(
            candidate=candidate,
            location=address,
            lat=lat,
            lon=lon,
            output_path="candidate_history.csv",
        )

        print("\nCandidate saved to candidate_history.csv")
