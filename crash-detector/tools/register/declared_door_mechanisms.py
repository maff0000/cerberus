#!/usr/bin/env python3
"""THE DECLARED **DERIVING MECHANISMS** — the second recognised DOOR FORM of
CD-RT-002-DOORS-REQUIRE-THEIR-TYPES.

``PO-DECISIONS-0015`` ruling 1, verbatim:

    *"(b) the door's establishment is DERIVED FROM THE SIGNATURE, preserving the property the
    old net's open arity existed for — the guard survives arity growth because it derives,
    not because it gapes"*

WHY A SECOND FORM EXISTS AT ALL
-------------------------------
``@admits(spec=DialSpec, usable=dict, now_utc=datetime)`` derives its PARAMETER LIST from the
signature and refuses any disagreement, which is planted violation P7 — but the TYPE beside
each name is HAND-WRITTEN. On the day somebody adds a parameter, an ``admits`` door FAULTS and
every call to it is refused. That is fail-closed and it is right for a door; it is **not** what
ruling 1 (b) asks of the CD-ASR-F03 guard, which must *survive* arity growth rather than fall
over on it, because the property the old net's ``*extra`` existed for was continuity of the
guard across a new argument. A mechanism that reads the ANNOTATION as the declaration keeps
both halves: the new parameter is established by exact type on the run it is added, and the
guard is not edited.

**SO THIS CHECK RECOGNISES TWO DOOR FORMS AND NEITHER IS AN EXEMPTION:**

* **FORM 1, DECLARED** — ``@admits(...)``, whose declaration is checked against the signature
  in both directions;
* **FORM 2, DERIVED** — a subject whose decorator is declared HERE, whose every parameter
  carries an ANNOTATION, and which has NO variadic parameter. Those two artefact properties
  are exactly what the mechanism itself refuses at import, read statically so an auditor does
  not have to import the product to see them.

WHAT A ROW HERE ASSERTS, AND IT IS NOT A LABEL
-----------------------------------------------
A ``DeclaredDoorMechanism`` is **DATA THAT THE INSTRUMENT CHECKS AGAINST THE CODE**, exactly as
``declared_nets.py``'s rows are. ``check_judgement_path_doors.py`` FAILS if any of these is
false:

1. the mechanism **EXISTS** — a module-level ``def`` of that name in that module
   (``MECHANISM_DECLARED_BUT_ABSENT``);
2. it **READS THE SIGNATURE** — it, or a module-level function it calls, calls
   ``inspect.signature`` (``MECHANISM_DOES_NOT_READ_THE_SIGNATURE``). §D.1's rule is *"derived
   from the signature rather than written into the body"*; a mechanism that never reads a
   signature is not deriving from one, whatever it is called;
3. it **COMPILES THROUGH THE PROJECT'S ONE DECLARATION VOCABULARY** — it, or a module-level
   function it calls, calls ``declaration`` (``MECHANISM_DOES_NOT_USE_THE_ONE_VOCABULARY``).
   ``crash_detector.admission.declaration``'s own docstring is the reason: *"Two declaration
   vocabularies that drift apart is how a reader comes to believe a field is established as
   strictly as a parameter when it is not; there is one, and it is here."* A second vocabulary
   grown inside a mechanism would be exactly that drift, wearing this register's clothes;
4. it **DECORATES SOMETHING** (``MECHANISM_DECORATES_NOTHING``). A declared mechanism that
   decorates nothing is a row that has outlived its subject, and a register whose rows can do
   that is a hand-maintained summary.

**AND AT EVERY SUBJECT IT DECORATES**, the check asserts the two properties the derivation
requires and refuses without: every parameter ANNOTATED
(``DERIVED_DOOR_PARAMETER_NOT_ANNOTATED``) and no variadic (``OPEN_CHANNEL``, the same
violation code an ``admits`` door gets for the same shape).

WHAT THIS FILE IS NOT
---------------------
**IT IS NOT AN EXEMPTION LIST AND ADDING A ROW HERE IS NOT A WAY TO SILENCE A VIOLATION.** A
row buys a subject nothing on its own: the four assertions above run against the mechanism's
own source, and the two assertions at each decorated subject run against that subject's own
signature. If you are reading this file looking for somewhere to put something that is
failing, you are in the wrong file and the answer is ``@admits``.

**AND THE LIMIT IT INHERITS IS THE ONE ``admits`` ALREADY DECLARES.** A mechanism is
recognised by its NAME in the source, exactly as ``admits`` is — that is DECLARED LIMIT 4 of
``check_judgement_path_doors.py`` and this register does not widen it or narrow it. What it
does change is the FAILURE DIRECTION, which is the safe one: rename a declared mechanism and
the check does not stop looking, it reports ``MECHANISM_DECLARED_BUT_ABSENT`` **and** the
subject it used to cover as ``UNDECORATED_JUDGEMENT_PATH_DOOR``. Two violations, not a silence.
"""

