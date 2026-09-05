import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_skills", ROOT / "scripts" / "validate_skills.py"
)
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


def write_repo(
    root, *, mode="namespace", prompt_type="activation", fixtures=None,
    invocation_policy="manual"
):
    skills = root / "skills"
    skill = skills / "demo"
    (skill / "evals").mkdir(parents=True)
    (skills / "common").mkdir()
    (skills / "common" / "ROUTING.md").write_text("routing\n")
    description = {
        "namespace": "Demo protocol developer reference.",
        "intent": "Does demos. TRIGGER on: demo work. SKIP other work.",
        "explicit": "Runs demos. Only use when explicitly requested.",
    }[mode]
    manual = "disable-model-invocation: true\n" if mode == "explicit" and invocation_policy == "manual" else ""
    composable = "  composable: true\n" if mode == "explicit" and invocation_policy == "composable" else ""
    (skill / "SKILL.md").write_text(
        f"---\nname: demo\ndescription: {description}\n{manual}metadata:\n"
        f"  activation: {mode}\n{composable}---\n\n# Demo\n"
    )
    case = {
        "id": 1,
        "prompt": "demo",
        "expected_output": "demo",
        "expectations": ["works"],
        "prompt_type": prompt_type,
    }
    if fixtures is not None:
        case["context"] = "fixture repo"
        case["fixture_files"] = fixtures
    cases = [case]
    if mode != "namespace" and prompt_type != "anti_trigger":
        cases.append({
            "id": 2,
            "prompt": "unrelated",
            "expected_output": "direct",
            "expectations": ["does not route"],
            "prompt_type": "anti_trigger",
        })
    (skill / "evals" / "evals.json").write_text(json.dumps(cases))
    return skills


class ValidatorTests(unittest.TestCase):
    def run_validator(self, skills):
        output = io.StringIO()
        with mock.patch.object(validator, "ROOT", skills.parent), \
             mock.patch.object(validator, "SKILLS", skills), \
             redirect_stdout(output):
            result = validator.main()
        return result, output.getvalue()

    def test_valid_materialized_activation_eval(self):
        with tempfile.TemporaryDirectory() as tmp:
            skills = write_repo(Path(tmp), fixtures={"src/app.py": "x = 1\n"})
            result, output = self.run_validator(skills)
            self.assertEqual(result, 0)
            self.assertIn("OK:", output)

    def test_rejects_unsafe_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            skills = write_repo(Path(tmp), fixtures={"../escape": "bad"})
            with self.assertRaises(SystemExit):
                self.run_validator(skills)

    def test_rejects_unknown_prompt_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            skills = write_repo(Path(tmp), prompt_type="mystery")
            with self.assertRaises(SystemExit):
                self.run_validator(skills)

    def test_non_namespace_requires_anti_trigger(self):
        with tempfile.TemporaryDirectory() as tmp:
            skills = write_repo(Path(tmp), mode="intent")
            eval_path = skills / "demo" / "evals" / "evals.json"
            eval_path.write_text(json.dumps([json.loads(eval_path.read_text())[0]]))
            with self.assertRaises(SystemExit):
                self.run_validator(skills)

    def test_explicit_requires_invocation_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            skills = write_repo(
                Path(tmp), mode="explicit", invocation_policy="missing"
            )
            with self.assertRaises(SystemExit):
                self.run_validator(skills)

    def test_composable_explicit_policy_is_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            skills = write_repo(
                Path(tmp), mode="explicit", invocation_policy="composable"
            )
            result, _ = self.run_validator(skills)
            self.assertEqual(result, 0)

    def test_human_only_explicit_is_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            skills = write_repo(Path(tmp), mode="explicit", invocation_policy="manual")
            result, _ = self.run_validator(skills)
            self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
