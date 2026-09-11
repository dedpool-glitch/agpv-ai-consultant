import copy
import unittest

from ui.simulation_comparison import changed_inputs, comparison_cautions, run_name, yield_difference


def run(yield_value=100, pitch=8, unit="kWh/m"):
    return {"input": {"lat": 40, "lon": -86, "module": {"height": 4.8},
                      "sim": {"quickSim": True}, "array": {"config": "fixed", "pitch": pitch}},
            "output": {"yearly_yield": yield_value, "yield_unit": unit}}


class ComparisonTests(unittest.TestCase):
    def test_reference_arithmetic_and_zero(self):
        self.assertEqual(yield_difference(run(125), run()), (25, 25))
        self.assertEqual(yield_difference(run(75), run()), (-25, -25))
        self.assertEqual(yield_difference(run(25), run(0)), (25, None))

    def test_incompatible_or_invalid_values(self):
        for candidate in (run(unit="kWh"), run(unit=None), run(float("nan")), run(None)):
            self.assertEqual(yield_difference(candidate, run()), (None, None))

    def test_four_runs_and_changed_parameters_do_not_mutate_records(self):
        runs = [run(pitch=pitch) for pitch in (8, 10, 12, 14, 16)]
        before = copy.deepcopy(runs)
        changes = changed_inputs(runs, [0, 2, 3, 4])
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]["Run 3"], "12")
        self.assertEqual(changes[0]["Run 5"], "16")
        self.assertTrue(run_name(runs[2], 2).startswith("Run 3 |"))
        self.assertEqual(runs, before)

    def test_location_module_and_settings_cautions(self):
        runs = [run(), run()]
        self.assertEqual(comparison_cautions(runs, [0, 1]), [])
        runs[1]["input"]["lat"] = 42
        runs[1]["input"]["module"]["height"] = 5
        runs[1]["input"]["sim"]["quickSim"] = False
        self.assertEqual(len(comparison_cautions(runs, [0, 1])), 3)

    def test_missing_input_is_visible(self):
        runs = [run(), {"output": {}}]
        self.assertTrue(comparison_cautions(runs, [0, 1]))
        self.assertTrue(any(row["Run 2"] == "Not available" for row in changed_inputs(runs, [0, 1])))


if __name__ == "__main__":
    unittest.main()
