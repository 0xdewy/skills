import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/spec-reconciler/scripts/reconcile_claims.py"
SPEC = importlib.util.spec_from_file_location("reconcile_claims", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def valid_ledger():
    return copy.deepcopy(MODULE.TEMPLATE)


class SpecReconcilerTests(unittest.TestCase):
    def test_template_is_valid_and_consistent(self):
        ledger = valid_ledger()
        self.assertEqual(MODULE.validate(ledger), [])
        result = MODULE.reconcile(ledger)
        self.assertEqual(result["summary"]["conflicts"], 0)
        self.assertEqual(result["summary"]["consistent_keys"], 1)

    def test_stale_derived_is_fixable(self):
        ledger = valid_ledger()
        ledger["claims"][1]["value"] = "integer"
        conflict = MODULE.reconcile(ledger)["conflicts"][0]
        self.assertEqual(conflict["classification"], "stale-derived")
        self.assertTrue(conflict["fixable"])
        self.assertEqual(conflict["target_surface_ids"], ["client"])
        self.assertEqual(conflict["target_actions"][0]["strategy"], "regenerate")
        self.assertEqual(
            conflict["target_actions"][0]["update_command"],
            "python scripts/generate_client.py",
        )

    def test_missing_policy_is_ambiguous(self):
        ledger = valid_ledger()
        ledger["authority_policy"] = {
            "source": None,
            "description": "No authority policy was found.",
        }
        for surface in ledger["surfaces"]:
            surface["authority_rank"] = None
        ledger["claims"][1]["value"] = "integer"
        self.assertEqual(MODULE.validate(ledger), [])
        conflict = MODULE.reconcile(ledger)["conflicts"][0]
        self.assertEqual(conflict["classification"], "ambiguous-authority")
        self.assertFalse(conflict["fixable"])

    def test_equal_rank_disagreement_is_authority_conflict(self):
        ledger = valid_ledger()
        ledger["surfaces"].append(
            {
                "id": "schema-two",
                "kind": "json-schema",
                "path": "schema.json",
                "role": "primary",
                "authority_rank": 1,
                "edit_strategy": "report-only",
            }
        )
        claim = copy.deepcopy(ledger["claims"][0])
        claim.update(
            {
                "id": "CLM-003",
                "surface": "schema-two",
                "location": "schema.json:3",
                "value": "integer",
            }
        )
        ledger["claims"].append(claim)
        self.assertEqual(MODULE.validate(ledger), [])
        conflict = MODULE.reconcile(ledger)["conflicts"][0]
        self.assertEqual(conflict["classification"], "authority-conflict")
        self.assertFalse(conflict["fixable"])

    def test_observed_disagreement_is_not_fixable(self):
        ledger = valid_ledger()
        client = ledger["surfaces"][1]
        client.update({"role": "observed", "edit_strategy": "report-only"})
        client.pop("update_command")
        ledger["claims"][1]["value"] = "integer"
        self.assertEqual(MODULE.validate(ledger), [])
        conflict = MODULE.reconcile(ledger)["conflicts"][0]
        self.assertEqual(conflict["classification"], "cross-surface-conflict")
        self.assertFalse(conflict["fixable"])

    def test_expected_derived_omission_is_fixable(self):
        ledger = valid_ledger()
        ledger["claims"] = ledger["claims"][:1]
        conflict = MODULE.reconcile(ledger)["conflicts"][0]
        self.assertEqual(conflict["classification"], "omission")
        self.assertTrue(conflict["fixable"])
        self.assertEqual(conflict["authoritative_value"], "string")

    def test_omission_without_policy_is_not_fixable(self):
        ledger = valid_ledger()
        ledger["authority_policy"]["source"] = None
        for surface in ledger["surfaces"]:
            surface["authority_rank"] = None
        ledger["claims"] = ledger["claims"][:1]
        self.assertEqual(MODULE.validate(ledger), [])
        conflict = MODULE.reconcile(ledger)["conflicts"][0]
        self.assertFalse(conflict["fixable"])
        self.assertNotIn("authoritative_value", conflict)

    def test_same_surface_disagreement_is_classified(self):
        ledger = valid_ledger()
        duplicate = copy.deepcopy(ledger["claims"][0])
        duplicate["id"] = "CLM-003"
        duplicate["location"] = "openapi.yaml:43"
        duplicate["value"] = "integer"
        ledger["claims"].append(duplicate)
        self.assertEqual(MODULE.validate(ledger), [])
        conflict = MODULE.reconcile(ledger)["conflicts"][0]
        self.assertEqual(conflict["classification"], "intra-surface-conflict")
        self.assertEqual(conflict["conflicting_surface_ids"], ["schema"])
        self.assertFalse(conflict["fixable"])

    def test_same_surface_duplicate_value_is_consistent(self):
        ledger = valid_ledger()
        duplicate = copy.deepcopy(ledger["claims"][0])
        duplicate["id"] = "CLM-003"
        duplicate["location"] = "openapi.yaml:43"
        ledger["claims"].append(duplicate)
        self.assertEqual(MODULE.validate(ledger), [])
        self.assertEqual(MODULE.reconcile(ledger)["summary"]["conflicts"], 0)

    def test_regenerate_requires_update_command(self):
        ledger = valid_ledger()
        del ledger["surfaces"][1]["update_command"]
        errors = MODULE.validate(ledger)
        self.assertTrue(any("update_command" in error for error in errors))

    def test_authority_source_requires_provenance(self):
        ledger = valid_ledger()
        ledger["authority_policy"]["source"] = "AGENTS.md"
        errors = MODULE.validate(ledger)
        self.assertTrue(any("path:line" in error for error in errors))

        ledger["authority_policy"]["source"] = "user:explicit decision"
        self.assertEqual(MODULE.validate(ledger), [])

    def test_malformed_expectation_surface_does_not_crash(self):
        ledger = valid_ledger()
        ledger["expectations"][0]["surfaces"] = [{"bad": "surface"}]
        errors = MODULE.validate(ledger)
        self.assertTrue(any("non-empty strings" in error for error in errors))

    def test_cli_prints_template_and_writes_result(self):
        template_result = subprocess.run(
            [sys.executable, str(SCRIPT), "--print-template"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(template_result.returncode, 0)
        ledger = json.loads(template_result.stdout)
        self.assertEqual(MODULE.validate(ledger), [])

        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "CLAIMS.json"
            output_path = Path(tmp) / "CONFLICTS.json"
            ledger_path.write_text(json.dumps(ledger))
            run_result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(ledger_path),
                    "--output",
                    str(output_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            output = json.loads(output_path.read_text())
        self.assertEqual(run_result.returncode, 0)
        self.assertEqual(output["summary"]["conflicts"], 0)


if __name__ == "__main__":
    unittest.main()
