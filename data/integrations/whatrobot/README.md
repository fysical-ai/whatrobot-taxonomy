# whatrobot → whatrobot mappings

When a category is retired (never renumbered), add a `<old-version>_to_<new-version>.yml` here with
rules `old category_id → [new category_id]`, so integrators can migrate.

**Status: planned.** The loader and dist builder do not yet read this directory; it will be wired up before the first category retirement.
