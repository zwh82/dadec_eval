import gzip
import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "fastq_to_fasta.py"
SPEC = importlib.util.spec_from_file_location("fastq_to_fasta", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FastqConversionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def test_gzip_conversion_preserves_primary_id(self):
        source = self.root / "reads.fq.gz"
        destination = self.root / "reads.fa"
        with gzip.open(source, "wt") as handle:
            handle.write("@S0R1 comment\nACGT\n+\nIIII\n")
        MODULE.convert(source, destination)
        self.assertEqual(destination.read_text(), ">S0R1\nACGT\n")

    def test_truncated_fastq_fails(self):
        source = self.root / "reads.fq"
        source.write_text("@S0R1\nACGT\n+\n")
        with self.assertRaisesRegex(ValueError, "Truncated"):
            MODULE.convert(source, self.root / "reads.fa")


if __name__ == "__main__":
    unittest.main()
