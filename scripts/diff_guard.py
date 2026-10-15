#!/usr/bin/env python3
"""Deny ANY edits except explicitly allowed datasource-column calculation formulas."""
import argparse
import sys
from lxml import etree
from _xml import load_xml, digest


def calculations(root):
    out = {}
    for ds in root.findall("./datasources/datasource"):
        dsid = ds.get("name")
        for col in ds.findall("./column"):
            calc = col.find("./calculation")
            if calc is None:
                continue
            key = f"{dsid}::{col.get('name')}"
            if key in out:
                raise ValueError(f"Duplicate calculated field identity {key!r}; review manually")
            out[key] = calc
    return out


def guard(before, after, allowed):
    orig = load_xml(before)
    cand = load_xml(after)
    if not allowed:
        raise ValueError("Explicit --allow datasource::column required")
    a = calculations(orig.getroot())
    b = calculations(cand.getroot())
    if a.keys() != b.keys():
        raise ValueError("Changed calculated-field inventory or internal field identifiers")
    if not allowed <= a.keys():
        raise ValueError("Unknown allowed key(s): " + ", ".join(sorted(allowed - a.keys())))
    changed = []
    for key in sorted(a.keys()):
        old = a[key].get("formula")
        new = b[key].get("formula")
        if old != new:
            if key not in allowed:
                raise ValueError(f"Unauthorized calculation changed: {key}")
            changed.append(key)
            b[key].set("formula", old if old is not None else "")
            if old is None:
                del b[key].attrib["formula"]
    if not changed:
        raise ValueError("No formula changes found; refusing to claim an edit")
    if etree.tostring(orig, method="c14n", with_comments=True) != etree.tostring(cand, method="c14n", with_comments=True):
        raise ValueError("Other XML changes detected after removing allowed formula differences (including whitespace)")
    return changed


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("original")
    ap.add_argument("candidate")
    ap.add_argument("--allow", action="append", required=True, metavar="DATASOURCE::COLUMN")
    args = ap.parse_args()
    try:
        changed = guard(args.original, args.candidate, set(args.allow))
    except (ValueError, etree.XMLSyntaxError, OSError) as e:
        sys.exit("FAIL: " + str(e))
    print("PASS strictly formula-only diff for:")
    for key in changed:
        print("  " + key)
    print("Original SHA256:", digest(args.original))
    print("Candidate SHA256:", digest(args.candidate))
    print("NOTE: Unchanged structure does not guarantee valid or equivalent formulas. Continue to XSD and Tableau validation.")


if __name__ == "__main__":
    main()
