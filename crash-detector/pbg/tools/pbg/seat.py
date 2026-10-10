"""Seat occupation as a state machine, not a yes/no (Placement Question B, the ordering defect).

WHAT WAS MEASURED. On the real record, with the seat unoccupied:

    required_executor_attestation at top level   -> FAIL. validate_document errors, so the record
                                                    CANNOT BE WRITTEN.
    the same demand nested one level down        -> NOT_VERIFIED. No error, so it can.

"The nesting that makes the record creatable is exactly the placement that makes it unread." Both
halves are wrong, and they are wrong in opposite directions, which is why fixing either one alone
makes the other worse. Placement is repaired in `placement.py`. This module repairs the ordering.

FAIL-CLOSED IS RIGHT FOR A QUESTION THAT CAN BE ANSWERED. "Has the executor attested?" cannot be
answered at the moment the authority is created: the seat cannot be occupied before the authority
that defines it exists, so at write time the demand is unanswerable BY CONSTRUCTION. Returning FAIL
there conflates NOT-YET with NO, and the framework already owns the right vocabulary.

So the seat has a lifecycle, and each state is decided by evidence rather than by assumption:

    AUTHORITY_CREATED_AWAITING_ATTESTATION   lawful. The record exists; the seat has done nothing.
    VALID_ATTESTATION_COMMITTED              an attestation exists and is coherent with the record.
    SEAT_OCCUPIED_AND_VERIFIED               and it was committed BEFORE the seat acted.

    ATTESTATION_CONFLICT                     two readable attestations disagree. Fail closed.
    ATTESTATION_INCOHERENT                   an attestation exists and contradicts its own record.
    SEAT_ACTED_WITHOUT_ATTESTATION           work exists under this authority and no attestation
                                             precedes it. This is the failure the demand always
                                             meant, and it is now MACHINE-ENFORCED.
    NOT_DETERMINABLE                         no committed history to read yet — a record being
                                             written, or a project without Git. Never a pass, and
                                             never an obstacle to lawful creation.

    DELIVERY_OR_VERDICT_COMMITTED            the seat attested, acted, and committed the artefact
                                             that CONCLUDES its work. Terminal.

WHAT MAKES IT ENFORCEMENT RATHER THAN A COMMENT. The transition from AWAITING to acted is observed
from Git: the commits between the authority's own introducing commit and its closure are classified
against THIS seat, and a commit containing any category in `ACTING_CATEGORIES` is the seat ACTING.
An unattested seat that has acted is an error on the record, not a note in a docstring.

The classification is per-seat rather than per-prefix, and that is the A2-R2 repair — see
`GOVERNANCE_PREFIXES` and `classify_path` for why a prefix rule made this control unable to fire for
an Assurance seat at all.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

AWAITING_ATTESTATION = "AUTHORITY_CREATED_AWAITING_ATTESTATION"
ATTESTATION_COMMITTED = "VALID_ATTESTATION_COMMITTED"
OCCUPIED_AND_VERIFIED = "SEAT_OCCUPIED_AND_VERIFIED"
ATTESTATION_CONFLICT = "ATTESTATION_CONFLICT"
ATTESTATION_INCOHERENT = "ATTESTATION_INCOHERENT"
ACTED_WITHOUT_ATTESTATION = "SEAT_ACTED_WITHOUT_ATTESTATION"
NOT_DETERMINABLE = "NOT_DETERMINABLE"

DELIVERY_OR_VERDICT_COMMITTED = "DELIVERY_OR_VERDICT_COMMITTED"

#: Path prefixes whose modification is RECORDING, not the work a seat performs.
#:
#: independent Assurance finding A2-R2. This was `("governance/", "evidence/")`, and a commit counted as ACTING only if it
#: touched something OUTSIDE those prefixes. An ASSURANCE seat's entire lawful work product IS
#: `evidence/` — a verdict, its probes, its transcripts — so no commit an auditor could lawfully make
#: ever counted. `SEAT_ACTED_WITHOUT_ATTESTATION` could not fire for an auditor and
#: `SEAT_OCCUPIED_AND_VERIFIED` was unreachable for one, which is why AUTH-0015 reported "nothing has
#: been done under it yet" after a complete committed audit that defeated a blocking control.
#:
#: The naive repair — classify all of `evidence/` as acting — trades a blind spot for a false
#: positive: reading another seat's evidence, or a prior seat's immutable evidence being carried in a
#: commit, would then look like this seat working. So `evidence/` is no longer classified by PREFIX
#: at all. It is classified by WHOSE it is, which requires knowing whose seat is being judged —
#: see `SeatContext` and `classify_path`.
GOVERNANCE_PREFIXES = ("governance/",)

#: States in which a seat may lawfully exist without a committed attestation.
PRE_ATTESTATION_STATES = frozenset({AWAITING_ATTESTATION, NOT_DETERMINABLE})

#: How one changed path relates to the seat being judged.
GOVERNANCE_RECORD = "GOVERNANCE_RECORD"
SEAT_START_EVIDENCE = "SEAT_START_EVIDENCE"
OWN_SEAT_EVIDENCE = "OWN_SEAT_EVIDENCE"
DELIVERY_OR_VERDICT_EVIDENCE = "DELIVERY_OR_VERDICT_EVIDENCE"
OTHER_SEAT_EVIDENCE = "OTHER_SEAT_EVIDENCE"
IMPLEMENTATION = "IMPLEMENTATION"

#: Categories that constitute a seat DOING something under its authority. Seat-start is excluded on
#: purpose: attesting OCCUPIES a seat, it does not act under it, and conflating the two would make
#: every seat "act" at the exact moment it became lawful to act.
ACTING_CATEGORIES = frozenset({OWN_SEAT_EVIDENCE, DELIVERY_OR_VERDICT_EVIDENCE, IMPLEMENTATION})

#: Filename markers for the artefacts that CONCLUDE a seat's work.
DELIVERY_MARKERS = ("seat-delivery-attestation", "verdict-", "VERDICT-")


@dataclass(frozen=True)
class SeatContext:
    """Whose seat is being judged, so a changed path can be attributed to it or not.

    Derived from the AUTHORITY RECORD — the role it assigns and the work item it names — never from
    the artefacts being classified. The same doctrine independent Assurance finding A1-R1 forced on evidence trust: the
    boundary comes from trusted context, not from the thing being measured.
    """
    area: str | None
    work_item: str | None
    attestation_path: str | None = None

    @property
    def own_prefix(self) -> str | None:
        if not self.area or not self.work_item:
            return None
        return f"evidence/{self.area}/{self.work_item}/"


def classify_path(path: str, context: SeatContext) -> str:
    """What a single changed path means FOR THIS SEAT."""
    if path.startswith(GOVERNANCE_PREFIXES):
        return GOVERNANCE_RECORD
    if not path.startswith("evidence/"):
        return IMPLEMENTATION
    if context.attestation_path and path == context.attestation_path:
        return SEAT_START_EVIDENCE
    own = context.own_prefix
    if own is None:
        # The seat cannot be located, so no evidence path can be attributed to it. Fail closed by
        # attributing nothing rather than by attributing everything.
        return OTHER_SEAT_EVIDENCE
    if not path.startswith(own):
        return OTHER_SEAT_EVIDENCE
    name = path.rsplit("/", 1)[-1]
    if any(marker in name for marker in DELIVERY_MARKERS):
        return DELIVERY_OR_VERDICT_EVIDENCE
    if "seat-start-attestation" in name:
        return SEAT_START_EVIDENCE
    return OWN_SEAT_EVIDENCE


@dataclass
class SeatLifecycle:
    state: str
    detail: str
    executor: str | None = None
    attestation_path: str | None = None
    acting_commits: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def verified(self) -> bool:
        return self.state == OCCUPIED_AND_VERIFIED

    @property
    def lawfully_unoccupied(self) -> bool:
        return self.state in PRE_ATTESTATION_STATES

    def render(self) -> str:
        lines = [f"SEAT LIFECYCLE: {self.state}", f"  {self.detail}"]
        if self.executor:
            lines.append(f"  executor    {self.executor}")
        if self.attestation_path:
            lines.append(f"  attestation {self.attestation_path}")
        for commit in self.acting_commits[:5]:
            lines.append(f"  acted at    {commit[:12]}")
        lines += [f"  - {f}" for f in self.findings]
        lines += [f"  ! {e}" for e in self.errors]
        return "\n".join(lines)


def _closing_commit(root: Path, rel_path: str) -> str | None:
    """The last commit that touched this record — for a CLOSED record, its closure."""
    from .authority import _git

    code, out = _git(root, "log", "-1", "--format=%H", "--", rel_path)
    return out.strip() or None if code == 0 else None


def _acting_commits(root: Path, authority_commit: str, until: str = "HEAD",
                    context: SeatContext | None = None) -> list[str]:
    """Commits under the authority that DID something rather than merely recorded something.

    Bounded at BOTH ends. An authority authorises work between its own commit and its closure; work
    done after a seat closed belongs to whatever seat was open then, and attributing it backwards
    would manufacture a violation out of ordinary succession.
    """
    return [sha for sha, categories in _classified_commits(root, authority_commit, until, context)
            if categories & ACTING_CATEGORIES]


def _classified_commits(root: Path, authority_commit: str, until: str = "HEAD",
                        context: SeatContext | None = None) -> list[tuple[str, set]]:
    """Each commit in the authority's window, with what its paths mean for THIS seat."""
    from .authority import _git

    context = context or SeatContext(None, None)
    code, out = _git(root, "rev-list", "--reverse", f"{authority_commit}..{until}")
    if code != 0:
        return []
    classified: list[tuple[str, set]] = []
    for sha in out.split():
        code, files = _git(root, "show", "--name-only", "--format=", sha)
        if code != 0:
            continue
        paths = [line.strip() for line in files.splitlines() if line.strip()]
        classified.append((sha, {classify_path(p, context) for p in paths}))
    return classified


