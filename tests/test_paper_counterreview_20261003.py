import hashlib
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "manuscript/candidates/2026-10-03_counteraudit_revision"


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, PACKAGE / "scripts" / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BUILD = load("october_counterreview_build", "build_editions.py")
CHECK = load("october_counterreview_controls", "check_review_controls.py")


class CounterreviewTests(unittest.TestCase):
    def test_reversible_overlay_shared_witnesses_and_scoped_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            shared = (PACKAGE / "sections/pattern_witnesses.tex").read_text()
            for edition in ("compact", "selected", "long"):
                target = Path(temp) / edition
                report = BUILD.assemble(target, edition)
                for relative, digest in report["predecessor"]["assembled_sources_sha256"].items():
                    text = (target / relative).read_text()
                    for change in reversed(report["counterreview_changes"]):
                        if change["file"] == relative:
                            self.assertEqual(text.count(change["after"]), 1)
                            text = text.replace(change["after"], change["before"])
                    self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), digest, relative)
                name = {"compact": "06_short_computational", "selected": "05_computational_core",
                        "long": "05_computational_results"}[edition]
                computational = (target / "sections" / (name + ".tex")).read_text()
                self.assertIn(shared, computational)
                self.assertNotIn("Computational Theorem~\\ref{cthm:order8} supplies", computational)
                self.assertIn("283657", computational)
                self.assertNotIn("only the realization of all eight patterns uses the census",
                                 (target / "sections/01_introduction.tex").read_text())
                if edition == "compact":
                    self.assertIn("tools/check_paper_editions.py",
                                  (target / "sections/08_short_reproducibility.tex").read_text())
                if edition != "compact":
                    self.assertIn("changes $2k$ cells", (target / "sections/02_definitions.tex").read_text())
                    self.assertNotIn("The two PDF variants", (target / "sections/06_snapshot_evidence.tex").read_text())
                    self.assertIn("StonesVojtechovskyWanless2012",
                                  (target / "sections/19_e9_free_coordinates.tex").read_text())

    def test_controls_and_essential_hypotheses(self):
        report = CHECK.check()
        self.assertTrue(report["passed"])
        self.assertEqual(len(report["eight_patterns"]), 8)
        self.assertEqual(report["malformed_controls_rejected"], 8)
        self.assertEqual(len(report["support_sign_controls"]), 6)
        self.assertEqual(report["mixed_S6_even_products"], 720)
        self.assertTrue(all(r["pattern"] == "TTT" for r in report["row_F_required_controls"].values()))

    def test_invalid_tables_and_matchings_rejected(self):
        for table in ([], [[0, 0], [1, 1]], [[False]], [[0, 1], [0, 1]]):
            with self.assertRaises(ValueError):
                CHECK.scan(table)
        with self.assertRaises(ValueError):
            CHECK.union_type((0, 0), (0, 1))

    def test_no_cutoff_or_theorem_upgrade(self):
        plan = json.loads((PACKAGE / "editions.json").read_text())
        self.assertFalse(plan["new_mathematical_claims"])
        self.assertTrue(plan["proof_dependencies_changed"])
        self.assertEqual(plan["evidence_cutoff_utc"], "2026-10-02T14:03:38Z")
        index = json.loads((PACKAGE / "THEOREM_EVIDENCE.json").read_text())
        self.assertEqual(index["compiled_label_count"], 106)
        self.assertEqual(len({r["label"] for r in index["records"]}), 106)

    def test_local_links_resolve(self):
        for document in PACKAGE.glob("*.md"):
            for link in re.findall(r"\[[^\]]+\]\(([^()\s]+)\)", document.read_text()):
                if "://" in link or link.startswith("#"):
                    continue
                path = (document.parent / link.split("#", 1)[0]).resolve()
                self.assertTrue(path.is_relative_to(ROOT), link)
                self.assertTrue(path.exists(), link)


if __name__ == "__main__":
    unittest.main()
