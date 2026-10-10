"""PBGv2 tooling.

The framework version is NEVER hardcoded here. It is read from the canonical VERSION file
(PBG-FWK-010 / PBG-FWK-011). Any module that embeds a version literal is a validation failure.
"""

from __future__ import annotations

from pathlib import Path


def framework_version(root: Path | None = None) -> str:
    from .versioning import read_version

    if root is None:
        here = Path(__file__).resolve()
        for candidate in [here, *here.parents]:
            if (candidate / "VERSION").is_file():
                root = candidate
                break
        else:  # pragma: no cover - only reachable outside a framework tree
            raise FileNotFoundError("VERSION not found")
    return read_version(root)


__all__ = ["framework_version"]
