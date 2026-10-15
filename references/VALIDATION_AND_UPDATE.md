# Tableau 2026.2 — Validation, compatibility tests and updates

## Gate order: fail closed

| Gate | Tool | Pass means | Not tested |
|---|---|---|---|
| Parse/format | `inspect_twb.py`, `_xml.py` | `.twb` safe XML parse, metadata inventory | Tableau validity |
| Version/XSD baseline | `validate_twb.py original.twb` | `version="26.2"`, verified local schema lock, XSD pass | formula/data correctness |
| Adapter no-op (only for Document API) | `probe_document_api.py original.twb` | `Workbook.save_as()` did not alter canonical XML in a no-change run | Tableau behavior, DB connectivity |
| Controlled editing | `edit_calculation.py ... --backend document-api` or explicitly `xml` | only one allowed existing `calculation@formula` changed; baseline and candidate XSD passed | semantic correctness |
| Independent diff | `diff_guard.py original candidate --allow ...` | no unauthorised XML changes, including whitespace text/comments | Formula syntax validity |
| Server load (optional) | `validate_server.py candidate.twb` | Server/Cloud API semantic-load verification passed | local Desktop drivers/business KPI |
| Desktop runtime | human/authorized Desktop tools | workbook actually loads and queries run locally | untested business scenarios |
| Business tests | compare agreed source/query/filter output | KPI changed only as intended | anything not in coverage |

**A missing gate must be reported as NOT VERIFIED, never silently treated as passed.** A validation failure cannot be suppressed by stripping unknown XML tags or changing root version/feature manifest.

### Install + initialize XSD

Run commands from the installed skill directory, or use absolute script paths. The XSD and lock live under `references/schemas/`. Local commands do not require Tableau Server.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/fetch_schema.py                         # fetch official 2026.2 XSD once
python scripts/fetch_schema.py --check                 # SHA-256 check on local file + lock
python scripts/inspect_twb.py /path/to/original.twb
python scripts/validate_twb.py /path/to/original.twb
```

The default source is pinned to the original 2026.2 schema commit `a705484638d79b9bec830a66cb0004ca75f999e0`. For a different reviewed source use `python scripts/fetch_schema.py --ref <40-hex-commit>`; `references/schemas/schema.lock.json` records source URL/ref and SHA-256. `--check` verifies local integrity, *not independent cryptographic authenticity* of a first-time upstream download. Do not commit proprietary Workbook files, credential env variables or server responses.

`validate_twb.py` requires **`version=26.2`**. It preserves `original-version`, including a legacy origin string, but highlights it for review. The official schema may reject old root formats; use a Tableau Desktop-saved 2026.2 **copy** if explicit migration is approved.

### Document API compatibility preflight

Document API v0.11 is **As-Is**, last formal release 2022; the calculation setter exists in source but is not part of README's supported feature claims. Install only if needed:

```bash
pip install tableaudocumentapi==0.11
python scripts/probe_document_api.py /path/to/original.twb
# Optional retained no-op output for manual inspection (path must be new):
python scripts/probe_document_api.py /path/to/original.twb --output /path/to/docapi-noop.twb
```

This test opens the TWB with Document API and calls `Workbook.save_as` **without changes**. The probe compares C14N XML after safe parsing, including comments and whitespace nodes; byte-identical status is separately reported. If structural equality fails, refuse Document API as write backend for this Workbook. A passing no-op is **necessary but insufficient**; optional Desktop check of the no-op output is recommended before first production use. The library may reserialize or repack `.twbx`; `.twbx` writes are not enabled in this harness.

### Formula update

```bash
python scripts/inspect_twb.py /path/to/original.twb
# Put exact replacement Tableau expression in UTF-8 formula.txt
python scripts/edit_calculation.py /path/to/original.twb \
  --output /path/to/candidate.twb \
  --allow 'ds-internal-name::[Calculation_123]' \
  --formula-file formula.txt \
  --backend document-api
