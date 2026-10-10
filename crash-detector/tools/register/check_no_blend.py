#!/usr/bin/env python3
"""CD-RT-002-AST-NO-BLEND — the two dials are never combined into one number.

    python3 tools/register/check_no_blend.py --root <subject tree>

CRITERION: CD-AC-002. PID §3.1 is CONSTITUTIONAL: "Two dials, never blended. Equity crash
and monetary/debasement fail in opposite directions; averaging cancels the signal."

WHAT THIS CHECK IS, AFTER CD-ASR-F01 (HIGH)
--------------------------------------------
**THIS CHECK IS A LOCATOR. IT IS NOT THE CLOSURE, AND IT CANNOT BE.** Read the DECLARED
LIMIT at the bottom of this header before reading a clean run as evidence of anything.

It used to be described as one of three independent refusals, and the register said "a
blend that slips past any one layer must still fail the other two". An independent auditor
REFUTED that claim BY EXECUTION: two working blends passed all three layers simultaneously
and each returned 0.5 from equity 0.9 and monetary 0.1 (`CD-ASR-F01`, escaped variants
`E01` and `E02`). Both walked past THIS check, for a reason that is structural and
permanent — flavour propagation here is INTRA-PROCEDURAL and purely STATIC, so moving the
arithmetic one call away, or reaching the attribute through ``getattr`` with a non-marker
string literal, erases the flavour entirely.

The class is now closed where it can be closed:

* AT THE TYPE — ``crash_detector.dials.magnitude.DialMagnitude``. A dial magnitude is a
  nominal, per-dial, NON-COERCIBLE value carrying its provenance as data. It defines no
  arithmetic dunder and no numeric coercion, so ``left + right``, ``sum([...])``,
  ``functools.reduce``, ``statistics.mean`` and every other reduction raise ``TypeError``
  from the interpreter regardless of how the two values were reached. Both `E01` and `E02`
  now raise when EXECUTED.
* AT THE POINT OF COMBINATION — ``combine_within_one_dial`` compares the provenance the
  magnitudes CARRY and refuses anything but a single dial, so the refusal does not depend
  on anybody having read the code. **THAT WAS TRUE AND IT WAS NOT ENOUGH.** It compared the
  DIAL SET and never the VALUE, and it handed a caller's arbitrary closure's return value to
  the derivation door — which is how `ASR2-002-A` published a blend with this check PASS on
  4873 assertions (`CD-ASR-WO2R-F01`, HIGH). Since `WO-2R2` increment 1a its ``using``
  parameter is a NAMED REDUCTION and not a callable, and the derivation door takes no number
  and no dial set at all: see boundary 8, which carries the measurement.
* AT THE DERIVATION DOOR — ``crash_detector.dials.provenance.derived_within_one_dial``
  admits only ``DeclaredQuantity`` values this system established, by EXACT TYPE, computes
  the provenance union itself, and computes the number itself from a closed set of named
  reductions. There is no argument on a derivation path through which a caller's ``float``
  or a caller's callable can arrive. ``DeclaredQuantity.__init__`` refuses always, so the
  type cannot be forged by writing its name either.
* AT THE RE-ENTRY — ``crash_detector.dials.provenance``. Added closing `CD-PL-F54`, which
  found the layers above open to the number being READ OFF a magnitude rather than asked
  for: ``float(repr(m).split("quantity=")[1].rstrip(")"))`` names no dial, two of those add,
  and the sum re-wrapped as a magnitude of one dial passed every provenance comparison and
  published. A magnitude is now built from a ``DeclaredQuantity`` and never from a bare
  ``float``, so a number that has left a magnitude by ANY exit cannot get back into one.
  MEASURED: `PL-Q4`, `PL-Q5`, `PL-Q6` and `PL-Q9` all raise ``QuantityProvenanceMissing``.
* AT THE PUBLICATION BOUNDARY — ``crash_detector.publication.dial_scalar`` releases a
  number into a dial slot only from a magnitude whose provenance is exactly that slot's
  dial, and the closed public envelope schema has no third key for a combined figure.
  **READ BOUNDARY 6 BEFORE RELYING ON THIS ONE.** It was claimed here as the layer that
  refuses a blend and it is NOT: the Project Lead re-wrapped the blend as a magnitude of one
  dial and ``number_for_dial_slot`` returned 0.5. What it refuses is a number arriving
  without a magnitude, or with the wrong dial's.

What THIS check still earns its keep for: it LOCATES a blend in the source, with a file and
a line, in the one place a reviewer can act on it cheaply; and it catches the three-line
spelling that no runtime layer would see until the branch executed. It is a locator with a
declared limit, and the register entry now says exactly that and no more.

FOUR RULES, DELIBERATELY DIFFERENT IN REACH
--------------------------------------------
  RULE 1  ARITHMETIC.  No expression anywhere in the application source may combine an
          equity-flavoured value and a monetary-flavoured value under an arithmetic or
          bitwise operator, a comparison, an augmented assignment, or a numeric aggregate
          (``sum``, ``min``, ``max``, ``mean``, ``statistics.*`` …). **There is no
          allowlist for this rule, not even the container and the serving layer.** Holding
          the two dials side by side never requires arithmetic between them.

  RULE 2  CO-OCCURRENCE.  No single expression may consume both dial types at all —
          outside the allowlisted container and serving layer, which are the two places
          BLUEPRINT §13 says composition legitimately happens. The container constructs a
          ``DialSet`` from both; the serving layer renders both side by side; the engine's
          ``evaluate`` builds the container. Everywhere else, an expression that has hold
          of both is one edit away from a headline number.

  RULE 3  REACHING PAST THE DECLARED RELEASE.  No expression anywhere in the application
          source may name the private slot in which a ``DialMagnitude`` holds its number
          (``_DialMagnitude__quantity``) or the one in which a ``DeclaredQuantity`` holds
          its own (``_DeclaredQuantity__value``, added at CD-PL-F54 because that closure
          created a SECOND private name holding the same number), by attribute or as a
          string handed to ``getattr``, nor call the pickle protocol that returns state
          (``__getstate__``, ``__reduce__``, ``__reduce_ex__`` — added closing
          ``CD-ENG-WO2R-F06``, a finding this seat raised against its own work).
          **There is no allowlist for this rule either**, save that each of the two
          modules that DEFINES a slot may name THAT slot and no other. The declared way to obtain the number is
          ``magnitude.quantity_for(<dial id>)``, which names one dial and refuses a
          mismatch; reaching around it is a deliberate act to obtain a number without
          saying which dial it belongs to, which is the first half of a blend. This rule
          is not aimed at a variant somebody wrote. It exists because the closure created
          two private names, and a guard over exactly those names is the narrowest
          kind of guard there is.

  RULE 4  A PROVENANCE DOOR OUTSIDE THE DECLARED ADMISSION SITES. **DENY BY DEFAULT.** No
          module on the scanned path may name ``observed_for_dial``,
          ``derived_within_one_dial`` or ``DeclaredQuantity`` — by call, attribute, import,
          annotation, decorator, default or a string handed to ``getattr`` — unless it is
          listed in ``DECLARED_ADMISSION_SITES`` with the reason it is there. Four modules
          are, and each reason is written beside it.

          WHAT THIS RULE IS, AFTER `CD-ASR-WO2R-F01` — READ THIS BEFORE CITING IT.
          It was written to answer `PL-Q9`, and it does: `PL-Q9` defeated RULE 1 by removing
          every flavour-bearing NAME, so there was nothing about a blend to recognise, and
          this check reported PASS on 3919 assertions while the module published a blend at
          runtime. This rule recognises no arithmetic, no dial marker and no laundering
          route, and reports an unlisted module because it is not a place anybody declared
          that numbers enter. That much stands and is genuinely useful.

          **THE SENTENCE THAT STOOD HERE — "IT HAS TO GET THE NUMBER BACK IN, AND SINCE
          CD-PL-F54 THERE IS EXACTLY ONE WAY TO DO THAT" — IS WITHDRAWN. IT WAS FALSE AND IT
          WAS MEASURED FALSE.** There was a SECOND way: `combine_within_one_dial`, a PUBLIC
          function re-exported in ``crash_detector.dials.__all__``, computed an honest
          single-dial set and then handed a caller's arbitrary closure's return value
          straight to the derivation door. `ASR2-002-A` used it, named nothing in this
          vocabulary, and published an equity 0.5 out of an equity 0.9 and a monetary 0.1
          with this check PASS on 4873 assertions. A REGISTRY THAT DENIES BY DEFAULT OVER A
          VOCABULARY IS ONLY AS CLOSED AS ITS VOCABULARY, and a vocabulary cannot enumerate
          the functions that have not been written yet.

          THE PROPERTY THAT IS TRUE, AND THE ONLY ONE THIS RULE NOW CLAIMS: **a module on
          the scanned path that NAMES one of these three names, in any of the scanned
          spellings, and is not a declared admission site, is reported.** That is a fact
          about names. It is not a fact about admission, it is not a bound on the set of
          routes, and **IT DOES NOT SURVIVE A RENAME** — rename a door at both ends and this
          rule goes silent while nothing about the system has changed. Recording a refusal
          from here as evidence about a CLASS is the inference that cost the second gate
          (`CD-PL-F74`, adopted project-wide at `CD-D-073`); a refusal from here is a
          VOCABULARY result and must be labelled one.

          WHAT ACTUALLY CLOSES THE DERIVATION ROUTE IS THE TYPE, NOT THIS RULE. See
          boundary 8.

          **AN IMPORT COUNTS**, unlike everywhere else in this check. Importing both score
          types is how a module legitimately gets hold of them; there is no comparable
          reason to import an admission door except to admit something.

BUILT FOR THE CLASS, NOT THE INSTANCE
--------------------------------------
The obvious plant is ``combined = (dials.equity.score + dials.monetary.score) / 2`` — one
expression, both markers, caught by inspecting that expression alone. The obvious ESCAPE is
to spell it over three statements:

    e = dials.equity.value.score
    m = dials.monetary.value.score
    combined = (e + m) / 2

By the time the addition happens, no dial marker is in the expression. A check that only
looked at single expressions would report the tree clean while the blend sat in it. So this
check carries a small intra-procedural FLAVOUR PROPAGATION: within each function (and at
module level) a local name assigned from an equity-flavoured expression becomes
equity-flavoured itself, through plain assignment, annotated assignment, augmented
assignment, tuple unpacking, walrus, ``for`` targets, ``with ... as`` and comprehension
targets. Parameters annotated with a score type are flavoured from their annotation. The
rules are then applied to the propagated flavours, so the three-statement spelling is
caught in the same breath as the one-liner.

FLAVOUR MARKERS: the score type names; the ``.equity`` / ``.monetary`` dial slots; the
``EQUITY_DIAL_ID`` / ``MONETARY_DIAL_ID`` constants; the dial-id string literals
``'equity_crash'`` / ``'monetary_debasement'``; and identifiers whose tokens name a dial.

SCANNED SET: the application source — ``src/crash_detector/`` and
``deploy/entrypoints/``. ``tests/`` is deliberately NOT scanned: the tests for CD-AC-002
must write ``operator.add(equity, monetary)`` in order to assert that it raises, and a
check that failed the test proving the property would be nonsense. ``import`` statements
are not expressions and are not markers — importing both types is how a module gets them.

DECLARED LIMIT — WHAT THIS CHECK DOES NOT CATCH, AND WHICH LAYER DOES
---------------------------------------------------------------------
Required by CD-RULE-004 and by the WO-2R dispatch, drawn in the pattern of
CD-RT-012-NO-EXECUTION-INTERFACE, whose declaration an independent auditor examined and
judged HONESTLY DRAWN AND DRAWN CONSERVATIVELY. That same auditor's caveat is why this
block exists: "CD-AC-002's AST guard has comparable limitations (intra-procedural, static)
and NO comparable written declaration, which is why CD-ASR-F01 is reported at HIGH."

It is written as fact, not as apology, and every boundary carries an example an auditor can
execute. **DO NOT READ A CLEAN RUN OF THIS CHECK AS PROOF THAT NO CODE PATH COMBINES THE
TWO DIALS.** It was clean for both blends that produced CD-ASR-F01. The register entry for
CD-RT-002-AST-NO-BLEND and this check's execution contract carry the same list.

THIS CHECK IS A STATIC READ OF SOURCE TEXT AT ONE COMMIT, AND ITS FLAVOUR PROPAGATION IS
INTRA-PROCEDURAL. Both limitations are permanent. They are not defects to be repaired in a
later work order; they are what a static intra-procedural checker IS.

  1  INTER-PROCEDURAL FLOW. A value carried into a function is not followed. Flavour is
     established per scope, from annotations and from assignments within that scope; a
     parameter annotated ``float`` carries no dial flavour whatever the caller passed.
     MEASURED EXAMPLE, which exits 0 here — this is `E01` verbatim:
         def _fold(left: float, right: float) -> float:
             return (left + right) / 2.0
         def banner_figure(dials):
             return _fold(dials.equity.value.score, dials.monetary.value.score)
     The call expression holds both dial markers but contains no arithmetic, so RULE 1
     does not fire; the arithmetic is one call away where there is no flavour to see.
     THE TYPE LAYER CARRIES THIS: executed, ``_fold`` raises
     ``TypeError: unsupported operand type(s) for +: 'DialMagnitude' and 'DialMagnitude'``.

  2  DYNAMIC ATTRIBUTE ACCESS ERASES FLAVOUR ENTIRELY. A dial reached through ``getattr``
     with a plain string is not a dial as far as this check is concerned. MEASURED
     EXAMPLE, which exits 0 here — this is `E02` verbatim:
         _SLOTS = ("equity", "monetary")
         magnitudes = [getattr(dials, slot).value.score for slot in _SLOTS]
         return sum(magnitudes) / len(magnitudes)
     No dial marker appears in any expression, so nothing is ever flavoured and no rule
     fires. This is the STRONGER of the two escapes because it needs no allowlisted path.
     THE TYPE LAYER CARRIES THIS: executed, ``sum`` raises
     ``TypeError: unsupported operand type(s) for +: 'int' and 'DialMagnitude'``.

  3  THE RULE 2 ALLOWLIST IS A REAL HOLE IN RULE 2, BY DESIGN. Six paths may consume both
     dials in one expression, and `E01` was planted in one of them
     (``src/crash_detector/serving``). RULE 1 has no allowlist and applies there in full,
     but RULE 1 only sees arithmetic it can attribute to both dials in one scope.
     MEASURED EXAMPLE: any inter-procedural fold placed under ``src/crash_detector/
     serving/`` is invisible to both rules. THE TYPE LAYER CARRIES THIS.

  4  THE SCANNED SET. Only ``src/crash_detector/`` and ``deploy/entrypoints/`` are read.
     ``tests/`` is deliberately excluded — the tests for CD-AC-002 must write
     ``operator.add(equity, monetary)`` in order to assert that it raises. MEASURED
     EXAMPLE: a blend placed in ``tests/`` or in ``db/`` exits 0 here. It also cannot
     reach a shipped image: all six application Dockerfiles COPY exactly ``src/`` and
     ``deploy/entrypoints/``.

  5  IT READS SOURCE, NOT BEHAVIOUR. A blend assembled at runtime — from a configuration
     value, from a plugin, from ``eval``, or from a module written at import time — is
     outside a static check entirely. MEASURED EXAMPLE: ``exec(open(cfg).read())`` is one
     expression naming no dial. THE TYPE LAYER CARRIES THIS, because the refusal is a
     property of the objects rather than of the text.

  6  A NUMBER ALREADY RELEASED IS AN ORDINARY FLOAT, AND THE EXITS ARE MANY.
     ``quantity_for(<dial id>)`` yields a bare ``float`` to a caller that names its one
     dial — and so, without the caller naming anything, do ``repr``, ``str``, ``format``,
     an f-string, ``%``-formatting, ``pprint``, a log line, ``json.dumps`` over
     ``__getstate__``, the bytes of a ``pickle`` and ``getattr`` on the private slot. Two
     such floats can be added by ordinary Python. MEASURED EXAMPLE, which RULE 1 DOES catch
     when spelled with the dial ids and does NOT catch when the ids are reached dynamically:
         e = dials.equity.value.score.quantity_for(EQUITY_DIAL_ID)
         m = dials.monetary.value.score.quantity_for(MONETARY_DIAL_ID)
         blended = (e + m) / 2.0

     **THIS BOUNDARY PREVIOUSLY READ "THE PUBLICATION BOUNDARY CARRIES THIS". THAT WAS
     MEASURED FALSE AND IS WITHDRAWN** (`CD-PL-F54`, and CD-RULE-006 exists because of it).
     The Project Lead re-wrapped the blend as ``DialMagnitude(dial_id="equity_crash",
     quantity=blended)``, whose provenance IS exactly the slot's dial, and
     ``number_for_dial_slot("equity_crash", <that>)`` RETURNED 0.5. Two declarations each
     assumed the other was covering the route. A declaration that misdirects an auditor to a
     layer which does not hold is worse than no declaration.

     THE RE-ENTRY CARRIES THIS, AND HERE IS THE EVIDENCE (CD-RULE-006). Since `CD-PL-F54`
     the blended ``float`` cannot be re-wrapped at all: ``DialMagnitude`` admits only a
     ``DeclaredQuantity``. Executed on a pristine extraction of this commit, from two
     legitimately constructed magnitudes of 0.4 and 0.6:
         PL-Q4 (repr-launder both, re-wrap as equity, publish)
             -> QuantityProvenanceMissing: a bare number (0.5) was offered as dial
                'equity_crash''s magnitude.
         PL-Q5 (the same through the declared door quantity_for)          -> same refusal
         PL-Q6 (number_for_dial_slot on the re-wrapped blend)             -> same refusal
         PL-Q9 (the flavour-free module, verbatim)                        -> same refusal
         V16a  (f-string over the private slot, no repr anywhere)         -> same refusal
         V16b  (JSON round trip of __getstate__, no repr anywhere)        -> same refusal
     What is NOT claimed: that the addition itself is refused. It is not, and cannot be —
     they are two ``float`` objects and Python adds floats. ``PL-Q1a`` still returns 1.0 and
     that is the honest state. The claim is that the sum cannot become a magnitude again.

  7  THE ADMISSION DOOR IS A DECLARATION, AND RULE 4 GUARDS IT BY REGISTRY, NOT BY TRUTH.
     ``observed_for_dial`` is the base case of the re-entry closure and it believes what it
     is told: something has to be the first number or the product cannot exist. A module
     that calls it with a blend and a fabricated ``inputs_used`` obtains a magnitude.
     MEASURED EXAMPLE — `V12`, which is `PL-Q9` with the door added, and which this check
     FAILS on with two RULE 4 violations (the import at line 3 and the call at line 22)
     while its RUNTIME is NOT refused and publishes 0.5.
     **NOT PROVED TO BE CARRIED ANYWHERE AT RUNTIME.** RULE 4 is the only layer over it and
     RULE 4 is static, so this residue inherits every limitation in this list.

     **THIS BOUNDARY USED TO ENUMERATE ITS OWN RESIDUES AS THOUGH THE LIST WERE EXHAUSTIVE —
     (i) an edit to ``DECLARED_ADMISSION_SITES``, (ii) a module outside the scanned set
     (boundary 4), (iii) a dynamically assembled door name (boundary 5). THAT ENUMERATION IS
     KNOWN INCOMPLETE AND THE CLAIM OF EXHAUSTIVENESS IS WITHDRAWN** (`CD-ASR-WO2R-F01`).
     The auditor's route was NONE OF THE THREE: the module was inside the scanned set, edited
     no registry, and assembled no name. It walked through a door this rule guards by using a
     PUBLIC function this rule did not know was a door. Two further residues are now known
     and are written down, and the list is no longer offered as complete:

       (iv) A PUBLIC FUNCTION THAT REACHES A DOOR ON ITS CALLER'S BEHALF. This is
            `ASR2-002-A`'s route. Nothing static can enumerate the functions that have not
            been written yet, so this residue is PERMANENT for a name-based rule. It is now
            carried at the TYPE for the DERIVATION door — see boundary 8, with the
            measurement — and it is NOT carried anywhere for the ADMISSION door, which is
            (v).
       (v)  A DECLARED ADMISSION SITE REACHED THROUGH A CALLER-SUPPLIED EXTENSION POINT.
            MEASURED as `CD-ENG-WO2R2-V05`: one stateful ``ContributionModel`` given to BOTH
            ``DialSpec``s sees each dial's figures in turn and returns the mean as the second
            dial's magnitude, admitted from ``engine/evaluate.py`` — the ONE declared product
            admission site — with every field of the claim TRUE except the number. THIS CHECK
            IS PASS WITH IT PRESENT (5002 assertions), ``check_no_numeric_default`` is PASS
            (397), the whole suite is 1333 passed, and ``number_for_dial_slot`` returned 0.5.
            **NOT PROVED TO BE CARRIED ANYWHERE.** No guard was built for it, deliberately:
            an identity check on the model object is defeated by two instances sharing a
            class attribute, and model purity is not decidable at this altitude. Closing it
            is a BLUEPRINT §7 / CD-D-005 architectural change owed to the Product Owner.

     `V13`, which reaches the door through ``importlib`` and ``getattr`` with a whole string,
     IS caught. The same residue is stated in ``src/crash_detector/dials/provenance.py``
     (module docstring), ``src/crash_detector/dials/magnitude.py`` (boundary E), the register
     entry and the execution contract, in the same words.

  8  THE DERIVATION DOOR IS CLOSED AT THE TYPE AND NOT HERE, AND THIS RULE CANNOT SEE THE
     DIFFERENCE. Added at `WO-2R2` increment 1a. Since that commit
     ``derived_within_one_dial`` takes NO number and NO dial set: it takes
     ``DeclaredQuantity`` values whose provenance this system established, refused by EXACT
     TYPE, and computes its own number from a CLOSED set of NAMED reductions
     (``SameDialReduction``), so there is no argument on any derivation path through which a
     caller's ``float`` or a caller's callable can arrive.
     WHY IT IS A BOUNDARY OF **THIS CHECK** RATHER THAN A FEATURE: this check exits 0 either
     way and always did. It was PASS on 4873 assertions with `ASR2-002-A` present at
     ``50fc231`` when the route was OPEN, and it is PASS on 4984 with the same variant
     present at increment 1a when the route is CLOSED. **A CLEAN RUN OF THIS CHECK CARRIES NO
     INFORMATION ABOUT THIS CLASS IN EITHER DIRECTION.**
     THE TYPE LAYER CARRIES THIS, AND HERE IS THE EVIDENCE (CD-RULE-006), each executed on
     its own pristine extraction:
         ASR2-002-A verbatim              -> UndeclaredReduction (type(reduction) check)
         CD-ENG-WO2R2-V01, every identifier renamed and the door aliased
                                          -> the identical refusal. THE RENAME TEST, EXECUTED.
         CD-ENG-WO2R2-V03, the reduction table rewritten
                                          -> TypeError from the interpreter, mappingproxy
         CD-ENG-WO2R2-V04, a duck-typed carrier and a float subclass
                                          -> QuantityProvenanceMissing, both arms
     Those refusals are exact-type and interpreter comparisons of OBJECTS. They survive a
     rename, they read no source and no registry, and none of them is this check.

EVERY "CARRIES THIS" ABOVE HAS BEEN RE-MEASURED AT THIS COMMIT, not inherited from the
increment that wrote it (CD-RULE-006). Boundaries 1, 2, 3 and 5 hand their residue to the
TYPE LAYER: `E01` raises ``TypeError: unsupported operand type(s) for +: 'DialMagnitude' and
'DialMagnitude'`` and `E02` raises ``TypeError: unsupported operand type(s) for +: 'int' and
'DialMagnitude'``, both executed on a pristine extraction of this commit. Boundary 6 now
hands its residue to the RE-ENTRY and carries the six executed refusals above. Boundary 8
hands its residue to the TYPE and carries four executed refusals of its own. **Boundary 7
hands its residue to NOBODY at runtime and says so, and residue (v) of boundary 7 is a
MEASURED, CURRENTLY OPEN ROUTE rather than a theoretical one.**

A NOTE ON HOW TO READ ANY REFUSAL THIS FILE MENTIONS (CD-PL-F74, adopted at CD-D-073). Every
refusal recorded anywhere on this project must name the LAYER that refused it and that
layer's SCOPE, and must state whether it survives a rename. In this header: RULE 4's refusals
are by a STATIC, INTRA-PROCEDURAL, DENY-BY-DEFAULT REGISTRY OVER A NAME VOCABULARY, scoped to
the three names in ADMISSION_VOCABULARY appearing literally in the scanned set, and they DO
NOT SURVIVE A RENAME. The type layer's refusals are exact-type or interpreter comparisons of
objects, scoped to every call in the process from anywhere, and they DO. Those two kinds of
evidence are not interchangeable, and reading the first as the second is what cost this
project its second gate.

FOR THE AUDITOR. A CD-AC-002 variant that lands beyond a boundary above is a finding
against THIS DECLARATION — was the limit honestly drawn? — and not an automatic RED
against the guard. A variant that reaches the violation through a route a boundary above
says is COVERED by the type layer or the publication boundary, and is nevertheless not
refused when EXECUTED, is a defect in the closure and should be reported as one.

EXIT: 0 clean · 1 violation, each with file and line · 2 usage · 3 precondition not met.
Never a skip, for any reason (PBG-CI-002).
"""

