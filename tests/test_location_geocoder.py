import pytest
from location_geocoder import geocode_location

def test_empty_location():
    with pytest.raises(ValueError):
        geocode_location("")