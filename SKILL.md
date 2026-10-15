---
name: tableau-workbook
description: >-
  Inspects, audits, safely edits, and validates local Tableau Desktop workbooks
  (.twb) and assesses packaged workbooks (.twbx). Use when a task involves Tableau
  2026.x workbook XML, calculated fields, field dependencies, data connections,
  worksheet or dashboard structure, Tableau Document API, Tableau MCP, XSD
  compatibility, or Tableau workbook migration. Provides tightly scoped formula
  editing for 2026.2; does not claim general TWBX or dashboard authoring support.
---

# Tableau Workbook Engineering

Target **Tableau Desktop 2026.2** for writes. Inspect other versions read-only; never relabel a workbook to bypass compatibility checks. Resolve all `scripts/...` and `references/...` paths relative to this `SKILL.md` directory, not the user's project working directory.

## Choose an operation

| Request | Allowed path | Gate |
|---|---|---|
| Inventory data sources, fields, calculations, worksheets, dashboards | Read-only `scripts/inspect_twb.py` | Local file; do not expose formulas unless requested |
| Modify an **existing** calculated-field formula | `scripts/edit_calculation.py` using tested Document API; controlled XML only when explicitly selected | Exact field ID, no-op probe (Document API), strict diff, locked XSD, Desktop/data verification |
| Change connections, create/delete fields, dashboards, relationships, filters or workbook layout | Analysis/prototype only | Requires separate explicit write authorization and a purpose-built tested adapter; this skill has **no structural-write certification** |
| Read/alter `.twbx` / `.hyper` | Discuss or inspect a separate extracted copy | No packaged-workbook write path in this skill |
| Use Tableau MCP / Server API | Discover actual available tools and permissions | User approval before upload, validation transmission, publish, overwrite, or remote mutation |
| Migrate Tableau version | Tableau Desktop's supported export/save on a **copy** | User approval; never edit `version`, `original-version`, or manifest to simulate conversion |

Read [TOOL_REGISTRY.md](references/TOOL_REGISTRY.md) before selecting a write backend. Document API 0.11 is **As-Is**, last published 2022; calculation setters exist in source but are not a guaranteed 2026.2-compatible public contract. Tableau MCP repository Desktop code is not proof that a local MCP tool is available or supported.

## Read-only workflow

1. Inspect the supplied file path and file type; treat it as **untrusted XML**. Do not interpolate untrusted workbook content into shell commands.
2. Run `python "<SKILL_DIR>/scripts/inspect_twb.py" /path/to/workbook.twb`.
3. State workbook `version` and `original-version`, exact internal `datasource.name::column.name` IDs, candidate impact and uncertainties. Worksheet usage results are a **partial** direct-reference inventory, not a complete dependency graph.
4. Do not expose connection secrets, embedded SQL, formulas or private workbook data in public logs or external services without authorization.

## Existing-formula edit: mandatory sequence

1. **Establish baseline:** preserve the original and its SHA-256; run `inspect_twb.py`, `fetch_schema.py --check`, then `validate_twb.py original.twb`. The schema must be the pinned official **2026.2 XSD**, and root `version` must be `26.2`. An older `original-version` is not by itself a failure. If the original fails the gate, **stop**; do not silently repair or downgrade it.
2. **Identify the target:** require one exact `datasource.name::[Calculation_ID]` and a user-approved new formula. Evaluate likely dependencies, LOD/aggregation implications and expected KPI changes. If ambiguous, ask before writing.
3. **Choose backend:** run `probe_document_api.py original.twb` before Document API editing. Treat any canonical XML drift as a **hard stop** for this backend. If explicitly authorized, the controlled XML backend may be selected; never silently switch after a failure.
4. **Create a candidate only:** save replacement expression in a UTF-8 file, then run:

   ```bash
   python "<SKILL_DIR>/scripts/edit_calculation.py" original.twb \
     --output candidate.twb \
     --allow 'datasource-internal-name::[Calculation_123]' \
     --formula-file formula.txt \
     --backend document-api
   ```

   Use `--backend xml` only with explicit approval. The script refuses existing outputs, checks original/candidate XSD, and applies `diff_guard.py` to allow **only** the named formula-attribute difference.
5. **Validate runtime and business semantics:** Open the candidate in Tableau Desktop **2026.2** and execute relevant queries/filters/worksheets; compare known-good KPIs to agreed expectations. Optional remote semantic validation via `validate_server.py` requires separate authorization and compatible Tableau Server/Cloud; it does not prove correctness of data or Desktop rendering. Never publish as a substitute for validation.
6. **Report a verification matrix:** candidate path and original/candidate hashes; targeted ID; backend; strict diff and XSD status; Tableau load status; affected KPI results; warnings; all checks **not performed**. Never describe unperformed checks as passed.

Detailed commands, conditions and schema-update procedure: [VALIDATION_AND_UPDATE.md](references/VALIDATION_AND_UPDATE.md).

## Safety invariants and stop conditions

- Never overwrite the original, the only backup, a published workbook, or a live Desktop session. Candidate output must be a fresh `.twb`; do not bundle/rewrite a `.twbx` here.
- Reject DTD/XXE, invalid version, unknown schema/hash, duplicate or missing field IDs, unauthorized XML differences, unexpected Document API serializer changes, missing dependencies, validation errors or new user edits since the baseline.
- Keep identifiers, namespace bindings, workbook manifest, version metadata, connection attributes, sheet references and unrelated content unchanged.
- Keep secrets in local environment variables. Do not transmit a TWB to Tableau Server/Cloud or any external service unless the user explicitly authorizes that destination and operation.
- On failure preserve original; report the failing gate and candidate state. Do not lower validation standards to force a pass.

## Reference files and available tooling

- [CONTEXT_2026_2.md](references/CONTEXT_2026_2.md): version format, Tableau XML/XSD, official resources; read for version or schema questions.
- [TOOL_REGISTRY.md](references/TOOL_REGISTRY.md): Document API source-level capabilities, MCP/TSC/Hyper, tool maturity; read before selecting adapters.
- [VALIDATION_AND_UPDATE.md](references/VALIDATION_AND_UPDATE.md): commands, acceptance evidence and schema pin/update steps; read for edits, remote verification, or upgrades.
- [Official XSD setup](references/schemas/README.md): fetch `twb_2026.2.0.xsd` and lock once; `fetch_schema.py` never overwrites an existing lock without review.
- `evals/cases.json`: task-level behavior tests. `tests/`: deterministic offline script/skill-contract tests. Run `python -m unittest discover -s "<SKILL_DIR>/tests" -v` after modifying this Skill.