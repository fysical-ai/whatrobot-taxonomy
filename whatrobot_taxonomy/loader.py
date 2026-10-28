"""Load data/ into typed records. YAML is read with ruamel.yaml so comments survive round-trips in dev tools."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ruamel.yaml import YAML

from . import DATA
from .models import (
    Attribute,
    Category,
    Example,
    Integration,
    LocalizedAttribute,
    LocalizedCategory,
    LocalizedValue,
    MappingFile,
    Value,
)

_yaml = YAML(typ="safe")

SOURCE_LOCALE = "en"


def read_yaml(path: Path):
    with path.open(encoding="utf-8") as fh:
        return _yaml.load(fh)


@dataclass
class Locale:
    code: str
    categories: dict[str, LocalizedCategory] = field(default_factory=dict)
    attributes: dict[str, LocalizedAttribute] = field(default_factory=dict)
    values: dict[str, LocalizedValue] = field(default_factory=dict)


@dataclass
class Mapping:
    integration: str
    version: str
    direction: str  # from_whatrobot | to_whatrobot
    file: MappingFile
    full_names: dict[str, str]


@dataclass
class Taxonomy:
    categories: dict[str, Category]
    attributes: dict[str, Attribute]  # by friendly_id
    values: dict[str, Value]  # by friendly_id
    application_groups: dict[str, list[str]]
    examples: list[Example]
    integrations: list[Integration]
    mappings: list[Mapping]
    locales: dict[str, Locale]
    data_dir: Path

    # ---- convenience -------------------------------------------------
    def children_of(self, cid: str) -> list[Category]:
        return [self.categories[c] for c in self.categories[cid].children]

    def ancestors(self, cid: str) -> list[Category]:
        out: list[Category] = []
        parent = self.categories[cid].parent_id
        while parent:
            out.append(self.categories[parent])
            parent = self.categories[parent].parent_id
        return out

    def effective_attributes(self, cid: str) -> list[str]:
        """Own attributes plus every ancestor's, root first, deduplicated in order."""
        chain = list(reversed(self.ancestors(cid))) + [self.categories[cid]]
        seen: list[str] = []
        for node in chain:
            for a in node.attributes:
                if a not in seen:
                    seen.append(a)
        return seen

    def full_name(self, cid: str, locale: str = SOURCE_LOCALE) -> str:
        chain = list(reversed(self.ancestors(cid))) + [self.categories[cid]]
        return " > ".join(self.localized_name(c.id, locale) for c in chain)

    def localized_name(self, cid: str, locale: str) -> str:
        if locale == SOURCE_LOCALE:
            return self.categories[cid].name
        loc = self.locales.get(locale)
        if loc and cid in loc.categories:
            return loc.categories[cid].name
        return self.categories[cid].name

    ROOT_ORDER = ("rb", "cp")

    def roots(self) -> list[Category]:
        roots = [c for c in self.categories.values() if c.parent_id is None]
        return sorted(roots, key=lambda c: self.ROOT_ORDER.index(c.id) if c.id in self.ROOT_ORDER else 99)

    def leaves(self) -> list[Category]:
        return [c for c in self.categories.values() if not c.children]


def load(data_dir: Path = DATA) -> Taxonomy:
    categories: dict[str, Category] = {}
    for f in sorted((data_dir / "categories").glob("*.yml")):
        for rec in read_yaml(f) or []:
            cat = Category.model_validate(rec)
            if cat.id in categories:
                raise ValueError(f"duplicate category id {cat.id} in {f.name}")
            categories[cat.id] = cat

    attributes: dict[str, Attribute] = {}
    for rec in read_yaml(data_dir / "attributes.yml") or []:
        attr = Attribute.model_validate(rec)
        if attr.friendly_id in attributes:
            raise ValueError(f"duplicate attribute {attr.friendly_id}")
        attributes[attr.friendly_id] = attr

    values: dict[str, Value] = {}
    for rec in read_yaml(data_dir / "values.yml") or []:
        val = Value.model_validate(rec)
        if val.friendly_id in values:
            raise ValueError(f"duplicate value {val.friendly_id}")
        values[val.friendly_id] = val

    application_groups = read_yaml(data_dir / "application_groups.yml") or {}
    examples = [Example.model_validate(r) for r in read_yaml(data_dir / "examples.yml") or []]

    integrations = [Integration.model_validate(r) for r in read_yaml(data_dir / "integrations/integrations.yml") or []]
    mappings: list[Mapping] = []
    for integ in integrations:
        for version in integ.available_versions:
            vdir = data_dir / "integrations" / integ.name / version
            names_file = vdir / "full_names.yml"
            full_names = {str(r["id"]): r["full_name"] for r in (read_yaml(names_file) or [])} if names_file.exists() else {}
            for direction in ("from_whatrobot", "to_whatrobot"):
                mf = vdir / "mappings" / f"{direction}.yml"
                if mf.exists():
                    mappings.append(Mapping(integ.name, version, direction, MappingFile.model_validate(read_yaml(mf)), full_names))

    locales: dict[str, Locale] = {}
    loc_root = data_dir / "localizations"
    if loc_root.exists():
        for ldir in sorted(p for p in loc_root.iterdir() if p.is_dir() and p.name != SOURCE_LOCALE):
            loc = Locale(ldir.name)
            if (ldir / "categories.yml").exists():
                loc.categories = {k: LocalizedCategory.model_validate(v) for k, v in (read_yaml(ldir / "categories.yml") or {}).items()}
            if (ldir / "attributes.yml").exists():
                loc.attributes = {k: LocalizedAttribute.model_validate(v) for k, v in (read_yaml(ldir / "attributes.yml") or {}).items()}
            if (ldir / "values.yml").exists():
                loc.values = {k: LocalizedValue.model_validate(v) for k, v in (read_yaml(ldir / "values.yml") or {}).items()}
            locales[ldir.name] = loc

    return Taxonomy(categories, attributes, values, application_groups, examples, integrations, mappings, locales, data_dir)
