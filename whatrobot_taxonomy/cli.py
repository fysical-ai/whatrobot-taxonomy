"""whatrobot taxonomy CLI — the same verbs as Shopify's bin/product_taxonomy.

  whatrobot-taxonomy validate          # schema + integrity + classification + mapping + localisation checks
  whatrobot-taxonomy dist              # regenerate dist/
  whatrobot-taxonomy docs              # regenerate docs/ explorer (static HTML from dist/)
  whatrobot-taxonomy schema            # write JSON Schemas generated from the pydantic models to schema/
  whatrobot-taxonomy classify FACTS    # classify ad-hoc facts, e.g. legs=4 medium=ground
  whatrobot-taxonomy release VERSION   # set VERSION, regenerate dist/ and docs/, update CHANGELOG

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
    r.set_defaults(fn=cmd_release)
    ns = p.parse_args(argv)
    return ns.fn(ns)


if __name__ == "__main__":
    sys.exit(main())
