#!/usr/bin/env python3
"""THE CLASS-2 SWEEP — every delegated judgement on the deciding paths, with a denominator.

    python3 -B tools/sweep/delegated_judgement_sweep.py --root .
    python3 -B tools/sweep/delegated_judgement_sweep.py --root . --list        # the table
    python3 -B tools/sweep/delegated_judgement_sweep.py --root . --list-undeclared

===========================================================================================
WHY THIS EXISTS, AND WHAT IT IS NOT
===========================================================================================
CD-AC-005's finding CD-ASR-WO2R-F02 was the FOURTH constructor route to ``Agrees`` after a
boundary had said "THREE MEASURED, and three is the denominator, not a proof that a fourth
does not exist". The hedge was honest and it did its job. What was missing was a way to say
what the denominator IS.

**THIS TOOL IS THE ENUMERATION, NOT THE CLOSURE, AND THE DIFFERENCE IS THE WHOLE POINT.**
The closure is :mod:`crash_detector.own_terms`: values are RE-CONSTRUCTED at the door, so no
method a caller defined runs while anything is being decided. That property is a runtime
property of the values and it does not depend on this file existing. What this file does is
make the SURFACE countable, and fail when the surface changes without anyone saying so.

It is a STATIC, INTRA-PROCEDURAL, AST-BASED LOCATOR. Every escape on this project's record
passed a static checker. Do not read a clean run of this tool as evidence that any class is
closed — read it as evidence that the set of places where a judgement COULD be delegated is
the set that was declared, and that each of them has a written disposition.

===========================================================================================
THE DENOMINATOR, AND THE METHOD BY WHICH IT IS TAKEN
===========================================================================================
**THE SUBJECT SET** is the transitive intra-package import closure of the six modules that
host a judgement about staleness, agreement or reading-ness — computed here, from the import
graph, rather than listed by hand:

    crash_detector.serving.witness_resolver   (agreement: resolve_panel, render_panel)
    crash_detector.witness.panel              (agreement: the sum type and its constructors)
    crash_detector.staleness                  (staleness: the window and the evidence)
    crash_detector.engine.evaluate            (staleness + reading-ness: the dial path)
    crash_detector.dials.reading              (reading-ness: fold, is_value)
    crash_detector.serving.dial_presentation  (reading-ness: what a surface may show)

The closure is OVER-INCLUSIVE ON PURPOSE. It is taken over MODULES, not over functions, so a
module that is imported for one constant still contributes every site it contains. An
over-inclusive denominator can only make this tool complain about places that do not matter;
an under-inclusive one is how a route goes uncounted.

**THE SITE SET** is every AST node in a subject module at which an operation could be
executed by an object the enclosing module did not construct. Two tiers, because the
dispatch asks for one and the class is the other:

  TIER 1 — ADMISSION.  ``isinstance``, ``issubclass``, ``hasattr``, ``getattr``. These are
  the sites the finding is literally about: a test that admits a value, and admits a
  subclass with it.

  TIER 2 — THE DECIDING OPERATION.  ``<  >  <= >= == !=`` (``__lt__`` and kin), ``in`` /
  ``not in`` (``__eq__`` and ``__hash__``), ``+ - * / % //`` (``__add__`` and kin),
  ``min`` / ``max`` / ``sorted`` / ``sum`` / ``math.fsum`` (``__lt__``), ``float`` / ``int``
  / ``str`` / ``len`` / ``bool`` / ``hash`` / ``math.isfinite`` / ``tuple`` / ``frozenset``
  / ``set`` / ``dict`` / ``list`` (``__float__``, ``__len__``, ``__iter__`` and kin), the
  set operators, truthiness in an ``if`` or behind a ``not``, and ``is`` / ``is not``
  (listed because identity is the one that is NEVER delegated, so it is the contrast).
  Tier 2 is where the auditor's variant actually did its work: ``isinstance`` let the object
  in, and ``__rsub__`` decided the answer.

**EVERY SITE CARRIES A WRITTEN DISPOSITION**, one of:

    ESTABLISHED   the operand was re-established by crash_detector.own_terms before this
                  operation, so what runs is CPython's implementation for an exact base type
    EXACT         the check is exact-type identity, or a comparison between class objects of
                  types this package sealed against subclassing
    OWN           both operands are values this module constructed in the same scope
    DELEGATED     the deciding operation IS executed by a supplied object — OPEN, and the
                  note says under whose authority it is left open
    OUT_OF_BOUND  reached by the sweep and DECLARED as outside this increment's scope

**AND SINCE WO-2R3 INCREMENT 7, THREE MORE — DRAFTED BY THE PROJECT LEAD, NOT YET RATIFIED**
(``PO-DECISIONS-0013`` ruling 3). The fifth Assurance seat's T8 measured the eleven undeclared
sites as THREE CATEGORIES where this form assumed one, and *"writing eleven dispositions into
a form that does not fit them would be the hand-maintained-summary defect with a signature"*.
**AN ENTRY USING ONE OF THESE IS ``(word, EVIDENCE MAPPING)`` AND NOT ``(word, note)``:**

    DEFECT_OPEN            a caller-influenceable route EXISTS and has been MEASURED. The
                           site is a real defect, recorded OPEN. **IT BUYS NOTHING** — not a
                           pass, not an exemption, and it does not make this sweep green.
                           REQUIRES: ``finding``, ``measured_reach``, ``counterfactual``.
    CARRIER_ONLY           reached by NO module under ``src/``; its only callers are carriers,
                           so the consequence of a false answer is CARRIER CREDIBILITY and not
                           product judgement. REQUIRES: ``callable``,
                           ``why_it_is_not_product_judgement``. **``callable`` IS
                           MACHINE-CHECKED — this word is an ENUMERATION, NOT A CLAIM, and it
                           fails the day a product module calls the thing.**
    UPSTREAM_OF_THE_PATH   not itself a judgement path, and in the closure anyway, because
                           what it decides is whether judgement-path doors establish their
                           arguments at all. **THE OPPOSITE OF AN EXCUSE.**
                           REQUIRES: ``decides``, ``route``.

**THE WORDS ARE A CONTRACT, NOT A LABEL SET.** An unrecognised word, a malformed entry, or an
extended word missing any mandatory evidence field is a VIOLATION — ``UNKNOWN_DISPOSITION``,
``MALFORMED_DISPOSITION``, ``DISPOSITION_EVIDENCE_MISSING``, ``CARRIER_ONLY_HAS_A_PRODUCT_CALLER``.

**AND SINCE THE WO-2R3 RECORD ACT, A FINDINGS REGISTER AND A REDRAFTED THIRD WORD**
(``PO-DECISIONS-0014`` ruling 1; ``PO-DECISIONS-0015`` rulings 4 and 6).

  * ``governance/findings/findings-register.json`` is the MINIMAL findings register the ruling
    ordered — ``id``, ``raised_at``, ``status``, **nothing else**, enforced by key-set equality.
    Every ``finding`` a register entry cites must resolve there as ``OPEN`` or the entry
    REFUSES: ``FINDING_DOES_NOT_RESOLVE``, ``FINDING_IS_NOT_OPEN``. Until this act the
    ``finding`` field was an unchecked string, which is the gap the ruling closed rather than
    shipped.
  * ``UPSTREAM_OF_THE_PATH`` was **REJECTED AS DRAFTED** — *"it binds the module register where
    its siblings bind the site register, and its fields are prose no machine can check"* — and
    is REDRAFTED. It is no longer admitted in :data:`DECLARED_MODULE_DISPOSITIONS` at all
    (``WORD_NOT_ADMITTED_IN_MODULE_REGISTER``), and its two fields are now machine-checked:
    ``operand_origin`` must be a member of the CLOSED set :data:`OPERAND_ORIGINS`, and ``gates``
    must be a SITE KEY that EXISTS in this run's own measured site set and lies in a DIFFERENT
    module. ``CALLER_SUPPLIED`` additionally requires a resolvable ``finding``.
  * **THE SITE REGISTER NOW COVERS BOTH TIERS.** :data:`DECLARED_ADMISSIONS` may carry tier-2
    site keys as well as tier-1 ones, and a module in the closure is DECLARED either by a
    :data:`DECLARED_MODULE_DISPOSITIONS` entry **or** by carrying a site entry for EVERY ONE of
    its tier-2 site keys — a DERIVED module answer, computed from the site register and never
    accepted as a sentence. Remove one tier-2 entry and the module goes UNDECLARED again.

**A DEFECT THAT WAS ALREADY HERE AND IS CLOSED BY THE SAME CHANGE:** until increment 7 the
``DISPOSITIONS`` tuple was consulted **only to print the summary table**. A register entry
carrying a word that was not in it was silently accepted, counted into nothing, and never
shown — so the one thing the vocabulary existed to constrain, it did not constrain. That now
fails, for the original five exactly as hard as for the new three.

**THE ELEVEN DISPOSITIONS ARE NOT WRITTEN AND ARE NOT THIS CONTRACT'S AUTHOR'S** (CD-D-130).
This increment lands the FORM; the Product Owner ratifies the words; the Project Lead then
writes the contents. Every extended count below reads **0** at this SHA and that is correct.

**THE REGISTER IS ASSERTED BY SET EQUALITY IN BOTH DIRECTIONS.** A site with no disposition
fails this tool, and a disposition for a site that no longer exists fails it too — because a
register that only complained about additions could be satisfied by deleting the entry that
does the complaining. That is the same argument
:data:`crash_detector.dials.reading.DECLARED_MEMBER_SURFACE` already makes about a class
dictionary.

===========================================================================================
DECLARED LIMIT (CD-RULE-004). This tool CLOSES NOTHING; it counts.
===========================================================================================
 1  IT IS STATIC AND INTRA-PROCEDURAL. It reads one expression at a time and does not know
    what any name is bound to at runtime. A disposition of ESTABLISHED is a CLAIM BY THIS
    SEAT about the code around the site, not something this tool verified. The runtime
    evidence for those claims is ``tests/test_own_terms.py`` and the variants under
    ``variants/WO-2R2/CLASS-2/``, and the claim an auditor should attack is the disposition
    text, not the count.
    CARRIER FOR THE RUNTIME HALF, MEASURED: crash_detector.own_terms, exercised by
    tests/test_own_terms.py (29 tests) and by the variants. For a site whose disposition is
    wrong, NOT PROVED TO BE CARRIED ANYWHERE — a mis-declared disposition is invisible here
    by construction.

 2  IT SEES ONLY OPERATORS AND CALLS WRITTEN LITERALLY IN THE SUBJECT MODULES. An operation
    reached through ``operator.lt``, ``functools.reduce``, a dunder invoked by name, a
    comprehension over a caller's generator, or any C-level protocol call CPython makes on
    this code's behalf is NOT a node this tool visits.
    MEASURED EXAMPLE, executable: a module writing ``operator.__lt__(a, b)`` instead of
    ``a < b`` produces no site here. NOT PROVED TO BE CARRIED ANYWHERE at the static layer;
    the RUNTIME layer carries it, because own_terms re-establishes the VALUE and an
    operation on an established value is CPython's whichever syntax reaches it.

 3  ITS SUBJECT SET IS AN IMPORT CLOSURE, SO A MODULE THAT REACHES A JUDGEMENT WITHOUT
    IMPORTING ONE OF THE SIX IS OUTSIDE IT. Nineteen names of this package are outside the
    closure — six package ``__init__`` modules and thirteen real ones — and every run prints
    them by name so the exclusion is disclosed rather than discovered. The claim that none of
    them decides staleness, agreement or reading-ness is a claim about THIS SHA, made by
    reading them, and it is the claim to attack: ``crash_detector.collectors.*`` CONSTRUCTS
    the timestamps that are later judged, and ``crash_detector.publication.*`` renders what
    was decided, but neither decides. NOT PROVED TO BE CARRIED ANYWHERE.

 4  A DISPOSITION IS KEYED BY THE EXPRESSION'S TEXT, so renaming a local variable makes the
    site UNDECLARED and this tool FAILS. That is the safe direction and it is deliberate: it
    is better to be asked to re-declare a site than to have a register quietly follow a
    rename. It also means a clean run of this tool is evidence about THIS SOURCE TEXT and
    survives no rewriting of it.
"""

