import gzip
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SNAKEMAKE = Path("/home/work/wenhai/bin/snakemake")
METHODS = (
    "dadec",
    "fmlrc",
    "f_hero",
    "ratatosk",
    "r_hero",
    "lordec",
    "l_hero",
    "colormap",
    "proovread",
    "vechat",
    "dechat",
)


class WorkflowFixture:
    def __init__(
        self,
        root,
        *,
        method="colormap",
        coverage="20x",
        evaluation_tool="quast",
        methods=None,
        short_coverages=None,
        long_subsamples=None,
        include_long=True,
    ):
        self.root = Path(root)
        self.inputs = self.root / "inputs"
        self.inputs.mkdir(parents=True)
        self.long = self.inputs / "long.fa"
        if include_long:
            self.long.write_text(">long\nACGT\n")
        self.short_paths = {}
        selected_short_coverages = (
            [coverage] if short_coverages is None else short_coverages
        )
        for label in selected_short_coverages:
            path = self.inputs / f"short_{label}.fq.gz"
            with gzip.open(path, "wt") as handle:
                handle.write("@short\nACGT\n+\nIIII\n")
            self.short_paths[label] = path
        self.subsample_paths = {}
        for label in long_subsamples or []:
            path = self.inputs / f"long_{label}.fa"
            path.write_text(">long_subsample\nACGT\n")
            self.subsample_paths[label] = path
        self.reference = self.inputs / "reference.fa"
        self.reference.write_text(">reference\nACGT\n")
        self.genome_map = self.inputs / "genome_to_id.tsv"
        self.genome_map.write_text(f"fixture\t{self.reference}\n")
        self.config_path = self.root / "config.yaml"
        run = {"id": f"fixture_{coverage}_{method}", "coverage": coverage, "method": method}
        if method is None:
            anchor = "dadec" if methods == "all" else list(methods)[0]
            run = {"id": f"fixture_allcov_{anchor}"}
        selected_methods = methods if methods is not None else [method]
        self.config = {
            "project_root": str(self.root),
            "dataset": {
                "id": "fixture",
                "variant": "test",
                "expected_genomes": 1,
                "long_coverage": "10x",
            },
            "inputs": {
                "long_reads": str(self.long) if include_long else None,
                "short_reads": {
                    label: str(path) for label, path in self.short_paths.items()
                },
                "long_read_subsamples": {
                    label: str(path) for label, path in self.subsample_paths.items()
                },
                "genome_map": str(self.genome_map),
                "simulation_configs": [],
            },
            "tools": {
                "conda": "/bin/true",
                "python": "/bin/true",
                "runner_python": "/bin/true",
                "hero_python": "/bin/true",
                "dadec": "/bin/true",
                "fmlrc": "/bin/true",
                "fmlrc_convert": "/bin/true",
                "ropebwt2": "/bin/true",
                "hero": "/bin/true",
                "ratatosk": "/bin/true",
                "lordec": "/bin/true",
                "colormap": "/bin/true",
                "proovread": "/bin/true",
                "vechat": "/bin/true",
                "dechat": "/bin/true",
                "seqkit": "/bin/true",
                "quast": "/bin/true",
                "metaquast": "/bin/true",
                "time": "/bin/true",
            },
            "environments": {
                "evaluation": "fixture",
                "methods": {name: "fixture" for name in METHODS},
            },
            "methods": selected_methods,
            "parameter_profile": "study",
            "parameters": {
                "profiles": {
                    "tool_defaults": {},
                    "study": {
                        "dadec_k1": 31,
                        "dadec_k2": 31,
                        "fmlrc_k1": 21,
                        "fmlrc_k2": 59,
                        "ratatosk_k1": 31,
                        "ratatosk_k2": 63,
                        "lordec_k": 21,
                    },
                },
                "hero_split": 10,
                "hero_iterations": 3,
                "lordec_solid": 5,
            },
            "resources": {
                "method_threads": 1,
                "metaquast_threads": 1,
                "min_free_disk_gb": 0.001,
            },
            "dadec": {
                "split_number": 1,
                "msa_threshold": 0.08,
                "abundance_min1": 2,
                "abundance_min2": 1,
            },
            "metaquast": {
                "ambiguity_usage": "all",
                "ambiguity_scores": [0.99],
                "min_contig": 500,
                "extra_args": "--fast",
            },
            "quast": {"min_contig": 500, "extra_args": "--fast"},
            "quast_cleanup": {"threshold_mib": 100},
            "evaluation": {"tool": evaluation_tool},
            "paths": {"run_root": "runs"},
            "run": run,
        }
        self.write_config()
        self.workdir = self.root / "snakemake-workdir"
        self.workdir.mkdir()

    def write_config(self):
        self.config_path.write_text(yaml.safe_dump(self.config, sort_keys=False))

    @property
    def run_root(self):
        method = self.config["run"]["method"]
        coverage = self.config["run"]["coverage"]
        return self.root / "runs" / f"fixture_{coverage}" / f"fixture_{coverage}_{method}"

    def run(self, *extra, rerun_triggers=("mtime",), targets=("all",)):
        command = [
            str(SNAKEMAKE),
            "--snakefile",
            str(ROOT / "Snakefile"),
            "--directory",
            str(self.workdir),
            "--configfile",
            str(self.config_path),
            "--cores",
            "1",
            "--nolock",
            "--dry-run",
            *[str(target) for target in targets],
        ]
        if rerun_triggers:
            command.extend(["--rerun-triggers", *rerun_triggers])
        command.extend(extra)
        environment = os.environ.copy()
        environment["PYTHONWARNINGS"] = "ignore"
        environment["XDG_CACHE_HOME"] = str(self.root / "cache")
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            env=environment,
        )

    def run_with_environment(self, environment_overrides, *extra):
        environment = os.environ.copy()
        environment["PYTHONWARNINGS"] = "ignore"
        environment["XDG_CACHE_HOME"] = str(self.root / "cache")
        environment.update(environment_overrides)
        command = [
            str(SNAKEMAKE),
            "--snakefile",
            str(ROOT / "Snakefile"),
            "--directory",
            str(self.workdir),
            "--configfile",
            str(self.config_path),
            "--cores",
            "1",
            "--nolock",
            "--dry-run",
            "all",
            *extra,
        ]
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            env=environment,
        )

    def seed_completed_run(self):
        base = time.time() - 1000
        old = base
        completed = base + 100
        changed = base + 200
        paths = {
            "preflight": self.run_root / "benchmark/preflight.json",
            "provenance": self.run_root / "benchmark/provenance.json",
            "long": self.run_root / "tmp/inputs/long_10x.fa",
            "short": self.run_root / "tmp/inputs/short_20x.fa",
            "reference": self.run_root / "tmp/reference/fixture.fa",
            "mapping": self.run_root / "tmp/reference/contig_to_genome.tsv",
            "corrected": self.run_root / "output/short_20x/colormap/corrected.fa",
            "resources": self.run_root
            / "benchmark/short_20x/colormap/resources.time.txt",
            "report": self.run_root / "output/short_20x/colormap/quast/report.tsv",
        }
        for name, path in paths.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"{name}\n")
            os.utime(path, (completed, completed))
        for path in [self.long, *self.short_paths.values(), self.reference]:
            os.utime(path, (old, old))
        os.utime(self.genome_map, (changed, changed))
        return paths


