import importlib.util
import json
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


layout = load_script("run_layout")
migration = load_script("migrate_run_layout")


class RunLayoutTests(unittest.TestCase):
    def test_groups_cover_current_naming_forms(self):
        cases = {
            "30strains_10x_colormap_original": "30strains_10x",
            "30strains_legacy_20x_f_hero_original_k21_k31": "30strains_legacy_20x",
            "arabidopsis_32x_dadec_ablation_k39": "arabidopsis_32x",
            "ecoli_error_miseq_ratatosk_original": "ecoli_error_miseq",
            "ecoli_miseq_20x_dadec_ablation_k31": "ecoli_miseq_20x",
        }
        for run_id, expected in cases.items():
            with self.subTest(run_id=run_id):
                self.assertEqual(layout.derive_run_group(run_id), expected)

    def test_score_selection_and_existing_directories(self):
        self.assertEqual(layout.normalize_ambiguity_scores("0.99,0.9999"), ["0.99", "0.9999"])
        self.assertEqual(layout.normalize_ambiguity_scores([0.9999, 0.99]), ["0.9999", "0.99"])
        self.assertEqual(layout.evaluation_variants("metaquast", "0.99,0.9999"), [
            ("metaquast", "0.99"),
            ("metaquast.ambiguity9999", "0.9999"),
        ])
        with self.assertRaises(ValueError):
            layout.normalize_ambiguity_scores("0.9")

    def test_migration_is_collision_safe_and_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = root / "benchmark/runs/30strains_10x_dadec_k31"
            provenance = run / "benchmark/provenance.json"
            provenance.parent.mkdir(parents=True)
            provenance.write_text(json.dumps({"run_id": run.name, "run_root": str(run)}))
            dry = migration.migrate(root, apply=False)
            self.assertEqual(dry["operations"][0]["status"], "move")
            migration.migrate(root, apply=True)
            moved = root / "benchmark/runs/30strains_10x" / run.name
            self.assertTrue(moved.is_dir())
            data = json.loads((moved / "benchmark/provenance.json").read_text())
            self.assertEqual(data["run_group"], "30strains_10x")
            again = migration.migrate(root, apply=False)
            self.assertEqual(again["operations"][0]["status"], "already_migrated")

    def test_migration_refuses_collision(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runs = root / "benchmark/runs"
            source = runs / "30strains_10x_dadec_k31"
            destination = runs / "30strains_10x" / source.name
            source.mkdir(parents=True)
            destination.mkdir(parents=True)
            with self.assertRaises(FileExistsError):
                migration.migrate(root, apply=True)


if __name__ == "__main__":
    unittest.main()