from __future__ import annotations

import argparse
import ast
import collections
import json
import pathlib
import sys

PACKAGE = "crash_detector"

#: The six modules that host a judgement about staleness, agreement or reading-ness. The
#: subject set is their transitive intra-package import closure, computed at run time.
JUDGEMENT_ENTRY_MODULES: tuple = (
    "crash_detector.serving.witness_resolver",
    "crash_detector.witness.panel",
    "crash_detector.staleness",
    "crash_detector.engine.evaluate",
    "crash_detector.dials.reading",
    "crash_detector.serving.dial_presentation",
)

TIER_1_ADMISSION = ("ISINSTANCE", "ISSUBCLASS", "DUCK")

_ORDERING_CALLS = frozenset({"min", "max", "sorted", "sum", "fsum"})
_COERCION_CALLS = frozenset(
    {
        "float",
        "int",
        "str",
        "len",
        "bool",
        "hash",
        "isfinite",
        "tuple",
        "frozenset",
        "set",
        "dict",
        "list",
        "next",
        "iter",
    }
)

#: THE FIVE ORIGINAL WORDS. A register entry using one of these is ``(word, note)`` where
#: ``note`` is prose, and that shape is UNCHANGED by this increment.
DISPOSITIONS = ("ESTABLISHED", "EXACT", "OWN", "DELEGATED", "OUT_OF_BOUND")

