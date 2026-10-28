"""CI test suite (docs/design.md §9.8). Licence: MIT."""
from __future__ import annotations

import json

import pytest

from whatrobot_taxonomy import DATA, DIST, ROOT
from whatrobot_taxonomy import version
from whatrobot_taxonomy.classify import Unclassifiable, classify
from whatrobot_taxonomy.dist import build
from whatrobot_taxonomy.loader import load
from whatrobot_taxonomy.validate import validate


@pytest.fixture(scope="session")
def tx():
    return load(DATA)


@pytest.fixture(scope="session")
def report(tx):
    return validate(tx)


# ------------------------------------------------------------ schema & integrity
def test_validation_has_no_errors(report):
    assert report.errors == [], "\n".join(report.errors)


def test_validation_warnings_are_reported(report, capsys):
    # warnings do not fail CI (localisation gaps are allowed) but must be visible in the log
    for w in report.warnings:
        print("WARN", w)


def test_roots_and_depth(tx):
    assert {r.id for r in tx.roots()} == {"rb", "cp"}
    assert max(c.depth for c in tx.categories.values()) <= 3


def test_decision_d5_robot_branches(tx):
    handles = [tx.categories[c].handle for c in tx.categories["rb"].children]
    assert handles == ["arm", "humanoid", "legged", "ground", "mobile-manipulator", "aerial", "aquatic", "wearable", "stationary", "kit"]


def test_decision_d6_component_branches(tx):
    handles = [tx.categories[c].handle for c in tx.categories["cp"].children]
    assert handles == ["end-effector", "actuator", "sensor", "compute", "power", "structure", "teleoperation"]
    ee = [tx.categories[c].handle for c in tx.categories["cp-1"].children]
    assert "gripper" in ee and "hand" in ee  # siblings under end-effector


def test_decision_d3_segment_has_no_industrial(tx):
    vals = tx.attributes["segment"].values
    assert "segment__industrial" not in vals
    assert vals[:-1] == ["segment__hobby", "segment__education", "segment__research", "segment__professional", "segment__consumer"]


def test_every_enum_ends_with_other(tx):
    for a in tx.attributes.values():
        if a.type == "enum":
            assert a.values[-1] == f"{a.friendly_id}__other"


def test_every_leaf_has_description_rule_and_example(tx):
    for leaf in tx.leaves():
        assert leaf.description and leaf.inclusion_rule and leaf.examples, leaf.id


def test_attribute_inheritance(tx):
    quad = tx.effective_attributes("rb-3-1")
    assert quad[: len(tx.categories["rb"].attributes)] == tx.categories["rb"].attributes
    assert {"wheel_feet", "has_arm", "height"} <= set(quad)
    assert "axes" not in quad  # arm-bound only
    assert "axes" in tx.effective_attributes("rb-1-1")
    assert "axes" in tx.effective_attributes("cp-3-3")  # shared numeric attribute


# ------------------------------------------------------------ classification (§2.1 / §4.1)
def test_examples_classify(tx):
    for ex in tx.examples:
        assert classify(ex.facts) == ex.expected, ex.handle


@pytest.mark.parametrize(
    "facts,expected",
    [
        ({"legs": 4, "integrated_arm": True, "manipulates": True}, "rb-3-1"),  # Spot with arm stays quadruped
        ({"legs": 4, "wheels_or_tracks": "wheels"}, "rb-3-1"),  # wheel-feet stays quadruped
        ({"humanoid_form": True, "wheels_or_tracks": "wheels"}, "rb-2-2"),
        ({"is_kit": True, "legs": 4}, "rb-10"),  # kit beats legs
        ({"worn_on_body": True, "legs": 2}, "rb-8-1"),  # wearable beats legs
        ({"wheels_or_tracks": "wheels", "integrated_arm": True}, "rb-5"),
        ({"wheels_or_tracks": "tracks"}, "rb-4-2"),
        ({"fixed_base": True, "manipulates": False}, "rb-9"),
        ({"legs": 4, "humanoid_form": False, "medium": "ground"}, "rb-3-1"),
        ({"component_kind": "end-effector", "grasps": True, "fingers": 3, "opposable_thumb": True, "dof": 4, "gripping_principle": "finger"}, "cp-1-1-1"),
        ({"component_kind": "actuator", "motion": "rotary", "integrated_control": True, "has_reducer": True, "industrial_bus": False}, "cp-2-2"),
    ],
)
def test_tie_break_order(facts, expected):
    assert classify(facts) == expected


def test_unclassifiable_raises():
    with pytest.raises(Unclassifiable):
        classify({"medium": "air"})  # needs aerial_lift
    with pytest.raises(Unclassifiable):
        classify({})
    with pytest.raises(Unclassifiable):
        classify({"legs": "two"})
    with pytest.raises(Unclassifiable):
        classify({"legs": 3})


# ------------------------------------------------------------ dist
def test_dist_builds_and_is_consistent(tx, tmp_path):
    files = build(tx, tmp_path)
    assert files
    cats = json.loads((tmp_path / "en" / "categories.json").read_text())
    ids = [c["id"] for v in cats["verticals"] for c in v["categories"]]
    assert len(ids) == len(tx.categories) == len(set(ids))
    zh = json.loads((tmp_path / "zh-Hans" / "categories.json").read_text())
    assert zh["verticals"][0]["categories"][0]["name"] != cats["verticals"][0]["categories"][0]["name"]
    mappings = json.loads((tmp_path / "integrations" / "all_mappings.json").read_text())
    assert len(mappings["mappings"]) == len(tx.mappings)


def test_committed_dist_is_up_to_date(tx, tmp_path):
    """dist/ is generated; a PR that edits data/ must regenerate it."""
    if not DIST.exists():
        pytest.skip("no committed dist")
    build(tx, tmp_path)
    for f in tmp_path.rglob("*.*"):
        rel = f.relative_to(tmp_path)
        assert (DIST / rel).exists(), f"dist/{rel} missing — run: whatrobot-taxonomy dist"
        assert (DIST / rel).read_text(encoding="utf-8") == f.read_text(encoding="utf-8"), f"dist/{rel} is stale — run: whatrobot-taxonomy dist"


def test_licence_files_present():
    assert (ROOT / "LICENSE").read_text(encoding="utf-8").startswith("MIT License")
    assert "Attribution 4.0" in (DATA / "LICENSE").read_text(encoding="utf-8")


def test_version_is_calver_and_matches_pyproject():
    import re
    v = version()
    assert re.fullmatch(r"\d{4}-\d{2}", v), v
    py = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert f'version = "{v.replace("-0", ".").replace("-", ".")}"' in py, "pyproject version must equal VERSION in PEP 440 form (2026-01 → 2026.1)"