def _coherence(doc: dict, attestation: dict, path: str) -> list[str]:
    """Ways an attestation can exist and still not attest to THIS seat."""
    problems = []
    for field_name in ("seat_id", "assigned_role", "work_item"):
        declared = str(doc.get(field_name) or "").strip()
        attested = str(attestation.get(field_name) or "").strip()
        if declared and attested and declared != attested:
            problems.append(
                f"{path} states {field_name}={attested!r} while the authority states "
                f"{declared!r}; an attestation that names another seat attests to another seat")
    if str(doc.get("assigned_role") or "") == "ENGINEER" and \
            attestation.get("holds_assurance_authority") is True:
        problems.append(
            f"{path} claims Assurance authority while occupying an ENGINEER seat; an executor that "
            "could assure its own work has no separation to attest to")
    if attestation.get("authority_inferred_from_instruction_file") is True:
        problems.append(
            f"{path} records that authority was inferred from an instruction file. An instruction "
            "file grants nothing (PBG-BOOT-001), so the seat is not lawfully occupied")
    return problems


def _excluded_because(reason: str) -> str:
    """A plain-English clause for why an attestation for this authority could not be used.

    The rendered finding already carries the exact gate, field and detail. This adds the sentence a
    reader wants first — WHAT KIND of thing is wrong — so a lifecycle error is intelligible without
    decoding a finding code.
    """
    if "SEAT_MISMATCH" in reason or "GRANTS_NO_SEAT" in reason:
        return "names another seat than the authority grants"
    if "WORK_ITEM" in reason:
        return "names another work item than the authority governs"
    if "ROLE" in reason:
        return "names another role than the authority assigns"
    if "AUTHORITY_NOT_FOUND" in reason or "AUTHORITY_NOT_DECLARED" in reason:
        return "names an authority that cannot be resolved"
    if "PRECEDES_AUTHORITY" in reason:
        return "was attested before the authority existed"
    if "PROVENANCE" in reason:
        return "carries provenance that does not support what it claims"
    return "fails a trust gate for this authority"


