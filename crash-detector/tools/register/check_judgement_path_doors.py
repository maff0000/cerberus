#!/usr/bin/env python3
"""CD-RT-002-DOORS-REQUIRE-THEIR-TYPES — every judgement-path door is an ``admits`` door.

    python3 -B tools/register/check_judgement_path_doors.py --root <subject tree>

CRITERION: CD-AC-002 and CD-AC-005. BP-AMENDMENT-0001 §D.1, in force:

    "Every public entry point on a judgement path establishes each of its arguments by
     EXACT TYPE at the door, and the establishment is derived from the signature rather
     than written into the body."

§D.1 names the acceptance test for that rule in the same paragraph, and this is it: *"a
static check that enumerates the judgement paths and fails on any public entry point that
is not decorated — not a list of three fixes."*

WHAT THIS CHECK IS, AND WHAT IT IS NOT
----------------------------------------
**IT IS AN ENUMERATOR, AND ITS VALUE IS THE DENOMINATOR IT PRINTS.** It parses; it does not
import the product and it does not execute it, so an auditor who trusts nothing in the
implementation can run it against a tree they extracted themselves. That also means it
proves NOTHING about runtime behaviour: every escape on this project's record passed a
static checker. The runtime claim is made by the plants (P5, P6, P7) and by
``tests/test_admission.py``, not here.

**IT DERIVES ITS SUBJECT FROM THE ARTEFACT AND NEVER FROM A LIST OF DOORS** (CD-D-098). The
amendment's §B measured 44 public callables with an unestablished parameter at ``f30e63c``.
That number is a floor on where to look and it is already STALE: WO-2R3 increment 1 created
``engine/mapping.py`` and with it ``compute(spec, payloads)`` — the one place in the product
a dial magnitude is computed — which post-dates the inventory entirely. A check enumerating
44 names would not have looked at it. This one walks the tree, so ``engine.mapping.compute``
is a subject because it EXISTS, and so is whatever the next increment writes.

**IT PRINTS ITS SUBJECT COUNT**, so a vacuous pass is visible. A run that found no subjects
refuses (``PBG-CI-002`` via ``Check.done``): `exit 0` must never be able to mean "I looked
at nothing".

HOW A SUBJECT IS DERIVED — TWO INDEPENDENT RULES, UNIONED
-----------------------------------------------------------
A callable is a SUBJECT if EITHER rule reaches it. They are unioned rather than intersected
because each covers the other's blind spot, and neither is trusted alone.

**RULE 1 — JUDGEMENT-PATH PACKAGES, DENY-BY-DEFAULT WITHIN THEM.** Every ``*.py`` under
``src/crash_detector/engine/`` and ``src/crash_detector/serving/`` is read, and every public
module-level ``def`` and every public method of a public class in it is a subject. Nothing
inside those packages is opted out by name: a NEW MODULE is a subject with no edit to this
file, which is the CD-D-098 property above.

**RULE 2 — RETURN-TYPE REACH, ANYWHERE UNDER ``src/``.** Any public callable whose return
annotation names one of the JUDGEMENT VALUE TYPES — the types that ARE a dial's answer or a
witness's answer — is a subject wherever it lives, including in a package rule 1 has never
heard of. A judgement-path door added under a new package name is caught by this rule if it
declares what it returns.

EXEMPTIONS, EACH DERIVED FROM THE ARTEFACT AND EACH COUNTED IN THE OUTPUT
--------------------------------------------------------------------------
* **NOT REACHABLE FROM OUTSIDE THE MODULE.** *Superseded wording, quoted rather than deleted
  (CD-RULE-004, PBG-CONT-003): "names beginning ``_`` — not public entry points".*
  **AND SUPERSEDED AGAIN AT WO-2R3 INCREMENT 8 (``PO-DECISIONS-0015`` ruling 1): a
  module-level ``def`` WHOSE RETURN ANNOTATION NAMES A JUDGEMENT VALUE TYPE IS A SUBJECT
  WHATEVER IT IS SPELLED.** Membership moves on real bindings and measured reach, never on an
  underscore; the full account and the measurement that bounded it are in DECLARED LIMIT 9.
  **``PO-DECISIONS-0012`` RULING 2 CORRECTED THIS CLAUSE FROM NAME-PREFIX TO REACHABILITY**,
  after the fifth Assurance seat took this check from 1 violation to 0 by renaming ONE
  function-local identifier with runtime identity unchanged. For a MODULE-LEVEL ``def`` the
  identifier at the ``def`` site IS the binding a caller names, so the underscore test is
  asked about the right name and behaves exactly as before. For a FUNCTION-LOCAL ``def`` it
  was asked about a LOCAL VARIABLE NO CALLER CAN EVER NAME; the check now follows the
  object's ESCAPE ROUTE out of its enclosing function instead. See
  :func:`_reachable_public_binding` and DECLARED LIMIT 9. **A function-local callable
  exempted this way on a JUDGEMENT PATH is not merely dropped — it must be declared a NET in
  ``tools/register/declared_nets.py`` or the check fails ``UNCLASSIFIED_INTERCEPTOR``,
  because "not a door" must never again mean "not seen";**
* ``@property`` accessors — a property getter takes only its receiver, and no argument can
  be added to one, so there is nothing for ``admits`` to be told about and nothing that can
  arrive later unguarded;
* methods of a class whose bases include ``Protocol`` — these are stubs describing a
  boundary to a foreign system, they have no body to guard, and BP-AMENDMENT-0001 §D.3
  (increment 3) is where that boundary is closed, by a different mechanism.

Each exemption's COUNT is printed. An exemption that starts absorbing the subject set is
therefore visible in the output rather than discovered later.

WHAT IT ASSERTS ABOUT EACH SUBJECT — AND THERE ARE NOW **TWO DOOR FORMS**
--------------------------------------------------------------------------
**FORM 1 — DECLARED.** The subject carries ``@admits(...)``, and:

1. it carries ``@admits(...)``;
2. the parameter names ``admits`` was told about are EXACTLY the parameter names in the
   signature, minus the method receiver. This is planted violation **P7** caught statically
   as well as at runtime: a new parameter added to a decorated door fails HERE too, and it
   fails without the module being imported.

**FORM 2 — DERIVED. NEW AT WO-2R3 INCREMENT 8** (``PO-DECISIONS-0015`` ruling 1 (b)). The
subject's decorator is declared in ``tools/register/declared_door_mechanisms.py``, which means
its establishment is DERIVED from its own signature and there is no ``admits(...)`` argument
list to compare against it — **the signature IS the declaration**. What is asserted instead is
the pair of artefact properties the derivation requires and refuses without: **EVERY PARAMETER
ANNOTATED** (``DERIVED_DOOR_PARAMETER_NOT_ANNOTATED``) and **NO VARIADIC PARAMETER**
(``OPEN_CHANNEL``, the same code an ``admits`` door gets for the same shape). The declared
mechanism is itself checked against its own source — it must EXIST, must read
``inspect.signature``, must compile through ``crash_detector.admission.declaration``, and must
DECORATE SOMETHING. **A ROW IN THAT REGISTER IS NOT AN EXEMPTION AND BUYS A SUBJECT NOTHING.**

Why a second form exists at all: ``admits`` derives the parameter LIST from the signature but
takes the TYPE beside each name by hand, so adding a parameter FAULTS the door and every call
is refused. That is right for a door and it is **not** what ruling 1 (b) asks of the CD-ASR-F03
guard, which must *survive* arity growth *"because it derives, not because it gapes"*.

====================================================================================
DECLARED LIMIT (CD-RULE-004) — in this header, in required-tests.yaml and in
contracts/execution/CD-RT-002-DOORS-REQUIRE-THEIR-TYPES.md, each with an executable
example. CD-RULE-006: each hand-off names a layer MEASURED to carry it, or says NOT PROVED
TO BE CARRIED ANYWHERE.

**THIS ROW HAS SIX DECLARED LIMITS AND ONLY FOUR OF THEM ARE BELOW.** The four here are
THE STATIC CHECK'S. Limits **5** (§D.1's rule is NOT held at the three §B.3 doors, whose
type establishment is body-borne) and **6** (the interpreter reach — ``__closure__``,
``__wrapped__``, and rebinding the establishing function in its own module namespace) are
THE MECHANISM'S, they live in the header of ``src/crash_detector/admission.py``, and they
are reproduced in full in the register entry and the execution contract. Numbering runs
1..6 across the two headers on purpose: they are one row's limits, not two lists.
An auditor who reads only this file has read FOUR SIXTHS of what this row declares open.
(CD-PL-F81, ruled CD-D-111 — until WO-2R3 increment 4 the register carried four of six and
``grep -c "__closure__" required-tests.yaml`` returned 0.)
====================================================================================

 1  **CONSTRUCTORS ARE STILL NOT SUBJECTS *OF THIS CHECK*, AND SINCE WO-2R3 INCREMENT 5
    THAT IS NO LONGER AN UNCARRIED GAP. NARROWED TO ITS MEASURED REACH; THE SUPERSEDED
    WORDING IS QUOTED RATHER THAN DELETED.**

    It read: *"CONSTRUCTORS ARE NOT SUBJECTS OF THIS CHECK, AND THAT IS A REAL GAP IN §D AS
    SCOPED. ... §D.2 lists no constructor and this check does not invent that scope. ... As
    a residue of §D.1's own rule: NOT PROVED TO BE CARRIED ANYWHERE."* The Product Owner
    ruled on exactly that declaration at PO-DECISIONS-0007 ruling 1 — ``__post_init__`` IS A
    BODY — and re-based it at PO-DECISIONS-0008 ruling 2 from four named types to THE CLASS.

    **STILL TRUE:** this check reads CALLABLES, and a constructor is not one of its
    subjects. Executable example, re-measured at increment 5 on a pristine extraction:
    ``variants/WO-2R3/V17-constructor-body-escape.patch`` deletes the
    ``type(spec) is not DialSpec`` loop from ``ConfigSnapshot.__post_init__`` and **this
    check still exits 0 with 54 assertions**. No reader should infer anything about
    constructors from a clean run of THIS check.

    **NO LONGER TRUE — THE HAND-OFF, AND THE CARRIER IS MEASURED (CD-RULE-006):** the
    structure is ``crash_detector.establishment.establishes``; the enumeration is
    ``python3 -B tools/register/check_constructor_field_establishment.py --root .``, which
    **ENUMERATES that class and asserts every fielded member carries its declaration —
    RUN IT AND READ ITS POPULATION LINE; NO COUNT IS TRANSCRIBED HERE** (CD-RULE-009, and
    see the note below on CD-PL-F91); and
    the measurement is V17 itself, RUN — with V17 applied and the mechanism present a duck
    ``DialSpec`` into ``ConfigSnapshot`` is REFUSED with
    ``establishment.FieldNotEstablished``, and with the mechanism removed
    (``V40-v17-violated-arm-establishes-removed.patch``) the same construction ESCAPES.

    **STILL NOT CARRIED, so this correction does not overstate itself:** the new mechanism
    establishes a field's TYPE and never a RELATION BETWEEN TWO FIELDS. §C.5's invariants 2
    and 3 and ``ConfigSnapshot``'s one-spec-per-dial REMAIN BODY-BORNE —
    ``variants/WO-2R3/V36-cross-field-invariant-body-rewrite.patch``, measured, ACCEPTED —
    and for that residue: **NOT PROVED TO BE CARRIED ANYWHERE.** It lives as residue (ii) of
    the constructor check's DECLARED LIMIT 1.

    **AND THIS NOTE ONCE CARRIED A COPY OF THE SIBLING'S CLASS DEFINITION AND COUNT, WHICH
    NO RULE POINTED AT (CD-PL-F91, raised by the Project Lead against this project's rules
    and not against a seat).** It read *"...which measures the body-borne field-establishment
    class at 32 members"*. That sentence carried BOTH the sibling's old class wording and a
    count, in a FOURTH place — CD-RULE-004's "all three places" are a LIMIT'S OWN three, and
    a copy living in a DIFFERENT instrument was outside every rule that keeps the three in
    step. PO-DECISIONS-0010 ruling 1 widened that class to **BODY-BORNE OR ABSENT** and
    moved the count, so the copy went stale exactly as an unpointed-at copy does. **THE
    REPAIR IS THAT THIS NOTE NOW CARRIES NEITHER** — no definition of the sibling's class
    and no count of it. It names the sibling's command instead, so a reader who wants either
    gets it from a measurement.

 2  **RULE 1's PACKAGE LIST IS A VOCABULARY.** ``engine`` and ``serving`` are spelled here.
    A judgement-path door written under a package name this file has never heard of is
    reached only by rule 2, and only if it annotates its return type. Executable example:
    ``variants/WO-2R3/V16-new-package-undecorated-door.patch`` adds
    ``src/crash_detector/judging/decide.py`` with a public, undecorated, unannotated
    ``decide(reading)`` — and this check still exits 0.
    **CARRIER: NOT PROVED TO BE CARRIED ANYWHERE.** No other layer enumerates judgement-path
    packages. It is stated here so the fourth Assurance seat can hit it without having to
    find it first.

 3  **``collectors/`` IS NOW A JUDGEMENT-PATH PACKAGE, AND WHAT REMAINS OPEN THERE IS
    NAMED CD-BP-003.** The limit this slot held at WO-2R3 increment 2 — *"``collectors/`` is
    not yet a judgement-path package here, by scope and not by oversight"* — WAS DISCHARGED
    AT INCREMENT 3 AND IS NOT RESTATED. ``collectors`` is in ``JUDGEMENT_PATH_PACKAGES``
    above, deny-by-default within, so every public callable in it is a subject and a new
    module there is a subject the day it is written.

    **THE SIZE OF THAT DISCHARGE, RE-MEASURED AT INCREMENT 4 AND STATED LIKE-FOR-LIKE**
    (CD-PL-F82, ruled CD-D-120). It was recorded as *"subjects 19 -> 24"*, which compared a
    TOTAL against a SUBSET: this check reaches subjects by two unioned rules, and at both
    SHAs rule 2 reaches 3 doors rule 1 does not, so 24 was the rule-1 part of a total of 27.
    Both figures below are re-derived by RUNNING THIS FILE, not transcribed::

        git archive 995ec3e | tar -x -C /tmp/cd-995   # increment-2 head, the base
        cd /tmp/cd-995 && python3 -B tools/register/check_judgement_path_doors.py --root .
            -> SUBJECTS ENUMERATED: 19. DECORATED: 19.   by rule 2 only: 3
            -> PASS — 38 assertions, 0 violations

        git archive 04cdd34 | tar -x -C /tmp/cd-clean # increment-3 head, this lane
        cd /tmp/cd-clean && python3 -B tools/register/check_judgement_path_doors.py --root .
            -> SUBJECTS ENUMERATED: 27. DECORATED: 27.   by rule 2 only: 3
            -> PASS — 54 assertions, 0 violations

    **TOTAL: 19 -> 27. RULE-1 SUBSET: 16 -> 24. ASSERTIONS: 38 -> 54.** The two subset
    figures are the printed total minus the printed rule-2-only count, arithmetic on this
    check's own output. Never pair 19 with 24: they are different measurements. The
    correction makes the coverage WIDER than it was claimed to be, not narrower — 27 of 27
    subjects are decorated. Nothing was unguarded because of the error, and nothing here
    changes what the check does: ``tests/test_judgement_path_doors.py`` still asserts
    ``subjects >= 24``, A FLOOR, which is why the discrepancy was never caught. **Raising
    that floor to an equality is NOT ruled and is NOT done here** (CD-D-120); it is a code
    change answering a documentary finding, and it is left alone deliberately.

    **WHAT IS OPEN IS NARROWER, AND IT IS THE SOFTEST SURFACE IN THE PRODUCT**
    (BLUEPRINT §17, CD-BP-003; the Product Owner named it the fourth Assurance seat's first
    target). ``collect``'s ``adapter``, ``sink``, ``ledger`` and ``validator`` are
    ``Protocol`` boundaries to genuinely foreign things — a market data source, the store —
    so exact-typing them against a concrete class is not available and BP-AMENDMENT-0001
    §D.3 part 2 says it would be wrong. They are declared ``ESTABLISHED_HERE`` and **this
    check prints all four, with file, line and parameter, at every run**, derived from the
    ARTEFACT and not from a list written here. **IT IS A DOOR THAT ADMITS, NOT AN ABSENCE OF
    A DOOR.**

    What IS closed at that door, and is not a limit: ``policy`` exact ``RetryPolicy``
    (``isinstance`` admitted a subclass shadowing ``max_attempts`` with a property until
    increment 3), ``started_utc`` exact ``datetime`` then rebuilt by ``ensure_utc``,
    ``delay`` exact ``DelayKind``, and every value the four Protocols RETURN exact-typed at
    its point of return.

    What is NOT closed, executable example — and it is a POSITIVE example, an object that is
    ADMITTED::

        class ConformingButFictional:            # supplies all five protocol members
            source_id = "src.does.not.exist"     # returns an exact FetchedResponse
            adapter_id = "fiction.v0"            # carrying a schema-conforming payload
            response_schema = {...}              # that it invented
            def fetch(self, *, timeout_seconds): return FetchedResponse(...)
            def is_empty(self, payload): return False

    ``variants/WO-2R3/V26-conforming-hostile-adapter.patch`` is that object and it is
    ADMITTED, measured at
    ``tests/test_collector_admission.py::test_cd_bp_003_a_structurally_conforming_adapter_is_admitted_whatever_it_says``.
    **CARRIER, PARTIAL AND MEASURED:** it cannot compute a dial value — nothing under
    ``collectors/`` may import ``crash_detector.dials`` or ``crash_detector.engine``,
    asserted over the whole package by
    ``tests/test_collector_boundaries.py::test_no_collector_module_imports_the_dial_types_or_the_engine``
    — and its observation still faces the staleness window and the required-input rules in
    ``engine.evaluate``. **CARRIER FOR WHETHER A CONFORMING ADAPTER IS TELLING THE TRUTH:
    NOT PROVED TO BE CARRIED ANYWHERE.** Source trust is CD-D-005 and BLUEPRINT §5 and it is
    OWED, not held. No guard was built over it.
    **THE PROTOCOL CONFORMANCE CHECK ITSELF FAILS THE RENAME TEST** (CD-PL-F74):
    ``missing_adapter_members`` asks ``hasattr`` for five SPELLED names, so it measures a
    VOCABULARY and not a class. That is unavoidable at a boundary to a foreign system —
    structural conformance IS nominal — and it is recorded rather than presented as a
    closure.
    **CARRIER MEASURED for the extent of the limit itself:**
    ``tests/test_admission.py::test_cd_bp_003_is_exactly_four_parameters_and_every_one_names_its_residue``
    pins CD-BP-003 at FOUR parameters of ONE door and requires each to name the risk and to
    write CD-RULE-006's words; a fifth is a test failure, not a quiet widening.

 4  **A DECORATOR NAMED ``admits`` IS RECOGNISED BY ITS NAME IN THE SOURCE.** This check
    reads TEXT; it cannot know that the ``admits`` a module imported is
    ``crash_detector.admission.admits``. Executable example:
    ``variants/WO-2R3/V18-counterfeit-admits.patch`` defines a do-nothing ``admits`` in
    ``crash_detector/own_terms.py`` — a module this check does not scan for doors — and
    imports it into ``serving/witness_resolver.py``. MEASURED, RE-TAKEN AT INCREMENT 4 BY
    RUNNING IT (it read ``38 assertions`` here, which was the increment-2 figure and had
    not moved with the artefact — CD-ENG-WO2R3-F14): this check exits 0 with **54
    assertions** and PASS, and ``ASR3-F04``'s duck row then renders ``WITNESS AGREES``.
    (The counterfeit must be planted OUTSIDE a judgement-path package to work. Defined
    inside ``serving/witness_resolver.py`` it is itself a public undecorated callable in a
    judgement-path package and this check reports it — measured, and disclosed here rather
    than claimed as design.)
    **CARRIER MEASURED: THE RUNTIME.** The same patched tree runs 3 FAILED under
    ``PYTHONPATH=src python3 -B -m pytest tests -q``, because the plants call the real doors
    and observe the real refusals. A static reader alone cannot carry this and does not
    claim to. CD-RULE-006 exists because two declarations once each assumed the other
    covered the route.

 7  **THE TRAVERSAL'S RESIDUAL REACH. NEW AT WO-2R3 INCREMENT 6, AND IT REPLACES A LIMIT THAT
    WAS NEVER DECLARED AT ALL.** (Numbered 7 because 1..4 are this file's and 5..6 are the
    mechanism's, and this row's limits run as ONE sequence across the two headers.)

    **THE UNDECLARED LIMIT THAT WAS HERE UNTIL THIS INCREMENT.** ``_callables`` read
    ``tree.body`` — top-level ``def``s plus the DIRECT members of top-level public classes —
    and its sibling ``check_constructor_field_establishment.py`` did the same for classes.
    **BOTH GOVERNING INSTRUMENTS SHARED THIS BLIND SPOT AND NEITHER DECLARED IT.**
    ``CD-ASR-WO2R3-01``'s four arms against ONE undecorated public door in
    ``collectors/runner.py``: module-level ``def`` **exit 1**; method of a top-level class
    **exit 1**; method nested ONE level **exit 0**; function-local ``def`` bound in a module
    dict **exit 0** — and live, ``POLICY["decide"]`` accepted unestablished arguments.
    ``_callables`` now descends to ANY DEPTH. **Both zeros are ones.**

    **WHAT IS NOW CLOSED, MEASURED** by ``variants/WO-2R3/P-B-how-deep-can-a-type-hide.py``,
    which plants one public undecorated callable at nine placements: nested ONE class level ·
    nested TWO class levels · inside a PUBLIC function body · inside a PRIVATE function body ·
    conditionally defined under ``if True:``. All are now NAMED by this check.

    **CORRECTED AT WO-2R3 INCREMENT 8 (`F-06-K`). SUPERSEDED, NOT DELETED (CD-RULE-004,
    PBG-CONT-003).** *Superseded wording, quoted in full: "**THE RESIDUAL REACH LIMITS ARE
    EXACTLY TWO, and they are the same two the sibling instrument declares as its DECLARED
    LIMIT 5, because they are properties of reading source rather than of either check:**"*

    **IT WAS ACCURATE ON THE CALLABLE-ENUMERATION AXIS AND FALSE ON THE NAME AXIS, AND
    INCREMENT 7 MADE IT WORSE WHILE IT SAID SO.** Increment 7 added ``for node in tree.body``
    at THREE new sites in this file — :func:`_module_bindings`, and the NET post-condition
    resolution and fetch in :func:`main` — while closing one in the fixpoint above. **Net
    residual across the two governing instruments: +2, with the declaration unmoved.**

    **AND THE FIRST OF THE THREE IS THE ONE THAT MATTERED: :func:`_module_bindings` IS THE
    FUNCTION THE REACHABILITY CLAUSE REASONS OVER.** Until this increment, "does this
    object's escape route land on a REAL PUBLIC BINDING?" was answered by a map that could
    not see a binding written inside any module-level block. All four sites now read module
    scope via :func:`_support.module_level_statements`.

    **WHAT THE BLINDNESS ACTUALLY COST HERE, MEASURED — AND IT IS LESS THAN THE WORST
    READING, WHICH IS RECORDED IN THE INSTRUMENT'S FAVOUR.** A function-local callable
    reachable only through a public module-level name bound inside ``if True:`` was reported
    UNREACHABLE and then refused as ``UNCLASSIFIED_INTERCEPTOR`` rather than named as the
    ``UNDECORATED_JUDGEMENT_PATH_DOOR`` it is. **THE EXIT CODE WAS RIGHT AND THE DIAGNOSIS
    WAS FALSE.** The NETS deny-by-default population is what held it, exactly as DECLARED
    LIMIT 9 says. **I LOOKED FOR AN ARM AT THIS SITE WHERE THE BLINDNESS CONVERTS A FAIL
    INTO A PASS AND COULD NOT BUILD ONE**: removing the NETS backstop means putting the
    callable outside both RULE 1 and RULE 2, and then it is not a subject at all. That
    search and its negative result are in the carrier's own docstring rather than left out
    because they were inconvenient. **THE FAIL-INTO-PASS CONVERSION IS REAL AT THE SIBLING
    INSTRUMENT** and is measured in its DECLARED LIMIT 5.

    **CARRIER (CD-RULE-006): ``tests/test_module_level_traversal.py``, six arms, ALL SIX
    FAILING AT ``4410275`` AND PASSING HERE.** Three of them are this file's sites.

    **THE RESIDUAL REACH LIMITS ARE TWO AGAIN, and they are the same two the sibling
    instrument declares as its DECLARED LIMIT 5, because they are properties of reading source
    rather than of either check. "AGAIN" IS LOAD-BEARING: they were two, then three for two
    increments while this paragraph said two, and they are two now.**

    (i) **A CALLABLE WITH NO ``FunctionDef`` NODE IS INVISIBLE.** A ``lambda`` bound to a name,
        or a function built by ``exec``/``type``, leaves nothing to walk. Executable example —
        the probe's ``built by type(...) AT RUNTIME`` placement writes
        ``hidden_decide = lambda reading: reading`` into ``engine/config.py``; MEASURED at both
        SHAs, this check **does not name it**. **CARRIER: NOT PROVED TO BE CARRIED ANYWHERE.**

    (ii) **A MODULE OUTSIDE ``src/crash_detector/`` IS NEVER PARSED.** Measured: the probe's
        ``in a module OUTSIDE the scanned root`` placement is not named at either SHA.
        **CARRIER: NOT PROVED TO BE CARRIED ANYWHERE.**

    **AND A LIMIT THAT TURNED OUT NOT TO BE ONE:** a module that does not parse is an
    ``UNPARSEABLE`` violation, not a silence. Measured, and therefore NOT declared as a limit.

    **WHAT THE WIDENING FOUND IN EXISTING CODE, WHICH IS A FINDING AND NOT A LIMIT.**
    ``engine/evaluate.py``'s ``guarded`` — the closure inside the private decorator
    ``_absence_is_never_a_number`` that carries the CD-ASR-F03 post-condition — is a
    PUBLIC-NAMED callable in a RULE 1 package with ``*extra, **extra_by_name`` and no
    ``@admits``. **THIS CHECK NOW EXITS 1 ON IT.** It is NOT exempted here and it is NOT fixed:
    ``engine/evaluate.py`` is outside WO-2R3 increment 6's writable scope, adding an exemption
    for it would be the quiet widening this project keeps finding, and deciding whether it
    should be decorated, renamed ``_guarded`` or declared exempt is a DESIGN QUESTION FOR THE
    PROJECT OWNER. Raised as ``CD-ENG-WO2R3-02-F06``. Note also that ``functools.wraps`` gives
    it the runtime ``__name__`` ``_evaluate_dial``, so the static reading and the runtime name
    DISAGREE about whether it is public at all — which is part of what makes it a question
    rather than an oversight.

 8  **``ESTABLISHED_HERE`` IS RESOLVED THROUGH ALIASES, AND THE SPELLINGS IT IS *NOT* RESOLVED
    THROUGH ARE NAMED. NEW AT WO-2R3 INCREMENT 6** (``PO-DECISIONS-0011`` ruling 1 item (c)).

    Until this increment this check matched the LITERAL name ``ESTABLISHED_HERE`` and nothing
    else. ``CD-ASR-WO2R3-01`` §2.4 hid a use behind ONE WORD — ``from ... import
    ESTABLISHED_HERE as _EH`` — and measured ``doors check: still reports 16 exemptions,
    EXIT=0``. **THE LIMIT THAT USE WEAKENS SAYS OF ITSELF "IT IS COUNTED, NOT HIDDEN", AND
    UNDER A ONE-WORD ALIAS THAT SENTENCE WAS FALSE.**

    **RESOLVED, EACH DEMONSTRATED BY ``variants/WO-2R3/P-C-an-aliased-exemption.py``:** an
    import alias; the plain form; a module-level rebinding run to a FIXPOINT so a chain of
    rebindings resolves; and any attribute spelled ``.ESTABLISHED_HERE``, whatever the module
    is aliased to. MEASURED, BOTH ARMS, with the auditor's own aliased door added:
    ``ESTABLISHED_HERE uses: 16`` and the door NOT named, at ``531c95c``; ``uses: 17`` and the
    door NAMED, here.

    **NOT RESOLVED — DECLARED, NOT SILENT, AND NONE OF THESE IS CLAIMED CLOSED:**

    * **CLOSED AT WO-2R3 INCREMENT 7 — this route is no longer a limit.** *Superseded wording,
      quoted rather than deleted (CD-RULE-004, PBG-CONT-003): "a name bound INSIDE A FUNCTION
      BODY — the rebinding fixpoint reads ``tree.body`` only, because a module-level binding
      is the only one a decorator at module level can see".* **That reasoning was sound about
      what a MODULE-LEVEL decorator can see and silent about a decorator INSIDE the same
      function**, which is where the escape was. The fixpoint now walks at ANY DEPTH.
      **MEASURED, BOTH ARMS, one planted alias bound in a function body with a door that
      escapes to a public module-level name: `ESTABLISHED_HERE uses: 16` before and `17`
      after, and the shipped tree's own count is UNMOVED at 16, so the widening added no
      false row here.** AND THE FIX IS RESIZED BY ITS OWN CARRIER RATHER THAN INFLATED: the
      runtime carrier `test_the_established_here_exemptions_are_exactly_this_set` ALREADY
      FAILED `17 != 16` on that plant BEFORE the widening, so this closed a gap in what the
      CHECK SAYS and not in what the project REFUSES;
    * a name computed at runtime — ``getattr(admission, "ESTABLISHED_" + "HERE")``;
    * an exemption reached through a CONTAINER — ``ALIASES = {"eh": ESTABLISHED_HERE}`` then
      ``@admits(x=ALIASES["eh"]("..."))``;
    * a WRAPPER — ``def eh(reason): return ESTABLISHED_HERE(reason)`` — which is a call to a
      function, not a reference to the object.

    **AND THE DISTINCTION THAT DECIDES WHETHER ANY OF THAT MATTERS (``CD-RULE-006``): A CHECK
    REPORTS; A CARRIER FAILS.** Giving this check alias-sight is HALF an answer. The other
    half is measured and it is better news than the record carried:
    ``tests/test_admission.py::test_the_established_here_exemptions_are_exactly_this_set`` and
    ``::test_every_established_here_states_a_reason_in_the_artefact`` enumerate the exemptions
    from the **RUNTIME compiled declaration objects**, where a spelling cannot matter, and they
    go **RED on an aliased seventeenth use AT ``531c95c`` AS WELL AS HERE** (``2 failed,
    23 passed``). **THAT CARRIER THEREFORE COVERS EVERY ROUTE IN THE "NOT RESOLVED" LIST
    ABOVE, INCLUDING THE ONES THIS CHECK CANNOT SEE**, because it never reads a name at all —
    provided the module is imported by ``pkgutil.walk_packages`` and the door object is
    reachable from a module or class namespace. **FOR AN EXEMPTION ON A DOOR THAT IS NOT
    REACHABLE FROM ANY MODULE OR CLASS NAMESPACE: NOT PROVED TO BE CARRIED ANYWHERE.**

 9  **THE REACHABILITY CLAUSE — WHAT IT REACHES AND WHAT IT DOES NOT. NEW AT WO-2R3
    INCREMENT 7** (``PO-DECISIONS-0012`` rulings 1 and 2).

    **THE CRITERION.** A callable is a subject when a caller OUTSIDE ITS MODULE can OBTAIN
    AND CALL it. Module-level ``def``: the identifier IS the binding, so publicness of the
    identifier decides, unchanged. Function-local ``def``: the identifier is a local variable
    no caller can name, so :func:`_reachable_public_binding` follows the object's ESCAPE
    ROUTE — RETURNED, or STORED under a container or attribute — and asks whether the binding
    it reaches is public. **DENY BY DEFAULT WITHIN THE ROUTES IT FOLLOWS: any RETURN or STORE
    destination the clause cannot RESOLVE returns reachable.** ``PASSED_TO`` is tagged and
    deliberately NOT treated as an escape — see the limits below, where the measurement that
    forced that choice is recorded rather than the choice alone.

    **THE TWO CONTRASTS THAT PROVE IT REACHED THE CODE PATH AND NOT THE HEADER, BOTH
    MEASURED BY ``variants/WO-2R3/P-H-the-reachability-criterion-under-attack.sh``, EACH ARM
    RUNNING ITS OWN TREE'S OWN COPY OF THIS FILE:**

    ==================================  ==========================  ==========================
    arm                                 OLD clause (name-prefix)    NEW clause (reachability)
    ==================================  ==========================  ==========================
    ``guarded``                         exit 1, 28 subjects         exit 0, 27 subjects
    ``guarded`` -> ``_guarded``         **exit 0, 27 subjects**     exit 0, 27 subjects
    ``+ POLICY["decide"]``  (public)    exit 1, both flagged        exit 1, ``_install_policy.decide``
    ``+ POLICY["_decide"]`` (private)   **exit 1, NOT flagged**     **exit 1, ``_install_policy._decide``**
    ==================================  ==========================  ==========================

    Row 2 is the RENAME TEST: **the old clause's verdict moved on one identifier and the new
    one's does not.** Row 4 is the fourth Assurance seat's ESCAPE 4 ARM 4 with a PRIVATE-named
    local — **a name-prefix clause cannot see it at all**, and the old arm's single violation
    is ``guarded`` at line 341, not the plant. That row is the one that makes this
    structural rather than a subtler vocabulary.

    **WHAT IS NOT REACHED, AND IT IS DECLARED RATHER THAN LEFT TO BE FOUND. NONE OF THESE IS
    CLAIMED CLOSED:**

    * **an object PASSED to a callee.** The clause tags this ``PASSED_TO`` and **DOES NOT
      TREAT IT AS AN ESCAPE**, which is a DELIBERATE WEAKENING WITH A MEASURED REASON, and
      the reason is that the first version did the opposite. **DENY-BY-DEFAULT HERE TURNS
      THIS PROJECT'S OWN CD-ASR-F03 FIX INTO A VIOLATION:** increment 7 item 3 adds
      ``delattr(guarded, "__wrapped__")`` — a call with ``guarded`` as an argument — and the
      deny-by-default rule reclassified ``guarded`` as a reachable door, **which is the exact
      outcome PO-DECISIONS-0012 ruling 1 forbids.** MEASURED: the doors check went
      PASS -> ``FAIL — 2 violation(s)`` on the increment's own repair. **AND BOTH WAYS OUT
      WERE WORSE THAN THE PROBLEM** — an exclusion list of "callees that do not retain" is a
      VOCABULARY, which is what ruling 2 exists to remove, and decorating ``guarded`` is
      prohibited by ruling 1. So the rule answers the question actually asked (*can a caller
      outside obtain and call it*) rather than a broader one (*could anything at all happen
      to it*). **WHAT IS LOST IS REAL AND IS NOT DRESSED UP: a callee that STORES the object
      somewhere reachable is not seen.** What is NOT lost: if the CALL'S RESULT is stored or
      returned, the assignment and return rules catch it on the RESULT; and ESCAPE 4 ARM 4 is
      a SUBSCRIPT STORE, handled separately and unaffected (measured, both spellings).
      **CARRIER: NOT PROVED TO BE CARRIED ANYWHERE**, except that on a JUDGEMENT PATH the
      NETS population denies by default and such a callable fails as
      ``UNCLASSIFIED_INTERCEPTOR`` unless declared — measured, the same backstop as the
      container-literal route;
    * **an escape through a CONTAINER LITERAL** — ``return {"decide": local}`` is a return of
      a dict, not of the local, and this clause does not look inside it, so no route is
      tagged and the callable is reported UNREACHABLE. **THIS SEAT FIRST WROTE THAT DOWN AS
      "A REAL GAP, IN THE UNSAFE DIRECTION", THEN MEASURED IT, AND THE ASSERTION WAS WRONG.**
      Planted into ``engine/evaluate.py`` at a throwaway tree, the check **EXITS 1** —
      ``UNCLASSIFIED_INTERCEPTOR`` at ``_install_via_container.decide`` — because the NETS
      population denies by default and backstops the clause's blindness. **THE VERDICT IS
      RIGHT AND THE CLAUSE'S REASON IS WRONG**: it says it found no escape route, which is
      true, and until this measurement it went on to say the callable "NEVER LEAVES that
      frame", which was not. Corrected. **WHAT REMAINS OPEN IS THE OFF-JUDGEMENT-PATH CASE:
      there the callable is a printed row and nothing fails**, and that is NOT PROVED TO BE
      CARRIED ANYWHERE;
    * **an escape by ``setattr``/``globals()``** — computed at runtime, invisible to any AST;
    * **reachability ACROSS modules — REWRITTEN AT WO-2R3 INCREMENT 8 BY PRODUCT AUTHORITY
      (``PO-DECISIONS-0015`` ruling 1). THE SUPERSEDED WORDING, QUOTED AND NOT DELETED
      (CD-RULE-004, PBG-CONT-003):**

          *"The clause is per-module. A non-public module-level name is treated as
          unreachable from outside, which is TRUE OF NOTHING IN PYTHON — the underscore is a
          convention and ``from m import _x`` works, MEASURED at
          ``variants/WO-2R3/P-F-can-anything-reach-the-net-without-a-door.py`` arm A2. **THIS
          CHECK KEEPS THE CONVENTION DELIBERATELY**, because §D.1's class is PUBLIC entry
          points and abolishing publicness would make every private helper in the package a
          door. **THAT IS A PRODUCT-MEANING BOUNDARY AND NOT AN IMPLEMENTATION ONE
          (PBG-AUTH-005)."*

      **THAT PARAGRAPH NAMED THE RIGHT QUESTION AND HANDED IT UP, AND THE ANSWER CAME BACK.**
      ``PO-DECISIONS-0015`` ruling 1: *"membership moves on REAL PUBLIC BINDINGS AND MEASURED
      REACH, never on an underscore."* Ground 1 is the measurement that forced it —
      ``_evaluate_dial`` was excluded by its leading underscore while a conforming foreign
      adapter obtained it from ``sys.modules`` and CALLED it, passing no door.

      **WHAT MOVED, IN TWO PLACES AND NO MORE:**

      (i) **MEMBERSHIP.** A module-level ``def`` is a subject if it is PUBLIC **or if its
          return annotation names a JUDGEMENT VALUE TYPE.** A callable that PRODUCES A
          JUDGEMENT is a judgement-path door whatever it is spelled. This is a property of
          the artefact and it survives renaming the identifier IN EITHER DIRECTION, which the
          underscore test does not. MEASURED on the shipped tree: **SUBJECTS 27 -> 31**, and
          the four are ``_evaluate_dial``, ``_established_quantity``, ``_new_quantity`` and
          ``_shown_from``, all four now decorated.
      (ii) **THE ESCAPE-ROUTE DESTINATION TEST.** It asked whether the destination's
          IDENTIFIER was public and concluded that a private one was a dead end. It now asks
          whether the destination is **ITSELF AN ENUMERATED SUBJECT OF THIS CHECK**; if it
          is, the local's door obligation is **RESOLVED** to that binding — the name a caller
          actually writes — and asserted there, rather than DENIED. ``guarded``'s reason line
          used to read *"reaches only ['_evaluate_dial'], every one of them non-public"*,
          which was the false sentence Ground 1 falsified.

      **WHAT DELIBERATELY DID NOT MOVE, WITH THE MEASUREMENT THAT DECIDED IT.** RULE 1's
      deny-by-default within a judgement-path package still asks publicness of a module-level
      name that returns no judgement value. Abolishing publicness ALTOGETHER was measured on a
      pristine ``git archive`` extraction of ``314592c`` by replacing ``_is_public``'s body
      with ``return True``: **SUBJECTS 27 -> 68, FAIL — 42 violation(s)**, i.e. 41 private
      helpers becoming doors in one increment. Whether §D.1's *"public entry points"* class
      includes them is a PRODUCT-MEANING boundary and not an implementation one
      (PBG-AUTH-005), and this seat raises it rather than taking it. **CARRIER FOR THE
      REMAINING UNDERSCORE DEPENDENCE: NOT PROVED TO BE CARRIED ANYWHERE**, other than that on
      a judgement path the NETS population denies by default;
    * **the NETS register identifies a net by its ENCLOSING function**, which is a
      module-level name and therefore renameable. Renaming it fails the check LOUDLY
      (``NET_DECLARED_BUT_ABSENT``, whose text names all three possible causes) and never
      silently. **THE FIRST VERSION OF THE REGISTER KEYED ON THE NET'S OWN LOCAL NAME AND
      FAILED THE RENAME TEST — MEASURED, PASS -> FAIL ON `guarded` -> `_guarded` — WHICH IS
      RULING 2's OWN DEFECT REINTRODUCED IN THE FIX FOR IT. Corrected before landing and
      recorded here rather than only fixed.**

    **CARRIER (CD-RULE-006 — A CHECK REPORTS, A CARRIER FAILS).** Six tests in
    ``tests/test_judgement_path_doors.py``, each asserting by BREAKING the property in a
    throwaway tree: the rename test; ESCAPE 4 ARM 4 with a private-named local; an emptied
    register; a net that stops calling its post-condition; a net declared where none exists
    (which must fire BOTH directions of the set equality); and the printed residue.
    **FOR THE THREE UNREACHED ROUTES ABOVE: NOT PROVED TO BE CARRIED ANYWHERE.**
"""