class MinimalDependencyFixture:
    """Create real Snakemake metadata in a temporary, side-effect-free workflow."""

    def __init__(self, root):
        self.root = Path(root)
        self.reads = self.root / "reads.fa"
        self.genome_map = self.root / "genome_to_id.tsv"
        self.reads.write_text(">read\nACGT\n")
        self.genome_map.write_text("fixture\treference.fa\n")
        self.snakefile = self.root / "Snakefile"
        self.snakefile.write_text(
            """
rule all:
    input:
        "corrected.fa",
        "report.tsv"

rule preflight:
    input:
        reads="reads.fa"
    output:
        "preflight.json"
    shell:
        "touch {output}"

rule prepare_short_reads:
    input:
        preflight=rules.preflight.output,
        reads="reads.fa"
    output:
        "prepared.fa"
    shell:
        "touch {output}"

rule correct_method:
    input:
        preflight=rules.preflight.output,
        reads="prepared.fa"
    output:
        "corrected.fa"
    shell:
        "touch {output}"

rule prepare_reference:
    input:
        genome_map="genome_to_id.tsv"
    output:
        "reference.fa"
    shell:
        "touch {output}"

rule quast_corrected:
    input:
        corrected="corrected.fa",
        reference="reference.fa"
    output:
        "report.tsv"
    shell:
        "touch {output}"
""".lstrip()
        )
        initial = self.run(dry_run=False)
        if initial.returncode != 0:
            raise RuntimeError(output(initial))

    def run(self, *, dry_run=True, targets=("all",)):
        command = [
            str(SNAKEMAKE),
            "--snakefile",
            str(self.snakefile),
            "--directory",
            str(self.root),
            "--cores",
            "1",
            "--nolock",
            *[str(target) for target in targets],
            "--rerun-triggers",
            "mtime",
        ]
        if dry_run:
            command.append("--dry-run")
        environment = os.environ.copy()
        environment["PYTHONWARNINGS"] = "ignore"
        environment["XDG_CACHE_HOME"] = str(self.root / "cache")
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            env=environment,
        )

    @staticmethod
    def change(path):
        path.write_text(path.read_text() + "# changed\n")


