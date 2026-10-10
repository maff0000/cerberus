"""Independent Assurance finding U3-2 — attestation content is a claim; the commit that
introduced it is evidence.

THE DEFECT. PBGv2 accepted a self-declared executor identity from an attestation sitting in the
correct lawful path, without ever verifying the provenance of the commit that introduced it.
`git_author_of` was called exactly once, from `git_author_disagreement`, on the CANDIDATE commit. No
control anywhere examined the committing identity of an ATTESTATION file. And the repository's own
history contains Assurance verdicts committed under the identity of a party this cycle excludes from
Assurance — so the disclosure claiming "commit attribution" as a live compensating defence was
describing something that did not exist.

THE DOCTRINE:

    Attestation content is a claim. Commit provenance is evidence. Neither alone is sufficient where
    executor separation is security-critical.

GIT AUTHOR IS NOT TRUTH, AND THIS MODULE NEVER TREATS IT AS TRUTH. `git -c user.name=...` sets it to
any string. It is ONE INPUT, combined with three others and never trusted alone:

    authority-bound instance   the authority record grants the seat (see `authority_binding`)
    seat-start attestation     the seat was lawfully occupied before anything was implemented
    introducing-commit         which commit first added this blob, by whom, and is it still that blob
    spawn ancestry             a record committed BEFORE the instance existed, minting its identity

THE CONFIDENCE LADDER. Every attestation gets a LABEL, and the label is the product. Nothing is
silently invalidated and nothing is silently upgraded:

    CONTENT_ONLY_LEGACY            the file's introducing commit cannot be established at all. The
                                   content is the only evidence there is. READABLE, LABELLED, and
                                   never sufficient for a new internal cycle.
    COMMIT_ATTRIBUTED              an introducing commit is established, the blob is unchanged since
                                   it, and it was introduced after its authority existed. This is
                                   the level the transitional external-dispatch history sits at, and
                                   it remains LAWFUL for that history.
    SPAWN_BOUND                    additionally, a spawn record committed BEFORE the introducing
                                   commit mints this exact instance identity for this exact seat.
                                   The instance could not have chosen its own name.
    AUTHORITY_AND_SPAWN_VERIFIED   additionally, the authority grants the seat AND the introducing
                                   commit's own attribution matches the identity that spawn record
                                   assigned. The strongest level available without cryptographic
                                   signing, which PBGv2 does not have and this module does not
                                   pretend to.

WHY LEGACY EVIDENCE SURVIVES. The transitional model — an EXTERNAL executor, dispatched manually,
with no spawn record because no spawn machinery existed — was lawful when it was written and stays
lawful. Retroactively invalidating it would destroy the append-only history that is one of the two
defences that DOES exist. `required_level_for` reads the AUTHORITY's own declared actor class to
decide which standard applies, so the rule is a property of the cycle rather than of the calendar.

NO PERSONA DEPENDENCY — THIS IS A HARD REQUIREMENT AND NOT A STYLE PREFERENCE. No persona, vendor,
model or human name appears anywhere in this module, and none may be added. A confidence model that
works because it recognises a particular executor string has reintroduced the exact coupling the
closed system exists to remove. Every comparison here is between values read out of records at run
time; the only literals are field names and level names.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from . import validation as vld

# --- the ladder, weakest first. Order is meaningful and `rank` is derived from it. ---------------- #

CONTENT_ONLY_LEGACY = "CONTENT_ONLY_LEGACY"
COMMIT_ATTRIBUTED = "COMMIT_ATTRIBUTED"
SPAWN_BOUND = "SPAWN_BOUND"
AUTHORITY_AND_SPAWN_VERIFIED = "AUTHORITY_AND_SPAWN_VERIFIED"

LEVELS = (CONTENT_ONLY_LEGACY, COMMIT_ATTRIBUTED, SPAWN_BOUND, AUTHORITY_AND_SPAWN_VERIFIED)

#: The only level that may establish internal PBGv2 seat occupancy for a NEW internal cycle.
STRONGEST = AUTHORITY_AND_SPAWN_VERIFIED

#: How an authority declares that its seat is occupied by an agent instance PBGv2 itself created,
#: rather than by an externally dispatched party. Generic by construction: it is a prefix on the
#: record's own `actor_id`, which is already required to be a GENERIC seat-occupant class.
INTERNAL_ACTOR_PREFIX = "INTERNAL_"

#: Where a Project Lead spawn record for a work item is looked for. Read-only, and read TOLERANTLY:
#: PBGv2 has no spawn-record schema and this module does not invent one (that is FWK-OBS-007, which
#: is explicitly not in this lane). It reads the fields if they are there and reports the level it
#: can justify if they are not.
SPAWN_ROOT = "evidence/governance"
SPAWN_GLOB = "*spawn*.y*ml"

#: The field a spawn record uses to mint an instance identity, and the seat it mints it for.
SPAWN_INSTANCE_FIELD = "internal_agent_instance_id"
SPAWN_SEAT_FIELDS = ("generic_seat", "seat_id")
SPAWN_IDENTITY_FIELD = "commit_identity_assigned"


def rank(level: str) -> int:
    return LEVELS.index(level) if level in LEVELS else -1


def _text(value) -> str:
    return str(value or "").strip()


def _same(left, right) -> bool:
    return _text(left).casefold() == _text(right).casefold()


# --- what the repository can be asked about a file ------------------------------------------------ #

@dataclass(frozen=True)
class CommitProvenance:
    """The introducing commit of one governed file, and what it can and cannot show."""
    rel_path: str
    commit: str | None = None
    author_name: str | None = None
    author_email: str | None = None
    committer_name: str | None = None
    committer_email: str | None = None
    committed_utc: str | None = None
    blob: str | None = None
    working_blob: str | None = None
    add_commits: tuple = ()

    @property
    def known(self) -> bool:
        return bool(self.commit)

    @property
    def blob_rewritten(self) -> bool:
        """The bytes on disk are not the bytes the introducing commit added.

        A copied or edited attestation does NOT inherit the original's provenance. Without this the
        strongest claim in the ladder could be earned by taking a lawful file and changing what it
        says.
        """
        return bool(self.blob and self.working_blob and self.blob != self.working_blob)

    @property
    def replayed(self) -> bool:
        """More than one commit ADDS this path — cherry-pick, revert-and-readd, or a replay."""
        return len(self.add_commits) > 1


def _git(root: Path, *args: str) -> tuple[int, str]:
    from .authority import _git as run                        # one git accessor for the package

    return run(Path(root), *args)


def repository_available(root: Path) -> bool:
    """Does this tree have a commit history that provenance could be read from at all?

    THE DISTINCTION THAT KEEPS THIS HONEST, and it is not a loophole:

        a tree with history, and an artefact absent from it   the artefact is UNCOMMITTED. That is a
                                                              real deficiency in real evidence and it
                                                              is reported.
        a tree with NO history at all                         provenance is not a question that can
                                                              be asked here. Reporting a deficiency
                                                              would be reporting the absence of an
                                                              evidence CLASS as though it were the
                                                              absence of a FACT.

    A governed project necessarily has history — durable evidence means committed evidence — so this
    is False only for a scratch tree or a test fixture, where there is nothing to weaken.
    """
    code, out = _git(Path(root), "rev-parse", "--verify", "HEAD")
    return code == 0 and bool(out.strip())


#: Per-process memo for the IMMUTABLE half only: which commit introduced a path, who it is
#: attributed to, and what blob it carried. Those are facts about committed history and they cannot
#: change while the process runs without a commit happening.
#:
#: THE WORKING BLOB IS DELIBERATELY NOT CACHED, AND THAT IS THE POINT. Caching it produced a control
#: that could return a verdict for bytes that had since changed — a provenance model whose answer
#: depends on process-local cache state, in the one place that must not be foolable. It cost a
#: single `git hash-object` per assessment to remove that property, so it is removed rather than
#: mitigated by asking every caller to remember to reset something.
_HISTORY_CACHE: dict[tuple, tuple] = {}
_BINDING_CACHE: dict[tuple, tuple] = {}


def reset_caches() -> None:
    """Drop the memo. Correctness never depends on this being called; only speed does."""
    _HISTORY_CACHE.clear()
    _BINDING_CACHE.clear()


def _signature(paths) -> tuple:
    """A cheap identity for a set of files: path, size and mtime. Any edit changes it."""
    out = []
    for path in sorted(paths):
        try:
            stat = Path(path).stat()
            out.append((str(path), stat.st_size, stat.st_mtime_ns))
        except OSError:                                        # pragma: no cover - defensive
            out.append((str(path), None, None))
    return tuple(out)


def commit_provenance(root: Path, rel_path: str) -> CommitProvenance:
    """Which commit introduced `rel_path`, by whom, and whether it is still the same bytes.

    Never raises and never guesses. A path that git knows nothing about comes back with
    `known == False`, which is a labelled absence and is exactly what CONTENT_ONLY_LEGACY means.
    """
    root = Path(root)
    key = (str(root.resolve()), str(rel_path))
    if key not in _HISTORY_CACHE:
        _HISTORY_CACHE[key] = _committed_history(root, rel_path)
    add_commits, introducing, meta, blob = _HISTORY_CACHE[key]
    if not add_commits:
        return CommitProvenance(rel_path)
    return CommitProvenance(
        rel_path, introducing, meta[0] or None, meta[1] or None, meta[2] or None, meta[3] or None,
        meta[4] or None, blob, _working_blob(root, rel_path), add_commits)


def _working_blob(root: Path, rel_path: str) -> str | None:
    """The hash of the bytes ON DISK, read fresh EVERY time. Never memoised."""
    target = Path(root) / rel_path
    if not target.is_file():
        return None
    code, out = _git(Path(root), "hash-object", "--", str(target))
    return out.strip() if code == 0 else None


def _committed_history(root: Path, rel_path: str) -> tuple:
    """The part of a file's provenance that COMMITTED HISTORY fixes, and which cannot drift.

    Returns `(add_commits, introducing, meta, blob)`. The working blob is deliberately absent — it
    is the only mutable half and it is read fresh on every assessment.
    """
    code, adds = _git(root, "log", "--diff-filter=A", "--format=%H", "--", rel_path)
    add_commits = tuple(line.strip() for line in adds.splitlines() if line.strip()) if code == 0 \
        else ()
    if not add_commits:
        return (), None, ("", "", "", "", ""), None

    # The EARLIEST add is the introduction; a later one is a replay and is reported as such.
    introducing = add_commits[-1]
    code, meta = _git(root, "show", "-s", "--format=%an%x1f%ae%x1f%cn%x1f%ce%x1f%cI", introducing)
    parts = meta.split("\x1f") if code == 0 else []
    parts += [""] * (5 - len(parts))

    code, blob = _git(root, "rev-parse", f"{introducing}:{rel_path}")
    return add_commits, introducing, tuple(parts[:5]), (blob.strip() if code == 0 else None)


# --- spawn records: read as EVIDENCE, never as authority ------------------------------------------ #

@dataclass(frozen=True)
class SpawnBinding:
    """A committed statement that a named instance identity was minted for a named seat."""
    rel_path: str
    instance_id: str
    seat_id: str | None = None
    work_item: str | None = None
    authority_id: str | None = None
    assigned_identity: str | None = None
    commit: str | None = None
    committed_utc: str | None = None


def read_spawn_bindings(root: Path) -> tuple[list[SpawnBinding], list[vld.ValidationFinding]]:
    """Every readable spawn record's instance-to-seat binding, and the ones that would not read.

    TOLERANT BY DESIGN. There is no governed spawn-record schema in PBGv2 and building one is
    FWK-OBS-007, which is out of this lane. A record missing the fields below simply binds nothing;
    it is not a defect in the record and it is not a reason to fail a cycle that never claimed to be
    spawn-bound. What it does mean is that the strongest level cannot be reached — an absence of
    evidence lowers a label, it never raises one.
    """
    root = Path(root)
    base = root / SPAWN_ROOT
    present = sorted(base.rglob(SPAWN_GLOB)) if base.is_dir() else []
    # Keyed on the FILE SIGNATURES, not just the root: an edited, added or removed spawn record
    # changes the key, so the memo cannot answer for bytes that are no longer there. A cache that
    # can go stale under a control this one supports is not a speed-up, it is a defect.
    key = (str(root.resolve()), _signature(present))
    if key in _BINDING_CACHE:
        cached = _BINDING_CACHE[key]
        return list(cached[0]), list(cached[1])

    bindings: list[SpawnBinding] = []
    findings: list[vld.ValidationFinding] = []
    if not present:
        _BINDING_CACHE[key] = ((), ())
        return bindings, findings

    for path in present:
        try:
            rel = str(path.resolve().relative_to(root.resolve()))
        except ValueError:
            findings.append(vld.ValidationFinding(
                vld.PATH_CONTAINMENT, "OUTSIDE_ROOT", str(path),
                detail="a spawn record resolving outside PROJECT_ROOT binds nothing here"))
            continue
        doc, problems = vld.load_governed_mapping(path, root=root, path_label=rel)
        if problems:
            findings.extend(problems)
            continue
        instance = _text(doc.get(SPAWN_INSTANCE_FIELD))
        if not instance:
            continue                                          # not an instance-minting record
        seat = next((_text(doc.get(f)) for f in SPAWN_SEAT_FIELDS if _text(doc.get(f))), None)
        introduced = commit_provenance(root, rel)
        bindings.append(SpawnBinding(
            rel, instance, seat, _text(doc.get("work_item")) or None,
            _text(doc.get("authority_id")) or None,
            _text(doc.get(SPAWN_IDENTITY_FIELD)) or None,
            introduced.commit, introduced.committed_utc))
    _BINDING_CACHE[key] = (tuple(bindings), tuple(findings))
    return bindings, findings


# --- the assessment ------------------------------------------------------------------------------- #

@dataclass
class ProvenanceAssessment:
    """One attestation's provenance, its confidence level, and every reason for that level."""
    rel_path: str
    level: str = CONTENT_ONLY_LEGACY
    #: False when the tree carries no commit history at all, so provenance is UNDETERMINABLE rather
    #: than DEFICIENT. `sufficiency_findings` declines to fault an assessment it could not make.
    determinable: bool = True
    executor_id: str | None = None
    seat_id: str | None = None
    authority_id: str | None = None
    work_item: str | None = None
    candidate: str | None = None
    commit: CommitProvenance | None = None
    binding: SpawnBinding | None = None
    reasons: list[str] = field(default_factory=list)
    findings: list[vld.ValidationFinding] = field(default_factory=list)

    def at_least(self, required: str) -> bool:
        return rank(self.level) >= rank(required)

    def render(self) -> str:
        lines = [f"{self.rel_path}: {self.level}"]
        if self.commit and self.commit.known:
            lines.append(f"  introduced  {self.commit.commit[:12]} by "
                         f"{self.commit.author_name} <{self.commit.author_email}> "
                         f"(committer {self.commit.committer_name})")
        else:
            lines.append("  introduced  <no committed introduction found>")
        if self.binding:
            lines.append(f"  spawn-bound {self.binding.rel_path} mints {self.binding.instance_id}")
        lines += [f"  - {r}" for r in self.reasons]
        lines += [f"  - {f.render()}" for f in self.findings]
        return "\n".join(lines)