from __future__ import annotations

import ast
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _support import Check, parse_root, python_files, read_text, resolve_root  # noqa: E402

CHECK_ID = "CD-RT-002-AST-NO-BLEND"

SCAN_DIRS = ("src/crash_detector", "deploy/entrypoints")

#: Where consuming both dials in one expression is legitimate (RULE 2 only — RULE 1 has no
#: allowlist). Each is named with the reason it is here, so widening the list is a
#: deliberate act with a stated justification rather than a quiet append.
CO_OCCURRENCE_ALLOWLIST = {
    "src/crash_detector/dials/dialset.py": (
        "THE CONTAINER. DialSet holds the two readings side by side and exposes no scalar; "
        "constructing it necessarily names both slots (BLUEPRINT §7, §13)."
    ),
    "src/crash_detector/dials/scores.py": (
        "THE MODULE THAT DEFINES BOTH TYPES. `SCORE_TYPES = (EquityCrashScore, "
        "MonetaryDebasementScore)` enumerates them as data so the guards that assert their "
        "unrelatedness can iterate, which is the opposite of blending them. RULE 1 applies "
        "here in full and without allowlist, and the type-level refusal "
        "(CD-RT-002-TYPE-NO-ARITHMETIC) is a second independent instrument over this file."
    ),
    "src/crash_detector/dials/__init__.py": (
        "the package's re-export surface: __all__ and the import block name both types."
    ),
    "src/crash_detector/engine/evaluate.py": (
        "evaluate() BUILDS the container: `DialSet(equity=..., monetary=...)` is one "
        "expression naming both, and the dial/score type map is one dict naming both. "
        "RULE 1 still applies here in full, which is what actually guards this module."
    ),
    "src/crash_detector/engine/__init__.py": (
        "the package's re-export surface."
    ),
    "src/crash_detector/serving": (
        "THE SERVING LAYER. BLUEPRINT §13: 'composition happens only at the serving "
        "layer'. It renders both dials side by side; RULE 1 still forbids arithmetic "
        "between them here."
    ),
}

