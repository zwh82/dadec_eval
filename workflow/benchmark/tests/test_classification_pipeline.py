import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts/classification/scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import common
import compare_reports
import evaluate


class ClassificationConfigTests(unittest.TestCase):
    def test_30strains_legacy_config_defaults_to_10x(self):
        config = common.load_config(ROOT / "config/classification/30strains_legacy.yaml")
        self.assertEqual(common.selected_coverages(config), ["10x"])
        self.assertEqual(common.selected_coverages(config, "20x,30x"), ["20x", "30x"])
        self.assertIn(("10x", "fmlrc_current"), common.configured_classify_samples(config, ["10x"]))
        self.assertIn(("10x", "dadec_dev"), common.configured_classify_samples(config, ["10x"]))
        self.assertIn(("10x", "lordec"), common.configured_classify_samples(config, ["10x"]))
        self.assertIn(("30x", "dadec"), common.configured_classify_samples(config, ["30x"]))

    def test_legacy_guardrails_reject_nonlegacy_paths(self):
        config = {
            "dataset_id": "30strains_legacy",
            "run_config_dir": "benchmark/config/runs/30strains",
            "coverages": {
                "10x": {
                    "fmlrc": {"corrected_fasta": "benchmark/runs/30strains_10x/x.fa", "run_id": "30strains_10x_fmlrc"},
                    "dadec_dev": {"corrected_fasta": "benchmark/runs/30strains_legacy_10x/y.fa", "run_id": "30strains_legacy_10x_dadec"},
                    "classify": {
                        "lordec": {
                            "corrected_fasta": "benchmark/runs/30strains_10x/l.fa",
                            "run_id": "30strains_10x_lordec",
                        }
                    },
                }
            },
        }
        errors = []
        common.validate_legacy_guardrails(config, ["10x"], errors)
        self.assertTrue(any("run_config_dir" in error for error in errors))
        self.assertTrue(any("fmlrc fasta" in error for error in errors))
        self.assertTrue(any("classify.lordec fasta" in error for error in errors))


class ReportComparisonTests(unittest.TestCase):
    def write_report(self, path, num_reads):
        path.write_text(
            "name\ttaxID\ttaxRank\tgenomeSize\tnumReads\tnumUniqueReads\tabundance\n"
            f"Escherichia coli\t562\tspecies\t100\t{num_reads}\t{num_reads}\t0.5\n"
        )

    def test_exact_report_match_and_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            a = root / "a.tsv"
            b = root / "b.tsv"
            c = root / "c.tsv"
            self.write_report(a, 10)
            self.write_report(b, 10)
            self.write_report(c, 11)
            self.assertTrue(compare_reports.compare_reports(a, b)["match"])
            mismatch = compare_reports.compare_reports(a, c)
            self.assertFalse(mismatch["match"])
            self.assertEqual(mismatch["diffs"][0]["kind"], "row_mismatch")


class AssignmentScoringTests(unittest.TestCase):
    def test_truth_group_macro_metrics_match_historical_shape(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assignment = root / "assignments.tsv"
            assignment.write_text(
                "readID\tseqID\ttaxID\tscore\t2ndBestScore\thitLength\tqueryLength\tnumMatches\n"
                "A-1\tA\t1\t0\t0\t0\t0\t1\n"
                "A-2\tB\t2\t0\t0\t0\t0\t1\n"
                "B-1\tB\t2\t0\t0\t0\t0\t1\n"
            )
            groups = [{"A"}, {"B"}]
            result = evaluate.score_assignment(assignment, groups)
            self.assertEqual(result["total_assignments"], 3)
            self.assertAlmostEqual(result["accuracy"], 2 / 3)
            self.assertAlmostEqual(result["precision"], (1.0 + 0.5) / 2)
            self.assertAlmostEqual(result["recall"], (0.5 + 1.0) / 2)
            self.assertAlmostEqual(result["F1"], 0.75)
            self.assertAlmostEqual(result["macro_precision"], 0.75)
            self.assertAlmostEqual(result["macro_recall"], 0.75)
            self.assertAlmostEqual(result["macro_F1"], 0.75)
            self.assertAlmostEqual(result["micro_precision"], 2 / 3)
            self.assertAlmostEqual(result["micro_recall"], 2 / 3)
            self.assertAlmostEqual(result["micro_F1"], 2 / 3)
            self.assertAlmostEqual(result["micro_accuracy"], 2 / 3)
            self.assertEqual(result["total_TP"], 2)
            self.assertEqual(result["total_FP"], 1)
            self.assertEqual(result["total_FN"], 1)


if __name__ == "__main__":
    unittest.main()
