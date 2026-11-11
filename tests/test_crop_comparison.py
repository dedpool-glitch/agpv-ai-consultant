"""Crop comparisons use saved outcomes and expose changed conditions."""

import copy

from ui.crop_comparison import (
    combined_solar_rows,
    crop_comparison_cautions,
    crop_comparison_rows,
    crop_runs,
)


def sample_run(yield_value=10.0, with_pv=True):
    return {
        "input": {"lat": 40.4, "lon": -86.9,
                  "array": {"pitch": 5}, "module": {"height": 2},
                  "sim": {"quickSim": True}},
        "output": {"yearly_yield": 900, "yield_unit": "kWh/m"} if with_pv else {},
        "crop_result": {
            "crop": "maize", "sowing_date": "2024-03-15",
            "maturity_date": "2024-09-15",
            "mean_grain_yield_t_ha": yield_value,
        },
    }


def test_crop_comparison_filters_solar_and_invalid_runs():
    valid = sample_run()
    assert crop_runs([{"output": {"yearly_yield": 900}}, valid,
                      sample_run(float("nan")), sample_run(True)]) == [valid]


def test_crop_comparison_uses_unrounded_yield_and_maturity_duration():
    first = sample_run(10.004)
    second = sample_run(10.009)
    rows = crop_comparison_rows([first, second], [0, 1], 0)
    assert rows[1]["Difference (t/ha)"] == 0.01
    assert rows[1]["Days to maturity"] == 184
    assert rows[0]["Difference (%)"] == 0.0
    assert crop_comparison_cautions([first, second], [0, 1]) == []
    zero = sample_run(0)
    assert crop_comparison_rows([zero, second], [0, 1], 0)[1]["Difference (%)"] is None


def test_crop_comparison_flags_changed_conditions_without_mutating_runs():
    first = sample_run()
    second = copy.deepcopy(first)
    second["crop_result"].update(crop="rice", sowing_date="2024-04-01")
    second["input"]["lat"] = 41.0
    second["output"] = {}
    original = copy.deepcopy([first, second])
    warnings = crop_comparison_cautions([first, second], [0, 1])
    assert len(warnings) == 4
    assert any("PV shade" in warning for warning in warnings)
    assert [first, second] == original


def test_crop_comparison_flags_pv_setup_changes():
    first = sample_run()
    second = copy.deepcopy(first)
    second["input"]["array"]["pitch"] = 8
    warnings = crop_comparison_cautions([first, second], [0, 1])
    assert len(warnings) == 1
    assert "PV layouts" in warnings[0]


def test_four_combined_runs_compare_solar_and_crop_against_one_reference():
    runs = [sample_run(8 + index) for index in range(4)]
    for index, run in enumerate(runs):
        run["output"]["yearly_yield"] = 900 + 100 * index
    selected = [0, 1, 2, 3]
    crop_rows = crop_comparison_rows(runs, selected, 1)
    solar_rows = combined_solar_rows(runs, selected, 1)
    assert len(crop_rows) == len(solar_rows) == 4
    assert crop_rows[3]["Difference (t/ha)"] == 2
    assert solar_rows[3]["Difference"] == 200
    assert solar_rows[3]["Difference (%)"] == 20
    assert solar_rows[1]["Unit"] == "kWh/m"


def test_solar_comparison_requires_pv_and_compatible_units():
    runs = [sample_run(), sample_run(with_pv=False)]
    assert combined_solar_rows(runs, [0, 1], 0) is None
    runs[1] = sample_run()
    runs[1]["output"]["yield_unit"] = "kWh"
    assert combined_solar_rows(runs, [0, 1], 0) is None
    runs[1]["output"]["yield_unit"] = "KWH/M"
    assert combined_solar_rows(runs, [0, 1], 0) is not None
