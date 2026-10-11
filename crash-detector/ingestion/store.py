"""A durable, append-only DEV store that mirrors ``raw.observation`` / ``raw.reading``.

It implements the runner's two storage protocols (``ObservationSink``, ``ReadingLedger``)
with the SAME rules as ``db/migrations/0002``:

* ``raw_observation`` — one row per fetch attempt, failures included, append-only. No
  free-text detail column and no payload (PBG-SEC-002).
* ``raw_reading`` — the validated payload of one source period, ``UNIQUE (source_id,
  source_as_of_utc)``; a re-fetch of a claimed period adds an observation row, never a
  second reading.

SQLite (stdlib) because the Postgres ``cd-store`` is written-not-deployed (STATUS §4) and
this seat has no authority to stand it up. The row shapes are 1:1 with the migration so the
cut-over is a connection change. No UPDATE or DELETE is issued by this module, and the file
is opened with triggers that refuse both — the grant matrix's guarantee, stated in the one
place a single-file store can state it.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from typing import Iterator, Union

from crash_detector.collectors.attempt import AttemptRecord, ReadingKey
from crash_detector.observations import OK, Empty, FetchFailed, Malformed
from crash_detector.time_utc import format_utc

__all__ = ["SqliteStore"]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS raw_source_registry (
    source_id TEXT PRIMARY KEY, adapter_id TEXT NOT NULL, poll_seconds INTEGER NOT NULL,
    stands_for TEXT NOT NULL, declared_feed TEXT NOT NULL, serves TEXT NOT NULL,
    registered_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS raw_observation (
    observation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL, adapter_id TEXT NOT NULL, collector_run_id TEXT NOT NULL,
    attempt_number INTEGER NOT NULL CHECK (attempt_number >= 1),
    requested_utc TEXT NOT NULL, observed_utc TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('OK','FETCH_FAILED','MALFORMED','EMPTY')),
    source_as_of_utc TEXT, error_class TEXT, http_status INTEGER,
    schema_error_class TEXT, instance_path TEXT
);
CREATE TABLE IF NOT EXISTS raw_reading (
    reading_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL, source_as_of_utc TEXT NOT NULL,
    payload TEXT NOT NULL CHECK (json_type(payload) = 'object'),
    observation_id INTEGER NOT NULL REFERENCES raw_observation(observation_id),
    admitted_utc TEXT NOT NULL,
    UNIQUE (source_id, source_as_of_utc)
);
CREATE TRIGGER IF NOT EXISTS raw_observation_no_update BEFORE UPDATE ON raw_observation
    BEGIN SELECT RAISE(ABORT, 'raw_observation is append-only'); END;
CREATE TRIGGER IF NOT EXISTS raw_observation_no_delete BEFORE DELETE ON raw_observation
    BEGIN SELECT RAISE(ABORT, 'raw_observation is append-only'); END;
CREATE TRIGGER IF NOT EXISTS raw_reading_no_update BEFORE UPDATE ON raw_reading
    BEGIN SELECT RAISE(ABORT, 'raw_reading is append-only'); END;
CREATE TRIGGER IF NOT EXISTS raw_reading_no_delete BEFORE DELETE ON raw_reading
    BEGIN SELECT RAISE(ABORT, 'raw_reading is append-only'); END;
"""


