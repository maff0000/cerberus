#!/usr/bin/env python3
"""CD-RT-002-SCHEMA-CLOSED — the published envelope has no place for a third number.

    python3 tools/register/check_schema_closed.py --root <subject tree>

CRITERION: CD-AC-002 (BLUEPRINT §13: "public envelope schema closed to a combined field"),
with CD-AC-001 and CD-AC-006 riding on the same closure.

This is the third of CD-AC-002's three independent refusals. The type system refuses
``equity + monetary``; the AST no-blend check refuses the expression that reaches for the
two ``.score`` floats; and this refuses the *document*. A blend that got past both other
instruments still has to be published, and a closed schema with an allowlist of properties
has nowhere to put it.

WHAT IS ASSERTED — SEVEN INDEPENDENT PROPOSITIONS, all structural, all stdlib
-----------------------------------------------------------------------------
 1  CLOSED AT EVERY LEVEL. Every object-shaped schema node — the root, every entry in
    ``properties``, every ``$defs`` member, every branch of a ``oneOf``/``anyOf``/``allOf``,
    every ``items`` — declares ``"additionalProperties": false``. Not ``true``, and not a
    schema object: ``additionalProperties: {"type": "number"}`` is an *open* schema that
    admits any number under any name, which is the exact defect wearing a type constraint.
 2  NO ESCAPE HATCH. No ``patternProperties``, and no ``unevaluatedProperties`` that is
    anything other than ``false``. Either one re-opens a closed document.
 3  PROPERTIES ARE AN ALLOWLIST, AND IT IS THE DECLARED ONE. The root ``properties`` keys
    equal the set declared below, exactly. Adding ``combined_stress`` — or ``overall``, or
    any key at all — fails here whatever it is called, because the assertion is set
    equality and not a search for a name somebody guessed.
 4  REQUIRED MATCHES THE ALLOWLIST. Every declared property is required, so a consumer
    never has to tell "absent" from "omitted".
 5  NO THIRD TOP-LEVEL NUMBER. Exactly one root property is scalar-numeric
    (``staleness_window_seconds``, which is a window and not a reading). This holds even
    if proposition 3 were edited: a blended headline has to be a number somewhere, and
    this counts the numbers.
 6  UNKNOWN CARRIES NO SCORE. The ``dial_reading_unknown`` branch declares no ``score``
    property at all, so an UNKNOWN dial carrying a number is unrepresentable rather than
    merely discouraged. That is CD-AC-001 held in the schema.
 7  NOTHING IS FETCHED. ``$id`` is a ``urn:`` and every ``$ref`` is a local ``#`` fragment,
    so no validator can be induced to resolve a remote schema (Standards Baseline §4).

WHY THIS CHECK IS STRUCTURAL AND NOT A VALIDATOR RUN. A behavioural probe — build an
envelope, add a key, watch a validator reject it — needs ``jsonschema``, which is a
declared dependency of the application but not of this stdlib-only register. The
behavioural half is covered, and covered properly, by
``tests/test_envelope_contracts.py`` and ``tests/test_publication_refusal.py``; this
check's job is the structure, which is where a plant would be applied and where a
behavioural probe is weakest — a probe only rejects the keys the prober thought of, while
proposition 1 rejects every key at every level by construction.

EXIT: 0 clean · 1 violation, each with the JSON pointer and the line · 2 usage · 3
precondition not met. Never a skip, for any reason (PBG-CI-002).
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _support import Check, parse_root, read_text, resolve_root  # noqa: E402

CHECK_ID = "CD-RT-002-SCHEMA-CLOSED"

#: The PUBLIC envelope's complete property allowlist (BLUEPRINT §8, the honesty fields).
#: Widening this list is a deliberate schema edit with a ``schema_version`` bump, and it
#: must be made HERE as well — which is exactly the friction intended. There is no entry
#: for a combined, overall or blended number, and there is no room for one.
PUBLIC_ALLOWLIST = frozenset(
    {
        "schema_version",
        "as_of_utc",
        "published_utc",
        "regime",
        "staleness_window_seconds",
        "inputs_used",
        "degraded_inputs",
        "config_snapshot_id",
        "equity_crash",
        "monetary_debasement",
    }
)

#: The PRIVATE envelope carries the same fields plus its classification marker.
PRIVATE_ALLOWLIST = frozenset(PUBLIC_ALLOWLIST | {"classification"})

#: The only root property that may be a scalar number. A window is not a reading.
NUMERIC_ROOT_PROPERTIES = frozenset({"staleness_window_seconds"})

#: Keywords whose value is a subschema, or a list/map of subschemas.
SUBSCHEMA_KEYS = ("items", "contains", "not", "propertyNames", "if", "then", "else")
SUBSCHEMA_LISTS = ("oneOf", "anyOf", "allOf", "prefixItems")
SUBSCHEMA_MAPS = ("properties", "$defs", "definitions", "patternProperties")


def _line_index(text: str) -> list:
    return [len(line) + 1 for line in text.splitlines()]


def _find_line(text: str, pointer_tail: str) -> int:
    """Best-effort line for a JSON key, so the finding says WHERE and not only WHAT."""
    if not pointer_tail:
        return 1
    pattern = re.compile(r'^\s*"' + re.escape(pointer_tail) + r'"\s*:', re.MULTILINE)
    match = pattern.search(text)
    if match:
        return text.count("\n", 0, match.start()) + 1
    return 1


class SchemaWalker:
    def __init__(self, check: Check, path: pathlib.Path, text: str) -> None:
        self.check = check
        self.path = path
        self.text = text

    def report(self, pointer: str, tail: str, rule: str, what: str) -> None:
        self.check.violation(
            self.path, _find_line(self.text, tail), rule, f"at {pointer or '#'} — {what}"
        )

    def walk(self, node, pointer: str = "", tail: str = "") -> None:
        if not isinstance(node, dict):
            return

        looks_like_object = "properties" in node or node.get("type") == "object"
        if looks_like_object:
            self.check.asserted()
            closed = node.get("additionalProperties", "ABSENT")
            if closed is not False:
                rendered = (
                    "absent" if closed == "ABSENT" else json.dumps(closed)[:80]
                )
                self.report(
                    pointer,
                    tail,
                    "1: object schema is not closed",
                    f'"additionalProperties" is {rendered}, not false. An open object '
                    "admits a key nobody declared — including a blended headline number "
                    "under any name at all. A SCHEMA value here is not a closure either: "
                    'additionalProperties: {"type": "number"} admits every number.',
                )

        self.check.asserted()
        if "patternProperties" in node:
            self.report(
                pointer,
                "patternProperties",
                "2: escape hatch",
                '"patternProperties" re-opens a closed object to every key matching the '
                "pattern. A closed document has no patterns.",
            )
        if "unevaluatedProperties" in node and node["unevaluatedProperties"] is not False:
            self.report(
                pointer,
                "unevaluatedProperties",
                "2: escape hatch",
                '"unevaluatedProperties" is not false, which re-opens what '
                "additionalProperties closed.",
            )

        self.check.asserted()
        for key, value in node.items():
            if key == "$ref" and isinstance(value, str) and not value.startswith("#"):
                self.report(
                    pointer,
                    "$ref",
                    "7: remote reference",
                    f'"$ref": "{value}" is not a local # fragment. A validator that can '
                    "be induced to fetch a schema is a validator an attacker can point "
                    "somewhere else.",
                )
            if key == "$id" and isinstance(value, str) and not value.startswith("urn:"):
                self.report(
                    pointer,
                    "$id",
                    "7: dereferenceable $id",
                    f'"$id": "{value}" is not a urn. A urn cannot be dereferenced; a URL '
                    "can.",
                )

        for key in SUBSCHEMA_MAPS:
            child = node.get(key)
            if isinstance(child, dict):
                for name, sub in child.items():
                    self.walk(sub, f"{pointer}/{key}/{name}", name)
        for key in SUBSCHEMA_LISTS:
            child = node.get(key)
            if isinstance(child, list):
                for index, sub in enumerate(child):
                    self.walk(sub, f"{pointer}/{key}/{index}", tail)
        for key in SUBSCHEMA_KEYS:
            child = node.get(key)
            if isinstance(child, dict):
                self.walk(child, f"{pointer}/{key}", key)
            elif isinstance(child, list):
                for index, sub in enumerate(child):
                    self.walk(sub, f"{pointer}/{key}/{index}", tail)


def _check_schema(
    check: Check, path: pathlib.Path, allowlist: frozenset, label: str
) -> None:
    text = read_text(check, path)
    if text is None:
        return
    try:
        schema = json.loads(text)
    except json.JSONDecodeError as exc:
        check.violation(
            path,
            exc.lineno,
            "UNPARSEABLE",
            f"the {label} envelope schema is not valid JSON ({exc.msg}). A contract the "
            "check cannot read is a contract nothing is validated against.",
        )
        return
    if not isinstance(schema, dict):
        check.violation(path, 1, "MALFORMED", "the schema document is not an object.")
        return

    SchemaWalker(check, path, text).walk(schema)

    # -- 3: the root property allowlist, exactly ------------------------------------- #
    check.asserted()
    declared = set(schema.get("properties", {}))
    if declared != set(allowlist):
        added = sorted(declared - set(allowlist))
        removed = sorted(set(allowlist) - declared)
        detail = []
        if added:
            detail.append(f"UNDECLARED KEYS PRESENT: {', '.join(added)}")
        if removed:
            detail.append(f"DECLARED KEYS MISSING: {', '.join(removed)}")
        check.violation(
            path,
            _find_line(text, added[0] if added else "properties"),
            "3: the root properties are not the declared allowlist",
            f"the {label} envelope's root properties differ from the allowlist this "
            "register declares. " + "; ".join(detail) + ". A new top-level key is a "
            "deliberate contract change: it needs a schema_version bump and an edit here, "
            "which is the friction that stops a headline number arriving quietly.",
        )

    # -- 4: everything declared is required ------------------------------------------ #
    check.asserted()
    required = set(schema.get("required", []))
    if required != set(allowlist):
        check.violation(
            path,
            _find_line(text, "required"),
            "4: required does not match the allowlist",
            f"required={sorted(required)} but the allowlist is {sorted(allowlist)}. A "
            "consumer must never have to tell 'this dial is absent' from 'this field was "
            "omitted'.",
        )

    # -- 5: exactly one scalar-numeric root property --------------------------------- #
    check.asserted()
    numeric_roots = {
        name
        for name, sub in schema.get("properties", {}).items()
        if isinstance(sub, dict) and sub.get("type") in ("number", "integer")
    }
    if numeric_roots != set(NUMERIC_ROOT_PROPERTIES):
        extra = sorted(numeric_roots - set(NUMERIC_ROOT_PROPERTIES))
        check.violation(
            path,
            _find_line(text, extra[0] if extra else "properties"),
            "5: a third top-level number",
            f"the {label} envelope declares scalar-numeric root properties "
            f"{sorted(numeric_roots)}; the only one permitted is "
            f"{sorted(NUMERIC_ROOT_PROPERTIES)} (a staleness window, not a reading). A "
            "blended headline has to be a number somewhere, and this counts the numbers "
            "whatever they are called.",
        )

    # -- 6: UNKNOWN declares no score ------------------------------------------------- #
    check.asserted()
    unknown = schema.get("$defs", {}).get("dial_reading_unknown")
    if not isinstance(unknown, dict):
        check.violation(
            path,
            _find_line(text, "$defs"),
            "6: the UNKNOWN branch is missing",
            f"the {label} envelope declares no $defs/dial_reading_unknown. Without it "
            "there is no branch in which an unknown dial is representable without a "
            "number, which is CD-AC-001's whole subject.",
        )
    else:
        unknown_properties = set(unknown.get("properties", {}))
        if "score" in unknown_properties or "score" in set(unknown.get("required", [])):
            check.violation(
                path,
                _find_line(text, "dial_reading_unknown"),
                "6: UNKNOWN carries a score",
                "the UNKNOWN branch declares a `score` property. An unknown dial must "
                "have nowhere to put a number, not merely be discouraged from putting "
                "one there (CD-AC-001).",
            )


def main() -> int:
    args = parse_root(CHECK_ID, __doc__)
    root, code = resolve_root(CHECK_ID, args.root)
    if root is None:
        return code

    check = Check(CHECK_ID, root)

    subjects = (
        (root / "contracts/public_envelope.schema.json", PUBLIC_ALLOWLIST, "public"),
        (root / "contracts/private_envelope.schema.json", PRIVATE_ALLOWLIST, "private"),
    )
    missing = [str(path) for path, _, _ in subjects if not path.is_file()]
    if missing:
        return check.refuse(
            "an envelope contract is missing from the subject tree: "
            + ", ".join(missing)
            + ". A schema that is absent cannot be closed, and its absence must not read "
            "as a pass."
        )

    for path, allowlist, label in subjects:
        _check_schema(check, path, allowlist, label)

    return check.done("contracts/public_envelope.schema.json and private_envelope.schema.json")


if __name__ == "__main__":
    raise SystemExit(main())
