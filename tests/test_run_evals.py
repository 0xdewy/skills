import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner = load_module("run_evals", ROOT / "scripts" / "run_evals.py")
grader = load_module(
    "llm_judge_grade",
    ROOT / "skills" / "skill-lab" / "scripts" / "llm_judge_grade.py",
)


class FixtureTests(unittest.TestCase):
    def test_materializes_files_and_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = runner.materialize_fixtures(
                {"fixture_files": {"src/app.py": "print('ok')\n", "empty": None}},
                root,
            )
            self.assertEqual((root / "src/app.py").read_text(), "print('ok')\n")
            self.assertTrue((root / "empty").is_dir())
            self.assertRegex(manifest["src/app.py"], r"^[0-9a-f]{64}$")

    def test_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "unsafe fixture path"):
                runner.materialize_fixtures(
                    {"fixture_files": {"../escape": "bad"}}, Path(tmp)
                )


class BackendOutputTests(unittest.TestCase):
    def test_normalizes_claude_json_and_usage(self):
        raw = json.dumps({"result": "answer", "usage": {"input_tokens": 12, "output_tokens": 3}})
        output, usage = runner.normalize_backend_output("claude", raw)
        self.assertEqual(output, "answer")
        self.assertEqual(usage, {"input_tokens": 12, "output_tokens": 3})

    def test_normalizes_codex_jsonl_and_usage(self):
        raw = "\n".join([
            json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "answer"}}),
            json.dumps({"type": "turn.completed", "usage": {"input_tokens": 20, "output_tokens": 4}}),
        ])
        output, usage = runner.normalize_backend_output("codex", raw)
        self.assertEqual(output, "answer")
        self.assertEqual(usage["input_tokens"], 20)

    def test_detects_structured_codex_error(self):
        raw = json.dumps({"type": "error", "message": "model unavailable"})
        failed, detail = runner.backend_reported_error("codex", raw)
        self.assertTrue(failed)
        self.assertEqual(detail, "model unavailable")

    def test_backend_default_omits_model_flag(self):
        self.assertNotIn("--model", runner._claude_cmd("p", "demo", False, None))
        self.assertNotIn("-m", runner._codex_cmd("p", "demo", False, None))

    def test_codex_eval_workspace_is_writable(self):
        command = runner._codex_cmd("p", "demo", False, None)
        self.assertEqual(command[command.index("--sandbox") + 1], "workspace-write")

    def test_forced_prompts_name_exact_skill_file(self):
        for command in (
            runner._claude_cmd("do it", "demo", True, None),
            runner._codex_cmd("do it", "demo", True, None),
        ):
            self.assertIn("skills/demo/SKILL.md", command[-1])
            self.assertTrue(command[-1].endswith("do it"))

    def test_run_eval_uses_fixture_workspace_as_cwd(self):
        with tempfile.TemporaryDirectory() as tmp:
            eval_dir = Path(tmp)
            proc = SimpleNamespace(
                stdout=json.dumps({"result": "done", "usage": {"input_tokens": 2}}),
                stderr="",
                returncode=0,
            )
            with mock.patch.object(runner.subprocess, "run", return_value=proc) as call:
                result = runner.run_eval(
                    "claude",
                    {"id": 1, "prompt": "work", "fixture_files": {"src/a.py": "x = 1\n"}},
                    "demo",
                    eval_dir,
                    "test-model",
                    10,
                )
            self.assertEqual(call.call_args.kwargs["cwd"], str(eval_dir / "workspace"))
            self.assertEqual((eval_dir / "output.txt").read_text(), "done")
            self.assertEqual(result["usage"]["input_tokens"], 2)


class GraderArtifactTests(unittest.TestCase):
    def test_codex_judge_backend_extracts_agent_message(self):
        proc = SimpleNamespace(
            stdout=json.dumps({
                "type": "item.completed",
                "item": {"type": "agent_message", "text": '{"pass":true}'},
            }),
            stderr="",
            returncode=0,
        )
        with mock.patch.object(grader.subprocess, "run", return_value=proc) as call:
            output = grader.call_judge("grade", "codex:gpt-test")
        self.assertEqual(output, '{"pass":true}')
        self.assertIn("gpt-test", call.call_args.args[0])

    def test_unchanged_fixtures_do_not_contaminate_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            results = Path(tmp)
            base = results / "eval-1"
            workspace = base / "workspace"
            workspace.mkdir(parents=True)
            body = "SECRET_FIXTURE_TOKEN\n"
            fixture = workspace / "fixture.py"
            fixture.write_text(body)
            import hashlib
            (base / "run.json").write_text(json.dumps({
                "fixture_manifest": {"fixture.py": hashlib.sha256(body.encode()).hexdigest()}
            }))
            (base / "output.txt").write_text("agent answer\n")
            artifacts = grader.gather_artifacts(results, 1)
            self.assertIn("agent answer", artifacts)
            self.assertNotIn("SECRET_FIXTURE_TOKEN", artifacts)

    def test_required_file_can_live_in_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "workspace").mkdir()
            (base / "workspace" / "report.md").write_text("ok")
            held, failed = grader.deterministic_checks(
                {"required_files": ["report.md"]}, "", base
            )
            self.assertFalse(failed)
            self.assertTrue(held)


if __name__ == "__main__":
    unittest.main()
