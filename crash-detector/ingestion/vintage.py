"""Which (series, transformation) pairs are REVISION-PRONE — and the vintage vocabulary.

WO-1.14. A historical backfill that fetches today's FRED series and stores it as though it
had been read at the time is not a backfill, it is a forgery: for a revised series the
number we would have seen in 2008 is not the number the series carries now. This module is
the declaration of WHICH series that actually matters for, derived from measurement rather
than from reputation.

THE EVIDENCE
    ``evidence/wo114_alfred_probe.json`` — ALFRED's keyless vintage endpoint, probed
    2026-10-13, all 23 FRED rows of :data:`ingestion.catalog.INGREDIENTS`, no errors. For
    each series the probe compares the FIRST available vintage against the CURRENT one over
    the observations the two share, and counts the ones that differ MATERIALLY: more than
    ``material_threshold`` (0.005) of the value. Those counts, and nothing else, decide the
    sets below. :func:`classify` is the derivation; the frozen sets are its output on that
    file, and ``tests/test_vintage_declaration.py`` re-derives them and fails if the file
    and the declaration ever disagree.

THE RULE, stated once
    * The window judged is the REPLAY window (``replay_window``, the 1999-01-01-onwards span
      the detector actually replays) when that window is itself populated — at least
      :data:`MIN_SHARED_OBSERVATIONS` shared observations. Otherwise the full shared window
      is judged instead. Judging a series on history the engine never replays either
      condemns it for a rounding convention retired decades ago or acquits it on four points.
    * One material difference in the judged window is enough: REVISION-PRONE. Revision is a
      property of a publisher's process, and a process that revised once revises again.
    * Zero material differences over at least :data:`MIN_SHARED_OBSERVATIONS` shared
      observations: REVISION-STABLE. The floor is what separates "measured as stable" from
      "not measured". 250 is about a year of business-daily prints or twenty years of
      monthly ones, and it is comfortably below the 694 of the thinnest series that clears
      it (DFII10) and comfortably above the 1 of the two that do not.
    * Zero material differences over a window too thin to support the claim: UNDETERMINED.
      Not "stable". :func:`requires_original_vintage` therefore answers from
      :data:`REVISION_STABLE` and not from :data:`REVISION_PRONE`: the backfill may skip
      point-in-time fetching only where stability was POSITIVELY measured, so a series added
      to the catalog tomorrow and never probed is fetched vintage-by-vintage rather than
      silently trusted.

DFF IS THE ONE JUDGEMENT CALL, AND IT IS MADE BY THE RULE
    Over its full 18,624 shared observations the daily fed funds rate shows 93 material
    differences (0.5%). Every one of them is pre-1999 and the largest is 0.005 — the
    three-decimal rounding of 1969 prints, sitting exactly on the materiality threshold.
    Over the replay window DFF differs in ZERO of 2,369 shared observations, not merely zero
    materially. So DFF is REVISION-STABLE *for the window this detector replays*, and the
    rule above says so without DFF being named. If ``compare_from`` is ever moved back
    before 1999, re-probe: the test will then fail here, which is the point of deriving the
    sets instead of typing them.

THE VOCABULARY IS NOW WIDER THAN THIS MODULE'S MEASUREMENTS, AND THAT IS DELIBERATE (WO-1.16)
    Everything above is about FRED, because a revision axis is what everything above
    measures. :data:`VINTAGE_NO_REVISION_MECHANISM` is the label for a source that HAS NO
    SUCH AXIS — Cboe's static index history is the first one backfilled — and it is in this
    module rather than next to the adapter for one reason: the vocabulary of
    ``raw_reading.vintage`` is closed and is declared in exactly one place
    (:data:`VINTAGE_LABELS`, from which ``ingestion.store`` builds its CHECK), so a third
    label declared anywhere else would be a second vocabulary.

    Read the three labels as three different WARRANTS for one stored number, not as three
    degrees of the same one:

    * :data:`VINTAGE_ORIGINAL` — a vintage was READ. The warrant is the server's own
      vintage-dated answer, carried on the row.
    * :data:`VINTAGE_CURRENT_ONLY` — today's body, on the authority of a MEASUREMENT
      (:data:`REVISION_STABLE` plus :data:`STABILITY_MEASURED_FROM`) that revision does not
      matter over the window asked for.
    * :data:`VINTAGE_NO_REVISION_MECHANISM` — today's body, because the source publishes no
      other body and exposes no way to ask for one. There is no vintage to read and nothing
      for a stability measurement to be measured against.

    The third is weaker than the first and is NOT the second: see its own comment for why
    neither existing label could carry a Cboe reading honestly.
"""

