"""Localisation review: fingerprints, status, review-sheet export and import. Licence: MIT.

Every localisable English string is a *field* with a key:

    category.<id>.name | category.<id>.description | category.<id>.aliases
    attribute.<friendly_id>.name | attribute.<friendly_id>.description
    value.<friendly_id>.name

A localised field is *reviewed* when its entry's ``source`` map holds the fingerprint of the English text a
native reader checked it against. If the English changes later the fingerprints differ and the field is
*stale*. Fields without a fingerprint are *drafts*; fields with no text at all are *missing*.

Review round trip (docs/design.md §9.9):

    whatrobot-taxonomy l10n export --locale da --locale zh-Hans -o review.csv   # rows to review
    ... reviewers correct the text and tick the OK column (e.g. in a shared Google Sheet) ...
    whatrobot-taxonomy l10n import review.csv --locale da                       # only ticked rows land
    whatrobot-taxonomy l10n status                                              # reviewed / stale / draft / missing
"""
from __future__ import annotations

import csv
import hashlib
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from ruamel.yaml import YAML

from . import DATA
from .loader import SOURCE_LOCALE, Taxonomy

KINDS = {"category": "categories", "attribute": "attributes", "value": "values"}
KIND_FIELDS = {"category": ("name", "description", "aliases"), "attribute": ("name", "description"), "value": ("name",)}
ALIAS_SPLIT = re.compile(r"\s*[;；]\s*")
TRUTHY = {"true", "1", "yes", "y", "x", "ok", "✓", "✔"}

# Display headers used in the shared review sheet, mapped to canonical CSV columns.
# "Dansk (DA)" -> da, "DA ✓" -> da_ok, "DA note" -> da_note; codes not listed are lower-cased.
SHEET_CODES = {"ZH": "zh-Hans", "ZH-HANS": "zh-Hans"}


def fingerprint(text: str | list[str] | None) -> str:
    """Stable 12-hex fingerprint of an English string (aliases are joined with '; ')."""
    if isinstance(text, list):
        text = "; ".join(text)
    norm = " ".join((text or "").split())
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:12]


def parse_key(key: str) -> tuple[str, str, str]:
    kind, _, rest = key.partition(".")
    ident, _, fld = rest.rpartition(".")
    if kind not in KIND_FIELDS or not ident or fld not in KIND_FIELDS[kind]:
        raise KeyError(key)
    return kind, ident, fld


def _record(tx: Taxonomy, kind: str, ident: str):
    return {"category": tx.categories, "attribute": tx.attributes, "value": tx.values}[kind].get(ident)


def english(tx: Taxonomy, key: str) -> str:
    kind, ident, fld = parse_key(key)
    rec = _record(tx, kind, ident)
    if rec is None:
        raise KeyError(key)
    val = getattr(rec, fld)
    return "; ".join(val) if isinstance(val, list) else (val or "")


def fields(tx: Taxonomy) -> list[tuple[str, str]]:
    """(key, type label) for every localisable field, in display order: robot tree, component tree, attributes, values."""
    out: list[tuple[str, str]] = []

    def walk(cid: str):
        yield cid
        for ch in tx.categories[cid].children:
            yield from walk(ch)

    for root in tx.roots():
        for cid in walk(root.id):
            out += [(f"category.{cid}.name", "Category name"), (f"category.{cid}.description", "Category description"),
                    (f"category.{cid}.aliases", "Search terms")]
    for fid in tx.attributes:
        out += [(f"attribute.{fid}.name", "Spec name"), (f"attribute.{fid}.description", "Spec description")]
    for fid in tx.values:
        out.append((f"value.{fid}.name", "Option"))
    return out


