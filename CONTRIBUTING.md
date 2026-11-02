# Contributing

Everything comes from the source-of-truth files in `data/`. Open an issue with one of the templates, or submit a PR that edits `data/` only.

1. `pip install -e ".[dev]"`
2. Edit `data/` (never `dist/` or `docs/` — they are generated).
3. `whatrobot-taxonomy validate` — must report 0 errors.
4. `whatrobot-taxonomy dist && whatrobot-taxonomy docs` — commit the regenerated files.
5. `pytest`.
6. Add a line to `CHANGELOG.md` under the unreleased version.

Rules that CI enforces (docs/design.md §9.8): positional ids are never reused or renumbered; every leaf has a description, an inclusion rule and at least one example; every enum ends with `<attr>__other`; every category is mapped or explicitly unmapped for each integration; every example in `data/examples.yml` must classify to its expected category under the tie-break rules in `whatrobot_taxonomy/classify.py`.

Retiring a category: leave the id gap and remove it from its parent's `children`. A `whatrobot → whatrobot` migration mapping for retired ids is planned (`data/integrations/whatrobot/`) but not yet implemented in the tooling.

Translations: edit `data/localizations/<locale>/` only. A field counts as reviewed when it is listed under the entry's `source` with the fingerprint of the English it was checked against; the easiest way to get that right is the review round trip in docs/design.md §9.9 (`whatrobot-taxonomy l10n export` → review sheet → `l10n import`). Stable releases need every locale fully reviewed.

By contributing you agree that data contributions are licensed CC BY 4.0 and code contributions MIT.
