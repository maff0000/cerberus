#!/usr/bin/env python3
"""CD-RT-003-ENGINE-NO-WITNESS-REACH — the engine cannot reach witness code, transitively.

    python3 tools/register/check_engine_no_witness_reach.py --root <subject tree>

CRITERION: CD-AC-003, "witnesses are side-by-side, never ingredients" (PID §6). PID doctrine
§3.4: a witness that is also an ingredient corroborates nothing. BLUEPRINT §13 requires that
"nothing reachable from src/crash_detector/engine/ reaches witness code".

The separation is held in TWO independent places, and this check is one of them. The other
is the store, where ``cd_engine`` holds no privilege of any kind on schema ``witness`` —
that is CD-RT-003-GRANT-MATRIX-LIVE, and it is a different instrument reading a different
substrate. Either alone would be a single point of failure for the product's most
consequential separation.

WHAT IT DOES
-------------
Builds the module map of the application package from the filesystem, then walks the import
graph outward from EVERY module under ``src/crash_detector/engine/`` — transitively, to
fixpoint — and asserts that no module in the reachable set is witness code.

BUILT FOR THE CLASS, NOT THE INSTANCE. The obvious plant is ``import
crash_detector.witness`` at the top of ``evaluate.py``, and a one-line grep would find it.
These are the routes a grep would not find, and each is checked:

  * TRANSITIVE reach. The engine imports a helper; three modules later the helper's helper
    imports witness code. The engine still reaches it. This is why the walk is to fixpoint
    rather than one level deep, and it is the route a plant author actually uses.
  * RELATIVE imports. ``from .. import witness``, ``from ..witness import panel``, at any
    depth. Resolved against the importing module's package, not pattern-matched.
  * ALIASED imports. ``import crash_detector.witness as anything``, ``from
    crash_detector.witness import Agrees as A`` — the alias is irrelevant, the target is not.
  * ATTRIBUTE reach without an import of the submodule. A module that imports the top-level
    ``crash_detector`` package and then writes ``crash_detector.witness.panel`` has reached
    witness code without ever naming it in an import statement.
  * DYNAMIC import by string. ``importlib.import_module("crash_detector.witness.panel")``,
    ``__import__(...)``. A literal argument naming witness code is a violation. A NON-literal
    argument — ``import_module(name)`` — is ALSO a violation, because the check cannot
    follow it and an import route the guard cannot follow is a hole with a comment in it.
    Failing closed here is the whole point: the alternative is passing on ignorance.
  * A WITNESS MODULE PATH IN A STRING, anywhere in a reachable module — the payload of an
    indirection whose mechanism the check has not seen.

PRECONDITIONS, all of which REFUSE rather than pass (PBG-CI-002): the engine package must
exist and contain modules; the witness package must exist — "the engine does not reach
witness code" is vacuously true of a tree with no witness code, and vacuously true is not
true; and the reachable set must be non-trivial, so a check that resolved no imports at all
cannot report a clean graph.

EXIT: 0 clean · 1 violation, with file and line · 2 usage · 3 precondition not met.
"""

from __future__ import annotations

import ast
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _support import Check, parse_root, read_text, resolve_root  # noqa: E402

CHECK_ID = "CD-RT-003-ENGINE-NO-WITNESS-REACH"

SOURCE_ROOT = "src"
PACKAGE = "crash_detector"
ENGINE_PACKAGE = "crash_detector.engine"
WITNESS_PACKAGE = "crash_detector.witness"


