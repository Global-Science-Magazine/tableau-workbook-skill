# Official Tableau 2026.2 workbook schema

This directory is populated on the user's machine by `scripts/fetch_schema.py`.

- Source: https://github.com/tableau/tableau-document-schemas
- Canonical file: `schemas/2026_2/twb_2026.2.0.xsd`
- Pinned raw URL: https://raw.githubusercontent.com/tableau/tableau-document-schemas/a705484638d79b9bec830a66cb0004ca75f999e0/schemas/2026_2/twb_2026.2.0.xsd
- Local destination: `references/schemas/twb_2026.2.0.xsd`
- Local lock: `references/schemas/schema.lock.json` (source/ref, file SHA-256, schema version)

From the **skill directory**, run:

```bash
python scripts/fetch_schema.py
python scripts/fetch_schema.py --check
```

The default source is pinned to Git commit `a705484638d79b9bec830a66cb0004ca75f999e0` (Add 262 TWB XSD). For reviewed updates, pass `--ref <40-char-commit-sha>` or deliberately select `--ref main`. To update, use `--candidate`, inspect the diff and consciously promote both the schema and lock; **do not replace a pinned schema silently**.

The official XSD itself is **not shipped** in this package because it could not be retrieved into the packaging environment. Fetching requires access to `raw.githubusercontent.com`. Without a downloaded and locked XSD, `validate_twb.py` and `edit_calculation.py` fail closed. Do not substitute a fabricated or older-version XSD.
