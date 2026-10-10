"""Regime-aware staleness — ``window_for(regime)`` (CD-AC-009, BLUEPRINT §7).

    RegimeStalenessPolicy({"CALM": 600.0, "STRESS": 120.0}).window_for("STRESS")
        -> StalenessWindow(seconds=120.0)

**THE SAME AGE THAT PASSES IN CALM FAILS IN STRESS.** That sentence is the criterion, and
this module makes it a property of the TYPE rather than a property of whichever two numbers
somebody configured.

===========================================================================================
WHAT WAS ALREADY HERE, MEASURED BEFORE A LINE WAS WRITTEN
===========================================================================================
``crash_detector.staleness`` derives a CEILING of 900 s from PID §5's ratified assurance
latency budget, and says — five times, in its docstring, in two module constants and in its
declared limit 1 — that the OPERATING window is ``window_for(regime)``, **owed at WO-3**,
and that it deliberately implements none of it::

    grep -n regime src/crash_detector/staleness.py   ->  5 lines, ALL PROSE
    grep -n regime src/crash_detector/engine/config.py -> 1 line, PROSE
    grep -rn regime src/ --include=*.py              ->  6 lines, NOT ONE OF THEM CODE

So there was no half-built mechanism to extend and none to build a second one beside. What
there was is a DOOR — :class:`~crash_detector.staleness.StalenessWindow` — and the whole of
this module's relationship to it is that **every window it hands out comes through that
door**. The ceiling therefore still binds: a policy cannot widen a window past 900 s by
declaring it, because declaring it constructs a ``StalenessWindow`` and that constructor
refuses.

===========================================================================================
THE VOCABULARY IS DERIVED, NOT CHOSEN (CD-RULE-003)
===========================================================================================
**THE CLAUSE.** ``PID.md`` §6, the ratified criterion table, ``CD-AC-009``:

    | **CD-AC-009** | Regime-aware staleness windows | in a planted high-vol regime, the
    | staleness window tightens; **the same age that passes in calm fails in stress** |

and ``PID.md`` §4: *"Regime-aware staleness: windows tighten when vol spikes"*.

**THE DERIVATION.** The ratified sentence names exactly two regimes — **calm** and
**stress** — and states a RELATION between their windows rather than a value for either.
:data:`REGIME_ORDER` is those two, in the order the clause puts them, and nothing else. A
third regime is a PID amendment, in the same way a third dial slot is
(:data:`~crash_detector.publication.dial_scalar.PUBLISHABLE_DIAL_SLOTS`, "Two. A third is a
PID amendment.").

**AND THE NUMBERS ARE NOT DERIVED, BECAUSE NO CLAUSE GIVES THEM.** This is the branch
:mod:`crash_detector.dials.scores` takes and :mod:`crash_detector.staleness` did not: there
the clause existed and the ceiling was derived from it; here it does not. Nothing in the
PID, the Blueprint or any ratified decision says a calm window is 600 s, or 300 s, or any
number at all. **SO THIS MODULE DECLARES NONE.**

    *** THERE IS NO DEFAULT POLICY IN THIS MODULE, AND A CALLER THAT CANNOT STATE ONE DOES
        NOT GET A PRUDENT ONE. IT GETS AN ERROR. ***

That is :mod:`crash_detector.staleness`'s own rule ("THERE IS NO DEFAULT WINDOW ANYWHERE")
carried up one level, and a test asserts by module attribute scan that no constructed policy
is reachable from this module.

===========================================================================================
*** WHAT IS ENFORCED IS THE RELATION, AND THAT IS THE WHOLE POINT ***
===========================================================================================
A seat that invented ``{"CALM": 600, "STRESS": 120}`` would have satisfied CD-AC-009 for
exactly as long as nobody edited the numbers. The criterion is not those numbers; it is that
**stress is tighter than calm**, whatever the numbers are.

:class:`RegimeStalenessPolicy` refuses, at construction, ANY policy in which the window does
not **strictly tighten** as stress rises. So:

* ``{"CALM": 600, "STRESS": 120}``  -> admitted; the relation holds;
* ``{"CALM": 600, "STRESS": 600}``  -> **REFUSED**; a constant window is the criterion's own
  named violation, *"the window made constant"*;
* ``{"CALM": 120, "STRESS": 600}``  -> **REFUSED**; *"the comparison inverted so stress
  loosens it"*;
* ``{"CALM": 600}``                 -> **REFUSED**; a regime with no declared window does not
  fall back to the ceiling, to the calm window, or to anything else. Deny by default.

**A DEPLOYMENT THEREFORE CANNOT CONFIGURE ITS WAY OUT OF CD-AC-009.** That matters because
the finding that created :mod:`crash_detector.staleness` — ``CD-ASR-F06`` — was reached
**by configuration alone, with no source edit at all**. Closing the class means the
configuration surface cannot express the violation either.

===========================================================================================
WHAT THIS MODULE DOES NOT DO, STATED SO IT IS NOT OVER-READ
===========================================================================================
**IT DOES NOT COMPUTE THE REGIME.** BLUEPRINT §7: *"The regime is computed from the engine's
own ingredients"* — and there are **no registered ingredients**: ``raw.source_registry`` is
empty by design and the ingredient set is held with the Product Authority (``CD-D-005`` /
``Q25``). A classifier written now would be a classifier over nothing, and choosing which
observed quantity means "vol spiked" is product meaning (``PBG-AUTH-005``). **The regime
arrives as an argument. Deciding it is somebody else's, and it is owed with the source set.**

===========================================================================================
DECLARED LIMIT (CD-RULE-004). Stated identically here, in ``required-tests.yaml`` and in
``contracts/execution/CD-RT-009-REGIME-AWARE-STALENESS.md``.
===========================================================================================
 1  **THE RELATION IS ENFORCED; THE OPERATING NUMBERS ARE NOT ESTABLISHED.** A deployment
    declaring ``{"CALM": 900.0, "STRESS": 899.0}`` satisfies every check in this module and
    has a stress window one second tighter than a calm window that consumes the ENTIRE PID §5
    detectability budget. The relation holds and the deployment is still bad.
    **NOT PROVED TO BE CARRIED ANYWHERE.** Bounding it needs an operating window, which is
    the product quantity this module refuses to invent.

 2  **THE REGIME IS TAKEN ON TRUST FROM THE CALLER.** This module admits a regime NAME
    against a closed vocabulary; it does not and cannot check that the named regime is the
    one the market is actually in. A caller that passes ``CALM`` during a crash gets the calm
    window. **NOT PROVED TO BE CARRIED ANYWHERE** — the classifier is owed with the
    ingredient set, and until it exists there is nothing to compare the claim against.

 3  **THE CEILING IS CARRIED, THE FLOOR IS NOT.** Every window is admitted through
    :class:`~crash_detector.staleness.StalenessWindow`, so ``> 900 s`` is refused
    — MEASURED, and the refusal comes from that constructor and not from a check repeated
    here. There is no lower bound beyond "strictly positive": ``{"CALM": 0.002, "STRESS":
    0.001}`` is admitted and would make everything permanently stale.
    **NOT PROVED TO BE CARRIED ANYWHERE**, and it is the same missing clause as boundary 1.

 4  **A POLICY IS DATA AND DATA CAN BE FORGED PAST FROZEN.** ``object.__setattr__`` walks
    past ``@dataclass(frozen=True)`` here exactly as it does on every frozen value in this
    repository — see :mod:`crash_detector.staleness` boundary 3, which measures the identical
    residue. ``__slots__`` is declared, so an UNDECLARED attribute is refused; overwriting a
    DECLARED slot on a constructed value is not preventable at the Python level.
    **NOT PROVED TO BE CARRIED ANYWHERE.** A property of the language, not of this design.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Tuple

from crash_detector.staleness import StalenessWindow

__all__ = [
    "REGIME_CALM",
    "REGIME_STRESS",
    "REGIME_ORDER",
    "REGIME_ORDER_SOURCE",
    "RegimeNotDeclared",
    "StalenessPolicyIncoherent",
    "RegimeStalenessPolicy",
]

#: The two regimes ``PID.md`` §6 CD-AC-009 names, in the order that clause puts them:
#: ascending stress. DERIVED from the ratified sentence and not chosen — see the module
#: docstring. A third member is a PID amendment, reviewed as one.
REGIME_CALM = "CALM"
REGIME_STRESS = "STRESS"

#: Ascending stress. The ORDER is the load-bearing part: it is what
#: :class:`RegimeStalenessPolicy` walks to assert that the window strictly tightens, so the
#: criterion is checked against a declared sequence rather than against a pair of names
#: somebody remembered to compare.
REGIME_ORDER: Tuple[str, ...] = (REGIME_CALM, REGIME_STRESS)

#: The clause the vocabulary derives from, carried as DATA so a reader of a refusal is told
#: where the two names come from rather than having to trust them.
REGIME_ORDER_SOURCE = (
    "PID.md §6, ratified criterion table, CD-AC-009: 'in a planted high-vol regime, the "
    "staleness window tightens; the same age that passes in CALM fails in STRESS'; and "
    "PID.md §4: 'Regime-aware staleness: windows tighten when vol spikes'. The clause names "
    "exactly two regimes and states a RELATION between their windows rather than a value "
    "for either. The relation is enforced here; the numbers are the deployment's to declare "
    "and are NOT derivable from any ratified text (CD-RULE-003)."
)


class RegimeNotDeclared(KeyError):
    """A regime outside the declared vocabulary, or one the policy does not cover.

    A ``KeyError`` because what happened is a lookup that found nothing, and callers that
    already handle a missing key keep working. It is emphatically not a signal to fall back:
    there is no window to fall back to, which is the whole reason this raises.
    """


class StalenessPolicyIncoherent(ValueError):
    """A declared policy does not tighten as stress rises, or does not cover the vocabulary.

    A ``ValueError`` to sit beside
    :exc:`~crash_detector.staleness.StalenessWindowOutOfRange`, which refuses the same class
    of thing — a window that has been declared into a shape in which it cannot mean what it
    claims — one level down.
    """


@dataclass(frozen=True)
class RegimeStalenessPolicy:
    """``window_for(regime) -> StalenessWindow``, with the CD-AC-009 relation enforced.

    Constructing one IS the admission of the whole policy, and it is the only way to obtain
    one: there is no second route by which a regime can acquire a window, so there is no
    second site to keep in step. That is the identical argument
    :class:`~crash_detector.staleness.StalenessWindow` makes about a single window, applied
    to the mapping over regimes.

    **REFUSED AT CONSTRUCTION:**

    * a mapping that does not cover **every** member of :data:`REGIME_ORDER` — a regime with
      no declared window does not inherit one;
    * a mapping naming anything outside :data:`REGIME_ORDER` — deny by default, so a typo
      is a refusal rather than a silently ignored entry;
    * any window that :class:`~crash_detector.staleness.StalenessWindow` refuses, which is
      how the PID §5 ceiling of 900 s reaches this type without being restated in it;
    * **any policy in which the window does not STRICTLY tighten as stress rises** — equal
      windows and inverted windows are both refused, and they are the criterion's own two
      named violations.
    """

    #: SEALED (PO-DECISIONS-0016 ruling 2), for the reason
    #: :class:`~crash_detector.staleness.StalenessWindow` states: without ``__slots__`` an
    #: instance carries a ``__dict__``, and ``__new__`` followed by ``__dict__.update(...)``
    #: yields an object of exactly this type carrying forged windows, having executed NO
    #: package code. Declared here rather than via ``@dataclass(slots=True)``, which also
    #: installs a stdlib ``__setstate__`` that re-opens the same route by its sibling.
    __slots__ = ("windows",)

    #: Regime name -> the admitted window for it. Built here from primitives; never the
    #: mapping the caller passed in, which they retain a reference to and could mutate.
    windows: Mapping[str, StalenessWindow]

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            f"{cls.__name__} may not subclass RegimeStalenessPolicy: a subclass could skip "
            "the tightening check in its own __post_init__ and still satisfy every "
            "isinstance check downstream, which is precisely the CD-AC-009 violation this "
            "type exists to make unrepresentable. The policy is CLOSED."
        )

    def __post_init__(self) -> None:
        declared = self.windows
        if not isinstance(declared, dict) and not hasattr(declared, "items"):
            raise StalenessPolicyIncoherent(
                "a regime staleness policy is declared as a mapping of regime name to a "
                f"number of seconds, got {type(declared).__name__}."
            )

        offered = dict(declared)

        unknown = sorted(name for name in offered if name not in REGIME_ORDER)
        if unknown:
            raise StalenessPolicyIncoherent(
                f"policy names {unknown}, which are not declared regimes. The vocabulary is "
                f"{list(REGIME_ORDER)} and it is an allowlist: an entry nobody declared is "
                "refused because nobody declared it, not because anything was recognised "
                f"about it. {REGIME_ORDER_SOURCE}"
            )

        missing = [name for name in REGIME_ORDER if name not in offered]
        if missing:
            raise StalenessPolicyIncoherent(
                f"policy declares no window for {missing}. A regime with no declared window "
                "does NOT inherit the calm window, the ceiling, or any other lenient "
                "default: it has no window, and a window nobody chose is a staleness rule "
                "nobody chose. Declare one for every regime in "
                f"{list(REGIME_ORDER)}."
            )

        # Admitted through the ONE DOOR. The PID §5 ceiling of 900 s, the refusal of nan,
        # inf, zero, negatives, bools and number subclasses all arrive here by construction
        # rather than by being restated — a second copy of an admission rule is a second
        # copy that can drift.
        admitted = {name: StalenessWindow(seconds=offered[name]) for name in REGIME_ORDER}

        # *** CD-AC-009 ITSELF. Walked over the DECLARED ORDER, so the check is over the
        # vocabulary rather than over a pair of names written out here. ***
        for tighter, looser in zip(REGIME_ORDER[1:], REGIME_ORDER[:-1]):
            if not admitted[tighter].seconds < admitted[looser].seconds:
                raise StalenessPolicyIncoherent(
                    f"the {tighter!r} window is {admitted[tighter].seconds!r} s and the "
                    f"{looser!r} window is {admitted[looser].seconds!r} s, so the window "
                    "does NOT tighten as stress rises. CD-AC-009 is the RELATION and not "
                    "the numbers: 'the same age that passes in calm fails in stress'. An "
                    "equal window is the criterion's own named violation ('the window made "
                    "constant') and a wider one is the other ('the comparison inverted so "
                    "stress loosens it'). REFUSED, not reordered — silently sorting a "
                    "policy would apply an interval the operator did not configure, with "
                    f"nothing in the record saying so. {REGIME_ORDER_SOURCE}"
                )

        object.__setattr__(self, "windows", admitted)

    def window_for(self, regime: str) -> StalenessWindow:
        """The admitted window for ``regime``, or a refusal. **The one door.**

        Never returns a default and never returns the widest window it holds. A regime this
        policy does not cover cannot be covered by guessing, and the guess would be widest
        exactly when the caller is most confused about what regime it is in.
        """
        if type(regime) is not str:
            raise RegimeNotDeclared(
                f"a regime is named by a plain str, got {type(regime).__name__}. A subclass "
                "of str may redefine __eq__ and __hash__, and the lookup is the whole of "
                "this answer."
            )
        try:
            return self.windows[regime]
        except KeyError:
            raise RegimeNotDeclared(
                f"{regime!r} is not a declared regime. The vocabulary is "
                f"{list(REGIME_ORDER)}. {REGIME_ORDER_SOURCE}"
            ) from None

    def declared_regimes(self) -> Tuple[str, ...]:
        """The regimes this policy covers, in ascending order of stress."""
        return REGIME_ORDER
