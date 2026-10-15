# Tableau Agent tool registry — verified 2026-10-14

This is a **capability/assurance registry**, not a claim that every tool is installed or that its current source API is stable. Test on an actual Desktop 2026.2 workbook before granting write permission.

| Tool | Scope | Official support / status | Verified in source or docs | Harness policy |
|---|---|---|---|---|
| [`tableau-document-schemas`](https://github.com/tableau/tableau-document-schemas) | `.twb` XSD 2026.2.0 | Tableau Supported | `schemas/2026_2/twb_2026.2.0.xsd` | Mandatory local static gate; checksum lock |
| [`document-api-python`](https://github.com/tableau/document-api-python) | `.twb/.twbx`, data source/field representations | **As-Is; unsupported**; latest formal release v0.11 (2022-11-07) | README lists reading fields & connection edits; source `Field.calculation` setter and `Datasource.add_calculation` exist | Experimental formula-write adapter only after no-op roundtrip + full gates |
| [`tableau-mcp`](https://github.com/tableau/tableau-mcp) | Cloud/Server discovery/query/admin; Desktop code under development | Tableau Supported repository; Desktop authoring described as coming soon in official guide | Desktop code has `get-workbook-xml`, `apply-workbook`, `list-instances`, `check-for-user-changes`, `list-worksheets`, `list-dashboards` | Server/Cloud tools on approved deployment; Desktop tools need a runtime availability/behavior test. `apply-workbook` is destructive; not validation |
| [`server-client-python`](https://github.com/tableau/server-client-python) | Server/Cloud REST API | Tableau Supported | workbook publishing, connections/admin actions and other REST functions | Allowed only with explicit server action permission; not local `.twb` editor |
| [Workbook REST validation](https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_ref_workbooks_and_views.htm#validate_workbook) | Load/semantic validation, no publish | Cloud June 2026 / Server 2026.2, API 3.29 | `POST .../workbooks/validateWorkbook`; `tableau_workbook` file field | Opt-in authorized remote semantic gate; Desktop alone cannot call this |
| [`hyper-api-samples`](https://github.com/tableau/hyper-api-samples) | `.hyper` extracts | Tableau samples | examples for Hyper API | Out of scope for TWB formula edits |
| [`tableau-migration-sdk`](https://github.com/tableau/tableau-migration-sdk) | environment migration | Official repo | multi-site/server migration workflows | Out of scope for routine local editing |

## What the Document API README does and doesn't establish

`document-api-python` README says *updating field information is not supported*. Yet the public **source code** includes:
- [`Field.calculation` setter](https://github.com/tableau/document-api-python/blob/master/tableaudocumentapi/field.py): alters `<calculation formula="...">`; creates a `<calculation>` child if needed.
- [`Datasource.add_calculation`](https://github.com/tableau/document-api-python/blob/master/tableaudocumentapi/datasource.py): adds a calculated field using a generated identifier.
- [`Workbook.save_as`](https://github.com/tableau/document-api-python/blob/master/tableaudocumentapi/workbook.py): writes the entire workbook through an XML serializer, not an in-place attribute patch.
- [`xfile.py`](https://github.com/tableau/document-api-python/blob/master/tableaudocumentapi/xfile.py): ZIP handling for packaged workbooks, involving extract and repack.

Therefore **method exists** ≠ **documented feature** ≠ **works in 2026.2** ≠ **safe on production workbook**. The harness *never* enables `add_calculation` as part of its FORMULA_EDIT automation and limits `.twb` writes to *existing* formulas.

## Tableau MCP distinctions

See [MCP README](https://github.com/tableau/tableau-mcp) and [official Introduction](https://tableau.github.io/tableau-mcp/docs/intro). Hosted Tableau MCP at `https://mcp.tableau.com` targets Tableau Cloud. Self-hosted mode supports appropriate Server/Cloud setups with configuration and permissions. The source tree includes experimental Desktop tooling, but the main documented MCP installation does not guarantee Desktop authoring operations on this user's machine. Verify actual tool registration and compatible Tableau Desktop process before use; do not invent Desktop tool availability. The `apply-workbook` code applies full workbook XML and can overwrite live app state.

## Agent routing decision

1. **Read local TWB:** hardened XML parser first; optionally Document API only for supported extracts if it can parse the file.
2. **Formula-only update:** `probe_document_api.py` → `edit_calculation.py` with Document API adapter → guard + XSD → Desktop. On probe failure, stop and report explicit XML fallback option; no automatic switch.
3. **Connections/field creation/layout:** this kit is read-only for those structures; design a new adapter contract and tests before writes.
4. **Published Server/Cloud content:** use Tableau MCP / TSC for appropriate supported actions, with explicit user permission. Don't treat remote validation as editing or publishing.

## Reassessment / update triggers

- New Document API release or README/API behavior change: rerun no-op and formula smoke tests, inspect source diff, record release and tests.
- Desktop authoring officially exposed and documented in Tableau MCP: verify installed package, session, tool descriptions, authorization model, conflict detection and any `apply-workbook` semantics; only then consider an adapter.
- Tableau Desktop version change: obtain matching official schema, test again, do not recycle a 2026.2 lock for 2026.3.