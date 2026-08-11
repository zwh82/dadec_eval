import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load_script(name):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

aggregate = load_script("aggregate")
collector = load_script("collect_summaries")
migration = load_script("migrate_legacy_layout")

class ConfigTests(unittest.TestCase):
    def test_dataset_configs_have_distinct_ids_and_expected_inputs(self):
        config_dir = ROOT / "config/datasets"
        thirty = (config_dir / "30strains.yaml").read_text()
        hundred = (config_dir / "100strains.yaml").read_text()
        self.assertIn("id: 30strains", thirty)
        self.assertIn("expected_genomes: 30", thirty)
        self.assertIn("id: 100strains", hundred)
        self.assertIn("expected_genomes: 100", hundred)
        self.assertIn("10x: data/30strains/sim_30strains_short_10x.fq.gz", thirty)
        self.assertIn("30x: data/100strains/sim_100strains_short_30x.fq.gz", hundred)

class CollectionTests(unittest.TestCase):
    def write_summary(self, root, dataset, short_coverage):
        table = root / dataset / "tables/benchmark_summary.tsv"
        table.parent.mkdir(parents=True)
        row = {field: "0" for field in aggregate.FIELDS}
        row.update({
            "dataset": dataset, "long_coverage": "10x",
            "short_coverage": short_coverage, "method": "dadec",
        })
        with open(table, "w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=aggregate.FIELDS, delimiter="\t")
            writer.writeheader(); writer.writerow(row)

    def test_same_coverage_is_isolated_by_dataset(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_summary(root, "30strains", "10x")
            self.write_summary(root, "100strains", "10x")
            rows = collector.collect(root)
            self.assertEqual({row["dataset"] for row in rows}, {"30strains", "100strains"})

    def test_dataset_path_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_summary(root, "30strains", "10x")
            table = root / "30strains/tables/benchmark_summary.tsv"
            text = table.read_text().replace("30strains", "100strains")
            table.write_text(text)
            with self.assertRaisesRegex(ValueError, "Dataset/path mismatch"):
                collector.collect(root)

class MigrationTests(unittest.TestCase):
    def test_dry_run_does_not_move_and_apply_is_atomic(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "benchmark/results/corrected/10x/dadec.fa"
            source.parent.mkdir(parents=True)
            source.write_text("data")
            dry = migration.migrate(root, apply=False)
            self.assertTrue(source.exists())
            self.assertTrue(any(op["status"] == "move" for op in dry["operations"]))
            migration.migrate(root, apply=True)
            destination = root / "benchmark/results/30strains/short_10x/dadec/corrected.fa"
            self.assertFalse(source.exists())
            self.assertEqual(destination.read_text(), "data")

    def test_collision_refuses_migration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "benchmark/results/corrected/10x/dadec.fa"
            destination = root / "benchmark/results/30strains/short_10x/dadec/corrected.fa"
            source.parent.mkdir(parents=True); destination.parent.mkdir(parents=True)
            source.write_text("old"); destination.write_text("new")
            with self.assertRaises(FileExistsError):
                migration.migrate(root, apply=True)

if __name__ == "__main__":
    unittest.main()
