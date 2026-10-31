import copy
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/common/scripts/validate_state.py"
SPEC = importlib.util.spec_from_file_location("validate_state", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class GoalStateTests(unittest.TestCase):
    def test_template_is_valid(self):
        self.assertEqual(MODULE.validate_goal(copy.deepcopy(MODULE.GOAL_TEMPLATE)), [])

    def test_pass_requires_all_criteria(self):
        state = copy.deepcopy(MODULE.GOAL_TEMPLATE)
        state.update({"state": "passed", "next_action": None})
        errors = MODULE.validate_goal(state)
        self.assertTrue(any("every criterion" in error for error in errors))

    def test_iteration_cannot_exceed_cap(self):
        state = copy.deepcopy(MODULE.GOAL_TEMPLATE)
        state["current_iteration"] = state["cap"] + 1
        errors = MODULE.validate_goal(state)
        self.assertTrue(any("exceed cap" in error for error in errors))

    def test_duplicate_criterion_is_rejected(self):
        state = copy.deepcopy(MODULE.GOAL_TEMPLATE)
        state["criteria"].append(copy.deepcopy(state["criteria"][0]))
        errors = MODULE.validate_goal(state)
        self.assertTrue(any("duplicates" in error for error in errors))


    def test_quick_mode_is_valid(self):
        state = copy.deepcopy(MODULE.GOAL_TEMPLATE)
        state["mode"] = "quick"
        self.assertEqual(MODULE.validate_goal(state), [])

    def test_cli_prints_valid_template(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "goal", "--print-template"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(MODULE.validate_goal(json.loads(result.stdout)), [])


if __name__ == "__main__":
    unittest.main()
