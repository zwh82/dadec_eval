import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("method_config", ROOT / "scripts/method_config.py")
methods = importlib.util.module_from_spec(spec); spec.loader.exec_module(methods)

class MethodSelectionTests(unittest.TestCase):
    def test_all_and_subset(self):
        self.assertEqual(len(methods.select_methods("all")), 11)
        self.assertEqual(methods.select_methods("DADEC,F_HERO,CoLoRMap"),
                         ["dadec", "f_hero", "colormap"])

    def test_duplicate_and_unknown_fail(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            methods.select_methods("DADEC,dadec")
        with self.assertRaisesRegex(ValueError, "Unknown"):
            methods.select_methods("missing")

class ParameterTests(unittest.TestCase):
    def config(self, profile="tool_defaults", **values):
        return {"parameter_profile": profile, "parameters": {"profiles": {
            "tool_defaults": {}, "study": {"fmlrc_k1": 21, "fmlrc_k2": 59}
        }, "hero_split": 10, "hero_iterations": 3, "lordec_solid": 5},
        "dadec": {"split_number": 1, "msa_threshold": 0.08,
                  "abundance_min1": 2, "abundance_min2": 1}, **values}

    def test_tool_defaults_emit_no_k_flags(self):
        profile, values = methods.resolve_k_values(self.config())
        self.assertEqual(profile, "tool_defaults"); self.assertEqual(values, {})
        for method in methods.METHOD_LABELS:
            self.assertEqual(methods.k_args(method, values), [])

    def test_study_and_override(self):
        _, values = methods.resolve_k_values(self.config("study", fmlrc_k2=49))
        self.assertEqual(methods.k_args("fmlrc", values), ["-k", "21", "49"])
        self.assertEqual(methods.k_args("f_hero", values), ["-k", "21", "49"])

    def test_invalid_even_k_and_lordec_default_fail(self):
        with self.assertRaisesRegex(ValueError, "odd"):
            methods.resolve_k_values(self.config(fmlrc_k1=22))
        with self.assertRaisesRegex(ValueError, "requires -k"):
            methods.validate_lordec(["lordec"], {})

    def test_coverage_parameters_override_dataset_defaults(self):
        config=self.config("study")
        config["parameters"]["by_coverage"]={"10x": {
            "profiles": {"study": {"fmlrc_k2": 31, "lordec_k": 21}},
            "settings": {"hero_split": 12, "dadec_threshold": 0.1},
        }}
        _, values=methods.resolve_coverage_parameters(config,"10x")
        self.assertEqual(values["fmlrc_k2"],31)
        self.assertEqual(values["lordec_k"],21)
        self.assertEqual(values["hero_split"],12)
        self.assertEqual(values["dadec_threshold"],0.1)

if __name__ == "__main__": unittest.main()
