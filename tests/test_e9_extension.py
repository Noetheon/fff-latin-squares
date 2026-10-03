"""Fail-closed scope, control comparison and successor checks for the E9 edition."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "manuscript/candidates/2026-10-02_e9_symmetry_review"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BUILD = load("e9_build", PACKAGE / "scripts/build_editions.py")
CHECK = load("e9_check", ROOT / "tools/check_e9_symmetry.py")
FINITE = load("e9_finite", PACKAGE / "scripts/enumerate_s6.py")


class E9ExtensionTests(unittest.TestCase):
    def test_reversible_overlay_and_one_shared_proof(self):
        with tempfile.TemporaryDirectory() as temporary:
            for variant in ("compact", "selected", "long"):
                target = Path(temporary) / variant
                result = BUILD.assemble(target, variant)
                for relative, digest in result["predecessor"]["assembled_sources_sha256"].items():
                    text = (target / relative).read_text()
                    for change in reversed(result["e9_changes"]):
                        if change["file"] == relative:
                            self.assertEqual(text.count(change["after"]), 1)
                            text = text.replace(change["after"], change["before"])
                    self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), digest, relative)
                section = target / "sections/19_e9_free_coordinates.tex"
                self.assertEqual(section.exists(), variant != "compact")
                if section.exists():
                    self.assertEqual(section.read_bytes(), (PACKAGE / "sections" / section.name).read_bytes())

    def test_control_ignores_only_declared_runtime_fields(self):
        reference = json.loads((PACKAGE / "results/enumeration_results.json").read_text())
        changed = json.loads(json.dumps(reference))
        changed["runtime"]["elapsed_seconds_before_serialization"] += 1
        changed["runtime"]["python"] = "other-version"
        self.assertEqual(CHECK.scientific(reference), CHECK.scientific(changed))
        for key, value in (("two_3+3_fixed_point_free_even_cycled_count", 1), ("status", "FAIL")):
            changed = json.loads(json.dumps(reference))
            changed[key] = value
            self.assertNotEqual(CHECK.scientific(reference), CHECK.scientific(changed))
        changed = json.loads(json.dumps(reference))
        changed["runtime"]["source_sha256"] = "0" * 64
        self.assertNotEqual(CHECK.scientific(reference), CHECK.scientific(changed))

    def test_exact_mixed_countercontrol(self):
        alpha = (3, 0, 2, 1, 4, 5)
        beta = (1, 2, 0, 4, 5, 3)
        self.assertEqual(FINITE.checked_product(alpha, beta), (2, 3, 0, 5, 1, 4))
        control = FINITE.mixed_rectangle_control(beta, alpha)
        self.assertEqual(control["rows"], [(0, 1, 2, 3, 4, 5), (2, 4, 0, 1, 5, 3), (5, 2, 1, 0, 3, 4)])
        self.assertTrue(all(row["relative_type"] == "4+2" for row in control["pair_controls"]))
        with self.assertRaises(RuntimeError):
            FINITE.mixed_rectangle_control(beta, beta)

    def test_complete_compiled_index_and_scope(self):
        index = json.loads((PACKAGE / "THEOREM_EVIDENCE.json").read_text())
        self.assertEqual(index["compiled_label_count"], 106)
        self.assertEqual(len({r["label"] for r in index["records"]}), 106)
        added = {r["label"]: r for r in index["records"] if ":e9-" in r["label"]}
        self.assertEqual(set(added), {"lem:e9-six-point-product", "thm:e9-two-free-coordinates", "cor:e9-three-view-freeness"})
        self.assertTrue(all(set(row["editions"]) == {"selected", "long"} for row in added.values()))
        text = (PACKAGE / "sections/19_e9_free_coordinates.tex").read_text()
        for boundary in ("actual", "row-F", "not an FFF18 table", "order $18$ remains open", "No column-F or symbol-F quotient"):
            self.assertIn(boundary, text)

    def test_current_links_are_local_and_resolve(self):
        for document in PACKAGE.glob("*.md"):
            for link in re.findall(r"\[[^\]]+\]\(([^()\s]+)\)", document.read_text()):
                if "://" in link or link.startswith("#"):
                    continue
                target = (document.parent / link.split("#", 1)[0]).resolve()
                self.assertTrue(target.is_relative_to(ROOT), link)
                self.assertTrue(target.exists(), link)


if __name__ == "__main__":
    unittest.main()
