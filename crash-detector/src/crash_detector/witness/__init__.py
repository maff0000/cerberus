"""The witness layer — strictly side-by-side (BLUEPRINT §6).

A parallel pipeline that shares no component with the score, meeting it only where the two
are displayed next to each other. **Nothing in :mod:`crash_detector.engine` imports this
package**, and ``cd_engine`` will hold no grant of any kind on schema ``witness``.

WO-2 delivers the panel sum type and the serving-layer absence/staleness mapping
(CD-AC-005). Divergence computation and the live witness adapters are WO-4 (CD-AC-004).
"""

from crash_detector.witness.panel import (
    PANEL_CONSTRUCTORS,
    PANEL_STATES,
    UNAVAILABLE_REASONS,
    Agrees,
    Diverges,
    Unavailable,
    WitnessPanel,
    panel_state,
)

__all__ = [
    "Agrees",
    "Diverges",
    "PANEL_CONSTRUCTORS",
    "PANEL_STATES",
    "UNAVAILABLE_REASONS",
    "Unavailable",
    "WitnessPanel",
    "panel_state",
]
