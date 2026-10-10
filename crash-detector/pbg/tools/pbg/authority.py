"""Authority record validation — before the write, not after.

PD-2. A closure edit introduced a duplicate `target_candidate` key. `continuity.parse_strict`
rejects duplicates, so `boot._read_authority` failed for the ENTIRE directory: no authority could
be resolved at all, and the only reason it was caught is that somebody happened to read the
directory afterwards. A control that fires only when the next person tries to work is a trap laid
for them, not a control.

Two distinct properties are needed and they are not the same thing:

    PREVENTION   an invalid record cannot enter governed history through the supported path
    DIAGNOSIS    when a corrupt record does exist, say exactly which one, and keep the valid ones
                 visible instead of collapsing the directory to an opaque None

ENFORCEMENT TRUTH. Prevention here is real but bounded, and the boundary is stated rather than
implied:

    supported authority writer                     ENFORCED
    project-owned pre-commit hook, when installed  ENFORCED
    raw `git commit` outside the supported path    NOT_GLOBALLY_PREVENTED

Git will accept any bytes it is given. Claiming otherwise would be exactly the kind of
overstatement independent Assurance found in the read-only adapter's docstring two candidates
ago.

APPEND-ONLY. The historical corrupt commit is not rewritten. It stays in history, superseded by
later valid governance, and this module makes it visible rather than pretending it never happened.

--------------------------------------------------------------------------------------------------
The F13/F14/F15 repair. Three ways this validator could be made to say ALLOW when the honest
answer was DENY, all of them by REMOVING something rather than by asserting something false:

    F13   OMISSION. `target_candidate` was optional, and the separation-of-duties comparison was
          guarded by `if role == ASSURANCE_ROLE and actor and target`. Leave the field out and the
          guard is false, the comparison never runs, and an Engineer can be assigned Assurance of
          its own candidate. The control was not defeated; it was never reached.

    F14   CORRUPTION. Sibling records that failed to parse were stored as None and skipped by
          `if not isinstance(other, dict): continue`. One unparseable file therefore DELETED the
          separation-of-duties and single-ACTIVE checks for every other record. Damaging a record
          was a way to acquire permission.

    F15   ROLE EXEMPTION AND DIRECTION. The one timestamp check was `role == ENGINEER_ROLE` and
          compared granted_utc against the TARGET commit only. Assurance records were exempt
          outright, and no role was checked against its own authority commit — so AUTH-0008 could
          carry a granted_utc eight hours after the commit that recorded it and validate clean.
          An authority stamped after the work is a retrospective authorisation.

The common shape is that a missing fact was read as an absent objection. Everything below treats a
fact that could not be established as a reason to refuse, and says which check could not complete.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import continuity

AUTHORITY_DIR = "governance/authority"

REQUIRED_FIELDS = ("authority_id", "status", "record_type", "assigned_role", "actor_id",
                   "grantor", "work_item", "granted_utc")

VALID_STATUSES = ("ACTIVE", "CLOSED", "SUPERSEDED", "REVOKED")
VALID_ROLES = ("PROJECT_LEAD", "ENGINEER", "ASSURANCE_ENGINEER")

#: Set on a record whose role must never be held by whoever implemented the target.
ASSURANCE_ROLE = "ASSURANCE_ENGINEER"
ENGINEER_ROLE = "ENGINEER"

#: F15. Clock skew between the machine that stamps a grant and the machine that commits it is real,
#: and it is SMALL. Five minutes, documented here so its width is auditable rather than buried in a
#: comparison. AUTH-0008 carried a granted_utc eight hours after its own authority commit: any
#: tolerance generous enough to admit that is generous enough to authorise finished work
#: retrospectively, which is the entire defect. A tolerance is a permitted measurement error, never
#: a permitted rewriting of order.
CLOCK_SKEW_TOLERANCE = timedelta(minutes=5)

#: Fields naming work that this authority purports to authorise. The authority commit must be a
#: strict ancestor of each. `new_candidate` is the Engineer's product; the evidence fields are the
#: Assurance counterpart. A record naming none of them simply has no such check to run, and that is
#: reported as a check NOT RUN rather than as a pass.
AUTHORISED_WORK_FIELDS = ("new_candidate", "evidence_commit", "audit_evidence_commit")


def render_blocked(diagnosis: dict) -> str:
    """The AUTHORITY_RESOLUTION_BLOCKED diagnostic, rendered in full.

    Everything an operator needs to locate the fault without reading the directory by hand, and an
    explicit statement that nothing was written — because the question a blocked write always
    raises is "did it half-happen?".
    """
    lines = [f"  resolution: {diagnosis.get('resolution', 'AUTHORITY_RESOLUTION_BLOCKED')}"]
    for record in diagnosis.get("corrupt_records", []):
        lines.append(f"  corrupt_record: {record['path']}")
        lines.append(f"      {record['error']}")
    for record in diagnosis.get("valid_active_records", []):
        lines.append(f"  valid_active_authority: {record['path']}")
        lines.append(f"      {record.get('authority_id')} {record.get('status')} "
                     f"{record.get('assigned_role')} / {record.get('actor_id')} "
                     f"target={str(record.get('target_candidate'))[:12] or 'none'}")
    if not diagnosis.get("valid_active_records"):
        lines.append("  valid_active_authority: none resolvable")
    proposed = diagnosis.get("proposed_record") or {}
    if proposed:
        lines.append(f"  proposed_record: {proposed.get('path')}")
        lines.append(f"      {proposed.get('authority_id')} {proposed.get('status')} "
                     f"{proposed.get('assigned_role')} / {proposed.get('actor_id')} "
                     f"target={str(proposed.get('target_candidate'))[:12] or 'none'}")
    for incomplete in diagnosis.get("checks_not_completed", []):
        lines.append(f"  check_not_completed: {incomplete}")
    lines.append(f"  bytes_written: {str(diagnosis.get('bytes_written', False)).lower()}")
    return "\n".join(lines)


class AuthorityInvalid(Exception):
    """A record failed validation. Carries every reason, not merely the first."""

    code = "AUTHORITY_INVALID"

    def __init__(self, path, errors, diagnosis: dict | None = None):
        self.path, self.errors = path, list(errors)
        self.diagnosis = dict(diagnosis or {})
        body = "\n".join(f"  - {e}" for e in self.errors)
        extra = f"\n{render_blocked(self.diagnosis)}" if self.diagnosis else ""
        super().__init__(f"{self.code}: {path}\n{body}{extra}")


class AuthorityResolutionBlocked(AuthorityInvalid):
    """F14. Governance state is corrupt, so no new authority may be created from it.

    Deliberately a subclass: every caller that already refuses on AuthorityInvalid keeps refusing.
    The distinct class and code exist so the REASON is not flattened — "your record is wrong" and
    "the directory it must be judged against is unreadable" are different findings and lead to
    different repairs.
    """

    code = "AUTHORITY_RESOLUTION_BLOCKED"


# --- git helpers: read-only ----------------------------------------------------------------------- #

def _git(root: Path, *args: str) -> tuple[int, str]:
    r = subprocess.run(["git", *args], cwd=str(root), capture_output=True, text=True)
    return r.returncode, r.stdout.strip()


def commit_exists(root: Path, sha: str) -> bool:
    """Is this a commit object IN THIS repository? `cat-file -e` alone would accept any object."""
    if not sha or len(sha) < 7:
        return False
    code, kind = _git(root, "cat-file", "-t", sha)
    return code == 0 and kind == "commit"


def commit_time(root: Path, sha: str) -> datetime | None:
    code, out = _git(root, "show", "-s", "--format=%cI", sha)
    if code != 0 or not out:
        return None
    try:
        return datetime.fromisoformat(out)
    except ValueError:
        return None


def is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    """PD-1's enforceable half: did the authority commit actually precede the work?"""
    code, _ = _git(root, "merge-base", "--is-ancestor", ancestor, descendant)
    return code == 0


