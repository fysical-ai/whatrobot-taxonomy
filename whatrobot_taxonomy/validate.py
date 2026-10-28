"""Validation rules (docs/design.md §9.8). Returns errors (fail CI) and warnings (reported only)."""
from __future__ import annotations

from dataclasses import dataclass, field

from .classify import Unclassifiable, classify
from .loader import Taxonomy

MAX_DEPTH = 3


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    @property
    def ok(self) -> bool:
        return not self.errors


def validate(tx: Taxonomy) -> Report:
    r = Report()
    _structure(tx, r)
    _attributes_and_values(tx, r)
    _application_groups(tx, r)
    _examples(tx, r)
    _mappings(tx, r)
    _localisation(tx, r)
    return r


# ---------------------------------------------------------------- structure
def _structure(tx: Taxonomy, r: Report) -> None:
    cats = tx.categories
    seen_friendly: dict[str, str] = {}
    for cid, cat in cats.items():
        # positional id matches parent/children
        parent = cat.parent_id
        if parent is not None:
            if parent not in cats:
                r.error(f"{cid}: parent {parent} does not exist")
            elif cid not in cats[parent].children:
                r.error(f"{cid}: not listed in children of {parent}")
        for child in cat.children:
            if child not in cats:
                r.error(f"{cid}: child {child} does not exist")
            elif cats[child].parent_id != cid:
                r.error(f"{cid}: child {child} has a different positional parent")
        if cat.depth > MAX_DEPTH:
            r.error(f"{cid}: depth {cat.depth} exceeds max {MAX_DEPTH}")
        # friendly_id = parent friendly_id + "." + handle
        if parent is None:
            if cat.friendly_id != cat.handle:
                r.error(f"{cid}: root friendly_id must equal handle")
        elif parent in cats and cat.friendly_id != f"{cats[parent].friendly_id}.{cat.handle}":
            r.error(f"{cid}: friendly_id must be {cats[parent].friendly_id}.{cat.handle}")
        if cat.friendly_id in seen_friendly:
            r.error(f"{cid}: friendly_id {cat.friendly_id} duplicates {seen_friendly[cat.friendly_id]}")
        seen_friendly[cat.friendly_id] = cid
        # attributes exist
        for a in cat.attributes:
            if a not in tx.attributes:
                r.error(f"{cid}: attribute {a} does not exist")
        # leaf completeness
        if not cat.children and not cat.examples:
            r.error(f"{cid}: leaf has no examples")
        # handle unique among siblings
    for cid, cat in cats.items():
        handles = [cats[c].handle for c in cat.children if c in cats]
        if len(handles) != len(set(handles)):
            r.error(f"{cid}: duplicate child handles")
    # no cycles: positional ids make cycles impossible if parents resolve; still check reachability
    reachable: set[str] = set()
    stack = [c.id for c in tx.roots()]
    while stack:
        cid = stack.pop()
        if cid in reachable:
            r.error(f"{cid}: reached twice (cycle or duplicate child listing)")
            continue
        reachable.add(cid)
        stack.extend(cats[cid].children if cid in cats else [])
    for cid in cats:
        if cid not in reachable:
            r.error(f"{cid}: unreachable from a root")


# ------------------------------------------------------- attributes & values
def _attributes_and_values(tx: Taxonomy, r: Report) -> None:
    ids = [a.id for a in tx.attributes.values()]
    if len(ids) != len(set(ids)):
        r.error("duplicate attribute ids")
    vids = [v.id for v in tx.values.values()]
    if len(vids) != len(set(vids)):
        r.error("duplicate value ids")
    # every enum value referenced exists; every value belongs to exactly one attribute
    referenced: dict[str, str] = {}
    for a in tx.attributes.values():
        for v in a.values or []:
            if v not in tx.values:
                r.error(f"{a.friendly_id}: value {v} missing from values.yml")
            if v in referenced:
                r.error(f"value {v} referenced by both {referenced[v]} and {a.friendly_id}")
            referenced[v] = a.friendly_id
        for c in a.companions or []:
            if c not in tx.attributes:
                r.error(f"{a.friendly_id}: companion {c} does not exist")
        if a.derived_from and a.derived_from not in tx.attributes:
            r.error(f"{a.friendly_id}: derived_from {a.derived_from} does not exist")
    for v in tx.values.values():
        if v.attribute_friendly_id not in tx.attributes:
            r.error(f"value {v.friendly_id}: attribute {v.attribute_friendly_id} does not exist")
        elif v.friendly_id not in referenced:
            r.error(f"value {v.friendly_id}: not listed by its attribute")
    # every attribute bound somewhere
    bound = {a for c in tx.categories.values() for a in c.attributes}
    for a in tx.attributes.values():
        if a.friendly_id not in bound and not a.derived_from and a.friendly_id not in _companion_set(tx):
            r.warn(f"{a.friendly_id}: attribute bound to no category")


def _companion_set(tx: Taxonomy) -> set[str]:
    return {c for a in tx.attributes.values() for c in (a.companions or [])}


