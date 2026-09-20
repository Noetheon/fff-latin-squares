import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("demo", ROOT / "tools/demo_fff.py")
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


class DemoTests(unittest.TestCase):
    def test_explicit_table_matches_written_construction(self):
        table = json.loads((ROOT / "examples/order8_fff.json").read_text())["table"]
        generated = [[2 * ((x // 2 + y // 2) % 4)
                      + ((x % 2 + y % 2 + (x // 2 == y // 2 == 1)) % 2)
                      for y in range(8)] for x in range(8)]
        self.assertEqual(table, generated)
        result = demo.validate(table)
        self.assertTrue(result["fff"])
        self.assertTrue(result["reduced"])
        self.assertEqual([v["pairs_checked"] for v in result["views"].values()], [28]*3)
        self.assertTrue(all(len(c) % 2 == 0 for view in result["views"].values()
                            for pair in view["pairs"] for c in pair["cycles"]))

    def test_negative_control_has_real_odd_witnesses(self):
        table = [[(r+c) % 3 for c in range(3)] for r in range(3)]
        result = demo.validate(table)
        self.assertEqual(result["pattern"], "TTT")
        for view in result["views"].values():
            self.assertTrue(all(len(p["odd_cycles"]) == 1 for p in view["pairs"]))

    def test_matching_equations_all_three_views(self):
        table = json.loads((ROOT / "examples/order8_fff.json").read_text())["table"]
        report = demo.validate(table)
        for view, data in report["views"].items():
            for pair in data["pairs"]:
                a, b = pair["lines"]
                for x, y in enumerate(pair["permutation"]):
                    if view == "row":
                        self.assertEqual(table[a][x], table[b][y])
                    elif view == "col":
                        self.assertEqual(table[x][a], table[y][b])
                    else:
                        r = next(r for r in range(len(table)) if table[r][x] == a)
                        self.assertEqual(table[r][y], b)

    def test_cyclic_even_group_is_not_necessarily_fff(self):
        self.assertEqual(demo.validate([[(r+c) % 6 for c in range(6)]
                                        for r in range(6)])["pattern"], "TTT")
        self.assertTrue(demo.validate([[(r+c) % 4 for c in range(4)]
                                       for r in range(4)])["fff"])

    def test_invalid_tables_fail_closed(self):
        for table in ([], [[0,1]], [[0,0],[1,1]], [[0,1],[0,1]],
                      [[0,2],[2,0]], [[False]], [[0.0]], "not a table"):
            with self.subTest(table=table), self.assertRaises(ValueError):
                demo.validate(table)

    def test_expected_reports_and_hashes(self):
        expected = json.loads((ROOT / "examples/expected_results.json").read_text())
        for filename, saved in expected.items():
            payload = (ROOT / "examples" / filename).read_bytes()
            actual = demo.validate(json.loads(payload)["table"])
            actual["input_sha256"] = hashlib.sha256(payload).hexdigest()
            self.assertEqual(actual, saved)


if __name__ == "__main__":
    unittest.main()
