"""Negative controls and evidence boundaries for the current public edition."""
import hashlib
from itertools import permutations
import json
from pathlib import Path
import runpy
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "manuscript/candidates/2026-09-28_research_review"
CURRENT_SOURCE = ROOT / "manuscript/candidates/2026-09-30_research_review"
PDF_ALIASES = {"papers/FFF_Compact_Research_Dossier.pdf",
               "papers/FFF_Long_Research_Dossier.pdf"}
CORRECTIONS_SHA256 = "7f359799f6b97bb14e512e90483221c92bb4b7848548423a547d2b3844de42a9"
sys.path.insert(0, str(SOURCE / "scripts"))
AUDIT = runpy.run_path(str(SOURCE / "scripts/audit_snapshot.py"))
UPDATE = runpy.run_path(str(SOURCE / "scripts/audit_update.py"))
CRT = runpy.run_path(str(SOURCE / "scripts/audit_crt_update.py"))
sys.path.pop(0)


class CurrentSnapshotTests(unittest.TestCase):
    def receipt_rows(self, records, digest_key):
        self.assertIsInstance(records, list)
        self.assertTrue(records, "receipt inventory must not be empty")
        indexed = {}
        for row in records:
            self.assertIsInstance(row, dict)
            self.assertIsInstance(row["path"], str)
            relative = Path(row["path"])
            self.assertTrue(relative.parts)
            self.assertFalse(relative.is_absolute())
            self.assertNotIn("..", relative.parts)
            self.assertEqual(relative.as_posix(), row["path"])
            self.assertNotIn(row["path"], indexed, "duplicate receipt path")
            self.assertRegex(row[digest_key], r"^[0-9a-f]{64}$")
            indexed[row["path"]] = row
        return indexed

    def receipt_chain(self, capture_bytes, correction_bytes, current):
        capture = json.loads(capture_bytes)
        correction = json.loads(correction_bytes)
        self.assertEqual(capture["last_in_scope_claim"], "C271")
        self.assertEqual(correction["last_in_scope_claim"], "C271")
        self.assertEqual(current["last_in_scope_claim"], "C280")
        self.assertEqual(correction["previous_receipt_sha256"],
                         hashlib.sha256(capture_bytes).hexdigest())
        self.assertEqual(current["previous_receipt_sha256"],
                         hashlib.sha256(correction_bytes).hexdigest())
        expected = {path: row["public_sha256"] for path, row in
                    self.receipt_rows(capture["files"], "public_sha256").items()}
        for receipt in (correction, current):
            replacements = self.receipt_rows(receipt["superseded_aliases"], "public_sha256")
            self.assertEqual(set(replacements), PDF_ALIASES)
            for path, row in replacements.items():
                self.assertEqual(row["previous_sha256"], expected[path], path)
                expected[path] = row["public_sha256"]
            for path, row in self.receipt_rows(receipt["files"], "sha256").items():
                self.assertIn(set(row), ({"path", "sha256"}, {"path", "bytes", "sha256"}))
                if "bytes" in row:
                    self.assertIs(type(row["bytes"]), int, path)
                    self.assertGreaterEqual(row["bytes"], 0, path)
                    self.assertEqual((ROOT / path).stat().st_size, row["bytes"], path)
                if path in expected:
                    self.assertEqual(row["sha256"], expected[path],
                                     "receipt attempts to rewrite frozen bytes: " + path)
                expected[path] = row["sha256"]
        return expected

    def test_selected_input_inventory(self):
        self.assertGreater(AUDIT["audit_sources"]()["immutable_files_checked"], 35)
        capture = (ROOT / "PUBLIC_SNAPSHOT_2026-09-28.json").read_bytes()
        correction = (ROOT / "PUBLIC_SNAPSHOT_2026-09-28_CORRECTIONS.json").read_bytes()
        self.assertEqual(hashlib.sha256(correction).hexdigest(), CORRECTIONS_SHA256)
        current = json.loads((ROOT / "PUBLIC_SNAPSHOT_2026-09-30.json").read_text())
        expected_files = self.receipt_chain(capture, correction, current)
        typography = json.loads((ROOT / "PUBLIC_SNAPSHOT_2026-09-30_TYPOGRAPHY.json").read_text())
        expected_files = self.typography_receipt(
            expected_files, (ROOT / "PUBLIC_SNAPSHOT_2026-09-30.json").read_bytes(),
            typography)
        counteraudit_bytes = (ROOT / "PUBLIC_SNAPSHOT_2026-09-30_COUNTERAUDIT.json").read_bytes()
        expected_files = self.counteraudit_receipt(
            expected_files, (ROOT / "PUBLIC_SNAPSHOT_2026-09-30_TYPOGRAPHY.json").read_bytes(),
            json.loads(counteraudit_bytes))
        e9_bytes = (ROOT / "PUBLIC_SNAPSHOT_2026-10-02.json").read_bytes()
        expected_files = self.e9_receipt(expected_files, counteraudit_bytes, json.loads(e9_bytes))
        expected_files = self.review_receipt(expected_files, e9_bytes,
            json.loads((ROOT / "PUBLIC_SNAPSHOT_2026-10-03.json").read_text()))
        for relative, expected in expected_files.items():
            path = ROOT / relative
            self.assertFalse(path.is_symlink(), relative)
            self.assertTrue(path.resolve().is_relative_to(ROOT), relative)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected, relative)
        self.assertTrue(CURRENT_SOURCE.is_dir())
        prefix = CURRENT_SOURCE.relative_to(ROOT).as_posix() + "/"
        recorded = {row["path"] for row in current["files"] if row["path"].startswith(prefix)}
        shipped = {path.relative_to(ROOT).as_posix() for path in CURRENT_SOURCE.rglob("*")
                   if path.is_file()}
        self.assertTrue(shipped)
        self.assertEqual(recorded, shipped, "new candidate receipt coverage differs")

    def review_receipt(self, expected, previous_bytes, successor):
        self.assertEqual(successor["previous_receipt_sha256"], hashlib.sha256(previous_bytes).hexdigest())
        self.assertEqual(successor["baseline_claim_cutoff"], "C280")
        self.assertEqual(successor["baseline_evidence_cutoff_utc"], "2026-09-30T12:54:17Z")
        self.assertEqual(successor["selected_evidence_cutoff_utc"], "2026-10-02T14:03:38Z")
        self.assertIs(successor["mathematical_claims_changed"], False)
        self.assertIs(successor["proof_dependencies_changed"], True)
        self.assertEqual(successor["unrestricted_order18"], "open")
        result = dict(expected)
        replacements = self.receipt_rows(successor["superseded_aliases"], "public_sha256")
        self.assertEqual(set(replacements), PDF_ALIASES | {"papers/FFF_Selected_Research_Dossier.pdf"})
        for path, row in replacements.items():
            self.assertEqual(row["previous_sha256"], result[path], path)
            result[path] = row["public_sha256"]
        prefix = "manuscript/candidates/2026-10-03_counteraudit_revision/"
        rows = self.receipt_rows(successor["files"], "sha256")
        for path, row in rows.items():
            self.assertTrue(path.startswith(prefix), path)
            self.assertNotIn(path, result, "Attempt to replace frozen science")
            self.assertEqual(set(row), {"path", "bytes", "sha256"})
            self.assertIs(type(row["bytes"]), int)
            self.assertEqual((ROOT / path).stat().st_size, row["bytes"])
            result[path] = row["sha256"]
        shipped = {p.relative_to(ROOT).as_posix() for p in (ROOT / prefix).rglob("*") if p.is_file()}
        self.assertEqual(set(rows), shipped)
        return result

    def test_review_successor_cannot_change_cutoff_or_frozen_bytes(self):
        current = json.loads((ROOT / "PUBLIC_SNAPSHOT_2026-10-03.json").read_text())
        previous = (ROOT / "PUBLIC_SNAPSHOT_2026-10-02.json").read_bytes()
        old = {r["path"]: r["previous_sha256"] for r in current["superseded_aliases"]}
        for fault in ("chain", "alias", "science", "dependency", "scope", "cutoff", "missing", "frozen"):
            bad = json.loads(json.dumps(current))
            if fault == "chain":
                bad["previous_receipt_sha256"] = "0" * 64
            elif fault == "alias":
                bad["superseded_aliases"][0]["previous_sha256"] = "0" * 64
            elif fault == "science":
                bad["mathematical_claims_changed"] = True
            elif fault == "dependency":
                bad["proof_dependencies_changed"] = False
            elif fault == "scope":
                bad["unrestricted_order18"] = "excluded"
            elif fault == "cutoff":
                bad["selected_evidence_cutoff_utc"] = "2026-10-03T00:00:00Z"
            elif fault == "frozen":
                bad["files"][0]["path"] = "manuscript/main.tex"
            else:
                bad["files"].pop()
            with self.subTest(fault=fault), self.assertRaises(AssertionError):
                self.review_receipt(old, previous, bad)

    def e9_receipt(self, expected, previous_bytes, successor):
        self.assertEqual(successor["previous_receipt_sha256"], hashlib.sha256(previous_bytes).hexdigest())
        self.assertEqual(successor["baseline_claim_cutoff"], "C280")
        self.assertIs(successor["mathematical_claims_changed"], True)
        self.assertEqual(successor["unrestricted_order18"], "open")
        self.assertEqual(successor["selected_addition"], "E9 two-free-coordinate theorem only")
        result = dict(expected)
        aliases = PDF_ALIASES | {"papers/FFF_Selected_Research_Dossier.pdf"}
        replacements = self.receipt_rows(successor["superseded_aliases"], "public_sha256")
        self.assertEqual(set(replacements), aliases)
        for path, row in replacements.items():
            self.assertEqual(row["previous_sha256"], result[path], path)
            result[path] = row["public_sha256"]
        prefix = "manuscript/candidates/2026-10-02_e9_symmetry_review/"
        rows = self.receipt_rows(successor["files"], "sha256")
        for path, row in rows.items():
            self.assertTrue(path.startswith(prefix), path)
            self.assertNotIn(path, result, "Attempt to replace frozen science")
            self.assertEqual((ROOT / path).stat().st_size, row["bytes"])
            result[path] = row["sha256"]
        shipped = {p.relative_to(ROOT).as_posix() for p in (ROOT / prefix).rglob("*") if p.is_file()}
        self.assertEqual(set(rows), shipped, "Selected extension coverage differs")
        return result

    def test_e9_successor_rejects_wrong_alias_or_scope(self):
        current = json.loads((ROOT / "PUBLIC_SNAPSHOT_2026-10-02.json").read_text())
        previous = (ROOT / "PUBLIC_SNAPSHOT_2026-09-30_COUNTERAUDIT.json").read_bytes()
        old = {r["path"]: r["previous_sha256"] for r in current["superseded_aliases"]}
        for fault in ("chain", "alias", "science", "scope", "missing"):
            bad = json.loads(json.dumps(current))
            if fault == "chain":
                bad["previous_receipt_sha256"] = "0" * 64
            elif fault == "alias":
                bad["superseded_aliases"][0]["previous_sha256"] = "0" * 64
            elif fault == "science":
                bad["mathematical_claims_changed"] = False
            elif fault == "scope":
                bad["unrestricted_order18"] = "excluded"
            else:
                bad["files"].pop()
            with self.subTest(fault=fault), self.assertRaises(AssertionError):
                self.e9_receipt(old, previous, bad)

    def counteraudit_receipt(self, expected, previous_bytes, successor):
        self.assertEqual(successor["previous_receipt_sha256"],
                         hashlib.sha256(previous_bytes).hexdigest())
        self.assertEqual(successor["last_in_scope_claim"], "C280")
        self.assertIs(successor["mathematical_claims_changed"], False)
        result = dict(expected)
        replacements = self.receipt_rows(successor["superseded_aliases"], "public_sha256")
        self.assertEqual(set(replacements), PDF_ALIASES)
        for path, row in replacements.items():
            self.assertEqual(row["previous_sha256"], result[path])
            result[path] = row["public_sha256"]
        added = self.receipt_rows(successor["new_aliases"], "public_sha256")
        self.assertEqual(set(added), {"papers/FFF_Selected_Research_Dossier.pdf"})
        for path, row in added.items():
            self.assertNotIn(path, result)
            result[path] = row["public_sha256"]
        for path, row in self.receipt_rows(successor["files"], "sha256").items():
            if path in result:
                self.assertEqual(row["sha256"], result[path], "Frozen source changed: " + path)
            result[path] = row["sha256"]
        return result

    def test_counteraudit_receipt_keeps_frozen_sources_and_single_new_alias(self):
        old = {path: "1" * 64 for path in PDF_ALIASES | {"immutable.txt"}}
        previous = b"frozen predecessor"
        receipt = {"previous_receipt_sha256": hashlib.sha256(previous).hexdigest(),
                   "last_in_scope_claim": "C280", "mathematical_claims_changed": False,
                   "superseded_aliases": [{"path": path, "previous_sha256": "1" * 64,
                                           "public_sha256": "2" * 64} for path in sorted(PDF_ALIASES)],
                   "new_aliases": [{"path": "papers/FFF_Selected_Research_Dossier.pdf",
                                    "public_sha256": "3" * 64}],
                   "files": [{"path": "counteraudit-source.txt", "sha256": "4" * 64}]}
        result = self.counteraudit_receipt(old, previous, receipt)
        self.assertEqual(result["immutable.txt"], old["immutable.txt"])
        for fault in ("missing", "unexpected", "overwrite", "frozen", "claim"):
            changed = json.loads(json.dumps(receipt))
            if fault == "missing":
                changed["new_aliases"] = []
            elif fault == "unexpected":
                changed["new_aliases"][0]["path"] = "papers/Unreviewed.pdf"
            elif fault == "overwrite":
                changed["new_aliases"][0]["path"] = "immutable.txt"
            elif fault == "frozen":
                changed["files"] = [{"path": "immutable.txt", "sha256": "0" * 64}]
            else:
                changed["mathematical_claims_changed"] = True
            with self.subTest(fault=fault), self.assertRaises(AssertionError):
                self.counteraudit_receipt(old, previous, changed)

    def typography_receipt(self, expected, previous_bytes, successor):
        self.assertEqual(successor["previous_receipt_sha256"],
                         hashlib.sha256(previous_bytes).hexdigest())
        self.assertEqual(successor["last_in_scope_claim"], "C280")
        self.assertIs(successor["mathematical_claims_changed"], False)
        result = dict(expected)
        replacements = self.receipt_rows(successor["superseded_aliases"], "public_sha256")
        self.assertEqual(set(replacements), PDF_ALIASES)
        for path, row in replacements.items():
            self.assertEqual(row["previous_sha256"], result[path])
            result[path] = row["public_sha256"]
        for path, row in self.receipt_rows(successor["files"], "sha256").items():
            if path in result:
                self.assertEqual(row["sha256"], result[path], "Frozen source changed: " + path)
            result[path] = row["sha256"]
        return result

    def test_typography_successor_does_not_relax_frozen_payload_checks(self):
        previous = b"frozen receipt"
        expected = {path: "1" * 64 for path in PDF_ALIASES | {"frozen.txt"}}
        successor = {"previous_receipt_sha256": hashlib.sha256(previous).hexdigest(),
                     "last_in_scope_claim": "C280", "mathematical_claims_changed": False,
                     "superseded_aliases": [
                         {"path": path, "previous_sha256": "1" * 64, "public_sha256": "2" * 64}
                         for path in sorted(PDF_ALIASES)],
                     "files": [{"path": "layout.txt", "sha256": "3" * 64}]}
        result = self.typography_receipt(expected, previous, successor)
        self.assertEqual(result["frozen.txt"], "1" * 64)
        for fault in ("chain", "alias", "science", "frozen"):
            changed = json.loads(json.dumps(successor))
            if fault == "chain":
                changed["previous_receipt_sha256"] = "0" * 64
            elif fault == "alias":
                changed["superseded_aliases"][0]["previous_sha256"] = "0" * 64
            elif fault == "science":
                changed["mathematical_claims_changed"] = True
            else:
                changed["files"].append({"path": "frozen.txt", "sha256": "9" * 64})
            with self.subTest(fault=fault), self.assertRaises(AssertionError):
                self.typography_receipt(expected, previous, changed)

    def receipt_fixture(self):
        capture = {"last_in_scope_claim": "C271", "files": [
            {"path": path, "public_sha256": "1" * 64}
            for path in sorted(PDF_ALIASES | {"frozen-original.txt"})]}
        capture_bytes = json.dumps(capture).encode()
        correction = {"last_in_scope_claim": "C271",
                      "previous_receipt_sha256": hashlib.sha256(capture_bytes).hexdigest(),
                      "files": [{"path": "frozen-correction.txt", "sha256": "2" * 64}],
                      "superseded_aliases": [
                          {"path": path, "previous_sha256": "1" * 64, "public_sha256": "2" * 64}
                          for path in sorted(PDF_ALIASES)]}
        correction_bytes = json.dumps(correction).encode()
        current = {"last_in_scope_claim": "C280",
                   "previous_receipt_sha256": hashlib.sha256(correction_bytes).hexdigest(),
                   "files": [{"path": "new-source.txt", "sha256": "3" * 64}],
                   "superseded_aliases": [
                       {"path": path, "previous_sha256": "2" * 64, "public_sha256": "3" * 64}
                       for path in sorted(PDF_ALIASES)]}
        return capture_bytes, correction_bytes, current

    def test_receipt_chain_preserves_both_frozen_generations(self):
        expected = self.receipt_chain(*self.receipt_fixture())
        self.assertEqual(expected["frozen-original.txt"], "1" * 64)
        self.assertEqual(expected["frozen-correction.txt"], "2" * 64)
        self.assertEqual(expected["new-source.txt"], "3" * 64)
        for alias in PDF_ALIASES:
            self.assertEqual(expected[alias], "3" * 64)

    def test_receipt_chain_rejects_broken_links_and_aliases(self):
        for fault in ("receipt_hash", "alias_predecessor", "missing_alias", "duplicate_alias", "other_alias"):
            capture, correction, current = self.receipt_fixture()
            if fault == "receipt_hash":
                current["previous_receipt_sha256"] = "0" * 64
            elif fault == "alias_predecessor":
                current["superseded_aliases"][0]["previous_sha256"] = "1" * 64
            elif fault == "missing_alias":
                current["superseded_aliases"].pop()
            elif fault == "duplicate_alias":
                current["superseded_aliases"].append(current["superseded_aliases"][0])
            else:
                current["superseded_aliases"][0]["path"] = "frozen-original.txt"
            with self.subTest(fault=fault), self.assertRaises(AssertionError):
                self.receipt_chain(capture, correction, current)

    def test_receipt_cannot_redeclare_changed_historical_files(self):
        for path in ("frozen-original.txt", "frozen-correction.txt"):
            capture, correction, current = self.receipt_fixture()
            current["files"].append({"path": path, "sha256": "3" * 64})
            with self.subTest(path=path), self.assertRaises(AssertionError):
                self.receipt_chain(capture, correction, current)

    def test_receipt_rejects_duplicate_and_unsafe_paths(self):
        for path in ("new-source.txt", "../outside", "/outside", "./noncanonical"):
            capture, correction, current = self.receipt_fixture()
            current["files"].append({"path": path, "sha256": "3" * 64})
            with self.subTest(path=path), self.assertRaises(AssertionError):
                self.receipt_chain(capture, correction, current)

    def test_expanded_certificate_scope_and_corner_positive(self):
        table = UPDATE["corner_table"](19, 7)
        self.assertTrue(AUDIT["scan"](table)[0]["fff"])
        self.assertEqual(UPDATE["intercalates"](table), 1)
        self.assertEqual(UPDATE["minor_certificate"](table)["rank"], 58)
        record = json.loads((SOURCE / "results/update_audit.json").read_text())
        family = record["expanded_class_family"]
        self.assertEqual(len(family["independently_checked_minors"]), 1703)
        self.assertEqual(family["order40_lower_bound"], 1450956)
        self.assertFalse(family["C157_dependency"])

    def test_crt_pinned_imports_and_separate_probes(self):
        builder, physical, payload = CRT["load_inputs"]()
        self.assertIs(physical.Context, builder.Context)
        self.assertEqual([item["N"] for item in payload["cases"]], [9, 15, 45, 75])
        self.assertEqual(CRT["PROBES"], ((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)))

    def test_channel_truth_tables_include_failures(self):
        for n in range(1, 7):
            first = list(range(n))
            for second in permutations(range(n)):
                shape = AUDIT["partition"](first, second)
                self.assertEqual(shape, AUDIT["matching_partition"](first, second))
                self.assertEqual(AUDIT["color_channel"](first, second), all(x % 2 == 0 for x in shape))

    def test_invalid_latin_rejected(self):
        for table in ([[0, 0], [1, 1]], [[0, 1], [0, 1]]):
            with self.assertRaises(ValueError):
                AUDIT["scan"](table)

    def test_odd_order_and_trivial_boundary(self):
        self.assertEqual(AUDIT["scan"]([[0]])[0]["pattern"], "FFF")
        self.assertEqual(AUDIT["scan"]([[0, 1], [1, 0]])[0]["pattern"], "FFF")
        self.assertEqual(AUDIT["scan"]([[(r+c) % 3 for c in range(3)] for r in range(3)])[0]["pattern"], "TTT")

    def test_explicit_counterexample(self):
        result, _ = AUDIT["scan"](AUDIT["load_table"](SOURCE / "evidence/data/order12_first.json"))
        self.assertTrue(result["latin"] and result["fff"])
        self.assertEqual(result["line_pairs_checked"], 198)

    def test_affine_criterion_not_universal_exclusion(self):
        self.assertEqual(AUDIT["affine_pattern"](97, 36), "FFF")
        self.assertTrue(all(AUDIT["affine_pattern"](17, a) != "FFF" for a in range(2, 17)))
        self.assertEqual(AUDIT["scan"](AUDIT["affine_table"](11, 6))[0]["pattern"], "FFF")


if __name__ == "__main__":
    unittest.main()
