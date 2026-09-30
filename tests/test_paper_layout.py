"""Keep front-matter defects visible without optional PDF/TeX dependencies."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "manuscript/candidates/2026-09-30_typography_review"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


LAYOUT = load(ROOT / "tools/check_paper_layout.py", "layout")
BUILD = load(SOURCE / "scripts/build_pdfs.py", "layout_build")


class PaperLayoutTests(unittest.TestCase):
    def fixture(self):
        return (["Title Abstract Keywords. Mathematics Subject Classification",
                 "Status, attribution, and evidence boundary. Draft.",
                 "Contents 1 Introduction 1 References 2",
                 "1 Introduction Mathematical text.",
                 "References Bibliography."],
                ["i", "ii", "iii", "1", "2"], 3, 4)

    def test_isolated_contents_and_body_numbering(self):
        self.assertEqual(LAYOUT.structure_errors(*self.fixture()), [])

    def test_reported_shared_page_defect_is_rejected(self):
        texts, labels, intro, refs = self.fixture()
        texts[2] += " 1 Introduction Mathematical text."
        self.assertTrue(LAYOUT.structure_errors(texts, labels, 2, refs))
        texts[1] += " Contents"
        self.assertTrue(LAYOUT.structure_errors(texts, labels, intro, refs))

    def test_numbering_missing_metadata_blank_pages_and_references(self):
        for fault in ("numbering", "metadata", "blank", "references", "unresolved"):
            texts, labels, intro, refs = self.fixture()
            if fault == "numbering":
                labels[3] = "4"
            elif fault == "metadata":
                texts[0] = "Title only"
            elif fault == "blank":
                texts[4] = ""
            elif fault == "references":
                texts[4] = "End of discussion. References"
            else:
                texts[3] += " Theorem ??"
            with self.subTest(fault=fault):
                self.assertTrue(LAYOUT.structure_errors(texts, labels, intro, refs))

    def test_both_entries_share_front_matter_and_reference_policy(self):
        for entry in ("main.tex", "main_core.tex"):
            source = (SOURCE / entry).read_text()
            self.assertIn(r"\documentclass[11pt]{article}", source)
            self.assertEqual(source.count(r"\dossierfrontmatter"), 1)
            self.assertEqual(source.count(r"\dossierreferences"), 1)
            self.assertNotIn(r"\footnotesize", source)
            self.assertIn(r"\author{}", source)
        setup = (SOURCE / "paper_setup.tex").read_text()
        self.assertGreaterEqual(setup.count(r"\clearpage"), 4)
        self.assertIn(r"\usepackage[hidelinks]{hyperref}", setup)
        self.assertIn(r"\setlength{\cftsecnumwidth}{2.6em}", setup)

    def test_body_and_bibliography_preserved_in_build(self):
        with tempfile.TemporaryDirectory() as directory:
            result = BUILD.assemble(Path(directory) / "source")
            self.assertTrue(result["body_and_bibliography_byte_preserved"])
            self.assertEqual(len(result["preserved_sources_sha256"]), 33)
            for entry in ("main.tex", "main_core.tex"):
                import re
                prior = (BUILD.BASE / entry).read_text()
                current = (SOURCE / entry).read_text()
                pattern = r"\\input\{(sections/(?!00_)[^}]+)\}"
                self.assertEqual(re.findall(pattern, prior), re.findall(pattern, current))

    def test_abstract_is_one_paragraph_and_conservative(self):
        source = (SOURCE / "sections/00_abstract.tex").read_text()
        abstract = source.split(r"\begin{abstract}", 1)[1].split(r"\end{abstract}", 1)[0]
        self.assertLessEqual(len(abstract.split()), 250)
        self.assertNotIn("\n\n", abstract.strip())
        self.assertNotIn(r"\cite", abstract)
        self.assertIn("remain open", abstract)
        self.assertIn("not censuses", abstract)
