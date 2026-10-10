"""Building dial magnitudes in tests. MECHANICS, not a relaxed expectation.

Since ``CD-PL-F54`` a :class:`~crash_detector.dials.magnitude.DialMagnitude` is built from
a :class:`~crash_detector.dials.provenance.DeclaredQuantity` rather than from a bare
``float``: a number that has left a magnitude has lost its dial, so no bare number may
re-enter one. A test that wants a magnitude therefore has to say where its number came
from, exactly as the product's one admission site in
``crash_detector.engine.evaluate`` does.

**Nothing any test asserts became weaker.** The constructions became explicit, and the
refusals that used to be asserted against ``DialMagnitude(...)`` are asserted against the
admission door instead — plus a NEW refusal, that a bare ``float`` cannot be a magnitude at
all, which several tests now assert directly.

This module is not a test module and pytest does not collect it (it does not match
``test_*.py``), in the manner of ``tests/collector_fakes.py``.
"""

from __future__ import annotations

from crash_detector.dials.magnitude import DialMagnitude
from crash_detector.dials.provenance import observed_for_dial

#: A stand-in ingredient source id. It is deliberately NOT a dial id: a dial is not an
#: ingredient of a dial, and ``observed_for_dial`` refuses one that says otherwise.
TEST_SOURCE_IDS: tuple[str, ...] = ("test-source",)


def quantity_of(dial_id: str, value: float, inputs_used=TEST_SOURCE_IDS):
    """A declared quantity for ONE dial, as the admission door yields one."""
    return observed_for_dial(dial_id=dial_id, quantity=value, inputs_used=inputs_used)


def magnitude_of(dial_id: str, value: float, inputs_used=TEST_SOURCE_IDS) -> DialMagnitude:
    """A magnitude for ONE dial, carrying a number admitted for that same dial."""
    return DialMagnitude(
        dial_id=dial_id, quantity=quantity_of(dial_id, value, inputs_used)
    )
