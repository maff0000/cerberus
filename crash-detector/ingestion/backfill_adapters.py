"""BACKFILL-ONLY adapter construction — the one door :class:`AlfredVintageAdapter` is behind.

WO-1.14. ``ingestion.catalog.build_adapter`` is the LIVE collector's constructor: one call,
one bounded GET, a few seconds of budget, called once per ingredient per pass by
``ingestion.run``. :class:`~ingestion.adapters.AlfredVintageAdapter` cannot be that: ONE
``fetch`` is a bisection over vintage dates costing ``2 + ceil(log2(days))`` GETs under a
TOTAL deadline, and it answers for ONE named observation date rather than for "the latest".
Reaching it from the live loop would not be a slow poll, it would be a different question
answered under a budget that cannot carry it.

WHY THIS IS A SEPARATE MODULE AND NOT A FLAG. The obvious shape is
``build_adapter(ing, clock, backfill=True)``, and it is the wrong one: the live loop would
then be one mistaken keyword away from the vintage search, and nothing but a reviewer's
attention would stand between them. So the separation is STRUCTURAL and runs the only
direction that cannot be reopened by a later edit:

    * this module imports ``ingestion.catalog``; ``ingestion.catalog`` does not import this
      module, and cannot — the reverse import is an import cycle, so the live module cannot
      acquire a reference to the vintage adapter by accident;
    * ``ingestion.catalog`` never names :class:`~ingestion.adapters.AlfredVintageAdapter` at
      all. Not in ``build_adapter``, not in its imports, not in its ``__all__``. There is no
      argument, flag or ``kind`` string that makes ``build_adapter`` return one;
    * ``ingestion.run`` — the live loop — imports ``ingestion.catalog`` and NOT this module.

``tests/test_wo114.py`` asserts each of those three as a property of the source and of the
imported namespaces, so this is a tested boundary rather than a described one.

WHAT ROUTES WHERE, AND ON WHOSE AUTHORITY. ``ingestion.vintage.requires_original_vintage``
decides, and it is the only thing that decides. Measured-stable pairs are backfilled from
FRED's current body (:class:`~ingestion.adapters.FredAdapter`, exactly as live); everything
else — measured revision-prone, AND anything never probed — is backfilled vintage by
vintage. That default is the fail-safe direction and it belongs to ``ingestion.vintage``,
not here; this module only obeys it.

A DECLARED LIMIT OF THE STABLE BRANCH, STATED RATHER THAN DISCOVERED LATER.
:class:`~ingestion.adapters.FredAdapter` asks for the whole current series and reads its
LATEST observation, plus ``ing.history`` rows before it. That is the right ANSWER for a
measured-stable pair — stability measured over the replay window is exactly the claim that
today's body carries the figure a collector would have seen — but it is not yet a per-date
fetch: selecting the observation for a given date out of that body, and deciding whether
``history`` must be deepened to reach back far enough, is the BACKFILL DRIVER's work and is
not settled here. ``observation_date`` is therefore consumed by the vintage branch only, and
is accepted on both so that one call site routes without knowing which branch it will get.

NOTHING HERE FETCHES, PACES, STORES OR LABELS. It constructs an adapter and returns it, the
same as ``build_adapter``. The ``vintage=`` label a backfilled reading carries
(``ingestion.vintage.VINTAGE_ORIGINAL`` / ``VINTAGE_CURRENT_ONLY``) is the driver's to write,
and the driver does not exist yet.
"""

from __future__ import annotations

from datetime import datetime
from typing import Callable

from ingestion.adapters import ALFRED_HOST, AlfredVintageAdapter, FredAdapter
from ingestion.catalog import Ingredient
from ingestion.vintage import requires_original_vintage

__all__ = ["BACKFILL_EGRESS_HOSTS", "VINTAGE_BACKFILLABLE_KINDS", "build_backfill_adapter"]