#: The private slot in which a ``DialMagnitude`` holds its number, in both the spelling a
#: reader would type and the mangled spelling CPython actually installs. RULE 3 refuses
#: either, as an attribute and as a string constant (so ``getattr(m, "_DialMagnitude__
#: quantity")`` is refused with the attribute form). Declared as data because the closure
#: created exactly ONE private name and this rule guards exactly that name.
#:
#: ``_DeclaredQuantity__value`` and ``__value`` joined it at CD-PL-F54, because that closure
#: created a SECOND private name holding the same number. A guard over the first name only
#: would have been exactly the narrowness this rule exists to avoid: reaching
#: ``_DeclaredQuantity__value`` obtains a bare float without naming a dial, which is the
#: same act as reaching ``_DialMagnitude__quantity`` and is the first half of the same
#: blend. This seat raised the omission against its own work while re-running the eleven
#: plants, before any variant exercised it.
SEALED_MAGNITUDE_SLOTS = frozenset(
    {
        "_DialMagnitude__quantity",
        "__quantity",
        "_DeclaredQuantity__value",
        "__value",
    }
)

#: Which module may name which slot: each DECLARES one and must read it to release the
#: number. Keyed PER MODULE rather than as one shared exemption, so the magnitude module
#: cannot reach the declared quantity's private slot or the reverse. A rule that fired on a
#: definition would forbid the structure it exists to protect; a rule that exempted a module
#: wholesale would open a door beside it.
SLOT_DECLARING_MODULES = {
    "src/crash_detector/dials/magnitude.py": frozenset(
        {"_DialMagnitude__quantity", "__quantity"}
    ),
    "src/crash_detector/dials/provenance.py": frozenset(
        {"_DeclaredQuantity__value", "__value"}
    ),
}

