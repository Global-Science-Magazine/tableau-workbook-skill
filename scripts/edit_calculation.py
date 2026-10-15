#!/usr/bin/env python3
"""Create a NEW formula-only TWB candidate using a gated Document API or XML adapter."""
import argparse
from pathlib import Path
import sys
from lxml import etree
from _xml import load_xml, digest
from diff_guard import guard
from validate_twb import validate
from probe_document_api import probe


def _field_id(key):
    if '::' not in key:
        raise ValueError('Use an exact datasource-name::[Column_Internal_Name] identifier')
    dsid, colid = key.split('::', 1)
    if not dsid or not colid:
        raise ValueError('Both datasource and column internal names are required')
    return dsid, colid


def _xml_adapter(original, output, dsid, colid, formula):
    tree = load_xml(original)
    matches = []
    for ds in tree.getroot().findall('./datasources/datasource'):
        if ds.get('name') != dsid:
            continue
        for col in ds.findall('./column'):
            if col.get('name') == colid and col.find('./calculation') is not None:
                matches.append(col.find('./calculation'))
    if len(matches) != 1:
        raise ValueError(f'Expected one existing calculation, found {len(matches)}: {dsid}::{colid}')
    matches[0].set('formula', formula)
    tree.write(str(output), encoding='utf-8', xml_declaration=True)


def _document_adapter(original, output, dsid, colid, formula):
    probe(original)  # must pass no-op roundtrip, not just load
    try:
        from tableaudocumentapi import Workbook
    except ImportError as e:
        raise RuntimeError('Run: pip install tableaudocumentapi==0.11') from e
    wb = Workbook(str(original))
    found = [ds for ds in wb.datasources if ds.name == dsid]
    if len(found) != 1:
        raise ValueError(f'Expected exactly one datasource {dsid!r}, found {len(found)}')
    fields = [f for f in found[0].fields.values() if f.id == colid and f.calculation is not None]
    if len(fields) != 1:
        raise ValueError(f'Expected exactly one existing calculated field {colid!r}, found {len(fields)}')
    fields[0].calculation = formula  # source-level capability; NOT supported in Document API README
    wb.save_as(str(output))


def edit(original, output, key, formula, backend='document-api'):
    original = Path(original).resolve(strict=True)
    output = Path(output).resolve()
    if output.suffix.lower() != ".twb" or original == output or output.exists() or output.is_symlink():
        raise ValueError('Output must be a new .twb path (not a symlink) and cannot be the input file')
    if not formula.strip():
        raise ValueError('Formula must not be empty')
    dsid, colid = _field_id(key)
    validate(original)   # locked official 2026.2 XSD baseline required
    if backend == 'document-api':
        _document_adapter(original, output, dsid, colid, formula)
    elif backend == 'xml':
        _xml_adapter(original, output, dsid, colid, formula)
    else:
        raise ValueError(f'Unknown backend: {backend}')
    try:
        changed = guard(original, output, {key})
        validate(output)
    except Exception as e:
        raise ValueError(f'Candidate written to {output}, but static gate FAILED: {e}') from e
    return changed, digest(original), digest(output)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('original')
    ap.add_argument('--output', required=True, help='new candidate .twb path (must not exist)')
    ap.add_argument('--allow', required=True, help='one exact datasource-name::[Column_Internal_Name]')
    ap.add_argument('--formula-file', required=True, help='UTF-8 text containing replacement Tableau formula')
    ap.add_argument('--backend', choices=['document-api', 'xml'], default='document-api',
                    help='document-api first; XML requires explicit selection, never silent fallback')
    args = ap.parse_args()
    try:
        formula = Path(args.formula_file).read_text(encoding='utf-8').rstrip('\r\n')
        changed, old_sha, new_sha = edit(args.original, args.output, args.allow, formula, args.backend)
    except (RuntimeError, ValueError, OSError, etree.XMLSyntaxError, etree.XMLSchemaError) as e:
        sys.exit('FAIL: ' + str(e))
    print('PASS formula-only diff + baseline/candidate locked XSD; changed:', ', '.join(changed))
    print('Backend:', args.backend)
    print('Original SHA256:', old_sha)
    print('Candidate SHA256:', new_sha)
    print('NOT YET VERIFIED: Tableau Desktop opening, semantic validation, KPI/query results.')


if __name__ == '__main__':
    main()
