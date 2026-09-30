"""Keep editorial amendments narrow and the evidence map fail-closed."""
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "manuscript/candidates/2026-09-30_counteraudit_revision"
SPEC = importlib.util.spec_from_file_location("counteraudit_build", PACKAGE / "scripts/build_editions.py")
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)


class CounterauditTests(unittest.TestCase):
    def test_only_declared_changes_and_preserved_witnesses(self):
        with tempfile.TemporaryDirectory() as tmp:
            for edition in ("compact", "selected", "long"):
                target = Path(tmp) / edition
                report = BUILD.assemble(target, edition)
                changes = report["counteraudit_changes"]
                self.assertTrue(changes)
                self.assertTrue(all(change["count"] == 1 for change in changes))
                for relative, digest in report["predecessor"]["assembled_sources_sha256"].items():
                    text = (target / relative).read_text()
                    for change in reversed(changes):
                        if change["file"] == relative:
                            self.assertEqual(text.count(change["after"]), 1)
                            text = text.replace(change["after"], change["before"])
                    import hashlib
                    self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), digest)
                abstract = (target / "sections/00_abstract.tex").read_text()
                self.assertIn("this project's former", abstract)
                self.assertLess(len(abstract.split(r"\end{abstract}")[0].split()), 251)
                if edition != "compact":
                    self.assertIn("without a\nprimitive-group filter", abstract)
                else:
                    reproduction = (target / "sections/08_short_reproducibility.tex").read_text()
                    self.assertIn(r"\begin{verbatim}", reproduction)
                    self.assertIn("  --output .audit/three-editions-check", reproduction)
                    self.assertNotIn(r"\texttt{--output", reproduction)
                bibliography = (target / "references_nonpower.bib").read_text()
                self.assertIn(r"howpublished  = {Preprint, \url{https://arxiv.org/abs/2607.09459}}", bibliography)
                self.assertIn("journal       = {Journal of Combinatorial Designs}", bibliography)

    def test_replacement_guard_rejects_missing_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.tex"
            path.write_text("unchanged")
            with self.assertRaises(ValueError):
                BUILD.OLD.replace_exact(path, "absent", "new")
            self.assertEqual(path.read_text(), "unchanged")

    def test_current_evidence_links_resolve_inside_repository(self):
        checked = 0
        for document in sorted(PACKAGE.glob("*.md")):
            for link in re.findall(r"\[[^\]]+\]\(([^()\s]+)\)", document.read_text()):
                if "://" in link or link.startswith("#"):
                    continue
                target = (document.parent / link.split("#", 1)[0]).resolve()
                self.assertTrue(target.is_relative_to(ROOT), (document.name, link))
                self.assertTrue(target.exists(), (document.name, link))
                checked += 1
        self.assertGreaterEqual(checked, 50)

    def test_current_index_keeps_critical_scope(self):
        text = (PACKAGE / "THEOREM_EVIDENCE.md").read_text()
        for boundary in ("C38 is disproved", "Unrestricted order 18 remains open",
                         "C274", "C279", "C280", "not two independent search kernels",
                         "138468", "not every sentence"):
            self.assertIn(boundary, text)
        record = json.loads((PACKAGE / "THEOREM_EVIDENCE.json").read_text())
        self.assertEqual(record["compiled_label_count"], 103)
        self.assertEqual(len({r["label"] for r in record["records"]}), 103)
        c157 = next(r for r in record["records"] if r["label"] == "cthm:order10-nonexistence")
        self.assertNotIn("compact", c157["editions"])


if __name__ == "__main__":
    unittest.main()
