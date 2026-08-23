#!/usr/bin/env python3
"""CD-RT-002-SEALED-AGAINST-FORGED-ESTABLISHMENT.

    python3 -B tools/register/check_sealed_against_forged_establishment.py --root <subject tree>
    python3 -B tools/register/check_sealed_against_forged_establishment.py --root . --why

CRITERION: ``PO-DECISIONS-0016`` **ruling 2**, authored by the Product Owner, quoted in full
because it is the whole of this file's authority:

    *"THE CLASS OF 99 IS SEALED — INCREMENT 9, BEFORE THE SEVENTH SEAT (Q2/F-06-J).
    CD-PL-F104 and CD-D-166 are ADDED: the sealing property (no ``__new__`` +
    ``__dict__.update`` route around establishment) is required of the CLASS —
    instrument-enumerated over all 99 governed classes, exclusions MEASURED AND DECLARED
    never assumed, a plant in the established contrast form. Fourth widening, same law:
    floors are not populations, and a remedy applied to 13 of 99 is a census with extra
    steps."*

====================================================================================
THE PROPERTY. IT IS PRINTED AT EVERY RUN SO A READER CAN DISAGREE WITH IT WITHOUT
READING THIS SOURCE.
====================================================================================

**A GOVERNED CLASS MUST NOT BE CONSTRUCTIBLE WITH FORGED STATE BY A ROUTE THAT EXECUTES NO
PACKAGE CODE.**

Not *"cannot be forged"* — no in-process guard can say that, and this file does not. The
property is about **WHO REFUSED**. If a route reaches an object of the exact governed type,
carrying attacker-supplied field values, and **NOT ONE LINE under** ``src/crash_detector/``
executed, then this package decided nothing and its establishment boundary was not
consulted — it was walked around. That is precisely what ``@establishes`` exists to prevent.

``variants/WO-2R3/P-E23-what-the-in-package-execution-sentence-gets-wrong.py`` arm 1 counted
it with :func:`sys.settrace` and the numbers are the reason this check exists::

    LINES OF PACKAGE CODE EXECUTED BY THAT  : 0
    type(smuggled) is exactly Agrees        : True
    smuggled.as_of_utc                      : 'not a datetime'
    CONTROL — the same values through Agrees(...): REFUSED TypeError, 36 LINES

**36 LINES THROUGH THE FRONT DOOR AND A REFUSAL; 0 LINES AROUND IT AND AN OBJECT.**

====================================================================================
THIS FILE IMPORTS THE SUBJECT. ITS SIBLING DELIBERATELY DOES NOT, AND THE DIFFERENCE
IS DECLARED RATHER THAN LEFT TO BE NOTICED.
====================================================================================

``check_constructor_field_establishment.py`` PARSES. It says so, and its reason is good: an
auditor who trusts nothing in the implementation can run it against a tree they extracted
themselves. **THIS CHECK CANNOT DO THAT, BECAUSE THE PROPERTY IS A RUNTIME PROPERTY.**
``__dictoffset__`` is a C-level slot on the type object; ``__setstate__`` is installed by
``dataclasses._add_slots`` AFTER the class body has been read; and *"executes no package
code"* is a statement about execution. **EVERY ESCAPE ON THIS PROJECT'S RECORD PASSED A
STATIC CHECKER.** So this file constructs the objects, reads the exception types and the
messages, and names the layer that refused from the FAILURE TEXT rather than the exit code.

**WHAT THAT COSTS, SAID PLAINLY (DECLARED LIMIT 1).** Importing the subject executes the
subject's module-level code. A tree whose import raises is a tree this check REFUSES on
(exit 3), not one it passes. An auditor who will not import an untrusted tree should run
this in a container and should not pretend the parse-only sibling proves the same thing.

====================================================================================
THE ENUMERATION IS *REUSED*, NOT COPIED — AND WHAT HAPPENS WHEN THE TWO DISAGREE.
====================================================================================

The dispatch required this to be said, and it is said: **THE POPULATION IS OBTAINED BY
IMPORTING ``check_constructor_field_establishment`` FROM THE SUBJECT TREE AND CALLING ITS OWN
``_classes()``** over the same file set (every ``*.py`` under ``src/crash_detector`` that is
not in a ``__pycache__``). It is not a transcription of 99 names and it is not a
reimplementation of its traversal. **A HARD-CODED LIST OF 99 NAMES ROTS AT THE NEXT CLASS
ANYONE ADDS**, and a reimplementation is a second opinion pretending to be a first.

That is derivation ONE. Derivation TWO is INDEPENDENT and it is the one the import buys:
after each module is imported, its ``vars()`` are descended and every class whose
``__module__`` is that module is recorded, at any nesting depth. **ONE READING IS OF THE
SOURCE TEXT AND THE OTHER IS OF THE LIVE OBJECT GRAPH.** They can disagree in both
directions and both directions are real:

* IN THE SOURCE AND NOT LIVE — a class inside ``if False:``, inside a function, or one a
  decorator replaced with something that is not a class;
* LIVE AND NOT IN THE SOURCE — a class built by ``type(...)``, by ``exec``, or by a
  decorator, which no source reading can see.

**WHEN THEY DISAGREE THIS CHECK RAISES A VIOLATION AND EXITS NON-ZERO.** It does not adopt
either reading, it does not take the union, and it does not take the intersection: a
disagreement between two derivations of one population IS the finding, and smoothing it is
the defect ``CD-RULE-009`` exists to stop. The two sets are printed in full, both
directions, at every run.

====================================================================================
THE DECLARED ROUTE SET, AND WHY IT GREW.
====================================================================================

``R1`` ``cls.__new__(cls)`` then ``__dict__.update(...)`` — the route the record names.
``R2`` ``object.__new__(cls)`` then ``__dict__.update(...)`` — the same, walking past an
       overridden ``__new__``.
``R3`` ``copyreg._reconstructor(cls, object, None)`` then ``__dict__.update(...)`` — what
       :mod:`pickle` protocols 0 and 1 do, reached from an untrusted byte string.
``R4`` ``cls.__new__(cls)`` then ``__setstate__(state)`` — the sibling the ruling names,
       with ``state`` keyed by the class's OWN slot or field names, because a
       ``__setstate__`` that indexes state by field name refuses an unrelated key **for the
       wrong reason**, and a contrast arm that fails for the wrong reason proves nothing
       (``F09``, ``F15``, the ``CD-ENG-WO2R3-F12`` standard).

**R2 AND R3 ARE IN THE SET BECAUSE A MEASUREMENT CONTRADICTED THE SET.** With R1 alone, five
``enum.Enum`` subclasses report *"the route does not reach an instance"* — ``Enum.__new__()``
demands a value — and **R2 FORGES EVERY ONE OF THEM.** The set grew because it was measured
wrong, which is the only reason a set is allowed to grow on this project.

**DECLARED LIMIT 2: THE ROUTE SET IS DECLARED, NOT PROVED COMPLETE.** A route nobody has
thought of is invisible to this check exactly as it is to every other guard here. A green run
means *"none of these four reached an object"*, and it means nothing wider.

====================================================================================
EXCLUSIONS ARE MEASURED PROPERTIES. THERE IS ONE, AND IT IS PROVED BY CONSTRUCTION.
====================================================================================

``PO-DECISIONS-0012`` ruling 2 removed vocabularies from this project's instruments, and the
dispatch restated it: *"AN EXCLUSION MUST BE A MEASURED PROPERTY OF THE CLASS, NOT A NAME ON
A LIST."* **THIS FILE CONTAINS NO LIST OF EXCLUDED CLASSES AND NO LIST OF EXCLUDED BASES.**

**THE ONE EXCLUSION — THE SEAL IS PHYSICALLY UNAVAILABLE.** For each class, the base that
imposes an instance ``__dict__`` is located by walking ``__mro__`` and reading
``__dictoffset__``. Then a **THROWAWAY SUBCLASS OF THAT BASE IS BUILT AT RUN TIME, DECLARING
``__slots__ = ()``, AND ITS ``__dictoffset__`` IS READ**. If it is still non-zero, no
declaration anywhere can seal any subclass of that base, and the class is EXCLUDED — with the
base named, the probe's measured number printed, and a further condition: **the base must be
OUTSIDE this package**, because a base we own carrying a ``__dict__`` is our defect to fix
and not our exclusion to claim.

*"It is ``AdmissionFault``"* is a list entry. *"A probe subclass of ``builtins.BaseException``
declaring ``__slots__ = ()`` still reports ``__dictoffset__ == 16``"* is a measurement, taken
on this interpreter, on this run. **EVERY EXCLUDED CLASS PRINTS ITS OWN MEASUREMENT.** If a
future interpreter makes ``BaseException`` sealable, this check requires the seal of those 43
classes on the very next run, with no edit.

**DECLARED LIMIT 3 — THE RESIDUE, NAMED HONESTLY (``CD-RULE-006``).** The excluded classes are
NOT safe. They are UNSEALABLE. Every one of them can still be reached by at least one route
in the set. **THAT RESIDUE IS NOT PROVED TO BE CARRIED ANYWHERE**, and a green run of this
check is not evidence about it. The counts are printed unconditionally so that "not required"
can never mean "not looked at".

**DECLARED LIMIT 4 — WHAT A SEALED VERDICT DOES NOT SAY.** It says the four routes did not
reach an object carrying forged state. It says NOTHING about a subclass of that class (which
carries no seal of its own — the same shape as ``establishment.py``'s DECLARED LIMIT 4),
nothing about what a caller can do with a legitimately-constructed instance, and nothing
about the ``CD-BP-003`` door, which hands in-package execution to any caller and is measured
in ``establishment.py``'s own declared limit.

**DECLARED LIMIT 5 — THIS CHECK REPORTS; IT IS NOT THE CARRIER.** The runtime contrast that
proves the route FAILS is ``tests/test_sealed_against_forged_state.py`` and the plant
``plants/CD-AC-002/CD-RT-002-SEALED-AGAINST-FORGED-ESTABLISHMENT.patch``. A check that both
measures a property and is the only thing that would notice its removal is one instrument
wearing two hats.

**DECLARED LIMIT 6 — THERE IS NO IMPORT-TIME REFUSAL, AND THAT IS DELIBERATE AND DATED.** A
class added without ``__slots__`` imports cleanly; nothing in the package objects, and this
boundary check is what catches it. An import-time guard was BUILT
(``src/crash_detector/sealing.py``) and REMOVED, because a new package module enters the
Class-2 sweep's import closure and could only be dispositioned in
``tools/sweep/declared_dispositions.py``, which ``PO-DECISIONS-0017`` ruling 2 protected until
after the seventh Assurance seat. **DEFERRED WITH A REASON, NOT DROPPED.**

*This limit was stated in the execution contract and NOT in this header, which is
``CD-RULE-004``'s own defect in the file that cites the rule. Carried here by
``CD-ENG-WO2R3-09`` (finding ``CD-ENG-WO2R3-09-F02``) with no change of meaning.*

====================================================================================
**DECLARED LIMIT 7 — WHAT THE WORD "SEALED" MEANS IN THIS INSTRUMENT'S OWN EXIT, AND
IT IS NOT THE ENGLISH WORD. THIS LIMIT IS PRINTED AFTER THE VERDICT ON EVERY RUN.**
====================================================================================

``PO-DECISIONS-0018`` ruling 1(b), the Product Owner's own bytes, carried into
``BLUEPRINT`` §16 ``CD-D-172`` and §17 ``CD-BP-005``:

    *"SEALED means sealed against declared routes; NOT sealed against deliberate in-process
    forgery, which the platform does not permit preventing. A green board that says exactly
    that is honest; a green board that says more is the sixth false green."*

**A DOCSTRING IS NOT AN EXIT.** DECLARED LIMITS 1–5 above have been true and unread since
this file was written, because a reader runs the check and reads its last line. So this
limit is not only written here: :func:`main` prints it to stdout **AFTER** the ``PASS``/
``FAIL`` line, **on every exit path including a precondition refusal**, with **THIS RUN'S
OWN MEASURED NUMBERS IN IT.**

**AND THE NUMBERS ARE MEASURED, NOT ASSERTED (``CD-RULE-003``).** Two further routes are
EXECUTED against every class on every run — see :data:`OUT_OF_SCOPE_ROUTES` — and what they
reach is counted and printed:

``F1`` ``cls.__new__(cls)`` then ``object.__setattr__(instance, member, FORGED)``
``F2`` ``type.__new__(<metatype>, name, bases, namespace)`` — forging the TYPE, not the
       value; attempted only where the governed class IS itself a metatype.

**THEY ARE NOT IN** :data:`ROUTES` **AND THEY DO NOT MOVE THE VERDICT, DELIBERATELY.**
Appending them to the declared set and calling the class closed is what the Product Owner
named *the census game* and ruled out in ruling 1: *"an enumeration cannot close a
property-defined class — and this class is defined by a platform property we do not
control."* And scoring them would make this check permanently RED for ``object.__setattr__``
and ``type.__new__``, **which are CPython working as documented** — a red that no edit to
this package could ever clear, reported as though it were a defect somebody could fix.
So they are measured, printed, and **declared OUT OF SCOPE** (§17 ``CD-BP-005``: HIGH,
ACCEPTED AND DECLARED). What they buy is that the limit carries a NUMBER instead of an
adjective.

**AND THE RESIDUE OF THAT MEASUREMENT IS SPLIT BY REASON, BECAUSE A ROUTE THAT FAILS FOR
THE WRONG REASON SCORES A CLASS CLOSED** (the ``CD-ENG-WO2R3-F12`` standard, which
:func:`_r5` already exists because of). A class ``F1`` does not forge is reported as one of:

* ``FORGED`` — exact type, forged value read back, zero package lines;
* ``NO STATE TO FORGE`` — the object WAS reached, with exact type and zero package lines,
  but the class declares no ``__slots__`` member and no dataclass field for the probe to
  write. **"NOT FORGED" IS VACUOUSLY TRUE OF A STATELESS OBJECT AND IS NOT A SEAL.**
  Counting these as survivors is exactly how a defensible-looking number is manufactured;
* ``NOT REACHED`` — the constructor itself refused, with the exception type and message
  printed, so a reader can judge whether it refused for the right reason.

**WHAT THIS CHECK STILL DOES NOT CLAIM AFTER ALL OF THAT.** It does not claim any governed
class is sealed against deliberate in-process forgery; it claims the opposite, with a count.
It does not claim ``CD-ASR-WO2R3-04-F01``, ``CD-AC-002`` or ``CD-AC-005`` is closed. The
defence against deliberate in-process forgery is **DETECTION** — witness divergence and the
provenance chain, the FORGERY-DETECTION OBLIGATION owed at **WO-3** as a first-class
criterion (§16 ``CD-D-172``) — **and it is not built yet.** Meanwhile the blast radius is
what §17 says it is: the detector is ADVISORY (``D1``) and no money moves on it (``D2``).
"""

