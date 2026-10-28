"""Generate dist/ from data/: per-locale JSON + TXT for categories, attributes, values; integrations JSON.

Output shape follows Shopify's dist files where applicable, extended with the typed attribute fields.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from . import DIST, version
from .loader import SOURCE_LOCALE, Taxonomy

GID = "gid://whatrobot/TaxonomyCategory/{id}"
GID_ATTR = "gid://whatrobot/TaxonomyAttribute/{id}"
GID_VALUE = "gid://whatrobot/TaxonomyValue/{id}"


def _loc_attr(tx: Taxonomy, fid: str, locale: str) -> tuple[str, str]:
    a = tx.attributes[fid]
    if locale != SOURCE_LOCALE and (loc := tx.locales.get(locale)) and fid in loc.attributes:
        la = loc.attributes[fid]
        return la.name, la.description or a.description
    return a.name, a.description


def _loc_value(tx: Taxonomy, fid: str, locale: str) -> str:
    v = tx.values[fid]
    if locale != SOURCE_LOCALE and (loc := tx.locales.get(locale)) and fid in loc.values:
        return loc.values[fid].name
    return v.name


def _loc_cat(tx: Taxonomy, cid: str, locale: str) -> tuple[str, str]:
    c = tx.categories[cid]
    if locale != SOURCE_LOCALE and (loc := tx.locales.get(locale)) and cid in loc.categories:
        lc = loc.categories[cid]
        return lc.name, lc.description or c.description
    return c.name, c.description


def value_json(tx: Taxonomy, fid: str, locale: str) -> dict:
    v = tx.values[fid]
    return {"id": GID_VALUE.format(id=v.id), "name": _loc_value(tx, fid, locale), "friendly_id": v.friendly_id, "handle": v.handle}


def attribute_json(tx: Taxonomy, fid: str, locale: str, with_values: bool = True) -> dict:
    a = tx.attributes[fid]
    name, desc = _loc_attr(tx, fid, locale)
    out: dict = {
        "id": GID_ATTR.format(id=a.id),
        "name": name,
        "friendly_id": a.friendly_id,
        "handle": a.handle,
        "description": desc,
        "question": a.question,
        "type": a.type,
        "multi": a.multi,
    }
    for k in ("unit", "format", "ref_target", "derived_from", "companions"):
        if getattr(a, k) is not None:
            out[k] = getattr(a, k)
    if a.type == "enum" and with_values:
        out["values"] = [value_json(tx, v, locale) for v in a.values or []]
    return out


def category_json(tx: Taxonomy, cid: str, locale: str) -> dict:
    c = tx.categories[cid]
    name, desc = _loc_cat(tx, cid, locale)
    return {
        "id": GID.format(id=c.id),
        "level": c.depth,
        "name": name,
        "full_name": tx.full_name(cid, locale),
        "friendly_id": c.friendly_id,
        "handle": c.handle,
        "description": desc,
        "aliases": c.aliases,
        "inclusion_rule": c.inclusion_rule,
        "parent_id": GID.format(id=c.parent_id) if c.parent_id else None,
        "children": [{"id": GID.format(id=ch), "name": _loc_cat(tx, ch, locale)[0]} for ch in c.children],
        "ancestors": [{"id": GID.format(id=a.id), "name": _loc_cat(tx, a.id, locale)[0]} for a in tx.ancestors(cid)],
        "attributes": [
            {"id": GID_ATTR.format(id=tx.attributes[a].id), "name": _loc_attr(tx, a, locale)[0], "friendly_id": a, "handle": tx.attributes[a].handle}
            for a in tx.effective_attributes(cid)
        ],
        "examples": c.examples,
    }


def build(tx: Taxonomy, out: Path = DIST) -> list[Path]:
    if out.exists():
        shutil.rmtree(out)
    written: list[Path] = []
    locales = [SOURCE_LOCALE, *tx.locales]
    ordered_cats = sorted(tx.categories, key=lambda cid: [int(p) if p.isdigit() else p for p in cid.split("-")])
    for locale in locales:
        ldir = out / locale
        ldir.mkdir(parents=True)
        cats = {"version": version(), "verticals": []}
        for root in tx.roots():
            cats["verticals"].append(
                {
                    "name": _loc_cat(tx, root.id, locale)[0],
                    "prefix": root.id,
                    "categories": [category_json(tx, cid, locale) for cid in ordered_cats if tx.categories[cid].root == root.id],
                }
            )
        attrs = {"version": version(), "attributes": [attribute_json(tx, fid, locale) for fid in tx.attributes]}
        vals = {"version": version(), "values": [value_json(tx, fid, locale) for fid in tx.values]}
        written += [
            _write_json(ldir / "categories.json", cats),
            _write_json(ldir / "attributes.json", attrs),
            _write_json(ldir / "values.json", vals),
            _write_txt(ldir / "categories.txt", [f"{GID.format(id=cid)} : {tx.full_name(cid, locale)}" for cid in ordered_cats]),
            _write_txt(ldir / "attributes.txt", [f"{GID_ATTR.format(id=a.id)} : {_loc_attr(tx, a.friendly_id, locale)[0]}" for a in tx.attributes.values()]),
            _write_txt(ldir / "values.txt", [f"{GID_VALUE.format(id=v.id)} : {_loc_value(tx, v.friendly_id, locale)} [{_loc_attr(tx, v.attribute_friendly_id, locale)[0]}]" for v in tx.values.values()]),
        ]
    # integrations
    idir = out / "integrations"
    idir.mkdir()
    all_mappings = {"version": version(), "mappings": []}
    for m in tx.mappings:
        src = f"whatrobot/{version()}" if m.direction == "from_whatrobot" else f"{m.integration}/{m.version}"
        tgt = f"{m.integration}/{m.version}" if m.direction == "from_whatrobot" else f"whatrobot/{version()}"
        rules = []
        for rule in m.file.rules:
            if m.file.input_kind == "attribute_value":
                inp = {"attribute_value": {"friendly_id": rule.input["attribute_value"], "name": tx.values[rule.input["attribute_value"]].name}}
            elif m.direction == "from_whatrobot":
                cid = rule.input["category_id"]
                inp = {"category": {"id": GID.format(id=cid), "full_name": tx.full_name(cid)}}
            else:
                cid = rule.input["category_id"]
                inp = {"category": {"id": cid, "full_name": m.full_names.get(cid, cid)}}
            outs = []
            for o in rule.output.get("category_id", []):
                if m.direction == "from_whatrobot":
                    outs.append({"id": o, "full_name": m.full_names.get(o, o)})
                else:
                    outs.append({"id": GID.format(id=o), "full_name": tx.full_name(o)})
            rules.append({"input": inp, "output": {"category": outs}})
        entry = {"input_taxonomy": src, "output_taxonomy": tgt, "rules": rules}
        all_mappings["mappings"].append(entry)
        written.append(_write_json(idir / f"{src.replace('/', '_')}_to_{tgt.replace('/', '_')}.json", {"version": version(), "mappings": [entry]}))
    written.append(_write_json(idir / "all_mappings.json", all_mappings))
    return written


def _write_json(path: Path, obj: dict) -> Path:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _write_txt(path: Path, lines: list[str]) -> Path:
    path.write_text(f"# whatrobot taxonomy {version()} — CC BY 4.0\n" + "\n".join(lines) + "\n", encoding="utf-8")
    return path
