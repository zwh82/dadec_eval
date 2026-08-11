import importlib.util
import sys
import unittest
import tempfile
from types import SimpleNamespace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("run_method", ROOT / "scripts/run_method.py")
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)

class CommandFormattingTests(unittest.TestCase):
    def test_shell_join_quotes_and_supports_non_strings(self):
        self.assertEqual(module.shell_join(["tool", "a b", 21]), "tool 'a b' 21")

    def test_lordec_uses_isolated_short_read_path(self):
        with tempfile.TemporaryDirectory() as directory:
            work=Path(directory)/"work"; work.mkdir()
            short=Path(directory)/"input.fa"; short.write_text(">r\nACGT\n")
            args=SimpleNamespace(k_args=["-k","21"],lordec_solid=5,long=str(short),
                                 short=str(short),lordec="/bin/false",threads=1)
            with open(Path(directory)/"log","w") as log, self.assertRaises(Exception):
                module.lordec_rounds(args,work,1,log)
            self.assertEqual((work/"short.fa").resolve(),short.resolve())

    def test_run_uses_requested_working_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"command.log"
            with open(path,"w") as log:
                module.run(["/bin/sh","-c","pwd"],log,cwd=directory)
            self.assertEqual(path.read_text().splitlines()[-1],directory)

if __name__ == "__main__": unittest.main()
