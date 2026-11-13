import tempfile, unittest
from pathlib import Path
from database import storage
class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.old=storage.DB_PATH; storage.DB_PATH=Path(self.tmp.name)/"db.sqlite"; storage.init_db()
    def tearDown(self): storage.DB_PATH=self.old; self.tmp.cleanup()
    def test_save_and_read_visit(self):
        vid=storage.save_visit({"name":"Test","phone":"0900000000","age":1990,"job":""},"Khớp gối",{"pain":3},"summary",{"result":"ok"},"report")
        self.assertGreater(vid,0); self.assertEqual(len(storage.list_visits()),1)
        detail=storage.get_visit_detail(vid); self.assertEqual(detail["input"]["pain"],3)
        self.assertEqual(len(storage.list_patient_visits("0900000000")),1)

    def test_save_without_phone_using_name_and_birth_year(self):
        vid=storage.save_visit({"name":"Nguyen Van A","age":1985,"phone":""},"Khớp vai",{"pain":2},"summary",{"result":"review"},"report")
        detail=storage.get_visit_detail(vid)
        self.assertEqual(detail["name"],"Nguyen Van A")
        self.assertEqual(detail["birth_year"],1985)
        rows=storage.list_visits()
        self.assertEqual(rows[0]["phone"],"")
        self.assertEqual(len(storage.list_patient_visits_by_id(rows[0]["patient_id"])),1)
if __name__=="__main__": unittest.main()