#: HTTP hosts reached ONLY by the backfill path. SEPARATE from ``ingestion.catalog``'s
#: :data:`~ingestion.catalog.EGRESS_HOSTS` for the same reason this module is separate from
#: that one, and the separation is the point rather than a filing convenience.
#:
#: WHY ``alfred.stlouisfed.org`` IS NOT IN ``EGRESS_HOSTS``. That dict is DERIVED from what
#: the LIVE collector's adapters resolve to — ``tests/test_ingestion.py`` asserts it equals
#: the hostnames of ``build_adapter(i)._url()`` over :data:`~ingestion.catalog.INGREDIENTS`,
#: by EQUALITY — and it is mirrored host-for-host by ``deploy/egress-destinations.yaml`` and
#: by ``cd-collectors``' ``x-egress.hosts`` in ``deploy/compose.yaml``. Putting ALFRED there
#: would be a false claim in the one place the system makes claims about egress: it would say
#: the live collector service reaches this host, which it structurally does not and must not.
#:
#: WHY IT IS NOT IN ``deploy/egress-destinations.yaml`` EITHER, AND WHAT THAT LEAVES OWED.
#: A registered destination's ``services`` list must name compose services that exist and
#: declare ``policy: ALLOWLIST`` (CD-EGRESS-004/006, closing CD-ASR-F04). The only such
#: service that could carry ALFRED today is ``cd-collectors`` — the live collector — so
#: registering it there would import the very claim the paragraph above refuses, in the file
#: whose whole purpose is that an egress claim be true and attributable. The honest entry
#: names a BACKFILL service, and ``deploy/compose.yaml`` declares no such service: the
#: designed six-service stack is unchanged by this WO and adding a seventh is an architecture
#: decision, not this round's. So what is OWED, named here so it is not invisible: when the
#: backfill driver round lands, it owes a compose service with its own ``x-egress``
#: ALLOWLIST and a ``DEST-ALFRED-001`` entry registered to THAT service. Until then this
#: declaration is where the host is written down, and no allowlist anywhere permits it —
#: fail-closed, which is the accurate description of a backfill that does not run yet.
BACKFILL_EGRESS_HOSTS: dict[str, str] = {
    ALFRED_HOST: "Federal Reserve Bank of St. Louis (ALFRED vintage graph CSV; keyless, "
                 "the same public door as fred.stlouisfed.org with a vintage_date parameter)",
}

#: The ingredient kinds a POINT-IN-TIME backfill has been reasoned about for, stated
#: positively so every other kind is refused rather than quietly handled. ALFRED serves
#: vintages of FRED series and nothing else: there is no vintage endpoint behind Cboe, Yahoo,
#: multpl, LBMA or the HERMES peer, and ``ingestion.vintage``'s evidence covers the 23 FRED
#: pairs only. A backfill of a non-FRED kind would therefore be today's value wearing a past
#: date, which is the forgery this whole WO exists to prevent — so it is a refusal here, and
#: whether those kinds can be backfilled at all is an open question with an owner, not a
#: default this module gets to pick.
VINTAGE_BACKFILLABLE_KINDS = ("fred",)


def build_backfill_adapter(ing: Ingredient, observation_date: str, clock: Callable[[], datetime]):
    """The adapter that answers for ``ing`` at ``observation_date`` — point-in-time where it must.

    :class:`~ingestion.adapters.AlfredVintageAdapter` when
    ``ingestion.vintage.requires_original_vintage`` says this pair needs the figure as first
    published; :class:`~ingestion.adapters.FredAdapter` when stability was POSITIVELY
    measured. A kind outside :data:`VINTAGE_BACKFILLABLE_KINDS` is refused.
    """
    if ing.kind not in VINTAGE_BACKFILLABLE_KINDS:
        raise ValueError(
            f"{ing.source_id} is kind {ing.kind!r}; a point-in-time backfill is declared only for "
            f"{VINTAGE_BACKFILLABLE_KINDS} (see ingestion.backfill_adapters.VINTAGE_BACKFILLABLE_KINDS)"
        )
    common = dict(source_id=ing.source_id, as_of_rule=ing.as_of_rule, unit=ing.unit, clock=clock)
    if requires_original_vintage(ing.ref, ing.transformation):
        return AlfredVintageAdapter(ing.ref, ing.transformation, observation_date, **common)
    return FredAdapter(ing.ref, ing.transformation, ing.history, **common)