def where(tx: Taxonomy, key: str) -> str:
    """Short context for a reviewer: where the string appears on the site."""
    kind, ident, fld = parse_key(key)
    if kind == "category":
        name = tx.categories[ident].name
        return {"name": tx.full_name(ident).replace(" > ", " › "), "description": f"Description of {name}",
                "aliases": f"Other names people search for, for {name}. Separate with ;"}[fld]
    if kind == "attribute":
        a = tx.attributes[ident]
        if fld == "description":
            return f"Help text for {a.name}"
        on = [c.name for c in tx.categories.values() if ident in (c.attributes or [])]
        unit = f" · unit {a.unit}" if a.unit and a.unit not in ("count", "year", "currency") else ""
        return f"Spec label and filter on: {', '.join(on) or 'product data'}{unit}"
    v = tx.values[ident]
    return f"Option of: {tx.attributes[v.attribute_friendly_id].name}"


def localized(tx: Taxonomy, locale: str, key: str) -> tuple[str | None, str | None]:
    """(text, reviewed-against fingerprint) of a field in a locale."""
    kind, ident, fld = parse_key(key)
    loc = tx.locales.get(locale)
    entry = getattr(loc, KINDS[kind]).get(ident) if loc else None
    if entry is None:
        return None, None
    val = getattr(entry, fld, None)
    text = "; ".join(val) if isinstance(val, list) else val
    return (text or None), (entry.source or {}).get(fld)


def state(tx: Taxonomy, locale: str, key: str) -> str:
    text, fp = localized(tx, locale, key)
    if not text:
        return "missing"
    if fp is None:
        return "draft"
    return "reviewed" if fp == fingerprint(english(tx, key)) else "stale"


def status(tx: Taxonomy, locales: list[str] | None = None) -> dict[str, Counter]:
    keys = [k for k, _ in fields(tx) if english(tx, k)]
    return {loc: Counter(state(tx, loc, k) for k in keys) for loc in (locales or list(tx.locales))}


def launch_ready(counts: Counter) -> bool:
    return counts["reviewed"] > 0 and counts["reviewed"] == sum(counts.values())


# ------------------------------------------------------------ export
def export_rows(tx: Taxonomy, locales: list[str], only_needed: bool = False) -> list[dict[str, str]]:
    rows = []
    for key, label in fields(tx):
        en = english(tx, key)
        if not en:
            continue
        states = {loc: state(tx, loc, key) for loc in locales}
        if only_needed and all(s == "reviewed" for s in states.values()):
            continue
        row = {"key": key, "type": label, "english": en, "where": where(tx, key)}
        for loc in locales:
            text, _ = localized(tx, loc, key)
            row[loc] = text or ""
            row[f"{loc}_ok"] = ""
            row[f"{loc}_note"] = "" if states[loc] != "stale" else "English changed since review"
        rows.append(row)
    return rows


def write_csv(rows: list[dict[str, str]], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else ["key"])
        w.writeheader()
        w.writerows(rows)


# ------------------------------------------------------------ import
def canonical_header(h: str) -> str:
    h = h.strip()
    low = h.lower()
    if low in ("key", "english", "type", "where", "where it appears"):
        return {"where it appears": "where"}.get(low, low)
    if m := re.fullmatch(r".*\(([A-Za-z-]+)\)", h):
        code = m.group(1).upper()
        return SHEET_CODES.get(code, code.lower())
    if m := re.fullmatch(r"([A-Za-z-]+)\s*(✓|ok)", h, flags=re.I):
        code = m.group(1).upper()
        return SHEET_CODES.get(code, code.lower()) + "_ok"
    if m := re.fullmatch(r"([A-Za-z-]+)\s+note", h, flags=re.I):
        code = m.group(1).upper()
        return SHEET_CODES.get(code, code.lower()) + "_note"
    return h