from __future__ import annotations

import copyreg
import importlib
import importlib.util
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _support import Check, parse_root, resolve_root  # noqa: E402

CHECK_ID = "CD-RT-002-SEALED-AGAINST-FORGED-ESTABLISHMENT"

#: Every module whose ``__module__`` begins with this is PACKAGE CODE. The whole property
#: turns on it: "no package code ran" is what makes a route a bypass rather than a refusal.
PACKAGE = "crash_detector"

#: A value no governed type would ever legitimately hold, so a forged read is unambiguous.
FORGED = "FORGED — this value passed through no establishment boundary"

#: The name of the sibling instrument whose derivation is REUSED. Named once, here, so that
#: a rename is one edit and not a hunt.
SIBLING = "check_constructor_field_establishment"


# --------------------------------------------------------------------------------------- #
# LOADING THE SUBJECT TREE. CD-PL-F98: A CONTRAST RUN WITH THE WRONG TREE ON `sys.path` IS
# INDISTINGUISHABLE FROM A FIX THAT DOES NOTHING.
# --------------------------------------------------------------------------------------- #

def _load_subject(check: Check, root: pathlib.Path):
    """Import the SUBJECT tree's package and its sibling instrument, or refuse.

    Every imported module's ``__file__`` is VERIFIED to live under ``root``. A
    ``crash_detector`` already importable from somewhere else — the developer's checkout, an
    installed wheel, the tree this process was started in — would otherwise be measured while
    the report named the subject, which is ``CD-PL-F98`` exactly.
    """
    package_root = root / "src" / PACKAGE
    if not package_root.is_dir():
        return None, None, check.refuse(
            f"{package_root} is not a directory. --root must be the repository root of the "
            "tree under audit, not the package directory."
        )
    sibling_path = root / "tools" / "register" / f"{SIBLING}.py"
    if not sibling_path.is_file():
        return None, None, check.refuse(
            f"{sibling_path} does not exist. This check REUSES that instrument's own "
            "enumeration rather than reimplementing it, so a subject tree without it is a "
            "tree this check cannot enumerate."
        )

    # Evict anything already imported under these names, then put the SUBJECT first.
    for name in list(sys.modules):
        if name == PACKAGE or name.startswith(PACKAGE + ".") or name == SIBLING:
            del sys.modules[name]
    sys.path.insert(0, str(root / "src"))
    sys.path.insert(0, str(root / "tools" / "register"))
    try:
        sibling = importlib.import_module(SIBLING)
        package = importlib.import_module(PACKAGE)
    except Exception as exc:  # noqa: BLE001 — an unimportable subject is a refusal, not a pass
        return None, None, check.refuse(
            f"importing the subject tree raised {type(exc).__name__}: {exc}. This check "
            "measures a RUNTIME property and cannot report one about a tree that does not "
            "import. This is a non-zero exit with a stated reason, never a skip."
        )

    for module, label in ((sibling, "the sibling instrument"), (package, "the package")):
        where = pathlib.Path(getattr(module, "__file__", "") or "").resolve()
        if root.resolve() not in where.parents:
            return None, None, check.refuse(
                f"{label} resolved to {where}, which is NOT under the subject tree {root}. "
                "Refusing rather than measuring the wrong tree (CD-PL-F98)."
            )
    return sibling, package, 0


