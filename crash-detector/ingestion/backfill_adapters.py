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

WHAT ROUTES WHERE, AND ON WHOSE AUTHORITY. Within FRED,
``ingestion.vintage.requires_original_vintage`` decides and it is the only thing that
decides. Measured-stable pairs are backfilled from FRED's current body
(:class:`~ingestion.adapters.FredAdapter`, exactly as live); everything else — measured
revision-prone, AND anything never probed — is backfilled vintage by vintage. That default
is the fail-safe direction and it belongs to ``ingestion.vintage``, not here; this module
only obeys it.

THE DISPATCH BRANCHES ON ``kind`` FIRST, AND THAT IS NOT TIDINESS (WO-1.16). ``cboe`` and
``yahoo`` are now backfillable, and ``requires_original_vintage`` MUST NOT BE ASKED ABOUT
EITHER. The function answers a question about a FRED (series, transformation) pair measured
against ALFRED's vintage trail; a Cboe index id and a Yahoo symbol are not in
:data:`~ingestion.vintage.REVISION_STABLE` and never could be, so asking would return its
fail-safe ``True`` — "backfill this from original vintages" — about a source that HAS no
vintages and for which there is no vintage adapter to route to. It would not crash; it would
quietly give a confident wrong answer to a question that does not apply, which is worse. So
the branch is on ``ing.kind``: FRED keeps exactly today's logic, Cboe and Yahoo ask nothing
and construct their per-date readers directly.

WHAT THIS FUNCTION DOES NOT RE-CHECK, AND WHY THE ABSENCE IS THE DECISION (WO-1.16). ``yahoo``
is backfillable per COLUMN and not per kind — a dated read of ``adjclose`` has no
point-in-time meaning at all (:data:`~ingestion.vintage.NO_REVISION_MECHANISM_COLUMNS`), and
two live indicators ask for exactly that column — so there IS a Yahoo ingredient this module
must never hand back a working adapter for. It does not, and it does not take a line of its
own to say so: ``ing.column`` is resolved to ``field=`` and handed to
:class:`~ingestion.adapters.YahooChartAdapter`, whose ``__init__`` RAISES on
``field="adjclose"`` with an ``observation_date`` set — before a URL is built, before a byte
is fetched, before this function can return. That raise propagates out of the constructor
this function is required to call, so it IS this function's refusal; a copy of the rule here
would add no defence and one more place for it to drift out of step with the adapter that
enforces it. ``tests/test_wo114.py`` asserts the raise at THIS function's call site with the
real catalog rows, so what is held is the end-to-end refusal rather than one module's
politeness. The genuinely independent second door is a DIFFERENT question at a different
dispatch — ``ingestion.backfill``'s label selection, which can derive no label for
``yahoo``/``adjclose`` and stops the whole range — and it is independent exactly because it
does not re-ask this one.

BOTH BRANCHES NOW CONSUME ``observation_date`` (WO-1.15). They ask different sources, but
they ask the same question — "what does this pair say for the observation dated D?" — and
the stable branch asks it of FRED's CURRENT body by windowing the request on D
(``cosd``/``coed``) and matching the row by exact date
(``ingestion.adapters.parse_fred_csv_for_date``). That is the right ANSWER for a
measured-stable pair, and only for one: stability measured over the replay window is exactly
the claim that today's body carries the figure a collector would have seen, which is why
``ingestion.vintage`` — not this module — decides which pairs may be read that way, and why
``ingestion.backfill``'s date floor still refuses a date the measurement does not cover.

    THIS CLOSES THE LIMIT WO-1.14 DECLARED HERE and names what replaced it. The old text
    said the stable branch asked for the whole body and read its LATEST row, so a date years
    back came back as a perfectly good reading of the WRONG period, and that per-date
    selection was OWED. It is now done. What is NOT done and is not pretended to be:
    ``ing.history`` is not carried by a dated fetch — a one-day window has no history in it —
    so a backfilled reading for ``fred.DFII10.history`` carries the value and no history
    array. ``ingestion.adapters.parse_fred_csv_for_date`` records why.

