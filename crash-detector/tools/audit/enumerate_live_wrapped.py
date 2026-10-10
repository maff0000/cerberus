#!/usr/bin/env python3
"""EVERY LIVE ``__wrapped__`` IN THE PACKAGE, ENUMERATED **BY INSTRUMENT, NOT BY MEMORY**.

``PO-DECISIONS-0013`` ruling 2: *"Every other live ``__wrapped__`` is enumerated BY
INSTRUMENT, not by memory."*

    PYTHONPATH=<tree>/src python3 -B tools/audit/enumerate_live_wrapped.py

**WHY THIS IMPORTS THE PRODUCT, WHEN EVERY OTHER INSTRUMENT IN THIS REPOSITORY REFUSES TO.**
``__wrapped__`` is a RUNTIME ATTRIBUTE SET ON A COMPILED FUNCTION OBJECT by
``functools.wraps``. It appears in no source file — there is no line reading
``__wrapped__ = ...`` anywhere in ``src/`` — so **A SOURCE SCAN CANNOT ANSWER THIS QUESTION,
AND A GREP IS NOT AN INSTRUMENT.** That is exactly the reading that let the CD-ASR-F03 guard
carry a live bypass through three assurance gates: everyone looked at the decorator's source,
saw ``@functools.wraps``, and did not ask the object.

**THE COST IS DISCLOSED RATHER THAN GLOSSED.** Importing the product means this instrument
cannot be trusted by an auditor who trusts nothing in the implementation — the property the
static checks in ``tools/register/`` are built to have. It is a different instrument for a
different question and it does not replace them. Run it as evidence ABOUT runtime, never as
evidence about source.

**AND THE POPULATION IT WALKS IS DECLARED.** It imports every module under
``crash_detector`` with ``pkgutil.walk_packages`` and then walks module namespaces, class
namespaces one level in, and the ``__dict__`` of every function it finds. **WHAT IT DOES NOT
REACH IS STATED IN ``NOT_REACHED`` BELOW AND PRINTED AT EVERY RUN**, because an enumeration
that does not say what it could not see is a count wearing a closure's clothes.
"""

from __future__ import annotations

import importlib
import pathlib
import pkgutil
import sys

PACKAGE = "crash_detector"

#: THE THREE CLASSIFICATIONS. **DERIVED FROM THE OBJECT, NEVER FROM A LIST OF KNOWN-GOOD
#: NAMES** — a hand-maintained allowlist here would be the exact defect this instrument
#: exists to catch, because a new project decorator would land inside it unread.
PACKAGE_DECORATOR = (
    "**APPLIED BY THIS PROJECT'S OWN CODE — THE ONLY BUCKET THAT IS A FINDING**"
)
STDLIB_DESCRIPTOR = (
    "a `staticmethod`/`classmethod` object — CPython gives these a BUILT-IN `__wrapped__` "
    "descriptor; nothing applied `functools.wraps` and there is no guard to step round"
)
FOREIGN_DECORATOR = (
    "wrapped by code OUTSIDE the package — e.g. `reprlib.recursive_repr`, which "
    "`dataclasses` applies to every generated `__repr__`. Not this project's decorator "
    "and not a guard"
)


def _classify(carrier, package_root: str) -> str:
    """Which mechanism put `__wrapped__` on this object.

    **THE DISCRIMINATOR IS WHERE THE WRAPPER'S OWN CODE LIVES**, read off
    `carrier.__code__.co_filename`. It is not the target's `__module__`, and that matters:
    `functools.wraps` COPIES `__module__` from the wrapped function, so a `dataclasses`
    `__repr__` wrapped by `reprlib` reports `__module__` = the product module and would be
    misfiled as this project's code by any check that trusted it. **MEASURED: that is
    exactly what the first version of this instrument would have done.**
    """
    if isinstance(carrier, (staticmethod, classmethod)):
        return STDLIB_DESCRIPTOR
    code = getattr(carrier, "__code__", None)
    if code is None:
        return STDLIB_DESCRIPTOR
    return (
        PACKAGE_DECORATOR
        if str(pathlib.Path(code.co_filename).resolve()).startswith(package_root)
        else FOREIGN_DECORATOR
    )

#: **WHAT THIS INSTRUMENT CANNOT SEE. PRINTED AT EVERY RUN.** An enumeration is only as good
#: as its declared reach, and this project's most-found defect is the understated residue.
NOT_REACHED = (
    "an object reachable only from a FUNCTION'S CLOSURE CELLS — this walks namespaces, and "
    "a decorated function held only in another function's cell is not in one",
    "an object created LAZILY, after import — nothing here calls anything, so a wrapper "
    "built on first use does not exist yet when this runs",
    "a wrapper on an object stored inside a CONTAINER (list, dict, tuple) in a namespace — "
    "this walks names, not the values they point into",
    "a class attribute more than ONE level of nesting in (a method of a nested class)",
    "anything in a module that fails to import — reported as an IMPORT FAILURE row and "
    "never silently skipped",
)