def _module_name(relative: pathlib.PurePath) -> str:
    parts = relative.with_suffix("").parts
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join((PACKAGE,) + tuple(parts))


# --------------------------------------------------------------------------------------- #
# THE DECLARED ROUTE SET.
# --------------------------------------------------------------------------------------- #

def _state_for(cls: type) -> dict:
    """The state offered to ``__setstate__``, keyed by the class's OWN member names.

    Slot names first, then declared dataclass field names, then a fallback marker. A
    ``__setstate__`` that indexes by field name and is handed an unrelated key raises
    ``KeyError`` — a refusal for the WRONG REASON, which would score the class sealed when it
    is not. Both mangled and unmangled spellings of a private slot are offered, because
    ``__slots__ = ('__quantity',)`` becomes ``_Cls__quantity`` on the instance.
    """
    names: list = []
    for name in getattr(cls, "__slots__", ()) or ():
        names.append(name)
        if name.startswith("__") and not name.endswith("__"):
            names.append(f"_{cls.__name__.lstrip('_')}{name}")
    fields = getattr(cls, "__dataclass_fields__", None)
    if isinstance(fields, dict):
        names.extend(fields)
    if not names:
        names = ["__cd_forged__"]
    return {name: FORGED for name in names}


def _r1(cls: type):
    subject = cls.__new__(cls)
    subject.__dict__.update({"__cd_forged__": FORGED})
    return subject


def _r2(cls: type):
    subject = object.__new__(cls)
    subject.__dict__.update({"__cd_forged__": FORGED})
    return subject


def _r3(cls: type):
    subject = copyreg._reconstructor(cls, object, None)
    subject.__dict__.update({"__cd_forged__": FORGED})
    return subject


def _r4(cls: type):
    subject = cls.__new__(cls)
    subject.__setstate__(_state_for(cls))
    return subject


