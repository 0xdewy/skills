import datetime as dt
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "check_domain_freshness", ROOT / "scripts" / "check_domain_freshness.py"
)
freshness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(freshness)


class FreshnessTests(unittest.TestCase):
    def test_age_rejects_stale_and_future_dates(self):
        today = dt.date(2026, 7, 10)
        self.assertIsNone(freshness.age_problem("2026-06-01", today, 90))
        self.assertIn("stale", freshness.age_problem("2026-01-01", today, 90))
        self.assertIn("future", freshness.age_problem("2026-07-11", today, 90))

    def test_marked_docs_require_source_and_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc = root / "ref.md"
            doc.write_text("# Ref\nLast verified: 2026-07-10\n")
            issues = freshness.check_marked_docs(
                [doc], "demo", dt.date(2026, 7, 10), 90, root
            )
            self.assertEqual(len(issues), 1)
            self.assertIn("source", issues[0])

    def test_hyperliquid_checks_digest_and_mirror(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            refs = root / "skills" / "hyperliquid" / "references"
            docs = refs / "docs"
            docs.mkdir(parents=True)
            llms = b"index\n"
            (refs / "llms.txt").write_bytes(llms)
            url = "https://example.test/page.md"
            (docs / "page.md").write_text(f"---\nsource_url: {url}\nscrape_status: ok\n---\n")
            manifest = {
                "generated_at": "2026-07-10T00:00:00Z",
                "llms_sha256": hashlib.sha256(llms).hexdigest(),
                "page_count": 1,
                "ok_count": 1,
                "error_count": 0,
                "pages": [{"url": url, "local_path": "references/docs/page.md", "status": "ok"}],
            }
            (refs / "source-map.json").write_text(json.dumps(manifest))
            self.assertEqual(
                freshness.check_hyperliquid(root, dt.date(2026, 7, 10), 90), []
            )
            manifest["llms_sha256"] = "0" * 64
            (refs / "source-map.json").write_text(json.dumps(manifest))
            self.assertTrue(any("digest" in issue for issue in freshness.check_hyperliquid(
                root, dt.date(2026, 7, 10), 90
            )))


if __name__ == "__main__":
    unittest.main()
