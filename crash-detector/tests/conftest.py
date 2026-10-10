"""Shared fixtures.

``pythonpath = ["src"]`` in ``pyproject.toml`` is what makes ``crash_detector`` importable
with no install step; nothing here manipulates ``sys.path``.

Every fixture below returns a fresh object per test. There is no module- or session-scoped
mutable fixture on purpose: a shared fixture mutated by one test silently changes what
every later test is measuring.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

#: A fixed instant. The dial core takes ``now_utc`` as an argument precisely so that tests
#: never depend on the wall clock.
FIXED_NOW = datetime(2026, 8, 19, 12, 0, 0, tzinfo=timezone.utc)

#: Ten minutes, as the declared staleness window used throughout the tests. A test
#: constant, not a product value: the real window is configuration, and the regime-aware
#: window is CD-AC-009 in WO-3.
#:
#: It was one hour until CD-ASR-F06 was closed. A window is now admitted only through
#: :class:`crash_detector.staleness.StalenessWindow`, which refuses anything above
#: ``STALENESS_WINDOW_CEILING_SECONDS`` — 900 s, DERIVED from PID.md §5's ratified
#: 15-minute detectability budget — so 3600.0 is not an admissible window anywhere any
#: more, including in a fixture. 600.0 is chosen only because it is strictly below the
#: ceiling with room to spare. It carries no product meaning and none may be read into it.
WINDOW_SECONDS = 600.0


@pytest.fixture()
def now() -> datetime:
    return FIXED_NOW


@pytest.fixture()
def window() -> float:
    return WINDOW_SECONDS


def ago(seconds: float) -> datetime:
    """``seconds`` before :data:`FIXED_NOW`. Negative values are in the future."""
    return FIXED_NOW - timedelta(seconds=seconds)


def freshness_for(
    as_of_utc: datetime = FIXED_NOW, *, window_seconds: float = WINDOW_SECONDS
):
    """Freshness evidence for an observation dated ``as_of_utc``, read at FIXED_NOW.

    A helper, not a shortcut: it constructs a real
    :class:`crash_detector.staleness.FreshnessEvidence`, so it RAISES for anything stale
    or future-dated exactly as production does. There is no test-only route to agreement
    and there must not be one, or the tests would be proving something the product does
    not do (CD-ASR-F06).
    """
    from crash_detector.staleness import FreshnessEvidence, StalenessWindow

    return FreshnessEvidence(
        as_of_utc=as_of_utc,
        observed_at_utc=FIXED_NOW,
        window=StalenessWindow(seconds=window_seconds),
    )
