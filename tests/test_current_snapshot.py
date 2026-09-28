"""Negative controls and evidence boundaries for the current public edition."""
import hashlib
from itertools import permutations
import json
from pathlib import Path
import runpy
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "manuscript/candidates/2026-09-28_research_review"
sys.path.insert(0, str(SOURCE / "scripts"))
AUDIT = runpy.run_path(str(SOURCE / "scripts/audit_snapshot.py"))
UPDATE = runpy.run_path(str(SOURCE / "scripts/audit_update.py"))
CRT = runpy.run_path(str(SOURCE / "scripts/audit_crt_update.py"))
sys.path.pop(0)


class CurrentSnapshotTests(unittest.TestCase):
    def test_selected_input_inventory(self):
        self.assertGreater(AUDIT["audit_sources"]()["immutable_files_checked"], 35)
        capture = json.loads((ROOT / "PUBLIC_SNAPSHOT_2026-09-28.json").read_text())
        self.assertEqual(capture["last_in_scope_claim"], "C271")
        for row in capture["files"]:
            self.assertEqual(hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest(), row["public_sha256"])

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
