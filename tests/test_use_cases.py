"""Use cases, environment profiles and their checks (docs/design.md §11). Licence: MIT."""
from __future__ import annotations

import dataclasses
import json

import pytest
from pydantic import ValidationError

from whatrobot_taxonomy import DATA, DIST
from whatrobot_taxonomy.loader import load
from whatrobot_taxonomy.models import Requirement, UseCase
from whatrobot_taxonomy.validate import validate


@pytest.fixture(scope="module")
def tx():
    return load(DATA)


def _with(tx, uc_id: str, **changes):
    """A copy of the taxonomy in which one use case has `changes` applied."""
    uc = tx.use_cases[uc_id]
    new = UseCase.model_validate(uc.model_dump() | changes)
    return dataclasses.replace(tx, use_cases={**tx.use_cases, uc_id: new})


def _errors(tx) -> list[str]:
    return [e for e in validate(tx).errors if e.startswith(("uc-", "env-"))]


def _req(**kw):
    return Requirement.model_validate({"level": "hard", "rationale": "test"} | kw).model_dump()


def test_pilot_use_cases_are_valid(tx):
    assert len(tx.use_cases) >= 6
    assert _errors(tx) == []


def test_every_solution_type_is_piloted(tx):
    assert {u.solution_type for u in tx.use_cases.values()} == {"turnkey", "platform", "cell"}


def test_every_hard_requirement_has_a_rationale(tx):
    for uc_id in tx.use_cases:
        for _, req in tx.requirements_of(uc_id):
            assert req.rationale.strip()


def test_profiles_are_expanded_before_own_requirements(tx):
    reqs = tx.requirements_of("uc-1")
    assert [env for env, _ in reqs][:3] == ["env-outdoor-all-weather"] * 3
    assert reqs[-1][0] is None


def test_condition_needs_exactly_one_operand():
    with pytest.raises(ValidationError):
        Requirement.model_validate({"attribute": "payload", "op": ">=", "level": "hard", "rationale": "x"})
    with pytest.raises(ValidationError):
        Requirement.model_validate({"attribute": "payload", "op": ">=", "value": 1, "param": "p", "level": "hard", "rationale": "x"})


@pytest.mark.parametrize(
    "changes, expect",
    [
        ({"application": "application__nonsense"}, "is not an application value"),
        ({"related_applications": ["application__inspection-maintenance"]}, "repeats the use case's own application"),
        ({"body_plans": [{"category": "cp-1", "note": "x"}]}, "is not a robot category"),
        ({"body_plans": [{"category": "rb-4", "note": "x"}, {"category": "rb-4-1", "note": "x"}]}, "lies inside another listed body plan"),
        ({"environment": ["env-nowhere"]}, "environment profile env-nowhere does not exist"),
        ({"requirements": [_req(attribute="no_such_attribute", op="eq", value=True)]}, "attribute no_such_attribute does not exist"),
        ({"requirements": [_req(attribute="autonomy", op=">=", value=3)]}, "needs a number attribute"),
        ({"requirements": [_req(attribute="autonomy", op="in", value=["self-driving"])]}, "is not a value of autonomy"),
        ({"requirements": [_req(attribute="payload", op="ip_liquids>=", value=4)]}, "only applies to ip_rating"),
        ({"requirements": [_req(attribute="battery_runtime", op=">=", param="missing")]}, "parameter missing is not defined"),
        ({"requirements": [_req(attribute="battery_runtime", op=">=", param="site")]}, "needs number"),
        ({"requirements": [_req(attribute="wingspan", op=">=", value=1)]}, "is bound to none of the body plans"),
        ({"requirements": [_req(attribute="stairs", op="eq", value=True, when={"nope": True})]}, "when refers to parameter nope"),
        ({"slots": [{"role": "x", "name": "X", "need": "optional", "category": "rb-1", "note": "x"}]}, "is not a component category"),
        ({"slots": [{"role": "x", "name": "X", "need": "optional", "category": "cp-5", "where": [{"attribute": "modality", "op": "has", "value": "thermal"}], "note": "x"}]}, "is not bound in cp-5"),
    ],
)
def test_bad_use_cases_are_rejected(tx, changes, expect):
    errors = _errors(_with(tx, "uc-3", **changes))
    assert any(expect in e for e in errors), errors


def test_unused_parameter_is_rejected(tx):
    errors = _errors(_with(tx, "uc-3", requirements=[]))
    assert any("is used by no requirement" in e for e in errors)


def test_turnkey_takes_no_related_applications_or_required_parts(tx):
    assert any("turnkey" in e for e in _errors(_with(tx, "uc-1", related_applications=["application__agriculture"])))
    slot = {"role": "dock", "name": "Dock", "need": "required", "category": "cp-5", "note": "x"}
    assert any("cannot require a component" in e for e in _errors(_with(tx, "uc-1", slots=[slot])))


def test_dist_carries_use_cases_with_profiles_expanded(tx):
    data = json.loads((DIST / "en" / "use_cases.json").read_text(encoding="utf-8"))
    assert [u["id"] for u in data["use_cases"]] == sorted(tx.use_cases, key=lambda i: int(i.split("-")[1]))
    mowing = next(u for u in data["use_cases"] if u["id"] == "uc-1")
    assert mowing["application"]["group"]["handle"] == "consumer"
    assert [r.get("profile") for r in mowing["requirements"]][:3] == ["env-outdoor-all-weather"] * 3
    assert all(("param" in r) != ("value" in r) for u in data["use_cases"] for r in u["requirements"])
    assert {p["key"]: p["default"] for p in mowing["parameters"]} == {"lawn_area": None, "slope": None}