from __future__ import annotations

from typing import Mapping, Union

__all__ = [
    "VINTAGE_ORIGINAL",
    "VINTAGE_CURRENT_ONLY",
    "VINTAGE_NO_REVISION_MECHANISM",
    "VINTAGE_LABELS",
    "MATERIAL_THRESHOLD",
    "MIN_SHARED_OBSERVATIONS",
    "STABILITY_MEASURED_FROM",
    "EVIDENCE_FILE",
    "EVIDENCE_PROBED_UTC",
    "NO_REVISION_MECHANISM_KINDS",
    "NO_REVISION_MECHANISM_EVIDENCE",
    "REVISION_PRONE",
    "REVISION_STABLE",
    "REVISION_UNDETERMINED",
    "classify",
    "requires_original_vintage",
    "has_no_revision_mechanism",
]

#: A reading whose value is the one the source FIRST published for that period — what was
#: knowable then. Earned by READING A VINTAGE: in this tree, only
#: ``ingestion.adapters.AlfredVintageAdapter`` produces one, and the reading carries the
#: vintage date the server itself named.
#:
#: CORRECTION, recorded rather than edited away (PBG-CONT-003). This comment also said:
#:
#:     *"The only label a backfilled historical reading may carry."*
#:
#: WO-1.14's driver round measured that false, and the two sentences cannot both stand. A
#: backfill of a MEASURED-STABLE pair does not read a vintage at all — it reads today's body,
#: on the authority of :data:`REVISION_STABLE` — so what it stores is by definition
#: :data:`VINTAGE_CURRENT_ONLY`, which is that label's own stated meaning word for word. The
#: superseded sentence would have had a DFF reading from today's body claim to be the figure
#: first published, which is the one claim this module exists to stop.
VINTAGE_ORIGINAL = "original"
#: A reading carrying today's value for a past period, because no vintage of it is
#: available. Admissible only where revision was measured not to matter — which means
#: :data:`REVISION_STABLE` for the pair AND an observation date at or after
#: :data:`STABILITY_MEASURED_FROM`, the date the measurement itself begins at. Both halves,
#: because "measured not to matter" is a claim about a window and not about a series.
VINTAGE_CURRENT_ONLY = "current_only"
#: A reading taken from today's body of a source that HAS NO REVISION MECHANISM AT ALL: it
#: publishes one body, serves no vintages of it, and accepts no parameter that would ask for
#: a different one. So there is nothing for a vintage search to recover, and nothing for a
#: stability measurement to be measured against.
#:
#: READ WHAT IT CLAIMS, AND WHAT IT POINTEDLY DOES NOT. It claims the source exposes no
#: revision axis — a property of the ENDPOINT, established by probing it. It does NOT claim
#: the number equals what printed on the day: that would need a contemporaneous record this
#: label's own premise says does not exist. A consumer that needs "the figure as first
#: published, verified" must read :data:`VINTAGE_ORIGINAL` and nothing else.
#:
#: WHY NEITHER EXISTING LABEL COULD CARRY A CBOE READING (WO-1.16, and the argument is the
#: deliverable here, not the constant). The probe is
#: ``evidence/wo116_cboe_probe.json``, 2026-10-15: every plausible windowing parameter —
#: ``dt``, ``date``, ``startDate``/``endDate``, ``start``/``end``, ``from``/``to``,
#: ``start_date``/``end_date``, plus two negative controls (FRED's own ``cosd``/``coed``
#: names and a nonsense parameter) — returned a body BYTE-IDENTICAL to the bare URL's, same
#: SHA-256, all 9,294 rows, 1990-01-02 to 2026-10-14. There is no vintage endpoint, no
#: window, no ``as of``; there is one file.
#:
#: * NOT :data:`VINTAGE_ORIGINAL`. That label is MECHANISM-EARNED and says so: "earned by
#:   READING A VINTAGE... only ``AlfredVintageAdapter`` produces one, and the reading carries
#:   the vintage date the server itself named". A Cboe reading carries no vintage date,
#:   because no server named one. The tempting argument — a daily index close is final the
#:   moment it prints, so the figure in today's body IS the figure first published — is an
#:   argument from REPUTATION about a publisher's process, and the first line of this
#:   module's docstring is that this declaration is "derived from measurement rather than
#:   from reputation". Worse, it is unfalsifiable here: if Cboe ever did silently restate a
#:   close, a row labelled ``original`` would be a false claim with nothing in the system
#:   able to detect it, whereas THIS label stays exactly true either way. And the precedent
#:   is already recorded above: a sentence about ``original`` was found false by measurement
#:   and was superseded rather than edited away. Quietly widening the same label by
#:   reinterpretation, a round later, is the drift that correction exists to warn against.
#: * NOT :data:`VINTAGE_CURRENT_ONLY`. Its stated admissibility is :data:`REVISION_STABLE`
#:   membership AND an observation date at or after :data:`STABILITY_MEASURED_FROM` — two
#:   halves of one FRED measurement, neither of which exists for Cboe. Using it would smuggle
#:   in a claim that stability was MEASURED when nothing was measured, which is the same
#:   species of overclaim as the first option, pointing the other way.
#:
#: So: a third label, because this is a third epistemic situation and the honest thing to do
#: with one is name it. The cost is a widened CHECK constraint, paid once; the alternative
#: cost is a vocabulary whose words no longer mean what they say.
VINTAGE_NO_REVISION_MECHANISM = "no_revision_mechanism"
#: The closed vocabulary of the ``raw_reading.vintage`` column. ``ingestion.store`` builds
#: its CHECK constraint from this tuple so the SQL and the Python cannot drift apart.
VINTAGE_LABELS = (VINTAGE_ORIGINAL, VINTAGE_CURRENT_ONLY, VINTAGE_NO_REVISION_MECHANISM)