def read_review(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        rdr = csv.reader(fh)
        header = [canonical_header(h) for h in next(rdr)]
        return [dict(zip(header, r)) for r in rdr if any(c.strip() for c in r)]


@dataclass
class ImportReport:
    imported: Counter = field(default_factory=Counter)
    unticked: int = 0
    english_changed: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    needs_name: list[str] = field(default_factory=list)
    kept_reviewed: int = 0


def import_review(tx: Taxonomy, locale: str, rows: list[dict[str, str]], data_dir: Path = DATA,
                  accept_changed_english: bool = False) -> ImportReport:
    """Write ticked rows for `locale` into data/localizations/<locale>/. Unticked rows are left alone."""
    if locale == SOURCE_LOCALE:
        raise ValueError("the source locale is not imported")
    rep = ImportReport()
    if rows and locale not in rows[0]:
        raise ValueError(f"no column for locale {locale!r}; columns: {', '.join(rows[0])}")
    ok_col = f"{locale}_ok"
    pending: dict[tuple[str, str], dict[str, str]] = defaultdict(dict)
    for row in rows:
        key = row.get("key", "").strip()
        try:
            kind, ident, fld = parse_key(key)
            current = english(tx, key)
        except KeyError:
            rep.errors.append(f"unknown key {key!r}")
            continue
        if row.get(ok_col, "").strip().lower() not in TRUTHY:
            rep.unticked += 1
            continue
        text = (row.get(locale) or "").strip()
        if not text:
            rep.errors.append(f"{key}: ticked but empty")
            continue
        if " ".join(row.get("english", "").split()) != " ".join(current.split()) and not accept_changed_english:
            rep.english_changed.append(key)
            continue
        pending[(kind, ident)][fld] = text

    files = {k: _read_locale_file(data_dir, locale, k) for k in KINDS.values()}
    changed: set[str] = set()
    for (kind, ident), flds in pending.items():
        entries = files[KINDS[kind]][1]
        entry = dict(entries.get(ident) or {})
        if "name" not in entry and "name" not in flds:
            rep.needs_name.append(f"{kind}.{ident}")
            continue
        src = dict(entry.get("source") or {})
        for fld, text in flds.items():
            if fld == "aliases":
                vals = [a for a in ALIAS_SPLIT.split(text) if a]
                entry[fld] = list(dict.fromkeys(vals))
            else:
                entry[fld] = text
            src[fld] = fingerprint(english(tx, f"{kind}.{ident}.{fld}"))
            rep.imported[kind] += 1
        entry["source"] = src
        entries[ident] = entry
        changed.add(KINDS[kind])

    order = {
        "categories": [k.split(".")[1] for k, _ in fields(tx) if k.startswith("category.") and k.endswith(".name")],
        "attributes": list(tx.attributes),
        "values": list(tx.values),
    }
    for kind_file, (header, entries) in files.items():
        if kind_file in changed:
            _write_locale_file(data_dir, locale, kind_file, header, entries, order[kind_file])
    return rep


def import_drafts(tx: Taxonomy, locale: str, rows: list[dict[str, str]], data_dir: Path = DATA) -> ImportReport:
    """Write every non-empty text for `locale` as an unreviewed draft (machine first drafts).

    A field already reviewed against the current English is kept as it is. A draft replacing a stale review
    drops that field's fingerprint, so the field reads as draft until a reviewer ticks it.
    """
    if locale == SOURCE_LOCALE:
        raise ValueError("the source locale is not imported")
    rep = ImportReport()
    if rows and locale not in rows[0]:
        raise ValueError(f"no column for locale {locale!r}; columns: {', '.join(rows[0])}")
    pending: dict[tuple[str, str], dict[str, str]] = defaultdict(dict)
    for row in rows:
        key = row.get("key", "").strip()
        try:
            kind, ident, fld = parse_key(key)
            english(tx, key)
        except KeyError:
            rep.errors.append(f"unknown key {key!r}")
            continue
        text = (row.get(locale) or "").strip()
        if not text:
            rep.unticked += 1
            continue
        if state(tx, locale, key) == "reviewed":
            rep.kept_reviewed += 1
            continue
        pending[(kind, ident)][fld] = text

    files = {k: _read_locale_file(data_dir, locale, k) for k in KINDS.values()}
    changed: set[str] = set()
    for (kind, ident), flds in pending.items():
        entries = files[KINDS[kind]][1]
        entry = dict(entries.get(ident) or {})
        if "name" not in entry and "name" not in flds:
            rep.needs_name.append(f"{kind}.{ident}")
            continue
        src = dict(entry.get("source") or {})
        for fld, text in flds.items():
            if fld == "aliases":
                entry[fld] = list(dict.fromkeys(a for a in ALIAS_SPLIT.split(text) if a))
            else:
                entry[fld] = text
            src.pop(fld, None)
            rep.imported[kind] += 1
        if src:
            entry["source"] = src
        else:
            entry.pop("source", None)
        entries[ident] = entry
        changed.add(KINDS[kind])

    order = {
        "categories": [k.split(".")[1] for k, _ in fields(tx) if k.startswith("category.") and k.endswith(".name")],
        "attributes": list(tx.attributes),
        "values": list(tx.values),
    }
    for kind_file, (header, entries) in files.items():
        if kind_file in changed:
            _write_locale_file(data_dir, locale, kind_file, header, entries, order[kind_file])
    return rep


# ------------------------------------------------------------ YAML in the house style (one flow mapping per line)
_PLAIN_BAD_START = set("-?:,[]{}#&*!|>'\"%@` ")
_RESERVED = re.compile(r"^(?:~|null|true|false|yes|no|on|off|y|n|[-+]?(?:\.inf|\.nan|\d[\d_]*(?:\.\d*)?(?:e[-+]?\d+)?|0x[0-9a-f]+|0o[0-7]+))$", re.I)
FIELD_ORDER = ("name", "description", "aliases", "source")
_yaml = YAML(typ="safe", pure=True)


def _scalar(s: str) -> str:
    plain = (s and s == s.strip() and s[0] not in _PLAIN_BAD_START and not _RESERVED.match(s)
             and not any(c in s for c in ",[]{}") and ": " not in s and " #" not in s and not s.endswith(":")
             and "\n" not in s)
    return s if plain else "'" + s.replace("'", "''") + "'"


def _flow(v) -> str:
    if isinstance(v, dict):
        keys = [k for k in FIELD_ORDER if k in v] + [k for k in v if k not in FIELD_ORDER]
        return "{" + ", ".join(f"{k}: {_flow(v[k])}" for k in keys) + "}"
    if isinstance(v, list):
        return "[" + ", ".join(_flow(x) for x in v) + "]"
    return _scalar(str(v))


HEADER = """# whatrobot taxonomy — {locale} localisation of {what}
# Licence: CC BY 4.0. Keyed by {keyed}. Localised: {loc_fields}. Inclusion rules stay English.
# Review state: a field listed under `source` was reviewed by a native reader against the English text with that
# fingerprint; fields not listed are LLM drafts. Check with: whatrobot-taxonomy l10n status
---
"""
_HEADER_ARGS = {
    "categories": ("categories", "category id", "name, description, aliases"),
    "attributes": ("attributes", "attribute friendly_id", "name, description"),
    "values": ("attribute values", "value friendly_id", "name"),
}


def _read_locale_file(data_dir: Path, locale: str, kind_file: str) -> tuple[str, dict]:
    path = data_dir / "localizations" / locale / f"{kind_file}.yml"
    if not path.exists():
        return "", {}
    with path.open(encoding="utf-8") as fh:
        data = _yaml.load(fh) or {}
    return "", dict(data)


def _write_locale_file(data_dir: Path, locale: str, kind_file: str, _header: str, entries: dict, order: list[str]) -> Path:
    what, keyed, loc_fields = _HEADER_ARGS[kind_file]
    lines = [HEADER.format(locale=locale, what=what, keyed=keyed, loc_fields=loc_fields).rstrip("\n")]
    for ident in sorted(entries, key=lambda i: order.index(i) if i in order else len(order)):
        lines.append(f"{_scalar(ident)}: {_flow(entries[ident])}")
    text = "\n".join(lines) + "\n"
    if _yaml.load(text) != entries:  # the hand-written flow style must round-trip exactly
        raise AssertionError(f"{locale}/{kind_file}.yml would not round-trip")
    path = data_dir / "localizations" / locale / f"{kind_file}.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path
