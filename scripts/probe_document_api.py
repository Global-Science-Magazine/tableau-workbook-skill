#!/usr/bin/env python3
"""Test Tableau Document API 0.11 no-op save_as on a real TWB; never overwrite input."""
import argparse
from pathlib import Path
import sys
import tempfile
from lxml import etree
from _xml import load_xml, digest


def same_xml_structure(before, after):
    """Fail closed on any C14N XML change, including whitespace text and comments."""
    a = load_xml(before)
    b = load_xml(after)
    return etree.tostring(a, method='c14n', with_comments=True) == etree.tostring(b, method='c14n', with_comments=True)


def probe(input_path, output_path=None):
    input_path = Path(input_path).resolve(strict=True)
    load_xml(input_path)
    try:
        from tableaudocumentapi import Workbook
    except ImportError as e:
        raise RuntimeError('Document API not installed. Run: pip install tableaudocumentapi==0.11') from e
    if output_path is None:
        with tempfile.TemporaryDirectory(prefix='tableau-docapi-probe-') as td:
            return _roundtrip(Workbook, input_path, Path(td) / 'noop.twb')
    dest = Path(output_path).resolve()
    if dest.suffix.lower() != ".twb" or dest == input_path or dest.exists() or dest.is_symlink():
        raise ValueError('Output must be a new .twb path, different from input')
    dest.parent.mkdir(parents=True, exist_ok=True)
    return _roundtrip(Workbook, input_path, dest)


def _roundtrip(workbook_type, before, after):
    workbook_type(str(before)).save_as(str(after))
    load_xml(after)
    result = {
        'before_sha256': digest(before),
        'roundtrip_sha256': digest(after),
        'byte_identical': digest(before) == digest(after),
        'c14n_identical': same_xml_structure(before, after),
        'result_path': str(after),
    }
    if not result['c14n_identical']:
        raise ValueError(
            'Document API changed XML during no-op roundtrip. Block this backend for this workbook; '
            'review a separate semantic diff/desktop test before overriding policy. '
            'To retain failing output for inspection, rerun with --output NEW_PATH.twb.'
        )
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('original')
    ap.add_argument('--output', help='optional path to keep the no-op output; must not already exist')
    args = ap.parse_args()
    try:
        r = probe(args.original, args.output)
    except (RuntimeError, ValueError, OSError, etree.XMLSyntaxError) as e:
        sys.exit('FAIL: ' + str(e))
    print('PASS Document API 0.11 no-op canonical-XML roundtrip')
    print('Original SHA256:', r['before_sha256'])
    print('Roundtrip SHA256:', r['roundtrip_sha256'])
    print('Byte-identical:', r['byte_identical'])
    print('NOTE: This is not a Tableau 2026.2 compatibility guarantee. Validate saved output against XSD and Desktop.')


if __name__ == '__main__':
    main()
