import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
spec=importlib.util.spec_from_file_location("combine_resources",ROOT/"scripts/combine_resources.py")
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)

class CombineResourcesTests(unittest.TestCase):
    def test_sum_time_and_max_memory(self):
        with tempfile.TemporaryDirectory() as directory:
            paths=[]
            for number,(wall,user,system,memory) in enumerate(((1,2,3,100),(4,5,6,80))):
                path=Path(directory)/str(number)
                path.write_text(f"wall_seconds={wall}\nuser_cpu_seconds={user}\nsystem_cpu_seconds={system}\nmax_rss_kb={memory}\nexit_code=0\n")
                paths.append(path)
            result=module.combine(paths)
            self.assertEqual(result["wall_seconds"],5)
            self.assertEqual(result["user_cpu_seconds"],7)
            self.assertEqual(result["system_cpu_seconds"],9)
            self.assertEqual(result["max_rss_kb"],100)
if __name__=="__main__": unittest.main()
