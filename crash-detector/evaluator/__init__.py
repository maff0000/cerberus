"""The state machine's own memory, and (later) the ``cd-live-evaluator`` pass that fills it.

WO-1.3a round 4, built to ``governance/WO-1.3a-engine-spec.md`` §7-9.

It lives OUTSIDE ``src/crash_detector`` for the reason :mod:`ingestion` does: the
application tree in ``src/`` computes a reading from what it is handed and owns no
durable store. ``ingestion`` is the collector's side of BLUEPRINT §5 (it fetches and
records, it never computes); this package is the evaluator's side (it computes nothing
the engine does not, and it records what one evaluation concluded).

NOTHING HERE IS DEPLOYED BY THIS ROUND. Spec §9 holds the container, the compose entry
and the Dockerfile for a later round, once the logic is proven, and this package is the
first half of that logic: the store. The evaluator pass itself — read the raw store,
compute via :mod:`crash_detector.engine.statistics`, apply spec §3's precedence, write
one row — is the next step and is not here yet.

Import route: ``PYTHONPATH=src:.`` from ``crash-detector/``.
"""
