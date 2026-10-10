#!/usr/bin/env python3
"""THE DECLARED **NETS** — the second asserted population of CD-RT-002-DOORS-REQUIRE-THEIR-TYPES.

``PO-DECISIONS-0012`` ruling 2, verbatim:

    *"A second declared population is created: NETS — function-local post-condition guards on
    judgement paths — enumerated and asserted exactly as doors are, each with its
    post-condition named. 'Not a door' must never again mean 'not seen.' Zero unclassified
    interceptors on any judgement path."*

WHY THIS FILE EXISTS AT ALL
---------------------------
Before ``PO-DECISIONS-0012`` the doors instrument had exactly two answers about a callable:
DOOR, or nothing. ``guarded`` — the CD-ASR-F03 post-condition wrapper — was answered
"nothing", and "nothing" was indistinguishable from "not looked at". **THE RULING'S SENTENCE
IS THE WHOLE SPECIFICATION: "NOT A DOOR" MUST NEVER AGAIN MEAN "NOT SEEN."**

WHAT A ROW HERE ASSERTS, AND IT IS NOT A LABEL
-----------------------------------------------
A ``DeclaredNet`` is **DATA THAT THE INSTRUMENT CHECKS AGAINST THE CODE**, not a sentence
describing the code. ``check_judgement_path_doors.py`` FAILS if any of these is false:

1. the net **EXISTS** — an unreachable function-local callable is found inside the declared
   ``enclosing`` function in the declared module. A declared net that no longer exists is a
   violation (``NET_DECLARED_BUT_ABSENT``), not a stale row nobody notices;
2. the declared ``post_condition`` is **DEFINED AT MODULE LEVEL** in the declared module
   (``NET_POST_CONDITION_UNRESOLVABLE``);
3. **THE NET'S BODY ACTUALLY CALLS IT** (``NET_POST_CONDITION_NOT_CALLED``). This is the
   assertion that makes the row data rather than prose: a maintainer who deletes the call
   and leaves this file alone breaks the build, which is the only definition of "named" that
   survives contact with an editor;
4. the post-condition **IS ITSELF AN ``admits`` DOOR** (``NET_POST_CONDITION_NOT_A_DOOR``).
   A net exists to check what a body returned. A post-condition that does not establish its
   own arguments is a net that believes whatever the body hands it, which is the failure it
   was written to prevent, one layer in.

**AND THE ASSERTION IN THE OTHER DIRECTION, WHICH IS THE ONE THE RULING IS ACTUALLY ABOUT:**
every function-local callable the doors instrument finds on a judgement path and DECLINES to
make a door subject must appear here. One that does not is ``UNCLASSIFIED_INTERCEPTOR`` and
the check exits 1. **SET EQUALITY, BOTH DIRECTIONS, EXACTLY AS THE RULING SAYS.**

WHAT THIS FILE IS NOT
---------------------
**IT IS NOT AN EXEMPTION LIST AND ADDING A ROW HERE IS NOT A WAY TO SILENCE A VIOLATION.**
A callable only becomes eligible for a row by being UNREACHABLE under the instrument's
reachability clause; a reachable callable is a DOOR and no row here changes that. If you are
reading this file looking for somewhere to put something that is failing, you are in the
wrong file and the answer is `@admits`.
"""

from __future__ import annotations

from typing import NamedTuple


class DeclaredNet(NamedTuple):
    """One function-local post-condition guard on a judgement path.

    ``module``
        the module path relative to ``src/``, e.g. ``crash_detector/engine/evaluate.py``.

    ``enclosing``
        **THE IDENTITY OF THE NET, AND IT IS DELIBERATELY *NOT* THE NET'S OWN NAME.** The
        dotted path, from module level, of the function the net is defined INSIDE — e.g.
        ``_absence_is_never_a_number``.

        The first version of this register keyed on the net's own qualname
        (``_absence_is_never_a_number.guarded``) and **THAT VERSION FAILED THIS PROJECT'S
        RENAME TEST, MEASURED**: renaming the function-local ``guarded`` to ``_guarded`` —
        two lines, no behaviour change — took the check from PASS to FAIL with
        ``NET_DECLARED_BUT_ABSENT``, because the register was identifying its member by an
        identifier NO CALLER CAN NAME. That is the same defect ``PO-DECISIONS-0012`` ruling 2
        corrected in the membership clause, reintroduced one file away, in the fix for it.

        Keying on the ENCLOSING function fixes it, and the reason is not cosmetic: the
        enclosing function is a MODULE-LEVEL name, which is a name a reader can look up and a
        caller can reference, so depending on it is depending on something real. The net's
        own leaf name is REPORTED by the instrument and is load-bearing for nothing.

        If an enclosing function ever holds MORE THAN ONE unreachable local, the instrument
        refuses with ``AMBIGUOUS_NET`` rather than guessing which one this row means.

    ``post_condition``
        **THE NAME OF THE CALLABLE THAT IS THE POST-CONDITION.** Module-level in ``module``,
        and CALLED in the net's body. Not a description of one.

    ``what_it_refuses``
        prose, and it is the only prose field. It is for a reader and the instrument checks
        NOTHING about it — said here so nobody mistakes it for a control.

    ``what_it_does_not_bind``
        **THE DECLARED RESIDUE (CD-RULE-004).** What the post-condition does NOT see. This
        is prose too, and it is here rather than in a comment because a net's blind spot is
        the first thing a reader of this file needs and the last thing anyone writes down.
    """

    module: str
    enclosing: str
    post_condition: str
    what_it_refuses: str
    what_it_does_not_bind: str


#: THE DECLARED NETS. Deny-by-default: a function-local callable on a judgement path that is
#: not reachable under a public binding and is not declared here FAILS THE CHECK.
DECLARED_NETS: "tuple[DeclaredNet, ...]" = (
    DeclaredNet(
        module="crash_detector/engine/evaluate.py",
        enclosing="_absence_is_never_a_number",
        post_condition="refuse_a_number_without_its_inputs",
        what_it_refuses=(
            "a value-bearing Reading from a dial whose declared required inputs were not all "
            "present. CD-ASR-F03's whole runtime closure: it never asks where the number came "
            "from, so a literal, a module-level constant, a configuration default and a "
            "magnitude carried across an outage all fail identically."
        ),
        what_it_does_not_bind=(
            "**EVERYTHING PAST THE THIRD ARGUMENT, AND THAT IS MEASURED RATHER THAN ASSUMED.** "
            "The net's signature is (spec, usable, now_utc, *extra, **extra_by_name); the "
            "post-condition reads THREE things (spec, usable, reading). `now_utc`, `*extra` and "
            "`**extra_by_name` are bound by NOTHING here. `*extra` carries `model`, which is "
            "what `compute` executes to produce the magnitude, while the post-condition's "
            "premise reads `spec.model_ref` — A NAME ON THE SPEC, NOT THE OBJECT THAT DECIDES "
            "THE NUMBER. Measured at increment 7 by "
            "variants/WO-2R3/P-F-can-anything-reach-the-net-without-a-door.py arms B1a-B2c: no "
            "`*extra` model can change what the evaluator RETURNS at this tree, because every "
            "member of the closed MappingKind set raises in `compute` — **SO THE BOUND IS "
            "`compute`'s OWN DOOR AND A MAPPING SET WITH NO COMPUTING MEMBER (CD-D-005 OWED), "
            "AND NOT THIS NET.** When a computing mapping lands, this residue is live and must "
            "be re-measured (CD-ENG-WO2R3-03-F03)."
        ),
    ),
)