#: The REFLECTION reach. `__getstate__` and the pickle protocol return a magnitude's state,
#: and state is the number. Keying that state by the private slot name (see
#: ``DialMagnitude.__getstate__``) means a reader must write the slot name and is caught by
#: the set above — but calling the protocol at all, in application source, is the same act
#: as reaching the slot and there is no legitimate reason to do it. Added closing
#: CD-ENG-WO2R-F06, a finding this seat raised against its own increment-2 work after
#: `sum(m.__getstate__()["quantity"] for m in both) / 2` returned 0.5 with nothing refusing
#: it. Deny by default, narrowly: three names, no allowlist beyond the defining module.
SEALED_MAGNITUDE_REFLECTION = frozenset(
    {"__getstate__", "__reduce__", "__reduce_ex__"}
)

#: Everything RULE 3 refuses to see named in application source.
SEALED_MAGNITUDE_REACH = SEALED_MAGNITUDE_SLOTS | SEALED_MAGNITUDE_REFLECTION

#: The one module RULE 3 does not apply to: the module that DECLARES the slot, and which
#: must therefore name it in order to read it out inside ``quantity_for``. This is not an
#: allowlist in the RULE 2 sense — it is the definition site, and a rule that fired on the
#: definition would forbid the structure it exists to protect.
MAGNITUDE_MODULE = "src/crash_detector/dials/magnitude.py"

