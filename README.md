# Tableau Workbook Skill

A reusable, security-conscious [Agent Skill](https://agentskills.io/) for inspecting, selectively editing, and validating Tableau Desktop workbooks. **Write target: Tableau Desktop 2026.2**.

The skill routes reads and narrowly scoped formula edits through explicit Python scripts, keeps vendor/version knowledge in references, and enforces fail-closed XML, schema and diff checks. It does **not** certify general dashboard authoring or Tableau Desktop runtime correctness.

## Installation

Clone this repository into either agent's user-level skills directory:

```bash
# Codex
mkdir -p ~/.agents/skills
git clone https://github.com/Global-Science-Magazine/tableau-workbook-skill.git ~/.agents/skills/tableau-workbook

# Claude Code (as an alternative or separately)
mkdir -p ~/.claude/skills
git clone https://github.com/Global-Science-Magazine/tableau-workbook-skill.git ~/.claude/skills/tableau-workbook
```

Then, from the skill directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/fetch_schema.py
python scripts/fetch_schema.py --check
```

To use the experimental Document API formula-editing adapter, additionally run `python -m pip install -r requirements-document-api.txt` and `python scripts/probe_document_api.py /path/to/workbook.twb` before any edit. Use a separate Python 3.11 environment if Document API 0.11 is incompatible with newer Python.

## Usage

Ask your agent: **“Use the tableau-workbook skill to inventory this TWB's data sources, calculated fields, and worksheet references; do not modify it.”** See [SKILL.md](SKILL.md) for operation gates and [INSTALL.md](INSTALL.md) for full setup.

## Safety and validation

- Original workbook is immutable; edits create a candidate file only.
- For 2026.2 writes, the official pinned XSD and SHA-256 lock are mandatory; XSD files are **downloaded after installation**, not vendored here.
- Document API is tagged **As-Is** and formula setters are source-level capabilities, not an officially supported 2026.2 contract. A no-op round-trip probe is mandatory.
- Static XSD/diff checks do **not** replace Tableau Desktop loading or KPI regression tests.
- Any upload/publish or remote validation requires explicit authorization.

**Validation status:** 22 deterministic local unit/contract tests passed on the packaged Skill. Integration with a real Tableau 2026.2 workbook and live agent behavioral evaluations have not yet been run.

## References

Official [Tableau workbook schemas](https://github.com/tableau/tableau-document-schemas), [Document API](https://github.com/tableau/document-api-python), [Tableau MCP](https://github.com/tableau/tableau-mcp), and [Agent Skills specification](https://agentskills.io/specification). The 2026.2 XSD is pinned to Tableau commit `a705484638d79b9bec830a66cb0004ca75f999e0`; see [schema setup](references/schemas/README.md).

## License

MIT. See [LICENSE](LICENSE).
