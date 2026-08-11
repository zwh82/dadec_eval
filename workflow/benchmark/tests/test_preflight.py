import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "scripts/preflight.py"
spec = importlib.util.spec_from_file_location("preflight", path)
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)


class RequiredToolsTests(unittest.TestCase):
    def test_normal_run_keeps_method_dependencies(self):
        tools = preflight.required_tools(["fmlrc"], "metaquast")
        self.assertTrue(
            {"conda", "python", "runner_python", "time", "seqkit",
             "metaquast", "fmlrc", "fmlrc_convert", "ropebwt2"}.issubset(tools)
        )

    def test_evaluation_only_skips_correction_dependencies(self):
        self.assertEqual(
            preflight.required_tools(["fmlrc"], "metaquast", evaluation_only=True),
            {"conda", "python", "metaquast"},
        )


if __name__ == "__main__":
    unittest.main()
