"""Small synthetic fixtures test diff containment; not Tableau-valid sample workbooks."""
import pathlib
import sys
import tempfile
import unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
from diff_guard import guard
from _xml import load_xml

BASE = b'''<?xml version="1.0" encoding="utf-8"?>
<workbook version="26.2" original-version="26.2"><datasources><datasource name="ds"><column name="[Calculation_123]" caption="KPI"><calculation class="tableau" formula="SUM([Sales])" /></column></datasource></datasources></workbook>'''

class GuardTest(unittest.TestCase):
    def run_case(self, changed, allow=('ds::[Calculation_123]',)):
        with tempfile.TemporaryDirectory() as td:
            a=pathlib.Path(td)/'a.twb'; b=pathlib.Path(td)/'b.twb'
            a.write_bytes(BASE); b.write_bytes(changed)
            return guard(a, b, set(allow))

    def test_formula_change_only(self):
        self.assertEqual(self.run_case(BASE.replace(b'SUM([Sales])', b'AVG([Sales])')), ['ds::[Calculation_123]'])

    def test_version_tampering_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Other XML changes'):
            self.run_case(BASE.replace(b'SUM([Sales])', b'AVG([Sales])').replace(b'version="26.2"', b'version="26.1"'))

    def test_unauthorized_change_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Unknown allowed'):
            self.run_case(BASE.replace(b'SUM([Sales])', b'AVG([Sales])'), allow=('ds::[Calculation_999]',))

    def test_cannot_hide_nonformula_change(self):
        with self.assertRaisesRegex(ValueError, 'Other XML changes'):
            self.run_case(BASE.replace(b'SUM([Sales])', b'AVG([Sales])').replace(b'caption="KPI"', b'caption="New"'))

    def test_outside_root_comment_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Other XML changes'):
            self.run_case(BASE.replace(b'SUM([Sales])', b'AVG([Sales])') + b'<!-- injected -->')

    def test_no_change_is_not_pass(self):
        with self.assertRaisesRegex(ValueError, 'No formula changes'):
            self.run_case(BASE)

    def test_doctype_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)/'bad.twb'
            p.write_bytes(BASE.replace(b'<workbook ', b'<!DOCTYPE workbook [<!ENTITY x "value">]><workbook ', 1))
            with self.assertRaisesRegex(ValueError, "DOCTYPE"):
                load_xml(p)

if __name__ == '__main__':
    unittest.main()