def _application_groups(tx: Taxonomy, r: Report) -> None:
    app = tx.attributes.get("application")
    grp = tx.attributes.get("application_group")
    if not app or not grp:
        r.error("application / application_group attributes missing")
        return
    seen: dict[str, str] = {}
    for g, apps in tx.application_groups.items():
        if g not in (grp.values or []):
            r.error(f"application_groups: group {g} is not a value of application_group")
        for a in apps:
            if a not in (app.values or []):
                r.error(f"application_groups: {a} is not a value of application")
            if a in seen:
                r.error(f"application_groups: {a} in both {seen[a]} and {g}")
            seen[a] = g
    for a in app.values or []:
        if a not in seen:
            r.error(f"application_groups: {a} has no group")


# --------------------------------------------------------------- examples
def _examples(tx: Taxonomy, r: Report) -> None:
    for ex in tx.examples:
        if ex.expected not in tx.categories:
            r.error(f"example {ex.handle}: expected category {ex.expected} does not exist")
            continue
        try:
            got = classify(ex.facts)
        except Unclassifiable as e:
            r.error(f"example {ex.handle}: unclassifiable ({e})")
            continue
        if got != ex.expected:
            r.error(f"example {ex.handle}: classified as {got}, expected {ex.expected}")
        eff = set(tx.effective_attributes(ex.expected))
        for k, v in ex.attributes.items():
            if k not in tx.attributes:
                r.error(f"example {ex.handle}: unknown attribute {k}")
                continue
            if k not in eff:
                r.error(f"example {ex.handle}: attribute {k} is not bound on {ex.expected}")
            attr = tx.attributes[k]
            if attr.type == "enum":
                vals = v if isinstance(v, list) else [v]
                if len(vals) > 1 and not attr.multi:
                    r.error(f"example {ex.handle}: {k} is single-select")
                for val in vals:
                    if f"{k}__{val}" not in tx.values:
                        r.error(f"example {ex.handle}: {k}={val} is not a known value")
    # every category example handle that is in examples.yml must classify there
    ex_by_handle = {e.handle: e for e in tx.examples}
    for cat in tx.categories.values():
        for h in cat.examples:
            if h in ex_by_handle and ex_by_handle[h].expected != cat.id:
                r.error(f"{cat.id}: lists example {h} but examples.yml expects {ex_by_handle[h].expected}")
            elif h not in ex_by_handle:
                r.warn(f"{cat.id}: example {h} has no entry in examples.yml")


# --------------------------------------------------------------- mappings
def _mappings(tx: Taxonomy, r: Report) -> None:
    all_cats = set(tx.categories)
    for m in tx.mappings:
        label = f"{m.integration}/{m.version}/{m.direction}"
        mf = m.file
        if m.direction == "from_whatrobot":
            if mf.input_kind == "category":
                mapped = {rule.input.get("category_id") for rule in mf.rules}
                for cid in mapped:
                    if cid not in all_cats:
                        r.error(f"{label}: rule input {cid} is not a category")
                for cid in mf.unmapped_category_ids:
                    if cid not in all_cats:
                        r.error(f"{label}: unmapped {cid} is not a category")
                    if cid in mapped:
                        r.error(f"{label}: {cid} both mapped and unmapped")
                in_scope = {c for c in all_cats if tx.categories[c].root in mf.scope}
                missing = in_scope - mapped - set(mf.unmapped_category_ids)
                if missing:
                    r.error(f"{label}: categories neither mapped nor unmapped: {sorted(missing)}")
            else:
                mapped_vals = {rule.input.get("attribute_value") for rule in mf.rules}
                if None in mapped_vals:
                    r.error(f"{label}: a rule is missing input.attribute_value")
                    mapped_vals.discard(None)
                attr_fid = next(iter(mapped_vals)).split("__")[0] if mapped_vals else None
                attr = tx.attributes.get(attr_fid or "")
                if not attr:
                    r.error(f"{label}: cannot resolve attribute for values {sorted(mapped_vals)}")
                    continue
                all_vals = set(attr.values or [])
                for v in mapped_vals | set(mf.unmapped_attribute_values):
                    if v not in all_vals:
                        r.error(f"{label}: {v} is not a value of {attr_fid}")
                missing = all_vals - mapped_vals - set(mf.unmapped_attribute_values)
                if missing:
                    r.error(f"{label}: values neither mapped nor unmapped: {sorted(missing)}")
            for rule in mf.rules:
                for out in rule.output.get("category_id", []):
                    if m.full_names and out not in m.full_names:
                        r.warn(f"{label}: output {out} has no full_name")
        else:  # to_whatrobot
            for rule in mf.rules:
                for out in rule.output.get("category_id", []):
                    if out not in all_cats:
                        r.error(f"{label}: output {out} is not a category")


# ------------------------------------------------------------ localisation
def _localisation(tx: Taxonomy, r: Report) -> None:
    for code, loc in tx.locales.items():
        for cid in tx.categories:
            if cid not in loc.categories:
                r.warn(f"{code}: category {cid} not localised")
        for cid in loc.categories:
            if cid not in tx.categories:
                r.error(f"{code}: localised category {cid} does not exist")
        for fid in tx.attributes:
            if fid not in loc.attributes:
                r.warn(f"{code}: attribute {fid} not localised")
        for fid in loc.attributes:
            if fid not in tx.attributes:
                r.error(f"{code}: localised attribute {fid} does not exist")
        for fid in tx.values:
            if fid not in loc.values:
                r.warn(f"{code}: value {fid} not localised")
        for fid in loc.values:
            if fid not in tx.values:
                r.error(f"{code}: localised value {fid} does not exist")
