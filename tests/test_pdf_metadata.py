"""Fail-closed controls for the optional generated-PDF metadata checker."""
from pathlib import Path
import runpy
from types import SimpleNamespace
import unittest

CHECK = runpy.run_path(str(Path(__file__).resolve().parents[1] / "tools/check_pdf_metadata.py"))


class PdfMetadataTests(unittest.TestCase):
    def test_only_plain_first_page_fit_allowed(self):
        ref = SimpleNamespace(idnum=12, generation=0)
        self.assertTrue(CHECK["local_first_page_fit"]({"/S": "/GoTo", "/D": [ref, "/Fit"]}, ref))
        for bad in ({"/S": "/JavaScript", "/D": [ref, "/Fit"]},
                    {"/S": "/GoTo", "/D": [ref, "/Fit"], "/Next": {}},
                    {"/S": "/GoToR", "/D": [ref, "/Fit"]},
                    {"/S": "/GoTo", "/D": [SimpleNamespace(idnum=13, generation=0), "/Fit"]}):
            with self.subTest(bad=bad):
                self.assertFalse(CHECK["local_first_page_fit"](bad, ref))


if __name__ == "__main__":
    unittest.main()