def introducing_commit(root: Path, rel_path: str) -> str | None:
    code, out = _git(root, "log", "--diff-filter=A", "--format=%H", "-1", "--", rel_path)
    return out or None if code == 0 else None


def _parse_utc(value) -> tuple[datetime | None, str | None]:
    """Parse a governed timestamp. Returns (datetime, reason-it-failed).

    STRICT ABOUT ZONE. A timestamp without an explicit zone is not a UTC timestamp, it is a
    timestamp whose zone the reader is invited to assume — and the reader assuming UTC is how a
    one-hour error becomes invisible. Previously a naive value was silently relabelled UTC here,
    which meant the strictest check in the module began with a guess.

    YAML makes this subtle rather than obvious. An unquoted `2026-08-03T14:30:00Z` is parsed by
    PyYAML into a tz-aware datetime; an unquoted `2026-08-03T14:30:00` becomes a NAIVE datetime;
    a quoted value stays a string. All three arrive here and only the first two are timestamps at
    all. The type-narrow check this replaces accepted only `str` and returned None for datetimes,
    so the comparison silently never ran — the same class as the all-digit SHA parsed as int 0.
    """
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return None, "no timezone designator (a naive timestamp is not UTC, it is unlabelled)"
        return value.astimezone(timezone.utc), None
    if not isinstance(value, str):
        return None, f"not a timestamp; YAML produced {type(value).__name__}"
    text = value.strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None, "not an ISO-8601 timestamp"
    if parsed.tzinfo is None:
        return None, "no timezone designator (a naive timestamp is not UTC, it is unlabelled)"
    return parsed.astimezone(timezone.utc), None


def _describe(delta: timedelta) -> str:
    seconds = int(abs(delta).total_seconds())
    if seconds >= 3600:
        return f"{seconds // 3600}h{(seconds % 3600) // 60:02d}m"
    if seconds >= 60:
        return f"{seconds // 60}m{seconds % 60:02d}s"
    return f"{seconds}s"


