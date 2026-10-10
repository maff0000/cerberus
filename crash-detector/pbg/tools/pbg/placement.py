"""Canonical placement of security-relevant authority fields (Placement Question A).

THE FINDING, MEASURED. `excluded_executors` at top level was read; the same field nested under
`separation_of_duties` read as None; and NOTHING REPORTED that a field of that name in that position
had been ignored. A non-waivable control silently degraded to documentation, which is what happened
to AUTH-0011.

Two things had to be true at once and were not:

    a field's POSITION must not decide whether it is enforced
    a record that a governed history already contains must not become unwritable

This module gets both by declaring the permitted positions as DATA
(`tools/pbg/data/authority-field-placement.yaml`) and enforcing three outcomes over them:

    resolve_field()      returns the value the framework will ACT on, combined FAIL-CLOSED across
                         every permitted position, plus findings naming where it came from
    placement_errors()   returns the reasons a record is INVALID: a security-relevant field in an
                         UNDECLARED position, or two declared positions that disagree

The registry ships INSIDE the package, beside the code that reads it. A consuming project vendors the
framework at `pbg/`, so the data travels with the module; there is no host path here and no
project-supplied override, because a project that could redeclare where a security field lives could
move it somewhere the framework does not look.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

#: INSIDE the package, beside the code that reads it.
#:
#: It lived in `schemas/` first, which is one directory outside `tools/pbg/` — and a deployment that
#: vendors the package without that directory then had the code and not its data. The framework's
#: own hook fixture is exactly that shape, and the result was a validator that could not establish
#: placement and therefore refused EVERY authority commit, valid records included: the A-3 failure
#: reproduced one layer down. Data that a control cannot run without travels with the control.
REGISTRY_RELATIVE = ("data", "authority-field-placement.yaml")

TOP_LEVEL = "top_level"

#: Stable prefixes, so a caller can tell a REPORT from a REASON THE RECORD IS INVALID without
#: matching on prose. A note accompanies a result; a divergence invalidates it.
NOTE = "placement: "
DIVERGENCE = "placement divergence: "


class PlacementRegistryMissing(RuntimeError):
    """The registry is part of the shipped package. Its absence is a refusal, not a default."""


def registry_path() -> Path:
    return Path(__file__).resolve().parent.joinpath(*REGISTRY_RELATIVE)


@lru_cache(maxsize=1)
def _registry_cached(path: str, mtime: float) -> dict:
    doc = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return doc.get("fields") or {}


def registry() -> dict:
    """The declared placement rules. Missing or unreadable is a refusal — never an empty default.

    An empty default would mean "no field is security-relevant", which is the most permissive
    possible answer to a question about enforcement.
    """
    path = registry_path()
    try:
        return _registry_cached(str(path), path.stat().st_mtime)
    except OSError as exc:
        raise PlacementRegistryMissing(
            f"the field-placement registry {path} cannot be read ({exc}); placement of "
            "security-relevant fields cannot be established and must not be assumed") from exc
    except yaml.YAMLError as exc:
        raise PlacementRegistryMissing(
            f"the field-placement registry {path} is not valid YAML: {exc}") from exc


SECURITY_RELEVANT_FIELDS = None       # populated lazily; see `field_names()`


def field_names() -> tuple:
    return tuple(sorted(registry()))


def _at(doc: dict, dotted: str):
    """The value at a dotted path, or a sentinel when the path does not exist."""
    node = doc
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return _MISSING
        node = node[part]
    return node


class _Missing:
    def __repr__(self):                                    # pragma: no cover - debugging aid
        return "<missing>"


_MISSING = _Missing()


def _occurrences(node, name: str, path: tuple = ()) -> list[tuple[str, object]]:
    """Every position in the document where `name` appears as a key, however deeply nested."""
    found: list[tuple[str, object]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            here = path + (str(key),)
            if str(key) == name:
                found.append((".".join(here), value))
            found.extend(_occurrences(value, name, here))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            found.extend(_occurrences(value, name, path + (f"[{index}]",)))
    return found


def _truthy(value) -> bool:
    if isinstance(value, (list, tuple, set, dict, str)):
        return bool(value)
    return value is not None and value is not False


def _combine(rule: str, values: list):
    """Fail closed across positions: the widest prohibition, or any demand at all."""
    if rule == "union":
        merged: list = []
        for value in values:
            for item in (value or []):
                if item not in merged:
                    merged.append(item)
        return merged
    if rule == "any_truthy":
        for value in values:
            if _truthy(value):
                return value
        return None
    return values[0] if values else None                   # pragma: no cover - registry-driven


def resolve_field(doc: dict, name: str) -> tuple[object, list[str]]:
    """The value the framework will ACT on for `name`, and everything worth saying about where it is.

    Combined fail-closed across every DECLARED position, so a nested copy enforces exactly as hard
    as a canonical one. Positions that are not declared are not combined here — they are validation
    errors, produced by `placement_errors`, because a security-relevant field the framework cannot
    place is a field it must not silently act on either.
    """
    rule = registry().get(name)
    if rule is None:                                       # not a governed field; plain read
        return doc.get(name), []

    findings: list[str] = []
    positions: list[tuple[str, object]] = []

    canonical = doc.get(name, _MISSING)
    if not isinstance(canonical, _Missing):
        positions.append((TOP_LEVEL, canonical))

    for alias in rule.get("accepted_alias_paths") or []:
        value = _at(doc, f"{alias}.{name}")
        if not isinstance(value, _Missing):
            positions.append((f"{alias}.{name}", value))

    if not positions:
        return None, findings

    if len(positions) == 1 and positions[0][0] != TOP_LEVEL:
        findings.append(
            f"{NOTE}{name} is declared at {positions[0][0]} rather than at the canonical top "
            "level. It is read and ENFORCED there — a declared alias position is not an inert one "
            "— and the placement is reported so it cannot pass unnoticed")
    elif len(positions) > 1:
        rendered = ", ".join(f"{where}={value!r}" for where, value in positions)
        distinct = {repr(value) for _, value in positions}
        if len(distinct) == 1:
            findings.append(
                f"{NOTE}{name} appears at {len(positions)} declared positions with the same value "
                f"({rendered}); enforced once, and the duplication is reported rather than reduced "
                "silently to whichever was read first")
        else:
            findings.append(
                f"{DIVERGENCE}{name} appears at {len(positions)} declared positions with DIFFERENT "
                f"values ({rendered}). Combined fail-closed, and the record is INVALID: placement "
                "must never be able to change enforcement")

    return _combine(str(rule.get("fail_closed_combination") or ""),
                    [value for _, value in positions]), findings


def placement_errors(doc: dict) -> list[str]:
    """Every reason this record's field placement makes it INVALID.

    Two, and only two, because they are the two ways placement can change enforcement:

        an UNDECLARED position   the framework does not look there, so the field would be inert
        DECLARED positions that DISAGREE   the answer would depend on which one a reader found

    A field sitting at a declared alias is neither: it is enforced identically and merely reported.
    """
    errors: list[str] = []
    try:
        rules = registry()
    except PlacementRegistryMissing as exc:
        return [str(exc)]

    for name, rule in sorted(rules.items()):
        permitted = {TOP_LEVEL} | {f"{alias}.{name}"
                                   for alias in (rule.get("accepted_alias_paths") or [])}
        for where, value in _occurrences(doc, name):
            position = TOP_LEVEL if where == name else where
            if position in permitted:
                continue
            errors.append(
                f"security-relevant field {name!r} appears at {where!r}, which is not a declared "
                f"position for it (declared: {', '.join(sorted(permitted))}). A field the framework "
                "does not read is a control that silently became documentation — the defect "
                "Placement Question A named. Move it, or declare the position in "
                f"{registry_path().name} beside the package.")

        _, findings = resolve_field(doc, name)
        errors += [f for f in findings if f.startswith(DIVERGENCE)]
    return errors
