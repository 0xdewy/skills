import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "philosopher"
SCRIPT = SKILL / "scripts" / "philosopher.py"
BOOK = """Title: Sayings
*** START OF THE PROJECT GUTENBERG EBOOK SAYINGS ***

INTRODUCTION

The translator thinks the author was wrong about courage.

BOOK I

CHAPTER I

Courage is the mean between cowardice and rashness. {filler}

CHAPTER II

Friendship is one soul dwelling in two bodies.

NOTES

The translator explains friendship at length.

*** END OF THE PROJECT GUTENBERG EBOOK SAYINGS ***
License text about courage.
"""


class PhilosopherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.write_book(BOOK.format(filler="Nobody praises the timid. " * 120))
        self.catalog = self.dir / "catalog.json"
        self.set_catalog("Courage is the mean")

    def write_book(self, text):
        (self.dir / "pg7.txt").write_text(text)

    def set_catalog(self, start):
        self.catalog.write_text(json.dumps({"sage": {"name": "Sage", "dates": "?", "works": [
            {"id": 7, "title": "Sayings", "translator": "A. Nother", "start": start, "end": "NOTES"}]}}))

    def run_cli(self, *args):
        env = {**os.environ, "PHILOSOPHER_CACHE": str(self.dir / "cache"),
               "PHILOSOPHER_MIRROR": (self.dir / "pg{id}.txt").as_uri().replace("%7B", "{").replace("%7D", "}")}
        return subprocess.run([sys.executable, "-B", "-I", str(SCRIPT), "--catalog", str(self.catalog), *args],
                              capture_output=True, text=True, env=env)

    def test_search_returns_only_the_authors_text_with_a_citation(self):
        out = self.run_cli("search", "sage", "What is courage?").stdout
        self.assertIn("Courage is the mean", out)
        self.assertIn("Sayings, BOOK I › CHAPTER I (tr. A. Nother)", out)
        self.assertNotIn("translator thinks", out)
        self.assertNotIn("License", out)
        self.assertEqual(self.run_cli("search", "sage", "translator").stdout.strip(), "no passages found")

    def test_long_paragraphs_split_and_read_gives_neighbours(self):
        out = self.run_cli("read", "sage", "#2", "-c", "1").stdout
        self.assertIn("[#1]", out)
        self.assertIn("[#3]", out)
        self.assertTrue(all(len(p) < 1500 for p in out.split("[#")))
        self.assertIn("CHAPTER II", self.run_cli("search", "sage", "friendship soul").stdout)

    def test_index_rebuilds_when_the_catalog_entry_changes(self):
        self.assertIn("Courage", self.run_cli("search", "sage", "courage").stdout)
        self.set_catalog("Friendship is one soul")
        self.assertEqual(self.run_cli("search", "sage", "courage").stdout.strip(), "no passages found")

    def test_failures_are_reported_not_indexed(self):
        self.assertIn("unknown philosopher", self.run_cli("search", "nobody", "x").stderr)
        self.set_catalog("no such phrase")
        self.assertIn("start marker", self.run_cli("search", "sage", "courage").stderr)
        self.set_catalog("Courage is the mean")
        self.write_book(BOOK.split("*** END")[0])
        self.assertIn("incomplete", self.run_cli("search", "sage", "courage").stderr)
        self.assertFalse((self.dir / "cache" / "sage.db").exists())

    def test_parallel_first_searches_all_succeed(self):
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(4) as pool:
            runs = list(pool.map(lambda _: self.run_cli("search", "sage", "courage"), range(4)))
        self.assertTrue(all("Courage is the mean" in r.stdout for r in runs), [r.stderr for r in runs])
        self.assertEqual([p.name for p in (self.dir / "cache").iterdir()], ["sage.db"])

    def test_alias_names_the_same_philosopher(self):
        entry = json.loads(self.catalog.read_text())
        entry["sage"]["aliases"] = ["wise-one"]
        self.catalog.write_text(json.dumps(entry))
        self.assertIn("Courage is the mean", self.run_cli("search", "Wise-One", "courage").stdout)
        self.assertIn("sage / wise-one:", self.run_cli("list").stdout)

    def test_bundled_catalog_is_well_formed(self):
        catalog = json.loads((SKILL / "catalog.json").read_text())
        ids = [w["id"] for e in catalog.values() for w in e["works"]]
        self.assertEqual(len(ids), len(set(ids)))
        for e in catalog.values():
            self.assertTrue(e["name"] and e["dates"] and e["works"])
            self.assertTrue(all(w["title"] and w["start"] for w in e["works"]))

    @unittest.skipUnless(os.environ.get("PHILOSOPHER_LIVE"), "set PHILOSOPHER_LIVE=1 to download every source")
    def test_every_source_downloads_and_its_markers_match(self):
        env = {**os.environ, "PHILOSOPHER_CACHE": str(self.dir / "live")}
        for who in json.loads((SKILL / "catalog.json").read_text()):
            run = subprocess.run([sys.executable, "-B", "-I", str(SCRIPT), "search", who, "virtue good"],
                                 capture_output=True, text=True, env=env)
            self.assertIn("[#", run.stdout, f"{who}: {run.stderr}")


if __name__ == "__main__":
    unittest.main()
