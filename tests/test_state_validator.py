import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
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


class ProjectStateTests(unittest.TestCase):
    def test_template_is_valid(self):
        self.assertEqual(MODULE.validate_project(copy.deepcopy(MODULE.PM_TEMPLATE)), [])

    def test_ready_requires_accepted_dependencies(self):
        state = copy.deepcopy(MODULE.PM_TEMPLATE)
        state["slices"][0]["state"] = "review"
        errors = MODULE.validate_project(state)
        self.assertTrue(any("before dependencies" in error for error in errors))

    def test_cycle_is_rejected(self):
        state = copy.deepcopy(MODULE.PM_TEMPLATE)
        state["slices"][0]["dependencies"] = ["cli"]
        errors = MODULE.validate_project(state)
        self.assertTrue(any("cycle" in error for error in errors))

    def test_pass_requires_all_slices(self):
        state = copy.deepcopy(MODULE.PM_TEMPLATE)
        state.update({"state": "passed", "next_action": None})
        errors = MODULE.validate_project(state)
        self.assertTrue(any("every slice" in error for error in errors))

    def test_root_checks_accepted_artifact(self):
        state = copy.deepcopy(MODULE.PM_TEMPLATE)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            errors = MODULE.validate_project(state, root)
            self.assertTrue(any("does not exist" in error for error in errors))
            artifact = root / state["slices"][0]["artifact"]
            artifact.parent.mkdir(parents=True)
            artifact.write_text("DONE")
            self.assertEqual(MODULE.validate_project(state, root), [])

    def test_cli_prints_valid_templates(self):
        for kind, validator in (
            ("goal", MODULE.validate_goal),
            ("project-manager", MODULE.validate_project),
        ):
            result = subprocess.run(
                [sys.executable, str(SCRIPT), kind, "--print-template"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(validator(json.loads(result.stdout)), [])


if __name__ == "__main__":
    unittest.main()