class SqliteStore:
    """Implements ``ObservationSink`` and ``ReadingLedger`` over one SQLite file."""

    __slots__ = ("_db", "_pending")

    def __init__(self, path: str, *, read_only: bool = False) -> None:
        if read_only:
            # The GUI's door (WO-1.4): the database must already exist, nothing is created and
            # no write of any kind can be issued through this handle.
            self._db = sqlite3.connect(f"file:{path}?mode=ro", uri=True, isolation_level=None)
            self._pending = {}
            return
        self._db = sqlite3.connect(path, isolation_level=None)  # autocommit: durable per row
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA synchronous=FULL")
        self._db.executescript(_SCHEMA)
        self._pending: dict[ReadingKey, tuple[int, str]] = {}

    def close(self) -> None:
        self._db.close()

    def __enter__(self) -> "SqliteStore":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # -- registry -------------------------------------------------------------------- #

    def register(self, source_id: str, adapter_id: str, poll_seconds: int, stands_for: str,
                 declared_feed: str, serves: tuple, now: datetime) -> None:
        self._db.execute(
            "INSERT OR IGNORE INTO raw_source_registry VALUES (?,?,?,?,?,?,?)",
            (source_id, adapter_id, poll_seconds, stands_for, declared_feed,
             ",".join(serves), format_utc(now)),
        )

    # -- ObservationSink ------------------------------------------------------------- #

    def record(self, attempt: AttemptRecord) -> None:
        outcome = attempt.outcome
        as_of = error_class = schema_error = instance_path = None
        status = None
        payload_json = None
        if isinstance(outcome, OK):
            as_of = format_utc(outcome.source_as_of_utc)
            payload_json = json.dumps(dict(outcome.payload), sort_keys=True)
        elif isinstance(outcome, FetchFailed):
            error_class, status = outcome.error_class, outcome.http_status
        elif isinstance(outcome, Malformed):
            schema_error, instance_path = outcome.schema_error_class, outcome.instance_path
        elif not isinstance(outcome, Empty):  # the sum type is closed; no fall-through
            raise TypeError(f"not a FetchOutcome: {type(outcome).__name__}")
        cursor = self._db.execute(
            "INSERT INTO raw_observation (source_id, adapter_id, collector_run_id, attempt_number,"
            " requested_utc, observed_utc, outcome, source_as_of_utc, error_class, http_status,"
            " schema_error_class, instance_path) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (attempt.source_id, attempt.adapter_id, attempt.collector_run_id, attempt.attempt_number,
             format_utc(attempt.requested_utc), format_utc(attempt.completed_utc),
             attempt.outcome_class, as_of, error_class, status, schema_error, instance_path),
        )
        if payload_json is not None and attempt.reading_key is not None:
            self._pending[attempt.reading_key] = (cursor.lastrowid, payload_json)
        return None

    # -- ReadingLedger --------------------------------------------------------------- #

    def admit_if_absent(self, key: ReadingKey) -> bool:
        pending = self._pending.pop(key, None)
        if pending is None:
            raise LookupError("admit_if_absent called for a key no OK attempt recorded")
        observation_id, payload_json = pending
        cursor = self._db.execute(
            "INSERT OR IGNORE INTO raw_reading (source_id, source_as_of_utc, payload, observation_id,"
            " admitted_utc) VALUES (?,?,?,?,?)",
            (key[0], key[1], payload_json, observation_id, format_utc(datetime.now(timezone.utc))),
        )
        return cursor.rowcount == 1

    # -- reads ----------------------------------------------------------------------- #

    def last_attempt(self, source_id: str) -> Union[tuple[datetime, str], None]:
        row = self._db.execute(
            "SELECT observed_utc, outcome FROM raw_observation WHERE source_id=? "
            "ORDER BY observation_id DESC LIMIT 1", (source_id,)).fetchone()
        return None if row is None else (datetime.fromisoformat(row[0].replace("Z", "+00:00")), row[1])

    def latest_reading(self, source_id: str) -> Union[dict, None]:
        """Newest admitted reading by SOURCE period (not by when we fetched it)."""
        row = self._db.execute(
            "SELECT source_as_of_utc, payload, admitted_utc FROM raw_reading WHERE source_id=? "
            "ORDER BY source_as_of_utc DESC LIMIT 1", (source_id,)).fetchone()
        if row is None:
            return None
        return {"source_as_of_utc": row[0], "payload": json.loads(row[1]), "admitted_utc": row[2]}

    def recent_readings(self, source_id: str, limit: int) -> list:
        """Up to ``limit`` admitted payloads, newest SOURCE period first (a derivation's inputs)."""
        rows = self._db.execute(
            "SELECT payload FROM raw_reading WHERE source_id=? ORDER BY source_as_of_utc DESC LIMIT ?",
            (source_id, int(limit))).fetchall()
        return [json.loads(row[0]) for row in rows]

    def outcome_counts(self) -> Iterator[tuple[str, str, int]]:
        yield from self._db.execute(
            "SELECT source_id, outcome, COUNT(*) FROM raw_observation GROUP BY 1,2 ORDER BY 1,2")
