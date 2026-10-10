"""P-J — ``admits``'s OWN ARITY-OPEN ``door(*args, **kwargs)``, ASKED THE SAME QUESTION.

``PO-DECISIONS-0013`` ruling 6 puts this on the remediation increment: *"`admits`'s own
arity-open `door(*args, **kwargs)` addressed or declared with its measured reach."*

**THE SYMMETRY THAT MAKES IT AN ITEM.** ``PO-DECISIONS-0012`` ruling 1 defended ``guarded``'s
arity-openness as LOAD-BEARING and made it the reason ``guarded`` is a net rather than a door.
``admits``'s own wrapper is arity-open too and nobody had asked the same question of it. The
door binds and checks the parameters it was DECLARED, then forwards ``*args, **kwargs`` whole:

    **IS THERE ANYTHING A CALLER CAN PASS THAT REACHES THE ENTRY POINT WITHOUT PASSING
    THROUGH THE BINDING-AND-REFUSAL LOOP?**

    PYTHONPATH=<tree>/src python3 -B variants/WO-2R3/P-J-the-admits-door-arity.py

Every row is a LIVE CALL. Exits 0 whatever it measures — an instrument that reports.
"""

from __future__ import annotations

import inspect
import sys

ROWS: list = []


def row(arm: str, question: str, answer: str) -> None:
    ROWS.append((arm, question, answer))
    print(f"  {arm:<5} {question:<52} {answer}")