def lifecycle(root: Path, doc: dict, rel_path: str | None = None) -> SeatLifecycle:
    """Where this seat is in its lifecycle, decided from committed evidence.

    Never raises, never guesses, and never reports a state more advanced than the evidence supports.
    """
    from . import authority as auth
    from . import executors, placement

    root = Path(root)
    authority_id = doc.get("authority_id")
    demanded, findings = placement.resolve_field(doc, "required_executor_attestation")

    lookup = executors.attested_executor(root, authority_id)
    if lookup.conflicted:
        return SeatLifecycle(
            ATTESTATION_CONFLICT,
            f"seat-start evidence for {authority_id} conflicts, so who occupies this seat cannot "
            "be established: " + lookup.resolution.detail,
            findings=findings + lookup.resolution.findings,
            errors=[f"seat occupation is unestablished: {lookup.resolution.detail}"])

    attestation_source = lookup.resolution.selected
    attestation_path = attestation_source.rel_path if attestation_source else None
    findings += lookup.resolution.excluded

    if attestation_source is not None:
        problems = _coherence(doc, attestation_source.doc, attestation_path)
        if problems:
            return SeatLifecycle(ATTESTATION_INCOHERENT,
                                 "an attestation exists for this authority and contradicts it",
                                 executor=lookup.fact.executor_id if lookup.fact else None,
                                 attestation_path=attestation_path,
                                 findings=findings, errors=problems)

    # "WE DID NOT LOOK" MUST NEVER READ AS "NOT YET".
    #
    # Independent Assurance finding U3-1 added an AUTHORITY stage, and it does its job so early that
    # an attestation naming ANOTHER seat under this authority is now EXCLUDED before it can be
    # selected. Without this branch the seat would then report AWAITING_ATTESTATION — the lawful
    # pre-attestation state — while an incoherent attestation for it demonstrably exists on disk.
    # That is exactly the substitution this lifecycle model was built to prevent, arriving from the
    # opposite direction, and it is strictly worse than the diagnosis it replaced.
    #
    # `attested_executor` partitions on attestation_type == SEAT_START AND authority_id == this
    # authority, so every artefact in this exclusion list ALREADY names this authority. An exclusion
    # here therefore means "an attestation for this seat exists and cannot be used", which is
    # INCOHERENT, never ABSENT.
    if attestation_source is None and lookup.resolution.excluded:
        return SeatLifecycle(
            ATTESTATION_INCOHERENT,
            f"one or more seat-start attestations name {authority_id} and none of them can be used",
            findings=findings,
            errors=[f"an attestation naming {authority_id} was excluded and cannot establish this "
                    f"seat — it {_excluded_because(reason)}: {reason}"
                    for reason in lookup.resolution.excluded])

    authority_commit = auth.introducing_commit(root, rel_path) if rel_path else None
    if not authority_commit:
        state = NOT_DETERMINABLE if attestation_source is None else ATTESTATION_COMMITTED
        return SeatLifecycle(
            state,
            "this authority record is not yet in committed history, so what has been done under it "
            "cannot be read. Lawful: an authority may exist before its executor attests, and a "
            "record being written has authorised nothing yet",
            executor=lookup.fact.executor_id if lookup.fact else None,
            attestation_path=attestation_path, findings=findings)

    # A CLOSED authority authorises nothing after its closure, so the window ends there.
    active = str(doc.get("status") or "").upper() == "ACTIVE"
    until = "HEAD" if active else (_closing_commit(root, rel_path) or "HEAD")

    # independent Assurance finding A2-R2. Who this seat IS, taken from the authority record, so a changed evidence path can
    # be attributed to it or explicitly not attributed to it.
    from .evidence_resolution import ROLE_EVIDENCE_AREAS
    context = SeatContext(
        area=ROLE_EVIDENCE_AREAS.get(str(doc.get("assigned_role") or "").strip()),
        work_item=str(doc.get("work_item") or "").strip() or None,
        attestation_path=attestation_path)
    classified = _classified_commits(root, authority_commit, until, context)
    acting = [sha for sha, cats in classified if cats & ACTING_CATEGORIES]
    concluded = [sha for sha, cats in classified if DELIVERY_OR_VERDICT_EVIDENCE in cats]

    if attestation_source is None:
        if acting:
            unattested = (
                f"seat-start attestation is REQUIRED before any action under {authority_id} and "
                f"none exists, yet {acting[0][:12]} already acted under it. A seat occupied without "
                "an attestation is not lawfully occupied and its candidate supersedes nothing")
            observation = (
                f"no seat-start attestation exists for {authority_id}, and {acting[0][:12]} acted "
                "under it; who occupied that seat cannot be established from record. This record "
                "demands no attestation, so it is reported as an unestablished fact rather than as "
                "a breach of a rule it never carried")
            return SeatLifecycle(
                ACTED_WITHOUT_ATTESTATION,
                f"{len(acting)} commit(s) under this authority changed something other than "
                "governance and evidence, and no seat-start attestation precedes them",
                acting_commits=acting,
                findings=findings if demanded else findings + [observation],
                errors=[unattested] if demanded else [])
        return SeatLifecycle(
            AWAITING_ATTESTATION,
            f"{authority_id} exists and nothing has been done under it yet. The seat is NOT "
            "occupied and NOT independently verified; this is the lawful pre-attestation state, "
            "not a pass",
            findings=findings)

    attestation_commit = auth.introducing_commit(root, attestation_path)
    executor = lookup.fact.executor_id if lookup.fact else None

    if attestation_commit and not auth.is_ancestor(root, authority_commit, attestation_commit) \
            and attestation_commit != authority_commit:
        return SeatLifecycle(
            ATTESTATION_INCOHERENT,
            "the seat attested before the authority that defines the seat existed",
            executor=executor, attestation_path=attestation_path, findings=findings,
            errors=[f"attestation {attestation_path} was committed at {attestation_commit[:12]}, "
                    f"which does not descend from the authority commit {authority_commit[:12]}; an "
                    "executor cannot attest to a seat that does not yet exist"])

    premature = [sha for sha in acting
                 if attestation_commit and sha != attestation_commit
                 and not auth.is_ancestor(root, attestation_commit, sha)]
    if premature:
        return SeatLifecycle(
            ACTED_WITHOUT_ATTESTATION,
            "work was committed under this authority before the seat attested",
            executor=executor, attestation_path=attestation_path, acting_commits=premature,
            findings=findings,
            errors=[f"{premature[0][:12]} acted under {authority_id} before the seat-start "
                    f"attestation at {attestation_commit[:12] if attestation_commit else '<uncommitted>'}; "
                    "the attestation is the FIRST mutation of a seat, not a later formality"])

    if not acting:
        return SeatLifecycle(
            ATTESTATION_COMMITTED,
            f"{executor} has attested to this seat and nothing has been done under it yet",
            executor=executor, attestation_path=attestation_path, findings=findings)

    # TERMINAL. The seat attested, acted, and committed the artefact that CONCLUDES its work — a
    # delivery attestation for an Engineer, a verdict for an auditor. F-3 exists because there was no
    # vocabulary for "audited, completed, closed", so the machine reached for the lawful
    # PRE-attestation state and reported a finished audit as though nothing had happened. This state
    # falls out of the lifecycle rather than being a reporting project, which is exactly the
    # disposition AUTH-0016 asked for.
    if concluded:
        closed_note = "" if active else " The authority is CLOSED, so this is its final state."
        return SeatLifecycle(
            DELIVERY_OR_VERDICT_COMMITTED,
            f"{executor} attested, acted under this authority, and committed its concluding "
            f"delivery or verdict evidence at {concluded[-1][:12]}.{closed_note}",
            executor=executor, attestation_path=attestation_path, acting_commits=acting,
            findings=findings)

    return SeatLifecycle(
        OCCUPIED_AND_VERIFIED,
        f"{executor} attested at {attestation_commit[:12] if attestation_commit else '<uncommitted>'} "
        f"and every one of the {len(acting)} acting commit(s) descends from it",
        executor=executor, attestation_path=attestation_path, acting_commits=acting,
        findings=findings)


def enforcement_errors(root: Path, doc: dict, rel_path: str | None = None) -> list[str]:
    """The lifecycle reasons this record is INVALID. Empty while the seat is lawfully unoccupied."""
    return lifecycle(root, doc, rel_path).errors
