"""Offline tests for adapter fail-closed behavior (not Tableau 2026.2 compatibility)."""
import pathlib
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
from lxml import etree

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
from _xml import load_xml
from inspect_twb import inventory
from probe_document_api import probe, same_xml_structure
from edit_calculation import edit
from validate_server import assess_response

BASE = b'''<?xml version="1.0" encoding="utf-8"?>
<workbook version="26.2" original-version="25.1"><datasources><datasource name="ds"><column name="[Calculation_123]" caption="KPI"><calculation class="tableau" formula="SUM([Sales])"/></column></datasource></datasources><worksheets><worksheet name="Sheet1"><datasource-dependencies datasource="ds"><column name="[Calculation_123]"/></datasource-dependencies></worksheet></worksheets></workbook>'''


class StubWorkbook:
    def __init__(self, filename):
        self.filename = filename

    def save_as(self, out):
        etree.parse(self.filename).write(out, encoding='utf-8', xml_declaration=True)


class AdapterTests(unittest.TestCase):
    def test_noop_accepts_equivalent_xml(self):
        with tempfile.TemporaryDirectory() as td:
            src = pathlib.Path(td) / 'source.twb'
            src.write_bytes(BASE)
            with patch.dict(sys.modules, {'tableaudocumentapi': types.SimpleNamespace(Workbook=StubWorkbook)}):
                result = probe(src)
            self.assertTrue(result['c14n_identical'])

    def test_noop_blocks_content_change(self):
        class BrokenWorkbook(StubWorkbook):
            def save_as(self, out):
                super().save_as(out)
                p = pathlib.Path(out)
                p.write_bytes(p.read_bytes().replace(b'caption="KPI"', b'caption="Corrupted"'))
        with tempfile.TemporaryDirectory() as td:
            src = pathlib.Path(td) / 'source.twb'
            src.write_bytes(BASE)
            with patch.dict(sys.modules, {'tableaudocumentapi': types.SimpleNamespace(Workbook=BrokenWorkbook)}):
                with self.assertRaisesRegex(ValueError, 'changed XML'):
                    probe(src)

    def test_edit_xml_authorized_with_mocked_xsd(self):
        with tempfile.TemporaryDirectory() as td:
            src, dst = pathlib.Path(td) / 'src.twb', pathlib.Path(td) / 'candidate.twb'
            src.write_bytes(BASE)
            with patch('edit_calculation.validate', return_value=('file', 'schema', '', '25.1')):
                changed, _, _ = edit(src, dst, 'ds::[Calculation_123]', 'AVG([Sales])', 'xml')
            self.assertEqual(changed, ['ds::[Calculation_123]'])
            self.assertIn('AVG([Sales])', load_xml(dst).getroot().xpath('string(./datasources/datasource/column/calculation/@formula)'))

    def test_refuse_output_collision(self):
        with tempfile.TemporaryDirectory() as td:
            src = pathlib.Path(td) / 'src.twb'
            src.write_bytes(BASE)
            with self.assertRaisesRegex(ValueError, 'Output must be a new'):
                edit(src, src, 'ds::[Calculation_123]', 'AVG([Sales])', 'xml')

    def test_inspect_direct_sheet_reference(self):
        with tempfile.TemporaryDirectory() as td:
            p = pathlib.Path(td) / 'a.twb'
            p.write_bytes(BASE)
            field = inventory(p)['datasources'][0]['calculated_fields'][0]
            self.assertEqual(field['used_by_worksheets_direct'], ['Sheet1'])
            self.assertNotIn('formula', field)

    def test_server_response_ok(self):
        self.assertEqual(assess_response(200, {'warnings': [{'message': 'check'}]}), 1)

    def test_server_response_failed(self):
        with self.assertRaisesRegex(ValueError, '1 error'):
            assess_response(200, {'errors': [{'message': 'bad'}]})

    def test_server_response_malformed(self):
        with self.assertRaisesRegex(ValueError, 'Malformed'):
            assess_response(200, {'errors': 'oops'})
        with self.assertRaisesRegex(ValueError, 'JSON object'):
            assess_response(200, [])
        with self.assertRaisesRegex(ValueError, 'JSON object'):
            assess_response(200, {})
        with self.assertRaisesRegex(ValueError, 'HTTP 422'):
            assess_response(422, {'errors': []})


if __name__ == '__main__':
    unittest.main()