# ======================================================================================= #
# THE EXTENDED DISPOSITION VOCABULARY — **THE REGISTER CONTRACT.**
# WO-2R3 increment 7, PO-DECISIONS-0013 ruling 3:
#
#   *"The disposition vocabulary is EXTENDED FIRST. T8 measured three categories where the
#    form assumed one; writing eleven dispositions into a form that does not fit them would
#    be the hand-maintained-summary defect with a signature. The Project Lead drafts the
#    extended vocabulary (register-contract change, PO ratifies in-increment); THEN the
#    eleven are written."*
#
# **THE SPLIT IS SHARP AND THIS FILE IS ON ONE SIDE OF IT.** The Project Lead DRAFTED these
# three words. This file IMPLEMENTS THE CONTRACT THAT ACCEPTS THEM. The Product Owner
# RATIFIES. The Project Lead then writes the eleven dispositions in
# ``tools/sweep/declared_dispositions.py`` — **WHICH IS NOT THIS SEAT'S FILE AND CONTAINS NOT
# ONE WORD OF THIS SEAT'S** (CD-D-130).
#
# **THE WORDS ARE NOT RATIFIED.** This contract accepts them so the Product Owner can rule on
# something that EXISTS rather than on a proposal. If the ruling changes a word or drops one,
# this table is where that lands, and the eleven have not yet been written against it. That
# ordering is the whole of ruling 3.
#
# THE BINDING CONSTRAINT, VERBATIM FROM THE DISPATCH:
#   **"NO NEW WORD MAY BE A SYNONYM FOR 'NOT LOOKED AT'. The instrument must REJECT a
#   disposition whose mandatory evidence fields are absent — the words are a contract, not a
#   label set, and a vocabulary that can be satisfied with prose is the hand-maintained-
#   summary defect that ruling 3 exists to prevent."**
#
# **AND THE DEFECT THAT WAS ALREADY HERE, FOUND WHILE BUILDING THIS AND CLOSED BY IT.** Until
# this increment ``DISPOSITIONS`` WAS USED ONLY FOR PRINTING. A register entry carrying a
# word that is not in it was silently accepted, counted into nothing, and never printed — so
# the one thing the tuple existed to constrain, it did not constrain. ``UNKNOWN_DISPOSITION``
# below is that hole closed, and it binds the original five exactly as hard as the new three.
# ======================================================================================= #

#: word -> the evidence fields a register entry using it MUST carry, each present and
#: NON-EMPTY. An entry using one of these words is ``(word, evidence_mapping)`` and **not**
#: ``(word, note)``: the whole point is that prose is not enough for these three.
EXTENDED_DISPOSITIONS = {
    # A caller-influenceable route to this deciding operand EXISTS and has been MEASURED.
    # The site is a real defect, recorded OPEN, remediation owed and not yet done.
    # **IT BUYS NOTHING** — not a pass, not an exemption, and it does not make the sweep
    # green. A register full of DEFECT_OPEN is a register honestly describing a broken
    # system, and that is the word's entire purpose.
    "DEFECT_OPEN": ("finding", "measured_reach", "counterfactual"),
    # This site is reached by NO module under `src/`. Its only callers are carriers — tests
    # and instruments — so the consequence of a false answer is CARRIER CREDIBILITY, not
    # product judgement. **`callable` IS MACHINE-CHECKED**: see `_carrier_only_violations`.
    # This word is an ENUMERATION, NOT A CLAIM, and it breaks the build the day somebody
    # adds an import.
    "CARRIER_ONLY": ("callable", "why_it_is_not_product_judgement"),
    # **REDRAFTED BY PO-DECISIONS-0014 RULING 1, WHICH REJECTED IT AS DRAFTED.** This site is
    # not itself a judgement path AND belongs in the closure anyway, because what it decides
    # is whether judgement-path doors establish their arguments at all. **IT IS THE OPPOSITE
    # OF AN EXCUSE**, and under the redraft it cannot be written without saying WHERE THE
    # OPERAND CAME FROM and NAMING A CONCRETE DOWNSTREAM POINT IN ANOTHER MODULE. The drafted
    # fields (`decides`, `route`) were prose no machine could check and are GONE.
    "UPSTREAM_OF_THE_PATH": ("operand_origin", "gates"),
}

#: Every word the register may use. Anything else is `UNKNOWN_DISPOSITION`.
ALL_DISPOSITIONS = tuple(DISPOSITIONS) + tuple(EXTENDED_DISPOSITIONS)

# ======================================================================================= #
# THE REDRAFTED `UPSTREAM_OF_THE_PATH` — `PO-DECISIONS-0014` ruling 1:
#
#   *"REJECTED AS DRAFTED, for exactly the reasons its own author measured: it binds the
#    module register where its siblings bind the site register, and its fields are prose no
#    machine can check. It is REDRAFTED to bind the SITE register with machine-checkable
#    fields."*
#
# THREE THINGS CHANGED AND EACH ONE CAN BE MADE TO FAIL:
#
#  (a) **THE WORD IS NOT ADMITTED IN THE MODULE REGISTER AT ALL.** It lives only in
#      :data:`DECLARED_ADMISSIONS` — the SITE register — where its siblings live.
#      `WORD_NOT_ADMITTED_IN_MODULE_REGISTER`.
#  (b) **`operand_origin` IS MEMBERSHIP IN A CLOSED SET THIS INSTRUMENT OWNS.** Not a
#      sentence about where the operand came from — one of four names, and any other string
#      refuses. `OPERAND_ORIGIN_NOT_IN_THE_CLOSED_SET`.
#  (c) **`gates` IS A SITE KEY AND NOT A ROUTE DESCRIPTION.** It must EXIST in this run's own
#      measured site set and it must lie in a DIFFERENT module from the declaring site.
#      `GATES_SITE_DOES_NOT_EXIST`, `GATES_SITE_IS_IN_THE_DECLARING_MODULE`. The claim the
#      word exists to make — *"what this decides is whether judgement-path doors establish at
#      all"* — was previously prose. It now names a concrete downstream point, and **the day
#      that point moves, is renamed, or dies, the row refuses.** A claim about a route that
#      survives the route disappearing is not a claim.
#
# AND THE CONDITIONAL FIELD, WHICH IS THE WHOLE POINT OF THE WORD: if `operand_origin` is
# `CALLER_SUPPLIED`, the entry MUST also carry `finding`, and that finding must resolve to an
# `OPEN` row in the findings register or the row REFUSES
# (`CALLER_SUPPLIED_WITHOUT_A_FINDING`, then `FINDING_DOES_NOT_RESOLVE`/`FINDING_IS_NOT_OPEN`).
# **THERE IS NO SPELLING OF `UPSTREAM_OF_THE_PATH` THAT RECORDS A CALLER-CONTROLLED OPERAND
# AND CLAIMS NOTHING IS WRONG.** The old draft's `route` field could be satisfied by a
# sentence; this one cannot be satisfied at all without a fact the instrument independently
# holds.
# ======================================================================================= #

