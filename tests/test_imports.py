import sys, types, unittest

class ImportTests(unittest.TestCase):
    def test_modules_import_without_running_streamlit_ui(self):
        # Streamlit is an external runtime dependency; a tiny import stub lets us
        # validate Python module wiring in offline build environments.
        fake = types.ModuleType('streamlit')
        sys.modules.setdefault('streamlit', fake)
        import modules.tab1_hoso, modules.tab2_trithuc, modules.tab3_kham
        import modules.tab4_phcn, modules.tab5_doi_soat, modules.tab6_theo_doi
        import core.clinical_engine, core.diagnostic_audit, database.storage
        for module in (modules.tab1_hoso, modules.tab2_trithuc, modules.tab3_kham,
                       modules.tab4_phcn, modules.tab5_doi_soat, modules.tab6_theo_doi):
            self.assertTrue(callable(module.render))

if __name__ == '__main__':
    unittest.main()
