"""The store layer — schema migration only (BLUEPRINT §4, deliverable A5).

This package holds the **migration step** and nothing else. It is deliberately not a data
access layer, not a repository and not a connection factory:

  * migrations are applied by a **dedicated step that is not the application's startup
    path** (``PBG-DATA-002``, ``PBG-DATA-003``). A service that migrates on boot migrates
    once per replica, races the other replicas, and does it with whatever privileges the
    service happens to hold. The command that applies them lives at ``db/migrate.py``,
    outside the importable application package, so no service can reach it by an import
    even by accident;
  * nothing here imports a database driver. :func:`crash_detector.store.migrate.apply`
    takes an already-open **PEP 249 connection** as an argument. That keeps the whole of
    ``src/`` free of a driver import, and it means the apply logic is exercised by tests
    against a recording double as well as against a live PostgreSQL.

The persistence path for observations, readings, envelopes and alerts is WO-3 and is owed.
"""

from __future__ import annotations

__all__: tuple[str, ...] = ()
