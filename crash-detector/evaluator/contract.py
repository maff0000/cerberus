"""THE OUTPUT CONTRACT: one ``machine_state_history`` row out as DECISION-RULE.md §7's document.

WO-1.3a round 7, built to ``governance/WO-1.3a-engine-spec.md`` §12 (the Product Owner's
two scope calls) and §13 (this round: the assembly function, a plain dict, no serving).

**THIS IS THE ONE THING EPIC 2 READS** (DECISION-RULE.md §7: "Epic 2 reads only this. It
never reads CERBERUS internals"), so the field NAMES here are the schema and not a choice
this module may make. :func:`contract_for_row` builds the dict and nothing serialises it:
YAML or JSON is the caller's, and a later round's HTTP door is not this one's.

====================================================================================
WHAT IS PUBLISHED AS A STATED ABSENCE, AND WHY EACH ONE IS NOT A ZERO
====================================================================================

Three fields of §7 are null in this build. Each carries a ``*_not_computed`` sibling
rather than a plausible number, because a consumer cannot tell a placeholder from a
measurement and §7's whole premise is that it does not have to:

* ``sizing_multiplier`` — spec §12, OUT OF SCOPE and explicitly NOT emitted as ``0.0``.
  §7 makes it non-zero only in CALM and RECOVERY and derives it from valuation inputs
  (CAPE, a Buffett-indicator substitute, gold extension) that no code in this product
  computes. A ``0.0`` in CALM would read as "the detector recommends sizing to zero",
  which is the OPPOSITE of the truth that the detector has not spoken about sizing at
  all. ``sizing_not_computed`` is therefore :data:`SIZING_NOT_COMPUTED` — ``True`` in
  EVERY state, including the states in which a real multiplier would be zero, so that
  "not computed" is never confused with "computed as zero". Real sizing is WO-1.3c.
* ``inputs`` — **NOT A SCOPE CUT BUT A GAP IN WHAT THE ROW CARRIES**, found here and
  reported rather than papered over. §7 wants one entry per wired indicator carrying
  ``id, state, age_seconds, score or null``. A :class:`~evaluator.history_store.MachineStateRow`
  carries ``master_scores`` (keyed by MASTER id — a master is a ``max`` over several
  indicators, spec §2, so those keys are not indicator ids and publishing them under
  ``inputs`` would mislabel them) and ``count_at_or_beyond`` (indicator ids, but only the
  at-or-beyond subset, with no score and no age). Nothing in the row or in its history
  carries a per-indicator score, state or age. So the honest contract publishes ``None``
  with :data:`INPUTS_NOT_COMPUTED` beside it, rather than an empty list — which would
  claim this dial has no wired indicators — or a partial entry shape, which would break
  the one schema Epic 2 reads verbatim. Filling it needs the reading's ``Contribution``
  tuple AND per-input ages from the observations, neither of which the store holds today;
  that is a column/signature question for the PO, not an invention for this round.
* ``coverage_bracket.dial_value_min`` / ``dial_value_max`` — built, see below, whenever
  the row is resolvable and a real ``scored_weight_fraction`` is supplied. They are
  ``None`` with ``coverage_not_computed: True`` when either is absent: on an UNKNOWN row
  there is no dial value to bracket, and with no fraction there is no missing weight to
  impute over.

====================================================================================
``dial_value_min`` / ``dial_value_max``: THE RE-SCORE, DONE IN CLOSED FORM
====================================================================================

§7 defines the bracket as the dial's statistic "if every missing input scored 0" and
"if every missing input scored 1". Spec §12 called that a genuinely new engine computation
and allowed it to be deferred. It did not have to be: it is the SAME re-score, written out.

With the banded weighted mean (``crash_detector.engine.mapping._banded_weighted_mean``)

    breadth = Σ_scored w·s / Σ_scored w,   f = Σ_scored w / Σ_nominal w

imputing every missing input at 0 adds nothing to the numerator and all of the missing
weight to the denominator, and imputing every one at 1 adds all of it to both:

    min = Σ_scored w·s / Σ_nominal w                      = breadth · f
    max = (Σ_scored w·s + Σ_missing w) / Σ_nominal w       = breadth · f + (1 − f)

Both are ALGEBRAIC IDENTITIES of the re-score and not an approximation of it — which is
why this needs no per-indicator detail, and why it is buildable here while ``inputs`` is
not. ``test_decision_contract.py`` proves the identity against a re-score performed the
long way, over a weight set in which it would fail if the derivation were wrong.

``f`` is the caller's to compute, from THIS reading's contributions, with
:func:`ingestion.wiring.scored_coverage` — the function that answers MATH.md R-10. The
``coverage`` figure the GUI shows today is a DIFFERENT number (which rows are wired) and
substituting it here would widen or narrow the bracket by exactly the error R-10 names.

====================================================================================
``as_of``: THE ROW'S INSTANT IS THE OLDEST INPUT'S, AND §7 SAYS "NEWEST". REPORTED.
====================================================================================

§7's comment reads "<UTC timestamp of the newest input used>". The instant the engine
actually dates a reading by is ``crash_detector.engine.evaluate._oldest_as_of`` — "the
reading is only as fresh as its oldest input" — and that is what the row carries and what
is published here, unchanged. The engine's choice is the conservative one and the one every
freshness decision in this product is already made against; changing it is not a contract
round's business, and quietly publishing the oldest instant under a field documented as the
newest would be worse than either. The discrepancy is raised with the PO as a §7 wording
question. Per-input ages, which §7 points at for the detail, are the ``inputs`` gap above.

Import route: ``PYTHONPATH=src:.`` from ``crash-detector/``.
"""