# --- F15: timestamp coherence, every role, both directions ----------------------------------------- #

@dataclass
class TimestampReport:
    """What was checked, what could not be, and what failed.

    The third list is the point. A validator that prints "timestamp coherence: OK" after skipping
    the only check that would have caught the defect is worse than one that prints nothing, because
    the next reader stops looking. `coherence_claimed` is false whenever anything was skipped.
    """

    errors: list[str] = field(default_factory=list)
    checks_run: list[str] = field(default_factory=list)
    checks_skipped: list[str] = field(default_factory=list)

    @property
    def coherence_claimed(self) -> bool:
        return not self.errors and not self.checks_skipped

    def render(self) -> str:
        lines = [f"timestamp coherence: {'ESTABLISHED' if self.coherence_claimed else 'NOT ESTABLISHED'}"]
        lines += [f"  ran     : {c}" for c in self.checks_run]
        lines += [f"  NOT RUN : {c}" for c in self.checks_skipped]
        lines += [f"  FAIL    : {e}" for e in self.errors]
        return "\n".join(lines)


def _target_value(doc: dict, allow_fallback: bool = True):
    raw = doc.get("target_candidate")
    if raw is None and allow_fallback:
        raw = doc.get("prior_candidate")
    return raw


def timestamp_coherence(doc: dict, root: Path, rel_path: str | None = None,
                        now: datetime | None = None) -> TimestampReport:
    """Every timestamp rule, applied to EVERY role.

    Both directions matter and they catch different lies:

        granted_utc AFTER the authority commit     the grant was written into the past after the
                                                   commit existed — retrospective authorisation
        granted_utc BEFORE the target commit       the authority claims to predate the very thing
                                                   it names — an impossible reference
        granted_utc far in the future              a stamp that has not happened yet cannot record
                                                   a decision that has
        authority commit not before the work       the work was not authorised when it was done
    """
    report = TimestampReport()
    now = now or datetime.now(timezone.utc)
    root = Path(root)

    raw = doc.get("granted_utc")
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        report.errors.append(
            "granted_utc is missing; no timestamp check can be performed for any role, and an "
            "authority with no grant time cannot be placed in the order of events")
        report.checks_skipped.append("every timestamp check: granted_utc absent")
        return report

    granted, reason = _parse_utc(raw)
    if granted is None:
        report.errors.append(f"granted_utc {raw!r} is not a timezone-aware UTC timestamp: {reason}")
        report.checks_skipped.append("every comparison: granted_utc could not be parsed")
        return report
    report.checks_run.append("granted_utc_parses_as_timezone_aware_utc")

    # 1. not unreasonably in the future
    report.checks_run.append("granted_utc_not_in_the_future")
    if granted > now + CLOCK_SKEW_TOLERANCE:
        report.errors.append(
            f"timestamp incoherent: granted_utc {granted.isoformat()} is "
            f"{_describe(granted - now)} in the future (tolerance {_describe(CLOCK_SKEW_TOLERANCE)}). "
            "A grant cannot be recorded before it happens.")

    # 2. not materially later than the commit that records it
    auth_commit = introducing_commit(root, rel_path) if rel_path else None
    if rel_path is None:
        report.checks_skipped.append(
            "granted_utc_not_after_authority_commit: no record path supplied")
    elif auth_commit is None:
        report.checks_skipped.append(
            f"granted_utc_not_after_authority_commit: {rel_path} is not yet committed, so the "
            "authority commit it must precede does not exist yet")
    else:
        ctime = commit_time(root, auth_commit)
        if ctime is None:
            report.checks_skipped.append(
                f"granted_utc_not_after_authority_commit: commit time of {auth_commit[:12]} "
                "unreadable")
        else:
            report.checks_run.append("granted_utc_not_after_authority_commit")
            if granted > ctime + CLOCK_SKEW_TOLERANCE:
                report.errors.append(
                    f"timestamp incoherent: granted_utc {granted.isoformat()} is "
                    f"{_describe(granted - ctime)} LATER than the authority commit "
                    f"{auth_commit[:12]} ({ctime.isoformat()}) that records it. An authority "
                    "stamped after its own commit is a retrospective authorisation of work that "
                    "was already underway.")

    # 3. not before the commit it references — every role, not only ENGINEER
    raw_target = _target_value(doc)
    target = "" if raw_target is None else str(raw_target)
    if not target:
        report.checks_skipped.append(
            "granted_utc_not_before_target_candidate: the record names no target candidate")
    elif not commit_exists(root, target):
        report.checks_skipped.append(
            f"granted_utc_not_before_target_candidate: {target[:12]} does not resolve to a commit "
            "in this repository")
    else:
        tctime = commit_time(root, target)
        if tctime is None:
            report.checks_skipped.append(
                f"granted_utc_not_before_target_candidate: commit time of {target[:12]} unreadable")
        else:
            report.checks_run.append("granted_utc_not_before_target_candidate")
            if granted + CLOCK_SKEW_TOLERANCE < tctime:
                report.errors.append(
                    f"timestamp incoherent: granted_utc {granted.isoformat()} precedes the commit "
                    f"{target[:12]} it references ({tctime.isoformat()})")

    # 4. the authority commit must precede the work it authorises
    for name in AUTHORISED_WORK_FIELDS:
        value = doc.get(name)
        if value is None:
            continue
        for sha in ([value] if isinstance(value, (str, int)) else list(value)):
            sha = str(sha)
            if auth_commit is None:
                report.checks_skipped.append(
                    f"authority_commit_precedes_{name}: the authority record is not yet committed")
                continue
            if not commit_exists(root, sha):
                report.checks_skipped.append(
                    f"authority_commit_precedes_{name}: {sha[:12]} does not resolve to a commit "
                    "in this repository")
                continue
            report.checks_run.append(f"authority_commit_precedes_{name}")
            if auth_commit == sha:
                report.errors.append(
                    f"retrospective authorisation: the authority commit {auth_commit[:12]} IS "
                    f"{name} {sha[:12]}; a record cannot authorise the commit it ships in")
            elif not is_ancestor(root, auth_commit, sha):
                report.errors.append(
                    f"retrospective authorisation: the authority commit {auth_commit[:12]} is not "
                    f"an ancestor of {name} {sha[:12]}; the work was not authorised when it "
                    "was done")
    return report