from __future__ import annotations

import ast
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _support import (  # noqa: E402
    EXIT_USAGE,
    Check,
    module_level_statements,
    parse_root,
    read_text,
    resolve_root,
)
from declared_door_mechanisms import DECLARED_DOOR_MECHANISMS  # noqa: E402
from declared_nets import DECLARED_NETS  # noqa: E402

CHECK_ID = "CD-RT-002-DOORS-REQUIRE-THEIR-TYPES"

#: RULE 1. Packages every one of whose public callables is a door. DENY-BY-DEFAULT WITHIN:
#: no module inside these is opted out, so a new module is a subject the day it is written.
#: See DECLARED LIMIT 2 — this tuple itself is a vocabulary.
JUDGEMENT_PATH_PACKAGES = ("engine", "serving", "collectors")

#: DECLARED LIMIT 3. `collectors` JOINED RULE 1 AT WO-2R3 INCREMENT 3 (BP-AMENDMENT-0001
#: §D.3, A6). What remains open there is not a package gap: it is CD-BP-003, the four
#: `Protocol` parameters of `collect`, and it is DERIVED FROM THE ARTEFACT below rather than
#: listed here — this check reports the ESTABLISHED_HERE uses it actually finds under this
#: package, so the limit's extent cannot drift away from the code that carries it.
CD_BP_003_PACKAGE = "collectors"

