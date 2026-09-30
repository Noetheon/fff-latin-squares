"""Small fail-closed and scope controls for the 30 September paper release."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "manuscript/candidates/2026-09-30_research_review"
SPEC = importlib.util.spec_from_file_location("review30", PACKAGE / "scripts/audit_new_results.py")
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class PaperReviewTests(unittest.TestCase):
    def test_input_hashes_and_exact_coverage(self):
        self.assertEqual(AUDIT.verify_inputs(), 9)

    def test_tampered_hash_fails(self):
        original = AUDIT.read(PACKAGE / "evidence/source_manifest.json")
        broken = copy.deepcopy(original)
        broken["files"][0]["sha256"] = "0" * 64
        with patch.object(AUDIT, "read", return_value=broken), self.assertRaises(ValueError):
            AUDIT.verify_inputs()

    def test_missing_manifest_member_fails(self):
        broken = AUDIT.read(PACKAGE / "evidence/source_manifest.json")
        broken["files"].pop()
        with patch.object(AUDIT, "read", return_value=broken), self.assertRaises(ValueError):
            AUDIT.verify_inputs()

    def test_unsafe_payload_fails(self):
        broken = AUDIT.read(PACKAGE / "evidence/source_manifest.json")
        broken["files"][0]["payload"] = "../outside"
        with patch.object(AUDIT, "read", return_value=broken), self.assertRaises(ValueError):
            AUDIT.verify_inputs()

    def test_same_cardinality_substitution_fails(self):
        broken = AUDIT.read(PACKAGE / "evidence/source_manifest.json")
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp)
            import shutil
            shutil.copytree(PACKAGE / "evidence", package / "evidence")
            row = broken["files"][0]
            shutil.copyfile(package / "evidence" / row["payload"],
                            package / "evidence/unused.py")
            row["payload"] = "unused.py"
            with patch.object(AUDIT, "PACKAGE", package), patch.object(AUDIT, "read", return_value=broken):
                with self.assertRaisesRegex(ValueError, "input coverage"):
                    AUDIT.verify_inputs()

    def test_bool_not_equal_to_integer_in_comparison(self):
        self.assertNotEqual(AUDIT.canonical({"n": 1}), AUDIT.canonical({"n": True}))
        self.assertNotEqual(AUDIT.canonical({"n": 1}), AUDIT.canonical({"n": 1.0}))

    def test_duplicate_or_nonfinite_json_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "input.json"
            for bad in ('{"n":1,"n":2}', '{"n":NaN}', '{"n":Infinity}',
                        '{"n":1e999}', '{"n":-1e999}'):
                path.write_text(bad)
                with self.subTest(bad=bad), self.assertRaises(ValueError):
                    AUDIT.read(path)

    def test_anchor_alternatives(self):
        r = AUDIT.anchor_counts()
        self.assertEqual((r["nonnear_longest_cases"], r["nonnear_dual_positive_cases"]), (13, 31))
        self.assertEqual(r["minimum_positive_nonnear_pairs"], 32)

    def test_complete_degree10_prerequisite(self):
        r = AUDIT.degree_ten_prerequisite(AUDIT.module("mixed_independent"))
        self.assertEqual((r["examined"], r["retained"], r["connected_size10"]), (18900, 96, 0))

    def test_no_open_path_is_a_closed_cycle(self):
        m = AUDIT.module("mixed_independent")
        self.assertEqual(m.partial_odd_cycles({0: 1, 1: 2}), ())
        self.assertEqual(len(m.partial_odd_cycles({0: 1, 1: 2, 2: 0})), 1)

    def test_literal_positive_and_negative_table_controls(self):
        m = AUDIT.module("two_plex_independent")
        self.assertEqual(m.profile([[r ^ c for c in range(4)] for r in range(4)])["pattern"], "FFF")
        self.assertEqual(m.profile([[(r+c) % 3 for c in range(3)] for r in range(3)])["pattern"], "TTT")
        with self.assertRaises(ValueError):
            m.profile([[0, 0], [1, 1]])

    def test_paper_no_global_upgrade(self):
        report = AUDIT.read(PACKAGE / "results/portable_audit.json")
        self.assertIs(report["scientific"]["unrestricted_order18_decided"], False)
        self.assertIs(report["scientific"]["new_FFF18"], False)
        for name in ("main.tex", "main_core.tex"):
            text = (PACKAGE / name).read_text()
            self.assertIn("30 September 2026", text)
            self.assertIn("Not externally peer reviewed", text)
            self.assertIn("\\author{}", text)


if __name__ == "__main__":
    unittest.main()
