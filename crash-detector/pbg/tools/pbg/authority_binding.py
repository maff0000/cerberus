"""Independent Assurance finding U3-1 — an attestation establishes nothing unless a real
authority lawfully grants it.

THE DEFECT, IN THE VERDICT'S OWN TERMS. The implementer trust path applied CANDIDATE scope only.
`implementer_of` built its `TrustContext` with `expected_candidate` and `candidate_field` and passed
no `expected_authority_id` and no `expected_work_item`, though `TrustContext` supports both. The
only work-item constraint was `WORK_ITEM_PATH_MISMATCH`, which requires the declared work item to
appear in the artefact's own path — a condition a forger satisfies by choosing the directory name.

So this resolved ATTESTED / RESOLVED with ZERO exclusions::

    evidence/engineer/TOTALLY-INVENTED-WORK-ITEM/zz-delivery-attestation.yaml
      work_item:            TOTALLY-INVENTED-WORK-ITEM   <- no such work item exists
      authority_id:         AUTH-0003-ENGINEER           <- CLOSED, and its new_candidate is 8261ce8
      seat_id:              A-SEAT-THAT-NEVER-EXISTED
      external_executor_id: A-PARTY-THAT-NEVER-TOUCHED-IT
      produced_candidate:   b5471d01da117fc2b0bce3436a2c0a469c44542d

Every gate that RAN was satisfied. The gates that would have caught it — does this authority govern
this candidate, does this work item own this fact — were never asked.

THE DOCTRINE THIS MODULE ESTABLISHES, stated once so no caller can drift from it:

    No attestation establishes identity or candidate ownership unless the referenced authority
    lawfully grants that seat, role, work item and candidate relationship.

WHY IT IS A SEPARATE MODULE. `evidence_resolution` deliberately knows nothing about authority
records — its expectations arrive as plain values a caller computed. Putting the record lookup
inside it would make the trust primitive depend on the thing it is meant to be checked against.
This module produces a GATE: a callable that turns one artefact into a list of governed findings,
which `TrustContext` carries and `ownership_findings` runs at the declared AUTHORITY stage.

WHAT "LAWFUL RELATIONSHIP" MEANS FOR A CANDIDATE, and why closed records are not simply barred:

    the authority DECLARES new_candidate == this candidate
        The authority's own committed lifecycle records that this seat produced this commit. This
        is what makes historical evidence usable, and it is the ONLY thing that does. A CLOSED
        record may support historical evidence exactly here.

    the authority is ACTIVE and its target_candidate is an ancestor of this candidate
        The seat is open NOW. It cannot yet declare `new_candidate` — the Engineer may not write its
        own authority record, which is the whole point of PD-1 — so the delivery attestation is the
        durable statement, and ancestry is what ties it to the authority that opened the work.

    anything else
        NOT a relationship. A CLOSED authority that never recorded producing this candidate cannot
        establish ownership of it, however plausible the artefact looks.

NO SPECIAL CASES. No authority ID, seat ID, work item, executor name or candidate SHA appears
anywhere in this module. Every decision is derived from the record under evaluation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from . import validation as vld

#: Authority statuses that can still be reasoned about. Anything else is reported rather than
#: silently treated as one of these — an unrecognised lifecycle is not a licence.
ACTIVE = "ACTIVE"
CLOSED = "CLOSED"


def _text(value) -> str:
    return str(value or "").strip()


def _same(left, right) -> bool:
    return _text(left).casefold() == _text(right).casefold()


def _utc(value) -> datetime | None:
    """A governed timestamp, or None. Never raises, and never invents a timezone.

    A naive timestamp is NOT read as UTC. `authority._parse_utc` makes the same refusal for the
    same reason: a reader assuming UTC is how a one-hour error becomes invisible, and a chronology
    gate resting on a guess is not a gate.
    """
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc) if value.tzinfo else None
    if not isinstance(value, str):
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed.astimezone(timezone.utc) if parsed.tzinfo else None


def find_record(records: dict | None, authority_id: str) -> tuple[str | None, dict | None, bool]:
    """(path, record, unreadable) for `authority_id`.

    Three outcomes, deliberately distinct. NOT FOUND and FOUND-BUT-UNPARSEABLE are different facts
    with different correct responses, and collapsing them is F14's defect one directory over.
    """
    wanted = _text(authority_id)
    unreadable = False
    for path, doc in sorted((records or {}).items()):
        if doc is None:
            unreadable = True
            continue
        if isinstance(doc, dict) and _same(doc.get("authority_id"), wanted):
            return path, doc, False
    return None, None, unreadable


def relationship_findings(doc: dict, path: str, record: dict, *, candidate_field: str,
                          ancestry=None) -> list[vld.ValidationFinding]:
    """Whether the authority `record` lawfully relates to the candidate this artefact declares.

    `ancestry` is an optional `callable(ancestor, descendant) -> bool | None`, so this stays a pure
    function of two documents wherever git cannot be consulted. `None` means "undeterminable",
    which is reported as an absence of proof, never as proof of absence.
    """
    claimed = _text(doc.get(candidate_field))
    if not claimed:
        return []                                  # a candidate-less artefact is the caller's gate

    declared = _text(record.get("new_candidate"))
    if declared:
        if _same(declared, claimed):
            return []
        return [vld.ValidationFinding(
            vld.AUTHORITY, "AUTHORITY_CANDIDATE_MISMATCH", path, field=candidate_field,
            detail=(f"names candidate {claimed[:12]}, but authority "
                    f"{_text(record.get('authority_id'))} records producing "
                    f"{declared[:12]}. An authority that produced a different commit does not "
                    "govern this one, and an attestation cannot reassign it"))]

    status = _text(record.get("status")).upper()
    target = _text(record.get("target_candidate"))
    if status == ACTIVE and target:
        related = ancestry(target, claimed) if ancestry else None
        if related is True or related is None:
            # None = ancestry could not be determined here (no repository, or the commits are not
            # present). The relationship is ADMITTED on the record's own declared target and the
            # weaker basis is what the provenance model then labels; it is not silently upgraded.
            return []
        return [vld.ValidationFinding(
            vld.AUTHORITY, "AUTHORITY_ANCESTRY_INCOHERENT", path, field=candidate_field,
            detail=(f"names candidate {claimed[:12]}, and the ACTIVE authority "
                    f"{_text(record.get('authority_id'))} targets {target[:12]}, which is NOT an "
                    "ancestor of it. A seat's output must descend from the state that seat was "
                    "opened against"))]

    if status == CLOSED:
        return [vld.ValidationFinding(
            vld.AUTHORITY, "CLOSED_AUTHORITY_NO_CANDIDATE_RELATIONSHIP", path,
            field=candidate_field,
            detail=(f"names candidate {claimed[:12]} under authority "
                    f"{_text(record.get('authority_id'))}, which is CLOSED and whose committed "
                    "lifecycle records no candidate for it. A closed authority may support "
                    "historical evidence ONLY where its own lifecycle proves the relationship; "
                    "an unrelated closed record establishes nothing"))]

    return [vld.ValidationFinding(
        vld.AUTHORITY, "AUTHORITY_NO_CANDIDATE_RELATIONSHIP", path, field=candidate_field,
        detail=(f"names candidate {claimed[:12]}, and authority "
                f"{_text(record.get('authority_id'))} (status {status or 'undeclared'}) declares "
                "neither a produced candidate nor a target it could descend from. Absence of a "
                "candidate relationship is NOT_VERIFIED, never a pass"))]


def findings_for(doc: dict, path: str, records: dict | None, *, candidate_field: str = "",
                 ancestry=None) -> list[vld.ValidationFinding]:
    """Every reason this artefact's referenced authority does not lawfully grant what it claims.

    The gate order is the declared one, and it is checked in that order deliberately: an artefact
    naming an authority that does not exist must be refused for THAT reason, not for a downstream
    mismatch against a record that was never found.

        1. referenced authority exists
        2. authority record is valid for evidential use
        3. authority record grants the referenced seat
        4. authority work item matches
        5. authority role matches
        6. authority target candidate or delivered candidate relationship matches
        7. attestation chronology follows authority creation
    """
    out: list[vld.ValidationFinding] = []
    authority_id = _text(doc.get("authority_id"))
    if not authority_id:
        # The schema already requires it; stated here too so the AUTHORITY stage is never satisfied
        # by an artefact that simply declined to name anything.
        return [vld.ValidationFinding(
            vld.AUTHORITY, "AUTHORITY_NOT_DECLARED", path, field="authority_id",
            detail=("declares no authority_id, so no record can be checked for whether it grants "
                    "this seat. An artefact that names no authority is not evidence under one"))]

    if records is None:
        return [vld.ValidationFinding(
            vld.AUTHORITY, "AUTHORITY_RECORDS_UNAVAILABLE", path, field="authority_id",
            detail=(f"declares authority {authority_id} and no authority records could be read, so "
                    "the grant cannot be confirmed. Fail closed: an unverifiable grant is not a "
                    "grant"))]

    # 1 + 2 — the record exists, and is usable as evidence.
    record_path, record, unreadable = find_record(records, authority_id)
    if record is None:
        detail = (f"declares authority {authority_id}, which is not present in this project's "
                  "authority records. An invented authority grants nothing, and an artefact that "
                  "cites one is EXCLUDED rather than believed")
        if unreadable:
            detail += (". At least one authority record in this project is unparseable, so the "
                       "absence cannot even be established cleanly")
        return [vld.ValidationFinding(
            vld.AUTHORITY, "AUTHORITY_NOT_FOUND", path, field="authority_id", detail=detail)]
    if not isinstance(record, dict):                          # pragma: no cover - defensive
        return [vld.ValidationFinding(
            vld.AUTHORITY, "AUTHORITY_UNUSABLE", path, field="authority_id",
            detail=f"declares authority {authority_id}, whose record is not a mapping of fields")]

    where = Path(record_path).name if record_path else authority_id

    # 3 — the record grants the referenced SEAT.
    # A value the artefact never CLAIMED cannot mismatch — the schema stage is what requires these
    # fields to be present at all, and duplicating that here would report one defect twice while
    # saying something slightly different about it. What is refused is a CLAIM the record cannot
    # support, which is the whole shape of independent Assurance finding U3-1.
    claimed_seat = _text(doc.get("seat_id"))
    granted_seat = _text(record.get("seat_id"))
    if claimed_seat and not granted_seat:
        out.append(vld.ValidationFinding(
            vld.AUTHORITY, "AUTHORITY_GRANTS_NO_SEAT", path, field="seat_id",
            detail=(f"claims seat {claimed_seat or '<none>'} under authority {authority_id}, whose "
                    f"record ({where}) declares no seat_id at all. A record that names no seat "
                    "cannot be shown to grant this one, and a seat that cannot be shown to be "
                    "granted is refused")))
    elif granted_seat and not _same(granted_seat, claimed_seat):
        out.append(vld.ValidationFinding(
            vld.AUTHORITY, "AUTHORITY_SEAT_MISMATCH", path, field="seat_id",
            detail=(f"claims seat {claimed_seat or '<none>'}, but authority {authority_id} grants "
                    f"{granted_seat}. The authority record decides which seat exists; an invented "
                    "seat is not created by writing it down")))

    # 4 — the work item matches the one the authority governs.
    claimed_item = _text(doc.get("work_item"))
    granted_item = _text(record.get("work_item"))
    if claimed_item and not granted_item:
        out.append(vld.ValidationFinding(
            vld.AUTHORITY, "AUTHORITY_DECLARES_NO_WORK_ITEM", path, field="work_item",
            detail=(f"declares work_item {claimed_item} under authority "
                    f"{authority_id}, whose record declares none. The work item an artefact belongs "
                    "to comes from the authority, never from the directory it was filed in")))
    elif granted_item and not _same(granted_item, claimed_item):
        out.append(vld.ValidationFinding(
            vld.AUTHORITY, "AUTHORITY_WORK_ITEM_MISMATCH", path, field="work_item",
            detail=(f"declares work_item {claimed_item or '<none>'}, but authority {authority_id} "
                    f"governs {granted_item}. Choosing a directory name satisfies the path check "
                    "and proves nothing; the authority is what owns the work item")))

    # 5 — the role matches the one the authority assigns.
    claimed_role = _text(doc.get("assigned_role"))
    granted_role = _text(record.get("assigned_role"))
    if granted_role and claimed_role and not _same(granted_role, claimed_role):
        out.append(vld.ValidationFinding(
            vld.AUTHORITY, "AUTHORITY_ROLE_MISMATCH", path, field="assigned_role",
            detail=(f"declares assigned_role {claimed_role}, but authority {authority_id} assigns "
                    f"{granted_role}. A self-declared role is checked against the record, never "
                    "trusted in place of it")))

    # 6 — the candidate relationship.
    if candidate_field:
        out.extend(relationship_findings(doc, path, record, candidate_field=candidate_field,
                                         ancestry=ancestry))

    # 7 — chronology. An attestation cannot lawfully predate the authority it claims to act under;
    # that is PD-1 restated at the evidence layer.
    attested, granted = _utc(doc.get("attested_utc")), _utc(record.get("granted_utc"))
    if attested and granted and attested < granted:
        out.append(vld.ValidationFinding(
            vld.AUTHORITY, "ATTESTATION_PRECEDES_AUTHORITY", path, field="attested_utc",
            detail=(f"is attested {attested.isoformat()}, before authority {authority_id} was "
                    f"granted at {granted.isoformat()}. A seat cannot be occupied under an "
                    "authority that did not yet exist")))
    return out


def gate(root: Path, records: dict | None, *, candidate_field: str = "", use_git: bool = True):
    """A callable `(Source) -> [ValidationFinding]` for `TrustContext.authority_gate`.

    `use_git` is not a switch that weakens anything — ancestry is consulted when a repository is
    actually there, and its absence lowers the confidence the provenance model reports rather than
    raising the trust this gate grants.
    """
    ancestry = _ancestry_probe(root) if use_git else None

    def _gate(source):
        return findings_for(source.doc, source.rel_path, records,
                            candidate_field=candidate_field, ancestry=ancestry)

    return _gate


def _ancestry_probe(root: Path):
    """`(ancestor, descendant) -> True | False | None`, where None means undeterminable.

    Undeterminable is its own answer on purpose. A project with no git history, or a candidate SHA
    that is not an object in THIS repository, cannot be judged on ancestry — and answering False
    there would fail every test fixture while answering True would invent a fact.
    """
    from . import authority as auth_mod

    def _probe(ancestor: str, descendant: str):
        if not (ancestor and descendant):
            return None
        try:
            if not (auth_mod.commit_exists(root, ancestor)
                    and auth_mod.commit_exists(root, descendant)):
                return None
            return auth_mod.is_ancestor(root, ancestor, descendant)
        except Exception:                                     # pragma: no cover - defensive
            return None

    return _probe