#: The relative difference the probe counted as material. Recorded here so the declaration
#: below is readable as a claim about a measurement and not a bare list.
MATERIAL_THRESHOLD = 0.005

#: The floor below which "no material differences" is absence of evidence, not stability.
MIN_SHARED_OBSERVATIONS = 250

#: The DATE THE STABILITY CLAIM BEGINS AT, and therefore the date before which
#: :data:`REVISION_STABLE` says nothing at all. It is the probe's own ``compare_from`` — the
#: left edge of the replay window every ``replay_window`` figure in :data:`EVIDENCE_FILE`
#: was measured over — and ``tests/test_vintage_declaration.py`` asserts the two agree, the
#: same way it asserts :data:`MATERIAL_THRESHOLD` against the file's ``material_threshold``.
#:
#: WHY A BACKFILL NEEDS IT AND THE ROUTING DID NOT. ``requires_original_vintage`` answers for
#: a PAIR, which is the whole question when the asker is "shall I search vintages at all".
#: The backfill driver asks a narrower one — "may I store TODAY's body as the figure for
#: observation D" — and the measured answer is yes only for a D the measurement covered. DFF
#: is the case that makes this concrete rather than theoretical: it is REVISION-STABLE here
#: because it differs in ZERO of 2,369 shared observations from 1999 onward, and over its
#: FULL 18,624 shared observations it differs materially in 93, every one of them pre-1999.
#: So a 1985 DFF reading taken from today's body is NOT the figure first published, and
#: labelling it as though it were would be the forgery this module exists to prevent.
#: ``ingestion.backfill`` refuses such a date rather than storing it; see that module.
STABILITY_MEASURED_FROM = "1999-01-01"

EVIDENCE_FILE = "evidence/wo114_alfred_probe.json"
EVIDENCE_PROBED_UTC = "2026-10-13"

#: (series, transformation) pairs the evidence shows ARE revised: 15 of 23.
REVISION_PRONE = frozenset({
    ("BACTSAMFRBDAL", None),
    ("CPIAUCSL", "pc1"),
    ("CPILFESL", None),
    ("DRTSCILM", None),
    ("DTWEXBGS", None),
    ("GACDFSA066MSFRBPHI", None),
    ("GACDISA066MSFRBNY", None),
    ("GDP", None),
    ("IC4WSA", None),
    ("M2SL", "pc1"),
    ("NCBEILQ027S", None),
    ("NFCI", None),
    ("PCEPILFE", "pc1"),
    ("UMCSENT", None),
    ("WALCL", None),
})

