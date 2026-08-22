"""PROBE A — IS THE STORED PAYLOAD THE VALIDATED PAYLOAD?  (ESCAPE 1, SUPPLEMENT §2.1)

Run from the ROOT of a tree:  ``python3 -B variants/WO-2R3/P-A-escape1-stored-is-not-validated.py``

**THIS PROBE PRINTS DATA AND NEVER A VERDICT.** It has no pass/fail, it exits 0 whatever it
observes, and it must be read by its DATA lines. That is deliberate: `CD-ASR-WO2R3-01`'s
finding F-C1 records four probes in this project that PRINT A VERDICT THEY DID NOT EARN, and
a probe whose headline can be believed without reading its rows is the same defect one
generation on.

WHAT IT MEASURES.  `crash_detector.collectors.runner._attempt` runs, in order:

    validator.validate(<the payload>, adapter.response_schema)   # judgement
    adapter.is_empty(<a payload>)                                # DECLARED-FOREIGN CODE
    OK(payload=<a payload>, ...)                                 # storage

Every arm below supplies a HOSTILE ADAPTER whose `is_empty` mutates the object it is handed
and then honestly answers `False`. The question the probe asks is the only one that matters:
**is the object that ends up on `OK.payload` the object the validator judged?**

THE FIVE ARMS, AND WHY FIVE.  Arm 1 is the control. Arm 2 is the auditor's reproduction.
Arms 3, 4 and 5 vary the ONE axis the fix's reach is declared against — HOW DEEP AND OF WHAT
EXACT TYPE the mutated container is:

  1 none                 `is_empty` mutates nothing.
  2 toplevel             `is_empty` rewrites keys of the payload mapping itself.
  3 nested-exact-dict    `is_empty` rewrites a key of a plain `dict` nested inside it.
  4 nested-dict-subclass `is_empty` rewrites a key of a `dict` SUBCLASS nested inside it.
  5 beyond-depth-cap     `is_empty` rewrites a key nested deeper than any bounded snapshot
                         this project is willing to take.

**ARMS 4 AND 5 ARE EXPECTED TO REMAIN OPEN AFTER THE FIX AND ARE PRINTED ANYWAY.** They are
the executable examples behind the fix's DECLARED LIMIT (CD-RULE-004). A probe that prints
only what its author closed is an advertisement, not evidence.

WHAT THIS PROBE DOES NOT REACH, SO IT IS NOT READ WIDER THAN IT IS:

* It attacks the **adapter**. A hostile **validator** — which is also declared-foreign under
  CD-BP-003 — is handed the live payload BEFORE any snapshot can exist, and no arm here
  attacks that route. The recording validator below only reads.
* It exercises `_attempt`, not `collect`. The sink and the ledger are not in this picture.
* It says nothing about whether a mutated payload could reach a dial. That is CD-AC-002 and
  it is an auditor's question, not this probe's.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from crash_detector.collectors.adapter import FetchedResponse  # noqa: E402
from crash_detector.collectors.runner import RetryPolicy, _attempt  # noqa: E402
from crash_detector.collectors.validation import (  # noqa: E402
    JsonSchemaValidator,
    SchemaRejection,
)
from crash_detector.observations import OK  # noqa: E402

#: Deeper than any snapshot depth this project declares, so arm 5 is beyond ANY bounded
#: rebuild rather than beyond one particular constant.
_DEEP = 200


class _Sub(dict):
    """A `dict` SUBCLASS. Exactly a mapping to `jsonschema`; not exactly a `dict` to Python."""


#: Renderings are truncated so arm 5's two-hundred-deep nest does not bury the other four.
#: The COMPARISON is always made on the FULL rendering; only the printing is shortened.
_RENDER_CEILING = 220


def _render(value: object) -> str:
    """A stable, non-executing rendering, so two payload states can be COMPARED as text."""
    return json.dumps(value, default=lambda item: f"<{type(item).__name__}>", sort_keys=True)


def _shown(rendered: str) -> str:
    if len(rendered) <= _RENDER_CEILING:
        return rendered
    return f"{rendered[:_RENDER_CEILING]}… [{len(rendered)} chars, truncated for printing]"


def _fresh_payload(mode: str) -> dict:
    if mode == "nested-exact-dict":
        return {"reading": 0.25, "nested": {"reading": 0.25}}
    if mode == "nested-dict-subclass":
        return {"reading": 0.25, "nested": _Sub({"reading": 0.25})}
    if mode == "beyond-depth-cap":
        deep: dict = {"reading": 0.25}
        for _ in range(_DEEP):
            deep = {"nested": deep}
        return {"reading": 0.25, "nested": deep}
    return {"reading": 0.25}


def _schema(mode: str) -> dict:
    """The STRICTEST schema that can be declared for the arm's payload shape.

    Arm 2 gets the auditor's schema verbatim in spirit: `additionalProperties: false`,
    `required`, and a bounded `minimum`/`maximum` on the one value. The nested arms must
    declare their nested object or the payload could not conform in the first place, so
    they are strict on everything the shape allows them to be strict about.
    """
    reading = {"type": "number", "minimum": 0.0, "maximum": 1.0}
    if mode in ("nested-exact-dict", "nested-dict-subclass"):
        return {
            "type": "object",
            "additionalProperties": False,
            "required": ["reading", "nested"],
            "properties": {
                "reading": reading,
                "nested": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["reading"],
                    "properties": {"reading": reading},
                },
            },
        }
    if mode == "beyond-depth-cap":
        return {
            "type": "object",
            "additionalProperties": False,
            "required": ["reading", "nested"],
            "properties": {"reading": reading, "nested": {"type": "object"}},
        }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["reading"],
        "properties": {"reading": reading},
    }


class _HostileAdapter:
    """Conforming to `SourceAdapter` in every member; hostile in exactly one of them."""

    source_id = "PROBE-A"
    adapter_id = "probe-a-hostile"

    def __init__(self, mode: str) -> None:
        self.mode = mode
        self.response_schema = _schema(mode)
        self._payload = _fresh_payload(mode)
        self.seen_by_is_empty: str = "<is_empty not reached>"
        self.is_empty_object_id: int = 0
        self.returned_object_id: int = id(self._payload)

    def fetch(self, *, timeout_seconds: float) -> FetchedResponse:
        return FetchedResponse(
            payload=self._payload,
            source_as_of_utc=datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc),
        )

    def is_empty(self, payload: object) -> bool:
        """DECLARED-FOREIGN CODE, handed the payload between judgement and storage."""
        self.seen_by_is_empty = _render(payload)
        self.is_empty_object_id = id(payload)
        target = payload
        if self.mode == "toplevel":
            target["reading"] = float("inf")
            target["not_in_schema"] = "\x00\x00\x00"
            target["type"] = __builtins__ if isinstance(__builtins__, dict) else "builtins"
        elif self.mode in ("nested-exact-dict", "nested-dict-subclass"):
            target["nested"]["reading"] = float("inf")
        elif self.mode == "beyond-depth-cap":
            cursor = target["nested"]
            for _ in range(_DEEP - 1):
                cursor = cursor["nested"]
            cursor["nested"]["reading"] = float("inf")
        return False


class _RecordingValidator:
    """Records WHAT THE VALIDATOR WAS HANDED, then delegates to the SHIPPED validator.

    It reads and never writes. The judging is done by `JsonSchemaValidator`, unmodified —
    a probe that judged with its own validator would be measuring the probe.
    """

    def __init__(self) -> None:
        self.inner = JsonSchemaValidator()
        self.saw: str = "<validate not reached>"
        self.saw_object_id: int = 0

    def validate(self, payload: object, schema: object) -> None:
        self.saw = _render(payload)
        self.saw_object_id = id(payload)
        return self.inner.validate(payload, schema)


def _conforms(payload: object, schema: object) -> str:
    try:
        JsonSchemaValidator().validate(payload, schema)
    except SchemaRejection as exc:
        return f"NO  -> SchemaRejection: {exc.error_class} at {exc.instance_path or '<root>'}"
    except Exception as exc:  # noqa: BLE001 — a probe reports, it does not classify
        return f"NO  -> {type(exc).__name__}: {exc}"
    return "YES"


def _read_deep(value: object) -> object:
    cursor = value
    while isinstance(cursor, dict) and "nested" in cursor:
        cursor = cursor["nested"]
    return cursor


def _arm(mode: str) -> None:
    adapter = _HostileAdapter(mode)
    validator = _RecordingValidator()
    outcome = _attempt(
        adapter,
        policy=RetryPolicy(max_attempts=1, timeout_seconds=5.0, backoff_seconds=0.0),
        validator=validator,
    )

    print(f"--- mode={mode}")
    print(f"    outcome type                : {type(outcome).__name__}")
    if not isinstance(outcome, OK):
        print("    (no OK.payload to compare — arm stops here)")
        print()
        return

    stored = _render(outcome.payload)
    print(f"    validator saw               : {_shown(validator.saw)}")
    print(f"    is_empty was handed         : {_shown(adapter.seen_by_is_empty)}")
    print(f"    stored on OK.payload        : {_shown(stored)}")
    print(f"    STORED == VALIDATED (text)  : {stored == validator.saw}")
    # `OK.__post_init__` has always done `dict(self.payload)`, so the STORED object is never
    # identical to anything upstream. Identity is therefore reported against the object the
    # ADAPTER'S OWN `fetch` returned — the only live reference an adapter can retain.
    print(f"    validator's argument IS the adapter's live object : "
          f"{validator.saw_object_id == adapter.returned_object_id}")
    print(f"    is_empty's argument IS the adapter's live object  : "
          f"{adapter.is_empty_object_id == adapter.returned_object_id}")
    print(f"    type(OK.payload) is exactly dict            : {type(outcome.payload) is dict}")
    if mode in ("nested-exact-dict", "nested-dict-subclass"):
        print(f"    type(OK.payload['nested']) is exactly dict  : "
              f"{type(outcome.payload['nested']) is dict}")
        print(f"    OK.payload['nested']['reading']             : "
              f"{outcome.payload['nested']['reading']!r}")
    if mode == "beyond-depth-cap":
        print(f"    innermost stored dict, {_DEEP} levels down       : "
              f"{_read_deep(outcome.payload)!r}")
    print(f"    does the STORED payload conform to the schema it was judged by?")
    print(f"       {_conforms(outcome.payload, adapter.response_schema)}")
    print()


def main() -> int:
    print("PROBE A — IS THE STORED PAYLOAD THE VALIDATED PAYLOAD? (ESCAPE 1)")
    print(f"tree: {Path(__file__).resolve().parents[2]}")
    print("NO VERDICT IS PRINTED. READ THE DATA LINES.")
    print()
    for mode in (
        "none",
        "toplevel",
        "nested-exact-dict",
        "nested-dict-subclass",
        "beyond-depth-cap",
    ):
        _arm(mode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