def _identity_matches(assigned: str, provenance: CommitProvenance) -> bool:
    """Does the introducing commit's own attribution match the identity the spawn record assigned?

    GENERIC MATCHING, and deliberately forgiving of format rather than of substance. A spawn record
    writes an identity the way git writes one — `Name <email>` — so the email is compared when both
    carry one, and the name otherwise. What is NEVER done is recognising a particular party: the
    expected value arrives from the committed spawn record at run time and this function has no
    opinion about what it should say.
    """
    assigned = _text(assigned)
    if not assigned:
        return False
    emails = re.findall(r"<([^>]+)>", assigned)
    if emails:
        return any(_same(e, provenance.author_email) or _same(e, provenance.committer_email)
                   for e in emails)
    name = assigned.strip()
    return _same(name, provenance.author_name) or _same(name, provenance.committer_name)


def assess(root: Path, doc: dict, rel_path: str, *, records: dict | None = None,
           bindings: list[SpawnBinding] | None = None,
           authority_commit: str | None = None) -> ProvenanceAssessment:
    """Label one attestation with the strongest confidence level its evidence actually justifies.

    Every step can only ever HOLD or LOWER the level. There is no branch that raises it on a weaker
    input, which is what "never silently upgraded" has to mean in code rather than in prose.
    """
    root = Path(root)
    result = ProvenanceAssessment(
        rel_path,
        executor_id=_text(doc.get("external_executor_id")) or None,
        seat_id=_text(doc.get("seat_id")) or None,
        authority_id=_text(doc.get("authority_id")) or None,
        work_item=_text(doc.get("work_item")) or None,
        candidate=_text(doc.get("produced_candidate")) or None)

    # --- introducing commit ----------------------------------------------------------------------- #
    result.determinable = repository_available(root)
    result.commit = commit_provenance(root, rel_path)
    if not result.commit.known:
        result.reasons.append(
            "no committed introduction of this artefact could be established, so its content is the "
            "only evidence there is. Readable and labelled; never sufficient on its own"
            if result.determinable else
            "this tree carries no commit history, so commit provenance is not a question that can "
            "be asked here. UNDETERMINABLE, which is not the same as deficient")
        return result

    if result.commit.blob_rewritten:
        result.findings.append(vld.ValidationFinding(
            vld.PROVENANCE, "BLOB_REWRITTEN", rel_path,
            detail=(f"was introduced by {result.commit.commit[:12]} carrying blob "
                    f"{result.commit.blob[:12]}, and the bytes on disk are "
                    f"{result.commit.working_blob[:12]}. A rewritten or copied artefact does NOT "
                    "inherit the original's provenance")))
        result.reasons.append("provenance held at content-only: the committed bytes and the "
                              "working bytes are different artefacts")
        return result

    if result.commit.replayed:
        result.findings.append(vld.ValidationFinding(
            vld.PROVENANCE, "REPLAYED_EVIDENCE", rel_path,
            detail=(f"is ADDED by {len(result.commit.add_commits)} distinct commits ("
                    + ", ".join(c[:12] for c in result.commit.add_commits)
                    + "). Cherry-picked or replayed evidence is diagnosed, not accepted: the same "
                      "statement introduced twice has two provenances and can only have one")))
        result.reasons.append("provenance held at content-only: the artefact has more than one "
                              "introduction and therefore no single one")
        return result

    if authority_commit:
        from . import authority as auth_mod
        try:
            after = auth_mod.is_ancestor(root, authority_commit, result.commit.commit)
        except Exception:                                     # pragma: no cover - defensive
            after = None
        if after is False:
            result.findings.append(vld.ValidationFinding(
                vld.PROVENANCE, "INTRODUCED_BEFORE_AUTHORITY", rel_path,
                detail=(f"was introduced by {result.commit.commit[:12]}, which does not descend "
                        f"from the commit that created its authority ({authority_commit[:12]}). An "
                        "attestation must be introduced AFTER the authority it claims to act "
                        "under")))
            result.reasons.append("provenance held at content-only: the artefact predates its own "
                                  "authority in the committed history")
            return result

    result.level = COMMIT_ATTRIBUTED
    result.reasons.append(
        f"introduced by {result.commit.commit[:12]}, attributed to "
        f"{result.commit.author_name} <{result.commit.author_email}>, blob unchanged since. Git "
        "attribution is configuration and is never truth on its own — it is one input among four")

    # --- spawn ancestry ---------------------------------------------------------------------------- #
    if bindings is None:
        bindings = read_spawn_bindings(root)[0]

    executor = result.executor_id
    for_seat = [b for b in bindings if result.seat_id and _same(b.seat_id, result.seat_id)]
    for_instance = [b for b in bindings if executor and _same(b.instance_id, executor)]

    if not for_seat and not for_instance:
        result.reasons.append(
            "no committed spawn record mints an instance identity for this seat, so the executor "
            "identity rests on the attestation's own content plus its commit attribution. That is "
            "the transitional model and it is preserved, not invalidated")
        return result

    conflicting = [b for b in for_seat if not _same(b.instance_id, executor)]
    if conflicting and not for_instance:
        result.findings.append(vld.ValidationFinding(
            vld.PROVENANCE, "SPAWN_INSTANCE_MISMATCH", rel_path, field="external_executor_id",
            detail=(f"names executor {executor!r} for seat {result.seat_id!r}, while the committed "
                    "spawn record(s) "
                    + ", ".join(f"{b.rel_path} mint {b.instance_id!r}" for b in conflicting)
                    + " for that seat. Another agent instance cannot introduce this seat's "
                      "attestation, and conflicting provenance fails closed")))
        result.reasons.append("provenance held at commit-attributed: the spawn record and the "
                              "attestation name different occupants of the same seat")
        return result

    binding = next((b for b in for_instance
                    if not result.seat_id or not b.seat_id or _same(b.seat_id, result.seat_id)),
                   None)
    if binding is None:
        result.findings.append(vld.ValidationFinding(
            vld.PROVENANCE, "SPAWN_SEAT_MISMATCH", rel_path, field="seat_id",
            detail=(f"names executor {executor!r}, whose committed spawn record binds it to a "
                    "different seat. An instance spawned for one seat cannot author another seat's "
                    "attestation")))
        result.reasons.append("provenance held at commit-attributed: the instance is bound to a "
                              "different seat")
        return result

    if binding.work_item and result.work_item and not _same(binding.work_item, result.work_item):
        result.findings.append(vld.ValidationFinding(
            vld.PROVENANCE, "SPAWN_WORK_ITEM_MISMATCH", rel_path, field="work_item",
            detail=(f"declares work_item {result.work_item!r}; the spawn record minting "
                    f"{binding.instance_id!r} names {binding.work_item!r}")))
        result.reasons.append("provenance held at commit-attributed: the spawn record governs a "
                              "different work item")
        return result

    # The spawn record must PREDATE the attestation it binds. A record written afterwards could
    # simply have copied whatever the attestation already said, which proves nothing at all.
    if binding.commit and result.commit.commit:
        from . import authority as auth_mod
        try:
            before = auth_mod.is_ancestor(root, binding.commit, result.commit.commit)
        except Exception:                                     # pragma: no cover - defensive
            before = None
        if before is False:
            result.findings.append(vld.ValidationFinding(
                vld.PROVENANCE, "SPAWN_RECORD_NOT_ANCESTRAL", rel_path,
                detail=(f"the spawn record minting {binding.instance_id!r} was introduced by "
                        f"{binding.commit[:12]}, which does not precede this attestation's "
                        f"introduction at {result.commit.commit[:12]}. An identity minted after "
                        "the fact is a transcription, not a binding")))
            result.reasons.append("provenance held at commit-attributed: the spawn record does not "
                                  "precede the attestation it claims to bind")
            return result

    result.binding = binding
    result.level = SPAWN_BOUND
    result.reasons.append(
        f"{binding.rel_path} mints {binding.instance_id} for this seat and was committed before "
        "this attestation was introduced, so the instance identity was not self-chosen")

    # --- authority + assigned commit identity ------------------------------------------------------ #
    granted = False
    if records is not None and result.authority_id:
        from . import authority_binding as ab
        _path, record, _unreadable = ab.find_record(records, result.authority_id)
        granted = bool(record) and not ab.findings_for(doc, rel_path, records)
    if not granted:
        result.reasons.append(
            "the referenced authority does not lawfully grant this seat as evaluated here, or no "
            "authority records were supplied, so the strongest level is not reached")
        return result

    if binding.assigned_identity and not _identity_matches(binding.assigned_identity, result.commit):
        result.findings.append(vld.ValidationFinding(
            vld.PROVENANCE, "COMMIT_IDENTITY_NOT_AS_ASSIGNED", rel_path,
            detail=(f"was introduced by {result.commit.commit[:12]} attributed to "
                    f"{result.commit.author_name} <{result.commit.author_email}>, while the spawn "
                    f"record assigns {binding.assigned_identity!r} to this seat. The two disagree, "
                    "so the introduction cannot be shown to be this instance's own")))
        result.reasons.append("provenance held at spawn-bound: the introducing commit's "
                              "attribution is not the identity assigned to this seat")
        return result

    result.level = AUTHORITY_AND_SPAWN_VERIFIED
    result.reasons.append(
        "the authority grants this seat, the spawn record mints this instance for it, the "
        "introducing commit carries the identity that record assigned, and the blob is unchanged "
        "since. Four independent inputs agree")
    return result


