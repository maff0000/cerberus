"""Crash Detector — a standalone market-stress instrument.

ADVISORY ONLY (PID.md §1 and §4, CONSTITUTIONAL). This package detects, scores, explains
and publishes machine-readable state. It never executes, places or alters anything, and
it contains no order, execution or broker interface of any kind (PID §6, CD-AC-012).

Import with ``PYTHONPATH=src``. There is no install step and no build backend: see the
comment at the head of ``pyproject.toml`` for why that is deliberate.

Package map, and which work order each part is owed to:

===========================  =====  =====================================================
module                       WO     what it is
===========================  =====  =====================================================
``time_utc``                 WO-2   UTC-only timestamp handling; naive datetimes refused
``observations``             WO-2   the observation record and its four-way fetch outcome
``dials``                    WO-2   ``Reading``, the two unrelated score types, ``DialSet``
``engine``                   WO-2   the pure ``evaluate`` core and its config snapshot
``witness``                  WO-2   the ``WitnessPanel`` sum type
``serving.witness_resolver`` WO-2   absence and staleness -> UNAVAILABLE, never AGREES
===========================  =====  =====================================================
"""

__all__ = ["__version__"]

# Application version. This is NOT a release identity — release identity on this project
# is the exact Git SHA (Standards Baseline §3).
__version__ = "0.1.0"
