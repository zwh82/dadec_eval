import csv
import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


BENCHMARK_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = BENCHMARK_ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

import assembly_pipeline as pipeline


SNAKEMAKE = Path("/home/work/wenhai/bin/snakemake")
SNAKEFILE = BENCHMARK_ROOT / "assembly" / "Snakefile"


def digest(path):
    value = hashlib.sha256()
    value.update(Path(path).read_bytes())
    return value.hexdigest()


class AssemblyWorkflowTests(unittest.TestCase):
    def make_executable(self, path, body):
        path.write_text(f"#!{sys.executable}\n{body}")
        path.chmod(0o755)

    def make_fixture(self, root):
        root = Path(root)
        inputs = root / "inputs"
        tools = root / "tools"
        inputs.mkdir()
        tools.mkdir()
        reference = inputs / "reference.fa"
        reference.write_text(">reference\nACGTACGT\n")
        command_log = root / "commands.log"

        canu = tools / "canu"
        self.make_executable(
            canu,
            "import os, pathlib, sys\n"
            "if '-version' in sys.argv:\n"
            "    print('fake-canu 1.0')\n"
            "    raise SystemExit(0)\n"
            "with open(os.environ['FAKE_ASSEMBLY_LOG'], 'a') as handle:\n"
            "    handle.write('canu ' + ' '.join(sys.argv[1:]) + '\\n')\n"
            "directory = pathlib.Path(sys.argv[sys.argv.index('-d') + 1])\n"
            "prefix = sys.argv[sys.argv.index('-p') + 1]\n"
            "directory.mkdir(parents=True, exist_ok=True)\n"
            "(directory / (prefix + '.contigs.fasta')).write_text('>canu_contig\\nACGTACGT\\n')\n",
        )
        hifiasm = tools / "hifiasm"
        self.make_executable(
            hifiasm,
            "import os, pathlib, sys\n"
            "if '--version' in sys.argv:\n"
            "    print('fake-hifiasm 1.0')\n"
            "    raise SystemExit(0)\n"
            "with open(os.environ['FAKE_ASSEMBLY_LOG'], 'a') as handle:\n"
            "    handle.write('hifiasm ' + ' '.join(sys.argv[1:]) + '\\n')\n"
            "prefix = pathlib.Path(sys.argv[sys.argv.index('-o') + 1])\n"
            "prefix.parent.mkdir(parents=True, exist_ok=True)\n"
            "pathlib.Path(str(prefix) + '.bp.r_utg.gfa').write_text('S\\tsegment1\\tACGTACGT\\n')\n",
        )
        quast = tools / "quast.py"
        self.make_executable(
            quast,
            "import os, pathlib, sys\n"
            "if '--version' in sys.argv:\n"
            "    print('fake-quast 1.0')\n"
            "    raise SystemExit(0)\n"
            "with open(os.environ['FAKE_ASSEMBLY_LOG'], 'a') as handle:\n"
            "    handle.write('quast ' + ' '.join(sys.argv[1:]) + '\\n')\n"
            "output = pathlib.Path(sys.argv[sys.argv.index('-o') + 1])\n"
            "output.mkdir(parents=True, exist_ok=True)\n"
            "rows = [\n"
            "    ('Assembly', 'fixture'), ('# contigs', '1'),\n"
            "    ('Largest contig', '8'), ('Total length', '8'), ('N50', '8'),\n"
            "    ('# misassemblies', '0'), ('Genome fraction (%)', '100.0'),\n"
            "    ('# mismatches per 100 kbp', '0.0'),\n"
            "    ('# indels per 100 kbp', '0.0')]\n"
            "text = ''.join(left + '\\t' + right + '\\n' for left, right in rows)\n"
            "(output / 'report.tsv').write_text(text)\n"
            "(output / 'report.txt').write_text(text)\n",
        )

        methods = {}
        for method in sorted(pipeline.EXPECTED_BUILD_METHODS):
            source = inputs / f"{method}.corrected.fa"
            source.write_text(f">{method}_read\nACGTACGT\n")
            methods[method] = {"mode": "build", "corrected_fasta": str(source)}
        for method in sorted(pipeline.EXPECTED_REUSE_METHODS):
            assemblies = {}
            for assembler in pipeline.ASSEMBLERS:
                source = inputs / f"{method}.{assembler}.fa"
                source.write_text(f">{method}_{assembler}\nACGTACGT\n")
                assemblies[assembler] = str(source)
            methods[method] = {"mode": "reuse", "assemblies": assemblies}

        config_path = root / "config.yaml"
        config_path.write_text(
            yaml.safe_dump(
                {
                    "schema_version": 1,
                    "project_root": str(root),
                    "dataset": "drosophila",
                    "run_id": "fixture",
                    "threads": 64,
                    "quast_threads": 2,
                    "genome_size": "137m",
                    "min_free_disk_gb": 0,
                    "output_root": "results",
                    "reference": str(reference),
                    "tools": {
                        "python": sys.executable,
                        "time": "/usr/bin/time",
                        "canu": str(canu),
                        "hifiasm": str(hifiasm),
                        "quast": str(quast),
                    },
                    "methods": methods,
                },
                sort_keys=False,
            )
        )
        return config_path, command_log, inputs

    def run_workflow(self, config_path, command_log):
        env = dict(os.environ)
        env["FAKE_ASSEMBLY_LOG"] = str(command_log)
        env["XDG_CACHE_HOME"] = str(config_path.parent / ".cache")
        result = subprocess.run(
            [
                str(SNAKEMAKE),
                "--snakefile",
                str(SNAKEFILE),
                "--directory",
                str(config_path.parent),
                "--configfile",
                str(config_path),
                "--config",
                f"config_path={config_path}",
                "--cores",
                "64",
                "--nolock",
                "--rerun-triggers",
                "mtime",
                "--quiet",
            ],
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        if result.returncode != 0:
            self.fail(f"Snakemake failed ({result.returncode}):\n{result.stdout}")
        return result

    def test_full_matrix_routes_builds_reuses_and_is_restartable(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path, command_log, inputs = self.make_fixture(Path(directory))
            before = {path.name: digest(path) for path in inputs.glob("*.fa")}
            self.run_workflow(config_path, command_log)

            commands = command_log.read_text().splitlines()
            self.assertEqual(sum(line.startswith("canu ") for line in commands), 3)
            self.assertEqual(sum(line.startswith("hifiasm ") for line in commands), 3)
            self.assertEqual(sum(line.startswith("quast ") for line in commands), 18)
            self.assertTrue(
                all(
                    "maxThreads=64" in line
                    and " -p canu " in f" {line} "
                    and " -pacbio " in f" {line} "
                    and " -corrected " not in f" {line} "
                    and "/work_pacbio " in line
                    for line in commands
                    if line.startswith("canu ")
                )
            )
            self.assertTrue(
                all(
                    " -t 64 " in f" {line} "
                    for line in commands
                    if line.startswith("hifiasm ")
                )
            )
            self.assertTrue(
                all(
                    " -t 2 " in f" {line} "
                    for line in commands
                    if line.startswith("quast ")
                )
            )

            config = pipeline.load_config(config_path)
            result = pipeline.verify(config)
            self.assertEqual(result["matrix_size"], 18)
            with open(config["output_root"] / "summary.tsv", newline="") as handle:
                rows = list(csv.DictReader(handle, delimiter="\t"))
            self.assertEqual(len(rows), 18)
            self.assertEqual(
                {(row["method"], row["assembler"]) for row in rows},
                {
                    (method, assembler)
                    for method in config["methods"]
                    for assembler in pipeline.ASSEMBLERS
                },
            )
            after = {path.name: digest(path) for path in inputs.glob("*.fa")}
            self.assertEqual(before, after)

            first_count = len(commands)
            self.run_workflow(config_path, command_log)
            self.assertEqual(len(command_log.read_text().splitlines()), first_count)

    def test_preflight_rejects_zero_byte_and_missing_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path, _, _ = self.make_fixture(Path(directory))
            config = pipeline.load_config(config_path)
            invalid = config["methods"]["fmlrc"]["assemblies"]["canu"]
            invalid.write_bytes(b"")
            with self.assertRaisesRegex(ValueError, "empty"):
                pipeline.validate_config(
                    config, check_disk=False, capture_versions=False
                )
            invalid.unlink()
            with self.assertRaisesRegex(ValueError, "does not exist"):
                pipeline.validate_config(
                    config, check_disk=False, capture_versions=False
                )

    def test_configured_cell_skip_is_excluded_and_recorded(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path, command_log, _ = self.make_fixture(Path(directory))
            raw = yaml.safe_load(config_path.read_text())
            raw["methods"]["colormap"]["skip_assemblers"] = ["hifiasm"]
            raw["methods"]["colormap"]["skip_reasons"] = {
                "hifiasm": "empty GFA"
            }
            config_path.write_text(yaml.safe_dump(raw, sort_keys=False))

            self.run_workflow(config_path, command_log)
            commands = command_log.read_text().splitlines()
            self.assertEqual(sum(line.startswith("hifiasm ") for line in commands), 2)
            self.assertEqual(sum(line.startswith("quast ") for line in commands), 17)

            config = pipeline.load_config(config_path)
            result = pipeline.verify(config)
            self.assertEqual(result["status"], "complete_with_skips")
            self.assertEqual(result["matrix_size"], 17)
            manifest = yaml.safe_load((config["output_root"] / "manifest.json").read_text())
            self.assertEqual(
                manifest["skipped_cells"],
                [{"method": "colormap", "assembler": "hifiasm", "reason": "empty GFA"}],
            )

    def test_config_order_change_does_not_rebuild_completed_cells(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path, command_log, _ = self.make_fixture(Path(directory))
            self.run_workflow(config_path, command_log)
            completed_commands = command_log.read_text().splitlines()

            raw = yaml.safe_load(config_path.read_text())
            raw["methods"]["colormap"]["skip_assemblers"] = ["hifiasm"]
            raw["methods"]["colormap"]["skip_reasons"] = {
                "hifiasm": "deferred after a failed build"
            }
            config_path.write_text(yaml.safe_dump(raw, sort_keys=False))

            self.run_workflow(config_path, command_log)
            self.assertEqual(command_log.read_text().splitlines(), completed_commands)

    def test_gfa_conversion_requires_sequence_segments(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corrected = root / "corrected.fa"
            corrected.write_text(">read\nACGT\n")
            gfa = root / "assembly.gfa"
            gfa.write_text("H\tVN:Z:1.0\n")
            with self.assertRaisesRegex(ValueError, "no sequence-bearing"):
                pipeline.gfa_to_fasta(
                    gfa,
                    root / "assembly.fa",
                    root / "provenance.json",
                    "dadec",
                    "hifiasm",
                    corrected,
                )


if __name__ == "__main__":
    unittest.main()
