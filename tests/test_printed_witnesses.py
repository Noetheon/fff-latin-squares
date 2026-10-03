import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("printed_witnesses", ROOT / "tools/check_printed_witnesses.py")
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class PrintedWitnessTests(unittest.TestCase):
    def test_complete_and_mutated_extractions(self):
        table = json.loads(CHECK.ORDER12.read_text())["table"]
        patterns = json.loads((CHECK.PACKAGE / "evidence/pattern_witnesses.json").read_text())
        rows = "\n".join(" ".join(map(str, [i, *row])) for i, row in enumerate(table))
        encoded = "\n".join(key + value for key, value in patterns.items())
        self.assertEqual(CHECK.check_texts([rows, encoded], table, patterns)["order12_cells_checked"], 144)
        bad_texts = ([rows, encoded, encoded], [rows, encoded[:-1]], [rows, rows, encoded],
                     [rows.replace("0 0 1", "0 1 1", 1), encoded],
                     ["\n".join(rows.splitlines()[:-1]), encoded], [encoded])
        for texts in bad_texts:
            with self.subTest(texts=texts), self.assertRaises(ValueError):
                CHECK.check_texts(texts, table, patterns)


if __name__ == "__main__":
    unittest.main()
