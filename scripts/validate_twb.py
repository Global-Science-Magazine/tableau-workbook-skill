#!/usr/bin/env python3
"""Offline secure parse, version gate, SHA lock, and Tableau 2026.2 XSD check."""
import argparse
import json
import pathlib
import sys
from lxml import etree
from _xml import load_xml, digest

ROOT = pathlib.Path(__file__).resolve().parent.parent
XSD = ROOT / "references/schemas/twb_2026.2.0.xsd"
LOCK = ROOT / "references/schemas/schema.lock.json"


def validate(path):
    doc = load_xml(path)
    root = doc.getroot()
    v = root.get("version")
    ov = root.get("original-version")
    if v != "26.2":
        raise ValueError(f"Expected workbook version=26.2 for the 2026.2 XSD; got version={v!r}, original-version={ov!r}. Migrate a copy using Tableau Desktop, never rewrite the version attribute.")
    # original-version is provenance; preserve it rather than forcing equality with current version.
    if not XSD.exists() or not LOCK.exists():
        raise ValueError("Missing XSD or schema.lock.json. Run python scripts/fetch_schema.py")
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    if lock.get("schema_version") != "2026.2.0" or lock.get("sha256") != digest(XSD):
        raise ValueError("Schema lock mismatch; XSD untrusted/modified; run python scripts/fetch_schema.py --check")
    schema_parser = etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True, recover=False)
    xsd_doc = etree.parse(str(XSD), schema_parser)
    schema = etree.XMLSchema(xsd_doc)
    if not schema.validate(doc):
        errors = [f"line {e.line} col {e.column}: {e.message}" for e in schema.error_log]
        raise ValueError("XSD validation failed:\n" + "\n".join(errors[:30]) + ("\n..." if len(errors)>30 else ""))
    return digest(path), lock.get("sha256"), root.get("source-build"), ov


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("twb")
    args = ap.parse_args()
    try:
        file_sha, schema_sha, source_build, original_version = validate(args.twb)
    except (ValueError, etree.XMLSyntaxError, etree.XMLSchemaParseError, OSError, json.JSONDecodeError) as e:
        sys.exit("FAIL: " + str(e))
    print(f"PASS XML + version=26.2 + official locked XSD 2026.2.0\nTWB SHA256: {file_sha}\nXSD SHA256: {schema_sha}\nsource-build: {source_build or 'unspecified'}")
    if original_version != "26.2":
        print(f"REVIEW: original-version={original_version!r} differs from version=26.2; retained as provenance. Verify this matches the saved workbook and XSD.")
    print("NOTE: This does NOT test Tableau formula validity, data, rendering, or business semantics.")


if __name__ == "__main__":
    main()
