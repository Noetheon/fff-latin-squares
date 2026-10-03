import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


JSON = load("json_comparison", "audit_json.py")
AUDIT = load("audit_comparison", "compare_external_audit_20261003.py")


class StrictAuditComparisonTests(unittest.TestCase):
    def test_missing_is_not_null_in_either_direction(self):
        for left, right in (({}, {"x": None}), ({"x": None}, {}),
                            ({"a": [{"x": None}]}, {"a": [{}]})):
            self.assertTrue(JSON.differences(left, right))

    def test_type_is_not_python_numeric_equality(self):
        for left, right in ((True, 1), (False, 0), (1, 1.0), ([1], [True]), ([], {})):
            self.assertTrue(JSON.differences(left, right))

    def test_list_order_length_and_key_order(self):
        self.assertTrue(JSON.differences([1, 2], [2, 1]))
        self.assertTrue(JSON.differences([None], []))
        self.assertEqual(JSON.differences({"a": 1, "b": []}, {"b": [], "a": 1}), [])

    def test_duplicate_keys_and_nonfinite_numbers_rejected(self):
        for text in ('{"x":1,"x":1}', '{"a":{"x":null,"x":1}}',
                     "NaN", "Infinity", "-Infinity", "1e999"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                JSON.loads(text)
        for value in (float("nan"), float("inf"), {1: 2}, (1, 2)):
            with self.assertRaises(ValueError):
                JSON.differences(value, value)

    def test_declared_timing_only(self):
        a, b = {"seconds": 1.0, "count": 7}, {"seconds": 3.5, "count": 7}
        self.assertEqual(AUDIT.compare_record("current", "e9_independent.json", a, b), ["seconds"])
        for bad in ({"count": 7}, {"seconds": None, "count": 7},
                    {"seconds": True, "count": 7}, {"seconds": -1, "count": 7},
                    {"seconds": 1.0, "count": True}, {"seconds": 1.0, "count": 8},
                    {"seconds": 1.0, "count": 7, "extra": None}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                AUDIT.compare_record("current", "e9_independent.json", a, bad)

    def test_optional_pdf_status_not_silently_removed_when_absent(self):
        a = {"displayed_L12_bindings": [], "passed": True}
        b = {"displayed_L12_bindings": "missing optional dependency", "passed": True}
        saved = copy.deepcopy(a)
        self.assertEqual(len(AUDIT.compare_record("current", "compact_new_controls.json", a, b)), 1)
        self.assertEqual(a, saved)
        with self.assertRaises(ValueError):
            AUDIT.compare_record("current", "compact_new_controls.json", a, {"passed": True})

    def test_no_wildcard_exclusions_or_unreviewed_file(self):
        for scope, name in (("current", "order36.json"), ("current", "core_checks.json")):
            with self.assertRaises(ValueError):
                AUDIT.compare_record(scope, name, {"seconds": 1}, {"seconds": 2})

    def test_frozen_manifest_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "MANIFEST.sha256").write_text("not the pinned manifest\n")
            with self.assertRaises(ValueError):
                AUDIT.verify_package(root)

    def test_symlink_traversal_and_missing_output_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "file").write_text("{}")
            (root / "link").symlink_to(root / "file")
            for name in ("../file", "/absolute", "./file", "link", "missing"):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    AUDIT.regular_file(root, name)


if __name__ == "__main__":
    unittest.main()