#: **A CLOSED SET, OWNED BY THIS INSTRUMENT.** Where the deciding operand at this site came
#: from. Any other string is `OPERAND_ORIGIN_NOT_IN_THE_CLOSED_SET`.
OPERAND_ORIGINS = (
    # written in the source of the declaring module or in a `@admits`/`@establishes`
    # declaration that a module wrote about itself
    "SOURCE_DECLARATION",
    # a constant of this module or of an imported one, resolved at import
    "MODULE_CONSTANT",
    # a value this module constructed in this scope, so the operation is CPython's
    "OWN_CONSTRUCTION",
    # the operand, or the object the operand is read out of, reaches here from a caller.
    # **REQUIRES A `finding` THAT RESOLVES OPEN.**
    "CALLER_SUPPLIED",
)

#: The word(s) :data:`DECLARED_MODULE_DISPOSITIONS` may NOT carry. Exactly what the ruling
#: named and not one word more — being stricter than a ruling is still departing from it.
WORDS_NOT_ADMITTED_IN_THE_MODULE_REGISTER = ("UPSTREAM_OF_THE_PATH",)


def _upstream_of_the_path_violations(declared_admissions, declared_modules, site_keys):
    """Every redrafted-word entry whose machine-checked fields do not hold.

    Returns a list of ``(rule, where, detail)``. **THE `finding` HALF IS DELIBERATELY NOT
    HERE** — it is `_finding_resolution_violations`, which checks EVERY citation in EITHER
    register, so `DEFECT_OPEN` and `UPSTREAM_OF_THE_PATH` cannot drift apart on it.
    """
    found: list = []
    for key, value in declared_modules.items():
        if isinstance(value, tuple) and value and value[0] in WORDS_NOT_ADMITTED_IN_THE_MODULE_REGISTER:
            found.append((
                "WORD_NOT_ADMITTED_IN_MODULE_REGISTER", str(key),
                f"{value[0]!r} is a SITE disposition and this is the MODULE register. "
                "PO-DECISIONS-0014 ruling 1 rejected it as drafted BECAUSE it *\"binds the "
                "module register where its siblings bind the site register\"*. A module "
                "answer for this word is DERIVED from per-site entries and is never written.",
            ))
    for key, value in declared_admissions.items():
        if not (isinstance(value, tuple) and len(value) >= 2):
            continue
        word, evidence = value[0], value[1]
        if word != "UPSTREAM_OF_THE_PATH" or not isinstance(evidence, dict):
            continue
        where = f"{key[0]}::{key[1]} {key[2]}: {key[3]}" if isinstance(key, tuple) else str(key)
        origin = evidence.get("operand_origin")
        if origin not in OPERAND_ORIGINS:
            found.append((
                "OPERAND_ORIGIN_NOT_IN_THE_CLOSED_SET", where,
                f"{origin!r} is not an operand origin. The CLOSED set is "
                f"{list(OPERAND_ORIGINS)}. **THE DRAFTED FIELDS WERE PROSE NO MACHINE COULD "
                "CHECK, AND THIS IS WHAT REPLACED THEM.**",
            ))
        gates = evidence.get("gates")
        gates = tuple(gates) if isinstance(gates, (list, tuple)) else gates
        if not (isinstance(gates, tuple) and len(gates) == 4
                and all(isinstance(part, str) for part in gates)):
            found.append((
                "GATES_SITE_DOES_NOT_EXIST", where,
                f"`gates` is a SITE KEY 4-tuple (module, qualname, category, expression); "
                f"found {evidence.get('gates')!r}.",
            ))
        elif gates not in site_keys:
            found.append((
                "GATES_SITE_DOES_NOT_EXIST", where,
                f"`gates` names {gates!r}, which is NOT in this run's measured site set. "
                "**A CLAIM ABOUT A ROUTE THAT SURVIVES THE ROUTE DISAPPEARING IS NOT A "
                "CLAIM.** The day the gated point moves, is renamed, or dies, this row "
                "refuses — which is the entire reason the field is a key and not a sentence.",
            ))
        elif isinstance(key, tuple) and gates[0] == key[0]:
            found.append((
                "GATES_SITE_IS_IN_THE_DECLARING_MODULE", where,
                f"`gates` names a site in {gates[0]}, which is the DECLARING site's own "
                "module. The word asserts that this site is UPSTREAM of a judgement path; a "
                "site that only gates its own module has not been shown to be upstream of "
                "anything.",
            ))
        if origin == "CALLER_SUPPLIED" and not _finding_ids(evidence):
            found.append((
                "CALLER_SUPPLIED_WITHOUT_A_FINDING", where,
                "`operand_origin: CALLER_SUPPLIED` requires a `finding` that resolves OPEN. "
                "**THERE IS NO SPELLING OF THIS WORD THAT RECORDS A CALLER-CONTROLLED OPERAND "
                "AND CLAIMS NOTHING IS WRONG.** The binding constraint the word was drafted "
                "against was *\"no new word may be a synonym for 'not looked at'\"*, and this "
                "clause is where that is true.",
            ))
    return found


# ======================================================================================= #
# THE FINDINGS REGISTER — `PO-DECISIONS-0014` ruling 1, verbatim:
#
#   *"this project has finding IDs and NO FINDINGS REGISTER, so the `finding` field would be
#    an unchecked string. A MINIMAL findings register is created in the same act — id,
#    raised_at (boundary SHA), status (OPEN / CLOSED / SUPERSEDED), nothing else — and
#    `DEFECT_OPEN.finding` resolves against it or the row refuses. An index, not a system."*
#
# **IT IS JSON AND NOT PYTHON, DELIBERATELY.** A register that executes can compute its own
# answer; this one cannot do anything but be read. It is the same reasoning
# `governance/reconciliation/` gives for storing its probes as `.txt` — *"so that they are
# DATA"*.
#
# **`nothing else` IS ENFORCED AND IS NOT A STYLE NOTE.** A row whose key set is not EXACTLY
# {id, raised_at, status} is REFUSED, because a findings register that grows a `title` and a
# `severity` becomes the hand-maintained summary the ruling created it to stop. The finding's
# SUBSTANCE lives in the document that raised it — a verdict, a reconciliation record, a
# build-log entry. **This index answers ONE question: does this id exist, and is it open?**
#
# It is resolved from THIS FILE's location and not from `--root`, for the same reason
# `_load_register` is: an auditor runs this tool out of a tree it extracted itself, with no
# PYTHONPATH, no installed package and no wrapper (`PBG-ASSURE-001`).
# ======================================================================================= #

