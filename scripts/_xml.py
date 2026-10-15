"""Hardened local XML read helpers. Never fetch external entities."""
from pathlib import Path
from lxml import etree


def load_xml(path):
    path = Path(path)
    if path.suffix.lower() != ".twb":
        raise ValueError(f"Expected .twb (not .twbx): {path}")
    parser = etree.XMLParser(
        resolve_entities=False,
        load_dtd=False,
        no_network=True,
        remove_blank_text=False,
        recover=False,
        huge_tree=False,
    )
    doc = etree.parse(str(path), parser)
    if doc.docinfo.doctype:
        raise ValueError("DOCTYPE/DTD is not permitted in TWB input")
    if doc.getroot().tag != "workbook":
        raise ValueError(f"Root must be <workbook>, got {doc.getroot().tag!r}")
    return doc


def digest(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()
