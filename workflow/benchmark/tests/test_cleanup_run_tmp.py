import json
import os
import tempfile
import unittest
from pathlib import Path

from benchmark.scripts.cleanup_run_tmp import cleanup, discover, write_manifest


class CleanupRunTmpTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.runs = Path(self.temporary.name) / "runs"
        self.runs.mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    def make_run(self, name="run", completed=True):
        run = self.runs / "group" / name
        tmp = run / "tmp"
        tmp.mkdir(parents=True)
        (tmp / "large.bin").write_bytes(b"12345")
        provenance = run / "benchmark/provenance.json"
        provenance.parent.mkdir()
        provenance.write_text("{}\n")
        if completed:
            report = run / "output/short_10x/dadec/metaquast/combined_reference/report.tsv"
            report.parent.mkdir(parents=True)
            report.write_text("metric\tvalue\n")
        return run

    def test_dry_run_classifies_and_preserves(self):
        complete = self.make_run("complete")
        incomplete = self.make_run("incomplete", completed=False)
        manifest = cleanup(self.runs)
        self.assertEqual(manifest["selected_count"], 1)
        self.assertEqual(manifest["selected_bytes"], 5)
        self.assertTrue((complete / "tmp").is_dir())
        self.assertTrue((incomplete / "tmp").is_dir())

    def test_apply_deletes_only_completed_by_default(self):
        complete = self.make_run("complete")
        incomplete = self.make_run("incomplete", completed=False)
        manifest = cleanup(self.runs, apply=True)
        self.assertEqual(manifest["selected_count"], 1)
        self.assertFalse((complete / "tmp").exists())
        self.assertTrue((incomplete / "tmp").is_dir())
        self.assertTrue((complete / "benchmark/provenance.json").is_file())

    def test_incomplete_deletion_is_explicit(self):
        run = self.make_run(completed=False)
        cleanup(self.runs, apply=True, include_incomplete=True)
        self.assertFalse((run / "tmp").exists())

    def test_apply_can_resume_baseline(self):
        run = self.make_run()
        baseline = cleanup(self.runs)
        cleanup(self.runs, apply=True)
        resumed = cleanup(self.runs, apply=True, entries=baseline["entries"])
        self.assertEqual(resumed["selected_count"], 1)
        self.assertEqual(resumed["entries"][0]["action"], "already_deleted")
        self.assertFalse((run / "tmp").exists())

    def test_missing_provenance_is_rejected(self):
        run = self.make_run()
        (run / "benchmark/provenance.json").unlink()
        with self.assertRaises(FileNotFoundError):
            discover(self.runs)

    def test_symlink_is_rejected(self):
        run = self.make_run()
        for path in (run / "tmp").iterdir():
            path.unlink()
        (run / "tmp").rmdir()
        target = Path(self.temporary.name) / "target"
        target.mkdir()
        os.symlink(target, run / "tmp")
        with self.assertRaises(ValueError):
            discover(self.runs)

    def test_manifest_is_written_atomically(self):
        self.make_run()
        path = Path(self.temporary.name) / "manifest.json"
        manifest = cleanup(self.runs)
        write_manifest(path, manifest)
        self.assertEqual(json.loads(path.read_text())["selected_count"], 1)
        self.assertFalse(path.with_suffix(".json.tmp").exists())


if __name__ == "__main__":
    unittest.main()
