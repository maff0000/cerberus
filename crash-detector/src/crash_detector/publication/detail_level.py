"""Drill-down proportional to risk — **in exactly ONE place** (PID §4, BLUEPRINT §8).

    level   = detail_level_for(reading, dial_slot="equity_crash", policy=policy)
    content = content_for(level)      # what that level is permitted to emit

===========================================================================================
*** THE THING THE SCOPE ASKED FOR IS "IN ONE PLACE", AND THE DEFECT IS TWO CALL SITES ***
===========================================================================================
BLUEPRINT §8: *"Drill-down proportional to risk (PID §4) is a property of the ENVELOPE, not
of a front end... The surfaces render what they are given, so the proportionality rule lives
in one place and is testable without a browser."*

**TWO CALL SITES THAT EACH DECIDE HOW MUCH DETAIL TO EMIT IS THE DEFECT**, and it is a
defect with a specific consequence: the public page and the private page drift, and the one
that drifts wider is the public one, which is the one that must not. So this module is the
only place a detail level is decided, and ``tests/test_detail_level.py`` asserts that over
the whole package by walking the source.

===========================================================================================
THE THREE LEVELS AND WHAT EACH EMITS ARE RATIFIED. THE THRESHOLDS ARE NOT.
===========================================================================================
**THE CLAUSE.** ``PID.md`` §4, ratified:

    | Drill-down proportional to risk: **calm** = dial + one line; **elevated** = the
    | categories carrying the score; **acute** = everything, ranked by contribution.

So :data:`DETAIL_ORDER` and :data:`DETAIL_CONTENT` are **derived, verbatim**, from that
sentence — three levels, in that order, each emitting what the clause says it emits. A
fourth level is a PID amendment.

**AND THE THRESHOLDS ARE NOT DERIVABLE FROM ANYTHING** (``CD-RULE-003``). Deciding *at what
score* a dial stops being calm and becomes elevated requires a SCALE, and
:mod:`crash_detector.dials.scores` refuses to declare one in terms:

    *"No range constraint is imposed on the magnitude, and that is a refusal, not an
    omission. A declared range is a declared scale, and the scale of a dial is what the dial
    MEANS"* — owed under ``CD-D-005``, which is ``Q25``, **held with the Product Authority.**

    *** SO THERE IS NO DEFAULT POLICY IN THIS MODULE. A CALLER THAT CANNOT STATE THE
        THRESHOLDS DOES NOT GET PRUDENT-LOOKING ONES. IT GETS AN ERROR. ***

This is the same branch :mod:`crash_detector.regime` takes for ``window_for(regime)`` and the
same rule :mod:`crash_detector.staleness` states as *"there is no default window anywhere"*.

===========================================================================================
*** WHAT **IS** ENFORCED WITHOUT ANY THRESHOLD, AND IT IS CONSTITUTIONAL ***
===========================================================================================
``PID.md`` §3.2, ratified doctrine, and §4's prohibited-behaviour list:

    *"**Missing data must never render as calm.** Absence of signal is not absence of risk."*
    *"Prohibited behaviour: rendering stale or missing data as calm."*

**THAT NEEDS NO SCALE AND IT IS ENFORCED AT POLICY CONSTRUCTION.** A policy that maps a
``Degraded`` or ``Unknown`` reading to ``calm`` is **REFUSED**, so the prohibited rendering
is unrepresentable rather than merely discouraged — whatever thresholds a deployment
eventually declares. It is the single most load-bearing thing this module does, and it is
the half that did not have to wait for ``Q25``.

===========================================================================================
*** PER DIAL. NEVER ACROSS BOTH. THIS IS A ``CD-AC-002`` QUESTION AND IT IS RAISED. ***
===========================================================================================
:func:`detail_level_for` takes **ONE** reading and **ONE** dial slot. There is no function in
this module that takes both dials, and that is deliberate:

    A single envelope-level ``detail_level`` derived from BOTH readings would require a
    function that consumes the equity magnitude and the monetary magnitude and returns one
    answer. **That is the shape ``CD-AC-002`` forbids** — *"there is no function anywhere
    that takes both dial types and returns a number"* — reached one step to the side, since
    the output is a level rather than a number.

BLUEPRINT §8 says *"the envelope carries ``detail_level`` derived from the reading itself"*,
singular, which reads as per-reading and therefore per-dial. **But the envelope is singular
and the readings are two, so the sentence is genuinely ambiguous about where the field
attaches** — and where it attaches has a doctrine consequence.

The increment-15 seat did not resolve it (``PBG-AUTH-005``: implementation choices are the
Engineer's; product meaning is not), built the mechanism in the shape that CANNOT breach
``CD-AC-002`` — per dial — and raised the placement as ``CD-ENG-WO3-02-F03``.

*** **THAT QUESTION IS NOW RULED. ``PO-DECISIONS-0025`` ruling 5 (``Q29``):
"detail_level attaches PER-DIAL."** *** The ruling RATIFIES the shape already built and what
was owed was the WIRING, which WO-3 increment 16A paid:

* ``detail_level`` is declared in ``$defs/dial_reading`` in **both** closed envelope
  schemas, inside the dial object and **NOT at envelope top level**;
* it is **required in every branch** of the ``VALUE | DEGRADED | UNKNOWN`` union, because
  ``additionalProperties: false`` holds at the parent AND inside each branch, so a key must
  be admitted in each branch it is to appear in;
* ``schema_version`` was bumped ``1.0.0 -> 1.1.0`` in both contracts. **That bump is the
  friction this docstring named and it was paid once, deliberately.**

**AND THE TOP-LEVEL ABSENCE IS NOW A GUARDED PROPERTY RATHER THAN A CIRCUMSTANCE.**
``tests/test_detail_level.py`` asserts all three of: absent at top level (the ``CD-AC-002``
hazard, still live), present in ``$defs/dial_reading``, and admitted in every branch
including ``UNKNOWN`` — and proves each arm non-vacuous against MUTATED COPIES. The guard it
replaced checked only ``schema["properties"]`` and ``schema["required"]``, so **a per-dial
attachment passed it untouched**: it was enforced against the rejected option and unenforced
against the proposed one (``CD-PL-F169``).

===========================================================================================
DECLARED LIMIT (CD-RULE-004).
===========================================================================================
 1  **NO OPERATING THRESHOLD IS ESTABLISHED**, because the dial has no ratified scale. A
    deployment declaring ``{elevated: 0.4, acute: 0.8}`` satisfies every check here and
    those numbers mean nothing until ``Q25`` gives the dial a scale.
    **NOT PROVED TO BE CARRIED ANYWHERE**, and deliberately so.

    **AND AT 16A A SHARPER VERSION OF THE SAME LIMIT IS TRUE AND IS STATED RATHER THAN LEFT
    TO BE DISCOVERED: THE THRESHOLDS ARE ENTIRELY UNEXERCISED IN PRODUCTION.** With zero
    registered sources every dial reads ``Unknown``, and the ``Unknown`` branch never
    reaches :func:`_level_for_score` at all — it returns ``policy.absent_data_level``
    directly. So ``elevated_at`` and ``acute_at`` are read from the environment, validated,
    carried, and **never compared against anything** until ``16B`` registers a source AND
    ``Q25`` gives the dial a scale. They are exercised only by this package's own tests.

 2  **``detail_level`` IS PUBLISHED AS OF 16A — SUPERSEDING WHAT THIS LIMIT SAID AT
    INCREMENT 15**, which was: *"detail_level IS NOT PUBLISHED. Both closed envelope schemas
    still record it as DELIBERATELY ABSENT AND OWED... CD-AC-006's proportionality half is
    NOT DELIVERED by this increment."* **THAT WAS TRUE WHEN WRITTEN AND IS NOW FALSE**: the
    field is wired per-dial into both contracts under ``PO-DECISIONS-0025`` ruling 5.
    **WHAT IS STILL NOT DELIVERED, AND THE DISTINCTION MATTERS:** the field is in the
    CONTRACT, and no running process publishes an envelope, because ``src/`` has no
    entrypoint and ``publish_cycle`` has zero callers (``CD-PL-F167``). **A SCHEMA IS NOT A
    SURFACE.** ``CD-AC-006``'s proportionality half is REACHABLE now and is still not
    EVIDENCED by a live publication.

 3  **THE LEVEL IS DECIDED FROM THE READING AND FROM NOTHING ELSE.** It does not consult the
    regime, the witness panel or the other dial. Whether risk-proportionality ought to
    consider the regime is a product question nobody has asked.
    **NOT PROVED TO BE CARRIED ANYWHERE.**

 4  **THE ENVIRONMENT IS READ, NOT TRUSTED TO EXIST.** :func:`detail_policy_from_env` takes
    the thresholds from ``CD_DETAIL_*`` and **REFUSES when a variable is unset**. The
    alternative — a documented default — was considered and REJECTED, and the reason is this
    module's own standing rule rather than taste: a default ``elevated_at`` IS a declared
    scale, and *"the scale of a dial is what the dial MEANS"*, owed under ``CD-D-005``
    (``Q25``). A number that looks prudent in a config template is the same invention as a
    number that looks prudent in code; only the file changed.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from typing import Mapping, Tuple

from crash_detector.dials.reading import Degraded, Unknown, Value, fold
from crash_detector.publication.dial_scalar import number_for_dial_slot

__all__ = [
    "DETAIL_CALM",
    "DETAIL_ELEVATED",
    "DETAIL_ACUTE",
    "DETAIL_ORDER",
    "DETAIL_CONTENT",
    "DETAIL_ORDER_SOURCE",
    "DETAIL_ELEVATED_AT_ENV_VAR",
    "DETAIL_ACUTE_AT_ENV_VAR",
    "DETAIL_ABSENT_DATA_LEVEL_ENV_VAR",
    "DETAIL_POLICY_ENV_VARS",
    "DetailPolicyIncoherent",
    "DetailPolicyNotConfigured",
    "DetailPolicy",
    "detail_policy_from_env",
    "detail_level_for",
    "content_for",
]

#: PID §4, verbatim and in its own order: ascending risk.
DETAIL_CALM = "calm"
DETAIL_ELEVATED = "elevated"
DETAIL_ACUTE = "acute"

DETAIL_ORDER: Tuple[str, ...] = (DETAIL_CALM, DETAIL_ELEVATED, DETAIL_ACUTE)

#: *** THE PROPORTIONALITY RULE ITSELF, AND THE ONE PLACE IT LIVES. ***
#: What each level is permitted to emit, taken WORD FOR WORD from PID §4. A surface renders
#: what it is given; it does not decide this, which is why the rule is testable without a
#: browser.
DETAIL_CONTENT: Mapping[str, Tuple[str, ...]] = {
    DETAIL_CALM: ("dial", "one_line"),
    DETAIL_ELEVATED: ("dial", "one_line", "contributing_categories"),
    DETAIL_ACUTE: ("dial", "one_line", "contributing_categories", "contributions_ranked"),
}

DETAIL_ORDER_SOURCE = (
    "PID.md §4, ratified: 'Drill-down proportional to risk: calm = dial + one line; "
    "elevated = the categories carrying the score; acute = everything, ranked by "
    "contribution.' The three levels and what each emits are DERIVED from that clause. The "
    "THRESHOLDS between them are not derivable from any ratified text — they require a dial "
    "SCALE, and crash_detector.dials.scores refuses to declare one because 'the scale of a "
    "dial is what the dial MEANS', owed under CD-D-005 (Q25). PID §3.2 is separately "
    "constitutional and needs no scale: 'Missing data must never render as calm.'"
)


#: The thresholds and the absent-data level come from the ENVIRONMENT, never from a literal
#: in this module (``PBG-SEC-001``, Standards Baseline §10/§12, and ``PO-DECISIONS-0025``
#: ruling 2: ALL config via env). Named here as DATA so a refusal can say which variable was
#: missing, and so the deploy audit can find them without reading prose.
DETAIL_ELEVATED_AT_ENV_VAR = "CD_DETAIL_ELEVATED_AT"
DETAIL_ACUTE_AT_ENV_VAR = "CD_DETAIL_ACUTE_AT"
DETAIL_ABSENT_DATA_LEVEL_ENV_VAR = "CD_DETAIL_ABSENT_DATA_LEVEL"

DETAIL_POLICY_ENV_VARS: Tuple[str, ...] = (
    DETAIL_ELEVATED_AT_ENV_VAR,
    DETAIL_ACUTE_AT_ENV_VAR,
    DETAIL_ABSENT_DATA_LEVEL_ENV_VAR,
)


class DetailPolicyIncoherent(ValueError):
    """A declared detail policy cannot mean what it claims, or breaches PID §3.2."""


class DetailPolicyNotConfigured(DetailPolicyIncoherent):
    """The environment did not declare a detail policy, so there is none to apply.

    *** **A SUBCLASS OF** :exc:`DetailPolicyIncoherent` **DELIBERATELY**, so that a caller
    already guarding the policy boundary cannot acquire a NEW unguarded failure mode by this
    increment adding a new exception type beside the one it catches. A policy nobody
    declared is the limiting case of a policy that cannot mean what it claims. ***

    **AND IT IS RAISED RATHER THAN DEFAULTED, WHICH WAS A DECISION AND NOT AN OMISSION.**
    Supplying ``elevated_at`` when the deployment did not is declaring a SCALE for the dial,
    and :mod:`crash_detector.dials.scores` refuses to declare one in terms — *"a declared
    range is a declared scale, and the scale of a dial is what the dial MEANS"* — owed under
    ``CD-D-005``, which is ``Q25``. A default in a config template is the same invention as
    a default in code; only the file it hides in changed.

    ``absent_data_level`` is refused on the same terms even though PID §3.2 narrows it to
    two admissible values, because "narrowed to two" is not "decided", and choosing between
    ``elevated`` and ``acute`` for missing data is a product judgement about how loudly
    absence should shout.
    """


@dataclass(frozen=True)
class DetailPolicy:
    """The declared thresholds, and the level absent data renders at.

    **REFUSED AT CONSTRUCTION:**

    * thresholds that do not STRICTLY ascend from ``elevated`` to ``acute`` — a policy in
      which acute begins below elevated has an unreachable level, and an unreachable level
      is a drill-down tier nobody ever sees;
    * a threshold that is not a plain finite number;
    * *** an ``absent_data_level`` of ``calm`` — ``PID`` §3.2, CONSTITUTIONAL: "Missing data
      must never render as calm." *** This refusal needs no scale and is the half of this
      module that did not have to wait for ``Q25``.
    """

    #: SEALED (PO-DECISIONS-0016 ruling 2).
    __slots__ = ("elevated_at", "acute_at", "absent_data_level")

    elevated_at: float
    acute_at: float
    absent_data_level: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            f"{cls.__name__} may not subclass DetailPolicy: a subclass could skip the "
            "PID §3.2 refusal in its own __post_init__ and still satisfy every isinstance "
            "check downstream. The policy is CLOSED."
        )

    def __post_init__(self) -> None:
        for name in ("elevated_at", "acute_at"):
            declared = getattr(self, name)
            if type(declared) is not float and type(declared) is not int:
                raise DetailPolicyIncoherent(
                    f"{name} must be a plain int or float, got "
                    f"{type(declared).__name__}. A subclass of a number may redefine "
                    "comparison, and the comparison is the whole of the answer."
                )
            if not math.isfinite(float(declared)):
                raise DetailPolicyIncoherent(f"{name} must be finite, got {declared!r}.")
            object.__setattr__(self, name, float(declared))

        if not self.elevated_at < self.acute_at:
            raise DetailPolicyIncoherent(
                f"elevated begins at {self.elevated_at!r} and acute at {self.acute_at!r}, "
                "so the levels do not strictly ascend. A policy in which acute begins at or "
                "below elevated has a tier that is unreachable, and an unreachable "
                "drill-down tier is one nobody ever sees. REFUSED, not reordered."
            )

        if self.absent_data_level not in DETAIL_ORDER:
            raise DetailPolicyIncoherent(
                f"{self.absent_data_level!r} is not a declared detail level. The vocabulary "
                f"is {list(DETAIL_ORDER)}. {DETAIL_ORDER_SOURCE}"
            )

        # *** PID §3.2. CONSTITUTIONAL. NO SCALE REQUIRED. ***
        if self.absent_data_level == DETAIL_CALM:
            raise DetailPolicyIncoherent(
                "absent_data_level is 'calm', and PID §3.2 is constitutional on this: "
                "'MISSING DATA MUST NEVER RENDER AS CALM. Absence of signal is not absence "
                "of risk.' PID §4 lists 'rendering stale or missing data as calm' as "
                "PROHIBITED BEHAVIOUR. A Degraded or Unknown reading is exactly that "
                "missing data, and calm is exactly that rendering. REFUSED — and this "
                "refusal needs no dial scale, so it holds whatever thresholds are declared."
            )


def detail_policy_from_env(environ: "Mapping[str, str] | None" = None) -> DetailPolicy:
    """The declared :class:`DetailPolicy`, read from the environment. **NO DEFAULTS.**

    Every one of :data:`DETAIL_POLICY_ENV_VARS` must be set, or
    :exc:`DetailPolicyNotConfigured` names the missing one. See that exception for why a
    documented default was rejected.

    ``environ`` is a parameter rather than a hardcoded read of :data:`os.environ` so a test
    can exercise this without mutating process state — the same reason
    :func:`~crash_detector.publication.envelope_contract.contracts_dir` takes its override
    from a named variable. It defaults to the real environment.

    The value is parsed here and JUDGED by :class:`DetailPolicy`'s own ``__post_init__``.
    **There is no second copy of the PID §3.2 refusal in this function**, and there must not
    be: two guarded comparison sites are an enumeration, and enumerations come apart. A
    ``CD_DETAIL_ABSENT_DATA_LEVEL=calm`` therefore fails in exactly the place, and with
    exactly the message, that a hand-built policy would.
    """
    source = os.environ if environ is None else environ

    missing = [name for name in DETAIL_POLICY_ENV_VARS if not source.get(name)]
    if missing:
        raise DetailPolicyNotConfigured(
            f"no detail policy is declared: {', '.join(missing)} "
            f"{'is' if len(missing) == 1 else 'are'} unset or empty. This is a REFUSAL and "
            "not a missing default. Supplying a threshold nobody declared would be "
            "declaring a SCALE for the dial, and the scale of a dial is what the dial "
            f"MEANS — owed under CD-D-005 (Q25). {DETAIL_ORDER_SOURCE}"
        )

    numbers = {}
    for name, variable in (
        ("elevated_at", DETAIL_ELEVATED_AT_ENV_VAR),
        ("acute_at", DETAIL_ACUTE_AT_ENV_VAR),
    ):
        raw = source[variable]
        try:
            numbers[name] = float(raw)
        except (TypeError, ValueError):
            # The OFFERED VALUE is not echoed. A refusal message is a log line and a log
            # line is a governed artefact; the variable NAME is what a reader needs.
            raise DetailPolicyNotConfigured(
                f"{variable} is not a number, so no threshold can be read from it."
            ) from None

    return DetailPolicy(
        elevated_at=numbers["elevated_at"],
        acute_at=numbers["acute_at"],
        absent_data_level=source[DETAIL_ABSENT_DATA_LEVEL_ENV_VAR],
    )


def content_for(level: str) -> Tuple[str, ...]:
    """What ``level`` is permitted to emit. **The single source of the rule.**

    A surface calls this; it does not decide. There is no ``level, extra`` and no override,
    because an override is a second place the rule lives.
    """
    try:
        return DETAIL_CONTENT[level]
    except (KeyError, TypeError):
        raise DetailPolicyIncoherent(
            f"{level!r} is not a declared detail level. The vocabulary is "
            f"{list(DETAIL_ORDER)}. {DETAIL_ORDER_SOURCE}"
        ) from None


def detail_level_for(reading: object, *, dial_slot: str, policy: DetailPolicy) -> str:
    """The detail level for **ONE** reading of **ONE** dial.

    *** THERE IS NO VARIANT OF THIS FUNCTION THAT TAKES BOTH DIALS. *** See the module
    docstring: a level derived from both readings is the shape ``CD-AC-002`` forbids,
    reached one step to the side.

    The magnitude is released through
    :func:`~crash_detector.publication.dial_scalar.number_for_dial_slot` — the existing
    gate — so a number reaches this comparison only if its provenance is exactly the dial of
    the slot it claims. A bare float cannot be compared here, because a bare float cannot
    get past that door.

    Dispatch is :func:`~crash_detector.dials.reading.fold`, whose three branches are
    required keyword arguments: **a caller cannot forget ``Unknown`` and fall through to the
    value branch**, which is the exact failure PID §3.2 forbids.
    """
    if type(policy) is not DetailPolicy:
        raise TypeError(
            "a detail level is decided against a DetailPolicy, got "
            f"{type(policy).__name__}. A bare pair of numbers is not a policy: it has not "
            "passed the PID §3.2 admission that gives the policy its meaning."
        )

    def on_value(present: "Value") -> str:
        return _level_for_score(
            number_for_dial_slot(dial_slot, present.value), policy=policy
        )

    def on_degraded(damaged: "Degraded") -> str:
        # Carries a value AND its damage. The damage decides: PID §3.2 forbids calm for it,
        # and the policy has already been refused if it named calm here.
        return policy.absent_data_level

    def on_unknown(absent: "Unknown") -> str:
        # No value field of any kind. There is no number to compare, and 'no signal' is not
        # 'no risk'.
        return policy.absent_data_level

    return fold(
        reading, on_value=on_value, on_degraded=on_degraded, on_unknown=on_unknown
    )


def _level_for_score(score: float, *, policy: DetailPolicy) -> str:
    """Ascending comparison, most severe first, so the bands cannot overlap."""
    if score >= policy.acute_at:
        return DETAIL_ACUTE
    if score >= policy.elevated_at:
        return DETAIL_ELEVATED
    return DETAIL_CALM
