import pytest

from models.simple.light import expand_monthly_ground_light


def test_monthly_light_expands_on_calendar_boundaries():
    profiles = [[float(month)] * 101 for month in range(1, 13)]
    result = expand_monthly_ground_light(profiles, 2024)

    assert len(result["dates"]) == len(result["light_mj_m2"]) == 366
    assert result["dates"][59] == "2024-02-29"
    assert result["dates"][60] == "2024-03-01"
    assert result["light_mj_m2"][59][0] == 2.0
    assert result["light_mj_m2"][60][100] == 3.0
    assert len(expand_monthly_ground_light(profiles, 2025)["dates"]) == 365


@pytest.mark.parametrize("profiles", [
    [[1.0] * 101] * 11,
    [[1.0] * 100] + [[1.0] * 101] * 11,
    [[-1.0] * 101] + [[1.0] * 101] * 11,
])
def test_invalid_ground_light_is_rejected(profiles):
    with pytest.raises(ValueError):
        expand_monthly_ground_light(profiles, 2024)