def _r5(cls: type):
    """``__setstate__`` handed a POSITIONAL state, which is what the stdlib one expects.

    **THIS ROUTE EXISTS BECAUSE R4 ALONE MEASURED THIS INSTRUMENT'S OWN SUBJECT WRONG AND
    SCORED IT SEALED.** CPython's ``dataclasses._dataclass_setstate`` — the one
    ``@dataclass(frozen=True, slots=True)`` installs — is::

        def _dataclass_setstate(self, state):
            for field, value in zip(fields(self), state):
                object.__setattr__(self, field.name, value)

    It ZIPS. Handed a mapping it iterates the KEYS, so ``StalenessWindow.__setstate__(
    {'seconds': FORGED})`` sets ``seconds`` to the string ``'seconds'`` — an object that is
    forged in fact and does not carry the marker this check reads back, so R4 reported
    *"forged value readable False"* and the class was scored **SEALED WHEN IT IS NOT**.
    Handed a sequence it forges exactly as intended.

    **A ROUTE THAT FAILS FOR THE WRONG REASON SCORES A CLASS CLOSED, WHICH IS THE
    ``CD-ENG-WO2R3-F12`` STANDARD FAILING INSIDE THE INSTRUMENT THAT CITES IT.** Both shapes
    are offered because both exist in this tree: ``DialMagnitude.__setstate__`` and
    ``DeclaredQuantity.__setstate__`` INDEX BY NAME and need the mapping; the stdlib one ZIPS
    and needs the sequence.
    """
    subject = cls.__new__(cls)
    subject.__setstate__(list(_state_for(cls).values()))
    return subject


ROUTES = {
    "R1 cls.__new__(cls) + __dict__.update": _r1,
    "R2 object.__new__(cls) + __dict__.update": _r2,
    "R3 copyreg._reconstructor + __dict__.update": _r3,
    "R4 cls.__new__(cls) + __setstate__(MAPPING state)": _r4,
    "R5 cls.__new__(cls) + __setstate__(SEQUENCE state)": _r5,
}


# --------------------------------------------------------------------------------------- #
# THE OUT-OF-SCOPE PERIMETER MEASUREMENT — DECLARED LIMIT 7.
#
# **THESE ARE NOT IN `ROUTES`, THEY ARE NOT ASSERTED, AND THEY DO NOT MOVE THE VERDICT.**
# They exist so that the declared limit this file prints after its verdict carries a MEASURED
# NUMBER rather than an adjective. See DECLARED LIMIT 7 in the module docstring for why
# scoring them would be both the census game (PO-DECISIONS-0018 ruling 1) and a red that no
# edit to this package could ever clear.
# --------------------------------------------------------------------------------------- #

def _declared_members(cls: type) -> list:
    """Every member name the class ITSELF declares — slots (mangled and not) and fields.

    Distinct from :func:`_state_for`, which substitutes a fallback marker when a class
    declares nothing. **THE DIFFERENCE IS THE POINT:** an EMPTY list here means the class has
    no state to forge, and *"nothing was forged"* is then vacuously true rather than a seal.
    """
    names: list = []
    for name in getattr(cls, "__slots__", ()) or ():
        names.append(name)
        if name.startswith("__") and not name.endswith("__"):
            names.append(f"_{cls.__name__.lstrip('_')}{name}")
    fields = getattr(cls, "__dataclass_fields__", None)
    if isinstance(fields, dict):
        names.extend(fields)
    return list(dict.fromkeys(names))


def _f1(cls: type):
    """``cls.__new__(cls)`` then ``object.__setattr__`` — the value forged on the instance.

    ``object.__setattr__`` bypasses ``__setattr__`` overrides, ``@dataclass(frozen=True)``'s
    included, and writes a ``__slots__`` descriptor directly. Names that refuse are skipped
    rather than aborting the route: a class with one writable member is forged.
    """
    subject = cls.__new__(cls)
    for name in _declared_members(cls) or ["__cd_forged__"]:
        try:
            object.__setattr__(subject, name, FORGED)
        except Exception:  # noqa: BLE001 — an unwritable member is simply not this route's
            continue
    return subject


def _f2(cls: type):
    """``type.__new__(<metatype>, ...)`` — the TYPE forged, not a value on an instance.

    Attempted only where ``cls`` is itself a metatype. This is the second half of the pair
    ``BLUEPRINT`` §17 ``CD-BP-005`` names by name, and without it the four sealed metatypes
    of this tree report *"not forged"* against ``F1`` for the WRONG REASON — their
    ``__new__`` wants ``(name, bases, namespace)`` and refuses an instance-shaped call.
    """
    return type.__new__(cls, f"_forged_{cls.__name__}", (), {"__cd_forged__": FORGED})


OUT_OF_SCOPE_ROUTES = (
    ("F1 cls.__new__(cls) + object.__setattr__(member)", _f1, False),
    ("F2 type.__new__(<metatype>, name, bases, namespace)", _f2, True),
)


def _perimeter(cls: type) -> list:
    """EXECUTE the out-of-scope routes. ``[(label, verdict, detail)]``, verdict never scored.

    ``verdict`` is one of ``FORGED``, ``NO STATE TO FORGE``, ``NOT FORGED`` or
    ``NOT REACHED``. The three non-``FORGED`` words are kept APART on purpose: collapsing
    them into one *"survived"* bucket is how eleven classes that carry no state and four
    metatypes called with the wrong argument shape become *"eleven sealed classes"*.
    """
    out: list = []
    for label, route, metatype_only in OUT_OF_SCOPE_ROUTES:
        if metatype_only and not (isinstance(cls, type) and issubclass(cls, type)):
            continue
        subject, error, package_lines = _traced(lambda cls=cls, route=route: route(cls))
        if error is not None:
            first = str(error).splitlines()[0][:140] if str(error) else ""
            out.append((
                label, "NOT REACHED",
                f"the constructor itself REFUSED {type(error).__name__}: {first} "
                f"(package lines executed {package_lines}). **READ THE REASON: a route that "
                "fails for the wrong reason scores a class closed.**",
            ))
            continue
        forged = _forged_reachable(subject, cls)
        if forged and package_lines == 0:
            out.append((
                label, "FORGED",
                f"REACHED an object; exact type {type(subject) is cls}; forged value read "
                f"back True; package lines executed {package_lines}",
            ))
        elif not _declared_members(cls):
            out.append((
                label, "NO STATE TO FORGE",
                f"REACHED an object; exact type {type(subject) is cls}; package lines "
                f"executed {package_lines} — but this class declares NO __slots__ member and "
                "NO dataclass field, so there is nothing for the probe to write. "
                "**`NOT FORGED` IS VACUOUSLY TRUE OF A STATELESS OBJECT AND IS NOT A SEAL.**",
            ))
        else:
            out.append((
                label, "NOT FORGED",
                f"REACHED an object; exact type {type(subject) is cls}; package lines "
                f"executed {package_lines}; none of {len(_declared_members(cls))} declared "
                "member(s) read back the forged marker",
            ))
    return out