# --- record-level validation ----------------------------------------------------------------------- #

def validate_document(doc: dict, root: Path, siblings: dict | None = None,
                      path: str = "<new>", rel_path: str | None = None,
                      now: datetime | None = None) -> list[str]:
    """Every reason this record is invalid. Semantic, not merely structural.

    `siblings` maps path -> parsed document, with None for a record that would not parse. A None
    sibling is NOT quietly skipped: see `incomplete_checks`, which names the comparisons that
    therefore could not run, and `write_record`, which refuses on them.
    """
    errors: list[str] = []
    siblings = siblings or {}

    for field_name in REQUIRED_FIELDS:
        if not doc.get(field_name):
            errors.append(f"required field missing or empty: {field_name}")

    status = str(doc.get("status", ""))
    if status and status not in VALID_STATUSES:
        errors.append(f"status {status!r} is not one of {list(VALID_STATUSES)}")

    role = str(doc.get("assigned_role", ""))
    if role and role not in VALID_ROLES:
        errors.append(f"assigned_role {role!r} is not one of {list(VALID_ROLES)}")

    actor = str(doc.get("actor_id", ""))
    grantor = str(doc.get("grantor", ""))
    if actor and grantor and actor.upper() == grantor.upper():
        errors.append(f"self-grant prohibited: actor_id and grantor are both {actor!r}. An actor "
                      "may not author its own authority.")

    # F13. An Assurance authority is always Assurance OF a named candidate.
    #
    # There is no "general Assurance" and there must be no way to obtain one by leaving the field
    # out. The separation-of-duties comparison below is the control that stops an Engineer auditing
    # its own work, and it can only compare a target against a target: with none recorded, the
    # comparison does not run and the record validates clean. That is omission becoming permission,
    # in the one place where the consequence is an unaudited candidate.
    #
    # `prior_candidate` deliberately does NOT satisfy this. It names what came before, which is a
    # different fact from what is being assured.
    if role == ASSURANCE_ROLE:
        if "target_candidate" not in doc:
            errors.append(
                "target_candidate is MANDATORY for an ASSURANCE_ENGINEER authority and is absent. "
                "Assurance is always assurance OF a named candidate; with none recorded the "
                "separation-of-duties comparison cannot run, and omission would become permission "
                "(F13, PBG-SOD-001).")
        elif doc.get("target_candidate") is None:
            errors.append(
                "target_candidate is null on an ASSURANCE_ENGINEER authority. An explicit null is "
                "not a target; it is the absence of one written down (F13).")
        elif isinstance(doc["target_candidate"], str) and not doc["target_candidate"].strip():
            errors.append(
                "target_candidate is empty on an ASSURANCE_ENGINEER authority (F13).")

    # target candidate: exists, is a commit, and belongs to THIS repository.
    #
    # Resolved with explicit None checks rather than `a or b`. An all-digit SHA is parsed by YAML
    # as an integer, and the integer 0 is FALSY — so `or` skipped the entire target check for
    # exactly the value most likely to be a placeholder. Found by a test that expected a rejection
    # and got silence.
    raw = _target_value(doc, allow_fallback=role != ASSURANCE_ROLE)
    target = "" if raw is None else str(raw)
    if raw is not None and not isinstance(raw, str):
        errors.append(f"target_candidate {raw!r} is not a string; YAML has coerced it to "
                      f"{type(raw).__name__}. Quote the SHA — an unquoted all-digit value becomes "
                      "an integer and stops looking like a commit.")
    elif target and not (len(target) >= 7 and all(c in "0123456789abcdef" for c in target.lower())):
        errors.append(f"target_candidate {target!r} is not a hexadecimal commit SHA")
    if target and (isinstance(raw, str) or role != ASSURANCE_ROLE):
        if not commit_exists(root, target):
            errors.append(f"target_candidate {target[:12]} is not a commit in this repository "
                          "(nonexistent, or belongs to another repository)")

    # F15. Timestamp coherence for every role, in both directions.
    errors.extend(timestamp_coherence(doc, root, rel_path=rel_path, now=now).errors)

    # separation of duties: whoever implemented a candidate may not assure it
    if role == ASSURANCE_ROLE and actor and target:
        for other_path, other in siblings.items():
            if not isinstance(other, dict):
                continue                       # counted by incomplete_checks, never ignored
            if str(other.get("assigned_role", "")) != ENGINEER_ROLE:
                continue
            same_target = target in (str(other.get("target_candidate") or ""),
                                     str(other.get("new_candidate") or ""))
            if same_target and str(other.get("actor_id", "")).upper() == actor.upper():
                errors.append(
                    f"separation of duties: {actor} is assigned ASSURANCE_ENGINEER for "
                    f"{target[:12]}, but {Path(other_path).name} records {actor} as the ENGINEER "
                    "who produced it (PBG-SOD-001, non-waivable)")

    # PLACEMENT QUESTION A. A security-relevant field must not be able to sit somewhere the
    # framework does not look and quietly become documentation. The permitted positions are declared
    # in tools/pbg/data/authority-field-placement.yaml; an undeclared one, or two declared ones
    # that disagree invalidates the record. A declared alias is enforced identically and merely
    # reported, so append-only history is diagnosed rather than made unwritable.
    from . import placement, seat
    errors.extend(placement.placement_errors(doc))

    # PLACEMENT QUESTION B, the ordering defect. An authority may lawfully exist before its executor
    # attests — at creation the demand is unanswerable by construction, and FAIL there conflates
    # NOT-YET with NO. What may NOT happen is a seat ACTING unattested, and that is now observed
    # from committed history rather than asserted in prose.
    lifecycle = None
    if status == "ACTIVE":
        lifecycle = seat.lifecycle(root, doc, rel_path)
        errors.extend(lifecycle.errors)

    # SOD-TOOLING-0001. The comparison above reads actor_id against actor_id. It still fires for
    # records that carry NAMED actors — the whole of AUTH-0002..AUTH-0009 — so it stays. What it
    # cannot do is fire once internal identities are GENERIC, which is exactly what the closed-system
    # model requires: EXTERNAL_AUDITOR never equals EXTERNAL_ENGINEER, so the check ran, passed, and
    # proved nothing for every record written under that model.
    #
    # This compares the EXECUTORS instead, from durable attestations. FAIL is an error, EXCEPT where
    # the only unmet condition is that the seat has not been occupied yet and the lifecycle confirms
    # nothing has been done under it. That single exception is what makes a record demanding an
    # attestation creatable at all; it closes the moment the seat acts.
    if role == ASSURANCE_ROLE:
        from . import executors
        separation = executors.check_separation(root, doc, siblings or {})
        if separation.status == executors.FAIL:
            # An AFFIRMATIVE determination, never an absent one. A CLOSED record gets no lifecycle
            # walk, so it gets no exemption either — "we did not look" must never read as "not yet".
            not_yet = (separation.awaiting_attestation
                       and lifecycle is not None and lifecycle.lawfully_unoccupied)
            if not not_yet:
                errors.append(
                    f"separation of duties: {separation.detail} (PBG-SOD-001, non-waivable)")
                # Reports accompany a failure; they are not themselves reasons a record is invalid.
                # A placement NOTE says where a field was read from — which is worth printing and is
                # not a defect. A placement DIVERGENCE is already an error in its own right above.
                errors.extend(f for f in separation.findings
                              if not f.startswith(placement.NOTE))

    # one ACTIVE authority
    if status == "ACTIVE":
        others = [Path(p).name for p, o in siblings.items()
                  if isinstance(o, dict) and str(o.get("status", "")) == "ACTIVE"
                  and o.get("authority_id") != doc.get("authority_id")]
        if others:
            errors.append(f"a second ACTIVE authority would exist alongside {others}; boot returns "
                          "'ambiguous assignment' and fails closed")

    # path coherence
    writable = [str(x) for x in (doc.get("writable_scope") or doc.get("permitted_write_paths") or [])]
    protected = [str(x) for x in (doc.get("protected_scope")
                                  or doc.get("prohibited_modification_paths") or [])]
    for w in writable:
        for p in protected:
            if w == p:
                errors.append(f"path {w!r} is both writable and protected")
    return errors


