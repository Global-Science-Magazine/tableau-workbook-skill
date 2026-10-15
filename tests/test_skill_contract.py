"""Static Agent Skills spec and packaging checks; NOT behavioral model evals."""
import json
import pathlib
import re
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = ROOT / 'SKILL.md'


class SkillContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = SKILL.read_text(encoding='utf-8')
        assert raw.startswith('---\n'), 'missing frontmatter'
        cls.frontmatter, cls.body = raw[4:].split('\n---\n', 1)
        cls.md = raw

    def test_agent_skills_frontmatter(self):
        data = {}
        lines = self.frontmatter.splitlines()
        for line in lines:
            if line.startswith('name: '):
                data['name'] = line.partition(': ')[2]
            elif line.startswith('description: >-'):
                data['description'] = ' '.join(x.strip() for x in lines[lines.index(line)+1:] if x.strip())
            elif not line.startswith('  '):
                self.fail(f'Unexpected frontmatter key: {line}')
        self.assertEqual(set(data), {'name', 'description'})
        self.assertEqual(data['name'], ROOT.name)
        self.assertRegex(data['name'], r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
        self.assertLessEqual(len(data['name']), 64)
        self.assertTrue(20 <= len(data['description']) <= 1024)
        for term in ('.twb', '2026', 'computed', 'calculated fields', 'XSD'):
            if term == 'computed':
                continue
            self.assertIn(term.lower(), data['description'].lower())

    def test_skill_concision_and_relative_refs(self):
        self.assertLess(len(self.md.splitlines()), 180)
        self.assertNotIn('TODO', self.md)
        paths = re.findall(r'\]\((references/[^)#]+)\)', self.body)
        self.assertGreaterEqual(len(paths), 3)
        for path in paths:
            self.assertTrue((ROOT / path).exists(), path)

    def test_all_scripts_and_schema_paths(self):
        for name in ('fetch_schema', 'inspect_twb', 'diff_guard', 'validate_twb',
                     'validate_server', 'probe_document_api', 'edit_calculation'):
            self.assertTrue((ROOT / 'scripts' / f'{name}.py').is_file())
        from pathlib import Path
        sys.path.insert(0, str(ROOT / 'scripts'))
        import validate_twb, fetch_schema
        self.assertEqual(validate_twb.XSD, ROOT / 'references/schemas/twb_2026.2.0.xsd')
        self.assertEqual(fetch_schema.XSD, ROOT / 'references/schemas/twb_2026.2.0.xsd')
        self.assertEqual(validate_twb.LOCK, ROOT / 'references/schemas/schema.lock.json')

    def test_openai_interface_metadata(self):
        raw = (ROOT / 'agents' / 'openai.yaml').read_text()
        self.assertIn('interface:', raw)
        self.assertIn('display_name:', raw)
        self.assertIn('short_description:', raw)
        self.assertIn('default_prompt:', raw)

    def test_evals_cover_stop_conditions(self):
        data = json.loads((ROOT / 'evals' / 'cases.json').read_text())
        keys = [r['id'] for r in data]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertGreaterEqual(len(keys), 8)
        for case in data:
            self.assertTrue(case['query'] and case['expected'] and case['forbidden'])

    def test_fetch_schema_fails_closed_when_absent(self):
        if (ROOT / 'references/schemas/schema.lock.json').exists():
            self.skipTest('schema already provisioned in local user environment')
        cp = subprocess.run([sys.executable, str(ROOT/'scripts/fetch_schema.py'), '--check'],
                            capture_output=True, text=True)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn('schema/lock missing', cp.stderr)

    def test_synthetic_schema_header_matches_expected(self):
        import sys
        sys.path.insert(0, str(ROOT / 'scripts'))
        from fetch_schema import verify
        synthetic = b'''<!--\n Tableau Workbook Schema (TWB)\n Published: 2026-06-15T23:32:07Z\n Build: 20262.26.0528.2205\n--><xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" version="2026.2.0"/>'''
        pub, build = verify(synthetic)
        self.assertEqual(pub, '2026-06-15T23:32:07Z')
        self.assertEqual(build, '20262.26.0528.2205')


if __name__ == '__main__':
    unittest.main()
