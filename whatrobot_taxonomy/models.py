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


class LocalizedCategory(Strict):
    name: str
    description: str | None = None


class LocalizedAttribute(Strict):
    name: str
    description: str | None = None


class LocalizedValue(Strict):
    name: str