def incomplete_checks(doc: dict, siblings: dict) -> list[str]:
    """F14. The comparisons that a corrupt sibling made impossible, named individually.

    "Some checks did not run" is not a finding an operator can act on. Which checks, and against
    which unreadable record, is. Every entry here is a check whose absence could hide a DENY.
    """
    corrupt = sorted(p for p, d in (siblings or {}).items() if d is None)
    if not corrupt:
        return []
    names = ", ".join(Path(p).name for p in corrupt)
    role = str(doc.get("assigned_role", ""))
    missing = [
        f"single_active_authority: cannot tell whether {names} is ACTIVE, so a second ACTIVE "
        "authority cannot be ruled out",
    ]
    if role == ASSURANCE_ROLE:
        missing.append(
            f"separation_of_duties (PBG-SOD-001, non-waivable): cannot tell whether {names} "
            f"records {doc.get('actor_id')} as the ENGINEER who produced "
            f"{str(_target_value(doc) or 'the target')[:12]}")
    else:
        missing.append(
            f"separation_of_duties (PBG-SOD-001, non-waivable): cannot read the role, actor or "
            f"target recorded by {names}")
    return missing


def validate_record_file(path: Path, root: Path, siblings: dict | None = None) -> list[str]:
    """Parse strictly, then validate. A parse failure is itself the finding."""
    try:
        doc = continuity.parse_strict(Path(path).read_text(encoding="utf-8"))
    except continuity.ContinuityError as exc:
        return [f"unparseable: {exc}"]
    try:
        rel = str(Path(path).resolve().relative_to(Path(root).resolve()))
    except ValueError:                                     # pragma: no cover - defensive
        rel = None
    return validate_document(doc, root, siblings, str(path), rel_path=rel)


