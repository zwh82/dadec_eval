import importlib.util
import csv
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


resources = load_script("parse_resources")
metaquast = load_script("parse_metaquast")
aggregate = load_script("aggregate")


class ResourceParserTests(unittest.TestCase):
    def test_structured_time_output(self):
        parsed = resources.parse_resource_text(
            "wall_seconds=61.25\nuser_cpu_seconds=40.5\n"
            "system_cpu_seconds=2.5\ncpu_percent=70%\n"
            "max_rss_kb=1048576\nexit_code=0\n"
        )
        self.assertEqual(parsed["wall_seconds"], 61.25)
        self.assertEqual(parsed["total_cpu_seconds"], 43.0)
        self.assertEqual(parsed["max_rss_kb"], 1048576)

    def test_verbose_time_output(self):
        parsed = resources.parse_resource_text(
            "User time (seconds): 5.5\nSystem time (seconds): 1.5\n"
            "Percent of CPU this job got: 100%\n"
            "Elapsed (wall clock) time (h:mm:ss or m:ss): 1:02.50\n"
            "Maximum resident set size (kbytes): 42\nExit status: 0\n"
        )
        self.assertEqual(parsed["wall_seconds"], 62.5)
        self.assertEqual(parsed["total_cpu_seconds"], 7.0)

    def test_missing_resource_field_fails(self):
        with self.assertRaisesRegex(ValueError, "Missing resource fields"):
            resources.parse_resource_text("wall_seconds=1\n")


class MetaquastParserTests(unittest.TestCase):
    REPORT = (
        "Assembly\treads\n"
        "# contigs (>= 0 bp)\t101\n"
        "# contigs\t99\n"
        "# local misassemblies\t7\n"
        "Genome fraction (%)\t98.75\n"
        "# mismatches per 100 kbp\t12.5\n"
        "# indels per 100 kbp\t3.25\n"
        "N50\t10000\n"
    )

    def write_report(self, text):
        temporary = tempfile.NamedTemporaryFile("w", delete=False)
        with temporary:
            temporary.write(text)
        self.addCleanup(Path(temporary.name).unlink, missing_ok=True)
        return temporary.name

    def test_exact_five_metrics(self):
        parsed = metaquast.parse_report(self.write_report(self.REPORT))
        self.assertEqual(parsed, {
            "mismatches_per_100_kbp": 12.5,
            "indels_per_100_kbp": 3.25,
            "haplotype_coverage_percent": 98.75,
            "local_misassemblies": 7,
            "contigs_number": 99,
        })

    def test_thresholded_contig_row_is_not_substituted(self):
        report = self.REPORT.replace("# contigs\t99\n", "")
        with self.assertRaisesRegex(ValueError, "# contigs"):
            metaquast.parse_report(self.write_report(report))

    def test_missing_genome_fraction_fails(self):
        report = self.REPORT.replace("Genome fraction (%)\t98.75\n", "")
        with self.assertRaisesRegex(ValueError, "Genome fraction"):
            metaquast.parse_report(self.write_report(report))

    def test_duplicate_metric_fails(self):
        report = self.REPORT + "# contigs\t98\n"
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            metaquast.parse_report(self.write_report(report))

    def test_two_ambiguity_scores_reuse_one_resource_row(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            resources_path = root / "resources.tsv"
            metaquast_path = root / "metaquast.tsv"
            resource = {
                "run_id": "run", "parameter_set": "study", "dataset": "dataset",
                "long_coverage": "10x", "short_coverage": "10x", "method": "DADEC",
            }
            resource.update({"CPU(h)": "1", "WallTime(h)": "2", "Memory(GB)": "3"})
            with open(resources_path, "w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=[
                    *aggregate.RESOURCE_KEY_FIELDS, *aggregate.RESOURCE_FIELDS
                ], delimiter="\t")
                writer.writeheader(); writer.writerow(resource)
            rows = []
            for score in ("0.99", "0.9999"):
                row = {field: resource[field] for field in aggregate.RESOURCE_KEY_FIELDS}
                row["ambiguity_score"] = score
                row.update({field: "0" for field in aggregate.METAQUAST_FIELDS})
                rows.append(row)
            with open(metaquast_path, "w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=[
                    *aggregate.KEY_FIELDS, *aggregate.METAQUAST_FIELDS
                ], delimiter="\t")
                writer.writeheader(); writer.writerows(rows)
            combined = aggregate.aggregate(resources_path, metaquast_path)
            self.assertEqual(len(combined), 2)
            self.assertEqual({row["WallTime(h)"] for row in combined}, {"2"})


if __name__ == "__main__":
    unittest.main()