#: The door BP-AMENDMENT-0001 §D.2 lists as A6. Named so CD-BP-003 is reported at exactly
#: its own extent — the four Protocol parameters of this door — and not widened to every
#: ESTABLISHED_HERE that happens to share the package.
A6_DOOR = "collect"

#: RULE 2. The types that ARE a dial's answer, a witness's answer, or the material one is
#: computed from. A public callable that says it returns one of these is a judgement-path
#: door wherever it is written.
JUDGEMENT_VALUE_TYPES = frozenset(
    {
        "DialSet",
        "Reading",
        "Value",
        "Degraded",
        "Unknown",
        "WitnessPanel",
        "Agrees",
        "Diverges",
        "Unavailable",
        "Shown",
        "NotShown",
        "DialPresentation",
        "ScoreComputation",
        "DialMagnitude",
        "DeclaredQuantity",
        "ConfigSnapshot",
        "DialSpec",
        "ModelSpec",
    }
)

#: The decorator that makes a callable a door. See DECLARED LIMIT 4.
ADMITS = "admits"

#: The exemption inside `admits` itself. Every use is PRINTED with its location.
ESTABLISHED_HERE = "ESTABLISHED_HERE"

_RECEIVER_NAMES = ("self", "cls")


def _is_public(name: str) -> bool:
    """Is this identifier one a caller outside the module can NAME?

    **THIS IS STILL A NAME TEST AND IT IS STILL RIGHT — FOR THE NAMES IT IS ASKED ABOUT.**
    ``PO-DECISIONS-0012`` ruling 2 corrected the MEMBERSHIP CLAUSE from name-prefix to
    reachability; it did not abolish publicness, because §D.1's class IS public entry points.
    What changed is WHICH NAME the question is asked about — see
    :func:`_reachable_public_binding` and DECLARED LIMIT 9.

    For a MODULE-LEVEL ``def``, the identifier at the ``def`` site IS the binding a caller
    names, so this function is asked about the right name and its answer is unchanged.
    """
    return not name.startswith("_")


