# Tableau Desktop 2026.2 — versioned context for coding agents

**Verified/reviewed:** 2026-10-14. Read this alongside the **actual** pinned `references/schemas/twb_2026.2.0.xsd`; the overview below is not a replacement for schema declarations or runtime validation.

## Document model and compatibility

- `.twb` is declarative XML describing datasources, worksheets, dashboards and other workbook state. `.twbx` is a ZIP-based package containing a TWB and optional extracts/resources; the official TWB XSD does **not** validate TWBX directly.
- Schema mapping is **workbook `version="26.2"` → `twb_2026.2.0.xsd`**. Desktop maintenance release `2026.2.x`, workbook `version` and XSD `2026.2.0` are distinct identifiers.
- The root `original-version` can convey origin/provenance. When a 2026.2 file was upgraded from an earlier version, inspect `original-version` rather than assuming it must equal `26.2`. The harness enforces `version="26.2"` and XSD conformance, flags differing `original-version`, and **never auto-overwrites** it.
- `source-build` and `source-platform` are metadata; preserve rather than inventing values. Old Desktop generally cannot load new-version workbooks. Migrate/downgrade a **copy** with supported Desktop operations, not a manual version-string replacement.
- `<document-format-change-manifest>` records format features. Tableau's schema repository documents `<ManifestByVersion />` for directly authored workbooks. Do **not** replace an existing manifest on a routine edit.
- From 2026.2, XSD annotations include `user:localizable` types: `identifier`, `identifier-reference`, `no-restrictions`, `add-if-missing`, `see-documentation`, `do-not-localize`. The annotations are incomplete, so absent annotations are **not** permission to translate or rename. `identifier-reference` indicates a cross-object reference.
- Unknown or weakly validated XSD sections exist (`processContents="skip"`). The XSD does not check all connection attributes, calculation functions, referenced objects, or business semantics.

## Official 2026.2 XSD

- Repository: https://github.com/tableau/tableau-document-schemas
- In-repository path: `schemas/2026_2/twb_2026.2.0.xsd`
- Raw URL: https://raw.githubusercontent.com/tableau/tableau-document-schemas/main/schemas/2026_2/twb_2026.2.0.xsd
- Header (as previously inspected): schema version `2026.2.0`, publication `2026-06-15T23:32:07Z`, build `20262.26.0528.2205`.
- Local installation: `python scripts/fetch_schema.py`; local SHA-256 pin: `references/schemas/schema.lock.json`. By default the fetcher pins Git commit `a705484638d79b9bec830a66cb0004ca75f999e0` (initial 2026.2 XSD). Use `--ref <commit-sha>` only to select a different reviewed source; GitHub `main` is mutable even if the checksum is pinned locally. For later updates use `--candidate` instead of overwriting.
- **Not included in distribution**: XSD file bytes, because source fetching must happen on the user's machine. Do not manufacture/approximate XSD declarations.

## Logical anatomy

The major concepts (not a valid XML layout template) include:

```text
workbook
├── datasources (connections, relation graph, columns, calculations)
├── worksheets (datasource references, shelves, marks, filters)
├── dashboards (zones, worksheet refs, filters/actions)
└── stories, parameters, formatting and other feature-dependent nodes
```

IDs/internal `name` are not the same as visible `caption`. A `[Calculation_...]` may appear in multiple worksheet/table calculations, dependencies and formatting. `inspect_twb.py` reports only a **subset** of exact direct `datasource-dependencies` references; it is not a complete dependency graph and should not be used as proof that a formula is unused.

## Official programmatic tooling: implications for a 2026.2 agent

| Component | Current evidence | Authorized harness scope |
|---|---|---|
| [Document API](https://github.com/tableau/document-api-python) | v0.11 last formal release 2022-11-07; **As-Is**, limited officially documented support. Source includes `Field.calculation`, `Datasource.add_calculation`, XML `save_as` | Read or formula-write on a fresh candidate only after no-op and strict gates; no automatic new fields or general edits |
| [Tableau MCP](https://github.com/tableau/tableau-mcp) | Tableau-supported Server/Cloud MCP; Desktop tooling present under `src/tools/desktop` (`get-workbook-xml`, `apply-workbook`, change checks), but official docs describe full Desktop authoring as coming soon | Server/Cloud actions with explicit permission; Desktop editing **not assumed available or safe** |
| [Server Client Python](https://github.com/tableau/server-client-python) | Tableau-supported TSC for REST API | Server/Cloud actions; not an offline Desktop Workbook editor |
| [Document Schemas](https://github.com/tableau/tableau-document-schemas) | Tableau-supported XML XSD | Mandatory syntax gate for 2026.2 files |
| [REST Validate Workbook](https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_ref_workbooks_and_views.htm#validate_workbook) | API 3.29 from Server 2026.2 / Cloud June 2026 | Optional authenticated semantic/load gate; no publish |

Document API distinction: README says **updating field information is unsupported**, while public code has setters and `add_calculation`. **Implementation available** is not **supported or tested**. `Workbook.save_as` may reserialize an entire TWB; no-op roundtrip (semantic/structural equality) is mandatory before edit, and even a pass does not guarantee full runtime compatibility. A Document API read that returns some calculated fields does not prove the library understands all new 2026.2 features.

Tableau MCP distinction: hosted `https://mcp.tableau.com` is a Cloud integration, not a drop-in adapter for a local Desktop process. The source-level Desktop `apply-workbook` applies full XML to active session and can overwrite user's state. Future Desktop support should be gated by actual tool availability, permissions and concurrency/change detection.

## Verification ladder

1. **Valid XML syntax:** document parse without external entities/DTD.
2. **Valid matching XSD:** structure conforms to pinned Tableau 2026.2 XSD.
3. **Allowed changes only:** semantic XML diff vs original allows only formula attributes.
4. **Server/Cloud semantic-load test:** optional authorized REST `validateWorkbook` (not on Desktop alone); no publish.
5. **Desktop 2026.2 load test:** actual app opens candidate, with local drivers/credentials.
6. **Business regression:** run queries, check formula validity/aggregation/LOD/table calculations, expected KPI and dashboard behavior.

These are distinct. Passing any earlier step does not imply a later one. The REST endpoint validates semantic load, **not** business correctness.

## Known exception

A community discussion [#13](https://github.com/tableau/tableau-document-schemas/discussions/13) reports an older Workbook loadable in a new Desktop but not validating against the new XSD. This is a public case report, not a general compatibility guarantee. Treat original XSD failure as a **block for the automated edit**, not license to mutate version metadata.

## References and update sources

- XSD and manifest: https://github.com/tableau/tableau-document-schemas
- Document API README: https://github.com/tableau/document-api-python
- Document API `Field.calculation` implementation: https://github.com/tableau/document-api-python/blob/master/tableaudocumentapi/field.py
- Document API `Datasource.add_calculation`: https://github.com/tableau/document-api-python/blob/master/tableaudocumentapi/datasource.py
- Document API `.twbx` ZIP/serialization: https://github.com/tableau/document-api-python/blob/master/tableaudocumentapi/xfile.py
- Tableau MCP README: https://github.com/tableau/tableau-mcp
- Tableau MCP docs: https://tableau.github.io/tableau-mcp/docs/intro
- Tableau MCP Desktop source: https://github.com/tableau/tableau-mcp/tree/main/src/tools/desktop
- TSC: https://github.com/tableau/server-client-python
- REST Validate Workbook: https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_ref_workbooks_and_views.htm#validate_workbook
- Version compatibility: https://help.tableau.com/current/desktopdeploy/en-us/desktop_deploy_compatibility.htm