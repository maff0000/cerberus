"""The shared entrypoint shim (BLUEPRINT §2, deliverable A6 — DESIGN, nothing is built).

Every service's entrypoint is four lines over :func:`boot`. The lifecycle itself —
``SIGTERM``, the bounded shutdown, the stdout logging — lives in
:mod:`crash_detector.runtime.lifecycle`, because container-readiness is a property of the
APPLICATION and not of the Dockerfile.

WHAT THESE PROCESSES DO IN WO-2: they start, they declare themselves, they tick, and they
shut down cleanly when told to. That is the whole of it, and it is deliberate. WO-2
delivers the container set as DESIGN; the collectors have no registered source to fetch
(CD-D-005 is owed to the Product Owner), the engine has nothing to evaluate but the empty
registry, and the two surfaces have no envelope to serve. Giving them stub behaviour that
looked like work would be manufacturing the appearance of a running system, which is the
one thing this product exists not to do.

What IS real here and will not be rewritten in WO-3: the signal contract, the shutdown
budget, the exit codes and the log stream.

RT-B — building these images — IS FORBIDDEN IN WO-2 (PBG-RT-010). The state recorded is
CONTAINER_READY_DESIGN with CONTAINER_BUILD_NOT_YET_AUTHORISED.
"""

from __future__ import annotations

import os
import pathlib
import sys

_SRC = pathlib.Path(__file__).resolve().parents[2] / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    # Present so an entrypoint runs from a checkout as well as from an image, where
    # PYTHONPATH=/app/src is set by the Dockerfile. Resolved relative to this file: no
    # host-specific absolute path anywhere.
    sys.path.insert(0, str(_SRC))

from crash_detector.runtime.lifecycle import (  # noqa: E402
    DEFAULT_GRACE_SECONDS,
    Lifecycle,
)

__all__ = ["boot", "TICK_INTERVAL_ENV_VAR", "GRACE_SECONDS_ENV_VAR"]

#: Configuration is read from the environment (BLUEPRINT §11, PBG-SEC-001).
#:
#: THE TWO ARE NOT THE SAME KIND OF SETTING, AND THE DIFFERENCE IS STATED RATHER THAN
#: LEFT TO BE READ OFF THE CODE.
#:
#: ``CD_TICK_INTERVAL_SECONDS`` is REQUIRED and has no in-code default. A tick interval
#: nobody chose is a cadence nobody chose, and cadence is what CD-AC-008 alerts on: a
#: default here would mean an alert threshold derived from a number no human picked.
#:
#: ``CD_SHUTDOWN_GRACE_SECONDS`` is OPTIONAL and falls back to
#: :data:`~crash_detector.runtime.lifecycle.DEFAULT_GRACE_SECONDS`. That default is safe
#: to have because it is not a product number: it is bounded, it is declared in one place,
#: and it is checked against the platform's own ``stop_grace_period`` by a test. README.md
#: documents it as defaulting to 15.0, and this is the code that must agree with that.
TICK_INTERVAL_ENV_VAR = "CD_TICK_INTERVAL_SECONDS"
GRACE_SECONDS_ENV_VAR = "CD_SHUTDOWN_GRACE_SECONDS"


def _required_float(name: str) -> float:
    """The float in ``name``, or a refusal that says which of the two things went wrong.

    UNSET and SET-BUT-BLANK are reported differently on purpose. They have different
    causes and different fixes — nobody configured this, versus somebody configured it and
    the value did not arrive — and an operator reading the first message while looking at
    the second wastes the time the message exists to save. This is the same distinction
    the collector outcomes make between EMPTY and FETCH_FAILED (BLUEPRINT §5).
    """
    raw = os.environ.get(name)
    if raw is None:
        raise SystemExit(
            f"REFUSED: {name} is unset. Configuration comes from the environment — see "
            "deploy/compose.yaml, which declares it."
        )
    if not raw.strip():
        raise SystemExit(
            f"REFUSED: {name} is set but blank. A blank value is not an absent one: this "
            "process will not fall back to a default for a variable somebody set."
        )
    try:
        value = float(raw)
    except ValueError:
        raise SystemExit(
            f"REFUSED: {name} is not a number. The value is not reproduced here."
        ) from None
    return value


def boot(service_name: str) -> int:
    """Run ``service_name`` until it is told to stop. Returns the process exit code."""
    interval_seconds = _required_float(TICK_INTERVAL_ENV_VAR)

    # `is None` and not truthiness. An EMPTY or whitespace-only value is a variable
    # somebody set and got wrong, not a variable nobody set, and the two deserve different
    # answers: the first is refused by _required_float, the second takes the declared
    # default. `if os.environ.get(...)` conflates them and would silently accept a broken
    # setting as an absent one.
    raw_grace = os.environ.get(GRACE_SECONDS_ENV_VAR)
    grace_seconds = (
        DEFAULT_GRACE_SECONDS
        if raw_grace is None
        else _required_float(GRACE_SECONDS_ENV_VAR)
    )

    lifecycle = Lifecycle(service_name, grace_seconds=grace_seconds)
    lifecycle.install()

    def tick() -> None:
        # No work is declared for this service in WO-2. Stated on every tick rather than
        # left silent, so an operator watching the log sees a process that is running and
        # honestly idle, not one that might be doing something.
        lifecycle.log("tick", work="none_declared_in_wo2")

    return lifecycle.run(tick, interval_seconds=interval_seconds)