# --- which standard applies to which cycle -------------------------------------------------------- #

def required_level_for(record: dict | None) -> str:
    """The weakest level that may establish seat occupancy under this authority record.

    THE DISCRIMINATOR IS THE RECORD'S OWN `actor_id`, and that is deliberate. A cycle whose seat is
    occupied by an agent instance PBGv2 itself created must meet the strongest standard, because the
    spawn evidence exists and there is no excuse for it to be absent. A cycle dispatched under the
    earlier transitional model has no spawn record to offer and never claimed one; holding it to a
    standard that did not exist when it was written would invalidate lawful history to flatter a
    control, which is the opposite of what append-only history is for.

    Read off the record, generic, and with no calendar, no version pin and no name in sight.
    """
    if not isinstance(record, dict):
        return COMMIT_ATTRIBUTED
    actor = _text(record.get("actor_id")).upper()
    return STRONGEST if actor.startswith(INTERNAL_ACTOR_PREFIX) else COMMIT_ATTRIBUTED


def sufficiency_findings(assessment: ProvenanceAssessment, record: dict | None
                         ) -> list[vld.ValidationFinding]:
    """Whether this assessment meets the standard its own authority requires.

    Weaker levels stay READABLE for historical evidence — this returns findings, not a deletion —
    and only the strongest level may establish occupancy for a new internal cycle.
    """
    if not assessment.determinable:
        return []
    required = required_level_for(record)
    if assessment.at_least(required):
        return []
    why = ("the authority governing this seat declares an internally instantiated occupant"
           if required == STRONGEST else
           "durable evidence means committed evidence, and every cycle must reach at least")
    return [vld.ValidationFinding(
        vld.PROVENANCE, "PROVENANCE_BELOW_REQUIRED_LEVEL", assessment.rel_path,
        detail=(f"is established at {assessment.level}, and {why} {required}. Weaker levels remain "
                "readable for historical evidence and are never silently upgraded; they cannot "
                "establish occupancy for a cycle that should have produced the stronger "
                "evidence"))]
