"""The state machine's own memory, and (later) the ``cd-live-evaluator`` pass that fills it.

WO-1.3a round 4, built to ``governance/WO-1.3a-engine-spec.md`` §7-9.

It lives OUTSIDE ``src/crash_detector`` for the reason :mod:`ingestion` does: the
application tree in ``src/`` computes a reading from what it is handed and owns no
durable store. ``ingestion`` is the collector's side of BLUEPRINT §5 (it fetches and
records, it never computes); this package is the evaluator's side (it computes nothing
the engine does not, and it records what one evaluation concluded).

NOTHING HERE IS DEPLOYED BY ANY ROUND SO FAR. Spec §9 holds the container, the compose
entry and the Dockerfile for a later round, once the logic is proven. What is here is the
logic, in two modules: :mod:`evaluator.history_store` (the append-only memory) and
:mod:`evaluator.resolve` (spec §3's persistence, the second-leg rule and rule 5's
previous-state condition — the dial's OFFICIAL state, given its history and one reading).

Still to come, and named so the gap is not mistaken for completeness: the evaluator pass
that ties the two to real data — read the raw store, score the contributions, compute
breadth/acute/count via :mod:`crash_detector.engine.statistics`, resolve, append one row —
and ``trend_confirmed``, which is still a parameter a caller supplies and not yet computed
from any wired indicator (spec §7's own scope cut).

Import route: ``PYTHONPATH=src:.`` from ``crash-detector/``.
"""
