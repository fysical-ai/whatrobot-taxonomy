"""Localisation review round trip (docs/design.md §9.9). Licence: MIT."""
from __future__ import annotations

import csv
import json
import shutil

import pytest

from whatrobot_taxonomy import DATA, l10n
from whatrobot_taxonomy.dist import build
from whatrobot_taxonomy.loader import load
from whatrobot_taxonomy.validate import validate


@pytest.fixture()
def data_copy(tmp_path):
    d = tmp_path / "data"
    shutil.copytree(DATA, d)
    return d


def _review_csv(tx, path, locale, edits: dict[str, str], tick: set[str]):
    rows = l10n.export_rows(tx, [locale])
    for r in rows:
        if r["key"] in edits:
            r[locale] = edits[r["key"]]
        if r["key"] in tick:
            r[f"{locale}_ok"] = "TRUE"
    l10n.write_csv(rows, path)
    return path


def test_fingerprint_is_stable_and_ignores_spacing():
    assert l10n.fingerprint("Legged robot with four legs.") == l10n.fingerprint("Legged  robot with four legs. ")
    assert l10n.fingerprint(["robot dog", "quadruped"]) == l10n.fingerprint("robot dog; quadruped")
    assert len(l10n.fingerprint("x")) == 12


def test_every_field_key_parses_and_has_english():
    tx = load(DATA)
    keys = [k for k, _ in l10n.fields(tx)]
    assert len(keys) == len(set(keys))
    assert len(keys) == 3 * len(tx.categories) + 2 * len(tx.attributes) + len(tx.values)
    for k in keys:
        l10n.parse_key(k)
        assert l10n.english(tx, k)


def test_sheet_headers_are_understood():
    h = l10n.canonical_header
    assert [h(x) for x in ("Key", "English", "Where it appears", "Dansk (DA)", "DA ✓", "DA note", "中文 (ZH)", "ZH ✓", "ZH note", "Deutsch (DE)")] == [
        "key", "english", "where", "da", "da_ok", "da_note", "zh-Hans", "zh-Hans_ok", "zh-Hans_note", "de"]


def test_import_writes_only_ticked_rows_with_fingerprints(data_copy, tmp_path):
    tx = load(data_copy)
    keys = ["category.rb-3-1.name", "category.rb-3-1.description", "category.rb-3-1.aliases", "value.segment__hobby.name"]
    edits = {keys[0]: "Firbenet robot", keys[1]: "Robot med fire ben.", keys[2]: "robothund; firbenet robot", keys[3]: "Hobby",
             "category.rb-3-2.name": "Tobenet robot"}
    csv_path = _review_csv(tx, tmp_path / "review.csv", "da", edits, tick=set(keys))
    rep = l10n.import_review(tx, "da", l10n.read_review(csv_path), data_dir=data_copy)
    assert sum(rep.imported.values()) == 4 and not rep.errors
    tx2 = load(data_copy)
    q = tx2.locales["da"].categories["rb-3-1"]
    assert q.name == "Firbenet robot" and q.aliases == ["robothund", "firbenet robot"]
    assert set(q.source) == {"name", "description", "aliases"}
    assert "rb-3-2" not in tx2.locales["da"].categories  # edited but not ticked
    assert l10n.state(tx2, "da", keys[0]) == "reviewed"
    assert validate(tx2).ok
    # dist carries the localised search terms
    build(tx2, tmp_path / "dist")
    cats = json.loads((tmp_path / "dist" / "da" / "categories.json").read_text(encoding="utf-8"))
    quad = next(c for v in cats["verticals"] for c in v["categories"] if c["id"].endswith("/rb-3-1"))
    assert quad["aliases"] == ["robothund", "firbenet robot"] and quad["name"] == "Firbenet robot"


def test_changed_english_is_held_back_then_flagged_stale(data_copy, tmp_path):
    tx = load(data_copy)
    key = "category.rb-3-1.description"
    rows = l10n.export_rows(tx, ["da"])
    for r in rows:
        if r["key"] in (key, "category.rb-3-1.name"):
            r["da"], r["da_ok"] = "Robot med fire ben.", "TRUE"
        if r["key"] == "category.rb-3-1.name":
            r["da"] = "Firbenet robot"
        if r["key"] == key:
            r["english"] = "An older English text."
    rep = l10n.import_review(tx, "da", rows, data_dir=data_copy)
    assert rep.english_changed == [key] and rep.imported["category"] == 1
    # now review it properly, then change the English: the field turns stale and validation warns
    rows2 = [dict(r, english=l10n.english(tx, key)) for r in rows if r["key"] == key]
    l10n.import_review(load(data_copy), "da", rows2, data_dir=data_copy)
    src = data_copy / "categories" / "rb_robot.yml"
    src.write_text(src.read_text(encoding="utf-8").replace("Legged robot with four legs.", "Legged robot with exactly four legs."), encoding="utf-8")
    tx3 = load(data_copy)
    assert l10n.state(tx3, "da", key) == "stale"
    assert any("reviewed against older English" in w for w in validate(tx3).warnings)
    needed = {r["key"] for r in l10n.export_rows(tx3, ["da"], only_needed=True)}
    assert key in needed and "category.rb-3-1.name" not in needed


def test_existing_drafts_count_as_drafts():
    tx = load(DATA)
    counts = l10n.status(tx)["zh-Hans"]
    assert counts["draft"] > 0 and not l10n.launch_ready(counts)
