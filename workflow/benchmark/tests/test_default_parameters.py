import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "work_scripts/default_parameters"
sys.path.insert(0, str(SCRIPT_DIR))

import compare
import core
import runner


class TargetMatrixTests(unittest.TestCase):
    def test_matrix_has_25_groups_and_75_unique_targets(self):
        targets = core.build_targets()
        self.assertEqual(len(targets), 75)
        self.assertEqual(len({target.key for target in targets}), 75)
        self.assertEqual(
            {method: sum(target.method == method for target in targets) for method in core.METHOD_ORDER},
            {"fmlrc": 25, "ratatosk": 25, "lordec": 25},
        )

    def test_experiment_default_parameters_and_ecoli_labels(self):
        targets = core.build_targets()
        by_key = {target.key: target for target in targets}
        self.assertEqual(by_key[("30strains", "10x", "fmlrc")].signature, "k21_k59")
        self.assertEqual(by_key[("30strains", "10x", "ratatosk")].signature, "k31_k63")
        self.assertEqual(by_key[("30strains", "10x", "lordec")].signature, "k19_ls5")
        self.assertEqual(by_key[("ecoli_error", "20x", "lordec")].run_label, "miseq")
        self.assertEqual(by_key[("ecoli_error", "23x", "lordec")].run_label, "hiseq")

    def test_generated_config_has_stable_identity(self):
        target = next(
            target for target in core.build_targets()
            if target.key == ("30strains", "10x", "lordec")
        )
        text = core.generated_job_config(target)
        self.assertIn("parameter_set: tool_default", text)
        self.assertIn("lordec_k: 19", text)
        self.assertIn("lordec_solid: 5", text)