#: The module that DECLARES the two provenance doors. Its absence is a refusal, not a
#: clean scan: a tree without it has lost the layer that carries the criterion.
PROVENANCE_MODULE = "src/crash_detector/dials/provenance.py"

#: RULE 4's guarded vocabulary: everything by which a number acquires a DECLARED provenance
#: and therefore becomes admissible into a dial magnitude. Not a list of blend spellings —
#: a list of the doors, which is a different kind of list. It is short and it is closed
#: because the structure created exactly these doors and no others.
ADMISSION_VOCABULARY = frozenset(
    {
        "observed_for_dial",       # admits a measurement from OUTSIDE for one named dial
        "derived_within_one_dial",  # the union door, used only by combine_within_one_dial
        "DeclaredQuantity",         # the type itself: constructing one IS establishing one
    }
)

#: DENY BY DEFAULT OVER A DECLARED REGISTRY OF ADMISSION SITES (CD-PL-F54, and the same
#: shape CD-D-031 requires of the egress destination registry). A module on the scanned
#: path may name the admission vocabulary only if it is listed HERE, with the reason it is.
#: Everything else is a violation BY DEFAULT — not because the check recognised a blend in
#: it, but because it is not a place anybody declared that numbers enter.
#:
#: WHY THIS RULE EXISTS. `PL-Q9` defeated RULE 1 by removing every flavour-bearing NAME: no
#: dial appeared in any expression, no arithmetic touched a magnitude, and the check reported
#: PASS on 3919 assertions while the module published a blend at runtime. Nothing about a
#: blend is recognisable in such a module. So this rule watches the DOOR instead of the
#: traffic: it recognises no arithmetic, no dial marker and no laundering route, and reports
#: an unlisted module for being unlisted.
#:
#: **THE SENTENCE THAT STOOD HERE — "IT HAS TO GET THE NUMBER BACK IN, AND SINCE CD-PL-F54
#: THERE IS EXACTLY ONE WAY TO DO THAT" — IS WITHDRAWN. IT WAS MEASURED FALSE**
#: (`CD-ASR-WO2R-F01`). `ASR2-002-A` got the number back in through `combine_within_one_dial`,
#: a PUBLIC re-exported function that was not in ADMISSION_VOCABULARY and did not need to be,
#: and this check reported PASS on 4873 assertions while an equity 0.9 and a monetary 0.1
#: published as an equity 0.5. A REGISTRY THAT DENIES BY DEFAULT OVER A VOCABULARY IS ONLY AS
#: CLOSED AS ITS VOCABULARY.
#:
#: WHAT IS TRUE, AND IS ALL THAT IS CLAIMED: a module on the scanned path that NAMES one of
#: these three names, in any scanned spelling, and is not a declared site, is REPORTED. That
#: is a fact about names. It is not a bound on the set of routes, and IT DOES NOT SURVIVE A
#: RENAME — rename a door at both ends and this rule goes silent with nothing about the system
#: changed. A refusal from here is a VOCABULARY result and must be recorded as one
#: (CD-PL-F74, adopted project-wide at CD-D-073). The derivation route is closed AT THE TYPE
#: instead — see boundary 8 of the DECLARED LIMIT above — and the admission route is not
#: closed at all.
DECLARED_ADMISSION_SITES = {
    PROVENANCE_MODULE: (
        "DEFINES the doors. A rule that fired on the definition would forbid the structure "
        "it exists to protect."
    ),
    MAGNITUDE_MODULE: (
        "THE RE-ENTRY GATE. It imports DeclaredQuantity in order to REFUSE anything else at "
        "DialMagnitude's constructor, and calls derived_within_one_dial from "
        "combine_within_one_dial, whose dial set is computed from the magnitudes it was "
        "given rather than asserted by its caller."
    ),
    "src/crash_detector/dials/__init__.py": (
        "the package's re-export surface: the import block and __all__ name the door so "
        "that consumers have one place to import it from. It calls nothing."
    ),
    "src/crash_detector/engine/evaluate.py": (
        "THE ONE PRODUCT ADMISSION SITE. It is where a number enters a dial from outside "
        "the system, and the claim it makes is checked twice by an independent instrument: "
        "RULE F of check_no_numeric_default.py traces the magnitude through the door to "
        "ContributionModel.compute and reports any other provenance, and "
        "`_absence_is_never_a_number` re-derives from (spec, usable) whether the inputs "
        "cited were present at all. Being listed here exempts this module from RULE 4 and "
        "from nothing else."
    ),
}

