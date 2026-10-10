#!/usr/bin/env python3
"""CD-RT-002-EXACT-TYPE-ADMISSION — a forged metatype subclass is REFUSED at the door.

    python3 tools/register/check_exact_type_admission.py --root <subject tree>

CRITERION: CD-AC-002, and `PO-DECISIONS-0018` ruling 2 in its own words — *"EXACT TYPE,
everywhere on a judgement path where an `isinstance` still survives — sites enumerated BY
INSTRUMENT, the forged-subclass probe as the plant, both arms."*

===========================================================================================
**WHAT THIS CHECK CLOSES, AND WHAT IT DOES NOT — CD-RULE-004, IN THE FIRST SCREEN, AND SAID
THE SAME WAY IN THE REGISTER ENTRY (`required-tests.yaml`) AND IN THE EXECUTION CONTRACT
(`contracts/execution/CD-RT-002-EXACT-TYPE-ADMISSION.md`). A REGISTER ENTRY MAY NOT CLAIM
MORE THAN ITS GUARD DELIVERS.**
===========================================================================================

**IT DOES NOT CLOSE THE CLASS "A FORGED SUBCLASS CANNOT EXIST". IT DECLARES THAT LIMIT, AND
IT PROVES THE LIMIT IN ITS OWN OUTPUT AT EVERY RUN.** ARM 2 below CONSTRUCTS the forged class
on purpose and prints that it succeeded, with the count of package lines executed beside it —
**ZERO at three of the four metatypes and FOUR at `SealedReadingType`, where all four are
`SealedReadingType.__setattr__` falling through on a class that is not in `_SEALED` and NOT
ONE OF THEM IS A REFUSAL.** The count is pinned per site as a ceiling, below. That is
CPython working as documented — `type.__new__(metaclass, ...)` does not call
`metaclass.__new__` — and `PO-DECISIONS-0018` ruling 1 has settled that an enumeration cannot
close a property-defined class. **A CHECK THAT CLAIMED THE FORGERY WAS PREVENTED WOULD BE
DISPROVED BY THE LINE ABOVE ITS OWN CLAIM.**

**WHAT IT CLOSES IS THE USEFULNESS OF THE FORGERY, AT FOUR NAMED JUDGEMENT-PATH DOORS.** The
forged instance passes `isinstance` BY CONSTRUCTION and can never be made to fail it; it
fails exact type BY CONSTRUCTION and can never be made to pass it. **THAT ASYMMETRY IS THE
WHOLE REMEDY**, and this check asserts the half of it that this project controls: at each of
the four doors the forged instance is REFUSED, **with the DECLARED refusal identity for that
door** (CD-PL-F74) and not with an incidental `AttributeError` from a body that admitted it
and then tripped over it. *A refusal that arrives as a crash is not a refusal.*

**ITS DECLARED LIMITS, ENUMERATED:**

 1  **FOUR DOORS, NOT EVERY DOOR.** The subject is the four sealed metatypes named by
    `CD-ASR-WO2R3-04-F01` and ONE judgement-path door for each. The instrument that
    enumerates the whole population is `tools/sweep/delegated_judgement_sweep.py`, which is a
    different tool answering a different question, and the per-site carriers are
    `tests/test_exact_type_admission_sweep.py`. **THIS CHECK IS NOT A CENSUS AND DOES NOT
    CLAIM TO BE ONE.**
 2  **IT PROVES NOTHING ABOUT ROUTES IT DOES NOT WALK.** `object.__setattr__`,
    `cls.__new__(cls)` state forgery, `__reduce__`, `__class__` reassignment on a live object
    and `ctypes` are not exercised here. `CD-RT-002-SEALED-AGAINST-FORGED-ESTABLISHMENT` is a
    different instrument on a different property and **is not cited as support for anything
    in this file.**
 3  **IT RUNS IN-PROCESS AND IMPORTS THE SUBJECT TREE.** It is a runtime check because
    "refused" is a runtime claim, and every escape on this project's record passed a static
    checker. The cost is that it inherits whatever `--root` actually contains, which is why
    it prints the resolved `crash_detector.__file__` it imported (`CD-PL-F98`).
 4  **THE REFUSAL IDENTITIES ARE PINNED BY NAME AND THAT IS DELIBERATE.** If a refusal
    changes identity, this check goes RED and names the door. That is CD-PL-F74's rule, not
    brittleness: the identity a caller sees IS part of the contract, and three of this
    project's escapes were "the right outcome from the wrong layer".

===========================================================================================
WHAT IS ASSERTED
===========================================================================================

 CD-EXACT-ARM1-001  **THE DECLARED ROUTE IS STILL REFUSED.** For each of the four sealed
                    types, an ordinary `class Evil(V): ...` statement raises that module's
                    own surface violation. This is a REGRESSION TEST ON `PO-DECISIONS-0018`
                    RULING 1(a): *"The declared-route refusals STAND and are kept."* If a
                    change makes this arm stop refusing, the accident-proofing the Product
                    Owner explicitly kept has been broken.

 CD-EXACT-ARM2-002  **THE FORGED ROUTE STILL WORKS, AND THAT IS ASSERTED AND NOT LAMENTED.**
                    `type.__new__(M, 'Evil2', (V,), {..., '__float__': ...})` creates the
                    class; `issubclass(Evil2, V)` is True; an instance is built; `float(inst)`
                    is the forged number; `isinstance(inst, V)` is True. **IF ANY OF THESE
                    STOPS BEING TRUE THIS CHECK GOES RED**, because a check whose premise has
                    silently evaporated is measuring nothing, and its clean exit would then be
                    the sixth false green on this project.

 CD-EXACT-ARM2-003  **AND `type(inst) is V` IS FALSE.** The asymmetry, asserted as a fact
                    about the object rather than assumed as a property of the design.

 CD-EXACT-DOOR-004  **THE JUDGEMENT-PATH DOOR REFUSES THE FORGED INSTANCE, WITH THE DECLARED
                    REFUSAL IDENTITY.** One door per sealed type, named in `_DOORS` below with
                    the exception class it must raise. An admission is a violation; a refusal
                    of a DIFFERENT identity is a violation and is reported as such, with both
                    identities printed.

EXIT: 0 clean · 1 violation, with the door and the observed outcome · 2 usage ·
3 precondition not met. Never a skip, for any reason (PBG-CI-002).
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _support import Check, parse_root, resolve_root  # noqa: E402

CHECK_ID = "CD-RT-002-EXACT-TYPE-ADMISSION"

#: The forged member. A magnitude that coerces to a number is `CD-ASR-F01`'s own sentence,
#: so the probe carries the exact hazard the sealed types exist to refuse.
FORGED_NUMBER = 0.5


def _package_line_counter(package_dir: pathlib.Path):
    """Count lines of PACKAGE code executed while a callable runs. Zero is the claim."""
    prefix = str(package_dir)
    state = {"n": 0}

    def tracer(frame, event, arg):
        if frame.f_code.co_filename.startswith(prefix):
            state["n"] += 1
        return tracer

    return tracer, state


def _run_counting(package_dir: pathlib.Path, fn):
    tracer, state = _package_line_counter(package_dir)
    sys.settrace(tracer)
    try:
        result = fn()
    finally:
        sys.settrace(None)
    return result, state["n"]


def main(argv=None) -> int:
    args = parse_root(CHECK_ID, __doc__.splitlines()[0])
    root, code = resolve_root(CHECK_ID, args.root)
    if root is None:
        return code
    check = Check(CHECK_ID, root)

    src = root / "src"
    if not (src / "crash_detector" / "__init__.py").is_file():
        return check.refuse(
            f"{src}/crash_detector/__init__.py does not exist, so there is no subject to "
            "import. `refused` is a RUNTIME claim and this check will not make it against a "
            "tree it could not load."
        )

    sys.path.insert(0, str(src))
    for name in [m for m in sys.modules if m == "crash_detector" or m.startswith("crash_detector.")]:
        del sys.modules[name]

    try:
        import crash_detector  # noqa: F401
        from crash_detector.admission import NotAdmitted
        from crash_detector.dials.magnitude import (
            DialMagnitude,
            MagnitudeSurfaceViolated,
            SealedMagnitudeType,
            _established_quantity,
        )
        from crash_detector.dials.provenance import (
            DeclaredQuantity,
            QuantityProvenanceMissing,
            QuantitySurfaceViolated,
            SameDialReduction,
            SealedQuantityType,
            derived_within_one_dial,
        )
        from crash_detector.dials.reading import (
            Degraded,
            ReadingSurfaceViolated,
            SealedReadingType,
        )
        from crash_detector.serving.dial_presentation import (
            DialPresentationRefused,
            NotShown,
            SealedPresentationType,
            is_shown,
            present_dial,
        )
    except Exception as exc:  # pragma: no cover - a tree that will not import
        return check.refuse(
            f"the subject tree at {src} did not import: {type(exc).__name__}: {exc}"
        )

    package_dir = pathlib.Path(crash_detector.__file__).resolve().parent
    # CD-PL-F98: READ THE TREE LINE EVERY TIME. A contrast run with the wrong tree on
    # `sys.path` is indistinguishable from a fix that does nothing.
    check.note(f"imported crash_detector from: {package_dir / '__init__.py'}")
    check.note(f"python: {sys.version.split()[0]}")

    # (metatype, victim class, arm-1 refusal, door name, door call, declared refusal,
    #  package-line CEILING for the forged class creation)
    #
    # **THE CEILING IS PER SITE, MEASURED, AND NOT ASSUMED TO BE ZERO** — because at one of
    # the four it is NOT zero and pretending otherwise would be a fingerprint that is false
    # on the day it is written. `SealedReadingType`'s forged-class creation executes FOUR
    # lines of package code, and **NOT ONE OF THEM IS A REFUSAL**: traced line by line at
    # `686a374`, all four are `dials/reading.py` `SealedReadingType.__setattr__`, invoked by
    # `typing.Generic` machinery writing `__orig_bases__` / `__parameters__` onto the FORGED
    # class, which is not in `_SEALED` and therefore falls straight through to
    # `type.__setattr__`. The ceiling is asserted so that a package line that DID refuse — or
    # any new package code running on this path — moves the number and turns this check RED.
    doors = (
        (
            SealedMagnitudeType, DialMagnitude, MagnitudeSurfaceViolated,
            "crash_detector.dials.magnitude::_established_quantity",
            lambda inst: _established_quantity(inst),
            NotAdmitted, 0,
        ),
        (
            SealedQuantityType, DeclaredQuantity, QuantitySurfaceViolated,
            "crash_detector.dials.provenance::derived_within_one_dial",
            lambda inst: derived_within_one_dial(
                quantities=(inst,), reduction=SameDialReduction.MEAN
            ),
            QuantityProvenanceMissing, 0,
        ),
        (
            SealedReadingType, Degraded, ReadingSurfaceViolated,
            "crash_detector.serving.dial_presentation::present_dial",
            lambda inst: present_dial(dial_id="cd.availability", reading=inst),
            NotAdmitted, 4,
        ),
        (
            SealedPresentationType, NotShown, DialPresentationRefused,
            "crash_detector.serving.dial_presentation::is_shown",
            lambda inst: is_shown(inst),
            NotAdmitted, 0,
        ),
    )

    here = pathlib.Path(__file__)

    for (metatype, victim, surface_error, door_name, call, declared_refusal,
         line_ceiling) in doors:
        label = f"{metatype.__name__}/{victim.__name__}"

        # ---- ARM 1 — THE DECLARED ROUTE. RULING 1(a)'S REGRESSION TEST. ---------------- #
        check.asserted()
        namespace = {victim.__name__: victim}
        try:
            exec(f"class Evil(({victim.__name__},)[0]):\n    __slots__ = ()\n", namespace)
        except surface_error as refused:
            check.note(f"ARM 1 {label}: REFUSED {type(refused).__name__}")
        except Exception as other:
            check.violation(
                here, 0, "CD-EXACT-ARM1-001",
                f"{label}: the declared route `class Evil({victim.__name__})` raised "
                f"{type(other).__name__}, not the declared {surface_error.__name__}. The "
                "refusal identity a caller sees IS part of the contract (CD-PL-F74).",
            )
        else:
            check.violation(
                here, 0, "CD-EXACT-ARM1-001",
                f"{label}: **THE DECLARED ROUTE IS NO LONGER REFUSED.** An ordinary `class "
                f"Evil({victim.__name__})` statement SUCCEEDED. PO-DECISIONS-0018 ruling "
                "1(a) keeps these refusals as accident-proofing; this is that "
                "accident-proofing gone.",
            )

        # ---- ARM 2 — THE FORGED ROUTE. ASSERTED, NOT LAMENTED. ------------------------ #
        def make():
            return type.__new__(
                metatype, "Evil2", (victim,),
                {"__slots__": (), "__float__": lambda self: FORGED_NUMBER},
            )

        try:
            forged, class_lines = _run_counting(package_dir, make)
        except Exception as exc:
            check.asserted()
            check.violation(
                here, 0, "CD-EXACT-ARM2-002",
                f"{label}: the forged class could NOT be built ({type(exc).__name__}: "
                f"{exc}). **THIS CHECK'S PREMISE HAS EVAPORATED AND ITS CLEAN EXIT WOULD "
                "MEAN NOTHING.** If the platform or this package has genuinely closed the "
                "route, that is a product change that must be recorded and this check "
                "re-scoped — never left passing over a probe that no longer probes.",
            )
            continue

        instance, instance_lines = _run_counting(package_dir, lambda: forged.__new__(forged))

        check.asserted(6)
        premise = {
            "the forged class was created": forged is not None,
            "issubclass(Evil2, victim)": issubclass(forged, victim),
            "float(instance) is the forged number": float(instance) == FORGED_NUMBER,
            "isinstance(instance, victim)": isinstance(instance, victim),
            f"package lines for the forged class <= the measured ceiling {line_ceiling}":
                class_lines <= line_ceiling,
            "package lines for the forged INSTANCE is 0": instance_lines == 0,
        }
        for proposition, held in premise.items():
            if not held:
                check.violation(
                    here, 0, "CD-EXACT-ARM2-002",
                    f"{label}: the probe's own premise failed — {proposition!r} is False. "
                    "A check measuring a hazard that no longer exists in the shape it "
                    "describes is not evidence about anything.",
                )
        check.note(
            f"ARM 2 {label}: CREATED, package lines {class_lines} (instance "
            f"{instance_lines}) · issubclass True · float(inst) {float(instance)} · "
            f"isinstance True"
        )

        # ---- THE ASYMMETRY ------------------------------------------------------------ #
        check.asserted()
        if type(instance) is victim:
            check.violation(
                here, 0, "CD-EXACT-ARM2-003",
                f"{label}: `type(instance) is {victim.__name__}` is True for a forged "
                "subclass instance, which is the one thing this remedy relies on being "
                "False.",
            )

        # ---- CD-EXACT-DOOR-004 — THE JUDGEMENT PATH ----------------------------------- #
        check.asserted()
        try:
            admitted = call(instance)
        except declared_refusal as refused:
            first = str(refused).splitlines()[0][:96]
            check.note(
                f"DOOR {door_name}: REFUSED {type(refused).__name__}: {first}"
            )
        except Exception as other:
            check.violation(
                here, 0, "CD-EXACT-DOOR-004",
                f"{door_name}: the forged instance was refused, but by "
                f"{type(other).__name__} and NOT by the declared "
                f"{declared_refusal.__name__} — `{str(other).splitlines()[0][:120]}`. **THE "
                "RIGHT OUTCOME FROM THE WRONG LAYER IS THIS PROJECT'S MOST-REPEATED DEFECT "
                "AND IT IS A VIOLATION HERE, NOT A DETAIL.** A body that admitted the object "
                "and then tripped over a missing attribute has not refused it.",
            )
        else:
            check.violation(
                here, 0, "CD-EXACT-DOOR-004",
                f"{door_name}: **THE FORGED INSTANCE WAS ADMITTED** and the door returned "
                f"{admitted!r}. A {victim.__name__} that coerces to {FORGED_NUMBER}, built "
                "with zero lines of package code, reached a judgement path. That is "
                "CD-ASR-F01.",
            )

    check.note(
        "DECLARED LIMIT, PRINTED AT EVERY RUN: the forged subclass IS STILL CONSTRUCTIBLE — "
        "this check builds one in every ARM 2 above and says so. It does not claim the "
        "forgery is prevented, that any class is sealed, or that CD-ASR-F01 is closed. It "
        "claims that four named judgement-path doors refuse the instance by exact type."
    )

    return check.done(
        f"{len(doors)} sealed metatypes, both arms each, and "
        f"{len(doors)} judgement-path doors, in-process against {package_dir}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
