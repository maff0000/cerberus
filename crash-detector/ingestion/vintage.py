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
"""

from __future__ import annotations

from typing import Mapping, Union

__all__ = [
    "VINTAGE_ORIGINAL",
    "VINTAGE_CURRENT_ONLY",
    "VINTAGE_LABELS",
    "MATERIAL_THRESHOLD",
    "MIN_SHARED_OBSERVATIONS",
    "EVIDENCE_FILE",
    "EVIDENCE_PROBED_UTC",
    "REVISION_PRONE",
    "REVISION_STABLE",
    "REVISION_UNDETERMINED",
    "classify",
    "requires_original_vintage",
]

#: A reading whose value is the one the source FIRST published for that period — what was
#: knowable then. The only label a backfilled historical reading may carry.
VINTAGE_ORIGINAL = "original"
#: A reading carrying today's value for a past period, because no vintage of it is
#: available. Admissible only where revision was measured not to matter.
VINTAGE_CURRENT_ONLY = "current_only"
#: The closed vocabulary of the ``raw_reading.vintage`` column. ``ingestion.store`` builds
#: its CHECK constraint from this tuple so the SQL and the Python cannot drift apart.
VINTAGE_LABELS = (VINTAGE_ORIGINAL, VINTAGE_CURRENT_ONLY)

#: The relative difference the probe counted as material. Recorded here so the declaration
#: below is readable as a claim about a measurement and not a bare list.
MATERIAL_THRESHOLD = 0.005

#: The floor below which "no material differences" is absence of evidence, not stability.
MIN_SHARED_OBSERVATIONS = 250

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
    """
    return (series, transformation) not in REVISION_STABLE
