import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "scripts/compact_quast.py"
spec = importlib.util.spec_from_file_location("compact_quast", path)
cleanup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cleanup)


class QuastCleanupTests(unittest.TestCase):
    def test_dry_run_and_apply_preserve_primary_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "metaquast"
            report = root / "combined_reference/report.tsv"
            large = root / "combined_reference/contigs_reports/minimap_output/corrected.coords_tmp"
            small = root / "combined_reference/quast.log"
            large.parent.mkdir(parents=True)
            report.write_text("Assembly\tcorrected\n")
            small.write_text("log\n")
            large.write_bytes(b"x" * 2048)
            dry = cleanup.compact_roots([root], threshold_mib=0.001, apply=False)
            self.assertEqual(dry["file_count"], 1)
            self.assertTrue(large.exists())
            applied = cleanup.compact_roots([root], threshold_mib=0.001, apply=True)
            self.assertEqual(applied["file_count"], 1)
            self.assertFalse(large.exists())
            self.assertTrue(report.exists())
            self.assertTrue(small.exists())

    def test_missing_report_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "quast"
            root.mkdir()
            (root / "large.bin").write_bytes(b"x" * 2048)
            with self.assertRaises(FileNotFoundError):
                cleanup.compact_roots([root], threshold_mib=0.001, apply=True)


if __name__ == "__main__":
    unittest.main()
