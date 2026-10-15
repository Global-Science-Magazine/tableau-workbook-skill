#!/usr/bin/env python3
"""Read-only TWB inventory. Does not dump connection information or SQL."""
import argparse
import hashlib
import json
import sys
from _xml import load_xml, digest


def inventory(path, include_formulas=False):
    doc = load_xml(path)
    root = doc.getroot()
    res = {
        "file_sha256": digest(path),
        "version": root.get("version"),
        "original_version": root.get("original-version"),
        "source_build": root.get("source-build"),
        "source_platform": root.get("source-platform"),
        "has_manifest": root.find("./document-format-change-manifest") is not None,
        "datasources": [],
        "reference_method": "Exact worksheet datasource-dependencies column names only; not complete dependency analysis",
        "worksheets": [x.get("name") for x in root.findall("./worksheets/worksheet")],
        "dashboards": [x.get("name") for x in root.findall("./dashboards/dashboard")],
        "stories": [x.get("name") for x in root.findall("./stories/story")],
    }
    for ds in root.findall("./datasources/datasource"):
        fields = []
        for col in ds.findall("./column"):
            calc = col.find("./calculation")
            if calc is None:
                continue
            formula = calc.get("formula", "")
            obj = {
                "name": col.get("name"),
                "caption": col.get("caption"),
                "formula_sha256": hashlib.sha256(formula.encode("utf-8")).hexdigest(),
                "formula_chars": len(formula),
            }
            worksheets = []
            for ws in root.findall("./worksheets/worksheet"):
                for deps in ws.findall(".//datasource-dependencies"):
                    if deps.get("datasource") == ds.get("name") and any(
                        x.get("name") == col.get("name") for x in deps.findall("./column")
                    ):
                        worksheets.append(ws.get("name"))
                        break
            obj["used_by_worksheets_direct"] = sorted(set(worksheets))
            if include_formulas:
                obj["formula"] = formula
            fields.append(obj)
        res["datasources"].append({"name": ds.get("name"), "caption": ds.get("caption"),
                                   "calculated_fields": fields})
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("twb")
    ap.add_argument("--include-formulas", action="store_true", help="show expressions; may disclose private business logic")
    args = ap.parse_args()
    try:
        result = inventory(args.twb, args.include_formulas)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        sys.exit("FAIL inspect: " + str(e))


if __name__ == "__main__":
    main()
