"""Process lifecycle — the container-ready half that belongs to the application.

Container-readiness is a property of the APPLICATION, not of the Dockerfile
(``pbg/skills/core/container-ready-application-design.md``). A process that ignores
``SIGTERM`` gets killed, and whatever it was midway through becomes a recovery problem; no
amount of care in a compose file fixes that from outside. So the signal handling, the
bounded shutdown and the stdout/stderr logging live here, in code, and the entrypoints
under ``deploy/entrypoints/`` are thin shims over them.

Nothing in this package computes a dial value, reads a store or opens a socket.
"""

from __future__ import annotations

__all__: tuple[str, ...] = ()
