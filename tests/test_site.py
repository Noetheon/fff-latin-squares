from html.parser import HTMLParser
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from demo_fff import validate


class ExampleTable(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.inside = self.cell = False
        self.rows = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        if tag == "table" and dict(attrs).get("id") == "example-table":
            self.inside = True
        if self.inside and tag == "tr":
            self.row = []
        if self.inside and tag == "td":
            self.cell = True

    def handle_data(self, data):
        if self.cell:
            self.row.append(int(data.strip()))

    def handle_endtag(self, tag):
        if tag == "td":
            self.cell = False
        if self.inside and tag == "tr" and self.row:
            self.rows.append(self.row)
        if tag == "table":
            self.inside = False


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.elements = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


class SiteTests(unittest.TestCase):
    def setUp(self):
        self.source = (ROOT / "index.html").read_text()
        self.page = Page(self.source)

    def test_local_destinations_and_anchors_exist(self):
        ids = [attrs["id"] for _, attrs in self.page.elements if "id" in attrs]
        self.assertEqual(len(ids), len(set(ids)))
        for tag, attrs in self.page.elements:
            for key in ("href", "src"):
                if key not in attrs:
                    continue
                link = urlsplit(attrs[key])
                with self.subTest(tag=tag, url=attrs[key]):
                    if link.scheme:
                        self.assertEqual(link.scheme, "https")
                        self.assertEqual(link.netloc, "github.com")
                        self.assertTrue(link.path.startswith("/Noetheon/fff-latin-squares"))
                    elif link.path:
                        self.assertFalse(Path(link.path).is_absolute())
                        self.assertNotIn("..", Path(link.path).parts)
                        self.assertTrue((ROOT / link.path).is_file())
                    else:
                        self.assertIn(link.fragment, ids)

    def test_english_semantics_no_external_runtime(self):
        self.assertIn(("html", {"lang": "en"}), self.page.elements)
        self.assertEqual(sum(tag == "h1" for tag, _ in self.page.elements), 1)
        self.assertFalse(any(tag in {"script", "iframe"} for tag, _ in self.page.elements))
        for tag, attrs in self.page.elements:
            if tag == "img":
                self.assertIn("alt", attrs)
                self.assertIn("width", attrs)
                self.assertIn("height", attrs)
                self.assertFalse(urlsplit(attrs["src"]).scheme)

    def test_both_pdf_read_and_download_links(self):
        for filename in ("FFF_Compact_Research_Dossier.pdf", "FFF_Long_Research_Dossier.pdf"):
            links = [attrs for tag, attrs in self.page.elements
                     if tag == "a" and attrs.get("href") == f"papers/{filename}"]
            self.assertTrue(any("download" in attrs for attrs in links))
            self.assertTrue(any("download" not in attrs and "aria-hidden" not in attrs for attrs in links))

    def test_evidence_and_origin_boundary_retained(self):
        for required in ("Not peer reviewed", "ChatGPT/Codex", "The global conjecture remains open",
                         "Order 12", "No accountable scholarly author", "Rights remain reserved",
                         "not independent studies", "not a solver-free proof"):
            self.assertIn(required, self.source)
        self.assertIn("<details open>", self.source)

    def test_preview_and_review_entry_points(self):
        metadata = {attrs.get("property", attrs.get("name")): attrs.get("content")
                    for tag, attrs in self.page.elements if tag == "meta"}
        self.assertEqual(metadata["og:image"],
                         "https://noetheon.github.io/fff-latin-squares/assets/social-preview.png")
        self.assertEqual(metadata["og:image:width"], "1280")
        self.assertEqual(metadata["og:image:height"], "640")
        self.assertIn("Not peer reviewed", metadata["og:description"])
        self.assertIn("AI-generated", metadata["og:description"])
        self.assertIn("Run a small example", self.source)
        self.assertIn("REVIEW_TASKS.md", self.source)
        image = (ROOT / "assets/social-preview.png").read_bytes()
        self.assertEqual(image[:8], b"\x89PNG\r\n\x1a\n")
        self.assertLess(len(image), 1000000)
        self.assertEqual(int.from_bytes(image[16:20], "big"), 1280)
        self.assertEqual(int.from_bytes(image[20:24], "big"), 640)

    def test_displayed_example_is_exact_frozen_table(self):
        table = ExampleTable(self.source).rows
        frozen = json.loads((ROOT / "examples/order8_fff.json").read_text())["table"]
        self.assertEqual(table, frozen)
        result = validate(table)
        self.assertTrue(result["latin"] and result["reduced"] and result["fff"])
        self.assertEqual(result["pattern"], "FFF")
        self.assertEqual([view["pairs_checked"] for view in result["views"].values()], [28] * 3)
        pair = result["views"]["row"]["pairs"][0]
        self.assertEqual(pair["lines"], [0, 1])
        self.assertEqual(pair["cycles"], [[0, 1], [2, 3], [4, 5], [6, 7]])
        for cycle in pair["cycles"]:
            self.assertIn("<span>(" + " ".join(map(str, cycle)) + ")</span>", self.source)
        self.assertIn("One highlighted pair is only an illustration, not the full check", self.source)


if __name__ == "__main__":
    unittest.main()