from __future__ import annotations

from typing import NamedTuple


class DeclaredDoorMechanism(NamedTuple):
    """One decorator that MAKES a judgement-path door by deriving its establishment.

    ``module``
        the module path relative to ``src/``, e.g. ``crash_detector/engine/evaluate.py``.

    ``mechanism``
        the module-level name of the decorator. **A MODULE-LEVEL NAME**, which is a name a
        reader can look up and a caller can reference — the same identity rule
        ``declared_nets.py`` adopted after its first version failed this project's rename test
        by keying on a function-local identifier no caller can name.

    ``derives_from``
        prose naming WHAT the establishment is derived from, for a reader. The instrument
        checks NOTHING about it, and that is said here so nobody mistakes it for a control.

    ``what_it_does_not_establish``
        **THE DECLARED RESIDUE (CD-RULE-004).** What the derivation does NOT reach. Prose, and
        it is here rather than in a comment because a mechanism's blind spot is the first
        thing a reader of this file needs and the last thing anyone writes down.
    """

    module: str
    mechanism: str
    derives_from: str
    what_it_does_not_establish: str


#: THE DECLARED DERIVING MECHANISMS. Deny-by-default: a subject whose only decorator is not
#: `admits` and is not declared here is UNDECORATED_JUDGEMENT_PATH_DOOR.
DECLARED_DOOR_MECHANISMS: "tuple[DeclaredDoorMechanism, ...]" = (
    DeclaredDoorMechanism(
        module="crash_detector/engine/evaluate.py",
        mechanism="_absence_is_never_a_number",
        derives_from=(
            "the decorated callable's own RESOLVED ANNOTATIONS (typing.get_type_hints, not "
            "the annotation strings), one admission per parameter, each compiled through "
            "crash_detector.admission.declaration. A union becomes one_of(...); a "
            "subscripted generic becomes its origin; anything the one vocabulary does not "
            "recognise RAISES AT IMPORT and the module does not load. It is also the "
            "CD-ASR-F03 net: the door and the post-condition are one wrapper and one "
            "closure, which is what PO-DECISIONS-0015 ruling 1 means by 'the guard and the "
            "guarded are inseparable'."
        ),
        what_it_does_not_establish=(
            "**THE SUBSCRIPT OF A GENERIC, AND THAT IS DECLARED LIMIT 11.** `dict[str, OK]` "
            "establishes that the argument is exactly a `dict` and says nothing about its "
            "keys or its values; the element establishment on this path is "
            "`_latest_usable_ok`'s `type(outcome) is not OK`, one level up. **AND IT DOES "
            "NOT ESTABLISH TRUTH** — an exactly-typed DialSpec carrying a dishonest "
            "`required_input_ids` is admitted here and refused, if at all, somewhere else, "
            "which is admission.py's DECLARED LIMIT 3 read at this door. **AND THE BODY IT "
            "CARRIES AS A CODE OBJECT CAN BE RECONSTITUTED** with types.FunctionType by "
            "anything that can already read the closure — DECLARED LIMIT 10, and it is "
            "CARRIED (asserted TRUE) by tests/test_the_absence_door.py rather than claimed "
            "closed."
        ),
    ),
)