#: The closed set of statuses. Anything else REFUSES the register.
FINDING_STATUSES = ("OPEN", "CLOSED", "SUPERSEDED")

#: Exactly the three fields a row may carry. Not a minimum — an EQUALITY.
FINDING_FIELDS = frozenset({"id", "raised_at", "status"})

#: `tools/sweep/` -> repository root -> the register.
FINDINGS_REGISTER_PATH = (
    pathlib.Path(__file__).resolve().parent.parent.parent
    / "governance" / "findings" / "findings-register.json"
)


def _load_findings_register(path=None):
    """Read the minimal findings register. Returns ``(rows_by_id, problems)``.

    ``problems`` is a list of ``(rule, where, detail)`` in the sweep's own violation shape, so
    a malformed register FAILS THE RUN rather than raising out of it — an instrument that dies
    on its own input tells an auditor less than one that reports.
    """
    problems: list = []
    path = pathlib.Path(path) if path is not None else FINDINGS_REGISTER_PATH
    if not path.is_file():
        return {}, [(
            "FINDINGS_REGISTER_ABSENT", str(path),
            "PO-DECISIONS-0014 ruling 1 requires a findings register that DEFECT_OPEN.finding "
            "resolves against. Without it every `finding` is an unchecked string again.",
        )]
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        return {}, [("FINDINGS_REGISTER_UNREADABLE", str(path), f"{type(exc).__name__}: {exc}")]
    if not isinstance(rows, list):
        return {}, [(
            "FINDINGS_REGISTER_UNREADABLE", str(path),
            f"the register is a list of rows; found {type(rows).__name__}",
        )]
    by_id: dict = {}
    for index, row in enumerate(rows):
        where = f"{path.name}[{index}]"
        if not isinstance(row, dict) or set(row) != FINDING_FIELDS:
            problems.append((
                "FINDINGS_REGISTER_ROW_MALFORMED", where,
                f"a row carries EXACTLY {sorted(FINDING_FIELDS)} and NOTHING ELSE; found "
                f"{sorted(row) if isinstance(row, dict) else type(row).__name__}. "
                "**`nothing else` IS PART OF THE RULING.** A findings register that carries "
                "prose becomes the hand-maintained summary it was created to stop.",
            ))
            continue
        identifier, raised_at, status = row["id"], row["raised_at"], row["status"]
        if not isinstance(identifier, str) or not identifier.strip():
            problems.append(("FINDINGS_REGISTER_ROW_MALFORMED", where, "id is absent or empty"))
            continue
        if identifier in by_id:
            problems.append((
                "FINDINGS_REGISTER_DUPLICATE_ID", where,
                f"{identifier!r} appears twice. An index with two answers for one id is not an "
                "index.",
            ))
            continue
        if status not in FINDING_STATUSES:
            problems.append((
                "FINDINGS_REGISTER_BAD_STATUS", f"{where} {identifier}",
                f"{status!r} is not a status. The closed set is {list(FINDING_STATUSES)}.",
            ))
            continue
        if not (isinstance(raised_at, str) and len(raised_at) == 40
                and all(character in "0123456789abcdef" for character in raised_at)):
            problems.append((
                "FINDINGS_REGISTER_BAD_SHA", f"{where} {identifier}",
                f"raised_at is a full 40-character lower-case commit SHA; found {raised_at!r}. "
                "An abbreviated SHA is a transcription, and this project has a rule about "
                "those (CD-RULE-009, CD-PL-F36). **THIS CHECK IS SHAPE ONLY: it does NOT "
                "prove the object exists in any repository, and it cannot — the tool runs "
                "from an extraction with no git. NOT PROVED TO BE CARRIED ANYWHERE.**",
            ))
            continue
        by_id[identifier] = {"raised_at": raised_at, "status": status}
    return by_id, problems


def _finding_ids(evidence):
    """The finding ids an evidence mapping cites: one string, or a list/tuple of strings."""
    cited = evidence.get("finding")
    if isinstance(cited, str):
        return [cited] if cited.strip() else []
    if isinstance(cited, (list, tuple)):
        return [one for one in cited if isinstance(one, str) and one.strip()]
    return []


def _finding_resolution_violations(declared_admissions, declared_modules, findings):
    """**THE HALF OF `DEFECT_OPEN` THAT WAS AN UNCHECKED STRING UNTIL THIS ACT.**

    Every `finding` cited by any register entry must name a row in the findings register whose
    status is `OPEN`, or the entry REFUSES. Two distinct refusals, because they are two
    distinct mistakes: an id that resolves against NOTHING, and an id that resolves against a
    row somebody has already closed.
    """
    found: list = []
    for register, kind in ((declared_admissions, "ADMISSION"), (declared_modules, "MODULE")):
        for key, value in register.items():
            if not (isinstance(value, tuple) and len(value) >= 2):
                continue
            word, evidence = value[0], value[1]
            if word not in EXTENDED_DISPOSITIONS or not isinstance(evidence, dict):
                continue
            where = (
                f"{key[0]}::{key[1]} {key[2]}: {key[3]}" if isinstance(key, tuple) else str(key)
            )
            cited = _finding_ids(evidence)
            if "finding" in evidence and not cited:
                # **THE HOLE THIS CLOSES IS THE ONE `str(()).strip()` LEAVES OPEN.** The
                # mandatory-field check tests non-emptiness by stringifying, and `str(())` is
                # `"()"` — non-empty. An entry carrying `finding: ()` would therefore satisfy
                # the contract and cite nothing at all.
                found.append((
                    "FINDING_DOES_NOT_RESOLVE", where,
                    f"{word} carries a `finding` field that names NO id "
                    f"({evidence.get('finding')!r}). An empty citation is not a citation.",
                ))
            for identifier in cited:
                row = findings.get(identifier)
                if row is None:
                    found.append((
                        "FINDING_DOES_NOT_RESOLVE", where,
                        f"{word} cites finding {identifier!r}, which is NOT in the findings "
                        f"register. **A `finding` FIELD THAT RESOLVES AGAINST NOTHING IS AN "
                        f"UNCHECKED STRING**, which is the gap PO-DECISIONS-0014 ruling 1 "
                        f"closed rather than shipped.",
                    ))
                elif row["status"] != "OPEN":
                    found.append((
                        "FINDING_IS_NOT_OPEN", where,
                        f"{word} cites finding {identifier!r}, whose status is "
                        f"{row['status']!r}. A disposition that rests on a finding somebody "
                        "has closed is a disposition whose reason has died.",
                    ))
    return found