def _root_name(node):
    """The base ``Name`` of a ``Subscript``/``Attribute`` chain, or ``None``."""
    while isinstance(node, (ast.Subscript, ast.Attribute)):
        node = node.value
    return getattr(node, "id", None)


def _callee_name(call) -> str:
    target = call.func
    return getattr(target, "id", None) or getattr(target, "attr", None) or ""


def _module_bindings(tree) -> dict:
    """The module-level facts :func:`_reachable_public_binding` reasons over.

    Computed once per module. Three maps, each answering "where does the value produced by
    this module-level name END UP, under a name a caller can write?"

    ``decorates``
        ``name -> [names of module-level defs decorated with @name or @name(...)]``. A
        decorator's return value is BOUND TO THE NAME OF THE THING IT DECORATES, which is
        the single most important fact in this whole clause: ``_absence_is_never_a_number``
        returns ``guarded``, and what a caller can reach is not ``guarded`` but
        ``_evaluate_dial``.

    ``assigned_from``
        ``callee -> [module-level names assigned from callee(...)]``. ``HANDLER =
        make_handler()`` puts ``make_handler``'s return value where anyone can reach it.

    ``defined_at_module_level``
        every name bound by a module-level ``def``, ``class`` or assignment. Used to tell a
        module-level container from a local one.

    **THIS FUNCTION READS MODULE SCOPE, NOT ``tree.body``. CLOSED AT WO-2R3 INCREMENT 8**
    (`F-06-K`, and it is the convergence with GROUND 1). *Superseded implementation,
    described rather than deleted (CD-RULE-004, PBG-CONT-003): this loop read ``for node in
    tree.body``* — which is "module level AND NOT INDENTED", not module level. **THE
    REACHABILITY CLAUSE REASONS OVER THIS FUNCTION**, so until this increment
    ``evaluate_dial = _evaluate_dial`` written inside any module-level block was invisible
    to it, and "real public binding" was already wrong before the criterion below was asked
    the question. See :func:`_support.module_level_statements`.
    """
    decorates: dict = {}
    assigned_from: dict = {}
    defined: set = set()
    module_level_defs: dict = {}
    for node in module_level_statements(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(node.name)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # THE NODE, NOT ONLY THE NAME. WO-2R3 increment 8: the criterion below asks
                # what a destination RETURNS, and a name cannot answer that.
                module_level_defs[node.name] = node
            for decorator in node.decorator_list:
                head = decorator.func if isinstance(decorator, ast.Call) else decorator
                name = getattr(head, "id", None) or getattr(head, "attr", None)
                if name:
                    decorates.setdefault(name, []).append(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            bound = [t.id for t in targets if isinstance(t, ast.Name)]
            defined.update(bound)
            if isinstance(node.value, ast.Call):
                callee = _callee_name(node.value)
                if callee:
                    assigned_from.setdefault(callee, []).extend(bound)
    return {
        "decorates": decorates,
        "assigned_from": assigned_from,
        "defined_at_module_level": defined,
        "module_level_defs": module_level_defs,
    }


#: Route tags produced by :func:`_escape_routes`. Named as data so the check's own notes and
#: its violations quote the same words a reader finds in this file.
ESCAPE_RETURNED = "RETURNED"
ESCAPE_STORED = "STORED_UNDER"
ESCAPE_PASSED = "PASSED_TO"


def _escape_routes(local_name: str, enclosing) -> list:
    """How ``local_name`` LEAVES ``enclosing``'s frame, as ``(tag, destination)`` pairs.

    An object that never leaves the frame it was defined in cannot be obtained by anybody,
    whatever it is called. That is the whole of the reachability clause and this function is
    where it is decided.
    """
    routes = []
    for node in ast.walk(enclosing):
        if isinstance(node, ast.Return) and getattr(node.value, "id", None) == local_name:
            routes.append((ESCAPE_RETURNED, enclosing.name))
        elif isinstance(node, ast.Assign) and getattr(node.value, "id", None) == local_name:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    # A rebinding inside the same frame. Not an escape by itself; the new
                    # local name is followed by the caller of this function.
                    routes.append((ESCAPE_RETURNED, target.id))
                else:
                    routes.append((ESCAPE_STORED, _root_name(target) or "<unreadable>"))
        elif isinstance(node, ast.Call):
            for argument in list(node.args) + [k.value for k in node.keywords]:
                if getattr(argument, "id", None) == local_name:
                    routes.append((ESCAPE_PASSED, _callee_name(node)))
    return routes


def _is_a_door_binding(name: str, bindings: dict) -> bool:
    """Would the MODULE-LEVEL binding ``name`` be ENUMERATED AS A SUBJECT by this check?

    **NEW AT WO-2R3 INCREMENT 8** (``PO-DECISIONS-0015`` ruling 1), and it asks BOTH halves
    of subject-hood rather than only the first, because a "resolution" to a binding nothing
    asserts would be a silence wearing a resolution's clothes:

    * REACHABLE — the name is PUBLIC, **or** the ``def`` bound to it RETURNS A JUDGEMENT
      VALUE. The second is what stops the criterion moving on an underscore: it is a property
      of the artefact, and it survives renaming the identifier IN EITHER DIRECTION, which the
      first does not;
    * A SUBJECT — the module is a RULE 1 judgement-path package, **or** the ``def`` returns a
      judgement value (RULE 2). This is the same union ``main`` applies, asked here so the two
      cannot disagree.
    """
    node = bindings["module_level_defs"].get(name)
    if node is None:
        return False
    returns_a_judgement = _returns_a_judgement_value(node)
    reachable = _is_public(name) or returns_a_judgement
    a_subject = bindings["in_judgement_package"] or returns_a_judgement
    return reachable and a_subject


def _reachable_public_binding(name: str, function_chain: list, bindings: dict, node=None):
    """**THE REACHABILITY CLAUSE.** Can a caller outside this module obtain this callable?

    ``PO-DECISIONS-0012`` ruling 2: *"The doors instrument's membership clause is corrected
    from NAME-PREFIX (a vocabulary — CD-PL-F74's own conviction) to REACHABILITY."*

    **THE CRITERION, STATED ONCE AND REPEATED VERBATIM IN THE OTHER TWO CD-RULE-004 PLACES:**

        A callable is a subject of this check when a caller OUTSIDE ITS MODULE can OBTAIN
        AND CALL it. For a MODULE-LEVEL ``def`` the identifier at the ``def`` site IS the
        binding a caller names, so publicness of that identifier is the right question and
        nothing changes. For a FUNCTION-LOCAL ``def`` the identifier at the ``def`` site is
        a LOCAL VARIABLE THAT NO CALLER CAN EVER NAME, so asking whether it begins with an
        underscore is asking about the wrong name entirely. This clause instead follows the
        object's ESCAPE ROUTE out of its enclosing function and asks whether the binding it
        REACHES is public.

    **WHY THIS IS NOT "A SUBTLER NAME HEURISTIC", WHICH IS THE THING THE INCREMENT WAS
    WARNED AGAINST.** The test of a name heuristic is this project's own rename test, and
    the two spellings pull apart:

    * renaming the LOCAL (``guarded`` -> ``_guarded``) changes NOTHING, because no caller
      could name it under either spelling. **The old clause changed its verdict on exactly
      this rename — 1 violation to 0 — which is what proved it a vocabulary.**
    * renaming the DESTINATION (``_evaluate_dial`` -> ``evaluate_dial``) DOES change the
      verdict, and correctly: that name is one a caller writes, and making it public is
      making the object reachable. **A criterion that ignored that rename would be
      unsound in the other direction.**

    Returns ``(reachable, why)``. ``why`` is quoted in the violation and in the notes, so a
    reader never has to infer which clause decided their callable.

    **DENY BY DEFAULT, WITHIN THE ROUTES IT FOLLOWS.** A RETURN or STORE whose destination
    this function cannot RESOLVE returns reachable=True. **`PASSED_TO` IS THE ONE ROUTE IT
    TAGS AND DOES NOT ACT ON**, and that is a weakening with a measured reason recorded in
    DECLARED LIMIT 9 — deny-by-default there reclassified this project's own CD-ASR-F03 fix
    as a door, and the only escapes from that false positive were a vocabulary or the
    outcome PO-DECISIONS-0012 ruling 1 forbids.
    """
    if not function_chain:
        # ---------------------------------------------------------------------------- #
        # MODULE LEVEL — the identifier IS the binding a caller names.
        #
        # **AND SINCE WO-2R3 INCREMENT 8 THE UNDERSCORE IS NOT THE ONLY THING ASKED**
        # (`PO-DECISIONS-0015` ruling 1: *"membership moves on REAL PUBLIC BINDINGS AND
        # MEASURED REACH, never on an underscore"*). *Superseded implementation, described
        # rather than deleted (CD-RULE-004, PBG-CONT-003): this returned `_is_public(name)`
        # and nothing else.* **GROUND 1 IS WHAT MOVED IT:** `_evaluate_dial` was excluded by
        # its leading underscore while a conforming foreign adapter was MEASURED obtaining it
        # from `sys.modules` and calling it, passing no door. The underscore is a convention
        # that prevents no reach — `from m import _x` and `getattr(sys.modules[m], "_x")`
        # both work, measured — so a callable that PRODUCES A JUDGEMENT is a judgement-path
        # door whatever it is spelled.
        #
        # **WHAT WAS DELIBERATELY NOT DONE, WITH THE MEASUREMENT THAT DECIDED IT.** Abolishing
        # publicness altogether was measured on a pristine extraction of `314592c` by
        # replacing this function's body with `return True`: **SUBJECTS 27 -> 68, FAIL — 42
        # violations.** That is 41 private helpers becoming doors, and whether §D.1's *"public
        # entry points"* class includes them is a PRODUCT-MEANING boundary and not an
        # implementation one (PBG-AUTH-005). It is raised rather than taken. See DECLARED
        # LIMIT 9.
        # ---------------------------------------------------------------------------- #
        if _is_public(name):
            return True, "module-level name"
        if node is not None and _returns_a_judgement_value(node):
            return True, (
                "a NON-PUBLIC module-level name WHOSE RETURN ANNOTATION NAMES A JUDGEMENT "
                "VALUE TYPE. A callable that PRODUCES A JUDGEMENT is a judgement-path door "
                "whatever it is spelled, because the underscore prevents no reach: "
                "`from m import _x` and `getattr(sys.modules[m], '_x')` both work, MEASURED "
                "(PO-DECISIONS-0015 ruling 1 — never on an underscore)"
            )
        return False, "non-public module-level name that returns no judgement value"

    enclosing = function_chain[-1]
    routes = [route for route in _escape_routes(name, enclosing) if route[0] != ESCAPE_PASSED]
    passed_to = sorted({d for tag, d in _escape_routes(name, enclosing) if tag == ESCAPE_PASSED})
    if not routes:
        # **WHAT THIS SAYS IS WHAT WAS OBSERVED, NOT WHAT IT IMPLIES.** An earlier wording
        # read "it NEVER LEAVES that frame", which is a stronger claim than the evidence:
        # `return {"decide": local}` is a return of a DICT, so no route is tagged, and the
        # local escapes anyway. The verdict is still the safe one — on a judgement path the
        # callable lands in the NETS population and an undeclared one FAILS — but the
        # SENTENCE was wrong, and a shipped declaration wrong in a stated direction is this
        # project's most-found defect. See DECLARED LIMIT 9.
        return False, (
            f"function-local in {enclosing.name}(), and this clause found NO escape route "
            "it can read: no `return <name>`, and no store into a container or attribute"
            + (
                f"; it IS passed to {passed_to}, which this clause does NOT treat as an "
                "escape and DECLARES rather than guesses at (DECLARED LIMIT 9)"
                if passed_to
                else ""
            )
            + ". **THAT IS AN OBSERVATION, NOT A PROOF THAT IT CANNOT ESCAPE** — an escape "
            "inside a container literal is invisible here too (DECLARED LIMIT 9)"
        )

    for tag, destination in routes:
        if tag == ESCAPE_STORED:
            return True, (
                f"function-local in {enclosing.name}() but STORED UNDER {destination!r}, "
                "which puts it where a caller can subscript or attribute their way to it "
                "— this is the fourth Assurance seat's ESCAPE 4 ARM 4 shape"
            )
        # ESCAPE_PASSED IS **NOT** TREATED AS AN ESCAPE, AND THAT IS A DELIBERATE WEAKENING
        # WITH A MEASURED REASON. See DECLARED LIMIT 9.
        #
        # This clause first denied by default here — passing an object anywhere counted as
        # reaching. **MEASURED, THAT TURNS THIS PROJECT'S OWN CD-ASR-F03 FIX INTO A
        # VIOLATION:** increment 7 item 3 adds `delattr(guarded, "__wrapped__")`, which is a
        # CALL with `guarded` as an argument, so the deny-by-default rule reclassified
        # `guarded` as a reachable door — the exact outcome `PO-DECISIONS-0012` ruling 1
        # forbids. **AND BOTH WAYS OUT WERE WORSE THAN THE PROBLEM:** an exclusion list of
        # "callees that do not retain" is a VOCABULARY, which is what ruling 2 exists to
        # remove; and decorating `guarded` with `@admits` is prohibited by ruling 1.
        #
        # So the rule is corrected to answer the question actually asked — *can a caller
        # outside this module OBTAIN AND CALL this object* — rather than a broader one
        # ("could anything at all happen to it"). Passing an object to a callee does not by
        # itself create a binding outside this module that a caller can name; it creates the
        # POSSIBILITY that the callee stores it, which is undecidable here. **THE
        # POSSIBILITY IS DECLARED, NOT GUESSED AT IN EITHER DIRECTION.**
        #
        # What is NOT lost: if the CALL'S RESULT is stored or returned, that is caught by
        # the assignment and return rules applied to the RESULT. And the fourth Assurance
        # seat's ESCAPE 4 ARM 4 is a SUBSCRIPT STORE, handled above and unaffected.

    # Everything that remains is a RETURN. The object is reachable exactly where its
    # enclosing function's return value is reachable, so ask the same question one frame out.
    outer_reachable, outer_why = _reachable_public_binding(
        enclosing.name,
        function_chain[:-1],
        bindings,
        bindings["module_level_defs"].get(enclosing.name),
    )
    if outer_reachable:
        return True, (
            f"function-local in {enclosing.name}() and RETURNED from it, and "
            f"{enclosing.name} is itself reachable ({outer_why})"
        )

    if not function_chain[:-1]:
        # The enclosing function is module-level and non-public. Its return value can still
        # escape two ways, and BOTH are followed rather than assumed away.
        decorated = bindings["decorates"].get(enclosing.name, [])
        assigned = bindings["assigned_from"].get(enclosing.name, [])
        destinations = sorted(set(decorated + assigned))
        # ------------------------------------------------------------------------------ #
        # **REACH IS RESOLVED, NOT DENIED. NEW AT WO-2R3 INCREMENT 8** (`PO-DECISIONS-0015`
        # ruling 1). *Superseded wording, quoted rather than deleted (CD-RULE-004,
        # PBG-CONT-003): "its return value reaches only [...], every one of them non-public".*
        # *AND SUPERSEDED WITH IT, THE TWO BRANCHES ABOVE IT, WHICH READ:* `for target in
        # bindings["decorates"]...: if _is_public(target): return True, "...which DECORATES
        # the public module-level ..."` *and the same over* `assigned_from`. **THEY MADE A
        # DECORATOR'S WRAPPER A SECOND DOOR SUBJECT WHENEVER THE THING IT DECORATED WAS
        # PUBLICLY NAMED, AND THAT IS THE SAME CONFLATION READ FROM THE OTHER END**: the
        # object a caller obtains is ONE object, and the obligation belongs at the ONE name a
        # caller writes. **NOTHING IS SILENCED BY THE CHANGE**: a local whose destination is
        # not an enumerated subject still lands in the NETS population, where an undeclared
        # one FAILS `UNCLASSIFIED_INTERCEPTOR`, and a local STORED into a container is caught
        # by the branch above, which is unmoved (ESCAPE 4 ARM 4).
        #
        # **THAT SENTENCE WAS FALSE AND ITS FALSENESS IS GROUND 1.** `guarded`'s return value
        # reaches `_evaluate_dial`, and `_evaluate_dial` was MEASURED being obtained from
        # `sys.modules` and called by a conforming foreign adapter that passed no door. The
        # clause read the destination's SPELLING and concluded nobody could get there.
        #
        # The question is now asked of the destination rather than of its underscore: **is
        # the module-level binding this object reaches ITSELF A SUBJECT OF THIS CHECK?** If it
        # is, the door obligation belongs THERE — at the name a caller actually writes — and
        # is asserted there at that def's own site, so this identifier, which no caller can
        # name, is not a second subject. That is a RESOLUTION and it is stated as one; the
        # object is reachable and this says so.
        # ------------------------------------------------------------------------------ #
        # **RESOLUTION REQUIRES A DESTINATION WITH A DEF SITE TO RESOLVE *TO*.** A
        # module-level `def` has one and the check asserts it there. A module-level ASSIGNMENT
        # — `PUBLIC = _install()` — does NOT: there is no signature and no decorator at that
        # name for anything to assert, so resolving to it would discharge an obligation onto
        # nothing. That case falls through to the reachability branch below and the LOCAL is
        # the door subject, exactly as before. **MEASURED, AND IT IS WHY THIS CONDITION IS
        # TWO CLAUSES AND NOT ONE**: without it, `tests/test_module_level_traversal.py`'s
        # planted `public_evaluator = _install_evaluator()` went from
        # UNDECORATED_JUDGEMENT_PATH_DOOR to UNCLASSIFIED_INTERCEPTOR — the right exit code
        # for the wrong reason, which is the defect increment 8's item 5 had just corrected.
        resolved = [
            target
            for target in destinations
            if target in bindings["module_level_defs"]
            and _is_a_door_binding(target, bindings)
        ]
        if resolved:
            return False, (
                f"function-local in {enclosing.name}(), and the object a caller OBTAINS is "
                f"the module-level binding {resolved[0]!r}, WHICH IS ITSELF AN ENUMERATED "
                "SUBJECT OF THIS CHECK and is asserted as a door at its own def site. "
                "**REACH IS NOT DENIED HERE — IT IS RESOLVED**, and the obligation is "
                "discharged at the name a caller writes rather than at this identifier, "
                "which no caller can name (PO-DECISIONS-0015 ruling 1: never on an "
                "underscore)"
            )
        # REACHABLE, WITH NOWHERE TO RESOLVE THE OBLIGATION TO. The destination is a name a
        # caller can write and it is not a `def` this check asserts, so the LOCAL is the door.
        for target in destinations:
            if _is_public(target):
                return True, (
                    f"function-local in {enclosing.name}(), whose return value reaches the "
                    f"public module-level name {target!r} — and {target!r} is NOT a `def` "
                    "with a signature of its own, so there is nowhere to resolve the "
                    "obligation to and it rests here. This is the fourth Assurance seat's "
                    "ESCAPE 4 shape reached through an assignment rather than a subscript"
                )
        return False, (
            f"function-local in {enclosing.name}(), which is a NON-PUBLIC module-level "
            f"name; its return value reaches only {destinations or ['nothing at module level']}, "
            "and NOT ONE OF THEM IS AN ENUMERATED SUBJECT OF THIS CHECK — none is public and "
            "none returns a judgement value. **THAT IS AN OBSERVATION ABOUT THIS CHECK'S OWN "
            "SUBJECT SET AND NOT A PROOF THAT NOBODY CAN REACH IT**; the NETS population "
            "below is what stops it meaning 'not seen'"
        )

    return False, (
        f"function-local in {enclosing.name}() and returned from it, and {enclosing.name} "
        f"is not reachable ({outer_why})"
    )


def _annotatable_parameters(node, in_class_body: bool) -> list:
    """Every parameter of ``node`` an annotation could be written on, receiver excluded.

    The receiver of a method is excluded for the same reason ``admits`` skips it and by the
    same test — the callable was written inside a ``class`` body and the parameter is in first
    position and named ``self`` or ``cls`` (``crash_detector.admission`` DECLARED LIMIT 2).
    Variadics are excluded because they are refused outright, by their own violation, and
    reporting one twice under two names would be one defect wearing two rows.
    """
    arguments = node.args
    ordered = list(arguments.posonlyargs) + list(arguments.args)
    if in_class_body and ordered and ordered[0].arg in _RECEIVER_NAMES:
        ordered = ordered[1:]
    return ordered + list(arguments.kwonlyargs)


def _decorator_names(node) -> list:
    """Every decorator on ``node``, as the bare name at its head."""
    names = []
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        names.append(getattr(target, "id", None) or getattr(target, "attr", None) or "")
    return names


def _admits_call(node):
    """The ``admits(...)`` call decorating ``node``, or ``None``."""
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Call):
            target = decorator.func
            if (getattr(target, "id", None) or getattr(target, "attr", None)) == ADMITS:
                return decorator
        elif (getattr(decorator, "id", None) or getattr(decorator, "attr", None)) == ADMITS:
            # `@admits` without a call is not a declaration at all.
            return decorator
    return None


def _signature_names(node, in_class_body: bool) -> "tuple[list, list]":
    """The parameter names to establish, and any variadic parameters.

    The receiver rule is READ FROM THE SAME PLACE the runtime reads it: the first parameter
    is dropped only when the callable is written inside a class body AND it is named
    ``self`` or ``cls``. A module-level function whose parameter is named ``cls`` keeps it.
    """
    args = node.args
    ordered = list(args.posonlyargs) + list(args.args)
    if in_class_body and ordered and ordered[0].arg in _RECEIVER_NAMES:
        ordered = ordered[1:]
    names = [a.arg for a in ordered] + [a.arg for a in args.kwonlyargs]
    variadic = []
    if args.vararg:
        variadic.append("*" + args.vararg.arg)
    if args.kwarg:
        variadic.append("**" + args.kwarg.arg)
    return names, variadic


def _returns_a_judgement_value(node) -> bool:
    """Does the return annotation NAME one of the judgement value types?

    Read as source text, because ``from __future__ import annotations`` makes every
    annotation in this codebase a string and half of them are written as strings anyway.
    """
    if node.returns is None:
        return False
    rendered = ast.unparse(node.returns)
    return any(
        name in _identifiers(rendered) for name in JUDGEMENT_VALUE_TYPES
    )


def _identifiers(rendered: str) -> set:
    out: set = set()
    token = ""
    for character in rendered:
        if character.isalnum() or character == "_":
            token += character
        else:
            if token:
                out.add(token)
            token = ""
    if token:
        out.add(token)
    return out


def _established_here_spellings(tree) -> set:
    """Every LOCAL NAME in one module that is bound to ``ESTABLISHED_HERE``.

    **WO-2R3 INCREMENT 6, ITEM C.** Until this increment this check matched the LITERAL
    SPELLING ``ESTABLISHED_HERE`` and nothing else, so ``CD-ASR-WO2R3-01`` §2.4 hid an
    exemption behind ONE WORD::

        from crash_detector.admission import ESTABLISHED_HERE as _EH
        @admits(candidate=_EH("..."))
        def door(candidate): ...

    and measured ``doors check: still reports 16 exemptions, EXIT=0`` — **invisible**. The
    limit that use weakens says of itself *"IT IS COUNTED, NOT HIDDEN"*, and under a one-word
    alias that sentence was false.

    **WHAT IS RESOLVED, EACH DEMONSTRATED:**

    * ``from ... import ESTABLISHED_HERE as <alias>`` — the auditor's route;
    * ``from ... import ESTABLISHED_HERE`` — the plain form, unchanged;
    * ``<name> = ESTABLISHED_HERE`` and ``<name> = <an already-resolved name>`` **AT ANY
      DEPTH** — module level, inside a function body, inside a class body, inside an ``if`` —
      run to a FIXPOINT, so a chain of rebindings resolves too. *Superseded wording, quoted
      rather than deleted (CD-RULE-004, PBG-CONT-003): "at MODULE LEVEL".* **WIDENED AT
      WO-2R3 INCREMENT 7; the function-body case is measured in the fixpoint's own comment;**
    * ``<anything>.ESTABLISHED_HERE`` — an ATTRIBUTE access resolves by its attribute name,
      so ``import crash_detector.admission as adm; adm.ESTABLISHED_HERE`` was already caught
      and still is, whatever ``adm`` is spelled.

    **WHAT IS NOT RESOLVED, AND IT IS DECLARED RATHER THAN LEFT TO BE FOUND** — see DECLARED
    LIMIT 8:

    * *superseded — this read "a name bound INSIDE A FUNCTION BODY (this reads module-level
      bindings only)", and that route is **CLOSED** at WO-2R3 increment 7. The wording is
      quoted rather than deleted (CD-RULE-004, PBG-CONT-003) and the measurement that closed
      it is in the fixpoint's own comment: 16 uses before, 17 after, on one planted alias;*
    * ``getattr(admission, "ESTABLISHED_" + "HERE")`` or any name computed at runtime;
    * an exemption reached through a CONTAINER — ``ALIASES = {"eh": ESTABLISHED_HERE}`` then
      ``@admits(x=ALIASES["eh"]("..."))``;
    * a wrapper — ``def eh(reason): return ESTABLISHED_HERE(reason)`` — which is a call to a
      function, not a reference to the object.

    **THIS IS A REPORTING FIX AND NOT A CLOSURE, AND THE DIFFERENCE IS THE WHOLE OF CD-RULE-006:
    A CHECK REPORTS, A CARRIER FAILS.** The carrier is named and MEASURED in DECLARED LIMIT 8.
    """
    spellings = {ESTABLISHED_HERE}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == ESTABLISHED_HERE:
                    spellings.add(alias.asname or alias.name)
    # REBINDINGS AT ANY DEPTH, TO A FIXPOINT. `_EH = ESTABLISHED_HERE` then `E = _EH` both
    # resolve; the loop runs until nothing new is learned rather than once, because a single
    # pass would resolve the first rebinding and miss the second.
    #
    # **`ast.walk` AND NOT `tree.body`. CLOSED AT WO-2R3 INCREMENT 7** (PO-DECISIONS-0013
    # ruling 6). It read `for node in tree.body` — MODULE LEVEL ONLY — which was the same
    # blind spot `_callables` was widened out of at increment 6, twelve lines away, in the
    # increment dispatched to eliminate it.
    #
    # **THE ESCAPE, MEASURED BEFORE THE FIX RATHER THAN ASSERTED AFTER IT.** Planted into
    # `engine/model.py`: `def _install_door(): EH = ESTABLISHED_HERE` — the alias bound
    # INSIDE A FUNCTION BODY — then `@admits(value=EH("..."))` on a door that escapes to a
    # public module-level name. Before: `ESTABLISHED_HERE uses: 16`, the exemption NOT
    # counted, in a limit whose own text says it is **COUNTED, NOT HIDDEN**.
    #
    # **THE DIRECTION OF THE ERROR IS WHY THIS IS CLOSED RATHER THAN CARRIED.** Widening can
    # now ADD a spelling that a module-level decorator could not actually see — a false row,
    # which is NOISE. Not widening HIDES a weakening, which is the exact failure the limit
    # is named after. Between a noisy count and a silent one, a register that exists to say
    # "this many explicit weakenings" takes the noisy one.
    #
    # **AND THE CARRIER WAS ALREADY REAL, WHICH RESIZES THIS FIX RATHER THAN INFLATING IT**
    # (CD-RULE-006 — a check reports, a carrier fails). Measured on the same plant BEFORE
    # this widening: `tests/test_admission.py::test_the_established_here_exemptions_are_exactly_this_set`
    # ALREADY FAILED, `17 != 16`, because it enumerates from the RUNTIME compiled declaration
    # objects where a spelling cannot matter. **SO THIS IS A REPORTING FIX WITH A CARRIER
    # THAT ALREADY HELD, AND IT CLOSES A GAP IN WHAT THE CHECK SAYS, NOT IN WHAT THE PROJECT
    # REFUSES.** Saying otherwise would be claiming a closure for a note.
    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            value = node.value
            if value is None:
                continue
            source = getattr(value, "id", None) or getattr(value, "attr", None)
            if source not in spellings:
                continue
            targets = (
                node.targets if isinstance(node, ast.Assign) else [node.target]
            )
            for target in targets:
                name = getattr(target, "id", None)
                if name and name not in spellings:
                    spellings.add(name)
                    changed = True
    return spellings


def _established_here_parameters(call, spellings=None) -> list:
    """Which parameters of an ``admits(...)`` call declare ``ESTABLISHED_HERE``.

    ``spellings`` is the module's own set from :func:`_established_here_spellings`. It
    defaults to the literal name alone so this function is still meaningful read on its own,
    but every caller in this check passes the module's set — a default that silently narrowed
    the answer is how item C's defect was written in the first place.
    """
    known = {ESTABLISHED_HERE} if spellings is None else spellings
    found = []
    for keyword in call.keywords:
        if keyword.arg is None:
            continue
        for inner in ast.walk(keyword.value):
            head = inner.func if isinstance(inner, ast.Call) else inner
            if (getattr(head, "id", None) or getattr(head, "attr", None)) in known:
                found.append(keyword.arg)
                break
    return found


def main() -> int:
    arguments = parse_root(
        CHECK_ID,
        "Every public entry point on a judgement path is an `admits` door, and its "
        "declaration matches its signature exactly (BP-AMENDMENT-0001 §D.1).",
    )
    root, code = resolve_root(CHECK_ID, arguments.root)
    if root is None:
        return code
    check = Check(check_id=CHECK_ID, root=root)

    package_root = root / "src" / "crash_detector"
    if not package_root.is_dir():
        return check.refuse(
            f"{package_root} is not a directory. --root must be the repository root of "
            "the tree under audit, not the package directory."
        )

    files = sorted(
        path
        for path in package_root.rglob("*.py")
        if "__pycache__" not in path.parts
    )
    if not files:
        return check.refuse(f"no *.py found under {package_root}.")

    modules_by_rule_1 = 0
    subjects = 0
    #: file -> the non-literal spellings of ESTABLISHED_HERE bound in it. PRINTED at
    #: every run: an alias that resolves silently is only half of 'counted, not hidden'.
    aliased_spellings: dict = {}
    decorated = 0
    #: Function-local callables the reachability clause declined to make doors, with the
    #: reason it gave. Reconciled against DECLARED_NETS after the walk — SET EQUALITY IN
    #: BOTH DIRECTIONS (PO-DECISIONS-0012 ruling 2).
    unreachable_locals: list = []
    exempt_unreachable_local = 0
    #: relative path -> parsed module, kept so the NETS reconciliation can resolve a
    #: declared post-condition IN THE MODULE IT IS DECLARED IN rather than by grepping.
    trees_by_relative: dict = {}
    exempt_private = 0
    exempt_property = 0
    exempt_protocol = 0
    static_or_class_methods = 0
    established_here: list = []
    reached_only_by_rule_2: list = []
    #: THE SECOND DOOR FORM (PO-DECISIONS-0015 ruling 1 (b)). `(module, mechanism) -> the
    #: subjects it derived`, reconciled against DECLARED_DOOR_MECHANISMS after the walk —
    #: SET EQUALITY IN BOTH DIRECTIONS, exactly as the NETS population is.
    mechanisms_used: dict = {}
    derived_doors: list = []

    for path in files:
        source = read_text(check, path)
        if source is None:
            continue
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            check.violation(
                path,
                getattr(exc, "lineno", 0) or 0,
                "UNPARSEABLE",
                f"this file could not be parsed ({exc}). A file inside the scanned set that "
                "the check cannot read is a failure, not a file to pass over.",
            )
            continue

        relative = path.relative_to(package_root)
        in_judgement_package = (
            len(relative.parts) > 1 and relative.parts[0] in JUDGEMENT_PATH_PACKAGES
        )
        if in_judgement_package:
            modules_by_rule_1 += 1

        #: EVERY LOCAL NAME IN THIS MODULE BOUND TO `ESTABLISHED_HERE` (item C). Computed per
        #: module because an alias is a module-local fact, and matched against per parameter
        #: below. Until WO-2R3 increment 6 only the literal spelling was matched and one word
        #: hid an exemption from a limit whose own text says it is COUNTED, NOT HIDDEN.
        spellings = _established_here_spellings(tree)
        if spellings != {ESTABLISHED_HERE}:
            aliased_spellings[str(relative)] = sorted(spellings - {ESTABLISHED_HERE})

        bindings = _module_bindings(tree)
        # RULE 1 MEMBERSHIP IS A PROPERTY OF THE MODULE AND NOT OF THE TREE, so it is attached
        # here rather than computed inside `_module_bindings`. `_is_a_door_binding` needs it to
        # ask the SAME subject question `main` asks, so the two cannot disagree.
        bindings["in_judgement_package"] = in_judgement_package
        # RELATIVE TO `src/`, NOT to the package root, so a declared net's `module` field
        # reads `crash_detector/engine/evaluate.py` — the spelling a reader recognises as
        # the module — rather than the package-internal `engine/evaluate.py`.
        relative_src = str(path.relative_to(package_root.parent))
        trees_by_relative[relative_src] = tree
        mechanisms_here = [
            mechanism
            for mechanism in DECLARED_DOOR_MECHANISMS
            if mechanism.module == relative_src
        ]

        for node, in_class_body, class_node, function_chain in _callables(tree):
            # ---------------------------------------------------------------- #
            # THE MEMBERSHIP CLAUSE — REACHABILITY, NOT NAME-PREFIX.
            # PO-DECISIONS-0012 ruling 2. See _reachable_public_binding for the criterion
            # and for why it is not a subtler name heuristic.
            # ---------------------------------------------------------------- #
            reachable, why = _reachable_public_binding(
                node.name, function_chain, bindings, node
            )
            if not reachable:
                if function_chain:
                    # A function-local callable this clause declines to make a door. THE
                    # RULING'S SENTENCE: "'Not a door' must never again mean 'not seen.'"
                    # It is recorded here and reconciled against DECLARED_NETS below, so
                    # the only way out of this branch is a written declaration.
                    unreachable_locals.append(
                        (
                            relative_src,
                            node.lineno,
                            ".".join([f.name for f in function_chain] + [node.name]),
                            why,
                            node,
                            in_judgement_package or _returns_a_judgement_value(node),
                            ".".join(f.name for f in function_chain),
                        )
                    )
                    exempt_unreachable_local += 1
                else:
                    exempt_private += 1
                continue
            decorators = _decorator_names(node)
            if "property" in decorators or any(d == "setter" for d in decorators):
                exempt_property += 1
                continue
            if in_class_body and _is_protocol(class_node):
                exempt_protocol += 1
                continue
            if "staticmethod" in decorators or "classmethod" in decorators:
                static_or_class_methods += 1

            by_rule_1 = in_judgement_package
            by_rule_2 = _returns_a_judgement_value(node)
            if not (by_rule_1 or by_rule_2):
                continue

            subjects += 1
            where = _where(class_node, node, function_chain)
            if by_rule_2 and not by_rule_1:
                reached_only_by_rule_2.append(f"{relative}:{node.lineno} {where}")

            call = _admits_call(node)
            # ------------------------------------------------------------------------ #
            # **FORM 2 — THE DERIVED DOOR. NEW AT WO-2R3 INCREMENT 8** (`PO-DECISIONS-0015`
            # ruling 1 (b)). A subject decorated by a mechanism declared in
            # `tools/register/declared_door_mechanisms.py` establishes its arguments by
            # DERIVING them from its own signature, so there is no `admits(...)` argument
            # list to compare against the signature — the signature IS the declaration.
            # What is asserted instead is the pair of artefact properties the derivation
            # requires and refuses without: EVERY PARAMETER ANNOTATED, NO VARIADIC. Both are
            # checked below, and the mechanism itself is checked against its own source in
            # the reconciliation after this walk. **A ROW IN THAT REGISTER BUYS A SUBJECT
            # NOTHING ON ITS OWN.**
            # ------------------------------------------------------------------------ #
            derived_by = [
                mechanism
                for mechanism in mechanisms_here
                if mechanism.mechanism in decorators
            ]
            if derived_by and call is None:
                mechanism = derived_by[0]
                mechanisms_used.setdefault(
                    (relative_src, mechanism.mechanism), []
                ).append(f"{relative}:{node.lineno} {where}")
                decorated += 1
                derived_doors.append(
                    f"{relative}:{node.lineno} {where} — derived by {mechanism.mechanism}()"
                )
                names, variadic = _signature_names(node, in_class_body)
                check.asserted()
                if variadic:
                    check.violation(
                        path,
                        node.lineno,
                        "OPEN_CHANNEL",
                        f"{where} is a DERIVED door and declares {', '.join(variadic)}. A "
                        "variadic parameter has no name in the signature, and the name in "
                        "the signature is what the establishment is derived FROM. "
                        f"{mechanism.mechanism}() refuses this at import; it is a violation "
                        "here too so it is visible without running anything.",
                    )
                check.asserted()
                unannotated = [
                    parameter.arg
                    for parameter in _annotatable_parameters(node, in_class_body)
                    if parameter.annotation is None
                ]
                if unannotated:
                    check.violation(
                        path,
                        node.lineno,
                        "DERIVED_DOOR_PARAMETER_NOT_ANNOTATED",
                        f"{where} is a DERIVED door and its parameter(s) {unannotated} carry "
                        "NO ANNOTATION. **THE ANNOTATION IS THE DECLARATION** for this door "
                        f"form, so a parameter without one is a parameter with no "
                        f"establishment. {mechanism.mechanism}() raises AdmissionFault at "
                        "import rather than admitting it; this is the same fact read without "
                        "importing anything (BP-AMENDMENT-0001 §D.1, planted violation P7).",
                    )
                continue
            if call is None:
                check.asserted()
                check.violation(
                    path,
                    node.lineno,
                    "UNDECORATED_JUDGEMENT_PATH_DOOR",
                    f"{where} is a public entry point on a judgement path and it carries no "
                    f"@{ADMITS}(...). BP-AMENDMENT-0001 §D.1: every such door establishes "
                    "each of its arguments by exact type AT THE DOOR, derived from the "
                    "signature and not written into the body. A door whose establishment "
                    "lives in its body stops establishing the moment the body is rewritten, "
                    "which is CD-ASR-F03's shape exactly.",
                )
                continue
            if not isinstance(call, ast.Call):
                check.asserted()
                check.violation(
                    path,
                    node.lineno,
                    "ADMITS_NOT_CALLED",
                    f"{where} is decorated with a bare @{ADMITS} rather than "
                    f"@{ADMITS}(...). A decorator that declares nothing declares nothing.",
                )
                continue

            decorated += 1
            established_here.extend(
                f"{relative}:{node.lineno} {where}({parameter})"
                for parameter in _established_here_parameters(call, spellings)
            )

            names, variadic = _signature_names(node, in_class_body)
            check.asserted()
            if variadic:
                check.violation(
                    path,
                    node.lineno,
                    "OPEN_CHANNEL",
                    f"{where} declares {', '.join(variadic)}. A variadic parameter is the "
                    "general case of a parameter the declaration was not told about: "
                    "values arrive through it with no name to declare and no type to "
                    "require. The runtime refuses every call to such a door; it is a "
                    "violation here too so it is visible without running anything.",
                )
            if any(keyword.arg is None for keyword in call.keywords):
                check.violation(
                    path,
                    node.lineno,
                    "DECLARATION_UNREADABLE",
                    f"{where}'s @{ADMITS}(**...) is built from an expression this check "
                    "cannot read. A declaration a static reader cannot enumerate cannot be "
                    "checked against the signature, and an unreadable declaration is not a "
                    "declaration.",
                )
                continue

            declared = [keyword.arg for keyword in call.keywords]
            check.asserted()
            undeclared = [name for name in names if name not in declared]
            adrift = [name for name in declared if name not in names]
            if undeclared:
                check.violation(
                    path,
                    node.lineno,
                    "PARAMETER_NOT_DECLARED_TO_ADMITS",
                    f"{where} has parameter(s) {undeclared} in its signature that "
                    f"@{ADMITS}() was not told about. A new argument on a judgement-path "
                    "door arrives REFUSED, never unguarded (planted violation P7). The "
                    "runtime refuses every call to this door; this is the same fact read "
                    "without importing anything.",
                )
            if adrift:
                check.violation(
                    path,
                    node.lineno,
                    "DECLARATION_ADRIFT_FROM_SIGNATURE",
                    f"{where}'s @{ADMITS}() was told about {adrift}, which are not "
                    "parameters of it. A declaration that has come adrift from its "
                    "signature is guarding a door that is not there.",
                )

    # ================================================================================== #
    # THE SECOND POPULATION — **NETS**. PO-DECISIONS-0012 ruling 2.
    #
    #   "A second declared population is created: NETS — function-local post-condition
    #    guards on judgement paths — enumerated and asserted exactly as doors are, each with
    #    its post-condition named. 'Not a door' must never again mean 'not seen.' Zero
    #    unclassified interceptors on any judgement path."
    #
    # ASSERTED, NOT PRINTED, AND IN BOTH DIRECTIONS. The doors population is asserted by
    # violating on an undecorated subject; this one is asserted by violating on a member of
    # either set that is not in the other, and by checking each declaration AGAINST THE CODE
    # rather than reading it. A declaration nothing can falsify is a hand-maintained summary.
    # ================================================================================== #
    # IDENTITY IS (module, ENCLOSING FUNCTION) AND NOT (module, the net's own qualname).
    # The first version of this reconciliation keyed on the net's own name and FAILED THE
    # RENAME TEST, MEASURED: `guarded` -> `_guarded` took the check from PASS to FAIL with
    # NET_DECLARED_BUT_ABSENT, because the register was identifying its member by an
    # identifier no caller can name — PO-DECISIONS-0012 ruling 2's own defect, reintroduced
    # in the fix for it. The enclosing function is a MODULE-LEVEL name, so it is a name a
    # reader can look up and a caller can reference.
    on_a_judgement_path = [row for row in unreachable_locals if row[5]]
    found_nets = {(row[0], row[6]) for row in on_a_judgement_path}
    declared_nets = {(net.module, net.enclosing) for net in DECLARED_NETS}

    for relative, lineno, qualname, why, node, _, enclosing in on_a_judgement_path:
        check.asserted()
        if (relative, enclosing) not in declared_nets:
            check.violation(
                package_root.parent / relative,
                lineno,
                "UNCLASSIFIED_INTERCEPTOR",
                f"{qualname} is a function-local callable ON A JUDGEMENT PATH that the "
                f"reachability clause declined to make a door ({why}), AND IT IS NOT "
                "DECLARED AS A NET. PO-DECISIONS-0012 ruling 2: \"'Not a door' must never "
                "again mean 'not seen.'\" Declare it in tools/register/declared_nets.py "
                "with the callable that IS its post-condition named — or make it a door. "
                "**ADDING A ROW THERE IS NOT AN EXEMPTION**: the declaration is checked "
                "against the code and fails if the post-condition is not actually called.",
            )

    for net in DECLARED_NETS:
        check.asserted()
        if (net.module, net.enclosing) not in found_nets:
            check.violation(
                package_root.parent / net.module,
                0,
                "NET_DECLARED_BUT_ABSENT",
                f"a NET is declared inside {net.enclosing}() in {net.module} "
                "(tools/register/declared_nets.py) and this walk found no unreachable "
                "function-local callable there. **THREE CAUSES AND THE ROW CANNOT TELL "
                "THEM APART, SO ALL THREE ARE NAMED:** it was DELETED; the enclosing "
                f"function {net.enclosing}() was RENAMED; or the callable BECAME REACHABLE "
                "and is now a door. A declaration outliving the thing it describes is how a "
                "register stops being evidence. Correct the declaration or restore the net.",
            )
            continue

        tree = trees_by_relative.get(net.module)
        siblings = [
            row for row in on_a_judgement_path
            if (row[0], row[6]) == (net.module, net.enclosing)
        ]
        check.asserted()
        if len(siblings) > 1:
            check.violation(
                package_root.parent / net.module,
                siblings[0][1],
                "AMBIGUOUS_NET",
                f"{net.enclosing}() in {net.module} holds "
                f"{len(siblings)} unreachable function-local callables "
                f"({[row[2] for row in siblings]}) and this row cannot say which one it "
                "declares. **THE INSTRUMENT REFUSES TO GUESS.** Identity here is the "
                "ENCLOSING function precisely so it does not depend on a local identifier; "
                "the cost of that choice is this case, and it is a refusal rather than a "
                "silent first-match.",
            )
            continue
        node = siblings[0][4]
        # MODULE SCOPE, not `tree.body` — a post-condition defined inside a module-level
        # `if`/`try` block is resolvable at runtime and was UNRESOLVABLE here until WO-2R3
        # increment 8 (`F-06-K`). The error direction of the old reading was a FALSE
        # VIOLATION, not a silence, which is why it is the least dangerous of the four
        # sites and is still wrong.
        module_level = {
            child.name
            for child in (module_level_statements(tree) if tree else [])
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        check.asserted()
        if net.post_condition not in module_level:
            check.violation(
                package_root.parent / net.module,
                node.lineno,
                "NET_POST_CONDITION_UNRESOLVABLE",
                f"the NET inside {net.enclosing}() declares its post-condition as "
                f"{net.post_condition!r}, and there is no module-level def of that name in "
                f"{net.module}. **A NET'S POST-CONDITION IS NAMED AS DATA, NOT DESCRIBED IN "
                "PROSE** (PO-DECISIONS-0012 ruling 2) — a name that resolves to nothing is "
                "prose with a colon in it.",
            )
            continue

        check.asserted()
        called = {
            _callee_name(inner)
            for inner in ast.walk(node)
            if isinstance(inner, ast.Call)
        }
        if net.post_condition not in called:
            check.violation(
                package_root.parent / net.module,
                node.lineno,
                "NET_POST_CONDITION_NOT_CALLED",
                f"the NET inside {net.enclosing}() declares {net.post_condition!r} as its post-condition and "
                "ITS BODY DOES NOT CALL IT. This is the assertion that makes the "
                "declaration data rather than a label: a maintainer who removes the call "
                "and leaves the declaration alone has removed the guard and kept the "
                "paperwork, which is CD-ASR-F03's own shape.",
            )
            continue

        check.asserted()
        # MODULE SCOPE, not `tree.body` — and this site is the one whose old reading could
        # RAISE `StopIteration` rather than report, because the resolution above and this
        # fetch used the same narrow reading and would have disagreed the moment they did
        # not. WO-2R3 increment 8, `F-06-K`.
        post = next(
            child for child in module_level_statements(tree)
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            and child.name == net.post_condition
        )
        if _admits_call(post) is None:
            check.violation(
                package_root.parent / net.module,
                post.lineno,
                "NET_POST_CONDITION_NOT_A_DOOR",
                f"the NET inside {net.enclosing}(): its post-condition {net.post_condition!r} carries no "
                f"@{ADMITS}(...). A net exists to check what a body returned; a "
                "post-condition that does not establish its own arguments believes whatever "
                "the body hands it, which is the failure the net was written to prevent, "
                "one layer in.",
            )

    # ================================================================================== #
    # THE SECOND DOOR FORM — **DECLARED DERIVING MECHANISMS**. PO-DECISIONS-0015 ruling 1 (b).
    #
    # A row in tools/register/declared_door_mechanisms.py is checked AGAINST THE CODE, exactly
    # as a NETS row is, and for the same reason: a register whose rows nothing can falsify is
    # a hand-maintained summary. Four assertions per row, and set equality in both directions.
    # ================================================================================== #
    for mechanism in DECLARED_DOOR_MECHANISMS:
        tree = trees_by_relative.get(mechanism.module)
        module_defs = {
            child.name: child
            for child in (module_level_statements(tree) if tree else [])
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        check.asserted()
        if mechanism.mechanism not in module_defs:
            check.violation(
                package_root.parent / mechanism.module,
                0,
                "MECHANISM_DECLARED_BUT_ABSENT",
                f"a DERIVING DOOR MECHANISM {mechanism.mechanism}() is declared in "
                f"{mechanism.module} (tools/register/declared_door_mechanisms.py) and there "
                "is no module-level def of that name there. **TWO CAUSES AND THE ROW CANNOT "
                "TELL THEM APART, SO BOTH ARE NAMED:** it was DELETED, or it was RENAMED. "
                "Either way every subject it used to make a door is now UNDECORATED and is "
                "reported as such beside this — TWO violations, never a silence.",
            )
            continue

        # THE MECHANISM'S REACH: its own body, plus the module-level functions it calls. Both,
        # because a mechanism of any size delegates — this project's own splits
        # `_establishment_derived_from` and `_body_materials` out of the decorator — and an
        # assertion that read only the decorator would be satisfied by a one-line wrapper
        # round anything at all.
        subject_node = module_defs[mechanism.mechanism]
        reach = [subject_node]
        for inner in ast.walk(subject_node):
            if isinstance(inner, ast.Call):
                called = module_defs.get(_callee_name(inner))
                if called is not None and called not in reach:
                    reach.append(called)
        calls_anywhere = {
            _callee_name(inner)
            for reached in reach
            for inner in ast.walk(reached)
            if isinstance(inner, ast.Call)
        }

        check.asserted()
        if "signature" not in calls_anywhere:
            check.violation(
                package_root.parent / mechanism.module,
                subject_node.lineno,
                "MECHANISM_DOES_NOT_READ_THE_SIGNATURE",
                f"{mechanism.mechanism}() is declared a DERIVING mechanism and neither it nor "
                "any module-level function it calls reads `inspect.signature`. "
                "BP-AMENDMENT-0001 §D.1's rule is that the establishment is DERIVED FROM THE "
                "SIGNATURE rather than written into the body; a mechanism that never reads a "
                "signature is not deriving from one, whatever the register calls it.",
            )
        check.asserted()
        if "declaration" not in calls_anywhere:
            check.violation(
                package_root.parent / mechanism.module,
                subject_node.lineno,
                "MECHANISM_DOES_NOT_USE_THE_ONE_VOCABULARY",
                f"{mechanism.mechanism}() is declared a DERIVING mechanism and neither it nor "
                "any module-level function it calls compiles its declarations through "
                "`crash_detector.admission.declaration`. **THERE IS ONE DECLARATION "
                "VOCABULARY IN THIS PROJECT AND THIS IS HOW IT STAYS ONE.** Two vocabularies "
                "that drift apart is how a reader comes to believe a parameter is established "
                "as strictly as it says it is when it is not.",
            )
        check.asserted()
        if not mechanisms_used.get((mechanism.module, mechanism.mechanism)):
            check.violation(
                package_root.parent / mechanism.module,
                subject_node.lineno,
                "MECHANISM_DECORATES_NOTHING",
                f"{mechanism.mechanism}() is declared a DERIVING door mechanism and this walk "
                "found NO subject it decorates. A declared mechanism with no subject is a row "
                "that has outlived the thing it describes, which is the hand-maintained "
                "summary this register exists not to be.",
            )

    declared_mechanisms = {(m.module, m.mechanism) for m in DECLARED_DOOR_MECHANISMS}
    check.note(
        "DERIVING DOOR MECHANISMS — THE SECOND DOOR FORM (PO-DECISIONS-0015 ruling 1 (b)). "
        f"DECLARED: {len(declared_mechanisms)}. SUBJECTS THEY DERIVED: {len(derived_doors)}. "
        "**A ROW IS NOT AN EXEMPTION**: the mechanism must exist, must read "
        "`inspect.signature`, and must compile through `crash_detector.admission.declaration` "
        "— and at every subject it derives, EVERY PARAMETER MUST BE ANNOTATED and NO "
        "PARAMETER MAY BE VARIADIC, which are the two artefact properties the derivation "
        "itself refuses without."
    )
    for row in derived_doors:
        check.note(f"  DERIVED DOOR: {row}")
    for mechanism in DECLARED_DOOR_MECHANISMS:
        check.note(
            f"  MECHANISM: {mechanism.module}::{mechanism.mechanism}() — DERIVES FROM "
            f"{mechanism.derives_from[:150]}... DOES NOT ESTABLISH: "
            f"{mechanism.what_it_does_not_establish[:150]}..."
        )

    check.note(
        f"NETS — THE SECOND DECLARED POPULATION (PO-DECISIONS-0012 ruling 2). FOUND: "
        f"{len(found_nets)}. DECLARED: {len(declared_nets)}. NOT DECLARED BUT FOUND: "
        f"{len(found_nets - declared_nets)}. DECLARED BUT NOT FOUND: "
        f"{len(declared_nets - found_nets)}. **SET EQUALITY IS ASSERTED IN BOTH DIRECTIONS, "
        "NOT PRINTED** — and each declaration is checked AGAINST THE CODE: the "
        "post-condition must be a module-level def in that module, the net's body must "
        "actually CALL it, and it must itself be an admits door."
    )
    for net in DECLARED_NETS:
        found_leaf = [
            row[2] for row in on_a_judgement_path
            if (row[0], row[6]) == (net.module, net.enclosing)
        ]
        check.note(
            f"  NET: {net.module} inside {net.enclosing}() — FOUND AS {found_leaf or 'NOTHING'}; "
            f"post-condition {net.post_condition}(). **THE LEAF NAME IS REPORTED AND IS "
            "LOAD-BEARING FOR NOTHING** — identity is the enclosing MODULE-LEVEL name, so "
            "renaming the local does not move this verdict. DOES NOT BIND: "
            f"{net.what_it_does_not_bind[:130]}..."
        )
    off_path = [row for row in unreachable_locals if not row[5]]
    check.note(
        f"UNREACHABLE FUNCTION-LOCAL CALLABLES **NOT** ON A JUDGEMENT PATH: {len(off_path)}. "
        "These are NOT nets and are NOT declared, because ruling 2's population is "
        "'function-local post-condition guards ON JUDGEMENT PATHS' and this check does not "
        "widen a Product Owner's population on its own authority. **THEY ARE PRINTED SO "
        "THAT 'not a net' DOES NOT BECOME THE NEW 'not seen'** — which is the exact defect "
        "ruling 2 exists to prevent, one population over."
    )
    for relative, lineno, qualname, why, _node, _, _enclosing in off_path:
        check.note(f"  NOT A DOOR, NOT ON A JUDGEMENT PATH: {relative}:{lineno} {qualname} — {why}")

    check.note(
        f"RULE 1 (judgement-path packages, deny-by-default within): "
        f"{'/'.join(JUDGEMENT_PATH_PACKAGES)} — {modules_by_rule_1} module(s) read."
    )
    check.note(
        f"RULE 2 (return-type reach, anywhere under src/): reached "
        f"{len(reached_only_by_rule_2)} door(s) rule 1 did not."
    )
    for row in reached_only_by_rule_2:
        check.note(f"  by rule 2 only: {row}")
    check.note(f"SUBJECTS ENUMERATED: {subjects}. DECORATED: {decorated}.")
    check.note(
        f"EXEMPT: {exempt_private} non-public module-level or method names, "
        f"{exempt_unreachable_local} UNREACHABLE function-local callable(s) "
        f"(the WO-2R3 increment-7 reachability clause — each one is enumerated above, as a "
        f"NET if it is on a judgement path and as a printed row if it is not), "
        f"{exempt_property} @property accessor(s), {exempt_protocol} Protocol stub(s)."
    )
    check.note(
        f"staticmethod/classmethod in the subject set: {static_or_class_methods} "
        "(DECLARED LIMIT 2 in src/crash_detector/admission.py assumes this is 0)."
    )
    check.note(
        f"ESTABLISHED_HERE uses: {len(established_here)}. RESOLVED THROUGH ALIASES since "
        "WO-2R3 increment 6 (PO-DECISIONS-0011 ruling 1 item (c)): an import alias, a "
        "module-level rebinding run to a FIXPOINT, and any attribute spelled "
        f"`.{ESTABLISHED_HERE}` all count here. Until this increment ONLY the literal name "
        "did, and one word hid a use from a limit whose own text says it is COUNTED, NOT "
        "HIDDEN. What is still NOT resolved is DECLARED LIMIT 8, not a silence."
    )
    check.note(
        f"MODULES BINDING A NON-LITERAL SPELLING OF {ESTABLISHED_HERE}: "
        f"{len(aliased_spellings)}. A resolved alias is only half of 'counted, not hidden' — "
        "the other half is that a reader can SEE it was spelled differently."
    )
    for where, names in sorted(aliased_spellings.items()):
        check.note(f"  ALIAS: {where} binds {names}")
    for row in established_here:
        check.note(f"  ESTABLISHED_HERE: {row}")
    in_the_collectors = [
        row for row in established_here if row.startswith(f"{CD_BP_003_PACKAGE}/")
    ]
    # CD-BP-003 IS THE PROTOCOL BOUNDARY OF A6 AND NOTHING ELSE. The four parameters of
    # `collect` are separated from the establishment doors that share the package, because
    # a declared limit reported wider than it is, is as useless as one reported narrower:
    # a reader who cannot tell which of eight rows is the risk has not been told the risk.
    cd_bp_003 = [row for row in in_the_collectors if f" {A6_DOOR}(" in row]
    establishment_doors = [row for row in in_the_collectors if row not in cd_bp_003]
    check.note(
        f"DECLARED LIMIT 3 — CD-BP-003, THE PROTOCOL BOUNDARY THAT ADMITS: "
        f"{len(cd_bp_003)} parameter(s) of {A6_DOOR}() under {CD_BP_003_PACKAGE}/. "
        "BP-AMENDMENT-0001 §D.3 part 2: adapter, sink, ledger and validator keep their "
        "Protocols because the thing on the other side is genuinely foreign; every value "
        "they RETURN is established at the point of return. THIS IS A DOOR THAT ADMITS, NOT "
        "AN ABSENCE OF A DOOR, and it is BLUEPRINT §17's softest remaining surface — the "
        "Product Owner named it the fourth Assurance seat's first target. See the header "
        "for the executable example, which is an object that IS ADMITTED, and for what is "
        "NOT PROVED TO BE CARRIED ANYWHERE."
    )
    for row in cd_bp_003:
        check.note(f"  CD-BP-003 ADMITS: {row}")
    check.note(
        f"  (also under {CD_BP_003_PACKAGE}/, and NOT CD-BP-003: {len(establishment_doors)} "
        "ESTABLISHMENT DOOR parameter(s) — callables whose whole contract is to accept any "
        "object and establish or describe it, the same kind of use as own_model_id(value). "
        "Listed above with the rest; separated here so the risk is not reported wider than "
        "it is.)"
    )
    check.note(
        f"{CD_BP_003_PACKAGE}/ IS a judgement-path package under RULE 1 as of WO-2R3 "
        "increment 3. The increment-2 declaration that it was deferred BY SCOPE is "
        "DISCHARGED and is not restated."
    )
    check.note(
        "DECLARED LIMIT 1 — CONSTRUCTORS ARE STILL NOT SUBJECTS *OF THIS CHECK*, AND SINCE "
        "WO-2R3 INCREMENT 5 THAT IS NO LONGER AN UNCARRIED GAP. This check reads CALLABLES; "
        "a constructor is not one of its subjects, and V17 still leaves it exiting 0. THE "
        "CARRIER IS NAMED AND MEASURED (CD-RULE-006): "
        "crash_detector.establishment.establishes, enumerated and asserted by "
        "tools/register/check_constructor_field_establishment.py — RUN IT AND READ ITS OWN "
        "POPULATION LINE. THIS NOTE CITES NEITHER THAT CLASS'S DEFINITION NOR ITS COUNT, "
        "AND UNTIL PO-DECISIONS-0010 RULING 1 IT CITED BOTH: it read '...which measures the "
        "body-borne field-establishment class at 32 members'. That was a FOURTH place "
        "holding a copy of a sibling limit's definition and count with no rule pointing at "
        "it (CD-PL-F91) — CD-RULE-004's three places are each limit's OWN — and the ruling "
        "widened that class to BODY-BORNE OR ABSENT and moved the count, so the copy went "
        "stale exactly as an unpointed-at copy does. A COUNT READ FROM A SIBLING'S RUN IS A "
        "MEASUREMENT; A COUNT COPIED HERE IS A TRANSCRIPTION (CD-RULE-009). WHAT IS STILL "
        "NOT CARRIED is a CROSS-FIELD invariant, which no declared field list can state — "
        "that is residue (ii) of the constructor check's own DECLARED LIMIT 1, and the "
        "widening did not touch it. The superseded wording of this note is quoted in full "
        "in this file's header rather than deleted."
    )

    return check.done(
        f"{len(files)} file(s) under {package_root.relative_to(root)}; "
        f"{subjects} judgement-path door(s)"
    )


def _callables(tree):
    """Every function definition **AT ANY NESTING DEPTH**, with its enclosing class if any.

    **THIS IS WO-2R3 INCREMENT 6'S STRUCTURAL CHANGE TO THIS INSTRUMENT** (item B1,
    PO-DECISIONS-0011 ruling 2). It used to read ``tree.body`` — TOP LEVEL ONLY — plus the
    direct members of top-level public classes, and it did not declare that. Its sibling
    ``check_constructor_field_establishment.py`` had the same blind spot. **BOTH GOVERNING
    INSTRUMENTS SHARED IT AND NEITHER DECLARED IT.**

    ``CD-ASR-WO2R3-01`` measured the four arms against the same undecorated public door:

    ======================================  ==========
    where the door was defined              doors check
    ======================================  ==========
    module-level ``def``                    exit 1
    method of a TOP-LEVEL class             exit 1
    method nested one level (Outer.Inner)   **exit 0**
    function-local ``def``                  **exit 0** — and live, ``POLICY["decide"]``
                                            accepted unestablished arguments
    ======================================  ==========

    Both zeros are now ones.

    **THE ENCLOSING-CLASS RULE IS UNCHANGED IN SUBSTANCE AND WIDER IN REACH.** The old code
    skipped the members of a NON-PUBLIC top-level class. That is preserved, and it is now
    applied to the whole chain: a callable is skipped if ANY enclosing class is non-public,
    which is the same judgement — "nothing outside can name this" — asked of every level
    rather than only the first. **NO NEW EXEMPTION IS INTRODUCED HERE.** The three the check
    declares (non-public name, ``@property``, ``Protocol`` stub) are untouched and are still
    the only ones, and each is still counted in the output.

    ``in_class_body`` is TRUE only when the callable's IMMEDIATE parent is a class, because
    that is what it is used for — deciding whether a receiver parameter is skipped — and a
    function defined inside a METHOD has no receiver of its own.

    **THE FOURTH YIELD, NEW AT WO-2R3 INCREMENT 7** (``PO-DECISIONS-0012`` ruling 2): the
    chain of ENCLOSING FUNCTIONS, outermost first. It is empty for a module-level ``def`` and
    for a method, and non-empty for exactly the callables whose own identifier is a local
    variable nobody outside can name. :func:`_reachable_public_binding` needs it, and it is
    yielded rather than recomputed so the walk and the membership clause cannot disagree
    about what encloses what.
    """
    def descend(node, class_chain, immediate_class, function_chain):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if all(_is_public(name) for name in class_chain):
                    yield child, immediate_class is not None, immediate_class, function_chain
                yield from descend(child, class_chain, None, function_chain + [child])
            elif isinstance(child, ast.ClassDef):
                yield from descend(
                    child, class_chain + [child.name], child, function_chain
                )
            else:
                yield from descend(child, class_chain, immediate_class, function_chain)

    yield from descend(tree, [], None, [])


def _is_protocol(class_node) -> bool:
    if class_node is None:
        return False
    for base in class_node.bases:
        if (getattr(base, "id", None) or getattr(base, "attr", None)) == "Protocol":
            return True
    return False


def _where(class_node, node, function_chain=()) -> str:
    """The name to PRINT for a callable, qualified by whatever encloses it.

    **THE FUNCTION CHAIN IS INCLUDED SINCE WO-2R3 INCREMENT 7, AND ITS ABSENCE WAS A REAL
    REPORTING DEFECT** found by this increment's own carrier: a function-local door was
    reported as the bare leaf name, so a reader was told ``_decide is a public entry point``
    with no way to find which function it lives in. The traversal has walked at any nesting
    depth since increment 6; the REPORTING had not caught up, and a violation a reader
    cannot locate is a violation half-delivered.
    """
    enclosing = [f.name for f in function_chain]
    if class_node is not None:
        enclosing.append(class_node.name)
    prefix = ".".join(enclosing)
    return f"{prefix}.{node.name}" if prefix else node.name


if __name__ == "__main__":
    raise SystemExit(main())
