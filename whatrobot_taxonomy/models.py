"""Pydantic models for every source record. JSON Schemas are generated from these (`whatrobot-taxonomy schema`)."""
from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

CATEGORY_ID_RE = re.compile(r"^(rb|cp)(-[1-9]\d*)*$")
FRIENDLY_CAT_RE = re.compile(r"^[a-z][a-z0-9-]*(\.[a-z][a-z0-9-]*)*$")
SNAKE_RE = re.compile(r"^[a-z][a-z0-9_]*$")
KEBAB_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
VALUE_FID_RE = re.compile(r"^[a-z][a-z0-9_]*__[a-z0-9][a-z0-9.-]*$")

AttributeType = Literal["enum", "number", "bool", "text", "ref"]
RefTarget = Literal["robot", "component", "manufacturer"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Category(Strict):
    id: str = Field(pattern=CATEGORY_ID_RE.pattern, description="Positional, permanent id, e.g. rb-3-1")
    name: str = Field(min_length=1)
    friendly_id: str = Field(pattern=FRIENDLY_CAT_RE.pattern)
    handle: str = Field(pattern=KEBAB_RE.pattern)
    description: str = Field(min_length=1)
    aliases: list[str] = []
    inclusion_rule: str = Field(min_length=1)
    children: list[str] = []
    attributes: list[str] = []
    examples: list[str] = []

    @property
    def root(self) -> str:
        return self.id.split("-")[0]

    @property
    def depth(self) -> int:
        return self.id.count("-")

    @property
    def parent_id(self) -> str | None:
        return self.id.rsplit("-", 1)[0] if "-" in self.id else None

    @model_validator(mode="after")
    def _ids_consistent(self) -> Category:
        if self.handle != self.friendly_id.split(".")[-1]:
            raise ValueError(f"{self.id}: handle must equal the last segment of friendly_id")
        return self


class Basis(Strict):
    """One way of measuring a number attribute (e.g. payload while walking vs standing). The first basis listed on an
    attribute is its default: the figure to record when a source gives several. Another basis is recorded, with its
    label, only when the source gives no figure on the default basis."""
    handle: str = Field(pattern=KEBAB_RE.pattern)
    description: str = Field(min_length=1)


class Attribute(Strict):
    id: int = Field(gt=0)
    name: str = Field(min_length=1)
    friendly_id: str = Field(pattern=SNAKE_RE.pattern)
    handle: str = Field(pattern=KEBAB_RE.pattern)
    description: str = Field(min_length=1)
    question: str = Field(min_length=1)
    type: AttributeType
    multi: bool = False
    unit: str | None = None
    format: str | None = None
    values: list[str] | None = None
    ref_target: RefTarget | list[RefTarget] | None = None
    derived_from: str | None = None
    companions: list[str] | None = None
    bases: list[Basis] | None = Field(None, description="Measurement bases; the first is the default")

    @model_validator(mode="after")
    def _type_rules(self) -> Attribute:
        fid = self.friendly_id
        if self.handle != fid.replace("_", "-"):
            raise ValueError(f"{fid}: handle must be friendly_id with '_' → '-'")
        if self.type == "enum":
            if not self.values:
                raise ValueError(f"{fid}: enum attribute needs values")
            if self.values[-1] != f"{fid}__other":
                raise ValueError(f"{fid}: last enum value must be {fid}__other")
            for v in self.values:
                if not v.startswith(f"{fid}__"):
                    raise ValueError(f"{fid}: value {v} does not belong to this attribute")
            if len(set(self.values)) != len(self.values):
                raise ValueError(f"{fid}: duplicate values")
        elif self.values is not None:
            raise ValueError(f"{fid}: only enum attributes carry values")
        if self.bases is not None:
            if self.type != "number":
                raise ValueError(f"{fid}: only number attributes carry bases")
            hs = [b.handle for b in self.bases]
            if not hs or len(set(hs)) != len(hs):
                raise ValueError(f"{fid}: bases must be a non-empty list of unique handles")
        if self.type == "number" and not self.unit:
            raise ValueError(f"{fid}: number attribute needs a unit")
        if self.type != "number" and self.unit:
            raise ValueError(f"{fid}: unit only allowed on number attributes")
        if self.type == "ref" and not self.ref_target:
            raise ValueError(f"{fid}: ref attribute needs ref_target")
        if self.type != "ref" and self.ref_target:
            raise ValueError(f"{fid}: ref_target only allowed on ref attributes")
        return self


class Value(Strict):
    id: int = Field(gt=0)
    name: str = Field(min_length=1)
    friendly_id: str = Field(pattern=VALUE_FID_RE.pattern)
    handle: str = Field(min_length=1)

    @property
    def attribute_friendly_id(self) -> str:
        return self.friendly_id.split("__", 1)[0]


class Example(Strict):
    handle: str = Field(pattern=KEBAB_RE.pattern)
    name: str
    expected: str = Field(pattern=CATEGORY_ID_RE.pattern)
    facts: dict[str, object]
    attributes: dict[str, object] = {}


class MappingRule(Strict):
    input: dict[str, str]
    output: dict[str, list[str]]


class MappingFile(Strict):
    input_kind: Literal["category", "attribute_value"] = "category"
    scope: list[Literal["rb", "cp"]] = ["rb", "cp"]
    rules: list[MappingRule]
    unmapped_category_ids: list[str] = []
    unmapped_attribute_values: list[str] = []


class Integration(Strict):
    name: str = Field(pattern=KEBAB_RE.pattern)
    description: str
    source: str
    available_versions: list[str]


# ---------------------------------------------------------------- use cases (docs/design.md §11)
USE_CASE_ID_RE = re.compile(r"^uc-[1-9]\d*$")
ENV_ID_RE = re.compile(r"^env-[a-z0-9][a-z0-9-]*$")

RequirementOp = Literal["has", "in", "eq", ">=", "<=", "ip_solids>=", "ip_liquids>="]
Scalar = str | int | float | bool


class Condition(Strict):
    """One test of one attribute. `value` is a literal; `param` names a use-case parameter whose current value is
    used instead (the test is skipped while that parameter is not set). Exactly one of the two is given.

    Operators: `has` (the attribute's value, or one of its values, is `value` or one of `value`), `in` (the same test,
    written for single-select attributes), `eq`, `>=`, `<=` (numbers, compared on the attribute's default measurement
    basis only), `ip_solids>=` / `ip_liquids>=` (first / second digit of an IEC 60529 code in `ip_rating`)."""
    attribute: str = Field(pattern=SNAKE_RE.pattern)
    op: RequirementOp
    value: Scalar | list[Scalar] | None = None
    param: str | None = Field(default=None, pattern=SNAKE_RE.pattern)

    @model_validator(mode="after")
    def _one_operand(self) -> Condition:
        if (self.value is None) == (self.param is None):
            raise ValueError(f"{self.attribute}: give exactly one of value / param")
        if isinstance(self.value, list) and self.op not in ("has", "in"):
            raise ValueError(f"{self.attribute}: only has / in take a list")
        return self


class Requirement(Condition):
    """A condition a robot must (`hard`) or should (`soft`) meet for the use case. Hard is reserved for physics,
    geometry, law, a cited standard or the definition of the use case itself; a failed hard requirement excludes the
    robot. A soft requirement never excludes: it is shown as something to check. `when` limits the requirement to
    parameter settings (all listed parameters must have the listed value)."""
    level: Literal["hard", "soft"]
    rationale: str = Field(min_length=1)
    source: str | None = None
    when: dict[str, Scalar] | None = None


class Parameter(Strict):
    """Something the reader sets (a load, an area, indoor or outdoor). `default: null` means "not set": requirements
    bound to the parameter are skipped until the reader gives a value."""
    key: str = Field(pattern=SNAKE_RE.pattern)
    name: str = Field(min_length=1)
    type: Literal["number", "enum", "bool"]
    unit: str | None = None
    values: list[str] | None = None
    default: Scalar | None = None
    description: str | None = None

    @model_validator(mode="after")
    def _type_rules(self) -> Parameter:
        if self.type == "number" and not self.unit:
            raise ValueError(f"{self.key}: number parameter needs a unit")
        if self.type == "enum" and not self.values:
            raise ValueError(f"{self.key}: enum parameter needs values")
        if self.type != "enum" and self.values:
            raise ValueError(f"{self.key}: values only on enum parameters")
        if self.default is not None:
            ok = {"number": isinstance(self.default, (int, float)) and not isinstance(self.default, bool), "bool": isinstance(self.default, bool), "enum": self.default in (self.values or [])}[self.type]
            if not ok:
                raise ValueError(f"{self.key}: default {self.default!r} does not fit type {self.type}")
        return self


class BodyPlan(Strict):
    """A robot category that can do the job, with a one-line note on when it is the right kind."""
    category: str = Field(pattern=CATEGORY_ID_RE.pattern)
    note: str = Field(min_length=1)


class Slot(Strict):
    """A role the use case needs filled by a component (or by the robot itself): which component category, and
    which of its attributes decide."""
    role: str = Field(pattern=KEBAB_RE.pattern)
    name: str = Field(min_length=1)
    need: Literal["required", "recommended", "optional"]
    category: str = Field(pattern=CATEGORY_ID_RE.pattern)
    where: list[Condition] = []
    note: str = Field(min_length=1)


class EnvironmentProfile(Strict):
    """A named, reusable bundle of requirements describing where the robot works."""
    id: str = Field(pattern=ENV_ID_RE.pattern)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    requirements: list[Requirement] = Field(min_length=1)


class UseCase(Strict):
    """A job, written as requirements against the taxonomy's attributes. Which robots suit it is computed from
    product data by whoever holds a catalogue; no product is tagged with a use case."""
    id: str = Field(pattern=USE_CASE_ID_RE.pattern, description="Permanent id; numbers are never reused")
    handle: str = Field(pattern=KEBAB_RE.pattern)
    name: str = Field(min_length=1)
    application: str = Field(description="The application value this use case sits under, e.g. application__palletizing")
    aliases: list[str] = []
    solution_type: Literal["turnkey", "platform", "cell"] = Field(
        description="turnkey: the robot is the whole solution; platform: robot + payload + software; cell: robot + tooling + safety + integration"
    )
    description: str = Field(min_length=1)
    what_decides: str = Field(min_length=1, description="What decides the choice, in plain words")
    parameters: list[Parameter] = []
    body_plans: list[BodyPlan] = Field(min_length=1)
    related_applications: list[str] = Field(
        default=[], description="Applications whose robots are plausible platforms for this job although not marketed for it"
    )
    environment: list[str] = []
    requirements: list[Requirement] = []
    slots: list[Slot] = []


L10N_FIELDS = Literal["name", "description", "aliases"]
SOURCE_DESC = (
    "Review record: field -> fingerprint of the English text a native reader reviewed this field against "
    "(whatrobot_taxonomy.l10n.fingerprint). A field not listed is an unreviewed draft; a listed field whose "
    "fingerprint no longer matches the English is stale."
)


class LocalizedCategory(Strict):
    name: str
    description: str | None = None
    aliases: list[str] | None = Field(default=None, description="Search terms in this language; replaces the English aliases in this locale's dist")
    source: dict[L10N_FIELDS, str] | None = Field(default=None, description=SOURCE_DESC)


class LocalizedAttribute(Strict):
    name: str
    description: str | None = None
    source: dict[Literal["name", "description"], str] | None = Field(default=None, description=SOURCE_DESC)


class LocalizedValue(Strict):
    name: str
    source: dict[Literal["name"], str] | None = Field(default=None, description=SOURCE_DESC)
