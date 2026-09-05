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

INTENT = "Does demos. TRIGGER on: demo work. SKIP other work."
EXPLICIT = "Runs demos. Only use when explicitly requested."


def write_repo(root, *, description=INTENT, hidden=False, prompt_types=("activation", "anti_trigger"), fixtures=None):
    skills = root / "skills"
    skill = skills / "demo"
    (skill / "evals").mkdir(parents=True)
    (skills / "common").mkdir()
    (skills / "common" / "ROUTING.md").write_text("routing\n")
    flag = "disable-model-invocation: true\n" if hidden else ""
    (skill / "SKILL.md").write_text(
        f"---\nname: demo\ndescription: {description}\n{flag}---\n\n# Demo\n"
    )
    cases = []
    for index, kind in enumerate(prompt_types, start=1):
        case = {
            "id": index,
            "prompt": "demo",
            "expected_output": "demo",
            "expectations": ["works"],
            "prompt_type": kind,
        }
        if fixtures is not None and index == 1:
            case["context"] = "fixture repo"
            case["fixture_files"] = fixtures
        cases.append(case)
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

    def assert_fails(self, skills):
        with self.assertRaises(SystemExit):
            self.run_validator(skills)

    def test_valid_materialized_activation_eval(self):
        with tempfile.TemporaryDirectory() as tmp:
            skills = write_repo(Path(tmp), fixtures={"src/app.py": "x = 1\n"})
            result, output = self.run_validator(skills)
            self.assertEqual(result, 0)
            self.assertIn("OK:", output)

    def test_rejects_unsafe_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assert_fails(write_repo(Path(tmp), fixtures={"../escape": "bad"}))

    def test_rejects_unknown_prompt_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assert_fails(write_repo(Path(tmp), prompt_types=("mystery", "anti_trigger")))

    def test_every_skill_requires_anti_trigger(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assert_fails(write_repo(Path(tmp), prompt_types=("activation",)))

    def test_visible_skill_requires_activation_eval(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assert_fails(write_repo(Path(tmp), prompt_types=("forced", "anti_trigger")))

    def test_visible_skill_requires_trigger_skip(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assert_fails(write_repo(Path(tmp), description=EXPLICIT))

    def test_hidden_skill_is_valid_without_activation_eval(self):
        with tempfile.TemporaryDirectory() as tmp:
            skills = write_repo(
                Path(tmp), description=EXPLICIT, hidden=True,
                prompt_types=("forced", "anti_trigger"),
            )
            result, _ = self.run_validator(skills)
            self.assertEqual(result, 0)

    def test_hidden_skill_rejects_trigger_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assert_fails(write_repo(Path(tmp), description=INTENT, hidden=True))

    def test_hidden_skill_must_say_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assert_fails(write_repo(Path(tmp), description="Runs demos.", hidden=True))


if __name__ == "__main__":
    unittest.main()