def _traced(work):
    """Run ``work``, COUNTING the lines executed under the package with ``sys.settrace``.

    The property is *"executes no package code"*. A property about execution is measured by
    tracing execution — never by reading source and reasoning about it.
    """
    executed = 0

    def trace(frame, event, _arg):
        nonlocal executed
        name = frame.f_globals.get("__name__", "")
        if event == "line" and (name == PACKAGE or name.startswith(PACKAGE + ".")):
            executed += 1
        return trace

    previous = sys.gettrace()
    sys.settrace(trace)
    try:
        result, error = None, None
        try:
            result = work()
        except BaseException as exc:  # noqa: BLE001 — every refusal is a datum here
            error = exc
    finally:
        sys.settrace(previous)
    return result, error, executed


def _forged_reachable(subject, cls: type) -> bool:
    """Did a forged value actually LAND somewhere readable on ``subject``?

    An object that came back but carries none of the offered values is NOT a forgery: some
    ``__setstate__`` implementations discard what they are given. Read it back rather than
    assuming the write took (``runtime claims need runtime proof``).
    """
    if type(subject) is not cls:
        return False
    for name in ("__cd_forged__", *_state_for(cls)):
        try:
            if getattr(subject, name) == FORGED:
                return True
        except Exception:  # noqa: BLE001 — an unreadable member is simply not forged
            continue
    return False


def _measure(cls: type) -> dict:
    """EXECUTE every declared route against ``cls`` and report what each one did."""
    report = {}
    for label, route in ROUTES.items():
        subject, error, package_lines = _traced(lambda cls=cls, route=route: route(cls))
        if error is not None:
            report[label] = {
                "forged": False,
                "package_lines": package_lines,
                "outcome": f"REFUSED {type(error).__name__}: {error}",
            }
            continue
        forged = _forged_reachable(subject, cls)
        report[label] = {
            "forged": bool(forged and package_lines == 0),
            "package_lines": package_lines,
            "outcome": (
                f"REACHED an object; exact type {type(subject) is cls}; forged value "
                f"readable {forged}; package lines executed {package_lines}"
            ),
        }
    return report


# --------------------------------------------------------------------------------------- #
# THE ONE EXCLUSION, MEASURED BY CONSTRUCTION.
# --------------------------------------------------------------------------------------- #

def _dict_imposed_by(cls: type):
    """The base that gives ``cls`` instances a ``__dict__``, or ``None`` if it is its own."""
    imposer = None
    for base in cls.__mro__[1:]:
        if base.__dictoffset__:
            imposer = base
    return imposer


def _probe_subclass(base: type) -> type:
    """Build a throwaway subclass of ``base`` declaring ``__slots__ = ()``.

    **THROUGH THE BASE'S OWN METACLASS PROTOCOL, NOT THROUGH A PLAIN ``type(...)`` CALL.** The
    first draft of this function called ``type(base)(name, (base,), {...})`` with an ordinary
    dict, and five ``enum.Enum`` subclasses came back ``AttributeError: 'dict' object has no
    attribute '_member_names'`` — reported as UNMEASURABLE, which is honest but is not an
    answer. ``EnumMeta.__prepare__`` returns an ``_EnumDict``, and a metaclass that declares
    ``__prepare__`` is entitled to be given what it asked for. Asking the metaclass for its own
    namespace is the general form and it costs nothing on a metaclass that has none.

    Recorded rather than quietly fixed: **an instrument that reports UNMEASURABLE because it
    called the wrong constructor has measured its own defect and labelled it a property of the
    subject.** That is the shape of ``CD-PL-F113`` and it is why this docstring exists.
    """
    metaclass = type(base)
    name = f"_probe_{base.__name__}"
    prepare = getattr(metaclass, "__prepare__", None)
    namespace = prepare(name, (base,)) if prepare is not None else {}
    namespace["__slots__"] = ()
    return metaclass(name, (base,), namespace)


def _seal_availability(cls: type):
    """``(available, base, probe_dictoffset, reason)`` — BUILT AND READ, NEVER ASSERTED.

    Constructs a throwaway subclass of the base that imposes the ``__dict__``, declaring
    ``__slots__ = ()``, and reads the result. This is the whole of the exclusion clause and
    it is a run-time measurement of the interpreter in front of it.
    """
    imposer = _dict_imposed_by(cls)
    if imposer is None:
        return True, None, None, "no base imposes a __dict__ — the seal is this class's own to declare"
    try:
        probe = _probe_subclass(imposer)
    except Exception as exc:  # noqa: BLE001
        return (
            None,
            imposer,
            None,
            f"UNMEASURABLE: a probe subclass of {imposer.__module__}.{imposer.__qualname__} "
            f"could not be built ({type(exc).__name__}: {exc}), so neither availability nor "
            "unavailability is established. Reported as unmeasured rather than guessed.",
        )
    offset = probe.__dictoffset__
    if offset:
        return (
            False,
            imposer,
            offset,
            f"a probe subclass of {imposer.__module__}.{imposer.__qualname__} declaring "
            f"__slots__ = () STILL reports __dictoffset__ == {offset}, so no declaration on "
            "any subclass of that base can remove the instance __dict__",
        )
    return (
        True,
        imposer,
        offset,
        f"a probe subclass of {imposer.__module__}.{imposer.__qualname__} declaring "
        f"__slots__ = () reports __dictoffset__ == 0, so the seal IS available",
    )


def _is_ours(base) -> bool:
    module = getattr(base, "__module__", "") or ""
    return module == PACKAGE or module.startswith(PACKAGE + ".")


def _extra(parser) -> None:
    parser.add_argument(
        "--why",
        action="store_true",
        help=(
            "print the verdict, the measured exclusion clause and every route's outcome for "
            "EVERY class examined. The counts are printed either way; this prints the ledger "
            "behind them."
        ),
    )