```

`edit_calculation.py` validates the baseline, does the no-op probe when using Document API, writes to a new candidate, compares the exact formula-only structural change, and validates against locked XSD. It **will not** modify arbitrary fields or create a calculation. It **will not** silently fall back when Document API fails. If user explicitly authorizes fallback:

```bash
python scripts/edit_calculation.py /path/to/original.twb \
  --output /path/to/xml-candidate.twb \
  --allow 'ds-internal-name::[Calculation_123]' \
  --formula-file formula.txt \
  --backend xml
```

Strict diff rejects non-formula edits, even incidental whitespace in original XML nodes. If a no-op serializer disturbs the structure, don't waive this guard. Even with fully passing local checks, open the candidate in Tableau Desktop and test query results.

### Optional Tableau Cloud / Server validation

Prerequisites: Server **2026.2+** or Cloud **June 2026+**, API `3.29`, site ID, authenticated **session token** with appropriate permissions, authorization to upload TWB bytes for validation. Access scope for compatible JWT/UAT setups: `tableau:workbooks:read`. Desktop standalone has **no** equivalent REST endpoint.

```bash
export TABLEAU_BASE_URL='https://your-authorized-tableau-service.example'
export TABLEAU_SITE_ID='site-luid'
export TABLEAU_AUTH_TOKEN='valid-session-token'
python scripts/validate_server.py /path/to/candidate.twb
```

Endpoint: `POST /api/3.29/sites/{site-id}/workbooks/validateWorkbook`, multipart file field `tableau_workbook` and filename ending `.twb`. **Not TWBX. Not publishing.** A raw PAT secret is not a session token; authenticate first. The validator rejects unexpected redirects and reports errors without printing diagnostics by default; run with `--show-details` only in a private authorized terminal. HTTP 200 with no errors = successful Tableau Server/Cloud load validation; any errors/non-200 = failed; warnings require manual review. Official documentation: https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_ref_workbooks_and_views.htm#validate_workbook

**Never replace** this endpoint with `validateWorkbookAndUpload` (which stores/upload-stages content) or Tableau MCP `publish-workbook` (which publishes). Tableau MCP's publish tool explicitly warns it is a mutating operation; its authoring feature is disabled by default in the documented Server/Cloud deployment.

### Desktop acceptance checklist

- Open candidate copy in **Desktop 2026.2**, with no unexpected upgrade prompt or load error.
- Inspect changed field(s) for invalid formula, non-existent dependencies, type/aggregate/LOD/table-calc behavior.
- Run relevant queries against the intended sources and credentials; check impacted worksheets/dashboards/actions/filters.
- Compare known-good KPI outputs under explicit datasets, filters and dates; distinguish intended from unexpected changes.
- Capture original and candidate SHA-256, diff scope, XSD lock, API verdict/warnings if used, and manual review decision.

## Schema and tool updates

- `python scripts/fetch_schema.py --check`: verify currently locked file. Never silently replace a lock.
- `python scripts/fetch_schema.py --candidate [--ref <commit>]`: stage an upstream candidate into `references/schemas/twb_2026.2.0.xsd.candidate` plus lock, without replacing the existing pinned schema. Review source provenance, `sha256`, schema diff and local tests before authorized promotion.
- Official XSD may evolve on `main`: use a Git commit ref (40 hex) and record approval in Git for reproducibility; a hash locked against mutable `main` alone does not anchor provenance.
- New Tableau 2026.x release: obtain matching official XSD (if published), update version rules/checker separately, rerun compatibility suite on genuine local workbooks. Do **not** rename a 2026.2 XSD to pretend support for a newer format.
- New Document API release: review changed `Field`, `Datasource`, `Workbook.save_as`, test no-op and isolated formula edit on approved 2026.2 samples, check official support status.
- New Tableau MCP Desktop release: verify **runtime** available tools, permission model and change-conflict detection; do not treat GitHub branch code as stable support.

## CI / offline tests

`python -m unittest discover -s tests -v` covers synthetic diff containment, secure parsing, Document API no-op probes using **test stubs**, adapter selection, inventory, REST response classification, and skill packaging invariants. These tests do **not** test a real Tableau 2026.2 Workbook, official live XSD download, Document API against a genuine 2026.2 file, remote Tableau API, or Desktop visual/data behavior. Run those integration checks separately with an authorized workbook.