def _disposition_contract_violations(declared_admissions, declared_modules):
    """Every register entry whose WORD or EVIDENCE does not satisfy the contract.

    **THIS IS THE HALF OF RULING 3 THAT IS NOT A VOCABULARY.** A word list is a label set;
    what makes it a CONTRACT is that an entry which does not carry the word's mandatory
    evidence is REFUSED. Returns a list of ``(rule, where, detail)``.
    """
    found = []
    for register, kind in (
        (declared_admissions, "ADMISSION"),
        (declared_modules, "MODULE"),
    ):
        for key, value in register.items():
            where = f"{key[0]}::{key[1]} {key[2]}: {key[3]}" if isinstance(key, tuple) else str(key)
            if not isinstance(value, tuple) or len(value) < 2:
                found.append((
                    "MALFORMED_DISPOSITION", where,
                    f"a {kind} entry must be (word, note-or-evidence); found {value!r}",
                ))
                continue
            word, evidence = value[0], value[1]
            if word not in ALL_DISPOSITIONS:
                found.append((
                    "UNKNOWN_DISPOSITION", where,
                    f"{word!r} is not a disposition. The vocabulary is "
                    f"{list(ALL_DISPOSITIONS)}. **UNTIL WO-2R3 INCREMENT 7 AN UNRECOGNISED "
                    "WORD WAS SILENTLY ACCEPTED AND SILENTLY UNPRINTED** — the one thing "
                    "the vocabulary existed to constrain, it did not constrain.",
                ))
                continue
            if word not in EXTENDED_DISPOSITIONS:
                continue
            required = EXTENDED_DISPOSITIONS[word]
            if not isinstance(evidence, dict):
                found.append((
                    "DISPOSITION_EVIDENCE_MISSING", where,
                    f"{word} requires an EVIDENCE MAPPING carrying {list(required)}, not "
                    f"prose. Found {type(evidence).__name__}. **A VOCABULARY THAT CAN BE "
                    "SATISFIED WITH PROSE IS THE HAND-MAINTAINED-SUMMARY DEFECT RULING 3 "
                    "EXISTS TO PREVENT.**",
                ))
                continue
            for field in required:
                if not str(evidence.get(field, "")).strip():
                    found.append((
                        "DISPOSITION_EVIDENCE_MISSING", where,
                        f"{word} requires {field!r} and it is absent or empty. "
                        "**NO NEW WORD MAY BE A SYNONYM FOR 'NOT LOOKED AT'.**",
                    ))
    return found


def _carrier_only_violations(declared_admissions, sources, subject):
    """**`CARRIER_ONLY` IS AN ENUMERATION, NOT A CLAIM, AND THIS IS WHERE THAT IS TRUE.**

    The word asserts *"this site is reached by NO module under ``src/``"*. The draft says the
    register *"must be able to show that no caller exists under ``src/``, by instrument, and
    FAIL when one appears. A ``CARRIER_ONLY`` that becomes false when somebody adds an import
    must break the build the day they add it."*

    So the declared ``callable`` is looked for as a CALL in every module of the swept subject
    other than the one that defines it. Any hit is a violation.

    **WHAT THIS CHECK DOES NOT SEE, DECLARED HERE RATHER THAN LEFT TO BE FOUND:** a call
    reached through an alias (``f = admission_faults; f(x)``), through ``getattr`` on a
    module, or through a container. It reads CALL EXPRESSIONS BY NAME. That is the same
    class of limit the doors instrument declares for ``ESTABLISHED_HERE``, and it means this
    check is a FLOOR on the caller set and not a proof of its emptiness.
    """
    found = []
    for key, value in declared_admissions.items():
        if not (isinstance(value, tuple) and len(value) >= 2):
            continue
        word, evidence = value[0], value[1]
        if word != "CARRIER_ONLY" or not isinstance(evidence, dict):
            continue
        name = str(evidence.get("callable", "")).strip()
        if not name:
            continue
        defining_module = key[0] if isinstance(key, tuple) else None
        for module in subject:
            if module == defining_module:
                continue
            tree = sources.get(module)
            if tree is None:
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                target = node.func
                called = getattr(target, "id", None) or getattr(target, "attr", None)
                if called == name:
                    found.append((
                        "CARRIER_ONLY_HAS_A_PRODUCT_CALLER",
                        f"{key[0]}::{key[1]}" if isinstance(key, tuple) else str(key),
                        f"{name!r} is declared CARRIER_ONLY — 'reached by NO module under "
                        f"src/' — and {module} calls it at line {node.lineno}. **THE WORD "
                        "ASSERTS AN ENUMERATION AND THE ENUMERATION IS NOW FALSE.** Either "
                        "the caller is wrong or the disposition is.",
                    ))
    return found


class SweepFailed(SystemExit):
    pass


# ------------------------------------------------------------------------------------- #
# the enumerator
# ------------------------------------------------------------------------------------- #


class _Sites(ast.NodeVisitor):
    def __init__(self, module: str) -> None:
        self.module = module
        self.scope: list = []
        self.sites: list = []

    def _qualname(self) -> str:
        return ".".join(self.scope) or "<module>"

    def _record(self, node: ast.AST, category: str) -> None:
        self.sites.append(
            (self.module, self._qualname(), category, _normalise(ast.unparse(node)))
        )

    def visit_FunctionDef(self, node) -> None:
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node) -> None:
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_Call(self, node) -> None:
        func = node.func
        name = None
        if isinstance(func, ast.Name):
            name = func.id
        elif isinstance(func, ast.Attribute):
            name = func.attr
        if name == "isinstance":
            self._record(node, "ISINSTANCE")
        elif name == "issubclass":
            self._record(node, "ISSUBCLASS")
        elif name in ("hasattr", "getattr"):
            self._record(node, "DUCK")
        elif name in _ORDERING_CALLS:
            self._record(node, "ORDERING")
        elif name in _COERCION_CALLS:
            self._record(node, "COERCION")
        self.generic_visit(node)

    def visit_Compare(self, node) -> None:
        for op in node.ops:
            if isinstance(op, (ast.Is, ast.IsNot)):
                self._record(node, "IDENTITY")
            elif isinstance(op, (ast.In, ast.NotIn)):
                self._record(node, "MEMBERSHIP")
            else:
                self._record(node, "COMPARE")
        self.generic_visit(node)

    def visit_BinOp(self, node) -> None:
        if isinstance(
            node.op,
            (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow, ast.FloorDiv),
        ):
            self._record(node, "ARITH")
        elif isinstance(node.op, (ast.BitOr, ast.BitAnd, ast.BitXor)):
            self._record(node, "SETOP")
        self.generic_visit(node)

    def visit_If(self, node) -> None:
        if not isinstance(node.test, (ast.Compare, ast.Call)):
            self._record(node.test, "TRUTHINESS")
        self.generic_visit(node)

    def visit_UnaryOp(self, node) -> None:
        if isinstance(node.op, ast.Not) and not isinstance(
            node.operand, (ast.Compare, ast.Call)
        ):
            self._record(node.operand, "TRUTHINESS")
        self.generic_visit(node)


