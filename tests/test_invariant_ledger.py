import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/invariant-miner/scripts/validate_ledger.py"
SPEC = importlib.util.spec_from_file_location("validate_ledger", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def valid_ledger():
    return {
        "schema_version": 1,
        "target": "src/tags.py:canonical_tags",
        "seed": "invariant-miner-1",
        "budget": {"case_limit": 100, "time_limit_seconds": 10},
        "invariants": [
            {
                "id": "INV-001",
                "statement": "For all tag lists, canonicalization is idempotent.",
                "scope": "src/tags.py:canonical_tags",
                "status": "supported",
                "basis": "derived",
                "confidence": "high",
                "evidence": [
                    {
                        "source": "CONTRACT.md:1",
                        "claim": "The output is canonical.",
                    }
                ],
                "falsification": {
                    "method": "metamorphic",
                    "command": "python -m unittest tests.test_tags",
                    "result": "pass",
                    "receipt": {
                        "exit_code": 0,
                        "cases_executed": 100,
                        "duration_ms": 50,
                        "output_sha256": "a" * 64,
                    },
                },
                "durable_test": True,
                "test_path": "tests/test_tags.py",
            }
        ],
    }


class ValidateInvariantLedgerTests(unittest.TestCase):
    def test_valid_ledger(self):
        self.assertEqual(MODULE.validate(valid_ledger()), [])

    def test_supported_requires_passing_falsification(self):
        ledger = valid_ledger()
        ledger["invariants"][0]["falsification"]["result"] = "fail"
        errors = MODULE.validate(ledger)
        self.assertTrue(any("supported invariant" in error for error in errors))

    def test_falsified_requires_counterexample(self):
        ledger = valid_ledger()
        record = ledger["invariants"][0]
        record["status"] = "falsified"
        record["falsification"]["result"] = "fail"
        record["falsification"]["receipt"].update(
            {"exit_code": 1, "reproduction_command": "python -m unittest failing"}
        )
        errors = MODULE.validate(ledger)
        self.assertTrue(any("counterexample" in error for error in errors))

    def test_falsified_rejects_null_counterexample(self):
        ledger = valid_ledger()
        record = ledger["invariants"][0]
        record["status"] = "falsified"
        record["falsification"]["result"] = "fail"
        record["falsification"]["receipt"].update(
            {"exit_code": 1, "reproduction_command": "python -m unittest failing"}
        )
        record["counterexample"] = None
        errors = MODULE.validate(ledger)
        self.assertTrue(any("concrete counterexample" in error for error in errors))

    def test_observed_durable_test_requires_authorization(self):
        ledger = valid_ledger()
        ledger["invariants"][0]["basis"] = "observed"
        errors = MODULE.validate(ledger)
        self.assertTrue(any("policy_authorization" in error for error in errors))

    def test_durable_test_must_be_boolean(self):
        ledger = valid_ledger()
        ledger["invariants"][0]["durable_test"] = "yes"
        errors = MODULE.validate(ledger)
        self.assertTrue(any("must be a boolean" in error for error in errors))

    def test_durable_test_requires_test_path(self):
        ledger = valid_ledger()
        del ledger["invariants"][0]["test_path"]
        errors = MODULE.validate(ledger)
        self.assertTrue(any("test_path" in error for error in errors))

    def test_executed_result_requires_receipt(self):
        ledger = valid_ledger()
        del ledger["invariants"][0]["falsification"]["receipt"]
        errors = MODULE.validate(ledger)
        self.assertTrue(any("receipt is required" in error for error in errors))

    def test_receipt_requires_valid_digest_and_exit_code(self):
        ledger = valid_ledger()
        receipt = ledger["invariants"][0]["falsification"]["receipt"]
        receipt["output_sha256"] = "not-a-digest"
        receipt["exit_code"] = 2
        errors = MODULE.validate(ledger)
        self.assertTrue(any("64 hex chars" in error for error in errors))
        self.assertTrue(any("exit_code=0" in error for error in errors))

    def test_evidence_requires_provenance(self):
        ledger = valid_ledger()
        ledger["invariants"][0]["evidence"][0]["source"] = "CONTRACT.md"
        errors = MODULE.validate(ledger)
        self.assertTrue(any("path:line" in error for error in errors))

    def test_rejected_record_can_skip_falsification(self):
        ledger = valid_ledger()
        record = ledger["invariants"][0]
        record.update(
            {
                "status": "rejected",
                "rejection_reason": "The generator guarantees the property.",
                "falsification": None,
                "durable_test": False,
            }
        )
        self.assertEqual(MODULE.validate(ledger), [])

    def test_cli_rejects_duplicate_ids(self):
        ledger = valid_ledger()
        ledger["invariants"].append(dict(ledger["invariants"][0]))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "INVARIANTS.json"
            path.write_text(json.dumps(ledger))
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path)],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("duplicates", result.stderr)

    def test_printed_template_is_valid(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--print-template"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(MODULE.validate(json.loads(result.stdout)), [])


if __name__ == "__main__":
    unittest.main()