def _module_name(root: pathlib.Path, path: pathlib.Path) -> str:
    relative = path.relative_to(root / SOURCE_ROOT).with_suffix("")
    parts = list(relative.parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _is_witness(module: str) -> bool:
    return module == WITNESS_PACKAGE or module.startswith(WITNESS_PACKAGE + ".")


def _resolve(module: str, is_package: bool, node: ast.ImportFrom) -> str:
    """Resolve a relative ``from .. import x`` against the importing module.

    The anchor differs for a package and a plain module, and getting it wrong is not a
    cosmetic error: for ``crash_detector.engine.model``, ``from ..witness import panel``
    resolves to ``crash_detector.witness``, and an off-by-one produces the non-existent
    ``crash_detector.engine.witness``, which resolves to nothing and reads as clean. That
    is exactly how this check passed variant IG-V3 on its first run — see CD-ENG-F27.

    For a package (``__init__.py``) level 1 is the package itself; for a plain module
    level 1 is its containing package.
    """
    if not node.level:
        return node.module or ""
    parts = module.split(".")
    anchor = parts if is_package else parts[:-1]
    keep = len(anchor) - (node.level - 1)
    if keep < 0:
        return ""
    base = anchor[:keep]
    if node.module:
        base = base + node.module.split(".")
    return ".".join(base)


class ModuleImports:
    """The edges out of one module, plus the reach routes that are not import edges."""

    def __init__(
        self, check: Check, path: pathlib.Path, module: str, tree: ast.AST
    ) -> None:
        self.check = check
        self.path = path
        self.module = module
        self.is_package = path.name == "__init__.py"
        self.targets: set = set()
        self.local_package_names: set = set()
        self._collect(tree)

    def _add(self, dotted: str) -> None:
        if dotted:
            self.targets.add(dotted)

    def _collect(self, tree: ast.AST) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self._add(alias.name)
                    if alias.name == PACKAGE:
                        self.local_package_names.add(alias.asname or PACKAGE)
            elif isinstance(node, ast.ImportFrom):
                base = _resolve(self.module, self.is_package, node)
                self._add(base)
                for alias in node.names:
                    # `from crash_detector import witness` is an import of the SUBMODULE.
                    self._add(f"{base}.{alias.name}" if base else alias.name)
                    if base == PACKAGE and alias.name == PACKAGE:
                        self.local_package_names.add(alias.asname or alias.name)
            elif isinstance(node, ast.Call):
                self._collect_dynamic(node)

        # Attribute reach: `crash_detector.witness...` where only the package was imported.
        for node in ast.walk(tree):
            if not isinstance(node, ast.Attribute):
                continue
            base = node.value
            if isinstance(base, ast.Name) and base.id in self.local_package_names:
                self._add(f"{PACKAGE}.{node.attr}")

        # A witness module path carried as a string, in a module the engine can reach.
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if _is_witness(node.value.strip()):
                    self.check.violation(
                        self.path,
                        node.lineno,
                        "witness module path in a string literal",
                        f'the string "{node.value}" names witness code inside a module '
                        "the engine can reach. Whatever consumes it, the payload of an "
                        "indirection is a route, and a route the import graph cannot see "
                        "is the one worth reporting.",
                    )

    def _collect_dynamic(self, node: ast.Call) -> None:
        name = (
            node.func.attr
            if isinstance(node.func, ast.Attribute)
            else node.func.id if isinstance(node.func, ast.Name) else ""
        )
        if name not in {"import_module", "__import__", "find_spec", "load_module"}:
            return
        if not node.args:
            return
        first = node.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            self._add(first.value)
            return
        self.check.violation(
            self.path,
            node.lineno,
            "dynamic import the graph cannot follow",
            f"`{ast.unparse(node)[:120]}` imports a module named at run time. This check "
            "cannot follow it, so it cannot establish that the engine does not reach "
            "witness code through it. An import route the guard cannot follow is a hole "
            "with a comment in it, and this fails closed rather than passing on ignorance.",
        )


def main() -> int:
    args = parse_root(CHECK_ID, __doc__)
    root, code = resolve_root(CHECK_ID, args.root)
    if root is None:
        return code

    check = Check(CHECK_ID, root)

    package_dir = root / SOURCE_ROOT / PACKAGE.replace(".", "/")
    engine_dir = root / SOURCE_ROOT / ENGINE_PACKAGE.replace(".", "/")
    witness_dir = root / SOURCE_ROOT / WITNESS_PACKAGE.replace(".", "/")
    if not package_dir.is_dir():
        return check.refuse(f"{package_dir} does not exist in this subject tree.")
    if not engine_dir.is_dir():
        return check.refuse(
            f"{engine_dir} does not exist. There is no engine package to walk out from, "
            "so 'the engine reaches nothing' would be a statement about nothing."
        )
    if not witness_dir.is_dir():
        return check.refuse(
            f"{witness_dir} does not exist. 'The engine does not reach witness code' is "
            "VACUOUSLY true of a tree with no witness code, and vacuously true is not "
            "true. A guard that passes because its subject was deleted is the failure "
            "this refusal exists to prevent."
        )

    modules: dict = {}
    for path in sorted(package_dir.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        modules[_module_name(root, path)] = path

    roots = sorted(
        name
        for name in modules
        if name == ENGINE_PACKAGE or name.startswith(ENGINE_PACKAGE + ".")
    )
    if not roots:
        return check.refuse("the engine package contains no Python modules.")

    edges: dict = {}
    for name, path in modules.items():
        source = read_text(check, path)
        if source is None:
            continue
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            check.violation(
                path,
                exc.lineno or 0,
                "UNPARSEABLE",
                f"this application module could not be parsed ({exc.msg}), so its import "
                "edges are unknown. Unknown edges are a failure, never a pass.",
            )
            continue
        edges[name] = ModuleImports(check, path, name, tree)

    # -- walk to fixpoint -------------------------------------------------------------- #
    reached: dict = {name: (name, 0) for name in roots}
    frontier = list(roots)
    while frontier:
        current = frontier.pop()
        node = edges.get(current)
        if node is None:
            continue
        for target in sorted(node.targets):
            # Only project modules are edges. A stdlib or third-party import is not a
            # route to witness code, and following it would need the whole environment.
            candidate = target
            while candidate and candidate not in modules:
                if "." not in candidate:
                    candidate = ""
                    break
                candidate = candidate.rsplit(".", 1)[0]
            if not candidate:
                if _is_witness(target):
                    check.violation(
                        node.path,
                        0,
                        "engine reaches witness code",
                        f"`{current}` imports `{target}`, which is witness code that does "
                        "not exist as a module in this tree. The reach is real whether or "
                        "not the target resolves.",
                    )
                continue
            if candidate not in reached:
                reached[candidate] = (current, reached[current][1] + 1)
                frontier.append(candidate)

    check.asserted(len(reached))
    if len(reached) < 2:
        return check.refuse(
            f"only {len(reached)} module(s) were reached from the engine package. The "
            "import graph resolved to almost nothing, which means the walk failed rather "
            "than that the graph is clean."
        )

    # -- the assertion ----------------------------------------------------------------- #
    check.asserted()
    for name in sorted(reached):
        if not _is_witness(name):
            continue
        trail = [name]
        cursor = name
        while reached[cursor][0] != cursor and len(trail) < 20:
            cursor = reached[cursor][0]
            trail.append(cursor)
        check.violation(
            modules.get(name, root),
            0,
            "engine reaches witness code",
            "witness module `"
            + name
            + "` is REACHABLE from the engine package. Route (nearest first): "
            + " <- ".join(trail)
            + ". CD-AC-003: witnesses are side-by-side, never ingredients. A witness that "
            "is also an ingredient corroborates nothing (PID §3.4).",
        )

    witness_modules = sorted(name for name in modules if _is_witness(name))
    check.note(
        f"{len(witness_modules)} witness module(s) exist and were the subject of the "
        f"assertion: {', '.join(witness_modules)}"
    )

    return check.done(
        f"{len(modules)} modules in the application package; {len(reached)} reachable "
        f"from {len(roots)} engine module(s), walked to fixpoint"
    )


if __name__ == "__main__":
    raise SystemExit(main())
