import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "skill"
TOOL_PATHS = (
    ".codex/skills",
    ".claude/skills",
    ".config/opencode/skills",
    ".agents/skills",
    ".config/agents/skills",
    ".local/share/hermes/skills",
)


class SkillCliRepairTests(unittest.TestCase):
    def test_repair_creates_current_links_and_prunes_only_managed_orphans(self):
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            home = temp / "home"
            data = temp / "data"
            central = data / "skills"
            source = temp / "source" / "active"
            source.mkdir(parents=True)
            (source / "SKILL.md").write_text("---\nname: active\ndescription: test\n---\n")
            central.mkdir(parents=True)
            (central / "active").symlink_to(source)

            codex = home / ".codex" / "skills"
            codex.mkdir(parents=True)
            (codex / "retired").symlink_to(central / "retired")
            unrelated = codex / "unrelated"
            unrelated.symlink_to(temp / "missing-unmanaged")

            env = os.environ.copy()
            env["HOME"] = str(home)
            env["XDG_DATA_HOME"] = str(data)
            result = subprocess.run(
                [str(CLI), "repair"],
                env=env,
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertIn("Pruning broken managed link", result.stdout)
            self.assertFalse((codex / "retired").is_symlink())
            self.assertTrue(unrelated.is_symlink())
            for relative in TOOL_PATHS:
                link = home / relative / "active"
                self.assertTrue(link.is_symlink())
                self.assertEqual(os.readlink(link), str(central / "active"))


if __name__ == "__main__":
    unittest.main()