NOTHING HERE FETCHES, PACES, STORES OR LABELS. It constructs an adapter and returns it, the
same as ``build_adapter``. The ``vintage=`` label a backfilled reading carries — one of the
three in ``ingestion.vintage.VINTAGE_LABELS`` — is ``ingestion.backfill``'s to write, and it
derives it the same way this module derives the adapter rather than reading it off one.
"""

from __future__ import annotations

from datetime import datetime
from typing import Callable

from ingestion.adapters import (ALFRED_HOST, AlfredVintageAdapter, CboeAdapter, FredAdapter,
                                YahooChartAdapter)
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
#: ``cdn-api.cboe.com`` AND ``query1.finance.yahoo.com`` ARE DELIBERATELY ABSENT, though
#: WO-1.16 backfills both. This dict is hosts reached ONLY by the backfill path, and neither
#: of them is one: the live collector already reaches both
#: (``ingestion.catalog.EGRESS_HOSTS``). Cboe is the same host at the same URL — the backfill
#: changes only which ROW of the returned body is read. Yahoo is the same host at a DIFFERENT
#: query string (``period1``/``period2`` in place of ``range``), which is not a different
#: destination: an allowlist entry names a HOST, and that one is already allowlisted for the
#: live collector that reads the same symbols every pass. Listing either here would claim a
#: backfill-only egress destination that does not exist and would owe a second allowlist
#: entry for a host already allowlisted.
BACKFILL_EGRESS_HOSTS: dict[str, str] = {
    ALFRED_HOST: "Federal Reserve Bank of St. Louis (ALFRED vintage graph CSV; keyless, "
                 "the same public door as fred.stlouisfed.org with a vintage_date parameter)",
}

#: The ingredient kinds a POINT-IN-TIME backfill has been reasoned about for, stated
#: positively so every other kind is refused rather than quietly handled. ``multpl``,
#: ``lbma``, the HERMES peer and ``manual`` are absent: a backfill of one of them would be
#: today's value wearing a past date, which is the forgery this whole WO exists to prevent —
#: so it is a refusal here, and whether those kinds can be backfilled at all is an open
#: question with an owner, not a default this module gets to pick.
#:
#: THREE KINDS, FOR THREE DIFFERENT REASONS, AND THE REASONS DO NOT GENERALISE (WO-1.16):
#:
#: * ``fred`` — ALFRED serves vintages of FRED series, and where it does not have to,
#:   ``ingestion.vintage``'s evidence MEASURED that revision does not matter. Either way the
#:   date asked for is answered on recorded authority.
#: * ``cboe`` — the opposite warrant. There is no vintage endpoint and no stability
#:   measurement; there is a single static body which the probe showed CANNOT be windowed
#:   (``evidence/wo116_cboe_probe.json``), out of which one dated row is read by key. What a
#:   reading from it may claim is narrower than either FRED branch, and the narrower claim
#:   has its own label: :data:`~ingestion.vintage.VINTAGE_NO_REVISION_MECHANISM`.
#: * ``yahoo`` — the same label as Cboe and NOT the same scope, which is the one thing about
#:   this tuple that a reader has to carry away. The chart endpoint has no vintage endpoint
#:   either and it DOES take an absolute window, so one named session is asked for directly
#:   (``evidence/wo116_yahoo_window_probe.json``) — but the claim holds for the PRINTED close
#:   only. ``adjclose`` is restated retroactively by every dividend and split for every date
#:   before the event, forever (PID.md WO-1.16 scope correction), which is a revision
#:   mechanism in all but name and the one this label would lie about.
#:
#: SO THIS TUPLE IS NOT THE WHOLE GATE FOR ``yahoo``, AND IT IS NOT MEANT TO BE. ``kind`` is
#: the wrong granularity for that source;
#: :data:`~ingestion.vintage.NO_REVISION_MECHANISM_COLUMNS` holds the column half, and both
#: halves are enforced on the paths that act on them: the
#: adapter refuses to be CONSTRUCTED for a dated ``adjclose`` read, and ``ingestion.backfill``
#: refuses to derive a LABEL for one. Widening this tuple to ``yahoo`` therefore admits the
#: seven plain-close rows and still refuses the 51 ``adjclose`` ones (the two indicators of
#: PID.md's scope correction); this module's docstring traces that end to end, because "the
#: kind is backfillable" and "every row of that kind is backfillable" are not the same
#: sentence and only the first is true here.
VINTAGE_BACKFILLABLE_KINDS = ("fred", "cboe", "yahoo")


def build_backfill_adapter(ing: Ingredient, observation_date: str, clock: Callable[[], datetime]):
    """The adapter that answers for ``ing`` at ``observation_date`` — point-in-time where it must.

    ON THE FRED BRANCH: :class:`~ingestion.adapters.AlfredVintageAdapter` when
    ``ingestion.vintage.requires_original_vintage`` says this pair needs the figure as first
    published; :class:`~ingestion.adapters.FredAdapter` when stability was POSITIVELY
    measured. ON THE CBOE AND YAHOO BRANCHES: :class:`~ingestion.adapters.CboeAdapter` and
    :class:`~ingestion.adapters.YahooChartAdapter` in their dated modes, with NO vintage
    question asked — see this module's docstring on why asking one there would be a confident
    wrong answer rather than an error. A kind outside :data:`VINTAGE_BACKFILLABLE_KINDS` is
    refused, and so is a ``yahoo`` ingredient asking for ``adjclose`` — by the adapter it
    would have to be built from, which is the same docstring's second section.

    ``observation_date`` reaches EVERY adapter, and on the three current-body branches it is
    what makes the read a dated one rather than a read of the latest value (WO-1.15,
    WO-1.16). It is passed by KEYWORD to all of them, because every one of them already has
    something else in the positional slots a date could land in: ``history`` (``FredAdapter``
    third, ``YahooChartAdapter`` second), ``column`` (``CboeAdapter`` second) and ``field``
    (``YahooChartAdapter`` third). A date must never be able to trade places with any of them.
    """
    if ing.kind not in VINTAGE_BACKFILLABLE_KINDS:
        raise ValueError(
            f"{ing.source_id} is kind {ing.kind!r}; a point-in-time backfill is declared only for "
            f"{VINTAGE_BACKFILLABLE_KINDS} (see ingestion.backfill_adapters.VINTAGE_BACKFILLABLE_KINDS)"
        )
    common = dict(source_id=ing.source_id, as_of_rule=ing.as_of_rule, unit=ing.unit, clock=clock)
    if ing.kind == "fred":
        if requires_original_vintage(ing.ref, ing.transformation):
            return AlfredVintageAdapter(ing.ref, ing.transformation, observation_date, **common)
        return FredAdapter(ing.ref, ing.transformation, ing.history,
                          observation_date=observation_date, **common)
    if ing.kind == "cboe":
        return CboeAdapter(ing.ref, ing.column, observation_date=observation_date, **common)
    if ing.kind == "yahoo":
        # The field is resolved EXACTLY as ``ingestion.catalog.build_adapter`` resolves it —
        # ``ing.column or "close"``, because the catalog leaves ``column`` empty for the
        # default and the seven plain rows all do. Resolving it any other way here would
        # backfill a different QUANTITY than the live collector stores under the same
        # ingredient, which is the WO-1.14 defect class by field instead of by date. For
        # ``adjclose`` the constructor itself raises, and this module's docstring says why no
        # check of our own precedes it. ``ing.history`` is passed for the same reason the
        # FRED branch passes it and with the same effect: a dated read is one bar, so there
        # is no history in it to carry (``parse_yahoo_chart_for_date``).
        return YahooChartAdapter(ing.ref, ing.history, field=ing.column or "close",
                                 observation_date=observation_date, **common)
    # Unreachable while the tuple above and the branches here agree, which is exactly why it
    # is here: a kind ADDED to VINTAGE_BACKFILLABLE_KINDS without a branch must announce
    # itself, not inherit FRED's routing by falling off the end of this function.
    raise ValueError(
        f"{ing.source_id} is kind {ing.kind!r}: declared backfillable but no branch in "
        f"ingestion.backfill_adapters.build_backfill_adapter constructs an adapter for it"
    )