def output(result):
    return result.stdout + result.stderr


class DependencyIsolationTests(unittest.TestCase):
    def test_reference_change_does_not_schedule_read_preparation_or_correction(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = MinimalDependencyFixture(directory)
            fixture.change(fixture.genome_map)
            (fixture.root / "report.tsv").unlink()
            result = fixture.run(targets=("reference.fa", "report.tsv"))
            text = output(result)
            self.assertEqual(result.returncode, 0, text)
            self.assertIn("prepare_reference", text)
            self.assertIn("quast_corrected", text)
            self.assertNotIn("prepare_long_reads", text)
            self.assertNotIn("prepare_short_reads", text)
            self.assertNotIn("correct_method", text)

    def test_raw_read_change_still_schedules_preparation_and_correction(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = MinimalDependencyFixture(directory)
            fixture.change(fixture.reads)
            (fixture.root / "corrected.fa").unlink()
            (fixture.root / "report.tsv").unlink()
            result = fixture.run(targets=("corrected.fa", "report.tsv"))
            text = output(result)
            self.assertEqual(result.returncode, 0, text)
            self.assertIn("prepare_short_reads", text)
            self.assertIn("correct_method", text)

    def test_main_workflow_keeps_reference_out_of_correction_gate(self):
        snakefile = (ROOT / "Snakefile").read_text()
        methods = (ROOT / "rules/methods.smk").read_text()
        self.assertNotIn("genome_map=rooted(config[\"inputs\"][\"genome_map\"]),\n"
                         "    output: f\"{BENCHMARK_OUT}/preflight.json\"", snakefile)
        self.assertNotIn("ancient(rules.preflight.output)", snakefile)
        self.assertNotIn("ancient(rules.preflight.output)", methods)
        self.assertEqual(methods.count("preflight=rules.preflight.output"), 6)

    def test_evaluation_only_never_loads_correction_jobs(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = WorkflowFixture(directory)
            paths = fixture.seed_completed_run()
            result = fixture.run(
                "--config",
                "evaluation_only=true",
                "--forceall",
                rerun_triggers=None,
            )
            text = output(result)
            self.assertEqual(result.returncode, 0, text)
            self.assertIn("quast_corrected", text)
            self.assertNotIn("correct_method", text)
            self.assertNotIn("prepare_long_reads", text)
            self.assertNotIn("prepare_short_reads", text)

    def test_evaluation_only_missing_internal_fasta_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = WorkflowFixture(directory)
            result = fixture.run("--config", "evaluation_only=true")
            text = output(result)
            self.assertNotEqual(result.returncode, 0, text)
            self.assertIn("corrected.fa", text)
            self.assertNotIn("correct_method", text)

    def test_evaluation_only_rejects_external_input_modes(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = WorkflowFixture(directory)
            corrected = fixture.inputs / "external.fa"
            corrected.write_text(">external\nACGT\n")
            fixture.config["evaluation"]["corrected_fasta"] = str(corrected)
            fixture.write_config()
            result = fixture.run("--config", "evaluation_only=true")
            text = output(result)
            self.assertNotEqual(result.returncode, 0, text)
            self.assertIn("cannot be combined", text)

    def test_environment_run_suffix_survives_cli_config_override(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = WorkflowFixture(directory)
            result = fixture.run_with_environment(
                {"RUN_ID_SUFFIX": "dev_test"},
                "--config",
                "evaluation_only=true",
            )
            text = output(result)
            self.assertNotEqual(result.returncode, 0, text)
            self.assertIn("fixture_20x_colormap_dev_test", text)
            self.assertNotIn("fixture_20x_colormap/output", text)


class LegacyInputCompatibilityTests(unittest.TestCase):
    def test_hybrid_fasta_and_fastq_gz_inputs_keep_normal_routes(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = WorkflowFixture(directory)
            result = fixture.run()
            text = output(result)
            self.assertEqual(result.returncode, 0, text)
            self.assertIn(str(fixture.long), text)
            self.assertIn(str(fixture.short_paths["20x"]), text)
            self.assertIn("prepare_long_reads", text)
            self.assertIn("prepare_short_reads", text)
            self.assertIn("correct_method", text)

    def test_multiple_coverages_remain_independent(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = WorkflowFixture(
                directory,
                method=None,
                methods=["colormap"],
                short_coverages=["20x", "30x"],
            )
            result = fixture.run()
            text = output(result)
            self.assertEqual(result.returncode, 0, text)
            self.assertIn("coverage=20x", text)
            self.assertIn("coverage=30x", text)

    def test_long_read_subsample_remains_hybrid_long_input(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = WorkflowFixture(
                directory,
                coverage="20pct",
                method="colormap",
                long_subsamples=["20pct"],
            )
            result = fixture.run()
            text = output(result)
            self.assertEqual(result.returncode, 0, text)
            self.assertIn("prepare_long_read_subsample", text)
            self.assertIn("long_20pct.fa", text)
            self.assertIn("prepare_short_reads", text)

    def test_self_correction_uses_only_long_read_subsample(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = WorkflowFixture(
                directory,
                coverage="20pct",
                method="vechat",
                short_coverages=[],
                long_subsamples=["20pct"],
                include_long=False,
            )
            result = fixture.run()
            text = output(result)
            self.assertEqual(result.returncode, 0, text)
            self.assertIn("prepare_long_read_subsample", text)
            self.assertIn("correct_method", text)
            self.assertNotIn("prepare_short_reads", text)

    def test_all_method_hero_routing_is_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = WorkflowFixture(
                directory,
                coverage="20pct",
                method=None,
                methods="all",
                short_coverages=["20pct"],
                long_subsamples=["20pct"],
            )
            result = fixture.run()
            text = output(result)
            self.assertEqual(result.returncode, 0, text)
            self.assertIn("correct_method", text)
            self.assertIn("continue_base_to_round3", text)
            self.assertIn("hero_from_shared_round3", text)

    def test_external_corrected_fasta_supports_both_evaluators(self):
        for evaluator, rule in (
            ("quast", "quast_corrected"),
            ("metaquast", "metaquast_corrected"),
        ):
            with self.subTest(evaluator=evaluator), tempfile.TemporaryDirectory() as directory:
                fixture = WorkflowFixture(directory, evaluation_tool=evaluator)
                corrected = fixture.inputs / "external.fa"
                corrected.write_text(">external\nACGT\n")
                fixture.config["evaluation"]["corrected_fasta"] = str(corrected)
                fixture.write_config()
                result = fixture.run()
                text = output(result)
                self.assertEqual(result.returncode, 0, text)
                self.assertIn(rule, text)
                self.assertNotIn("correct_method", text)
                self.assertNotIn("prepare_short_reads", text)

    def test_external_report_with_blank_corrected_fasta_is_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = WorkflowFixture(directory, evaluation_tool="metaquast")
            report = fixture.inputs / "external_report.tsv"
            report.write_text("Assembly\tcorrected\n")
            fixture.config["evaluation"].update(
                {"corrected_fasta": "", "report": str(report)}
            )
            fixture.write_config()
            result = fixture.run()
            text = output(result)
            self.assertEqual(result.returncode, 0, text)
            self.assertIn("import_metaquast_report", text)
            self.assertNotIn("correct_method", text)
            self.assertNotIn("prepare_reference", text)


if __name__ == "__main__":
    unittest.main()
