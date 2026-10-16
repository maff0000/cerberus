"""Staleness as a TYPE — the one door a usable window comes through (CD-AC-005).

    StalenessWindow(seconds)                      a window that may lawfully be applied
    FreshnessEvidence(as_of_utc, observed_at_utc, window)
                                                  positive evidence that an observation
                                                  was CURRENT when it was read

===========================================================================================
WHY THIS MODULE EXISTS. CD-ASR-F06 (MEDIUM), CD-AC-005, escaped variant E07.
===========================================================================================
An independent auditor passed ``staleness_window_seconds=1e18`` to the serving resolver with
a panel row **ten years old** and marked ``AGREES``. It resolved to ``Agrees`` and rendered
``WITNESS AGREES``. With a window of ``60.0`` the same row correctly resolved to
``Unavailable``. **It needed no source edit at all — configuration alone.**

``_require_usable_window`` refused a non-finite or non-positive window and accepted **any**
finite positive number. The hazard was identified in writing by the previous seat — "no
window and a very large window both mean nothing is ever stale" — and then half-guarded:
infinity and zero were refused, ``1e18`` was not. A half-closed door.

Two separate defects hide inside that one sentence, and closing only the first would leave
the class open:

1. **THE WINDOW HAD NO CEILING.** Fixed below by :data:`STALENESS_WINDOW_CEILING_SECONDS`.
2. **AGREEMENT DID NOT REQUIRE FRESHNESS.** ``Agrees`` could be constructed by anyone, from
   anywhere, with no evidence that anything was current — so *any* route into the resolver
   that skipped the age comparison produced agreement, whatever the window said. That is
   the deeper half, and it is why :class:`FreshnessEvidence` exists.

===========================================================================================
THE CEILING IS **DERIVED** FROM RATIFIED PRODUCT INTENT AND WAS NOT CHOSEN (CD-RULE-003)
===========================================================================================
A number that carries product meaning is derived with its clause cited, or the seat fails
closed and escalates. It is never picked because it looks prudent. The precedent is written
at length in :mod:`crash_detector.dials.scores`, which REFUSES to impose a score range
because "a declared range is a declared scale, and the scale of a dial is what the dial
MEANS". This module takes the other branch of the same rule: here the clause exists.

**THE CLAUSE.** ``PID.md`` §5, the ratified property table, line 86, marked *RATIFIED
2026-08-18 — CD-D-003 resolved*:

    | **Assurance latency budget** | pipeline/publication failure independently detectable
    | ≤ **15 minutes**; a cadence breach alerts within **one publication cycle**; a candidate
    | defect is caught at the register gate before promotion |

**THE DERIVATION.** A staleness window is the interval during which a stored observation is
still treated as current. A window WIDER than the detectability budget means a dead witness
feed — or a dead collector — renders as *fresh* for longer than the product permits a
failure to go undetected. The budget therefore bounds the window **from above**, and does so
as a matter of the product's own ratified semantics rather than of anyone's judgement.
15 minutes = **900 seconds**.

**IT IS A CEILING AND NOT A SETTING, AND THE DIFFERENCE IS THE WHOLE POINT.** A window of
exactly 900 s consumes the ENTIRE detectability budget and leaves nothing for the detection
and the alerting themselves, so no sane deployment would run at the ceiling. What the
operating window should be is ``BLUEPRINT.md`` §7, CD-AC-009, scheduled for **WO-3**:

    **Regime-aware staleness** (CD-AC-009). The staleness window is a function, not a
    constant: ``window_for(regime) -> seconds``, tightening as observed volatility rises.

That function bounds the window further **from beneath** this ceiling, per regime. This
module does not implement it, does not anticipate it, and does not choose a default in its
place. **No tighter number is imposed here**, because a tighter number is not derivable from
any ratified clause, and choosing one that merely looks prudent is exactly the invention
CD-RULE-003 forbids (PBG-AUTH-005).

**THERE IS NO DEFAULT WINDOW ANYWHERE.** A caller that cannot state a window does not get a
lenient one and does not get a prudent one — it gets an error.

===========================================================================================
REFUSAL, NOT CLAMPING
===========================================================================================
A window above the ceiling is **refused**. It is not silently reduced to 900.

Clamping would produce a wrong window that looks like a right one: the caller believes it
configured 30 days, the system quietly applies 15 minutes, and the two disagree forever with
nothing in the record saying so. This is the identical argument
:class:`~crash_detector.dials.scores.ScoreOutOfRange` already makes about clamped scores,
and the identical argument :mod:`crash_detector.serving.witness_resolver` already makes
about coercing a measurement instead of rejecting it (Standards Baseline §4: reject, do not
coerce).

===========================================================================================
ONE DOOR, NOT TWO CHECKS. THIS MODULE IS SHARED WITH THE DIAL PATH ON PURPOSE.
===========================================================================================
There are TWO implementations of the same age comparison in this tree, and CD-ASR-F06 was
reported against only one of them. :mod:`crash_detector.engine.evaluate` takes its window
from the :class:`~crash_detector.engine.config.ConfigSnapshot` and performs its own
comparison, so a closure that bounded only the serving resolver would have left a decade-old
observation feeding a dial through configuration alone — the same class, one comparison site
across, which is closing the instance and calling it the class.

Both admit through :class:`StalenessWindow` and nothing else:
``ConfigSnapshot.window()`` is what the evaluation applies, and
``crash_detector.engine.evaluate._latest_usable_ok`` takes a ``StalenessWindow`` rather than
a float so a private helper cannot be called with an unadmitted quantity either. **Two
guarded comparison sites are an enumeration; one place a usable window can come into
existence is a closure.**

===========================================================================================
THE STRUCTURAL INVARIANT OF RECORD, NARROWED — CD-PL-F76, AT WO-2R2 INCREMENT 3.
===========================================================================================
The invariant that landed this closure (commit ``27e3794``, carried forward unchanged by
``2802924``, ``7edb84e`` and ``6641252``) opens: "No method defined by a caller-supplied
class executes during the computation of an age...". THAT SENTENCE IS WIDER THAN THE CLOSURE
IT DESCRIBES, and the counterexample is this closure's OWN declared boundary 5 below. It is
narrowed HERE and FORWARD. Commit ``27e3794`` is NOT rewritten and its message stands as
written (PBG-CONT-003, non-waivable); this text SUPERSEDES, it does not edit.

WHAT THE CLOSURE ACTUALLY HOLDS: **no method of** ``type(value)`` executes during the
computation of an age, the comparison of an age against a window, the selection of a panel
constructor from a stored state, or the admission of a divergence measurement — because every
one of those operates on a value of exact base type that ``crash_detector.own_terms``
constructed from primitives it read out of the supplied object through the base type's own
descriptors.

WHAT STILL EXECUTES, AND IT IS EXACTLY ONE THING: ``tzinfo.utcoffset``. It is a method of a
supplied OBJECT — the ``tzinfo`` instance reached through ``value.tzinfo`` — and NOT a method
of ``type(value)``; and it DETERMINES the age. A row whose stated wall clock is 22 HOURS OLD
resolves to ``Agrees`` and renders ``WITNESS AGREES`` against a 600-second window when its
``tzinfo`` reports a compensating offset. MEASURED — boundary 5 below, variant
``CD-ENG-WO2R2-V10``, identical at ``50fc231`` and at the closure. THE CPYTHON INTERPRETER
BOUNDS IT to strictly under 24 hours, MEASURED. BEYOND THAT BOUND, NOT PROVED TO BE CARRIED
ANYWHERE.

WHY IT IS NOT CLOSED HERE: a ``tzinfo`` cannot be refused without refusing ``zoneinfo``,
``pytz`` and ``pandas``, which all supply their own — that trades a defect for a defect.
Closing it needs a clock-trust instrument, and CD-RULE-003 forbids a seat inventing a skew
tolerance, or the CD-D-005 ingredient register. Both are Product Authority territory. It is
REPORTED upward under CD-D-081 as a pre-existing, bounded, declared residue, and NOT guarded.
NO CODE CHANGED FOR THIS NARROWING: the code is right; the sentence was too wide.

===========================================================================================
DECLARED LIMIT (CD-RULE-004). Stated identically here, in ``required-tests.yaml`` and in
``contracts/execution/CD-RT-005-PANEL-UNAVAILABLE-NEVER-AGREES.md``. Each hand-off names a
layer that was MEASURED or says NOT PROVED TO BE CARRIED ANYWHERE (CD-RULE-006).
===========================================================================================
 1  THE CEILING BOUNDS THE WINDOW; IT DOES NOT ESTABLISH WHAT THE WINDOW SHOULD BE. Any
    window from ``0.001`` to ``900.0`` seconds is admissible, and a deployment configuring
    ``899.0`` has a window this module does not question. The operating window is
    BLUEPRINT §7's ``window_for(regime)``, OWED AT WO-3 (CD-AC-009).
    NOT PROVED TO BE CARRIED ANYWHERE — and deliberately so. Deciding the operating window
    here would be inventing a product quantity (CD-RULE-003, PBG-AUTH-005); the honest state
    is a derived ceiling plus an explicitly owed function beneath it.

 2  CLOCK TRUST IS NOT ESTABLISHED, AND IS NOT CLAIMED. :class:`FreshnessEvidence` judges an
    age against the ``observed_at_utc`` it is handed. ``now_utc`` is an argument everywhere
    on the freshness path by design, so a historical evaluation replays exactly
    (BLUEPRINT §7), and a caller that passes a false instant gets evidence about the world
    it described.
    MEASURED: ``resolve_panel(row_dated_2016, now_utc=2016-08-21T12:00:10Z,
    staleness_window_seconds=600.0)`` returns ``Agrees`` and renders ``WITNESS AGREES``.
    NOT PROVED TO BE CARRIED ANYWHERE. It is pre-existing and project-wide rather than
    introduced by this closure, and closing it means trusting a clock, which is a different
    problem with a different instrument.

 3  ``object.__setattr__`` WALKS PAST FROZEN, here as on every frozen value in Python and in
    this repository.

    AMENDED AT INCREMENT 6, CD-PL-F65 / CD-D-058, AND THE PREVIOUS TEXT IS WHY. This
    boundary used to read "Both values use ``__slots__``, so an UNDECLARED attribute cannot
    be injected". That sentence is TRUE of the two values it was written about and it was
    REASSURING ABOUT A THIRD VALUE IT NEVER NAMED. It was INCOMPLETE, not false — the
    CD-PL-F62 shape, with no carrier claimed that does not exist — and the correction is
    carried here rather than made silently (PBG-CONT-003).

    THE TWO SLOTTED VALUES. :class:`StalenessWindow` and :class:`FreshnessEvidence` are both
    declared ``@dataclass(frozen=True, slots=True)``, so an UNDECLARED attribute cannot be
    injected — MEASURED: ``object.__setattr__(window, "ceiling", 1e18)`` raises
    ``AttributeError: 'StalenessWindow' object has no attribute 'ceiling'``, and so does
    ``"smuggled"``. Overwriting a DECLARED slot on an already-constructed value is NOT
    preventable at the Python level — MEASURED: ``object.__setattr__(window, "seconds",
    1e18)`` sticks and ``window.seconds`` then reads ``1e+18``, and
    ``object.__setattr__(evidence, "as_of_utc", <2016-08-21>)`` makes its derived
    ``age_seconds`` read ``315360000.0``.

    ``Agrees`` IS NOT ONE OF THEM, AND THE ``__slots__`` HALF DOES NOT HOLD THERE.
    :class:`~crash_detector.witness.panel.Agrees` is declared ``@dataclass(frozen=True)``
    with NO ``slots=True``. It carries a ``__dict__``, so on ``Agrees`` even the
    UNDECLARED-attribute protection is ABSENT — MEASURED:
    ``object.__setattr__(agrees, "smuggled", 1e18)`` STICKS and ``agrees.smuggled`` reads
    ``1e+18``, where the identical write on :class:`StalenessWindow` raises. An auditor
    reading the old sentence would have carried the slotted guarantee across to the value
    that actually renders the panel, and it is not there.

    AND THE ROUTE REACHES THE PRODUCT OWNER'S OWN FORBIDDEN SENTENCE. State it plainly
    rather than leave it to be inferred from "not preventable at the Python level" —
    MEASURED (PL-W5), on a LAWFULLY constructed fresh ``Agrees`` followed by ONE
    post-construction write::

        row = PanelRow(state="AGREES", as_of_utc=NOW, published_utc=NOW,
                       measures={"divergence_measure": 0.01})
        a = resolve_panel(row, now_utc=NOW, staleness_window_seconds=600.0)
        object.__setattr__(a, "as_of_utc", datetime(2016, 8, 21, 12, 0, tzinfo=utc))
        render_panel(a)          # -> 'WITNESS AGREES'

    That is ``WITNESS AGREES`` on a DECADE-OLD TIMESTAMP. ``render_panel`` dispatches on
    TYPE and re-validates nothing, so once a value of type ``Agrees`` exists no later layer
    looks at it again. Carrying the forgery down into the evidence makes it internally
    consistent as well — MEASURED, adding ``object.__setattr__(a.freshness, "as_of_utc",
    <2016-08-21>)`` and ``object.__setattr__(a.freshness.window, "seconds", 1e18)`` gives
    ``a.freshness.age_seconds == 315360000.0`` (3650 days),
    ``a.freshness.window.covers(315360000.0) is True``, and ``render_panel(a)`` still
    ``'WITNESS AGREES'``.

    NOT PROVED TO BE CARRIED ANYWHERE. No layer was measured refusing a forged ``Agrees``.

    THE THREE ROUTES THAT ARE REFUSED, WHICH STAND UNCHANGED: the decade-old row itself
    resolves to ``Unavailable`` and renders ``WITNESS UNAVAILABLE``;
    ``StalenessWindow(seconds=1e18)`` raises :class:`StalenessWindowOutOfRange`; and
    ``Agrees(...)`` built with evidence for a different instant raises
    :class:`~crash_detector.witness.panel.AgreementWithoutFreshnessEvidence`. The
    ``object.__setattr__`` residue is available only to code that has already chosen to
    write past the language's own frozen guarantee. It is the same residue declared as
    boundary B of :mod:`crash_detector.dials.magnitude` and measured there against a forged
    magnitude; it is a property of the language, not of this design.

    WHAT THIS BOUNDARY IS NOT — **CORRECTED AT WO-2R2 INCREMENT 2, AND THE PREVIOUS TEXT
    IS WHY.** It read, of the routes from ordinary input:

        "it is not a route from ordinary input, and every route measured that goes through
         a CONSTRUCTOR is refused. THREE MEASURED, and three is the denominator, not a
         proof that a fourth does not exist"

    **THE FOURTH EXISTED.** CD-ASR-WO2-02 found it and it is variant ASR2-005-A: a
    ``datetime`` subclass overriding ``__rsub__`` and ``astimezone``, which goes through
    ``PanelRow.__post_init__``, ``resolve_panel``, ``StalenessWindow.__post_init__`` and
    ``FreshnessEvidence.__post_init__`` — EVERY constructor on the path — and reaches
    ``Agrees``. A row dated 2016-08-21 read at 2026-08-19 with a 600 s window rendered
    ``WITNESS AGREES`` while ``CD-RT-005`` exited 0 with 152 passed and the whole suite
    passed. The hedge was honest and it did its job; what it could not do was say what the
    denominator WAS. That is what this correction supplies (PBG-CONT-003 — corrections
    supersede, never edit; the old sentence is quoted above rather than removed).

    **THE DENOMINATOR IS NOW STATED, AND SO IS THE METHOD BY WHICH IT WAS TAKEN.**
    The class was re-stated at the altitude the Product Owner set — ANY JUDGEMENT THIS
    SYSTEM MAKES THAT DELEGATES ITS DECIDING OPERATION TO AN OBJECT THE SYSTEM DID NOT
    CONSTRUCT — and swept, not by reading the modules that looked relevant, but
    mechanically:

      METHOD. Parse every module of ``src/crash_detector``. Compute the transitive
      intra-package IMPORT CLOSURE of the six modules that host a judgement about
      staleness, agreement or reading-ness (``serving.witness_resolver``, ``witness.panel``,
      this module, ``engine.evaluate``, ``dials.reading``, ``serving.dial_presentation``).
      Enumerate every AST node in that closure at which an operation could be executed by an
      object the module did not construct, in two tiers — admission (``isinstance``,
      ``issubclass``, ``hasattr``, ``getattr``) and the deciding operation itself
      (comparison, membership, arithmetic, ordering calls, coercion calls, set operations,
      truthiness, identity). The closure is taken over MODULES, not functions, so it is
      OVER-inclusive by construction.

      DENOMINATOR. **16 subject modules, 402 sites.** Tier 1: 30 distinct sites, 33
      occurrences (ISINSTANCE 24, ISSUBCLASS 0, DUCK 9). Tier 2: 369 occurrences
      (TRUTHINESS 103, COERCION 101, IDENTITY 47, COMPARE 36, ORDERING 30, MEMBERSHIP 26,
      ARITH 18, SETOP 8). Every tier-1 site carries a WRITTEN DISPOSITION and every subject
      module carries one for tier 2, asserted BY SET EQUALITY IN BOTH DIRECTIONS.

    **EXECUTABLE EXAMPLE.** Both halves of it, from the root of an extracted tree::

        python3 -B tools/sweep/delegated_judgement_sweep.py --root . --list
            -> exit 0, "402 sites enumerated over 16 modules"
        # and the route the old sentence could not count, on its own extraction:
        cp <ASR2-005-A> src/crash_detector/serving/panel_feed.py && python3 -B <its driver>
            -> Unavailable(reason='PANEL_ROW_STALE') -> 'WITNESS UNAVAILABLE'
            -> and the plain-datetime CONTROL arm renders the SAME string

    **CARRIER MEASURED (CD-RULE-006).** The carrier is
    :mod:`crash_detector.own_terms`, and it was measured refusing the variant on pristine
    extractions rather than reasoned about: at the audited base 50fc231 ASR2-005-A renders
    ``WITNESS AGREES`` while the control renders ``WITNESS UNAVAILABLE``; at the closure both
    arms render ``WITNESS UNAVAILABLE``. The auditor's finding WAS that divergence. A
    counterfactual extraction with one line changed — the descriptor read replaced by
    ``getattr`` — renders ``WITNESS AGREES`` again, so the line that carries it is identified
    and not merely nominated.

    **WHAT REMAINS OUTSIDE THE DENOMINATOR, AND IT IS NOT NOTHING:**

    * **19 names of the package are outside the import closure** and were not swept. Every
      run prints them. None of them decides staleness, agreement or reading-ness AT THIS SHA,
      which is a claim made by reading them and is the claim to attack.
    * **THE SWEEP DID NOT SEE THE AUDITOR'S OWN VARIANT FILE.** With ASR2-005-A present as
      ``src/crash_detector/serving/panel_feed.py`` the sweep still reports 402 sites, because
      that module imports none of the six entry modules. Disclosed here rather than left to
      be discovered: the sweep COUNTS and does not GUARD, and what refuses that variant is
      the re-construction at the door, which needs no module to be in any set.
    * **THE SWEEP'S OWN FOUR BOUNDARIES**, in its header: static and intra-procedural, so
      every ESTABLISHED disposition is a CLAIM BY THAT SEAT and not something the tool
      verified; it sees only operators written literally, so ``operator.__lt__`` produces no
      site; its subject set is an import closure; and a disposition keyed by expression text
      does not survive a rename. **For a MIS-DECLARED disposition: NOT PROVED TO BE CARRIED
      ANYWHERE** — it is invisible to the tool by construction.
    * **FOUR PLACES ARE DECLARED OPEN OR OUT OF BOUND RATHER THAN CLOSED**, named in
      ``tools/sweep/declared_dispositions.py``: the injected ``ContributionModel``
      (``crash_detector.engine.model`` — ruled closed by CONSTRUCTION at Blueprint §7 in WO-3
      by PO-DECISIONS-0003, and NOT to be closed by a guard here), ``SourceRecord``'s
      ``cadence_seconds`` int subclass, and ``FetchFailed.http_status`` and
      ``Malformed.instance_path``. Each says why, and each is **NOT PROVED TO BE CARRIED
      ANYWHERE**.
    * **AND BOUNDARY 5 BELOW**, which is a route to ``WITNESS AGREES`` on a stale row that
      this closure does NOT close.

    ``Agrees`` IS DELIBERATELY NOT SLOTTED BY THIS AMENDMENT, AND THAT IS AN INSTRUCTION
    OBEYED RATHER THAN AN OVERSIGHT (CD-D-058). Slotting it would close the
    UNDECLARED-attribute half — the ``"smuggled"`` write above — and leave the DECLARED-slot
    half wide open, and the DECLARED-slot half is the whole of PL-W5: the write that reaches
    ``WITNESS AGREES`` overwrites the declared field ``as_of_utc``. A change that closes the
    measured-harmless half and reads like a closure of the other is the CD-PL-F54 shape,
    which has already sent one increment back. Increment 6 writes no logic; if slotting is
    judged worth doing it belongs in a dispatch that can prove what it closes.

 4  THE PUBLISHED ENVELOPE'S ``staleness_window_seconds`` FIELD IS NOT ADMITTED THROUGH THIS
    DOOR. The envelope carries the window that WAS applied as a plain number validated by
    the JSON Schema, so a hand-built envelope declaring an inadmissible window is a
    publication-provenance question rather than a staleness one.
    NOT PROVED TO BE CARRIED ANYWHERE.

 5  A ``tzinfo`` IS A SUPPLIED OBJECT, AND IT IS THE LAST PLACE A SUPPLIED OBJECT'S METHOD
    STILL RUNS INSIDE A FRESHNESS COMPUTATION. **ADDED AT WO-2R2 INCREMENT 2. MEASURED
    OPEN.** Since that increment every timestamp is REBUILT by
    :func:`crash_detector.own_terms.own_instant` from the supplied object's own primitive
    fields, so no method of ``type(value)`` runs — but the UTC OFFSET is obtained by
    ``datetime.utcoffset(value)``, whose base implementation asks ``value.tzinfo``. A
    ``tzinfo`` cannot be refused without refusing ``zoneinfo``, ``pytz`` and ``pandas``, all
    of which supply their own, so it is not refused.

    MEASURED (variant CD-ENG-WO2R2-V10, on pristine extractions of BOTH 50fc231 and the
    closure, with identical results)::

        row = PanelRow(state="AGREES",
                       as_of_utc=datetime(2026, 8, 18, 14, tzinfo=SkewedZone(-22)),
                       published_utc=..., measures={"divergence_measure": 0.01})
        resolve_panel(row, now_utc=2026-08-19T12:00Z, staleness_window_seconds=600.0)
        # -> Agrees -> 'WITNESS AGREES', on a row whose stated wall clock is 22 HOURS OLD

    THE BOUND IS CARRIED BY THE CPYTHON INTERPRETER AND WAS MEASURED, not assumed:
    ``call_utcoffset`` refuses any return that is not a ``timedelta`` and any magnitude of
    one day or more — an offset of ``timedelta(days=1)`` raises ``ValueError: offset must be
    a timedelta strictly between -timedelta(hours=24) and timedelta(hours=24)``. So the
    worst this route can achieve is to move an instant by up to 24 hours, which is **96x the
    900-second ceiling** this module derives from PID §5.

    BEYOND THAT BOUND, NOT PROVED TO BE CARRIED ANYWHERE. It is the same fact as boundary 2
    — clock trust is not established and is not claimed — reached through the offset rather
    than through ``now_utc``, and it is a statement about the DATA a caller supplied rather
    than about code a caller supplied. It is NOT introduced by the WO-2R2 closure: it is
    measured identically at the audited base. It is stated here because the closure made it
    the LAST such route, and a residue that is now the only one of its kind should be
    findable without re-deriving it.

Do not read a clean run of ``CD-RT-005-PANEL-UNAVAILABLE-NEVER-AGREES`` as proof that every
freshness decision in a deployment is sound. Read it as proof of exactly three things: that
no window wider than the ratified detectability budget can be applied; that agreement cannot
exist without the comparison that justifies it; and — since WO-2R2 increment 2 — that the
values that comparison is made of are objects this system constructed, so the answer is not
the supplied timestamp's to give. It is not proof about boundary 5, which is open and
measured open, and it is not proof about the routes listed as outside the denominator in
boundary 3.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

from crash_detector.time_utc import age_seconds, ensure_utc
from crash_detector.establishment import establishes

__all__ = [
    "STALENESS_WINDOW_CEILING_SECONDS",
    "STALENESS_WINDOW_CEILING_SOURCE",
    "StalenessWindowOutOfRange",
    "FreshnessNotEstablished",
    "StalenessWindow",
    "RELEVANCE_WINDOW_CEILING_SECONDS",
    "RELEVANCE_WINDOW_CEILING_SOURCE",
    "RelevanceWindow",
    "FreshnessEvidence",
]

#: The HARD UPPER BOUND on any staleness window, in seconds. DERIVED — see the module
#: docstring — from PID.md §5's ratified assurance latency budget of 15 minutes. It is a
#: ceiling, NOT an operating window and NOT a default: the operating window is
#: BLUEPRINT §7's ``window_for(regime)``, owed at WO-3 (CD-AC-009).
STALENESS_WINDOW_CEILING_SECONDS: float = 900.0

#: The clause the ceiling derives from, carried as DATA so a reader of a refusal message is
#: told where the number comes from rather than having to trust it.
STALENESS_WINDOW_CEILING_SOURCE = (
    "PID.md §5, assurance latency budget, RATIFIED 2026-08-18 (CD-D-003 resolved): "
    "pipeline/publication failure independently detectable <= 15 minutes. A staleness "
    "window wider than the detectability budget renders a dead feed as fresh for longer "
    "than the product permits failure to go undetected. The OPERATING window is "
    "BLUEPRINT.md §7 CD-AC-009 `window_for(regime)`, owed at WO-3; this is only the "
    "ceiling above which no window may be applied at all."
)


class StalenessWindowOutOfRange(ValueError):
    """A staleness window was outside the range in which it can mean anything.

    A ``ValueError`` so that the pre-existing refusals of ``inf``, ``nan``, ``0`` and
    negatives keep the exception type they already had, and callers that were written
    against it do not have to change to stay correct.
    """


class FreshnessNotEstablished(ValueError):
    """Freshness could not be evidenced: the observation is stale, or future-dated.

    Raised by :class:`FreshnessEvidence`, which is the only thing that can make the
    evidence :class:`~crash_detector.witness.panel.Agrees` requires. A caller that reaches
    for agreement without a current observation gets this, from inside the constructor,
    whatever code path it took to get there.
    """


@establishes(
    seconds=float,
)
@dataclass(frozen=True)
class StalenessWindow:
    """A window that may lawfully be applied, in seconds.

    Constructing one IS the admission decision, and it is the ONLY admission decision:
    there is no other way to obtain a value of this type, so there is no second site to
    keep in step. Two guarded comparison sites are an enumeration; one place a usable
    window can come into existence is a closure.

    Refused: anything that is not a real number, ``bool`` (``isinstance(True, int)`` is
    true in Python and a boolean window is a type error wearing a value), ``nan``, ``inf``,
    zero, negatives, and **anything above** :data:`STALENESS_WINDOW_CEILING_SECONDS`.

    **SUBCLASSES OF ``float`` ARE REFUSED, AND SO ARE SUBCLASSES OF THIS TYPE.** Both are
    routes this seat found against its own first cut and closed rather than declared:

    * ``class W(float): __lt__ = lambda self, other: False`` passes an ``isinstance``
      check and then makes ``age > window`` answer ``False`` for every age, because Python
      tries the reflected operation first for a subclass on the right. A type that has
      redefined what comparison MEANS is not the number it claims to be, so the check is
      on the exact type and the stored value is a plain ``float`` computed from it.
    * ``class W(StalenessWindow): __post_init__ = lambda self: None`` would pass every
      ``isinstance`` check downstream while carrying any width at all — the same argument
      :class:`~crash_detector.dials.reading.SealedReadingType` already makes about the
      Reading sum type, and closed the same way: refused, not policed.
    """

    #: SEALED (PO-DECISIONS-0016 ruling 2). Without __slots__ an instance carries a
    #: __dict__, and `StalenessWindow.__new__(StalenessWindow)` followed by `__dict__.update(...)`
    #: yields an object of exactly this type carrying forged field values, having
    #: executed NO package code: the establishment boundary is not consulted, it is
    #: walked around. Declared here rather than via @dataclass(slots=True), which also
    #: installs a stdlib __setstate__ that re-opens the same route by its sibling.
    __slots__ = ("seconds",)

    seconds: float

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            f"{cls.__name__} may not subclass StalenessWindow: a subclass could redefine "
            "the admission that gives a window its meaning while remaining acceptable to "
            "every isinstance check downstream. The window is CLOSED; a different rule "
            "for windows is a change to this type, reviewed as one."
        )

    def __post_init__(self) -> None:
        declared = self.seconds
        # EXACT type, not isinstance. See the class docstring: a float subclass can
        # redefine comparison and a window that decides its own comparisons decides
        # its own answer.
        if type(declared) is not float and type(declared) is not int:
            raise TypeError(
                "staleness window must be a plain int or float number of seconds, got "
                f"{type(declared).__name__}. A subclass of a number is not a number: it "
                "may redefine what comparison means, and a window whose comparisons it "
                "controls is not a window at all."
            )
        window = float(declared)
        if not math.isfinite(window):
            raise StalenessWindowOutOfRange(
                f"staleness window must be finite, got {window!r}. An unbounded staleness "
                "window is no staleness window: it does not make the system lenient, it "
                "abolishes staleness."
            )
        if window <= 0.0:
            raise StalenessWindowOutOfRange(
                f"staleness window must be positive, got {window!r} seconds."
            )
        if window > STALENESS_WINDOW_CEILING_SECONDS:
            raise StalenessWindowOutOfRange(
                f"staleness window {window!r} seconds exceeds the ceiling of "
                f"{STALENESS_WINDOW_CEILING_SECONDS} seconds and is REFUSED, not clamped. "
                "A clamped window is a wrong window that looks like a right one: the "
                "caller would believe it configured one interval while the system applied "
                "another, with nothing in the record saying so. "
                f"The ceiling is DERIVED, not chosen: {STALENESS_WINDOW_CEILING_SOURCE}"
            )
        object.__setattr__(self, "seconds", window)

    def covers(self, age: float) -> bool:
        """Is an observation of this ``age`` in seconds still inside this window?

        A negative age is NOT covered. An observation claiming to be from the future would
        otherwise never age out of any window — one bad clock upstream and the reading is
        permanently current, most confidently exactly when the upstream is broken.
        """
        if type(age) is not float and type(age) is not int:
            raise TypeError(
                f"age must be a plain int or float number of seconds, got "
                f"{type(age).__name__}. A subclass of a number may redefine comparison, "
                "and the comparison is the whole of this answer."
            )
        value = float(age)
        if not math.isfinite(value):
            return False
        return 0.0 <= value <= self.seconds


#: The HARD UPPER BOUND on a per-indicator RELEVANCE window, in seconds: how old an
#: observation of a slow series may be and still be that series' CURRENT observation.
#: DERIVED from the Owner-ratified indicator mapping (``governance/mapping/indicator_mapping.yaml``):
#: the widest window that mapping declares, whatever that happens to be. It is therefore NOT a
#: constant of this module's choosing, and it MOVES WHEN THE RATIFIED MAPPING MOVES.
#:
#: WO-1.19 (2026-10-16) RAISED IT, from 10_368_000 s (120 days) to 18_144_000 s (210 days).
#: It was 120 days because that was the widest the mapping declared as ratified on 2026-08-24
#: (private_credit_stress and sloos_bank_lending, both quarterly). It is now 210 days because
#: that is ``buffett_indicator``'s window, newly ratified and now the widest the mapping
#: declares. THE REASON IS MEASURED, NOT ARGUED: ``evidence/wo119_release_lag_probe.json``
#: probed real ALFRED vintages for both of that row's wired legs over 14 real quarters and found
#: the slower one (the Z.1 series NCBEILQ027S) lagging the quarter end by up to 101 days, which
#: puts the real PEAK AGE of a healthy reading - one quarter cycle plus that lag - at up to ~192
#: days. A flat 120-day window could not avoid reading a LIVE feed STALE between releases, for
#: that row or for sloos_bank_lending (~133-day measured peak, now ratified at 150 days).
#:
#: THIS IS AN OWNER RATIFICATION, NOT A CODE-SIDE WORKAROUND: Matt confirmed the new windows on
#: those measured numbers on 2026-10-16, so the ratified mapping was edited and this derived
#: ceiling followed it. Widening a ceiling to fit the data was the move the previous seat
#: declined, and it remains declined - what changed is the ratified declaration this ceiling
#: reads FROM, not this module's willingness to exceed it.
#:
#: A ceiling and not a setting, for the same reason :data:`STALENESS_WINDOW_CEILING_SECONDS` is:
#: a relevance window that can be 1e18 abolishes staleness. Its enforcement is UNCHANGED by
#: WO-1.19 - still REFUSED, never clamped (see :meth:`RelevanceWindow.__post_init__`).
RELEVANCE_WINDOW_CEILING_SECONDS: float = 18_144_000.0

RELEVANCE_WINDOW_CEILING_SOURCE = (
    "the widest per-indicator window in the Owner-ratified indicator mapping "
    "(18,144,000 s = 210 days: buffett_indicator, whose wired legs are quarterly). WO-1.19 "
    "(2026-10-16) raised this from 10,368,000 s (120 days: private_credit_stress and "
    "sloos_bank_lending), because the Owner RATIFIED wider windows for buffett_indicator (210 "
    "days) and sloos_bank_lending (150 days) on REAL MEASURED release lag - ALFRED vintages over "
    "14-15 real quarters per leg, recorded in evidence/wo119_release_lag_probe.json - which "
    "showed a flat 120-day window reading a LIVE feed STALE between releases on both rows "
    "(measured peak ages ~192 and ~133 days). The ceiling is still DERIVED from the mapping and "
    "not chosen here: it moved because the ratified declaration moved. WO-1.3 (2026-10-11): the "
    "Owner directed that real data be wired into the engine, which resolves the collision "
    "admit_staleness_window recorded between FEED LIVENESS (the 900 s ceiling above, unchanged) "
    "and DATA CADENCE (this)."
)


@establishes(
    seconds=float,
)
@dataclass(frozen=True)
class RelevanceWindow:
    """How old an observation of ONE indicator may be and still be its current observation.

    **A DIFFERENT QUANTITY FROM** :class:`StalenessWindow`, **NOT A WIDER INSTANCE OF IT.**
    ``StalenessWindow`` is bounded by the 15-minute detectability budget (PID §5) and
    answers *"is the feed alive?"*. A three-month-old SLOOS print is not a dead feed; it is
    the current observation of a quarterly series. ``RelevanceWindow`` answers that second
    question, per indicator (PO-PRODUCT-0001 R2), and is bounded by the widest cadence the
    ratified mapping declares. The two types are separate so that neither can be passed
    where the other is meant: widening the liveness ceiling to fit the data was the move the
    previous seat declined, and this is the alternative it pointed at.

    Every hardening :class:`StalenessWindow` carries is carried here: exact numeric type,
    finite, positive, ceilinged-and-refused-not-clamped, closed against subclassing, and a
    negative (future-dated) age is never covered. Absence past the window is ABSENCE: the
    engine treats the observation as not there, never as a value with a caveat.
    """

    __slots__ = ("seconds",)

    seconds: float

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            f"{cls.__name__} may not subclass RelevanceWindow: a subclass could redefine "
            "the admission that gives a window its meaning while remaining acceptable to "
            "every isinstance check downstream."
        )

    def __post_init__(self) -> None:
        declared = self.seconds
        if type(declared) is not float and type(declared) is not int:
            raise TypeError(
                "relevance window must be a plain int or float number of seconds, got "
                f"{type(declared).__name__}. A subclass of a number may redefine "
                "comparison, and the comparison is the whole of this answer."
            )
        window = float(declared)
        if not math.isfinite(window):
            raise StalenessWindowOutOfRange(
                f"relevance window must be finite, got {window!r}. An unbounded window is "
                "no window: it abolishes staleness."
            )
        if window <= 0.0:
            raise StalenessWindowOutOfRange(
                f"relevance window must be positive, got {window!r} seconds."
            )
        if window > RELEVANCE_WINDOW_CEILING_SECONDS:
            raise StalenessWindowOutOfRange(
                f"relevance window {window!r} seconds exceeds the ceiling of "
                f"{RELEVANCE_WINDOW_CEILING_SECONDS} seconds and is REFUSED, not clamped. "
                f"The ceiling is DERIVED, not chosen: {RELEVANCE_WINDOW_CEILING_SOURCE}"
            )
        object.__setattr__(self, "seconds", window)

    def covers(self, age: float) -> bool:
        """Is an observation of this ``age`` in seconds still its indicator's current one?"""
        if type(age) is not float and type(age) is not int:
            raise TypeError(
                f"age must be a plain int or float number of seconds, got "
                f"{type(age).__name__}."
            )
        value = float(age)
        if not math.isfinite(value):
            return False
        return 0.0 <= value <= self.seconds


