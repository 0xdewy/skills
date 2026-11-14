import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "attention" / "scripts" / "attention.py"
FIXTURE = json.loads(
    (ROOT / "skills" / "attention" / "evals" / "evals.json").read_text()
)["evals"][0]["fixture_files"]["github.json"]


class AttentionTests(unittest.TestCase):
    def test_groups_only_the_prs_that_need_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            saved = Path(tmp) / "github.json"
            saved.write_text(FIXTURE)
            out = subprocess.run(
                [sys.executable, "-B", str(SCRIPT), "--input", str(saved)],
                capture_output=True, text=True, check=True,
            ).stdout
        self.assertIn("Review requested from you (1)", out)
        self.assertIn("Conflicts with the base branch (1)", out)
        self.assertIn("Checks failing (1)", out)
        self.assertIn("Approved and ready to merge (1)", out)
        self.assertIn("pull/5 [draft]", out)
        self.assertNotIn("pull/1 ", out)
        self.assertIn("4 of your 5 open PRs need you; 1 from others wait for your review.", out)


if __name__ == "__main__":
    unittest.main()
