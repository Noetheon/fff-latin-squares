"""Adversarial controls for the derivative audit, not new mathematical claims."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "verification/audits/2026-09-28_dossier_hardened"
SPEC = importlib.util.spec_from_file_location("compare_outputs", AUDIT / "scripts/compare_outputs.py")
COMPARE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(COMPARE)


class HardenedAuditTests(unittest.TestCase):
    def test_all_frozen_source_hashes(self):
        self.assertGreaterEqual(COMPARE.verify_source_manifest(AUDIT), 54)

    def test_all_python_assertion_entrypoints_reject_optimization(self):
        entries = list((AUDIT / "rerun/code").glob("*.py")) + [
            AUDIT / "rerun/run_all.py", AUDIT / "scripts/burnside_new.py",
            AUDIT / "scripts/reproduce_all.py",
        ]
        for entry in entries:
            for optimized in (["-O"], ["-OO"]):
                with self.subTest(entry=entry.name, optimized=optimized):
                    process = subprocess.run([sys.executable, "-B", *optimized, str(entry)],
                                             text=True, capture_output=True, timeout=10)
                    self.assertNotEqual(process.returncode, 0)
                    self.assertIn("optimized Python is not supported", process.stderr)
        process = subprocess.run([sys.executable, "-B", str(AUDIT / "rerun/code/check_report_values.py")],
                                 env=dict(os.environ, PYTHONOPTIMIZE="1"),
                                 text=True, capture_output=True, timeout=10)
        self.assertNotEqual(process.returncode, 0)
        self.assertIn("optimized Python is not supported", process.stderr)

    def test_corrupted_scientific_count_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(AUDIT / "rerun/code", root / "code")
            shutil.copytree(AUDIT / "rerun/results", root / "results")
            report = root / "results/report_value_checks.json"
            report.unlink()
            path = root / "results/smallorders_and_flags.json"
            value = json.loads(path.read_text())
            value["smallorders"]["2"]["total"] = 2
            path.write_text(json.dumps(value))
            process = subprocess.run([sys.executable, "-B", str(root / "code/check_report_values.py")],
                                     text=True, capture_output=True, timeout=10)
            self.assertNotEqual(process.returncode, 0)
            self.assertFalse(report.exists())

    def test_comparison_only_ignores_named_runtime_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(AUDIT / "results", root / "results")
            shutil.copytree(AUDIT / "rerun/results", root / "rerun/results")
            self.assertTrue(COMPARE.compare(AUDIT, root)["passed"])
            path = root / "results/burnside_and_arithmetic.json"
            value = json.loads(path.read_text())
            value["seconds"] += 123
            path.write_text(json.dumps(value, sort_keys=True))
            self.assertTrue(COMPARE.compare(AUDIT, root)["passed"])
            value["groups"][0]["bounds"]["1703"] += 1
            path.write_text(json.dumps(value))
            self.assertFalse(COMPARE.compare(AUDIT, root)["passed"])
            process = subprocess.run([sys.executable, "-B", str(AUDIT / "scripts/compare_outputs.py"),
                                      "--reference", str(AUDIT), "--fresh", str(root),
                                      "--output", str(root / "comparison.json")],
                                     capture_output=True, timeout=10)
            self.assertNotEqual(process.returncode, 0)
            path.unlink()
            self.assertFalse(COMPARE.compare(AUDIT, root)["passed"])

    def test_missing_runtime_or_reordered_arrays_are_not_normalized(self):
        name = "results/burnside_and_arithmetic.json"
        value = json.loads((AUDIT / name).read_text())
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "result.json"
            value["groups"].reverse()
            path.write_text(json.dumps(value))
            self.assertNotEqual(COMPARE.normalized(path, name), COMPARE.normalized(AUDIT / name, name))
            del value["seconds"]
            path.write_text(json.dumps(value))
            with self.assertRaises(KeyError):
                COMPARE.normalized(path, name)

    def test_inherited_runner_propagates_child_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "code").mkdir()
            (root / "results").mkdir()
            shutil.copy2(AUDIT / "rerun/run_all.py", root / "run_all.py")
            (root / "code/core_checks.py").write_text("raise SystemExit(7)\n")
            process = subprocess.run([sys.executable, "-B", str(root / "run_all.py")],
                                     capture_output=True, timeout=10)
            self.assertEqual(process.returncode, 7)
            records = json.loads((root / "results/execution_log.json").read_text())
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["returncode"], 7)

    @unittest.skipUnless(shutil.which("g++"), "C++17 compiler is needed for failure-path injection")
    def test_cpp_inventory_errors_have_failure_exit_status(self):
        source = (AUDIT / "rerun/independent_master_inventory_audit.cpp").read_text()
        for condition, message in (("q[0]<2||q[0]>9", "bad bucket"),
                                   ("it==idx.end()", "orbit image missing")):
            with self.subTest(message=message), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                self.assertEqual(source.count(f"if({condition})"), 1)
                (root / "test.cpp").write_text(source.replace(f"if({condition})", "if(true)"))
                subprocess.run(["g++", "-O2", "-std=c++17", str(root / "test.cpp"),
                                "-o", str(root / "checker")], check=True, capture_output=True, timeout=60)
                process = subprocess.run([str(root / "checker")], capture_output=True,
                                         text=True, timeout=30)
                self.assertNotEqual(process.returncode, 0)
                self.assertIn(message, process.stderr)

    def test_compact_summary_states_nontrivial_block_hypothesis(self):
        paper = ROOT / "manuscript/candidates/2026-09-28_audit_corrections"
        introduction = (paper / "sections/01_introduction_core.tex").read_text()
        self.assertIn("odd block size greater than one forces TTT", introduction)


if __name__ == "__main__":
    unittest.main()
