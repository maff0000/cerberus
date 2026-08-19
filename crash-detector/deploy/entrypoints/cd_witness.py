#!/usr/bin/env python3
"""Entrypoint for `cd-witness` — fetches witness observations and builds the witness panel (BLUEPRINT §6). Shares no component with the score.

Thin by design. The lifecycle contract it runs under is in
`crash_detector.runtime.lifecycle`; the shim is in `_service.py` beside this file.

RT-B is FORBIDDEN in WO-2: this image is written and not built
(CONTAINER_READY_DESIGN / CONTAINER_BUILD_NOT_YET_AUTHORISED).
"""

from __future__ import annotations

import sys

from _service import boot

SERVICE_NAME = "cd-witness"

if __name__ == "__main__":
    sys.exit(boot(SERVICE_NAME))
