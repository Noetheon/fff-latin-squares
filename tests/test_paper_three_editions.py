"""Editorial scope, shared-source preservation and compact finite controls."""
import importlib.util
from pathlib import Path
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "manuscript/candidates/2026-09-30_three_editions"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BUILD = load("three_editions", PACKAGE / "scripts/build_editions.py")
CHECK = load("compact_checks", PACKAGE / "scripts/check_compact_examples.py")


class ThreeEditionTests(unittest.TestCase):
    def test_catalogue_and_total_page_budget(self):
        self.assertEqual([e["id"] for e in BUILD.PLAN["editions"]], ["compact", "selected", "long"])
        compact = BUILD.PLAN["editions"][0]
        for pages in (12, 15, 18):
            self.assertTrue(BUILD.check_page_budget(compact, pages))
        for pages in (11, 19, 44):
            self.assertFalse(BUILD.check_page_budget(compact, pages))
        self.assertFalse(BUILD.PLAN["new_mathematical_claims"])

    def test_excerpt_markers_fail_closed(self):
        self.assertEqual(BUILD.excerpt("abc def ghi", "def", "ghi"), "def ")
        for text, start, end in (("abc", "z", None), ("abc abc", "abc", None),
                                 ("abc abc def", "def", "abc"), ("abc", "c", "a")):
            with self.assertRaises(ValueError):
                BUILD.excerpt(text, start, end)

    def test_compact_dependencies_are_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "source"
            report = BUILD.assemble(destination, "compact")
            seen = set()

            def contents(relative):
                if relative in seen:
                    return ""
                seen.add(relative)
                text = (destination / (relative + ".tex")).read_text()
                for child in re.findall(r"\\input\{([^}]+)\}", text):
                    text += contents(child)
                return text

            text = contents("main_compact")
            references = set(re.findall(r"\\(?:eqref|ref)\{([^}]+)\}", text))
            labels = re.findall(r"\\label\{([^}]+)\}", text)
            self.assertFalse(references - set(labels))
            self.assertEqual(len(labels), len(set(labels)))
            self.assertGreaterEqual(len(report["excerpts"]), 7)
            for term in ("no personal mathematical contribution", "Rights remain reserved",
                         "order $18$ remains open", "not a third independent publication"):
                self.assertIn(term, text)
            self.assertIn(r"\documentclass[11pt]{article}", text)
            self.assertIn("margin=30mm", text)
            self.assertNotIn(r"\footnotesize", text)

    def test_selected_changes_only_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "source"
            report = BUILD.assemble(destination, "selected")
            self.assertEqual(len(report["editorial_changes"]), 4)
            for path in (BUILD.BASE / "sections").glob("*.tex"):
                layout_override = BUILD.LAYOUT / "sections" / path.name
                original = (layout_override if layout_override.is_file() else path).read_text()
                actual = (destination / "sections" / path.name).read_text()
                if path.name in {"00_status_note.tex", "01_introduction_core.tex",
                                 "06_reproducibility_core.tex"}:
                    self.assertEqual(original.replace("compact", "selected-results"), actual)
                else:
                    self.assertEqual(original, actual)
            self.assertIn("Selected Results", (destination / "main_core.tex").read_text())

    def test_long_has_no_additional_overrides(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "source"
            report = BUILD.assemble(destination, "long")
            self.assertEqual(report["editorial_changes"], [])
            self.assertEqual(report["excerpts"], [])
            self.assertEqual(report["new_source_sha256"], {})
            self.assertEqual((destination / "main.tex").read_bytes(),
                             (BUILD.LAYOUT / "main.tex").read_bytes())

    def test_displayed_examples_and_negative_controls(self):
        report = CHECK.check()
        self.assertTrue(report["passed"])
        self.assertFalse(report["order8_census_rerun"])
        self.assertEqual(len(report["checks"]["pattern_controls"]), 8)
        with self.assertRaises(ValueError):
            CHECK.scan([[0, 0], [1, 1]])
        with self.assertRaises(ValueError):
            CHECK.cycle_lengths([0, 0])
        self.assertEqual(CHECK.cycle_lengths([1, 0, 3, 4, 2]), [2, 3])


if __name__ == "__main__":
    unittest.main()