def _normalise(text: str) -> str:
    """One line, single-spaced. A site's key must not move when a line is re-wrapped."""
    return " ".join(text.split())


def _module_name(path: pathlib.Path, package_root: pathlib.Path) -> str:
    relative = path.relative_to(package_root.parent).with_suffix("")
    parts = list(relative.parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _closure(sources: dict) -> set:
    """The transitive intra-package import closure of the six judgement entry modules."""
    imports = collections.defaultdict(set)
    for module, tree in sources.items():
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith(PACKAGE):
                    imports[module].add(node.module)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith(PACKAGE):
                        imports[module].add(alias.name)
    reached: set = set()
    pending = list(JUDGEMENT_ENTRY_MODULES)
    while pending:
        module = pending.pop()
        if module in reached or module not in sources:
            continue
        reached.add(module)
        pending.extend(imports[module])
    return reached


def sweep(root: pathlib.Path):
    package_root = root / "src" / PACKAGE
    if not package_root.is_dir():
        raise SweepFailed(f"no package at {package_root}")
    sources = {}
    paths = {}
    for path in sorted(package_root.rglob("*.py")):
        module = _module_name(path, package_root)
        sources[module] = ast.parse(path.read_text(encoding="utf-8"))
        paths[module] = path
    subject = _closure(sources)
    sites = []
    for module in sorted(subject):
        visitor = _Sites(module)
        visitor.visit(sources[module])
        sites.extend(visitor.sites)
    outside = sorted(set(sources) - subject)
    # `sources` is returned as well since WO-2R3 increment 7: `CARRIER_ONLY` is an
    # ENUMERATION over the swept modules, so the contract check needs the same parse the
    # sweep used. Re-parsing would be a second reading of one input and they come apart.
    return sites, sorted(subject), outside, sources


# ------------------------------------------------------------------------------------- #
# the declared disposition register
# ------------------------------------------------------------------------------------- #

def _load_register():
    """Load the sibling register without requiring the repository on sys.path.

    A tool an auditor runs as `python3 -B tools/sweep/...` from a tree it extracted itself
    must not need a PYTHONPATH, an installed package or a wrapper (PBG-ASSURE-001).
    """
    here = pathlib.Path(__file__).resolve().parent / "declared_dispositions.py"
    namespace: dict = {"__file__": str(here), "__name__": "declared_dispositions"}
    exec(compile(here.read_text(encoding="utf-8"), str(here), "exec"), namespace)
    return namespace["DECLARED_ADMISSIONS"], namespace["DECLARED_MODULE_DISPOSITIONS"]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".")
    parser.add_argument("--list", action="store_true", help="print every site")
    parser.add_argument("--list-undeclared", action="store_true")
    arguments = parser.parse_args(argv)
    root = pathlib.Path(arguments.root).resolve()

    declared_admissions, declared_modules = _load_register()
    findings, findings_problems = _load_findings_register()
    sites, subject, outside, sources = sweep(root)

    admissions = {site for site in sites if site[2] in TIER_1_ADMISSION}
    deciding = [site for site in sites if site[2] not in TIER_1_ADMISSION]
    # **THE SITE REGISTER NOW COVERS BOTH TIERS.** A tier-1 admission must be declared or the
    # run fails; a tier-2 site MAY be declared, and declaring every one of a module's tier-2
    # sites is what DERIVES that module's answer (PO-DECISIONS-0014 ruling 1, as read in
    # `governance/engineering/CD-THE-FIFTEEN-AND-THE-REDRAFT.md` §1.3).
    tier_2_keys = set(deciding)
    all_site_keys = admissions | tier_2_keys

    undeclared = sorted(admissions - set(declared_admissions))
    # STALE is measured against ALL site keys, not only tier-1 ones — otherwise every tier-2
    # entry the derivation needs would be reported as a declaration for a site that does not
    # exist. Set equality still holds in both directions; the set it holds over got bigger.
    stale = sorted(set(declared_admissions) - all_site_keys)

    tier_2_keys_by_module: dict = collections.defaultdict(set)
    for site in tier_2_keys:
        tier_2_keys_by_module[site[0]].add(site)
    # **THE DERIVED MODULE ANSWER.** A module with a module-register entry keeps it. A module
    # WITHOUT one is DECLARED only if EVERY ONE of its distinct tier-2 site keys carries a
    # site entry. The non-empty guard is load-bearing: a module with no tier-2 sites at all
    # would otherwise be derived VACUOUSLY, and a derivation that is satisfied by an empty set
    # is a check that cannot fail. **REMOVE ONE TIER-2 ENTRY AND THE MODULE GOES UNDECLARED.**
    derived_modules = {
        module
        for module in subject
        if module not in declared_modules
        and tier_2_keys_by_module[module]
        and tier_2_keys_by_module[module] <= set(declared_admissions)
    }
    undeclared_modules = sorted(set(subject) - set(declared_modules) - derived_modules)
    stale_modules = sorted(set(declared_modules) - set(subject))

    by_category = collections.Counter(site[2] for site in sites)
    tier_1_dispositions = collections.Counter(
        declared_admissions[site][0] for site in admissions if site in declared_admissions
    )
    tier_2_dispositions = collections.Counter(
        declared_admissions[site][0] for site in tier_2_keys if site in declared_admissions
    )
    tier_2_by_module = collections.Counter(site[0] for site in deciding)

    print("CD-CLASS-2-DELEGATED-JUDGEMENT-SWEEP")
    print(
        f"    SUBJECT SET: the transitive intra-package import closure of "
        f"{len(JUDGEMENT_ENTRY_MODULES)} judgement entry modules = {len(subject)} modules"
    )
    for module in subject:
        if module in declared_modules:
            disposition = declared_modules[module][0]
        elif module in derived_modules:
            disposition = "DERIVED"
        else:
            disposition = "UNDECLARED"
        declared_here = len(tier_2_keys_by_module[module] & set(declared_admissions))
        print(f"        [{disposition:12s}] {module:44s} tier-2 sites: "
              f"{tier_2_by_module[module]:4d} occurrences, "
              f"{len(tier_2_keys_by_module[module]):4d} distinct keys, "
              f"{declared_here:4d} declared per site")
    print(f"    OUTSIDE THE CLOSURE, therefore NOT swept: {len(outside)} modules")
    for module in outside:
        print(f"        {module}")
    print(f"    THE DENOMINATOR: {len(sites)} sites")
    print(f"        TIER 1 — admission: {len(admissions)} distinct sites "
          f"({sum(by_category[c] for c in TIER_1_ADMISSION)} occurrences)")
    for category in TIER_1_ADMISSION:
        print(f"            {category:12s} {by_category[category]}")
    print(f"        TIER 2 — the deciding operation: {len(deciding)} occurrences")
    for category, count in sorted(by_category.items()):
        if category not in TIER_1_ADMISSION:
            print(f"            {category:12s} {count}")
    print("    DISPOSITIONS DECLARED PER SITE — tier 1 (mandatory) | tier 2 (derives the module):")
    for disposition in ALL_DISPOSITIONS:
        marker = "  (EXTENDED)" if disposition in EXTENDED_DISPOSITIONS else ""
        print(f"        {disposition:22s} {tier_1_dispositions[disposition]:4d} | "
              f"{tier_2_dispositions[disposition]:4d}{marker}")
    print(f"        {'MODULES DERIVED':22s} {len(derived_modules):4d}       "
          f"{sorted(derived_modules) if derived_modules else ''}")
    # **A WORD THE VOCABULARY DOES NOT KNOW USED TO VANISH HERE.** The loop printed the five
    # and a register entry carrying anything else was counted into nothing and never shown.
    # It is now a violation (UNKNOWN_DISPOSITION); this line is the visible half of that.
    unknown_words = sorted(
        {word for word, _ in tier_1_dispositions.items() if word not in ALL_DISPOSITIONS}
    )
    print(f"        words used that are NOT in the vocabulary: {len(unknown_words)} {unknown_words or ''}")
    by_status = collections.Counter(row["status"] for row in findings.values())
    print(
        f"    THE FINDINGS REGISTER ({FINDINGS_REGISTER_PATH.name}): {len(findings)} rows — "
        + ", ".join(f"{status} {by_status[status]}" for status in FINDING_STATUSES)
        + ". **AN INDEX, NOT A SYSTEM.** Every `finding` cited by a register entry resolves "
        "here as OPEN or the entry refuses."
    )

    if arguments.list or arguments.list_undeclared:
        rows = undeclared if arguments.list_undeclared else sorted(admissions)
        for site in rows:
            disposition, note = declared_admissions.get(site, ("UNDECLARED", ""))
            print(f"    [{disposition:12s}] {site[0]}::{site[1]} {site[2]}: {site[3]}")
            if note:
                print(f"                     {note}")

    # ------------------------------------------------------------------------------- #
    # THE DISPOSITION CONTRACT (WO-2R3 increment 7, PO-DECISIONS-0013 ruling 3).
    # **THE WORDS ARE A CONTRACT, NOT A LABEL SET**, and this is where that is true: an
    # unrecognised word, a malformed entry, or an extended word without its mandatory
    # evidence is a VIOLATION rather than a row nobody reads.
    # ------------------------------------------------------------------------------- #
    contract_failures = (
        findings_problems
        + _disposition_contract_violations(declared_admissions, declared_modules)
        + _carrier_only_violations(declared_admissions, sources, subject)
        + _upstream_of_the_path_violations(
            declared_admissions, declared_modules, all_site_keys
        )
        + _finding_resolution_violations(declared_admissions, declared_modules, findings)
    )

    violations = 0
    for rule, where, detail in contract_failures:
        violations += 1
        print(f"    {rule}: {where}\n        {detail}")
    for site in undeclared:
        violations += 1
        print(
            f"    UNDECLARED ADMISSION: {site[0]}::{site[1]} {site[2]}: {site[3]}\n"
            "        A tier-1 admission on a deciding path has no written disposition. "
            "Declare it in tools/sweep/declared_dispositions.py — including DELEGATED or "
            "OUT_OF_BOUND, which are legitimate answers when they are written down."
        )
    for site in stale:
        violations += 1
        print(
            f"    STALE DECLARATION: {site[0]}::{site[1]} {site[2]}: {site[3]}\n"
            "        A disposition is declared for a site that does not exist. The register "
            "is asserted by set equality in BOTH directions, because one that only noticed "
            "additions could be satisfied by deleting the entry that complains."
        )
    for module in undeclared_modules:
        violations += 1
        missing = sorted(tier_2_keys_by_module[module] - set(declared_admissions))
        print(
            f"    UNDECLARED MODULE: {module}\n"
            "        A module entered the judgement closure with no tier-2 disposition. "
            "Say how its deciding operands are established, or say they are not — EITHER by "
            "a DECLARED_MODULE_DISPOSITIONS entry in one of the five original words, OR by "
            "declaring EVERY ONE of its tier-2 sites per site, which DERIVES the module "
            "answer instead of asserting it.\n"
            f"        tier-2 site keys still undeclared: {len(missing)} of "
            f"{len(tier_2_keys_by_module[module])}"
        )
    for module in stale_modules:
        violations += 1
        print(
            f"    STALE MODULE DECLARATION: {module}\n"
            "        Declared, but no longer in the closure."
        )

    if violations:
        print(
            f"CD-CLASS-2-SWEEP: FAIL — {len(sites)} sites, {violations} violations"
        )
        return 1
    open_words = ("DELEGATED", "OUT_OF_BOUND", "DEFECT_OPEN")
    open_sites = sum(
        tier_1_dispositions[word] + tier_2_dispositions[word] for word in open_words
    )
    open_modules = sum(
        1
        for module in subject
        if declared_modules.get(module, ("DERIVED", ""))[0] in open_words
    )
    print(
        f"CD-CLASS-2-SWEEP: PASS — {len(sites)} sites enumerated over {len(subject)} "
        f"modules; every tier-1 admission and every subject module carries a written or "
        f"DERIVED disposition; {open_sites} sites and {open_modules} modules are declared "
        "OPEN, OUT OF BOUND or an OPEN DEFECT and are named in this increment's Build Log."
    )
    print(
        "    **READ THE LINE ABOVE AS WHAT IT IS.** A PASS here is a statement about the "
        "SURFACE and never about the class. It says every site the enumerator found carries "
        f"a written disposition — including {tier_1_dispositions['DEFECT_OPEN'] + tier_2_dispositions['DEFECT_OPEN']} "
        "sites DECLARED AS OPEN DEFECTS, which are open defects and not fixed ones. **A "
        "REGISTER FULL OF `DEFECT_OPEN` BUYS NOTHING** — not a pass of any gate, not an "
        "exemption, and it does not mean anything was repaired. A zero exit code here is "
        "ARITHMETIC over the declaration set, not evidence about the code."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