#: Pairs MEASURED stable over a window large enough to mean it: 6 of 23.
REVISION_STABLE = frozenset({
    ("DFF", None),
    ("DFII10", None),
    ("SAHMREALTIME", None),
    ("T10Y2Y", None),
    ("T10Y3M", None),
    ("T5YIE", None),
})

#: Pairs whose first ALFRED vintage is too recent to compare against: 2 of 23. Both ICE BofA
#: OAS series, whose vintage trail begins 2023-10-16 with a single observation. No material
#: difference was found and none could have been. Treated as revision-prone by
#: :func:`requires_original_vintage`.
REVISION_UNDETERMINED = frozenset({
    ("BAMLC0A0CM", None),
    ("BAMLH0A0HYM2", None),
})


#: Ingredient KINDS whose source was PROBED and found to expose no revision mechanism — the
#: only kinds :data:`VINTAGE_NO_REVISION_MECHANISM` may be written for. Stated positively and
#: answered fail-safe by :func:`has_no_revision_mechanism`, for the same reason
#: :func:`requires_original_vintage` answers from :data:`REVISION_STABLE`: "nobody has
#: probed this source" must never read as "this source has no revisions".
#:
#: ``cboe`` only, and only because ``cdn-api.cboe.com``'s ``{index}_History.csv`` was asked.
#: ``yahoo`` is deliberately absent even though it has no vintage endpoint either: its
#: ``adjclose`` DRIFTS retroactively with every dividend and split (PID.md, WO-1.16 scope
#: correction), which is a revision mechanism in everything but name, and the honest label
#: for it is a question this declaration does not get to pre-answer.
NO_REVISION_MECHANISM_KINDS = frozenset({"cboe"})

#: Where the claim above was measured, per kind. Named here so the declaration is readable
#: as a probe result rather than as a belief, exactly as :data:`EVIDENCE_FILE` is for FRED.
NO_REVISION_MECHANISM_EVIDENCE = {"cboe": "evidence/wo116_cboe_probe.json"}


def classify(probe: Mapping) -> dict:
    """The derivation. ``probe`` is the parsed probe JSON; returns the three sets.

    Pure, and the only place the rule in this module's docstring exists as code. The frozen
    sets above are this function's output on :data:`EVIDENCE_FILE`.
    """
    prone, stable, undetermined = set(), set(), set()
    for entry in probe["series"]:
        pair = (entry["series"], entry["transformation"])
        revision = entry["revision"]
        window = revision["replay_window"]
        if window["shared_observations"] < MIN_SHARED_OBSERVATIONS:
            window = revision  # the replay window is unpopulated; judge the whole overlap
        if window["differing_materially"] > 0:
            prone.add(pair)
        elif window["shared_observations"] >= MIN_SHARED_OBSERVATIONS:
            stable.add(pair)
        else:
            undetermined.add(pair)
    return {
        "prone": frozenset(prone),
        "stable": frozenset(stable),
        "undetermined": frozenset(undetermined),
    }


def requires_original_vintage(series: str, transformation: Union[str, None] = None) -> bool:
    """Must this pair be backfilled from original vintages? Fail-safe: default YES.

    Answered from :data:`REVISION_STABLE` rather than :data:`REVISION_PRONE` so that an
    unprobed series is fetched point-in-time instead of being quietly assumed unrevised.

    IT IS A QUESTION ABOUT A FRED PAIR AND ONLY ABOUT ONE. For a kind with no revision axis
    (:func:`has_no_revision_mechanism`) there is no vintage adapter to route to and no
    stability measurement to appeal to, so the question does not arise rather than defaulting
    to ``True`` — ``ingestion.backfill_adapters`` asks it only on the FRED branch.
    """
    return (series, transformation) not in REVISION_STABLE


def has_no_revision_mechanism(kind: str) -> bool:
    """Was this ingredient KIND probed and found to expose no revision mechanism at all?

    The gate on :data:`VINTAGE_NO_REVISION_MECHANISM`. Fail-safe in the direction that costs
    nothing: an unknown kind answers ``False``, so it cannot acquire the label by being
    forgotten — it is refused by ``ingestion.backfill_adapters.VINTAGE_BACKFILLABLE_KINDS``
    instead, which is where a kind nobody has reasoned about belongs.
    """
    return kind in NO_REVISION_MECHANISM_KINDS
