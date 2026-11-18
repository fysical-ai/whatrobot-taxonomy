"""whatrobot taxonomy CLI — the same verbs as Shopify's bin/product_taxonomy.

  whatrobot-taxonomy validate          # schema + integrity + classification + mapping + localisation checks
  whatrobot-taxonomy dist              # regenerate dist/
  whatrobot-taxonomy docs              # regenerate docs/ explorer (static HTML from dist/)
  whatrobot-taxonomy schema            # write JSON Schemas generated from the pydantic models to schema/
  whatrobot-taxonomy classify FACTS    # classify ad-hoc facts, e.g. legs=4 medium=ground
  whatrobot-taxonomy release VERSION   # set VERSION, regenerate dist/ and docs/, update CHANGELOG
  whatrobot-taxonomy l10n status       # per locale: reviewed / stale / draft / missing fields
  whatrobot-taxonomy l10n export ...   # rows for native review (CSV; paste into the review sheet)
  whatrobot-taxonomy l10n import ...   # write ticked rows from a review CSV into data/localizations/<locale>/
  whatrobot-taxonomy l10n import FILE --draft --locale <code>   # write machine first drafts (unreviewed)

Equivalent: python -m whatrobot_taxonomy.cli <verb>
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date

from . import ROOT, models, version
from .classify import Unclassifiable, classify
from .dist import build
from .loader import load
from .validate import validate


def cmd_validate(_: argparse.Namespace) -> int:
    tx = load()
    rep = validate(tx)
    for w in rep.warnings:
        print(f"WARN  {w}")
    for e in rep.errors:
        print(f"ERROR {e}")
    print(
        f"{len(tx.categories)} categories, {len(tx.attributes)} attributes, {len(tx.values)} values, "
        f"{len(tx.examples)} examples, {len(tx.mappings)} mapping files, locales: {', '.join(tx.locales) or 'none'}"
    )
    print(f"{len(rep.errors)} errors, {len(rep.warnings)} warnings")
    return 0 if rep.ok else 1


def cmd_dist(_: argparse.Namespace) -> int:
    tx = load()
    rep = validate(tx)
    if not rep.ok:
        print("refusing to build dist with validation errors; run validate")
        return 1
    files = build(tx)
    print(f"wrote {len(files)} files to dist/ (version {version()})")
    return 0


def cmd_docs(_: argparse.Namespace) -> int:
    from .docs import build_docs

    out = build_docs(load())
    print(f"wrote {out}")
    return 0


def cmd_schema(_: argparse.Namespace) -> int:
    sdir = ROOT / "schema"
    sdir.mkdir(exist_ok=True)
    for name, model in {
        "category": models.Category,
        "attribute": models.Attribute,
        "value": models.Value,
        "example": models.Example,
        "mapping_file": models.MappingFile,
        "integration": models.Integration,
    }.items():
        (sdir / f"{name}.schema.json").write_text(json.dumps(model.model_json_schema(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote schemas to {sdir}")
    return 0


def cmd_classify(ns: argparse.Namespace) -> int:
    facts: dict[str, object] = {}
    for kv in ns.facts:
        k, sep, v = kv.partition("=")
        if not sep:
            print(f"expected key=value, got {kv!r}")
            return 2
        facts[k] = {"true": True, "false": False}.get(v.lower(), int(v) if v.isdigit() else v)
    try:
        cid = classify(facts)
    except Unclassifiable as e:
        print(f"unclassifiable: {e}")
        return 2
    print(f"{cid}  {load().full_name(cid)}")
    return 0


def cmd_release(ns: argparse.Namespace) -> int:
    if not re.fullmatch(r"\d{4}-\d{2}", ns.version):
        print("version must be CalVer YYYY-MM")
        return 2
    tx = load()
    rep = validate(tx)
    if not rep.ok:
        print("validation errors; aborting release")
        return 1
    from .l10n import launch_ready, status

    unready = {loc: c for loc, c in status(tx).items() if not launch_ready(c)}
    if unready and not ns.allow_unreviewed:
        for loc, c in unready.items():
            print(f"{loc}: {dict(c)}")
        print("locales above are not fully reviewed; finish the review or pass --allow-unreviewed")
        return 1
    (ROOT / "VERSION").write_text(ns.version + "\n", encoding="utf-8")
    build(tx)  # build() calls version() at write time, so it sees the new value
    from .docs import build_docs

    build_docs(tx)
    # pyproject version in PEP 440 form (2026-01 → 2026.1)
    pep = ns.version.replace("-0", ".").replace("-", ".")
    pp = ROOT / "pyproject.toml"
    pp.write_text(re.sub(r'^version = ".*"$', f'version = "{pep}"', pp.read_text(encoding="utf-8"), count=1, flags=re.M), encoding="utf-8")
    # CHANGELOG: mark an existing unreleased section for this version, or insert a new one before the first ## heading
    cl = ROOT / "CHANGELOG.md"
    text = cl.read_text(encoding="utf-8")
    today = date.today().isoformat()
    marker = f"## {ns.version} — unreleased"
    if marker in text:
        text = text.replace(marker, f"## {ns.version} — {today}", 1)
    else:
        stub = f"## {ns.version} — {today}\n\n- (describe changes to data/)\n\n"
        m = re.search(r"^## ", text, flags=re.M)
        text = text[: m.start()] + stub + text[m.start() :] if m else text + "\n" + stub
    cl.write_text(text, encoding="utf-8")
    print(f"released {ns.version}: VERSION, pyproject.toml, dist/, docs/, CHANGELOG.md updated — review, commit, then: git tag v{ns.version} && git push --tags")
    return 0


def cmd_l10n(ns: argparse.Namespace) -> int:
    from pathlib import Path

    from . import l10n

    tx = load()
    if ns.action == "status":
        counts = l10n.status(tx, ns.locale or None)
        for loc, c in counts.items():
            total = sum(c.values())
            ready = "ready" if l10n.launch_ready(c) else "not ready"
            print(f"{loc:8} {c['reviewed']:4} reviewed  {c['stale']:4} stale  {c['draft']:4} draft  {c['missing']:4} missing  of {total}  ({ready})")
        return 0
    if ns.action == "export":
        if not ns.locale:
            print("give at least one --locale")
            return 2
        rows = l10n.export_rows(tx, ns.locale, only_needed=ns.only_needed)
        out = Path(ns.output)
        l10n.write_csv(rows, out)
        print(f"wrote {len(rows)} rows to {out}")
        return 0
    # import
    if not ns.file or len(ns.locale or []) != 1:
        print("usage: whatrobot-taxonomy l10n import FILE --locale <code>")
        return 2
    rows = l10n.read_review(Path(ns.file))
    if ns.draft:
        rep = l10n.import_drafts(tx, ns.locale[0], rows)
        print(f"wrote {sum(rep.imported.values())} draft fields {dict(rep.imported)}; kept {rep.kept_reviewed} reviewed; {rep.unticked} rows empty")
    else:
        rep = l10n.import_review(tx, ns.locale[0], rows, accept_changed_english=ns.accept_changed_english)
        print(f"imported {sum(rep.imported.values())} reviewed fields {dict(rep.imported)}; {rep.unticked} rows not ticked (left as they were)")
    for k in rep.english_changed:
        print(f"SKIP  {k}: English changed since the sheet was made; re-export this row")
    for k in rep.needs_name:
        print(f"SKIP  {k}: no reviewed name yet, so the entry can't be created")
    for e in rep.errors:
        print(f"ERROR {e}")
    print("next: whatrobot-taxonomy validate && whatrobot-taxonomy dist && whatrobot-taxonomy docs")
    return 1 if rep.errors else 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="whatrobot-taxonomy", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate").set_defaults(fn=cmd_validate)
    sub.add_parser("dist").set_defaults(fn=cmd_dist)
    sub.add_parser("docs").set_defaults(fn=cmd_docs)
    sub.add_parser("schema").set_defaults(fn=cmd_schema)
    c = sub.add_parser("classify")
    c.add_argument("facts", nargs="+", help="key=value pairs")
    c.set_defaults(fn=cmd_classify)
    r = sub.add_parser("release")
    r.add_argument("version", help="CalVer, e.g. 2026-04")
    r.add_argument("--allow-unreviewed", action="store_true", help="release even if a locale has unreviewed or stale fields")
    r.set_defaults(fn=cmd_release)
    lz = sub.add_parser("l10n", help="localisation review: status, export, import")
    lz.add_argument("action", choices=["status", "export", "import"])
    lz.add_argument("file", nargs="?", help="review CSV (import)")
    lz.add_argument("--locale", action="append", help="locale code, e.g. da or zh-Hans (repeat for export)")
    lz.add_argument("-o", "--output", default="l10n-review.csv", help="export: CSV to write")
    lz.add_argument("--only-needed", action="store_true", help="export: only fields not yet reviewed, or stale, in a given locale")
    lz.add_argument("--draft", action="store_true", help="import: write every non-empty row as an unreviewed draft (machine first drafts); reviewed fields are kept")
    lz.add_argument("--accept-changed-english", action="store_true", help="import: accept rows whose English differs from the current English")
    lz.set_defaults(fn=cmd_l10n)
    ns = p.parse_args(argv)
    return ns.fn(ns)


if __name__ == "__main__":
    sys.exit(main())
