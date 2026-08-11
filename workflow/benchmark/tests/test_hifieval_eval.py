import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import run_hifieval_eval as runner
import collect_hifieval_results as collector


BASE_HEADER = (
    "error_type\tchrName\traw_errors\tcorrected_errors\toc\tcc\tuc"
    "\tFDR\tFNR\tTPR\n"
)


class HifievalEvaluationTests(unittest.TestCase):
    def test_header_normalization_and_truth_sampling(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fasta = root / "reads.fa"
            maf = root / "truth.maf"
            fasta.write_text(">S1_1:reference description\nACGT\n>S1_2:reference\nACGT\n")
            maf.write_text(
                "a\ns ref 0 4 + 10 ACGT\ns S1_1 0 4 + 4 ACGT\n\n"
                "a\ns ref 4 4 + 10 ACGT\ns S1_2 0 4 + 4 ACGT\n"
            )
            self.assertEqual(
                runner.sample_fasta_ids(fasta, "strip_after_colon"),
                ["S1_1", "S1_2"],
            )
            self.assertEqual(
                runner.sample_maf_read_ids(maf), ["S1_1", "S1_2"]
            )
            found, inspected = runner.match_maf_read_ids(maf, {"S1_2"})
            self.assertEqual(found, {"S1_2"})
            self.assertEqual(inspected, 2)

    def test_stream_clean_fasta_preserves_sequence_and_removes_suffix(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input.fa"
            output = root / "output.fa"
            source.write_text(">read1:ref extra text\nACGT\n>read2:ref\nTGCA\n")
            runner.stream_clean_fasta(source, output, "strip_after_colon")
            self.assertEqual(output.read_text(), ">read1\nACGT\n>read2\nTGCA\n")

    def make_executable(self, path, body):
        path.write_text("#!{}\n{}".format(sys.executable, body))
        path.chmod(0o755)

    def make_fixture(self, root):
        corrected = root / "corrected.fa"
        raw_paf = root / "raw.paf"
        reference = root / "reference.fa"
        maf = root / "truth.maf"
        corrected.write_text(">read1:reference\nACGT\n")
        raw_paf.write_text(
            "read1\t4\t0\t4\t+\tref\t4\t0\t4\t4\t4\t60\tcs:Z::4\n"
        )
        reference.write_text(">ref\nACGT\n")
        maf.write_text("a\ns ref 0 4 + 4 ACGT\ns read1 0 4 + 4 ACGT\n")

        minimap2 = root / "fake_minimap2.py"
        self.make_executable(
            minimap2,
            "import sys\n"
            "if '--version' in sys.argv:\n"
            "    print('fake-minimap2 1.0')\n"
            "else:\n"
            "    print('read1\\t4\\t0\\t4\\t+\\tref\\t4\\t0\\t4\\t4\\t4\\t60\\tcs:Z::4')\n",
        )
        hifieval = root / "fake_hifieval.py"
        self.make_executable(
            hifieval,
            "import pathlib, sys\n"
            "prefix = pathlib.Path(sys.argv[sys.argv.index('-o') + 1])\n"
            "for suffix in ('.summary.tsv', '.rdlvl.eval.tsv', '.metric.eval.tsv', '.hp.bed'):\n"
            "    pathlib.Path(str(prefix) + suffix).write_text('fixture\\n')\n"
            "base = {!r} + 'all\\tall\\t0\\t0\\t0\\t0\\t0\\t0.0\\t0.0\\t0.0\\n'\n"
            "pathlib.Path(str(prefix) + '.base.eval.tsv').write_text(base)\n"
            "pathlib.Path(str(prefix) + '.hp.ErrorRate.tsv').write_text('#HP Len\\tOC rate\\tUC rate\\n2\\t0.0\\t0.0\\n')\n".format(
                BASE_HEADER
            ),
        )
        readseval = root / "fake_readseval.py"
        self.make_executable(
            readseval,
            "import pathlib, sys\n"
            "prefix = pathlib.Path(sys.argv[sys.argv.index('-o') + 1])\n"
            "base = {!r} + 'all\\tall\\t0\\t0\\t0\\t0\\t0\\t0.0\\t0.0\\t0.0\\n'\n"
            "pathlib.Path(str(prefix) + '.base.eval.tsv').write_text(base)\n"
            "pathlib.Path(str(prefix) + '.read.eval.tsv').write_text("
            "'metric\\tcount\\nread_oc\\t0\\nread_uc\\t0\\nread_cc\\t0\\n')\n".format(
                BASE_HEADER
            ),
        )

        config_path = root / "config.yaml"
        config_path.write_text(
            yaml.safe_dump(
                {
                    "schema_version": 1,
                    "project_root": str(root),
                    "dataset": {"id": "fixture"},
                    "run": {"id": "fixture_fmlrc", "method": "fmlrc"},
                    "inputs": {
                        "corrected_fasta": str(corrected),
                        "raw_paf": str(raw_paf),
                        "reference": str(reference),
                        "truth_maf": str(maf),
                    },
                    "tools": {
                        "minimap2": str(minimap2),
                        "hifieval": str(hifieval),
                        "readseval": str(readseval),
                    },
                    "environment": Path(sys.prefix).name,
                    "threads": 2,
                    "header_transform": "strip_after_colon",
                    "read_mapping_mode": "legacy_endpoint",
                    "min_free_disk_gb": 0,
                    "checksum_inputs": True,
                    "output_dir": str(root / "results"),
                },
                sort_keys=False,
            )
        )
        return runner.load_config(config_path)

    def test_command_matches_historical_minimap2_flags(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.make_fixture(Path(directory))
            command = runner.build_minimap2_command(
                config, config.corrected_fasta, Path("corrected.paf"), 7
            )
            self.assertEqual(command[1:7], ["-t", "7", "-c", "--secondary=no", "--paf-no-hit", "--cs"])
            self.assertEqual(command[-2:], [str(config.reference), str(config.corrected_fasta)])
            read_command = runner.build_readseval_command(
                config, Path("corrected.paf"), Path("filtered")
            )
            self.assertEqual(
                read_command[-2:], ["--mapping-mode", "legacy_endpoint"]
            )

    def test_tiny_pipeline_is_restartable_and_forceable(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.make_fixture(Path(directory))
            report = runner.preflight(config)
            self.assertEqual(report["sample_matching_id"], "read1")

            provenance = runner.run_pipeline(config)
            self.assertEqual(provenance["status"], "complete")
            self.assertTrue((config.output_dir / ".complete").is_file())
            log = config.output_dir / "logs/minimap2.log"
            first_commands = log.read_text().count("] $ ")

            runner.run_pipeline(config)
            self.assertEqual(log.read_text().count("] $ "), first_commands)

            runner.run_pipeline(config, force=True)
            self.assertEqual(log.read_text().count("] $ "), first_commands + 1)
            self.assertTrue(
                (config.output_dir / "filtered/fmlrc.read.eval.tsv").is_file()
            )
            rows = collector.collect_config(config)
            self.assertEqual(len(rows), 2)
            self.assertEqual(
                [row["filter_state"] for row in rows],
                ["unfiltered", "filtered"],
            )
            self.assertTrue(all(row["method"] == "fmlrc" for row in rows))
            summary = Path(directory) / "summary.tsv"
            collector.write_summary(summary, rows)
            self.assertEqual(len(summary.read_text().splitlines()), 3)

            config.config_path.write_text(
                config.config_path.read_text() + "\n"
            )
            with self.assertRaisesRegex(RuntimeError, "config changed"):
                collector.collect_config(config)

    def test_output_prefix_uses_configured_method(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.make_fixture(Path(directory))
            data = yaml.safe_load(config.config_path.read_text())
            data["run"]["method"] = "dadec"
            data["run"]["id"] = "fixture_dadec"
            data["output_dir"] = str(Path(directory) / "dadec-results")
            config.config_path.write_text(yaml.safe_dump(data))
            config = runner.load_config(config.config_path)
            runner.run_pipeline(config)
            self.assertTrue(
                (config.output_dir / "unfiltered/dadec.base.eval.tsv").is_file()
            )
            self.assertTrue(
                (config.output_dir / "filtered/dadec.read.eval.tsv").is_file()
            )

    def test_invalid_transform_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.make_fixture(Path(directory))
            data = yaml.safe_load(config.config_path.read_text())
            data["header_transform"] = "unknown"
            config.config_path.write_text(yaml.safe_dump(data))
            with self.assertRaisesRegex(ValueError, "header_transform"):
                runner.load_config(config.config_path)

    def test_collector_config_pattern_is_dataset_neutral(self):
        path = collector.config_path(
            Path("/configs"),
            "32x_{method}_hifieval.yaml",
            "dadec",
        )
        self.assertEqual(path, Path("/configs/32x_dadec_hifieval.yaml"))
        with self.assertRaisesRegex(ValueError, r"contain \{method\}"):
            collector.config_path(Path("/configs"), "fixed.yaml", "dadec")


class Ecoli3AllToolConfigTests(unittest.TestCase):
    EXPECTED = {
        "dadec": "ecoli3_20x_dadec_dev_fix_a_k31_k31_s1_a2_a1",
        "fmlrc": "ecoli3_20x_fmlrc_original_k21_k59",
        "f_hero": "ecoli3_20x_f_hero_original_k21_k59_hs30_hi3",
        "ratatosk": "ecoli3_20x_ratatosk_original_k31_k63",
        "r_hero": "ecoli3_20x_r_hero_original_k31_k63_hs30_hi3",
        "lordec": "ecoli3_20x_lordec_original_k31_ls5",
        "l_hero": "ecoli3_20x_l_hero_original_k31_ls5_hs30_hi3",
        "colormap": "ecoli3_20x_colormap_original",
        "proovread": "ecoli3_20x_proovread_original",
    }

    def test_nine_configs_select_standard_nonempty_outputs(self):
        config_dir = ROOT / "config/runs/ecoli3/hifieval"
        paths = sorted(config_dir.glob("20x_*_hifieval.yaml"))
        configs = [runner.load_config(path) for path in paths]
        self.assertEqual({config.method for config in configs}, set(self.EXPECTED))
        for config in configs:
            self.assertIn(self.EXPECTED[config.method], str(config.corrected_fasta))
            self.assertTrue(config.corrected_fasta.is_file(), config.method)
            self.assertGreater(config.corrected_fasta.stat().st_size, 0)
            self.assertEqual(config.read_mapping_mode, "legacy_endpoint")
            self.assertEqual(
                config.output_dir.name, config.method, config.method
            )

    def test_batch_launcher_rejects_unknown_method_before_running(self):
        script = ROOT / "work_scripts/hifieval/ecoli3_all.sh"
        environment = os.environ.copy()
        environment["METHODS"] = "not_a_method"
        result = subprocess.run(
            [str(script), "--preflight"],
            env=environment,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("Unknown ecoli3 Hifieval method", result.stderr)


class ArabidopsisSimAllToolConfigTests(unittest.TestCase):
    EXPECTED = {
        "dadec": "arabidopsis_sim_32x_dadec_original_dev_fix_a_k39_k39_s4_a3_a2_t0p1",
        "fmlrc": "fmlrc1.fa",
        "f_hero": "F_HERO.fa",
        "ratatosk": "ratatosk1.fa",
        "r_hero": "R_HERO.fa",
        "lordec": "lordec1.fa",
        "l_hero": "L_HERO.fa",
        "colormap": "colormap_sp.fa",
        "proovread": "arabidopsis_sim_32x_proovread_original",
    }

    def test_nine_configs_select_nonempty_outputs(self):
        config_dir = ROOT / "config/runs/arabidopsis_sim/hifieval"
        paths = sorted(config_dir.glob("32x_*_hifieval.yaml"))
        configs = [runner.load_config(path) for path in paths]
        self.assertEqual({config.method for config in configs}, set(self.EXPECTED))
        for config in configs:
            self.assertIn(self.EXPECTED[config.method], str(config.corrected_fasta))
            self.assertTrue(config.corrected_fasta.is_file(), config.method)
            self.assertGreater(config.corrected_fasta.stat().st_size, 0)
            self.assertEqual(config.header_transform, "strip_after_colon")
            self.assertEqual(config.read_mapping_mode, "legacy_endpoint")
            self.assertEqual(config.output_dir.name, config.method)
            self.assertEqual(config.output_dir.parent.name, "arabidopsis_sim_32x")

    def test_batch_launcher_rejects_unknown_method_before_running(self):
        script = ROOT / "work_scripts/hifieval/arabidopsis_sim_all.sh"
        environment = os.environ.copy()
        environment["METHODS"] = "not_a_method"
        result = subprocess.run(
            [str(script), "--preflight"],
            env=environment,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("Unknown arabidopsis_sim Hifieval method", result.stderr)


if __name__ == "__main__":
    unittest.main()