from __future__ import annotations

import hashlib
import math
import os
from datetime import datetime
from pathlib import Path
from typing import Union

from crash_detector.dials.dialset import DIAL_IDS
from crash_detector.engine.statistics import State
from crash_detector.time_utc import format_utc
from evaluator.history_store import MachineStateRow
from ingestion.wiring import MAPPING_YAML, SCALING_JSON

__all__ = [
    "SCHEMA_VERSION",
    "DECISION_RULE_VERSION",
    "SIZING_NOT_COMPUTED",
    "INPUTS_NOT_COMPUTED",
    "BUILD_SHA_ENV",
    "BUILD_SHA_UNKNOWN",
    "content_version",
    "live_identity",
    "contract_for_row",
]

#: ``schema_version``, verbatim from DECISION-RULE.md §7's own first line. It is the
#: document's string and not a version this module numbers: a change to the published shape
#: is an edit to §7 first, and this constant follows it.
SCHEMA_VERSION = "decision-rule/v1"

#: ``identity.decision_rule_version`` — "this file's version" in §7's words. DECISION-RULE.md
#: carries no separate version line (its header states "OWNER-CONFIRMED (Matt, 2026-10-13)"),
#: so the only version the document states of itself is the ``v1`` in its schema id, and that
#: is what is published. **The two ``not_computed`` disclosures above are part of what this
#: version means in this build:** a consumer reading ``decision-rule/v1`` from THIS detector
#: is reading a contract whose sizing and per-input detail are declared absent in band, which
#: is why those flags are always present rather than emitted only when they are interesting.
DECISION_RULE_VERSION = "v1"

#: ``sizing_not_computed``, and it is a CONSTANT because it is true in every state (spec §12).
#: It is not a function of the row and must not become one by accident: the moment it varies,
#: a consumer has to decide which states it may trust, and no state's sizing is computed.
SIZING_NOT_COMPUTED = True

#: ``inputs_not_computed``. Constant for the same reason and a DIFFERENT fact: sizing is
#: unbuilt, whereas the per-input detail exists in the engine and is not carried by the row
#: this contract is assembled from (module docstring). One flag each, so the two gaps are not
#: closed by one change that only addresses one of them.
INPUTS_NOT_COMPUTED = True

#: Where ``identity.build_sha`` comes from in the running container, and the value it reads
#: when the image was built without one — ``gui/server.py``'s line, reused rather than
#: re-decided, so both published surfaces name the same env var and the same fallback.
BUILD_SHA_ENV = "CD_BUILD_SHA"
BUILD_SHA_UNKNOWN = "unknown"


def content_version(path: Path) -> str:
    """The sha256 hexdigest of a config file's BYTES — this repo's content-addressing, reused.

    Spec §12 says to find the existing convention and not invent one. It is
    ``hashlib.sha256(<bytes>).hexdigest()``, full 64 hex and no prefix, in
    ``crash_detector.store.migrations`` (every migration's ``checksum_sha256``, the identity
    a re-written migration is caught by) and in ``tools/audit/tree_fingerprint`` (per-file
    digest). Bytes and not decoded text, as both of those do: a hash over text would make
    the version depend on this process's decoding, and the artefact being identified is a
    file somebody shipped.

    **NOT** ``IndicatorMapping.provenance.mapping_version``, which is the mapping YAML's
    DECLARED ``schema_version`` field and answers a different question — which shape the
    file claims, not which bytes it has. A declared version is editable without the content
    changing and vice versa, and §7 asks for a hash.
    """
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def live_identity(build_sha: Union[str, None] = None) -> dict:
    """The three identity values a RUNNING build has to go outside itself to learn.

    ``{build_sha, scaling_version, mapping_version}``, ready to splat into
    :func:`contract_for_row`, which supplies ``decision_rule_version`` itself because that
    one is a constant of the source and not of the deployment.

    This is the IMPURE half, deliberately separated: it reads the environment and two files
    off disk, so :func:`contract_for_row` stays a pure function of its arguments and a test
    can state a sha rather than arrange one. ``build_sha=None`` reads
    :data:`BUILD_SHA_ENV`; an explicit value wins, for a caller that already knows it.
    """
    return {
        "build_sha": os.environ.get(BUILD_SHA_ENV, BUILD_SHA_UNKNOWN)
        if build_sha is None
        else build_sha,
        "scaling_version": content_version(SCALING_JSON),
        "mapping_version": content_version(MAPPING_YAML),
    }


