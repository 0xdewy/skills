import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "pr-smellz" / "scripts" / "changed_scope.py"


def run(cwd, *args):
    return subprocess.run(
        list(args), cwd=cwd, capture_output=True, text=True, check=True
    ).stdout


class ChangedScopeTests(unittest.TestCase):
    def test_reports_merge_base_stats_and_added_ranges(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run(repo, "git", "init", "-b", "main")
            run(repo, "git", "config", "user.email", "test@example.com")
            run(repo, "git", "config", "user.name", "Test")
            source = repo / "app.py"
            source.write_text("def value():\n    return 1\n")
            run(repo, "git", "add", "app.py")
            run(repo, "git", "commit", "-m", "base")
            run(repo, "git", "switch", "-c", "feature")
            source.write_text("def value():\n    result = 2\n    return result\n")
            (repo / "test_app.py").write_text("from app import value\nassert value() == 2\n")
            run(repo, "git", "add", ".")
            run(repo, "git", "commit", "-m", "change")

            output = run(repo, "python3", str(SCRIPT), "--base", "main")
            scope = json.loads(output)
            self.assertEqual(scope["files_changed"], 2)
            self.assertGreaterEqual(scope["additions"], 3)
            app = next(item for item in scope["files"] if item["path"] == "app.py")
            self.assertTrue(app["hunks"])
            self.assertGreaterEqual(app["hunks"][0]["new_count"], 1)
            self.assertIn("old_start", app["hunks"][0])

    def test_requires_unambiguous_base(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run(repo, "git", "init")
            result = subprocess.run(
                ["python3", str(SCRIPT)], cwd=repo, capture_output=True, text=True
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("pass --base", result.stderr)

    def test_modified_rename_keeps_new_path_stats(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run(repo, "git", "init", "-b", "main")
            run(repo, "git", "config", "user.email", "test@example.com")
            run(repo, "git", "config", "user.name", "Test")
            old = repo / "old.py"
            old.write_text("".join(f"line {i}\n" for i in range(20)))
            run(repo, "git", "add", ".")
            run(repo, "git", "commit", "-m", "base")
            run(repo, "git", "switch", "-c", "feature")
            run(repo, "git", "mv", "old.py", "new.py")
            new = repo / "new.py"
            new.write_text(new.read_text().replace("line 10\n", "changed\n"))
            run(repo, "git", "commit", "-am", "rename")

            scope = json.loads(run(repo, "python3", str(SCRIPT), "--base", "main"))
            self.assertEqual(scope["files"][0]["path"], "new.py")
            self.assertEqual(scope["files"][0]["old_path"], "old.py")
            self.assertEqual(scope["files"][0]["additions"], 1)
            self.assertEqual(scope["files"][0]["deletions"], 1)

    def test_removed_lines_keep_old_ranges(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run(repo, "git", "init", "-b", "main")
            run(repo, "git", "config", "user.email", "test@example.com")
            run(repo, "git", "config", "user.name", "Test")
            (repo / "auth.py").write_text("def handle(user):\n    authorize(user)\n    return work(user)\n")
            (repo / "keep.py").write_text("value = 1\n")
            (repo / "delete.py").write_text("obsolete = True\n")
            run(repo, "git", "add", ".")
            run(repo, "git", "commit", "-m", "base")
            run(repo, "git", "switch", "-c", "feature")
            (repo / "auth.py").write_text("def handle(user):\n    return work(user)\n")
            (repo / "keep.py").write_text("value = 2\n")
            (repo / "delete.py").unlink()
            run(repo, "git", "add", "-A")
            run(repo, "git", "commit", "-m", "change")

            scope = json.loads(run(repo, "python3", str(SCRIPT), "--base", "main"))
            auth = next(item for item in scope["files"] if item["path"] == "auth.py")
            deleted = next(item for item in scope["files"] if item["path"] == "delete.py")
            kept = next(item for item in scope["files"] if item["path"] == "keep.py")
            self.assertEqual(auth["hunks"], [{
                "old_start": 2,
                "old_count": 1,
                "new_start": 1,
                "new_count": 0,
            }])
            self.assertEqual(deleted["status"][0], "D")
            self.assertEqual(deleted["hunks"], [{
                "old_start": 1,
                "old_count": 1,
                "new_start": 0,
                "new_count": 0,
            }])
            self.assertEqual(kept["hunks"][0]["new_count"], 1)
            self.assertEqual(kept["hunks"][0]["old_count"], 1)

    def test_quoted_and_spaced_deletions_stay_on_their_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run(repo, "git", "init", "-b", "main")
            run(repo, "git", "config", "user.email", "test@example.com")
            run(repo, "git", "config", "user.name", "Test")
            for name in ("a.py", "β.py", "a file.py"):
                (repo / name).write_text(f"{name}\n")
            run(repo, "git", "add", ".")
            run(repo, "git", "commit", "-m", "base")
            run(repo, "git", "switch", "-c", "feature")
            for name in ("a.py", "β.py", "a file.py"):
                (repo / name).unlink()
            run(repo, "git", "add", "-A")
            run(repo, "git", "commit", "-m", "change")

            scope = json.loads(run(repo, "python3", str(SCRIPT), "--base", "main"))
            by_path = {item["path"]: item for item in scope["files"]}
            self.assertEqual(set(by_path), {"a.py", "β.py", "a file.py"})
            for item in by_path.values():
                self.assertEqual(item["hunks"], [{
                    "old_start": 1,
                    "old_count": 1,
                    "new_start": 0,
                    "new_count": 0,
                }])


if __name__ == "__main__":
    unittest.main()
