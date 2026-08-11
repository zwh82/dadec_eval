import gzip
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("prepare_reads",ROOT/"scripts/prepare_reads.py")
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)

class PrepareReadsTests(unittest.TestCase):
    def test_fasta_is_copied_without_seqkit(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/"reads.fa.gz"; target=Path(d)/"reads.fa"
            with gzip.open(source,"wt") as out: out.write(">r1\nACGT\n")
            module.prepare(source,target,"/does/not/exist")
            self.assertEqual(target.read_text(),">r1\nACGT\n")
if __name__=="__main__": unittest.main()