@establishes(
    as_of_utc=datetime,
    observed_at_utc=datetime,
    window=StalenessWindow,
)
@dataclass(frozen=True)
class FreshnessEvidence:
    """POSITIVE EVIDENCE that an observation was current when it was read.

    This is the invariant CD-ASR-F06 is really about, and it is worth more than the
    ceiling on its own.

    **Agreement requires evidence, and the evidence is not something a caller may assert.**
    The age is not a field: it is COMPUTED here from ``as_of_utc`` and ``observed_at_utc``,
    and if it falls outside ``window`` this constructor raises. So constructing the
    evidence **is** performing the age comparison. There is no route into
    :class:`~crash_detector.witness.panel.Agrees` that skips the comparison, because there
    is no ``Agrees`` without a :class:`FreshnessEvidence` and no ``FreshnessEvidence``
    without the comparison — including from an exception handler, a fallback branch, a
    default argument, or any code path that did not intend to check anything at all.

    **What this does NOT establish, stated so it is not over-read.** It evidences that a
    timestamp is inside a window, judged against the ``observed_at_utc`` it was handed.
    A caller that passes a false ``observed_at_utc`` — a clock ten years slow, or a
    deliberately fabricated instant — gets evidence about the world it described. That is
    the same property the whole product already has by design: ``now_utc`` is an argument
    everywhere on the freshness path, precisely so a historical evaluation can be replayed
    exactly (BLUEPRINT §7). Clock trust is not established here and is not claimed here.
    """

    #: SEALED (PO-DECISIONS-0016 ruling 2). Without __slots__ an instance carries a
    #: __dict__, and `FreshnessEvidence.__new__(FreshnessEvidence)` followed by `__dict__.update(...)`
    #: yields an object of exactly this type carrying forged field values, having
    #: executed NO package code: the establishment boundary is not consulted, it is
    #: walked around. Declared here rather than via @dataclass(slots=True), which also
    #: installs a stdlib __setstate__ that re-opens the same route by its sibling.
    __slots__ = ("as_of_utc", "observed_at_utc", "window")

    as_of_utc: datetime
    observed_at_utc: datetime
    window: StalenessWindow

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            f"{cls.__name__} may not subclass FreshnessEvidence: a subclass could skip "
            "the age comparison in its own __post_init__ and still satisfy every "
            "isinstance check that agreement depends on. Evidence is CLOSED."
        )

    def __post_init__(self) -> None:
        # EXACT type. Subclassing is already refused above; this makes the guarantee
        # independent of that, because a subclass that somehow existed would be accepted
        # by isinstance while carrying any window width at all.
        if type(self.window) is not StalenessWindow:
            raise TypeError(
                "freshness must be evidenced against a StalenessWindow, got "
                f"{type(self.window).__name__}. A bare number is not a window: it has not "
                "passed the admission that gives a window its meaning, and neither is a "
                "subclass that may have redefined that admission."
            )
        object.__setattr__(self, "as_of_utc", ensure_utc(self.as_of_utc))
        object.__setattr__(self, "observed_at_utc", ensure_utc(self.observed_at_utc))
        age = age_seconds(as_of_utc=self.as_of_utc, now_utc=self.observed_at_utc)
        if age < 0.0:
            raise FreshnessNotEstablished(
                f"the observation is dated {-age} seconds in the FUTURE, so no statement "
                "about its freshness can be made. A future-dated observation never ages "
                "out of any window."
            )
        if not self.window.covers(age):
            raise FreshnessNotEstablished(
                f"the observation is {age} seconds old and the applied staleness window is "
                f"{self.window.seconds} seconds, so it is STALE. Freshness cannot be "
                "evidenced for it, and therefore agreement cannot be constructed from it "
                "by any route."
            )

    @property
    def age_seconds(self) -> float:
        """How old the observation was when it was read. Derived, never stored."""
        return age_seconds(as_of_utc=self.as_of_utc, now_utc=self.observed_at_utc)
