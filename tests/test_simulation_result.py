import copy
import unittest

from ui.simulation_result import configuration_rows, format_value, run_location


class SimulationResultTests(unittest.TestCase):
    def test_display_rounding_preserves_small_values_and_inputs(self):
        self.assertEqual(format_value(1039.421), "1,039.42")
        self.assertEqual(format_value(40.4191229), "40.42")
        self.assertEqual(format_value(-0.004), "-0.004")
        self.assertEqual(format_value(0), "0")
        self.assertEqual(format_value(float("nan")), "Not available")

    def test_table_uses_actual_input_not_recommendation_value(self):
        run = {
            "input": {"array": {"tilt": 40.4191229}},
            "input_provenance": {"parameters": {"tilt": {
                "value": 25, "source": "llm_recommended", "justification": "Proposed tilt",
            }}},
        }
        original = copy.deepcopy(run)
        row = configuration_rows(run)[0]
        self.assertEqual(row["Value"], "40.42")
        self.assertEqual(row["Origin"], "LLM recommendation")
        self.assertEqual(run, original)

    def test_legacy_and_expert_origins_are_honest(self):
        run = {"input": {"array": {"pitch": 5}}}
        self.assertEqual(configuration_rows(run)[0]["Origin"], "Origin not recorded")
        run["input_provenance"] = {"source": "expert_form"}
        self.assertEqual(configuration_rows(run)[0]["Origin"], "Submitted through expert form")

    def test_module_and_sim_origins_use_group_metadata(self):
        run = {
            "input": {"module": {"height": 4.8}, "sim": {"quickSim": True}},
            "input_provenance": {
                "module": {"source": "stored_panel_specs"},
                "sim": {"source": "application_default"},
            },
        }
        self.assertEqual([r["Origin"] for r in configuration_rows(run)],
                         ["Stored panel specifications", "Application default"])

    def test_location_is_from_run_with_coordinate_fallback(self):
        run = {"input": {"lat": 40.419, "lon": -86.891}}
        self.assertEqual(run_location(run), "Latitude 40.42, longitude -86.89")
        run["location_context"] = {"confirmed_address": "Lafayette, Indiana"}
        self.assertEqual(run_location(run), "Lafayette, Indiana")
        self.assertEqual(run_location({}), "Location not recorded")


if __name__ == "__main__":
    unittest.main()