EQUITY = "EQUITY"
MONETARY = "MONETARY"

EQUITY_NAMES = frozenset({"EquityCrashScore", "EQUITY_DIAL_ID", "equity"})
MONETARY_NAMES = frozenset({"MonetaryDebasementScore", "MONETARY_DIAL_ID", "monetary"})
EQUITY_STRINGS = frozenset({"equity_crash"})
MONETARY_STRINGS = frozenset({"monetary_debasement"})
EQUITY_TOKENS = frozenset({"equity"})
MONETARY_TOKENS = frozenset({"monetary", "debasement"})

#: Calls that reduce several numbers to one. A blend does not need an operator.
AGGREGATE_CALLS = frozenset(
    {
        "sum", "min", "max", "abs", "round", "pow", "divmod",
        "mean", "fmean", "median", "average", "geometric_mean", "harmonic_mean",
        "stdev", "pstdev", "variance", "pvariance", "quantiles",
        "hypot", "prod", "fsum", "dist", "norm", "sqrt", "log",
        "blend", "combine", "combined", "overall", "aggregate", "composite",
    }
)


def _tokens(identifier: str) -> set:
    """Split ``equityScore``/``equity_score``/``EQUITY_DIAL_ID`` into lowercase tokens."""
    out: list[str] = []
    current: list[str] = []
    for char in identifier:
        if char == "_":
            if current:
                out.append("".join(current))
                current = []
            continue
        if char.isupper() and current and not current[-1].isupper():
            out.append("".join(current))
            current = [char]
            continue
        current.append(char)
    if current:
        out.append("".join(current))
    return {token.lower() for token in out if token}


class Flavours:
    """The set of dial flavours an expression is built from, with taint propagation."""

    def __init__(self) -> None:
        self.env: dict[str, set] = {}

    # -- reading an expression --------------------------------------------------------- #
    def of(self, node) -> set:
        found: set = set()
        if node is None:
            return found
        for inner in ast.walk(node):
            if isinstance(inner, ast.Name):
                found |= self._of_identifier(inner.id)
            elif isinstance(inner, ast.Attribute):
                found |= self._of_identifier(inner.attr)
            elif isinstance(inner, ast.arg):
                found |= self._of_identifier(inner.arg)
            elif isinstance(inner, ast.keyword) and inner.arg:
                found |= self._of_identifier(inner.arg)
            elif isinstance(inner, ast.Constant) and isinstance(inner.value, str):
                if inner.value in EQUITY_STRINGS:
                    found.add(EQUITY)
                if inner.value in MONETARY_STRINGS:
                    found.add(MONETARY)
        return found

    def _of_identifier(self, identifier: str) -> set:
        found: set = set(self.env.get(identifier, ()))
        if identifier in EQUITY_NAMES:
            found.add(EQUITY)
        if identifier in MONETARY_NAMES:
            found.add(MONETARY)
        tokens = _tokens(identifier)
        if tokens & EQUITY_TOKENS:
            found.add(EQUITY)
        if tokens & MONETARY_TOKENS:
            found.add(MONETARY)
        return found

    # -- propagation -------------------------------------------------------------------- #
    def bind(self, target, flavours: set) -> None:
        if not flavours:
            return
        for inner in ast.walk(target):
            if isinstance(inner, ast.Name):
                self.env.setdefault(inner.id, set()).update(flavours)

    def child(self) -> "Flavours":
        """A nested scope that inherits what the enclosing scope has established."""
        nested = Flavours()
        nested.env = {name: set(value) for name, value in self.env.items()}
        return nested