def _fraction(scored_weight_fraction: Union[float, None], resolvable: bool):
    """``scored_weight_fraction`` established as a real fraction, or refused.

    A coverage figure outside ``0..1`` is not a conservative or an optimistic reading of
    coverage, it is a defect in whatever computed it, and publishing it would put a
    ``dial_value_max`` below ``dial_value_min`` into the document Epic 2 trusts. ``0.0`` on
    a RESOLVABLE row is refused by the same argument: the row carries a breadth, a breadth
    is a weighted mean over inputs that were scored, and "nothing was scored" cannot be true
    of it.
    """
    if scored_weight_fraction is None:
        return None
    number = float(scored_weight_fraction)
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise ValueError(
            f"scored_weight_fraction must be a finite fraction in 0..1, got {number!r}"
        )
    if resolvable and number == 0.0:
        raise ValueError(
            "scored_weight_fraction is 0.0 on a row that carries a breadth. A breadth is "
            "the weighted mean of the inputs that WERE scored, so a zero scored weight "
            "disagrees with the reading it is supposed to describe."
        )
    return number


def contract_for_row(
    row: MachineStateRow,
    *,
    state_since: datetime,
    build_sha: str,
    scaling_version: str,
    mapping_version: str,
    scored_weight_fraction: Union[float, None] = None,
) -> dict:
    """ONE ROW AS DECISION-RULE.md §7'S DOCUMENT: a plain dict, nothing read, nothing written.

    ``row`` is one evaluation's conclusion for one dial, as
    :func:`evaluator.resolve.official_state_for_dial` built it and
    :meth:`evaluator.history_store.MachineStateHistoryStore.append` stored it. Everything
    published below is either carried by that row, supplied as an argument, or a constant of
    this module; NOTHING is recomputed from raw data, so the document says what the
    evaluation that produced the row concluded and not what a second evaluation would.

    ``state_since`` is the instant the dial's current state began, which the row does NOT
    carry and which is a property of the whole series:
    :meth:`~evaluator.history_store.MachineStateHistoryStore.state_since` answers it
    exactly, and its docstring says why a 20-row window cannot. It is REQUIRED and not
    defaulted — a dial whose history has no streak to measure (the very first row) is the
    caller's own ``row.as_of``, which the caller knows and this function would be guessing.

    ``scored_weight_fraction`` is THIS reading's scored weight over the dial's nominal
    weight, from :func:`ingestion.wiring.scored_coverage` (MATH.md R-10). ``None`` is
    admitted, and is the honest answer for a caller that does not hold the reading's
    contributions: the coverage block then publishes nulls with ``coverage_not_computed``,
    rather than the wired-weight figure R-10 names as wrong.

    The states differ in what they may carry, not in the shape of the document: every key is
    present in every state, and an UNKNOWN row's statistics are ``None`` (CD-RT-001 — the
    row carries no numbers because there are none, and the contract says so in the same
    place a resolvable row says a number). A consumer never has to probe for a key.
    """
    if type(row) is not MachineStateRow:
        raise TypeError(
            f"contract_for_row publishes a MachineStateRow, got {type(row).__name__}"
        )
    if row.dial_id not in DIAL_IDS:
        # Spec §12 fixes the enum at the two dials that exist. The store's CHECK says the
        # same thing, and a row that never went through the store would not have met it.
        raise ValueError(
            f"{row.dial_id!r} is not a dial this product declares. The dials are "
            f"{list(DIAL_IDS)}; §7's enum carries no GBP/USD split of the monetary dial."
        )

    resolvable = row.machine_state is not State.UNKNOWN
    fraction = _fraction(scored_weight_fraction, resolvable)
    # THE RE-SCORE, in the closed form the module docstring derives. Both arms need a dial
    # value AND a coverage fraction; with either absent there is no bracket, and the one
    # flag discloses both cases because in both of them the bracket was not computed.
    bracketed = resolvable and fraction is not None
    return {
        "schema_version": SCHEMA_VERSION,
        "dial": row.dial_id,
        "as_of": format_utc(row.as_of),
        # `State.name`, NOT `State.value`: the member values are namespaced `state.calm` so
        # that an engine state can never be confused with a PID §4 detail level (see the
        # enum's own comment), and §7's published vocabulary is the bare `CALM`/`UNKNOWN`.
        "state": row.machine_state.name,
        "state_since": format_utc(state_since),
        "persistence_counter": row.persistence_counter,
        "sizing_multiplier": None,
        "sizing_not_computed": SIZING_NOT_COMPUTED,
        "acute_rising": row.acute_rising,
        "statistics": {
            "breadth": row.breadth,
            "acute": row.acute,
            "count": row.indicator_count,
        },
        "coverage_bracket": {
            "scored_weight_fraction": fraction,
            "dial_value_min": row.breadth * fraction if bracketed else None,
            "dial_value_max": row.breadth * fraction + (1.0 - fraction)
            if bracketed
            else None,
            "coverage_not_computed": not bracketed,
        },
        "inputs": None,
        "inputs_not_computed": INPUTS_NOT_COMPUTED,
        "identity": {
            "build_sha": build_sha,
            "scaling_version": scaling_version,
            "mapping_version": mapping_version,
            "decision_rule_version": DECISION_RULE_VERSION,
        },
    }
