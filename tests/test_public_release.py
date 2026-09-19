import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("verify", ROOT / "tools/verify_public_release.py")
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)


class PublicReleaseTests(unittest.TestCase):
    def test_manifest_rejects_traversal_and_duplicates(self):
        digest = "a" * 64
        for text in (f"{digest}  ../outside\n", f"{digest}  /absolute\n",
                     f"{digest}  a\n{digest}  a\n", "bad  a\n"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                verify.parse_manifest(text)

    def test_manifest_tracks_bytes_and_unexpected_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "note.txt").write_text("Research only.\n")
            digest = hashlib.sha256((root / "note.txt").read_bytes()).hexdigest()
            (root / "PUBLIC_MANIFEST.sha256").write_text(f"{digest}  note.txt\n")
            self.assertTrue(verify.verify(root)["passed"])
            (root / "note.txt").write_text("changed")
            self.assertFalse(verify.verify(root)["passed"])
            (root / "extra.txt").write_text("untracked")
            self.assertIn("Unexpected: extra.txt", verify.verify(root)["failures"])

    def test_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "PUBLIC_MANIFEST.sha256").write_text("")
            (root / "link").symlink_to("missing")
            with self.assertRaises(ValueError):
                verify.verify(root)

    def test_real_public_manifest(self):
        self.assertTrue(verify.verify(ROOT)["passed"])


if __name__ == "__main__":
    unittest.main()