def _short(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {str(exc).splitlines()[0][:110]}"


def main() -> int:
    import importlib

    admission = importlib.import_module("crash_detector.admission")
    admits = admission.admits

    print(f"tree: {admission.__file__}")
    print(f"python: {sys.version.split()[0]}")
    print()
    print("THE DOOR'S OWN ARITY IS `(*args, **kwargs)`. THE QUESTION IS WHETHER ANYTHING")
    print("REACHES THE ENTRY POINT WITHOUT PASSING THROUGH THE BINDING-AND-REFUSAL LOOP.")
    print()

    # ---------------------------------------------------------------- A. THE CONTROL.
    # The loop refuses a wrong type. Everything below is measured against this working.
    @admits(a=int)
    def plain(a):
        return "BODY RAN"

    try:
        plain("not an int")
        row("A", "a declared parameter, wrong type", "*** ADMITTED ***")
    except Exception as exc:  # noqa: BLE001
        row("A", "a declared parameter, wrong type", f"refused -> {_short(exc)}")

    # ---------------------------------------------------------------- B. AN EXTRA ARGUMENT.
    # `signature.bind` binds against the ENTRY POINT's real signature, so an argument the
    # signature has no room for cannot be bound at all.
    try:
        plain(1, "an argument the signature has no room for")
        row("B", "an argument the signature cannot hold", "*** REACHED THE BODY ***")
    except Exception as exc:  # noqa: BLE001
        row("B", "an argument the signature cannot hold", f"refused -> {_short(exc)}")

    # ---------------------------------------------------------------- C. POSITIONAL vs KEYWORD.
    # `bound.arguments` is keyed by NAME whichever way the value arrived, so both spellings
    # should reach the same refusal. A door that guarded only one spelling would be a door
    # a caller chooses to pass through.
    try:
        plain(a="not an int")
        row("C", "the same wrong type passed BY KEYWORD", "*** ADMITTED ***")
    except Exception as exc:  # noqa: BLE001
        row("C", "the same wrong type passed BY KEYWORD", f"refused -> {_short(exc)}")

    # ---------------------------------------------------------------- D. A BAD DEFAULT.
    # `apply_defaults()` runs BEFORE the loop, so a default value is a value the door has to
    # establish like any other. If it did not, a door could ship a bad value in its own
    # signature and never be called wrongly at all.
    @admits(a=int)
    def with_a_bad_default(a="not an int"):
        return "BODY RAN"

    try:
        with_a_bad_default()
        row("D", "a BAD DEFAULT, never passed by the caller", "*** ADMITTED ***  <- unguarded")
    except Exception as exc:  # noqa: BLE001
        row("D", "a BAD DEFAULT, never passed by the caller", f"refused -> {_short(exc)}")

    # ---------------------------------------------------------------- E. THE ENTRY POINT'S
    # OWN `**kwargs`. THIS IS THE ONE THE SYMMETRY POINTS AT. If the entry point is itself
    # arity-open, values arrive inside a dict. The declaration can require the DICT; it
    # cannot name what is in it.
    try:

        @admits(a=int, rest=dict)
        def entry_point_is_itself_open(a, **rest):
            return f"BODY RAN with rest={rest!r}"

        outcome = entry_point_is_itself_open(1, anything=object(), whatever="at all")
        row("E", "the ENTRY POINT's own **kwargs", f"*** {outcome} ***")
    except Exception as exc:  # noqa: BLE001
        row("E", "the ENTRY POINT's own **kwargs", f"refused -> {_short(exc)}")

    # ---------------------------------------------------------------- F. THE ENTRY POINT'S
    # OWN `*args`.
    try:

        @admits(a=int, more=tuple)
        def entry_point_takes_star_args(a, *more):
            return f"BODY RAN with more={more!r}"

        outcome = entry_point_takes_star_args(1, object(), object())
        row("F", "the ENTRY POINT's own *args", f"*** {outcome} ***")
    except Exception as exc:  # noqa: BLE001
        row("F", "the ENTRY POINT's own *args", f"refused -> {_short(exc)}")

    # ---------------------------------------------------------------- G. THE `_RECEIVER_NAMES`
    # SKIP AT MODULE LEVEL. The skip is gated on `_is_defined_in_a_class_body`, so a
    # module-level function with a parameter named `cls` should NOT be skipped.
    @admits(cls=int)
    def module_level_with_a_receiver_name(cls):
        return "BODY RAN"

    try:
        module_level_with_a_receiver_name("not an int")
        row("G", "a module-level parameter NAMED `cls`", "*** ADMITTED ***  <- skipped")
    except Exception as exc:  # noqa: BLE001
        row("G", "a module-level parameter NAMED `cls`", f"refused -> {_short(exc)}")

    # ---------------------------------------------------------------- H. AN UNDECLARED
    # PARAMETER. `_faults` is computed at DECORATION and re-checked on EVERY call.
    try:

        @admits(a=int)
        def has_an_undeclared_parameter(a, b):
            return "BODY RAN"

        has_an_undeclared_parameter(1, 2)
        row("H", "a parameter admits was not told about", "*** ADMITTED ***")
    except Exception as exc:  # noqa: BLE001
        row("H", "a parameter admits was not told about", f"refused -> {_short(exc)}")

    # ---------------------------------------------------------------- I. WHAT THE DOOR
    # BINDS AGAINST. `follow_wrapped=False` — the door reads ITS OWN entry point's signature,
    # not a wrapped one. Measured rather than read off the comment that claims it.
    @admits(a=int)
    def already_wrapped(a):
        return "BODY RAN"

    row(
        "I",
        "the signature the door binds against",
        f"{inspect.signature(already_wrapped)} (read with follow_wrapped=False)",
    )

    # ---------------------------------------------------------------- J. **THE BOUND ON
    # ARM G, MEASURED SO THIS PROBE'S CONCLUSION CANNOT OVERSTATE.**
    #
    # Arm G's refusal holds because `_signature_parameters` only skips a receiver when
    # `_is_defined_in_a_class_body(entry_point)` is True — and that reads `__qualname__`,
    # **AN ORDINARY WRITABLE ATTRIBUTE.** The fifth Assurance seat falsified that function's
    # own docstring (*"it is not something a caller can influence"*) with one assignment.
    #
    # **THIS ARM MEASURES THAT DEFECT AND DOES NOT REPAIR IT.** It is T8 CATEGORY A, it is
    # explicitly outside this increment (CD-D-153, PO-DECISIONS-0013 ruling 6's enumeration
    # does not contain it), and it receives a disposition from the Project Lead after this
    # increment banks. It is measured HERE and only here because item 5's declaration must
    # name the reach it MEASURED — and a declaration that said "a module-level `cls` is
    # established" without this bound would be understating its residue, which is this
    # project's most-found defect.
    # **METHOD NOTE AGAINST MYSELF, RECORDED BECAUSE THE F12 STANDARD DEMANDS IT.** My first
    # version of this arm was `def free_function(cls)` with `@admits(cls=int)`. It REFUSED —
    # and for THE WRONG REASON: with `cls` skipped, the declaration named a parameter that no
    # longer existed, so the door faulted as ADRIFT. **I WOULD HAVE RECORDED "THE ROUTE IS
    # REFUSED", CONTRADICTING THE FIFTH SEAT'S MEASUREMENT, ON AN ARM THAT NEVER TESTED IT.**
    # Two arms refusing for different reasons look identical in a summary table. The shape
    # below is the fifth seat's: a SECOND declared parameter, so the declaration still matches
    # the post-skip signature and there is no fault to hide behind.
    def free_function(cls, other):
        return f"BODY RAN, first argument was {cls!r}"

    control = admits(other=int)(free_function)
    try:
        control("anything", 3)
        row("J0", "CONTROL — the same door WITHOUT the assignment", "*** ADMITTED ***")
    except Exception as exc:  # noqa: BLE001
        row("J0", "CONTROL — the same door WITHOUT the assignment", f"refused -> {_short(exc)}")

    def free_function_2(cls, other):
        return f"BODY RAN, first argument was {cls!r}"

    free_function_2.__qualname__ = "Faked.free_function_2"  # ONE STRING ASSIGNMENT
    try:
        faked = admits(other=int)(free_function_2)
        outcome = faked("an object no door established", 3)
        row(
            "J",
            "the same, after ONE `__qualname__` assignment",
            f"*** {outcome} *** (T8 Cat A — MEASURED, NOT MINE TO FIX)",
        )
    except Exception as exc:  # noqa: BLE001
        row("J", "the same, after ONE `__qualname__` assignment", f"refused -> {_short(exc)}")

    print()
    print("=" * 100)
    print(f"{len(ROWS)} arm(s) measured against {admission.__file__}")
    print("=" * 100)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
