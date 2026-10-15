# Tableau Workbook Skill · v1.0 · Tableau Desktop 2026.2

This repository contains an Agent Skills–compatible skill for Codex and Claude Code. It packages seven CLI tools plus `_xml.py`, scoped editing, schema pinning, verification rules, and offline tests.

## Install

Clone to one of the following user-level skill paths:

```bash
# Codex
mkdir -p ~/.agents/skills
git clone https://github.com/Global-Science-Magazine/tableau-workbook-skill.git ~/.agents/skills/tableau-workbook

# Claude Code
mkdir -p ~/.claude/skills
git clone https://github.com/Global-Science-Magazine/tableau-workbook-skill.git ~/.claude/skills/tableau-workbook
```

For a repo-local installation, use `.agents/skills/tableau-workbook/` for Codex or `.claude/skills/tableau-workbook/` for Claude Code. Confirm your client version discovers the skill. Restart or reload the client if necessary.

## Prepare runtime

```bash
cd ~/.agents/skills/tableau-workbook
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/fetch_schema.py
python scripts/fetch_schema.py --check
```

**Official XSD is not bundled.** Access to `raw.githubusercontent.com` is required once. The fetcher defaults to official 2026.2 XSD commit `a705484638d79b9bec830a66cb0004ca75f999e0` and locks the retrieved SHA-256. Without the XSD/lock, write operations fail closed.

To use the optional Document API adapter:

```bash
python -m pip install -r requirements-document-api.txt
python scripts/probe_document_api.py /path/to/workbook.twb
```

Document API 0.11 is old and uses `distutils.version`; Python 3.11 may be needed. The XML backend is **not** an automatic fallback; selecting it requires an explicit decision.

## Example tasks

- **Read only:** “Use the tableau-workbook skill to inventory this TWB's calculated fields and worksheet dependencies; do not edit.”
- **Bounded write:** “Replace this exact calculation formula in a new TWB candidate, following all validation gates. Do not publish.”
- **Compatibility:** “Check Tableau 2026.2 compatibility without rewriting version metadata.”

## Project-level guard (optional)

Add this to a project-local `AGENTS.md` or `CLAUDE.md`:

```markdown
- Use the tableau-workbook skill for Tableau TWB/TWBX tasks.
- Never overwrite original workbooks or publish without explicit approval.
- Treat edits as candidates until matching XSD, Tableau Desktop opening,
  and agreed business-result checks are completed.
```

## Testing and limitations

`python -m unittest discover -s tests -v` runs offline tests with synthetic workbooks and mocks. `evals/cases.json` contains behavioral eval scenarios for real Codex/Claude Code agents; these have **not** been executed. Real Tableau Desktop validation, server integration and formula result regression checks are still necessary.

## Official skill-creation guidance

- [OpenAI skill-creator](https://github.com/openai/skills/blob/main/skills/.system/skill-creator/SKILL.md)
- [OpenAI Skills Guide](https://developers.openai.com/api/docs/guides/tools-skills)
- [Anthropic Skill Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Anthropic skill-creator](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md)
- [Agent Skills specification](https://agentskills.io/specification)
