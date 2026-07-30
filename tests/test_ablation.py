import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("run_ablation", ROOT / "scripts" / "run_ablation.py")
ablation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ablation)


class AblationTests(unittest.TestCase):
    def test_direct_arm_removes_workflow_assertions(self):
        source = {
            "id": 1,
            "prompt": "Do work",
            "expected_output": "workflow output",
            "expectations": ["writes PLAN.md"],
            "outcome_expected": "correct result",
            "outcome_expectations": ["tests pass"],
            "required_files": ["PLAN.md"],
        }
        direct = ablation.arm_eval(source, "direct")
        self.assertEqual(direct["expectations"], ["tests pass"])
        self.assertEqual(direct["expected_output"], "correct result")
        self.assertNotIn("required_files", direct)
        self.assertTrue(direct["prompt"].startswith("Solve this task directly."))
        self.assertEqual(source["expectations"], ["writes PLAN.md"])

    def test_skill_arm_is_forced_but_uses_outcomes(self):
        candidate = ablation.arm_eval({
            "id": 2,
            "prompt": "Find bug",
            "expected_output": "find it",
            "expectations": ["uses a ledger"],
            "outcome_expectations": ["reports the counterexample"],
        }, "skill")
        self.assertEqual(candidate["prompt_type"], "forced")
        self.assertEqual(candidate["expectations"], ["reports the counterexample"])

    def test_codex_usage_does_not_double_count_cached_subsets(self):
        self.assertEqual(ablation.usage_total({
            "usage": {
                "input_tokens": 10, "output_tokens": 3,
                "cached_input_tokens": 8, "reasoning_output_tokens": 2,
            }
        }, "codex"), 13)

    def test_claude_usage_includes_separate_cache_classes(self):
        self.assertEqual(ablation.usage_total({
            "usage": {
                "input_tokens": 10, "output_tokens": 3,
                "cache_creation_input_tokens": 4, "cache_read_input_tokens": 5,
            }
        }, "claude"), 22)


if __name__ == "__main__":
    unittest.main()