def _main() -> int:
    arguments = parse_root(
        CHECK_ID,
        "Every governed class this tree declares is SEALED against construction with forged "
        "state by a route that executes no package code — or carries a MEASURED exclusion, "
        "proved by constructing a probe subclass at run time and reading its __dictoffset__ "
        "(PO-DECISIONS-0016 ruling 2).",
        extra=_extra,
    )
    root, code = resolve_root(CHECK_ID, arguments.root)
    if root is None:
        return code
    check = Check(check_id=CHECK_ID, root=root)

    sibling, _package, code = _load_subject(check, root)
    if sibling is None:
        return code

    package_root = root / "src" / PACKAGE
    files = sorted(
        path for path in package_root.rglob("*.py") if "__pycache__" not in path.parts
    )
    if not files:
        return check.refuse(f"no *.py found under {package_root}.")

    # --- DERIVATION ONE: the sibling instrument's OWN _classes(), reused, not copied ----- #
    import ast

    from_source: dict = {}
    for path in files:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            check.violation(path, getattr(exc, "lineno", 0) or 0, "UNPARSEABLE", str(exc))
            continue
        relative = path.relative_to(package_root)
        for qualname, node in sibling._classes(tree):
            from_source[(str(relative), qualname)] = (path, node.lineno)

    # --- DERIVATION TWO: the LIVE object graph, independent of any source reading -------- #
    from_live: dict = {}
    for path in files:
        relative = path.relative_to(package_root)
        name = _module_name(relative)
        try:
            module = importlib.import_module(name)
        except Exception as exc:  # noqa: BLE001
            return check.refuse(
                f"importing {name} from the subject tree raised {type(exc).__name__}: "
                f"{exc}. A module inside the scanned set that will not import is a refusal, "
                "not a file to pass over."
            )
        seen: set = set()

        def descend(container, prefix: str) -> None:
            for attribute, value in list(vars(container).items()):
                if not isinstance(value, type):
                    continue
                if getattr(value, "__module__", None) != name:
                    continue
                qualname = getattr(value, "__qualname__", attribute)
                if qualname in seen:
                    continue
                seen.add(qualname)
                from_live[(str(relative), qualname)] = value
                descend(value, qualname)

        descend(module, "")

    only_source = sorted(set(from_source) - set(from_live))
    only_live = sorted(set(from_live) - set(from_source))
    check.note(
        "THE POPULATION IS ASSERTED, NOT PRINTED. TWO INDEPENDENT DERIVATIONS ARE DIFFED AS "
        f"SETS AT EVERY RUN: the SOURCE reading — {SIBLING}._classes(), that instrument's OWN "
        f"traversal, REUSED and not reimplemented — finds {len(from_source)}; the LIVE reading "
        f"— vars() descent over the imported modules, at any nesting depth — finds "
        f"{len(from_live)}. IN THE SOURCE AND NOT LIVE: {len(only_source)}. LIVE AND NOT IN "
        f"THE SOURCE: {len(only_live)}. EITHER IS A VIOLATION BELOW, NOT A NOTE."
    )
    for key in only_source:
        check.violation(
            package_root / key[0], 0, "ENUMERATIONS DISAGREE",
            f"{key[1]} is found by the SOURCE reading and NOT by the LIVE reading. A class "
            "in the parsed AST that never reaches a live object is a class this check cannot "
            "measure the property of — a class inside `if False:`, inside a function, or one "
            "a decorator replaced. It is NOT adopted from either reading and it is NOT "
            "dropped.",
        )
    for key in only_live:
        check.violation(
            package_root / key[0], 0, "ENUMERATIONS DISAGREE",
            f"{key[1]} is a LIVE class of this module that the SOURCE reading does not find "
            "— built by type(), by exec, or by a decorator. It is inside the governed "
            "population by every runtime test and outside it by every static one.",
        )

    # --- THE MEASUREMENT ---------------------------------------------------------------- #
    required_sealed: list = []
    required_open: list = []
    excluded: list = []
    unmeasurable: list = []
    ledger: list = []

    # DECLARED LIMIT 7 — the out-of-scope perimeter, measured. NOT asserted, NOT scored.
    perimeter_forged: list = []
    perimeter_no_state: list = []
    perimeter_not_reached: list = []
    perimeter_not_forged: list = []
    perimeter_ledger: list = []

    for key in sorted(set(from_source) & set(from_live)):
        relative, qualname = key
        cls = from_live[key]
        _path, lineno = from_source[key]
        report = _measure(cls)
        forging = sorted(label for label, fact in report.items() if fact["forged"])
        available, base, probe_offset, reason = _seal_availability(cls)
        where = f"{relative}:{lineno} {qualname}"

        perimeter = _perimeter(cls)
        perimeter_ledger.append((where, perimeter))
        verdicts = {verdict for _label, verdict, _detail in perimeter}
        if "FORGED" in verdicts:
            perimeter_forged.append(where)
        elif verdicts == {"NO STATE TO FORGE"}:
            perimeter_no_state.append(where)
        elif "NOT FORGED" in verdicts:
            perimeter_not_forged.append(where)
        else:
            perimeter_not_reached.append(where)

        if not forging:
            check.asserted()
            required_sealed.append(where)
            ledger.append((
                where, "SEALED",
                f"no declared route reached an object of exactly this type carrying forged "
                f"state with zero package lines. __dictoffset__ == {cls.__dictoffset__}.",
                report,
            ))
            continue

        # It forges. Is the seal PHYSICALLY AVAILABLE to it? MEASURED, not assumed.
        if available is None:
            check.asserted()
            unmeasurable.append(where)
            ledger.append((where, "UNMEASURABLE", reason, report))
            check.violation(
                package_root / relative, lineno, "SEAL AVAILABILITY UNMEASURABLE",
                f"{qualname} is open to {forging} and whether the seal is available to it "
                f"could not be measured. {reason} An unmeasured exclusion is not an "
                "exclusion (PO-DECISIONS-0012 ruling 2).",
            )
            continue

        if not available and base is not None and not _is_ours(base):
            check.asserted()
            excluded.append((where, base, probe_offset, forging))
            ledger.append((
                where, "EXCLUDED — SEAL PHYSICALLY UNAVAILABLE",
                f"{reason}. The base is OUTSIDE this package "
                f"({base.__module__}.{base.__qualname__}), so the __dict__ is not ours to "
                f"remove. STILL OPEN TO: {forging}. THAT RESIDUE IS NOT PROVED TO BE CARRIED "
                "ANYWHERE.",
                report,
            ))
            continue

        check.asserted()
        required_open.append((where, forging))
        ours = base is not None and _is_ours(base)
        ledger.append((
            where, "OPEN — AND REQUIRED",
            (f"the seal IS available to it ({reason})" if base is None or not ours else
             f"the base that imposes the __dict__ is OUR OWN "
             f"({base.__module__}.{base.__qualname__}), which is a defect to fix and never "
             f"an exclusion to claim"),
            report,
        ))
        detail = "; ".join(f"{label} -> {report[label]['outcome']}" for label in forging)
        check.violation(
            package_root / relative, lineno, "OPEN TO FORGED STATE",
            f"{qualname} is a governed class that the sealing property is REQUIRED of, and "
            f"{len(forging)} declared route(s) reach an object of exactly this type carrying "
            f"forged field values having executed ZERO lines of package code: {detail}. "
            "Declare `__slots__` naming its members, and verify `__dictoffset__` is 0. If "
            "@dataclass(slots=True) is used, the stdlib __setstate__ it installs must be "
            "removed — it writes any state it is handed with no package code at all.",
        )

    total = len(from_source | from_live.keys())
    check.note(
        f"THE PROPERTY: A GOVERNED CLASS MUST NOT BE CONSTRUCTIBLE WITH FORGED STATE BY A "
        f"ROUTE THAT EXECUTES NO PACKAGE CODE. Measured by EXECUTING {len(ROUTES)} declared "
        f"routes against every class and counting package lines with sys.settrace — never by "
        f"reading source. THE ROUTE SET IS DECLARED, NOT PROVED COMPLETE (DECLARED LIMIT 2): "
        + " | ".join(ROUTES)
    )
    check.note(
        f"CLASSES EXAMINED: {total}. SEALED: {len(required_sealed)}. OPEN AND REQUIRED: "
        f"{len(required_open)}. EXCLUDED BY MEASUREMENT: {len(excluded)}. UNMEASURABLE: "
        f"{len(unmeasurable)}. "
        f"{len(required_sealed)} + {len(required_open)} + {len(excluded)} + "
        f"{len(unmeasurable)} = "
        f"{len(required_sealed) + len(required_open) + len(excluded) + len(unmeasurable)}. "
        "**THE ARITHMETIC IS PRINTED BECAUSE F-06-J's TABLE CLOSED AT 90 OF 99 AND NOTHING "
        "SAID SO.**"
    )
    check.note(
        "THE EXCLUSION IS ONE CLAUSE AND IT IS A MEASURED PROPERTY, NEVER A NAME ON A LIST: "
        "a throwaway subclass of the base that imposes the instance __dict__ is BUILT at run "
        "time with __slots__ = (), its __dictoffset__ is READ, and the class is excluded only "
        "if that number is non-zero AND the base is outside this package. Every excluded "
        "class prints its own measurement below. If a future interpreter makes such a base "
        "sealable, this check requires the seal of those classes on the next run, with no "
        "edit to this file."
    )
    by_base: dict = {}
    for _where, base, probe_offset, _forging in excluded:
        by_base.setdefault(f"{base.__module__}.{base.__qualname__}", [0, probe_offset])[0] += 1
    for base_name, (count, probe_offset) in sorted(by_base.items()):
        check.note(
            f"  EXCLUDED, {count} class(es): the __dict__ is imposed by {base_name}; a probe "
            f"subclass declaring __slots__ = () measures __dictoffset__ == {probe_offset} on "
            f"this interpreter ({sys.version.split()[0]}). NOT SAFE — UNSEALABLE. "
            "NOT PROVED TO BE CARRIED ANYWHERE (CD-RULE-006)."
        )
    check.note(
        "DERIVATION DISAGREEMENT IS A VIOLATION AND NEVER A RECONCILIATION: this check does "
        "not adopt the source reading, does not adopt the live reading, does not take the "
        "union and does not take the intersection of them for its VERDICT — it measures the "
        "intersection and FAILS on the difference, so a class only one reading can see is "
        "reported rather than quietly assigned to a side."
    )

    # --- DECLARED LIMIT 7 — THE OUT-OF-SCOPE PERIMETER, IN NUMBERS -------------------- #
    sealed_set = set(required_sealed)
    forged_set = set(perimeter_forged)
    sealed_and_forged = sorted(sealed_set & forged_set)
    sealed_and_not_forged = sorted(sealed_set - forged_set)
    LIMIT_7.update({
        "examined": total,
        "sealed": len(required_sealed),
        "forged": len(perimeter_forged),
        "no_state": len(perimeter_no_state),
        "not_reached": len(perimeter_not_reached),
        "not_forged": len(perimeter_not_forged),
        "sealed_and_forged": len(sealed_and_forged),
        "sealed_and_not_forged": len(sealed_and_not_forged),
        "sealed_survivors_no_state": len([w for w in sealed_and_not_forged
                                          if w in set(perimeter_no_state)]),
        "sealed_survivors_not_reached": len([w for w in sealed_and_not_forged
                                             if w in set(perimeter_not_reached)]),
        "routes": len(ROUTES),
    })
    check.note(
        "DECLARED LIMIT 7 — THE OUT-OF-SCOPE PERIMETER, MEASURED ON THIS RUN AND NOT SCORED: "
        f"{len(perimeter_forged)} of {total} class(es) examined were FORGED by a route that is "
        "NOT in the declared set — F1 cls.__new__(cls) + object.__setattr__(member), F2 "
        "type.__new__(<metatype>, ...) — exact type, forged value read back, ZERO package "
        f"lines. THAT INCLUDES {len(sealed_and_forged)} OF THE {len(required_sealed)} THIS "
        "CHECK CALLS SEALED. These routes do NOT move the verdict and are NOT counted as "
        "assertions: object.__setattr__ and type.__new__ are CPython working as documented, "
        "and BLUEPRINT §17 CD-BP-005 declares preventing them OUT OF SCOPE (HIGH, ACCEPTED "
        "AND DECLARED). Adding them to the declared set and calling the class closed is the "
        "census game (PO-DECISIONS-0018 ruling 1)."
    )
    check.note(
        f"AND THE {len(sealed_and_not_forged)} SEALED CLASS(ES) THE OUT-OF-SCOPE ROUTES DID "
        "NOT FORGE ARE SPLIT BY REASON, BECAUSE A ROUTE THAT FAILS FOR THE WRONG REASON "
        "SCORES A CLASS CLOSED: "
        f"{LIMIT_7['sealed_survivors_no_state']} declare NO __slots__ member and NO dataclass "
        "field, so there is NOTHING TO FORGE and 'not forged' is VACUOUSLY TRUE — that is not "
        f"a seal; {LIMIT_7['sealed_survivors_not_reached']} REFUSED THE CONSTRUCTOR CALL, each "
        "with its exception type and message in the --why ledger. **NOT ONE CLASS IN THIS TREE "
        "IS MEASURED SEALED AGAINST DELIBERATE IN-PROCESS FORGERY, AND THIS CHECK DOES NOT "
        "CLAIM ONE IS.**"
    )

    if getattr(arguments, "why", False):
        check.note("THE FULL LEDGER — every class examined, with its verdict and its routes:")
        for where, verdict, reason, report in ledger:
            check.note(f"  {verdict:<34} {where} — {reason}")
            for label, fact in report.items():
                check.note(f"        {label} -> {fact['outcome']}")
        check.note(
            "THE OUT-OF-SCOPE PERIMETER LEDGER (DECLARED LIMIT 7) — not scored, not asserted:"
        )
        for where, perimeter in perimeter_ledger:
            for label, verdict, detail in perimeter:
                check.note(f"  {verdict:<20} {where} — {label} -> {detail}")

    return check.done(
        f"{len(files)} module(s) under src/{PACKAGE}; {total} class(es) examined; "
        f"{len(required_sealed)} SEALED AGAINST THE {len(ROUTES)} DECLARED ROUTES "
        f"(of which {len(sealed_and_forged)} are FORGED by the out-of-scope in-process "
        f"routes — see DECLARED LIMIT 7 printed after this verdict), "
        f"{len(required_open)} OPEN AND REQUIRED, "
        f"{len(excluded)} EXCLUDED BY MEASUREMENT, {len(unmeasurable)} UNMEASURABLE"
    )