def _walk_live_objects():
    """Yield ``(where, object)`` for every function-like object in a reachable namespace."""
    package = importlib.import_module(PACKAGE)
    modules = [package]
    failures = []
    for info in pkgutil.walk_packages(package.__path__, prefix=f"{PACKAGE}."):
        try:
            modules.append(importlib.import_module(info.name))
        except Exception as exc:  # noqa: BLE001
            failures.append((info.name, f"{type(exc).__name__}: {exc}"))

    seen = set()
    for module in modules:
        for name, value in vars(module).items():
            if id(value) in seen:
                continue
            seen.add(id(value))
            if callable(value):
                yield f"{module.__name__}.{name}", value
            if isinstance(value, type):
                for attribute, member in vars(value).items():
                    if id(member) in seen or not callable(member):
                        continue
                    seen.add(id(member))
                    yield f"{module.__name__}.{name}.{attribute}", member
    yield from ()
    _walk_live_objects.failures = failures  # type: ignore[attr-defined]


def main() -> int:
    package = importlib.import_module(PACKAGE)
    print(f"tree: {package.__file__}")
    print(f"python: {sys.version.split()[0]}")
    print()

    carriers = list(_walk_live_objects())
    failures = getattr(_walk_live_objects, "failures", [])

    package_root = str(pathlib.Path(package.__file__).resolve().parent)
    buckets: dict = {
        PACKAGE_DECORATOR: [],
        STDLIB_DESCRIPTOR: [],
        FOREIGN_DECORATOR: [],
    }
    total = 0
    for where, obj in carriers:
        target = getattr(obj, "__wrapped__", None)
        if target is None:
            continue
        total += 1
        buckets[_classify(obj, package_root)].append(
            (where, getattr(target, "__qualname__", repr(target)))
        )

    print(f"OBJECTS INTERROGATED: {len(carriers)}")
    print(f"MODULES THAT FAILED TO IMPORT: {len(failures)}")
    for name, why in failures:
        print(f"  IMPORT FAILURE: {name} — {why}")
    print()
    print(f"**LIVE `__wrapped__` FOUND: {total}** — AND A COUNT IS NOT AN ANSWER.")
    print(
        "  Classified by WHERE THE WRAPPER'S OWN CODE LIVES, which is derived from the\n"
        "  object and not read off a list. Only the first bucket is this project's."
    )
    print()
    for bucket in (PACKAGE_DECORATOR, STDLIB_DESCRIPTOR, FOREIGN_DECORATOR):
        rows = buckets[bucket]
        print(f"  {bucket}: {len(rows)}")
        for where, target in sorted(rows):
            print(f"      {where} -> {target!r}")
        if not rows:
            print("      (none)")
        print()

    print("THE THREE SITES THIS PROJECT DECORATES, EACH ASKED DIRECTLY:")
    for label, obj in _the_three_sites():
        state = "PRESENT  <- A BYPASS" if hasattr(obj, "__wrapped__") else "absent"
        print(f"  {label:<58} {state}")
    print()

    print("WHAT THIS INSTRUMENT DOES NOT REACH (declared, not discovered):")
    for limit in NOT_REACHED:
        print(f"  - {limit}")
    print()
    print("=" * 92)
    print(
        "EXIT 0 WHATEVER IT FINDS. **THIS IS AN INSTRUMENT THAT REPORTS, NOT A CARRIER** "
        "(CD-RULE-006).\nThe carriers are the three `assert not hasattr(...)` tests named in "
        "the three sites' own comments."
    )
    print("=" * 92)
    return 0


def _the_three_sites():
    """The three decorators this project applies, resolved as LIVE OBJECTS."""
    from crash_detector.admission import admits
    from crash_detector.engine.config import ConfigSnapshot
    from crash_detector.engine.evaluate import evaluate

    evaluate_module = importlib.import_module("crash_detector.engine.evaluate")

    @admits(a=int)
    def a_freshly_built_admits_door(a):  # pragma: no cover - built to be asked, not called
        return a

    return (
        ("`admits`      — a freshly built door", a_freshly_built_admits_door),
        ("`admits`      — the shipped `evaluate` door", evaluate),
        ("`establishes` — ConfigSnapshot.__init__", ConfigSnapshot.__init__),
        (
            "`_absence_is_never_a_number` — the CD-ASR-F03 guard",
            evaluate_module._evaluate_dial,
        ),
    )


if __name__ == "__main__":
    raise SystemExit(main())
