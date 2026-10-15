#!/usr/bin/env python3
"""Install or stage (not overwrite) Tableau's official 2026.2 XSD."""
import argparse
import hashlib
import json
import pathlib
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMAS = ROOT / "references" / "schemas"
XSD = SCHEMAS / "twb_2026.2.0.xsd"
LOCK = SCHEMAS / "schema.lock.json"
UPSTREAM = "https://raw.githubusercontent.com/tableau/tableau-document-schemas"
SCHEMA_PATH = "schemas/2026_2/twb_2026.2.0.xsd"
DEFAULT_REF = "a705484638d79b9bec830a66cb0004ca75f999e0"  # official initial 2026.2 XSD commit
URL = f"{UPSTREAM}/{DEFAULT_REF}/{SCHEMA_PATH}"


def verify(content):
    tree = ET.fromstring(content)
    if tree.tag != "{http://www.w3.org/2001/XMLSchema}schema":
        raise ValueError("Downloaded data is not an XML Schema")
    if tree.attrib.get("version") != "2026.2.0":
        raise ValueError("Unexpected schema version: " + str(tree.attrib.get("version")))
    head = content[:3000].decode("utf-8", "replace")
    pub = re.search(r"Published:\s*(\S+)", head)
    build = re.search(r"Build:\s*([^\r\n]+)", head)
    if not (pub and build and "Tableau Workbook Schema (TWB)" in head):
        raise ValueError("Missing Tableau schema metadata; refusing unrecognized XSD")
    return pub.group(1), build.group(1).strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="check local SHA-256 lock without downloading")
    group.add_argument("--candidate", action="store_true", help="stage upstream as *.candidate without replacing pinned schema")
    ap.add_argument("--ref", default=DEFAULT_REF, help="upstream git ref: defaults to audited 2026.2 commit; main or another 40-hex commit allowed for reviewed updates")
    args = ap.parse_args()
    if args.ref != "main" and not re.fullmatch(r"[0-9a-fA-F]{40}", args.ref):
        sys.exit("FAIL: --ref must be main or a 40-character Git commit hash")
    upstream_url = f"{UPSTREAM}/{args.ref}/{SCHEMA_PATH}"
    SCHEMAS.mkdir(exist_ok=True)
    if args.check:
        if not XSD.is_file() or not LOCK.is_file():
            sys.exit("FAIL: schema/lock missing. Run: python scripts/fetch_schema.py")
        try:
            content = XSD.read_bytes()
            pub, build = verify(content)
            lock = json.loads(LOCK.read_text(encoding="utf-8"))
            sha = hashlib.sha256(content).hexdigest()
            if lock.get("sha256") != sha or lock.get("schema_version") != "2026.2.0":
                sys.exit("FAIL: schema SHA-256 or version mismatches local lock")
            print(f"PASS locked official schema: {sha}\nversion=2026.2.0 published={pub} build={build}")
        except (ValueError, ET.ParseError, OSError, json.JSONDecodeError) as e:
            sys.exit("FAIL: " + str(e))
        return
    if not args.candidate and (XSD.exists() or LOCK.exists()):
        sys.exit("REFUSED: schema/lock already exists. Use --check or --candidate; do not overwrite blindly.")
    req = urllib.request.Request(upstream_url, headers={"User-Agent": "tableau-2026.2-agent-harness/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=35) as resp:
            data = resp.read(10_000_000)
        pub, build = verify(data)
    except Exception as e:
        sys.exit(f"FAIL: cannot fetch trusted Tableau XSD from {upstream_url}\n{type(e).__name__}: {e}")
    sha = hashlib.sha256(data).hexdigest()
    record = {
        "source": upstream_url,
        "source_ref": args.ref,
        "schema_version": "2026.2.0",
        "published": pub,
        "source_build": build,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "sha256": sha,
        "sha256_scope": "entire original XSD file bytes",
    }
    dest = XSD.with_suffix(".xsd.candidate") if args.candidate else XSD
    lock_dest = SCHEMAS / ("schema.lock.candidate.json" if args.candidate else "schema.lock.json")
    # Exclusive creation. Failure never truncates the pinned files.
    try:
        with dest.open("xb") as f:
            f.write(data)
        with lock_dest.open("x", encoding="utf-8") as f:
            json.dump(record, f, indent=2, ensure_ascii=False)
            f.write("\n")
    except FileExistsError:
        sys.exit(f"REFUSED: already exists: {dest} or {lock_dest}; remove only staged .candidate files deliberately")
    print(f"STAGED: {dest}\nLOCK: {lock_dest}\nSHA256: {sha}\nPublished: {pub}; source build: {build}")
    if args.candidate:
        print("Candidate only. Compare against locked schema before any authorized replacement.")


if __name__ == "__main__":
    main()
