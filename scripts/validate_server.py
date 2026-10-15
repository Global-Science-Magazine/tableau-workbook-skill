#!/usr/bin/env python3
"""Explicit, authenticated Tableau Cloud/Server REST validation; never publishes."""
import argparse
import json
import os
import pathlib
import sys
from urllib.parse import urlparse
import requests


def assess_response(status, body):
    """Fail closed on malformed 200 bodies or validation errors; warnings need review."""
    if not isinstance(body, dict) or not body or not any(k in body for k in ("timestamp", "errors", "warnings")):
        raise ValueError("Expected a Tableau validation response JSON object with validation metadata")
    errors = body.get("errors", [])
    warnings = body.get("warnings", [])
    if not isinstance(errors, list) or not isinstance(warnings, list):
        raise ValueError("Malformed validation payload: errors/warnings must be lists when present")
    if status != 200:
        raise ValueError(f"Tableau validation returned HTTP {status}; errors={len(errors)}, warnings={len(warnings)}")
    if errors:
        raise ValueError(f"Tableau validation reported {len(errors)} error(s)")
    return len(warnings)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("twb")
    ap.add_argument("--base-url", default=os.getenv("TABLEAU_BASE_URL"))
    ap.add_argument("--site-id", default=os.getenv("TABLEAU_SITE_ID"))
    ap.add_argument("--show-details", action="store_true", help="print Tableau response (may contain confidential names)")
    args = ap.parse_args()
    token = os.getenv("TABLEAU_AUTH_TOKEN")
    p = pathlib.Path(args.twb)
    if p.suffix.lower() != ".twb" or not p.is_file():
        sys.exit("FAIL: only existing .twb files supported")
    if not args.base_url or not args.site_id or not token:
        sys.exit("FAIL: supply TABLEAU_BASE_URL, TABLEAU_SITE_ID and TABLEAU_AUTH_TOKEN (Tableau session token)")
    base = args.base_url.rstrip("/")
    u = urlparse(base)
    if u.scheme != "https" or not u.netloc or u.username or u.password or u.path not in ("", "/") or u.query or u.fragment:
        sys.exit("FAIL: BASE_URL must be HTTPS origin only (e.g. https://example.com); no embedded credentials")
    if any(x in args.site_id for x in ("/", "?", "#")):
        sys.exit("FAIL: invalid site-id")
    endpoint = f"{base}/api/3.29/sites/{args.site_id}/workbooks/validateWorkbook"
    print(f"Sending TWB bytes to authorized Tableau service: {u.netloc} (validation only; no publishing).", flush=True)
    try:
        with p.open("rb") as f:
            response = requests.post(
                endpoint,
                headers={"X-Tableau-Auth": token, "Accept": "application/json"},
                files={"tableau_workbook": (p.name, f, "application/xml")},
                timeout=(15, 120),
                allow_redirects=False,  # avoid sending credentials/data to unexpected hosts
            )
    except requests.RequestException as e:
        sys.exit("FAIL network: " + str(e))
    try:
        result = response.json()
    except ValueError:
        sys.exit(f"FAIL: HTTP {response.status_code}, unexpected non-JSON response (not printed to avoid exposing server details)")
    print("HTTP", response.status_code)
    if args.show_details:
        print(json.dumps(result, indent=2, ensure_ascii=False)[:20000])
    try:
        warnings = assess_response(response.status_code, result)
    except ValueError as e:
        sys.exit("FAIL remote validation: " + str(e) +
                 " (use --show-details to inspect server diagnostics locally)")
    print("PASS server-side Tableau load/semantic validation; NOT a business-result or local Desktop test.")
    if warnings:
        print(f"REVIEW REQUIRED: server reported {warnings} warning(s). Use --show-details locally if authorized.")


if __name__ == "__main__":
    main()
