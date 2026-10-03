from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import parse_qs, urlsplit
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from demo_fff import validate


class ExampleTable(HTMLParser):
    def __init__(self, source, table_id="example-table"):
        super().__init__()
        self.table_id = table_id
        self.inside = self.cell = False
        self.rows = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        if tag == "table" and dict(attrs).get("id") == self.table_id:
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


class ReaderContent(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.evidence_rows, self.walks = [], {}
        self.current_links = self.current_walk = None
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get("class", "").split()
        if tag == "article" and "evidence-row" in classes:
            self.current_links = []
        if tag == "a" and self.current_links is not None:
            self.current_links.append(attrs)
        if tag == "p" and "cycle-path" in classes:
            self.current_walk = attrs["data-table"]
            self.walks[self.current_walk] = ""

    def handle_data(self, data):
        if self.current_walk is not None:
            self.walks[self.current_walk] += data

    def handle_endtag(self, tag):
        if tag == "article" and self.current_links is not None:
            self.evidence_rows.append(self.current_links)
            self.current_links = None
        if tag == "p":
            self.current_walk = None


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

    def test_repository_document_destinations_and_heading_anchors_exist(self):
        for tag, attrs in self.page.elements:
            link = urlsplit(attrs.get("href", ""))
            prefix = "/Noetheon/fff-latin-squares/"
            if tag != "a" or link.netloc != "github.com" or not link.path.startswith(prefix):
                continue
            parts = link.path.removeprefix(prefix).split("/", 2)
            if parts[0] not in {"blob", "tree"}:
                continue
            with self.subTest(url=attrs["href"]):
                self.assertEqual(parts[1], "main")
                target = ROOT / parts[2]
                self.assertTrue(target.exists(), parts[2])
                if not link.fragment:
                    continue
                self.assertEqual(target.suffix, ".md")
                # These destinations use unique plain ATX headings, not arbitrary HTML.
                headings = re.findall(r"^#{1,6} (.+)$", target.read_text(), re.M)
                slugs = [re.sub(r"[^\w -]", "", h.lower()).replace(" ", "-")
                         for h in headings]
                self.assertEqual(slugs.count(link.fragment), 1, link.fragment)

    def test_all_result_rows_have_direct_evidence_links(self):
        content = ReaderContent(self.source)
        self.assertEqual(len(content.evidence_rows), 9)
        for links in content.evidence_rows:
            self.assertEqual(len(links), 1)
            self.assertIn("evidence-reference", links[0].get("class", "").split())
            self.assertTrue(urlsplit(links[0]["href"]).fragment)

    def test_idea_precedes_papers_and_preserves_construction_scope(self):
        self.assertLess(self.source.index('id="example"'), self.source.index('id="dossiers"'))
        self.assertIn("any two distinct rows, columns or symbols", self.source)
        self.assertIn("For every odd integer m &gt; 1", self.source)
        self.assertIn("not the smallest possible exponent or a decision at order 18", self.source)

    def test_stylesheet_cache_version_matches_content(self):
        styles = [attrs for tag, attrs in self.page.elements
                  if tag == "link" and attrs.get("rel") == "stylesheet"]
        self.assertEqual(len(styles), 1)
        link = urlsplit(styles[0]["href"])
        digest = hashlib.sha256((ROOT / link.path).read_bytes()).hexdigest()[:12]
        self.assertEqual(parse_qs(link.query), {"v": [digest]})

    def test_three_pdf_read_and_download_links(self):
        for filename in ("FFF_Compact_Research_Dossier.pdf", "FFF_Selected_Research_Dossier.pdf", "FFF_Long_Research_Dossier.pdf"):
            links = [attrs for tag, attrs in self.page.elements
                     if tag == "a" and attrs.get("href") == f"papers/{filename}"]
            self.assertTrue(any("download" in attrs for attrs in links))
            self.assertTrue(any("download" not in attrs and "aria-hidden" not in attrs for attrs in links))

    def test_evidence_and_origin_boundary_retained(self):
        for required in ("Not peer reviewed", "ChatGPT/Codex", "disproving the former power-of-two conjecture C38",
                         "Order 18 remains open", "No accountable scholarly author", "Rights remain reserved",
                         "not independent studies", "not a solver-free proof"):
            self.assertIn(required, self.source)
        self.assertIn("<details open>", self.source)
        self.assertIn("46 pages / PDF", self.source)
        self.assertIn("12 pages / PDF", self.source)
        self.assertIn("THEOREM_EVIDENCE.md", self.source)
        self.assertIn("91 pages / PDF", self.source)
        self.assertIn("through C280", self.source)
        for stale in ("38 pages / PDF", "42 pages / PDF", "80 pages / PDF",
                      "87 pages / PDF", "88 pages / PDF", "through C271"):
            self.assertNotIn(stale, self.source)
        self.assertNotIn("The global conjecture remains open", self.source)

    def test_current_snapshot_metadata(self):
        dates = [attrs.get("datetime") for tag, attrs in self.page.elements if tag == "time"]
        self.assertIn("2026-10-02", dates)
        self.assertIn("2026-10-02T14:03:38Z", dates)
        self.assertIn("2026-09-30T12:54:17Z", dates)
        metadata = {attrs.get("property", attrs.get("name")): attrs.get("content")
                    for tag, attrs in self.page.elements if tag == "meta"}
        for key in ("description", "og:description", "twitter:description"):
            with self.subTest(metadata=key):
                for required in ("2 October 2026", "C280", "2026-09-30T12:54:17Z", "2026-10-02T14:03:38Z",
                                 "Not peer reviewed", "order 18 remains open"):
                    self.assertIn(required.lower(), metadata[key].lower())

    def test_structural_and_count_coverage_boundaries(self):
        for required in ("31 dual-positive or 13 longest-cycle cases, not solved cases",
                         "column positivity is not imposed on the latter",
                         "same projected two-plex", "Different-projection pairs",
                         "72,474,624 labelled first transversals",
                         "18,118,656 free-four representatives, not main classes",
                         "Only 18 selected supports / 9,216 labelled firsts",
                         "138,468 liftable supports remain unexcluded by those packages",
                         "not every local radius or mate payload or fresh historical DRAT replay",
                         "1,703 represented classes", "1,450,956 at order 40"):
            with self.subTest(boundary=required):
                self.assertIn(required, self.source)

    def test_current_facades_point_to_same_snapshot(self):
        for filename in ("README.md", "EVIDENCE_STATUS.md", "REPRODUCIBILITY.md",
                         "WEBSITE.md", "REVIEW_TASKS.md"):
            with self.subTest(file=filename):
                source = (ROOT / filename).read_text()
                self.assertIn("2026-09-30T12:54:17Z", source)
                self.assertIn("C280", source)
                self.assertIn("2026-10-02T14:03:38Z", source)
                self.assertIn("manuscript/candidates/2026-09-30_research_review/", source)
                self.assertNotIn("/Users/", source)
                self.assertNotIn("/home/", source)
        for filename in ("README.md", "REPRODUCIBILITY.md"):
            with self.subTest(commands=filename):
                source = (ROOT / filename).read_text()
                self.assertIn("tools/check_current_snapshot.py", source)
                self.assertIn("audit_new_results.py", source)
                self.assertIn("--with-cpp", source)
        reproduction = (ROOT / "REPRODUCIBILITY.md").read_text()
        self.assertIn("--compare manuscript/candidates/2026-09-30_research_review/results/portable_audit.json",
                      reproduction)

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

    def test_displayed_negative_control_is_exact_frozen_table(self):
        table = ExampleTable(self.source, "negative-table").rows
        frozen = json.loads((ROOT / "examples/order3_nonfff.json").read_text())["table"]
        self.assertEqual(table, frozen)
        result = validate(table)
        self.assertTrue(result["latin"] and result["reduced"])
        self.assertFalse(result["fff"])
        self.assertEqual(result["pattern"], "TTT")
        self.assertEqual([view["pairs_checked"] for view in result["views"].values()], [3] * 3)

    def test_visible_cycle_walks_follow_the_actual_matching(self):
        walks = ReaderContent(self.source).walks
        self.assertEqual(set(walks), {"example-table", "negative-table"})
        for table_id, text in walks.items():
            with self.subTest(table=table_id):
                table = ExampleTable(self.source, table_id).rows
                walk = [int(point.strip()) for point in text.split("\N{RIGHTWARDS ARROW}")]
                pair = validate(table)["views"]["row"]["pairs"][0]
                self.assertEqual(pair["lines"], [0, 1])
                self.assertEqual(walk[0], walk[-1])
                self.assertEqual(len(set(walk[:-1])), len(walk) - 1)
                for source, target in zip(walk, walk[1:]):
                    self.assertEqual(pair["permutation"][source], target)
                    self.assertEqual(table[0][source], table[1][target])
                self.assertEqual(walk, [0, 1, 0] if table_id == "example-table" else [0, 2, 1, 0])


if __name__ == "__main__":
    unittest.main()