# --- precedence: PD-1's enforceable half ----------------------------------------------------------- #

def check_precedence(root: Path, authority_rel_path: str, implementation_commit: str,
                     kind: str = "implementation") -> list[str]:
    """The authority commit must be a strict ancestor of the work it authorises.

    `kind` names what the later commit IS — an implementation, or Assurance evidence. Both are
    "work done under this authority" and both must postdate it; an audit whose evidence predates
    the authority to audit is as retrospective as an implementation that does.
    """
    errors = []
    auth_commit = introducing_commit(root, authority_rel_path)
    if not auth_commit:
        return [f"cannot locate the commit introducing {authority_rel_path}"]
    if auth_commit == implementation_commit:
        errors.append(
            f"authority {authority_rel_path} was introduced in the SAME commit as the "
            f"{kind} {implementation_commit[:12]}; it cannot authorise work it ships with")
    elif not is_ancestor(root, auth_commit, implementation_commit):
        errors.append(
            f"authority commit {auth_commit[:12]} is not an ancestor of {kind} "
            f"{implementation_commit[:12]}; an authority added alongside or after the work does "
            "not authorise it retrospectively")
    return errors


# --- directory diagnosis: precise, not opaque ------------------------------------------------------ #

def diagnose(root: Path) -> dict:
    """Parse every record INDEPENDENTLY. One corrupt file must not blind the rest.

    Previously a single unparseable record made the whole directory resolve to None, so a valid
    ACTIVE authority became invisible and the message named nothing. Fail closed for RESOLUTION,
    but never fail silent about WHICH record is at fault.

    F14: a corrupt record of ANY lifecycle state — including a CLOSED one nobody is relying on —
    blocks resolution, because "this closed record is irrelevant" is a judgement that requires
    reading it. What corruption must never do is make the readable records invisible too.
    """
    directory = Path(root) / AUTHORITY_DIR
    result = {"records": {}, "corrupt": [], "active": [], "resolution": "NO_AUTHORITY_DIRECTORY"}
    if not directory.is_dir():
        return result

    for path in sorted(directory.glob("*.yaml")):
        rel = str(path.relative_to(root))
        try:
            doc = continuity.parse_strict(path.read_text(encoding="utf-8"))
        except continuity.ContinuityError as exc:
            result["records"][rel] = {"parsed": False, "error": str(exc)}
            result["corrupt"].append(rel)
            continue
        result["records"][rel] = {"parsed": True, "authority_id": doc.get("authority_id"),
                                  "status": doc.get("status"),
                                  "assigned_role": doc.get("assigned_role"),
                                  "actor_id": doc.get("actor_id"),
                                  "target_candidate": doc.get("target_candidate")}
        if str(doc.get("status", "")).upper() == "ACTIVE":
            result["active"].append(rel)

    if result["corrupt"]:
        result["resolution"] = "AUTHORITY_RESOLUTION_BLOCKED"
    elif len(result["active"]) > 1:
        result["resolution"] = "AMBIGUOUS_ASSIGNMENT"
    elif len(result["active"]) == 1:
        result["resolution"] = "RESOLVED"
    else:
        result["resolution"] = "NO_ACTIVE_AUTHORITY"
    return result


