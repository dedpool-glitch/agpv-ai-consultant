import copy
import importlib
import sys
import types
import unittest
from unittest.mock import Mock, patch


class FollowupRunContextTests(unittest.TestCase):
    def setUp(self):
        client = types.ModuleType("llm.client")
        client.call_llm = Mock(return_value=" Explanation ")
        with patch.dict(sys.modules, {"llm.client": client}):
            self.answerer = importlib.import_module("llm.general_agpv_answerer")
        self.mock = patch.object(self.answerer, "call_llm", return_value=" Explanation ")
        self.call = self.mock.start()
        self.addCleanup(self.mock.stop)

    def test_variant_inputs_and_origins_are_sent_with_matching_output(self):
        run = {
            "input": {"array": {"pitch": 10}},
            "output": {"yearly_yield": 989.61},
            "input_provenance": {"parameters": {"pitch": {
                "source": "llm_recommended", "justification": "Proposed for equipment access",
            }}},
        }
        original = copy.deepcopy(run)
        self.answerer.answer_general_agpv_question(
            "Why this spacing?", "test-key", pvmaps_state={"pitch": 5},
            latest_pvmaps_output={"yearly_yield": 111}, latest_pvmaps_run=run,
        )
        content = self.call.call_args.args[0][1]["content"]
        self.assertIn('"pitch": 10', content)
        self.assertIn("Proposed for equipment access", content)
        self.assertIn("989.61", content)
        self.assertNotIn('"yearly_yield": 111', content)
        self.assertEqual(run, original)

    def test_no_run_and_legacy_run_remain_supported(self):
        self.assertEqual(self.answerer.answer_general_agpv_question("Hi", "test-key"), "Explanation")
        self.answerer.answer_general_agpv_question(
            "Why this spacing?", "test-key",
            latest_pvmaps_run={"input": {"array": {"pitch": 5}}, "output": {}},
        )
        content = self.call.call_args.args[0][1]["content"]
        self.assertIn('"input_provenance": null', content)


if __name__ == "__main__":
    unittest.main()