class BlendScanner:
    def __init__(
        self,
        check: Check,
        path: pathlib.Path,
        allow_co_occurrence: bool,
        declares_the_slot: frozenset = frozenset(),
        is_admission_site: bool = False,
    ) -> None:
        self.check = check
        self.path = path
        self.allow_co_occurrence = allow_co_occurrence
        self.declares_the_slot = declares_the_slot
        self.is_admission_site = is_admission_site

    def report(self, node, rule: str, what: str) -> None:
        self.check.violation(self.path, getattr(node, "lineno", 0), rule, what)

    # -- driving ------------------------------------------------------------------------ #
    def scan_module(self, tree: ast.Module) -> None:
        self.scan_sealed_slot_reach(tree)
        self.scan_admission_vocabulary(tree)
        self.scan_body(tree.body, Flavours())

    def scan_admission_vocabulary(self, tree: ast.Module) -> None:
        """RULE 4 over the whole module: DENY BY DEFAULT outside the declared sites.

        Walked over the module rather than threaded through the expression scanner for the
        same reason RULE 3 is: it is not a question about flavour or about scope. Naming a
        door is a violation wherever it appears — in a call, an attribute, an import, an
        annotation, a decorator, a default or a string handed to ``getattr``.

        **AN IMPORT COUNTS.** Elsewhere in this check an import is explicitly not a marker,
        because importing both score types is how a module legitimately gets hold of them.
        Here the import IS the act: there is no reason to import an admission door except
        to admit something, and a module that imports it and does not call it has still
        put the door within reach of the next edit.
        """
        if self.is_admission_site:
            return
        for node in ast.walk(tree):
            named = ""
            if isinstance(node, ast.Name) and node.id in ADMISSION_VOCABULARY:
                named = node.id
            elif isinstance(node, ast.Attribute) and node.attr in ADMISSION_VOCABULARY:
                named = node.attr
            elif isinstance(node, ast.alias):
                for part in (node.name, node.asname):
                    if part and part.split(".")[-1] in ADMISSION_VOCABULARY:
                        named = part
            elif isinstance(node, ast.Constant) and node.value in ADMISSION_VOCABULARY:
                # `getattr(provenance, "observed_for_dial")` is the same act spelled to
                # avoid the attribute. The door names have no other use as data: unlike a
                # dunder name, nothing in this codebase tabulates them.
                named = str(node.value)
            else:
                continue
            # One assertion per node that COULD name a door, counted where it is judged.
            self.check.asserted()
            if not named:
                continue
            self.report(
                node,
                "RULE 4: a provenance door outside the declared admission sites",
                f"`{named}` establishes the provenance of a number, and this module is not "
                "a declared admission site. Since CD-PL-F54 a bare float cannot become a "
                "dial magnitude: the only way any number gets into one is through a door "
                "in ADMISSION_VOCABULARY or through a function that reaches one on its "
                "caller's behalf. THE SENTENCE THAT STOOD HERE — that such a module 'cannot "
                "avoid coming here' — WAS REFUTED BY EXECUTION AND IS WITHDRAWN AS A CLAIM "
                "BY THE PRODUCT OWNER (CD-ASR-WO2R-F01, CD-D-073). `ASR2-002-A` avoided "
                "coming here entirely, through `combine_within_one_dial`, a PUBLIC "
                "re-exported function that was not in this vocabulary and did not need to "
                "be. WHAT IS TRUE OF THIS RULE, AND IS ALL THAT IS CLAIMED FOR IT: it "
                "reports a module that NAMES one of these three names and is not a declared "
                "site, without recognising anything about a blend — so it does not need to "
                "anticipate a laundering route, and equally it cannot see one that names "
                "nothing. IT IS A LOCATOR OVER A NAME VOCABULARY AND IT DOES NOT SURVIVE A "
                "RENAME. What closes the derivation route is the TYPE (see boundary 8). "
                "DENY BY DEFAULT: the declared sites are "
                f"{sorted(DECLARED_ADMISSION_SITES)}, each with its stated reason in this "
                "file, and an unlisted module is a violation because it is not a place "
                "anybody declared that numbers enter — not because anything about it was "
                "recognised (CD-AC-002, CD-ASR-F01, CD-PL-F54).",
            )

    def scan_sealed_slot_reach(self, tree: ast.Module) -> None:
        """RULE 3 over the whole module, in one pass and with no allowlist.

        Walked over the module rather than threaded through the expression scanner
        because it is not a question about flavour or about scope: naming the private
        slot is a violation wherever it appears, in an expression, in a default, in a
        decorator, in an annotation or in a string.
        """
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Attribute, ast.Constant, ast.Call)):
                continue
            # One assertion per node that COULD name the reach — every attribute access,
            # every constant and every call in the module. Counting every AST node would
            # inflate the number without widening the guard, and a count is evidence.
            self.check.asserted()
            reached = ""
            if isinstance(node, ast.Attribute) and node.attr in SEALED_MAGNITUDE_REACH:
                reached = node.attr
            elif isinstance(node, ast.Constant) and node.value in SEALED_MAGNITUDE_SLOTS:
                # SLOT names only. A dunder NAME held as data is a legitimate thing in this
                # codebase — `ARITHMETIC_DUNDERS` and `TOLERATED_INTERPRETER_MACHINERY` are
                # both tables of dunder names, and a rule that could not tell a declaration
                # from a reach would forbid the guards it exists beside. The slot names have
                # no such use: outside the module that declares them they are only ever a
                # way of reaching the number.
                reached = str(node.value)
            elif isinstance(node, ast.Call):
                # `getattr(m, "__getstate__")()` is the same reach as `m.__getstate__()`,
                # spelled to avoid the attribute. Judged on the CALL, so a dunder name
                # sitting in a data table is untouched.
                callee = (
                    node.func.id if isinstance(node.func, ast.Name)
                    else node.func.attr if isinstance(node.func, ast.Attribute) else ""
                )
                if callee in ("getattr", "setattr", "delattr") and len(node.args) >= 2:
                    second = node.args[1]
                    if (
                        isinstance(second, ast.Constant)
                        and second.value in SEALED_MAGNITUDE_REACH
                    ):
                        reached = str(second.value)
            if not reached or reached in self.declares_the_slot:
                # The module that DECLARES this particular slot may name it, and only it.
                continue
            self.report(
                node,
                "RULE 3: reaching past the declared magnitude release",
                f"`{reached}` reaches past the declared release of a dial magnitude — "
                "it is either the PRIVATE slot in which a DialMagnitude holds its number "
                "or the pickle protocol that returns that slot as state. Either obtains a "
                "bare float without naming which dial it belongs to, which is the first "
                "half of a blend. The declared release is "
                "`magnitude.quantity_for(<dial id>)`, which names one dial and refuses a "
                "mismatch by comparing provenance (CD-AC-002, CD-ASR-F01, CD-ENG-WO2R-F06). "
                "There is no allowlist for this rule beyond the module that declares the "
                "slot.",
            )

    def scan_body(self, body, flavours: Flavours) -> None:
        for statement in body:
            self.scan_statement(statement, flavours)

    def scan_statement(self, node, flavours: Flavours) -> None:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            # Importing both types is how a module obtains them. Not an expression.
            return

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            nested = flavours.child()
            arguments = node.args
            every = (
                list(arguments.posonlyargs)
                + list(arguments.args)
                + list(arguments.kwonlyargs)
                + ([arguments.vararg] if arguments.vararg else [])
                + ([arguments.kwarg] if arguments.kwarg else [])
            )
            for argument in every:
                marks = nested.of(argument.annotation) | nested._of_identifier(argument.arg)
                if marks:
                    nested.env.setdefault(argument.arg, set()).update(marks)
            for decorator in node.decorator_list:
                self.scan_expression(decorator, nested)
            for default in list(arguments.defaults) + [
                d for d in arguments.kw_defaults if d is not None
            ]:
                self.scan_expression(default, nested)
            self.scan_body(node.body, nested)
            return

        if isinstance(node, ast.ClassDef):
            nested = flavours.child()
            for decorator in node.decorator_list:
                self.scan_expression(decorator, nested)
            self.scan_body(node.body, nested)
            return

        if isinstance(node, ast.Assign):
            # `__all__ = [...]` is a re-export surface, not a computation.
            if any(
                isinstance(target, ast.Name) and target.id == "__all__"
                for target in node.targets
            ):
                return
            self.scan_expression(node.value, flavours)
            marks = flavours.of(node.value)
            for target in node.targets:
                if isinstance(target, ast.Tuple) and isinstance(node.value, ast.Tuple):
                    for slot, value in zip(target.elts, node.value.elts):
                        flavours.bind(slot, flavours.of(value))
                else:
                    flavours.bind(target, marks)
            return

        if isinstance(node, ast.AnnAssign):
            if node.value is not None:
                self.scan_expression(node.value, flavours)
            marks = flavours.of(node.value) | flavours.of(node.annotation)
            flavours.bind(node.target, marks)
            return

        if isinstance(node, ast.AugAssign):
            left = flavours.of(node.target)
            right = flavours.of(node.value)
            self._judge_combination(node, left, right, f"`{ast.unparse(node)[:120]}`")
            self.scan_expression(node.value, flavours)
            flavours.bind(node.target, left | right)
            return

        if isinstance(node, (ast.For, ast.AsyncFor)):
            self.scan_expression(node.iter, flavours)
            flavours.bind(node.target, flavours.of(node.iter))
            self.scan_body(node.body, flavours)
            self.scan_body(node.orelse, flavours)
            return

        if isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                self.scan_expression(item.context_expr, flavours)
                if item.optional_vars is not None:
                    flavours.bind(item.optional_vars, flavours.of(item.context_expr))
            self.scan_body(node.body, flavours)
            return

        for field_name, value in ast.iter_fields(node):
            if isinstance(value, list):
                statements = [item for item in value if isinstance(item, ast.stmt)]
                expressions = [item for item in value if isinstance(item, ast.expr)]
                self.scan_body(statements, flavours)
                for expression in expressions:
                    self.scan_expression(expression, flavours)
            elif isinstance(value, ast.stmt):
                self.scan_statement(value, flavours)
            elif isinstance(value, ast.expr):
                self.scan_expression(value, flavours)
            elif isinstance(value, list) is False and isinstance(value, ast.AST):
                for sub in ast.iter_child_nodes(value):
                    if isinstance(sub, ast.stmt):
                        self.scan_statement(sub, flavours)
                    elif isinstance(sub, ast.expr):
                        self.scan_expression(sub, flavours)

    # -- expressions --------------------------------------------------------------------- #
    def scan_expression(self, node, flavours: Flavours) -> None:
        if node is None:
            return
        for inner in ast.walk(node):
            if isinstance(inner, ast.NamedExpr):
                flavours.bind(inner.target, flavours.of(inner.value))
            if isinstance(inner, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
                for generator in inner.generators:
                    flavours.bind(generator.target, flavours.of(generator.iter))

        self.check.asserted()

        for inner in ast.walk(node):
            if isinstance(inner, ast.BinOp):
                self._judge_combination(
                    inner,
                    flavours.of(inner.left),
                    flavours.of(inner.right),
                    f"`{ast.unparse(inner)[:120]}`",
                )
            elif isinstance(inner, ast.Compare):
                left = flavours.of(inner.left)
                for comparator in inner.comparators:
                    self._judge_combination(
                        inner,
                        left,
                        flavours.of(comparator),
                        f"`{ast.unparse(inner)[:120]}`",
                    )
            elif isinstance(inner, ast.BoolOp):
                seen: set = set()
                for value in inner.values:
                    marks = flavours.of(value)
                    self._judge_combination(
                        inner, seen, marks, f"`{ast.unparse(inner)[:120]}`"
                    )
                    seen |= marks
            elif isinstance(inner, ast.Call):
                name = (
                    inner.func.attr
                    if isinstance(inner.func, ast.Attribute)
                    else inner.func.id if isinstance(inner.func, ast.Name) else ""
                )
                is_aggregate = name in AGGREGATE_CALLS or bool(
                    _tokens(name) & {"blend", "combine", "combined", "aggregate", "mean", "average"}
                )
                if is_aggregate:
                    marks: set = set()
                    for argument in list(inner.args) + [k.value for k in inner.keywords]:
                        marks |= flavours.of(argument)
                    if EQUITY in marks and MONETARY in marks:
                        self.report(
                            inner,
                            "RULE 1: arithmetic across the two dials",
                            f"`{ast.unparse(inner)[:120]}` passes BOTH dials to the "
                            f"numeric aggregate `{name}`. A blend does not need an "
                            "operator: reducing the two dials to one number is the thing "
                            "PID §3.1 forbids, however it is spelled.",
                        )

        if not self.allow_co_occurrence:
            marks = flavours.of(node)
            if EQUITY in marks and MONETARY in marks:
                self.report(
                    node,
                    "RULE 2: one expression consumes both dials",
                    f"`{ast.unparse(node)[:120]}` consumes BOTH dial types in a single "
                    "expression, outside the container and the serving layer. BLUEPRINT "
                    "§13: composition happens only at the serving layer. An expression "
                    "holding both is one edit away from a headline number.",
                )

    def _judge_combination(self, node, left: set, right: set, rendered: str) -> None:
        if (EQUITY in left and MONETARY in right) or (
            MONETARY in left and EQUITY in right
        ):
            self.report(
                node,
                "RULE 1: arithmetic across the two dials",
                f"{rendered} combines an equity-flavoured value with a "
                "monetary-flavoured value. PID §3.1 is constitutional: the two dials fail "
                "in opposite directions and averaging cancels the signal. There is no "
                "allowlist for this rule, in any module.",
            )


def _allow_co_occurrence(root: pathlib.Path, path: pathlib.Path) -> bool:
    relative = path.relative_to(root).as_posix()
    for allowed in CO_OCCURRENCE_ALLOWLIST:
        if relative == allowed or relative.startswith(allowed.rstrip("/") + "/"):
            return True
    return False


def main() -> int:
    args = parse_root(CHECK_ID, __doc__)
    root, code = resolve_root(CHECK_ID, args.root)
    if root is None:
        return code

    check = Check(CHECK_ID, root)

    if not (root / "src/crash_detector").is_dir():
        return check.refuse(
            "src/crash_detector/ does not exist in this subject tree, so there is no "
            "application source to scan."
        )

    if not (root / MAGNITUDE_MODULE).is_file():
        return check.refuse(
            f"{MAGNITUDE_MODULE} does not exist in this subject tree. That module is the "
            "type-level closure of CD-AC-002 after CD-ASR-F01 — the nominal, per-dial, "
            "non-coercible magnitude — and this check is only a LOCATOR over it. A tree "
            "without it has lost the layer that actually carries the criterion, so this "
            "check refuses rather than reporting a clean scan of the layer that does not."
        )

    if not (root / PROVENANCE_MODULE).is_file():
        return check.refuse(
            f"{PROVENANCE_MODULE} does not exist in this subject tree. That module is the "
            "RE-ENTRY closure of CD-AC-002 after CD-PL-F54 — the declared quantity, "
            "without which a bare float could become a dial magnitude again — and RULE 4 "
            "has no vocabulary to deny by default over. A tree without it has lost the "
            "layer that actually carries the criterion, so this check refuses rather than "
            "reporting a clean scan of the layer that does not."
        )

    files = python_files(root, SCAN_DIRS)
    if not files:
        return check.refuse("no Python files found in the application source.")

    for path in files:
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
                f"this application module could not be parsed ({exc.msg}). A file the "
                "check cannot read is a file the check cannot guard, which is a failure "
                "and never a pass.",
            )
            continue
        BlendScanner(
            check,
            path,
            _allow_co_occurrence(root, path),
            declares_the_slot=SLOT_DECLARING_MODULES.get(
                path.relative_to(root).as_posix(), frozenset()
            ),
            is_admission_site=(
                path.relative_to(root).as_posix() in DECLARED_ADMISSION_SITES
            ),
        ).scan_module(tree)

    return check.done(
        f"{len(files)} application Python files under {', '.join(SCAN_DIRS)}; "
        f"{len(CO_OCCURRENCE_ALLOWLIST)} paths allowlisted for RULE 2 only; RULE 1 and "
        f"RULE 3 have no allowlist (RULE 3 exempts {len(SLOT_DECLARING_MODULES)} modules, "
        f"each for the ONE slot it declares and no other); RULE 4 denies by default over "
        f"{len(DECLARED_ADMISSION_SITES)} declared admission sites"
    )


if __name__ == "__main__":
    raise SystemExit(main())