def render_diagnosis(d: dict) -> str:
    lines = [f"AUTHORITY RESOLUTION: {d['resolution']}", ""]
    for rel, info in d["records"].items():
        if info["parsed"]:
            lines.append(f"  [ ok ] {rel}")
            lines.append(f"         {info.get('authority_id')} {info.get('status')} "
                         f"{info.get('assigned_role')} / {info.get('actor_id')}")
        else:
            lines.append(f"  [CORRUPT] {rel}")
            lines.append(f"         {info['error']}")
    if d["resolution"] == "AUTHORITY_RESOLUTION_BLOCKED":
        lines += ["", f"  corrupt_record: {d['corrupt']}"]
        if d["active"]:
            lines.append(f"  valid_active_record_present_but_not_usable: {d['active']}")
        lines.append("  Authority cannot be resolved while any record is unparseable. The valid "
                     "records above remain visible so the fault can be located precisely.")
    return "\n".join(lines)


# --- the supported writer -------------------------------------------------------------------------- #

def _sibling_docs_and_errors(root: Path, filename: str | None = None) -> tuple[dict, dict]:
    """Parsed siblings (None where unparseable) and the parse error for each corrupt one."""
    docs: dict = {}
    errors: dict = {}
    directory = Path(root) / AUTHORITY_DIR
    if not directory.is_dir():
        return docs, errors
    for path in sorted(directory.glob("*.yaml")):
        if filename is not None and path.name == filename:
            continue
        try:
            docs[str(path)] = continuity.parse_strict(path.read_text(encoding="utf-8"))
        except continuity.ContinuityError as exc:
            docs[str(path)] = None
            errors[str(path)] = str(exc)
    return docs, errors


def write_record(root: Path, filename: str, text: str,
                 now: datetime | None = None) -> Path:
    """The supported path for creating or amending an authority record.

    Validates BEFORE the bytes land. This is the only place in the framework where prevention
    rather than detection is claimed, and the claim is bounded: a raw `git commit` bypasses it.

    F14. A corrupt sibling now STRENGTHENS this refusal instead of weakening it. Previously an
    unparseable neighbour was stored as None and skipped, which deleted the separation-of-duties
    and single-ACTIVE comparisons for the record being written — damaging a file was a way to get
    permission. Now:

        every check that CAN still run from the valid records is run, and its failures reported
        every check that CANNOT complete is named
        the write is refused
        nothing is written

    all three at once, so the caller learns both what is broken and what could not be judged.
    """
    root = Path(root)
    target = root / AUTHORITY_DIR / filename
    try:
        doc = continuity.parse_strict(text)
    except continuity.ContinuityError as exc:
        raise AuthorityInvalid(filename, [f"unparseable: {exc}"]) from exc

    siblings, parse_errors = _sibling_docs_and_errors(root, filename)

    rel_path = str((Path(AUTHORITY_DIR) / filename).as_posix())
    errors = validate_document(doc, root, siblings, filename, rel_path=rel_path, now=now)
    blocked = incomplete_checks(doc, siblings)

    if blocked:
        diagnosis = {
            "resolution": "AUTHORITY_RESOLUTION_BLOCKED",
            "corrupt_records": [{"path": str(Path(p).relative_to(root)), "error": err}
                                for p, err in sorted(parse_errors.items())],
            "valid_active_records": [
                {"path": str(Path(p).relative_to(root)), "authority_id": d.get("authority_id"),
                 "status": d.get("status"), "assigned_role": d.get("assigned_role"),
                 "actor_id": d.get("actor_id"), "target_candidate": d.get("target_candidate")}
                for p, d in sorted(siblings.items())
                if isinstance(d, dict) and str(d.get("status", "")).upper() == "ACTIVE"],
            "proposed_record": {
                "path": rel_path, "authority_id": doc.get("authority_id"),
                "status": doc.get("status"), "assigned_role": doc.get("assigned_role"),
                "actor_id": doc.get("actor_id"),
                "target_candidate": doc.get("target_candidate")},
            "checks_not_completed": blocked,
            "bytes_written": False,
        }
        raise AuthorityResolutionBlocked(
            filename,
            errors + ["governance state is corrupt; no new authority may be created from it. "
                      "A fact that cannot be read is not a fact that permits."],
            diagnosis)

    if errors:
        raise AuthorityInvalid(filename, errors)

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


def read_records(root: Path) -> dict[str, dict | None]:
    """Every authority record, parsed independently. `None` marks one that could not be parsed.

    A corrupt record becomes a None ENTRY rather than a missing key, because "this file exists and
    I cannot read it" and "this file is not there" are different facts, and every caller that checks
    separation of duties needs to tell them apart (F14).
    """
    directory = Path(root) / AUTHORITY_DIR
    docs: dict[str, dict | None] = {}
    if not directory.is_dir():
        return docs
    for path in sorted(directory.glob("*.yaml")):
        try:
            docs[str(path)] = continuity.parse_strict(path.read_text(encoding="utf-8"))
        except continuity.ContinuityError:
            docs[str(path)] = None
    return docs


