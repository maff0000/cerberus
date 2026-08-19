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

#: One hour, as the declared staleness window used throughout the tests. A test constant,
#: not a product value: the real window is configuration, and the regime-aware window is
#: CD-AC-009 in WO-3.
WINDOW_SECONDS = 3600.0


@pytest.fixture()
def now() -> datetime:
    return FIXED_NOW


@pytest.fixture()
def window() -> float:
    return WINDOW_SECONDS


def ago(seconds: float) -> datetime:
    """``seconds`` before :data:`FIXED_NOW`. Negative values are in the future."""
    return FIXED_NOW - timedelta(seconds=seconds)
