import unittest
from core.knowledge_loader import load_knowledge
class KnowledgeTests(unittest.TestCase):
 def test_json_sets_load(self):
  self.assertEqual(len(load_knowledge("clinical_manual.json")),4)
  self.assertEqual(len(load_knowledge("clinical_tests/region_tests.json")),9)
  self.assertEqual(len(load_knowledge("rehabilitation/exercise_library.json")),9)
if __name__=="__main__": unittest.main()