# --------------------------------------------------------------------------------------- #
# THE EXIT CARRIES THE DECLARED LIMIT. **A DOCSTRING IS NOT AN EXIT.**
#
# `PO-DECISIONS-0018` ruling 1(b): *"The instrument's exit carries its declared limit ... A
# green board that says exactly that is honest; a green board that says more is the sixth
# false green."*
#
# `Check.done` in `_support.py` prints `PASS — N assertions, 0 violations` and that module is
# NOT this seat's to edit, so the limit is printed AFTER it, from here, in a `finally`, so it
# survives every exit path — clean, violation, usage, precondition refusal and an unhandled
# exception. A reader who runs this check and reads its LAST LINES is told what SEALED means.
# --------------------------------------------------------------------------------------- #

#: Filled in by :func:`_main` when the measurement is reached. **EMPTY MEANS NOT MEASURED**,
#: and the block below says so rather than printing a number it does not have (`CD-RULE-003`).
LIMIT_7: dict = {}


def _declared_limit_text() -> str:
    if LIMIT_7:
        measured = (
            f"    * NOT that a governed value cannot be forged in-process. IT CAN, AND THIS RUN\n"
            f"      MEASURED IT: {LIMIT_7['forged']} of the {LIMIT_7['examined']} classes examined were forged by\n"
            f"      `cls.__new__(cls)` + `object.__setattr__` or by `type.__new__(<metatype>, ...)`\n"
            f"      — exact type, forged value read back, ZERO lines of package code —\n"
            f"      INCLUDING {LIMIT_7['sealed_and_forged']} OF THE {LIMIT_7['sealed']} THIS CHECK CALLS SEALED.\n"
            f"    * NOT that the remaining {LIMIT_7['sealed_and_not_forged']} are sealed either. They are the residue of a\n"
            f"      route that did not reach them, split by reason and never pooled:\n"
            f"      {LIMIT_7['sealed_survivors_no_state']} declare NO member for a probe to write, so `not forged` is\n"
            f"      VACUOUSLY TRUE OF A STATELESS OBJECT; {LIMIT_7['sealed_survivors_not_reached']} refused the constructor call.\n"
            f"      **NOT ONE CLASS IN THIS TREE IS MEASURED SEALED AGAINST DELIBERATE\n"
            f"      IN-PROCESS FORGERY. THE HONEST COUNT OF THOSE IS ZERO.**\n"
        )
        claim = (
            f"  WHAT IT CLAIMS: none of the {LIMIT_7['routes']} DECLARED routes reached an object of exactly a\n"
            f"    governed type carrying a forged value while executing zero lines of\n"
            f"    src/crash_detector/. Where that holds it is REAL, and it proofs the product\n"
            f"    against ACCIDENT and casual misuse — which is what ruling 1(a) keeps it for.\n"
        )
    else:
        measured = (
            "    * NOT that a governed value cannot be forged in-process. IT CAN. **NO PERIMETER\n"
            "      MEASUREMENT WAS TAKEN ON THIS RUN** — the check exited before reaching it —\n"
            "      so no number is printed here rather than a number this run did not derive.\n"
        )
        claim = (
            "  WHAT IT CLAIMS ON THIS RUN: NOTHING. The check did not complete a measurement.\n"
        )
    return (
        "\n"
        "================================================================================\n"
        "DECLARED LIMIT 7 — PRINTED AFTER THE VERDICT, ON EVERY RUN, PASS OR FAIL.\n"
        "CD-RT-002-SEALED-AGAINST-FORGED-ESTABLISHMENT\n"
        "================================================================================\n"
        "  WHAT `SEALED` MEANS ABOVE, and it is NOT the English word:\n"
        "\n"
        "      SEALED AGAINST DECLARED ROUTES; **NOT** SEALED AGAINST DELIBERATE IN-PROCESS\n"
        "      FORGERY, WHICH THE PLATFORM DOES NOT PERMIT PREVENTING.\n"
        "\n"
        "    — PO-DECISIONS-0018 ruling 1(b), the Product Owner's own bytes, carried into\n"
        "      BLUEPRINT §16 CD-D-172 and §17 CD-BP-005.\n"
        "\n"
        + claim +
        "\n"
        "  WHAT IT DOES NOT CLAIM, AND NO RUN OF IT EVER WILL:\n"
        "    * NOT that the class is closed. An enumeration cannot close a property-defined\n"
        "      class, and this class is defined by a platform property we do not control.\n"
        "      The route set is DECLARED, NOT PROVED COMPLETE (DECLARED LIMIT 2).\n"
        + measured +
        "    * NOT that CD-ASR-WO2R3-04-F01 is closed, that CD-AC-002 or CD-AC-005 are\n"
        "      closed, or that any gate is open. This check closes no finding and no gate.\n"
        "\n"
        "  OUT OF SCOPE, DECLARED AND NOT PRETENDED (BLUEPRINT §17 CD-BP-005 — HIGH,\n"
        "  ACCEPTED AND DECLARED): preventing an in-process actor from constructing the\n"
        "  object at all. `object.__setattr__` and `type.__new__` are CPython working as\n"
        "  documented. Appending them to the declared set and calling the class closed is\n"
        "  the census game and is ruled out (PO-DECISIONS-0018 ruling 1).\n"
        "\n"
        "  WHERE THE DEFENCE ACTUALLY LIVES: **DETECTION** — witness divergence and the\n"
        "  provenance chain, the FORGERY-DETECTION OBLIGATION owed at WO-3 as a first-class\n"
        "  criterion (BLUEPRINT §16 CD-D-172). **IT IS NOT BUILT YET.** Blast radius\n"
        "  meanwhile is what §17 states: the detector is ADVISORY (D1) and no money moves\n"
        "  on it (D2). Prevention is reserved for Layer 3, out-of-process.\n"
        "================================================================================"
    )


def main() -> int:
    try:
        return _main()
    finally:
        print(_declared_limit_text())


if __name__ == "__main__":
    raise SystemExit(main())
