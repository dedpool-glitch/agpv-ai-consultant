import copy
import importlib
import sys
import types
import unittest
from unittest.mock import patch

from constants import QUESTIONNAIRE_DEFAULTS
from questionnaire.state import initialize_questionnaire_state
from services.parameter_provenance import build_parameter_provenance


class ParameterProvenanceTests(unittest.TestCase):
    def build(self, value=12, source="user_provided", quote="Use 12 meters for pitch", messages=None):
        return build_parameter_provenance(
            {"pitch": value},
            {"parameter_sources": {"pitch": {"source": source, "user_quote": quote}},
             "justifications": {"pitch": "Selected for this run."}},
            {}, messages or [{"role": "user", "content": "Use 12 meters for pitch"}],
        )["pitch"]

    def test_explicit_user_value_has_supporting_quote(self):
        record = self.build()
        self.assertEqual(record["source"], "user_provided")
        self.assertEqual(record["user_quote"], "Use 12 meters for pitch")
        self.assertIn("LLM interpretation", record["attribution"])

    def test_invented_quote_cannot_claim_user_origin(self):
        self.assertEqual(self.build(quote="Use 15 meters")["source"], "llm_recommended")

    def test_assistant_quote_cannot_claim_user_origin(self):
        record = self.build(messages=[{"role": "assistant", "content": "Use 12 meters for pitch"}])
        self.assertEqual(record["source"], "llm_recommended")

    def test_broad_preference_remains_recommendation(self):
        record = self.build(source="llm_recommended", quote=None,
                            messages=[{"role": "user", "content": "Leave room for machinery"}])
        self.assertEqual(record["source"], "llm_recommended")

    def test_matching_default_number_is_not_automatically_a_default(self):
        self.assertEqual(self.build(value=11, source="application_default")["source"], "llm_recommended")

    def test_default_panel_remains_default_even_when_requested(self):
        records = build_parameter_provenance(
            {"panel_model": "default values"}, {}, {},
            [{"role": "user", "content": "Use default values"}],
        )
        self.assertEqual(records["panel_model"]["source"], "application_default")

    def test_unchanged_fields_preserve_original_rationale(self):
        old = self.build(source="llm_recommended")
        baseline = {"pitch": 12, "parameter_provenance": {"pitch": old}}
        record = build_parameter_provenance({"pitch": 12}, {}, baseline, [])["pitch"]
        self.assertEqual(record, old)
        record["justification"] = "changed"
        self.assertNotEqual(record, old)

    def test_legacy_state_is_unknown_and_bad_metadata_does_not_crash(self):
        records = build_parameter_provenance(
            {"pitch": 12, "tilt": 25},
            {"parameter_sources": [], "justifications": None}, {"pitch": 12}, [],
        )
        self.assertEqual(records["pitch"]["source"], "unknown")
        self.assertEqual(records["tilt"]["source"], "llm_recommended")


class ProvenanceFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Avoid importing external API/MATLAB dependencies in these offline tests.
        client = types.ModuleType("llm.client")
        client.call_llm = lambda *args, **kwargs: "Explanation"
        runner = types.ModuleType("models.pvmaps.matlab_runner")
        runner.run_pvmaps = lambda *args, **kwargs: {}
        with patch.dict(sys.modules, {"llm.client": client, "models.pvmaps.matlab_runner": runner}):
            cls.service = importlib.import_module("services.pvmaps_estimate_service")
            cls.explainer = importlib.import_module("llm.output_generator")

    def test_run_and_variant_keep_separate_origins_and_forward_to_explainer(self):
        state = {"chat_messages": [{"role": "user", "content": "Use 12 meters for pitch"}]}
        values = dict(QUESTIONNAIRE_DEFAULTS, pitch=12)
        candidate = {
            "pvmaps_inputs": values,
            "justifications": {field: "Proposed initial setup." for field in values},
            "parameter_sources": {"pitch": {"source": "user_provided", "user_quote": "Use 12 meters for pitch"}},
        }
        location = {"latitude": 40, "longitude": -86}
        with patch.object(self.service, "retrieve_recommendation_context", return_value=[]), \
             patch.object(self.service, "generate_recommended_pvmaps_config", return_value=candidate) as generate, \
             patch.object(self.service, "run_pvmaps", return_value={"yearly_yield": 100}), \
             patch.object(self.service, "explain_output", return_value="Explanation") as explain:
            self.assertTrue(self.service.run_recommended_pvmaps_estimate(
                state, "unused", location, latest_user_message="Use 12 meters for pitch",
            ))
            first_run = copy.deepcopy(state["pvmaps_runs"][0])
            self.assertEqual(explain.call_args.kwargs["user_request"], "Use 12 meters for pitch")
            report_history = explain.call_args.kwargs["conversation_history"]
            self.assertEqual(report_history, [{"role": "user", "content": "Use 12 meters for pitch"}])
            self.assertIsNot(report_history, state["chat_messages"])
            self.assertEqual(first_run["user_request"], "Use 12 meters for pitch")
            origins = explain.call_args.kwargs["input_provenance"]
            self.assertEqual(origins["parameters"]["pitch"]["source"], "user_provided")
            self.assertEqual(origins["module"]["source"], "application_default")
            self.assertEqual(origins["sim"]["source"], "application_default")
            self.assertFalse(any(item.startswith("pitch =") for item in first_run["assumptions"]))

            state["chat_messages"].append({"role": "user", "content": "Try 15 meters for pitch"})
            variant = copy.deepcopy(candidate)
            variant["pvmaps_inputs"]["pitch"] = 15
            variant["parameter_sources"]["pitch"]["user_quote"] = "Try 15 meters for pitch"
            generate.return_value = variant
            self.assertTrue(self.service.run_recommended_pvmaps_estimate(state, "unused", location))
            self.assertEqual(state["pvmaps_runs"][0], first_run)
            self.assertEqual(state["questionnaire_state"]["parameter_provenance"]["pitch"]["value"], 12)
            self.assertEqual(state["pvmaps_runs"][1]["input_provenance"]["parameters"]["pitch"]["value"], 15)

    def test_invalid_inputs_do_not_persist_new_origins(self):
        baseline = initialize_questionnaire_state()
        state = {"questionnaire_state": baseline, "chat_messages": []}
        candidate = {"pvmaps_inputs": dict(QUESTIONNAIRE_DEFAULTS, array_elevation=1)}
        with patch.object(self.service, "retrieve_recommendation_context", return_value=[]), \
             patch.object(self.service, "generate_recommended_pvmaps_config", return_value=candidate), \
             patch.object(self.service, "run_pvmaps") as run:
            self.assertFalse(self.service.run_recommended_pvmaps_estimate(
                state, "unused", {"latitude": 40, "longitude": -86},
            ))
            run.assert_not_called()
            self.assertNotIn("parameter_provenance", baseline)

    def test_explainer_receives_metadata_and_allows_older_callers(self):
        origins = {"parameters": {"pitch": {"source": "user_provided", "value": 12}}}
        with patch.object(self.explainer, "call_llm", return_value="Explanation") as call:
            self.explainer.explain_output({}, "unused", input_provenance=origins)
            content = call.call_args.args[0][1]["content"]
            self.assertIn('"user_provided"', content)
            self.assertIn('"value": 12', content)
            self.assertEqual(self.explainer.explain_output({}, "unused"), "Explanation")

    def test_report_uses_current_request_and_text_history_without_plot_records(self):
        history = [
            {"role": "user", "content": "I need room for my equipment."},
            {"role": "assistant", "content": "We can examine wider spacing."},
            {"role": "assistant", "type": "pvmaps_run", "run_index": 0},
        ]
        original = copy.deepcopy(history)
        with patch.object(self.explainer, "call_llm", return_value="Explanation") as call:
            self.explainer.explain_output(
                {}, "unused", user_profile={"project_goal": "Maximize solar yield"},
                user_request="Actually, try wider spacing for machinery access.",
                conversation_history=history,
            )
            content = call.call_args.args[0][1]["content"]
            self.assertIn("Actually, try wider spacing for machinery access.", content)
            self.assertIn("I need room for my equipment.", content)
            self.assertIn("We can examine wider spacing.", content)
            self.assertNotIn("run_index", content)
            self.assertEqual(history, original)


if __name__ == "__main__":
    unittest.main()
