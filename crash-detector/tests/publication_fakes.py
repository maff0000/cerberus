"""Test doubles for the publication layer. **Named as doubles, living under ``tests/``.**

``RecordingConnection`` executes nothing. It journals the exact SQL and parameters it was
handed, IN ORDER, which is the property the publication tests actually need: *"validated
before written"* is a claim about ORDER, and the way to measure it is to record what order
things happened in and assert that on a refusal the journal contains **no envelope insert at
all**.

This is the same approach ``tests/test_store_migrate_apply.py`` already takes against
``crash_detector.store.migrate``, and it is available because ``src/`` imports no database
driver: every writer in this package takes an already-open PEP 249 connection.

===========================================================================================
*** THE ENVELOPES BELOW REGISTER NO SOURCE, AND CANNOT BE MISTAKEN FOR ONE ***
===========================================================================================
``Q25`` holds the ingredient set with the Product Authority, and ``CD-PL-F154`` is what
happens when a fixture escapes. So:

* both dials are ``UNKNOWN`` with ``missing_inputs: []`` — **which is the shipped WO-2 state
  and not a fabrication**: with zero registered sources there is nothing to name;
* ``inputs_used`` and ``degraded_inputs`` are **empty**, which the public schema explicitly
  documents as *"Empty is legal and is the WO-2 state"*;
* nothing here constructs a ``SourceRecord``, imports ``crash_detector.source_registry``, or
  emits a statement naming ``raw.source_registry``;
* the ``config_snapshot_id`` is the literal string ``SYNTHETIC-TEST-DOUBLE-NOT-A-CONFIG`` so
  that a grep for it lands here and nowhere near a registry.

**There is therefore no fixture in this file that could escape into the product as an
ingredient, because there is no ingredient in it.**
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

#: Taken from the module rather than retyped, so a fixture cannot silently pin a version the
#: contracts no longer declare — which is exactly what a hardcoded "1.0.0" did until WO-3
#: increment 16A bumped both schemas to 1.1.0 for the per-dial `detail_level`.
from crash_detector.publication.envelope_contract import ENVELOPE_SCHEMA_VERSION

from crash_detector.dials.dialset import EQUITY_DIAL_ID
from crash_detector.dials.reading import Degraded, Unknown
from crash_detector.publication.detail_level import DetailPolicy, detail_level_for

from dial_magnitudes import magnitude_of

#: Deliberately unmistakable. If this string is ever seen outside tests/, something escaped.
SYNTHETIC_CONFIG_SNAPSHOT_ID = "SYNTHETIC-TEST-DOUBLE-NOT-A-CONFIG"

AS_OF_UTC = "2026-08-23T12:00:00Z"
PUBLISHED_UTC = "2026-08-23T12:00:05Z"

#: The same instant as :data:`AS_OF_UTC`, PARSED FROM IT rather than written out a second
#: time, so the datetime a reading carries and the string its dial dict carries cannot drift
#: apart. The readings below need a real ``datetime``; the envelope needs the wire string.
NOW = datetime.strptime(AS_OF_UTC, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

#: *** THE LEVEL A MISSING-DATA DIAL CARRIES IS COMPUTED, NOT TYPED IN (WO-3 16A-FIX, F4). ***
#:
#: Until 16A-FIX ``unknown_dial()`` returned a hardcoded ``"detail_level": "elevated"`` under
#: a comment asserting the PID §3.2 guarantee. **The literal could have been ``"calm"`` and
#: nothing in this file would have objected** — the fake asserted a guarantee it did not
#: obtain, which is one half of why CD-ASR-WO3-03 returned RED. Now the value comes out of
#: :func:`~crash_detector.publication.detail_level.detail_level_for`, the function the
#: product would call, applied to a real :class:`Unknown`/:class:`Degraded` reading.
#:
#: The one literal left is ``absent_data_level`` below, and it **cannot be ``calm`` by
#: construction**: :class:`DetailPolicy`'s ``__post_init__`` raises ``DetailPolicyIncoherent``
#: on ``calm``, citing PID §3.2. So the fake now inherits the constitutional refusal rather
#: than re-stating it in a comment.
#:
#: SYNTHETIC AND MEANINGLESS AS NUMBERS. The dial has no ratified scale (``Q25`` holds it),
#: and no ``Unknown`` or ``Degraded`` reading ever reaches ``_level_for_score`` anyway — both
#: branches return ``policy.absent_data_level`` directly — so these thresholds are structure,
#: never a declared scale. **NOTHING HERE REGISTERS A SOURCE.**
FAKE_DETAIL_POLICY = DetailPolicy(
    elevated_at=0.4, acute_at=0.8, absent_data_level="elevated"
)


class RecordingCursor:
    """Records; executes nothing. Returns a fixed identity for ``RETURNING``."""

    def __init__(self, connection: "RecordingConnection") -> None:
        self._connection = connection

    def __enter__(self) -> "RecordingCursor":
        return self

    def __exit__(self, *exc_info: object) -> bool:
        return False

    def execute(self, sql: str, parameters: object = None) -> None:
        if self._connection.raise_on_execute is not None:
            self._connection.journal.append(("execute-raised", sql, parameters))
            raise self._connection.raise_on_execute
        self._connection.journal.append(("execute", sql, parameters))

    def fetchone(self) -> tuple:
        return (self._connection.returning_id,)

    def fetchall(self) -> list:
        return list(self._connection.rows_to_return)


class RecordingConnection:
    """A PEP 249 shaped double whose whole purpose is the journal."""

    def __init__(
        self,
        *,
        returning_id: int = 4242,
        rows_to_return: "list | None" = None,
        raise_on_execute: "BaseException | None" = None,
    ) -> None:
        self.journal: list = []
        self.returning_id = returning_id
        self.rows_to_return = rows_to_return or []
        self.raise_on_execute = raise_on_execute

    def cursor(self) -> RecordingCursor:
        return RecordingCursor(self)

    def commit(self) -> None:
        self.journal.append(("commit", None, None))

    def rollback(self) -> None:
        self.journal.append(("rollback", None, None))

    # --- what the assertions read --------------------------------------------------------

    @property
    def executed(self) -> list:
        """Every SQL string actually executed, in order."""
        return [entry[1] for entry in self.journal if entry[0] == "execute"]

    def statements_touching(self, table: str) -> list:
        """Every executed statement naming ``table``. The core assertion of the layer."""
        return [sql for sql in self.executed if table in sql]

    def wrote_nothing_to(self, *tables: str) -> bool:
        return all(not self.statements_touching(table) for table in tables)

    def parameters_for(self, table: str) -> list:
        return [
            entry[2]
            for entry in self.journal
            if entry[0] == "execute" and table in entry[1]
        ]


def unknown_dial(reason: str = "NO_SOURCE_REGISTERED") -> dict:
    """A dial reading in the UNKNOWN state — **the shipped WO-2 state**.

    ``dial_reading_unknown`` declares NO ``score`` property at all, so there is nothing here
    to render as a number because there is no number (CD-AC-001 held in the schema).
    ``missing_inputs`` may be empty: *"'no source is registered' is a real reason with
    nothing to name."*
    """
    return {
        "state": "UNKNOWN",
        "reason": reason,
        "since_utc": AS_OF_UTC,
        "missing_inputs": [],
        # REQUIRED IN THIS BRANCH AS OF SCHEMA 1.1.0 (PO-DECISIONS-0025 ruling 5), and
        # NARROWED TO $defs/absent_data_detail_level AS OF 16A-FIX, so `calm` is not a
        # document this branch has. COMPUTED, NOT TYPED IN — see FAKE_DETAIL_POLICY.
        "detail_level": detail_level_for(
            Unknown(reason=reason, since_utc=NOW, missing_inputs=()),
            dial_slot=EQUITY_DIAL_ID,
            policy=FAKE_DETAIL_POLICY,
        ),
    }


def degraded_dial(reason: str = "INPUT_MISSING", score: float = 0.01) -> dict:
    """A dial reading in the DEGRADED state — **a value AND its damage**.

    The default ``score`` is 0.01, far BELOW ``FAKE_DETAIL_POLICY.elevated_at``, and that is
    the point rather than an arbitrary number: an implementation that read the magnitude and
    ignored the state would render this dial ``calm``, which is precisely PID §4's prohibited
    *"rendering stale or missing data as calm"*. ``detail_level_for`` returns
    ``policy.absent_data_level`` for ``Degraded`` exactly as it does for ``Unknown``, so the
    level below is ``elevated`` **because of the damage and not because of the number**.

    ``missing_inputs`` carries one named input because the contract requires ``minItems: 1``
    here: a reading with nothing missing is a ``Value``, not a degradation. The name is the
    ``dial_magnitudes`` stand-in and **is not an ingredient** — nothing here registers a
    source (``Q25``).
    """
    reading = Degraded(
        value=magnitude_of(EQUITY_DIAL_ID, score),
        as_of_utc=NOW,
        missing_inputs=("test-source",),
        reason=reason,
    )
    return {
        "state": "DEGRADED",
        "score": score,
        "as_of_utc": AS_OF_UTC,
        "missing_inputs": ["test-source"],
        "reason": reason,
        "contributions": [],
        "detail_level": detail_level_for(
            reading, dial_slot=EQUITY_DIAL_ID, policy=FAKE_DETAIL_POLICY
        ),
    }


def public_envelope(**overrides: Any) -> dict:
    """A conforming public envelope. **THE ADMITTING ARM of every refusal test.**"""
    envelope = {
        "schema_version": ENVELOPE_SCHEMA_VERSION,
        "as_of_utc": AS_OF_UTC,
        "published_utc": PUBLISHED_UTC,
        "regime": "CALM",
        "staleness_window_seconds": 600.0,
        "inputs_used": [],
        "degraded_inputs": [],
        "config_snapshot_id": SYNTHETIC_CONFIG_SNAPSHOT_ID,
        "equity_crash": unknown_dial(),
        "monetary_debasement": unknown_dial(),
    }
    envelope.update(overrides)
    return envelope


def private_envelope(**overrides: Any) -> dict:
    """A conforming private envelope — the public allowlist plus its classification."""
    envelope = public_envelope()
    envelope["classification"] = "PRIVATE"
    envelope.update(overrides)
    return envelope