def validate_all(root: Path, now: datetime | None = None) -> dict:
    """Whole-directory validation, for the hook and the CLI.

    Reports two different questions separately, because they have different answers and only one of
    them gates action:

        ok          is every record in the directory valid, including CLOSED history?
        active_ok   is the record that currently confers authority valid?

    Append-only history means a record that was invalid when it was written STAYS invalid and stays
    visible. Rewriting it to make this command green would destroy the evidence the check exists to
    surface. So `ok` may be false forever while `active_ok` is true — and it is `active_ok` that
    answers "may I act". The distinction is reported, never used to suppress a finding.
    """
    root = Path(root)
    directory = root / AUTHORITY_DIR
    out: dict = {"ok": True, "errors": {}, "active_ok": True, "active_errors": {},
                 "blocked": False, "checks_not_completed": []}
    if not directory.is_dir():
        return out
    docs = {}
    for path in sorted(directory.glob("*.yaml")):
        try:
            docs[str(path)] = continuity.parse_strict(path.read_text(encoding="utf-8"))
        except continuity.ContinuityError as exc:
            out["ok"] = False
            out["errors"][str(path.relative_to(root))] = [f"unparseable: {exc}"]
            docs[str(path)] = None
            out["blocked"] = True
    for path, doc in docs.items():
        if doc is None:
            continue
        siblings = {p: d for p, d in docs.items() if p != path}
        rel = str(Path(path).relative_to(root))
        errors = validate_document(doc, root, siblings, path, rel_path=rel, now=now)
        if out["blocked"]:
            out["checks_not_completed"] += [f"{rel}: {c}" for c in incomplete_checks(doc, siblings)]
        if errors:
            out["ok"] = False
            out["errors"].setdefault(rel, []).extend(errors)
            if str(doc.get("status", "")).upper() == "ACTIVE":
                out["active_ok"] = False
                out["active_errors"].setdefault(rel, []).extend(errors)
    if out["blocked"]:
        out["active_ok"] = False
    return out


def validate_paths(root: Path, rel_paths, now: datetime | None = None) -> dict:
    """Validate only the named records — what the pre-commit hook needs.

    The hook guards the GATE, not the archive. Validating the whole directory there would mean an
    invalid record already in append-only history blocks every future commit forever, and the only
    ways out are rewriting history or `--no-verify`: one destroys evidence, the other trains people
    to bypass the control. Judging the records the commit actually touches keeps prevention real
    and keeps history honest.
    """
    root = Path(root)
    out: dict = {"ok": True, "errors": {}, "checked": []}
    docs, _ = _sibling_docs_and_errors(root)
    for rel in rel_paths:
        path = root / rel
        out["checked"].append(str(rel))
        if not path.is_file():
            continue                        # a deletion; nothing to validate into history
        try:
            doc = continuity.parse_strict(path.read_text(encoding="utf-8"))
        except continuity.ContinuityError as exc:
            out["ok"] = False
            out["errors"][str(rel)] = [f"unparseable: {exc}"]
            continue
        siblings = {p: d for p, d in docs.items() if Path(p) != path}
        errors = validate_document(doc, root, siblings, str(path), rel_path=str(rel), now=now)
        blocked = incomplete_checks(doc, siblings)
        if blocked:
            out["ok"] = False
            out["errors"].setdefault(str(rel), []).extend(
                errors + [f"AUTHORITY_RESOLUTION_BLOCKED — {c}" for c in blocked])
        elif errors:
            out["ok"] = False
            out["errors"][str(rel)] = errors
    return out


#: Honest statement of what is and is not prevented. Quoted by the CLI rather than paraphrased.
ENFORCEMENT_TRUTH = {
    "supported authority writer (authority.write_record)": "ENFORCED",
    "project-owned pre-commit hook, when installed": "ENFORCED",
    "raw git commit outside the supported path": "NOT_GLOBALLY_PREVENTED",
}


def enforcement_truth(root: Path) -> dict[str, str]:
    """ENFORCEMENT_TRUTH with the hook row resolved against THIS repository's actual state.

    independent Assurance finding F23. The static row says "when installed → ENFORCED". Every word of that is true and it
    left the reader to discover the precondition for themselves — on the repository where authority
    records were actually being written, the hook was NOT installed, so the honest-sounding row
    described protection that was not there. A conditional guarantee must report whether its
    condition holds, or it is an advertisement.
    """
    from . import hooks as hooks_mod

    truth = dict(ENFORCEMENT_TRUTH)
    try:
        state = hooks_mod.status(root)
    except Exception as exc:                               # pragma: no cover - defensive
        truth["project-owned pre-commit hook, when installed"] = (
            f"ENFORCED WHEN INSTALLED — state undetermined ({exc})")
        return truth

    if state.commissioned:
        truth["project-owned pre-commit hook, when installed"] = (
            f"ENFORCED — commissioned here via core.hooksPath={state.hooks_path}")
    else:
        truth["project-owned pre-commit hook, when installed"] = (
            f"NOT COMMISSIONED HERE ({state.status}) — prevention on this repository is currently "
            "nil; detection is unaffected")
    return truth