class SemanticAuditTests(unittest.TestCase):
    def target(self, root):
        return core.Target(
            dataset="ecoli_error", coverage="20x", run_label="miseq",
            method="fmlrc", parameters={"fmlrc_k1": 21, "fmlrc_k2": 59},
            dataset_config=root / "dataset.yaml", run_config_dir=root / "configs",
            evaluation_tool="quast",
        )

    def candidate(self, root, evaluation_tool="metaquast"):
        provenance = {
            "dataset": "ecoli_error", "methods": ["fmlrc"],
            "evaluation_tool": evaluation_tool, "parameter_set": "original",
            "run_id": "ecoli_error_miseq_fmlrc_original_k21_k59",
            "parameters_by_coverage": {"20x": {"fmlrc_k1": 21, "fmlrc_k2": 59}},
        }
        path = root / "benchmark/provenance.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(provenance))
        return core.RunCandidate(root, path, provenance)

    def write_correction(self, root):
        corrected = root / "output/short_20x/fmlrc/corrected.fa"
        corrected.parent.mkdir(parents=True)
        corrected.write_text(">read\nACGT\n")
        resources = root / "benchmark/short_20x/fmlrc/resources.time.txt"
        resources.parent.mkdir(parents=True)
        resources.write_text(
            "wall_seconds=1\nuser_cpu_seconds=1\nsystem_cpu_seconds=0\n"
            "max_rss_kb=1024\nexit_code=0\n"
        )

    def write_report(self, root):
        report = root / "output/short_20x/fmlrc/quast/report.tsv"
        report.parent.mkdir(parents=True)
        report.write_text(
            "# mismatches per 100 kbp\t1\n# indels per 100 kbp\t2\n"
            "Genome fraction (%)\t99\n# local misassemblies\t0\n# contigs\t3\n"
        )

    def test_original_label_and_historical_evaluator_still_match_parameters(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = self.target(root)
            candidate = self.candidate(root)
            self.assertTrue(core.candidate_matches_target(candidate, target))

    def test_completed_correction_with_new_evaluator_resumes_only_evaluation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = self.target(root)
            candidate = self.candidate(root)
            self.write_correction(root)
            status, _, missing = core.assess_candidate(candidate, target)
            self.assertEqual(status, "resume_evaluation")
            self.assertEqual(missing, ("NA",))
            self.write_report(root)
            status, _, missing = core.assess_candidate(candidate, target)
            self.assertEqual((status, missing), ("complete", ()))


class SelectionAndComparisonTests(unittest.TestCase):
    def test_evaluation_resume_cannot_schedule_correction_rules(self):
        from types import SimpleNamespace
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "job.yaml"
            config.write_text("run: {}\n")
            target = core.Target(
                dataset="ecoli_error", coverage="20x", run_label="miseq",
                method="fmlrc", parameters={"fmlrc_k1": 21, "fmlrc_k2": 59},
                dataset_config=root / "dataset.yaml", run_config_dir=root,
                evaluation_tool="quast",
            )
            record = core.AuditRecord(
                target, "resume_evaluation", "missing report", "existing", config,
                target.run_group, "run", root / "run", 0, ("NA",),
            )
            with patch.object(runner.subprocess, "run", return_value=SimpleNamespace(returncode=0)) as mocked:
                runner.invoke_record(record, root, True, 4, 60, [])
            command = mocked.call_args.args[0]
            self.assertIn("--allowed-rules", command)
            self.assertEqual(command[command.index("--allowed-rules") + 1], "quast_corrected")
            self.assertTrue(any(str(value).endswith("/quast/report.tsv") for value in command))

    def test_shards_are_stable_disjoint_and_complete(self):
        targets = core.build_targets()[:9]
        records = [
            core.AuditRecord(
                target, "new", "test", "generated", None,
                target.run_group, target.generated_run_base + "_" + target.signature,
                Path("/tmp") / target.target_id.replace(":", "_"), 0,
            )
            for target in targets
        ]
        shards = [core.shard_records(records, 3, index) for index in range(3)]
        keys = [{record.target.key for record in shard} for shard in shards]
        self.assertFalse(keys[0] & keys[1] or keys[0] & keys[2] or keys[1] & keys[2])
        self.assertEqual(set.union(*keys), {target.key for target in targets})
        self.assertEqual(
            [[record.target.key for record in shard] for shard in shards],
            [[record.target.key for record in core.shard_records(records, 3, index)] for index in range(3)],
        )

    def test_shard_ownership_does_not_shift_when_jobs_complete(self):
        from types import SimpleNamespace

        targets = core.build_targets()[:6]
        records = [
            core.AuditRecord(
                target, "new", "test", "generated", None,
                target.run_group, target.generated_run_base + "_" + target.signature,
                Path("/tmp") / target.target_id.replace(":", "_"), 0,
            )
            for target in targets
        ]
        args = SimpleNamespace(
            dataset=[], priority="all", shard_count=2, shard_index=1, limit=None,
        )
        before = [record.target.key for record in runner.select_pending(records, args)]
        shard_zero = core.shard_records(records, 2, 0)
        for record in shard_zero:
            record.status = "complete"
        after = [record.target.key for record in runner.select_pending(records, args)]
        self.assertEqual(before, after)

    def test_quality_order_and_group_decisions(self):
        base = {
            "haplotype_coverage_percent": 99,
            "mismatches_per_100_kbp": 2,
            "indels_per_100_kbp": 3,
            "local_misassemblies": 1,
            "contigs_number": 4,
            "WallTime(h)": 5,
        }
        better = dict(base, haplotype_coverage_percent=99.1)
        self.assertLess(compare.quality_key(better), compare.quality_key(base))
        self.assertEqual(compare.decide_score_statuses(["default_better"]), "default_better")
        self.assertEqual(compare.decide_score_statuses(["tie"]), "not_better")
        self.assertEqual(compare.decide_score_statuses(["no_comparator"]), "no_comparator")
        self.assertEqual(
            compare.decide_score_statuses(["default_better", "not_better"]),
            "mixed_scores",
        )


if __name__ == "__main__":
    unittest.main()
