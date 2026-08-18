"""Executor identity, and a separation-of-duties check that can actually fail (SOD-TOOLING-0001).

THE ORIGINAL DEFECT. PBG-SOD-001 is non-waivable: whoever implements a candidate may not assure it.
Its only executing comparison read `actor_id` off an ASSURANCE record and compared it with `actor_id`
on the sibling ENGINEER record that produced the same candidate. That worked while actor_ids were
named parties. It stopped working the moment PBGv2 became a genuinely closed system, because the
closed system requires GENERIC internal identities — and

    EXTERNAL_AUDITOR != EXTERNAL_ENGINEER

is true for every record that will ever exist. The check ran, passed, and proved nothing.

THE RESOLUTION is not to put the executor back into the authority. Generic seats are the point: an
executor must be substitutable without amending a record, a role model or a candidate. So identity
is split into two things that were previously one, and only one of them grants:

    assigned_role, seat_id      INTERNAL. Authoritative. Generic. Decides what may be done.
    external_executor_id        EXTERNAL. Non-authoritative. Named. Decides whether two seats were
                                occupied by the same party.

WHAT COUNTS AS A FACT, and why the ranking matters:

    ATTESTED     a committed seat attestation naming the executor. The only conclusive source.
    ADVISORY     external_execution.intended_executor on the authority. Corroborates; never
                 establishes. It is declared non-authoritative in the record itself, and a control
                 that promoted it would be taking authority from a field that disclaims it.
    GIT_AUTHOR   the candidate commit's author. Never conclusive: `git -c user.name=…` sets it to
                 any string, so it is evidence of configuration, not of identity. A-6: it is now
                 CONSULTED — as a declared diagnostic that can only ever REPORT a disagreement —
                 rather than sitting as a documented tier with no reader.

AND THE RULE THAT MAKES IT NON-VACUOUS: a fact that cannot be established is a reason to REFUSE.
Missing executor identity returns NOT_VERIFIED or FAIL. It never returns PASS.

--------------------------------------------------------------------------------------------------
A-1 AND A-2. Independent Assurance then found that "established" was doing less work than it looked.
Both resolvers took the FIRST match by sorted evidence path, across the entire evidence tree, with
no conflict detection, no work-item scope and no ownership boundary. `evidence/assurance/…` sorts
before `evidence/engineer/…`, so ONE file written inside an auditor's own authorised evidence path
preempted the true delivery record and this control returned PASS for a seat auditing its own
candidate — no code touched, no governance record altered.

Every candidate-to-executor resolution path in this module now goes through
`evidence_resolution.resolve_unique`, which enumerates rather than short-circuits, bounds each
artefact to the evidence area its role may lawfully write, reconciles agreeing duplicates
explicitly, and REFUSES when two readable records disagree. Path order still makes the report
deterministic; it no longer makes anything true.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import authority_binding as ab
from . import evidence_resolution as er
from . import provenance as prov

ASSURANCE_ROLE = "ASSURANCE_ENGINEER"
ENGINEER_ROLE = "ENGINEER"

#: Evidence roots searched for attestations. PROJECT_ROOT-relative, never a parent (F19/F21).
ATTESTATION_ROOT = er.EVIDENCE_ROOT
ATTESTATION_GLOB = "**/*attestation*.yaml"

SEAT_START = "SEAT_START"
SEAT_DELIVERY = "SEAT_DELIVERY"

# Sources of an executor fact, most to least conclusive.
ATTESTED = "ATTESTED"
ADVISORY = "ADVISORY"
GIT_AUTHOR = "GIT_AUTHOR"

#: The ONLY source that establishes an executor. Stated as a set so that a mutation which adds
#: ADVISORY or GIT_AUTHOR to it is a one-line, obvious, and TESTED weakening.
CONCLUSIVE_SOURCES = {ATTESTED}

PASS = "PASS"
FAIL = "FAIL"
NOT_VERIFIED = "NOT_VERIFIED"

#: The fields that MAKE a seat-start fact. Two attestations agreeing on all of these are one fact
#: recorded twice; two that differ on any of them are two contradictory facts.
SEAT_START_IDENTITY = ("external_executor_id", "authority_id", "assigned_role", "seat_id",
                       "work_item")

#: The fields that MAKE a delivery fact. `work_item` is here on purpose: one commit cannot have been
#: produced by two work items, so an evidence pack copied between them is a conflict, not a choice.
SEAT_DELIVERY_IDENTITY = ("external_executor_id", "authority_id", "assigned_role", "seat_id",
                          "work_item", "produced_candidate")


@dataclass(frozen=True)
class ExecutorFact:
    """Who occupied a seat, where that is recorded, and how strong the recording is."""
    executor_id: str | None
    source: str
    seat_id: str | None = None
    authority_id: str | None = None
    role: str | None = None
    evidence: str | None = None

    @property
    def established(self) -> bool:
        """A named executor from a conclusive source. Anything else is a lead, not a fact."""
        return bool(self.executor_id) and self.source in CONCLUSIVE_SOURCES

    def render(self) -> str:
        who = self.executor_id or "<unrecorded>"
        return f"{who} [{self.source}{'' if not self.evidence else ' ' + self.evidence}]"


@dataclass
class FactLookup:
    """An executor fact together with the resolution that produced it.

    Returned as a pair because the resolution carries what the fact alone cannot: which artefacts
    were considered, which were excluded and why, and whether anything conflicted. A caller that
    took only the fact would rebuild the silence this repair exists to remove.
    """
    fact: ExecutorFact | None
    resolution: er.Resolution

    @property
    def conflicted(self) -> bool:
        return self.resolution.conflicted


@dataclass
class SeparationResult:
    status: str
    detail: str
    candidate: str | None = None
    implementer: ExecutorFact | None = None
    auditor: ExecutorFact | None = None
    findings: list[str] = field(default_factory=list)
    resolutions: list[er.Resolution] = field(default_factory=list)
    #: Placement Question B. True when the ONLY reason this is not a pass is that the seat has not
    #: yet been occupied — a question that cannot be answered when the authority is created. The
    #: status stays FAIL, because the control has not been satisfied; the flag lets the validator
    #: distinguish NOT-YET from NO instead of refusing to write a record that demands an
    #: attestation. `seat.lifecycle` decides whether NOT-YET is still true.
    awaiting_attestation: bool = False

    @property
    def passed(self) -> bool:
        return self.status == PASS

    def render(self) -> str:
        lines = [f"PBG-SOD-001 separation of duties: {self.status}", f"  {self.detail}"]
        if self.candidate:
            lines.append(f"  candidate   {self.candidate[:12]}")
        lines.append(f"  implementer {self.implementer.render() if self.implementer else '<none>'}")
        lines.append(f"  auditor     {self.auditor.render() if self.auditor else '<none>'}")
        lines += [f"  - {f}" for f in self.findings]
        # A-1: conflicts are NAMED in human-readable output, not only under --json.
        for resolution in self.resolutions:
            if resolution.conflicted or resolution.findings or resolution.excluded:
                lines += ["  " + line for line in resolution.render().splitlines()]
        return "\n".join(lines)


# --------------------------------------------------------------------------------------------- #
# Reading durable executor facts
# --------------------------------------------------------------------------------------------- #

def attestation_sources(root: Path) -> tuple[list[er.Source], list[str]]:
    """Every seat attestation inside PROJECT_ROOT, and the ones that could not be read."""
    return er.read_sources(root, ATTESTATION_GLOB, subdir=ATTESTATION_ROOT,
                           required_key="attestation_type")


def read_attestations(root: Path) -> tuple[list[dict], list[str]]:
    """Backwards-compatible view: the parsed documents, each carrying its `_path`."""
    sources, unreadable = attestation_sources(root)
    records = []
    for source in sources:
        doc = dict(source.doc)
        doc["_path"] = source.rel_path
        records.append(doc)
    return records, unreadable


def _sources(root: Path, sources: list[er.Source] | None) -> list[er.Source]:
    if sources is not None:
        return sources
    found, _ = attestation_sources(root)
    return found


def _schema(root: Path) -> dict | None:
    """The governed attestation schema, cached per root.

    Returning None would mean "admit everything", which is the failure mode this repair exists to
    remove — so callers treat a missing schema as a refusal, and `schema_unavailable` reports it.
    """
    key = str(Path(root).resolve())
    if key not in _SCHEMA_CACHE:
        schema, problems = er.attestation_schema(root)
        _SCHEMA_CACHE[key] = (schema, problems)
    return _SCHEMA_CACHE[key][0]


def schema_unavailable(root: Path) -> list[str]:
    """Why no artefact can be schema-validated here, if that is the case. Empty when all is well."""
    _schema(root)
    return _SCHEMA_CACHE[str(Path(root).resolve())][1]


_SCHEMA_CACHE: dict[str, tuple[dict | None, list[str]]] = {}


def _records(root: Path, siblings: dict | None) -> dict | None:
    """THE FULL durable authority record set, never a caller-assembled subset.

    THIS DISTINCTION IS LOAD-BEARING. `siblings` means "every OTHER record" — `authority.validate_all`
    builds it by excluding the record currently under evaluation. An authority gate handed that set
    would report a record's own attestation as citing an authority that does not exist, which is
    both wrong and exactly the kind of confident false refusal that erodes trust in a control.

    Trusted context comes from the durable records on disk. The caller's set is merged ON TOP so a
    caller holding a parsed view (including the `None` entries that mark unparseable records) still
    contributes what it knows, but it can never be the reason a real record is invisible.

    Returns None ONLY when the records genuinely cannot be read at all, which the gate reports as
    AUTHORITY_RECORDS_UNAVAILABLE and fails closed on.
    """
    from . import authority as auth_mod
    try:
        on_disk = auth_mod.read_records(root)
    except Exception:                                          # pragma: no cover - defensive
        on_disk = None
    if siblings is None:
        return on_disk
    merged = dict(on_disk or {})
    merged.update(siblings)
    return merged


def _record_for(records: dict | None, authority_id: str | None) -> dict | None:
    if not authority_id or records is None:
        return None
    return ab.find_record(records, str(authority_id))[1]


def _provenance_gate(root: Path, records: dict | None):
    """independent Assurance finding U3-2's gate: the commit that introduced an artefact must support what it claims.

    ONLY EVER LOWERS TRUST. It emits findings for provenance that actively CONTRADICTS the artefact
    — a rewritten blob, a replayed introduction, a spawn record binding this seat to a different
    instance — and, for a cycle whose own authority declares an internally instantiated occupant,
    for evidence that falls below the level that cycle should have produced.

    It does NOT exclude legacy evidence for being legacy. The transitional external-dispatch history
    has no spawn record because no spawn machinery existed, and `provenance.required_level_for`
    reads the authority's own actor class rather than a date, so that history stays lawful and
    labelled instead of being retroactively destroyed.
    """
    if not prov.repository_available(root):
        # No commit history exists here at all, so there is no provenance to read. Returning a
        # no-op gate is honest about that: the assessment would be UNDETERMINABLE for every
        # artefact and would fault none of them, and running it anyway would only spend git calls
        # to reach that conclusion one artefact at a time.
        return None

    bindings, binding_findings = prov.read_spawn_bindings(root)

    def _gate(source):
        record = _record_for(records, source.doc.get("authority_id"))
        assessment = prov.assess(root, source.doc, source.rel_path, records=records,
                                 bindings=bindings)
        return [*binding_findings, *assessment.findings,
                *prov.sufficiency_findings(assessment, record)]

    return _gate


def provenance_labels(root: Path, lookups, siblings: dict | None = None) -> list[str]:
    """The confidence level of every artefact these lookups actually SELECTED (independent Assurance finding U3-2).

    Reported, never decisive. A level that contradicts an artefact has already excluded it at the
    PROVENANCE stage; this is the positive half — so a reader can see that a fact rests on
    CONTENT_ONLY_LEGACY rather than AUTHORITY_AND_SPAWN_VERIFIED, and weigh it accordingly.
    """
    root = Path(root)
    if not prov.repository_available(root):
        return []
    records = _records(root, siblings)
    bindings = prov.read_spawn_bindings(root)[0]
    out: list[str] = []
    for lookup in lookups:
        selected = getattr(lookup.resolution, "selected", None)
        if selected is None:
            continue
        assessment = prov.assess(root, selected.doc, selected.rel_path, records=records,
                                 bindings=bindings)
        required = prov.required_level_for(
            _record_for(records, selected.doc.get("authority_id")))
        out.append(
            f"attestation provenance — {selected.rel_path}: {assessment.level} "
            f"(this cycle requires {required}). Commit provenance is evidence and attestation "
            "content is a claim; neither is sufficient alone, and Git authorship on its own is "
            "configuration rather than identity")
    return out


def _role_of_authority(root: Path, authority_id: str | None, siblings: dict | None) -> str | None:
    """The role the AUTHORITY RECORD assigns to this seat — trusted context, not artefact content.

    Returns None when the authority cannot be located, and None means "unconstrained by this
    particular expectation". It never means "the artefact may decide": the role is still mandatory
    and the declared-role-versus-declared-area gate still runs.
    """
    if not authority_id:
        return None
    records = siblings
    if records is None:
        from . import authority as auth_mod
        try:
            records = auth_mod.read_records(root)
        except Exception:                                  # pragma: no cover - defensive
            return None
    for doc in (records or {}).values():
        if isinstance(doc, dict) and str(doc.get("authority_id") or "") == str(authority_id):
            role = str(doc.get("assigned_role") or "").strip()
            return role or None
    return None


def attested_executor(root: Path, authority_id: str | None,
                      sources: list[er.Source] | None = None,
                      siblings: dict | None = None) -> FactLookup:
    """The executor attested to the seat operating under `authority_id` (A-2).

    Enumerates EVERY applicable seat-start attestation. Two naming different executors for one
    authority is not a choice between them: it is a fact that cannot be established, and it fails
    closed with both artefacts named.
    """
    kind = f"{SEAT_START} attestation"
    if not authority_id:
        return FactLookup(None, er.Resolution(
            kind=kind, status=er.NOT_FOUND,
            detail="the record names no authority_id, so no seat-start fact can be scoped to it"))

    all_sources = _sources(root, sources)
    records = _records(root, siblings)
    # A-1-R1. The expected role comes from the AUTHORITY RECORD this seat-start fact is being scoped
    # to — the one place the artefact cannot reach. An attestation claiming ENGINEER for an
    # ASSURANCE authority is excluded even if it is sitting in the right area, and an attestation
    # claiming nothing at all is excluded because the schema requires the field.
    #
    # independent Assurance findings U3-1 and U3-2. The work item now comes from the AUTHORITY RECORD rather than from
    # the artefact, and the authority and provenance gates run. This path already scoped by
    # authority; it did NOT check that the authority grants the claimed SEAT, and an invented seat
    # under a real authority resolved.
    record = _record_for(records, authority_id)
    context = er.TrustContext(
        kind=kind,
        expected_attestation_type=SEAT_START,
        expected_role=_role_of_authority(root, authority_id, siblings),
        expected_authority_id=str(authority_id),
        expected_work_item=str((record or {}).get("work_item") or "").strip() or None,
        schema=_schema(root),
        authority_gate=ab.gate(root, records),
        provenance_gate=_provenance_gate(root, records))
    applicable, excluded = er.partition(
        all_sources,
        lambda s: (str(s.doc.get("attestation_type") or "") == SEAT_START
                   and str(s.doc.get("authority_id") or "") == str(authority_id)),
        context)

    resolution = er.resolve_unique(kind, applicable, SEAT_START_IDENTITY, subject=str(authority_id))
    resolution.excluded = excluded
    if not resolution.resolved:
        return FactLookup(None, resolution)

    doc = resolution.selected.doc
    executor = doc.get("external_executor_id")
    if not executor:
        resolution.status = er.NOT_FOUND
        resolution.detail = (f"{resolution.selected.rel_path} attests to no executor; an "
                             "attestation naming nobody attests nothing")
        return FactLookup(None, resolution)

    evidence = ", ".join(source.rel_path for source in resolution.applicable)
    return FactLookup(
        ExecutorFact(str(executor), ATTESTED, str(doc.get("seat_id") or "") or None,
                     str(authority_id), str(doc.get("assigned_role") or "") or None, evidence),
        resolution)


def advisory_executor(doc: dict) -> ExecutorFact | None:
    """`external_execution.intended_executor`, which the record itself declares non-authoritative.

    Returned so it can be REPORTED and cross-checked. Never `established`: a field that says
    "confers nothing, grants nothing and constrains nothing" cannot be the thing a non-waivable
    control rests on.
    """
    block = doc.get("external_execution")
    if not isinstance(block, dict):
        return None
    who = block.get("intended_executor")
    if not who:
        return None
    return ExecutorFact(str(who), ADVISORY, str(doc.get("seat_id") or "") or None,
                        str(doc.get("authority_id") or "") or None,
                        str(doc.get("assigned_role") or "") or None,
                        "authority.external_execution")


def git_author_of(root: Path, commit: str) -> ExecutorFact | None:
    """The candidate commit's author. A DIAGNOSTIC, and never anything more (A-6).

    Independent Assurance found this implemented as a documented third tier that nothing called —
    "a documented control with no reader is the shape this repository has met before". The governed
    disposition is the second of the two permitted: it is RETAINED and CONNECTED, with an explicitly
    non-authoritative role.

    Its only consumer is `git_author_disagreement`, which can add a FINDING and can never change a
    status. There is deliberately no path by which a missing ATTESTED identity falls back to this:
    `established` is false for GIT_AUTHOR because GIT_AUTHOR is not in CONCLUSIVE_SOURCES, and the
    separation check refuses on an unestablished identity before any diagnostic runs.
    """
    from .authority import _git                  # reuse the repository's own git accessor

    try:
        code, out = _git(root, "show", "-s", "--format=%an", commit)
    except Exception:                                      # pragma: no cover - defensive
        return None
    if code != 0 or not out.strip():
        return None
    return ExecutorFact(out.strip(), GIT_AUTHOR, evidence=f"git author of {commit[:12]}")


def git_author_disagreement(root: Path, candidate: str,
                            implementer: ExecutorFact | None) -> list[str]:
    """Report an attested implementer that differs from the commit's Git author (A-6).

    The asymmetry Assurance named: the auditor side reported an attested-versus-advisory
    disagreement while the implementer side cross-checked nothing at all. This closes it on the same
    terms — REPORTED, never decisive. A mismatch is common and innocent (a shared machine, a
    workflow bot, a rebase) and it is never evidence of who implemented anything. It is worth
    printing precisely because a reader can weigh it and a control cannot.
    """
    if not (implementer and implementer.established and candidate):
        return []
    author = git_author_of(root, candidate)
    if author is None or not author.executor_id:
        return []
    if author.executor_id.strip().casefold() == implementer.executor_id.strip().casefold():
        return []
    return [f"the attested implementer ({implementer.executor_id}) and the Git author of "
            f"{candidate[:12]} ({author.executor_id}) differ; Git authorship is configuration, not "
            "identity, so this is reported as a diagnostic and establishes nothing either way"]


def implementer_of(root: Path, candidate: str, siblings: dict,
                   sources: list[er.Source] | None = None) -> FactLookup:
    """Which executor actually PRODUCED `candidate` (A-1).

    Two durable routes, both anchored on the candidate rather than inferred from who is nearby:

        1. a SEAT_DELIVERY attestation naming produced_candidate — written after the commit exists,
           which is the only moment its SHA can be known;
        2. an ENGINEER authority whose new_candidate IS this candidate, joined to its seat-start
           attestation.

    Route 2 exists because route 1 cannot be written for candidates that predate this mechanism, and
    a control that only works for future records leaves the entire existing history unchecked.

    NEITHER route takes a first match any more. Route 1 enumerates every delivery attestation naming
    this candidate; route 2 enumerates every ENGINEER authority claiming to have produced it. Within
    a route, disagreement fails closed. ACROSS routes, disagreement also fails closed — a delivery
    record and an authority record that name different producers cannot both be right, and choosing
    the one that happens to be checked first is the defect wearing a second costume.
    """
    kind = f"{SEAT_DELIVERY} attestation"
    if not candidate:
        return FactLookup(None, er.Resolution(
            kind=kind, status=er.NOT_FOUND,
            detail="no candidate, so there is nothing to attribute to anybody"))

    all_sources = _sources(root, sources)
    records = _records(root, siblings)
    # A-1-R1. The boundary comes from TRUSTED CONTEXT, not from the artefact. Only an ENGINEER seat
    # produces a candidate, so the expected role is ENGINEER and the expected area is engineer/ —
    # asserted here rather than read off whatever the artefact happens to declare, or skipped when it
    # declares nothing.
    #
    # independent Assurance finding U3-1 — THE REPAIR. This context previously carried expected_candidate and candidate_field
    # and NOTHING else, so an artefact naming an invented work item, an invented seat and a CLOSED
    # unrelated authority resolved ATTESTED / RESOLVED with zero exclusions. The authority gate now
    # runs, with `candidate_field` passed through so the relationship between the authority and the
    # candidate it claims to have produced is evaluated rather than assumed.
    #
    # The work item is deliberately NOT constrained to a caller-supplied value here: this path asks
    # "who produced this commit", which is a question no single work item owns in advance. The work
    # item is constrained against the AUTHORITY the artefact itself names, inside the gate, which is
    # the constraint that actually binds — a forger controls the artefact and the directory, and
    # controls no authority record.
    context = er.TrustContext(
        kind=kind,
        expected_attestation_type=SEAT_DELIVERY,
        expected_role=ENGINEER_ROLE,
        expected_candidate=candidate,
        candidate_field="produced_candidate",
        schema=_schema(root),
        authority_gate=ab.gate(root, records, candidate_field="produced_candidate"),
        provenance_gate=_provenance_gate(root, records))
    applicable, excluded = er.partition(
        all_sources,
        lambda s: (str(s.doc.get("attestation_type") or "") == SEAT_DELIVERY
                   and str(s.doc.get("produced_candidate") or "") == candidate),
        context)

    resolution = er.resolve_unique(kind, applicable, SEAT_DELIVERY_IDENTITY,
                                   subject=f"candidate {candidate[:12]}")
    resolution.excluded = excluded

    delivery_fact: ExecutorFact | None = None
    if resolution.conflicted:
        return FactLookup(None, resolution)
    if resolution.resolved:
        doc = resolution.selected.doc
        executor = doc.get("external_executor_id")
        if executor:
            delivery_fact = ExecutorFact(
                str(executor), ATTESTED, str(doc.get("seat_id") or "") or None,
                str(doc.get("authority_id") or "") or None, ENGINEER_ROLE,
                ", ".join(s.rel_path for s in resolution.applicable))

    # Route 2. Every ENGINEER authority claiming to have produced this candidate, not the first.
    #
    # `new_candidate` ONLY. On an ENGINEER record `target_candidate` is the candidate the work
    # STARTS FROM, not the one it produces — AUTH-0009 targets 5e63542 and produced b5471d0.
    # Treating both as "produced" makes the seat REPAIRING a candidate look like the seat that
    # BUILT it, which on this very repository returned the right executor for the wrong reason.
    claimants = sorted(
        (path for path, other in (siblings or {}).items()
         if isinstance(other, dict)
         and str(other.get("assigned_role", "")) == ENGINEER_ROLE
         and str(other.get("new_candidate") or "") == candidate),
        key=str)

    authority_facts: list[tuple[str, ExecutorFact]] = []
    for path in claimants:
        other = siblings[path]
        lookup = attested_executor(root, other.get("authority_id"), all_sources, siblings)
        if lookup.conflicted:
            resolution.status = er.CONFLICT
            resolution.findings += lookup.resolution.findings
            resolution.detail = (
                f"the ENGINEER authority claiming to have produced {candidate[:12]} has "
                f"conflicting seat-start evidence: {lookup.resolution.detail}")
            return FactLookup(None, resolution)
        fact = lookup.fact or advisory_executor(other)
        if fact:
            authority_facts.append((path, fact))

    established = [(path, f) for path, f in authority_facts if f.established]
    names = {f.executor_id.strip().casefold() for _, f in established}
    if len(names) > 1:
        resolution.status = er.CONFLICT
        resolution.findings += [
            f"conflicting ENGINEER authority claim: {Path(p).name} resolves producer "
            f"{f.executor_id}" for p, f in established]
        resolution.detail = (f"{len(established)} ENGINEER authorities name different producers of "
                             f"{candidate[:12]}; an unestablished fact is a reason to refuse")
        return FactLookup(None, resolution)

    authority_fact = established[0][1] if established else (
        authority_facts[0][1] if authority_facts else None)

    if delivery_fact and authority_fact and authority_fact.established:
        if delivery_fact.executor_id.strip().casefold() != \
                authority_fact.executor_id.strip().casefold():
            resolution.status = er.CONFLICT
            resolution.findings.append(
                f"the SEAT_DELIVERY attestation names {delivery_fact.executor_id} as the producer "
                f"of {candidate[:12]} while the ENGINEER authority's seat-start evidence names "
                f"{authority_fact.executor_id}; the two durable routes disagree")
            resolution.detail = ("delivery evidence and authority evidence disagree about who "
                                 f"produced {candidate[:12]}, so the producer cannot be established")
            return FactLookup(None, resolution)

    fact = delivery_fact or authority_fact
    if fact is None and resolution.status == er.NOT_FOUND:
        resolution.detail = (f"no durable record attributes {candidate[:12]} to any executor; zero "
                             "applicable facts is NOT_VERIFIED, never a pass")
    return FactLookup(fact, resolution)


# --------------------------------------------------------------------------------------------- #
# The check
# --------------------------------------------------------------------------------------------- #

def check_separation(root: Path, doc: dict, siblings: dict) -> SeparationResult:
    """Compare the executor that PRODUCED the candidate with the executor AUDITING it.

    Not the seats. The seats are generic by design and comparing them is the defect. This compares
    the parties, from durable facts, and refuses when it cannot establish them.
    """
    from . import placement

    root = Path(root)
    candidate = str(doc.get("target_candidate") or "")
    sources, unreadable = attestation_sources(root)
    result = SeparationResult(NOT_VERIFIED, "not evaluated", candidate or None)

    # F14 applied to attestations: an unreadable input blocks, it does not get skipped.
    if unreadable:
        result.status = FAIL
        result.detail = ("executor attestations exist that cannot be read, so separation cannot be "
                         "established and must not be assumed")
        result.findings += [f"unreadable attestation — {u}" for u in unreadable]
        return result

    # A corrupt SIBLING authority means the implementer may be recorded in a file we cannot parse.
    if any(d is None for d in (siblings or {}).values()):
        result.status = FAIL
        result.detail = ("a sibling authority record is unparseable, so the executor that produced "
                         "this candidate cannot be ruled in or out")
        return result

    if not candidate:
        # F13's rule, restated where it bites: with no candidate there is nothing to compare ABOUT.
        result.status = FAIL
        result.detail = ("no target_candidate, so separation of duties has no subject; assurance is "
                         "always assurance OF a named candidate")
        return result

    auditor_lookup = attested_executor(root, doc.get("authority_id"), sources, siblings)
    implementer_lookup = implementer_of(root, candidate, siblings, sources)
    result.resolutions = [auditor_lookup.resolution, implementer_lookup.resolution]

    auditor = auditor_lookup.fact
    implementer = implementer_lookup.fact
    auditor_advisory = advisory_executor(doc)

    result.auditor = auditor or auditor_advisory
    result.implementer = implementer

    # Conflicting evidence NEVER produces PASS, whichever side it is on.
    for lookup, side in ((auditor_lookup, "the Assurance seat"),
                         (implementer_lookup, f"the producer of {candidate[:12]}")):
        if lookup.conflicted:
            result.status = FAIL
            result.detail = (f"the executor occupying {side} cannot be established: "
                             f"{lookup.resolution.detail}")
            result.findings += lookup.resolution.findings
            return result

    for lookup in (auditor_lookup, implementer_lookup):
        result.findings += [f"excluded evidence — {x}" for x in lookup.resolution.excluded]
        result.findings += [f for f in lookup.resolution.findings
                            if f.startswith((er.BYTE_IDENTICAL, er.SEMANTICALLY_IDENTICAL,
                                             er.PATH_ALIAS))]

    if auditor and auditor_advisory and auditor.executor_id != auditor_advisory.executor_id:
        result.findings.append(
            f"the attested executor ({auditor.executor_id}) and the advisory "
            f"external_execution.intended_executor ({auditor_advisory.executor_id}) disagree; the "
            "attestation is authoritative and the disagreement is itself worth reporting")

    result.findings += git_author_disagreement(root, candidate, implementer)

    # independent Assurance finding U3-2. LABEL THE EVIDENCE THAT WAS TRUSTED, on the surface a reader already looks at.
    # A confidence level computed and never shown would be "a documented control with no reader",
    # which is a shape this repository has met before and named. Findings from provenance that
    # CONTRADICTS an artefact exclude it above; this reports the level of what survived.
    result.findings += provenance_labels(root, [auditor_lookup, implementer_lookup], siblings)

    # ROUTE A — the exclusion list, read by CODE rather than by a reader.
    #
    # `excluded_executors` was a declared compensating control that no code read, and AUTH-0011
    # then nested it one level down where it was inert twice over. It is resolved through
    # `placement`, so a declared alias position enforces IDENTICALLY to the canonical one and an
    # undeclared position is a validation error rather than silence.
    excluded_value, placement_findings = placement.resolve_field(doc, "excluded_executors")
    result.findings += placement_findings
    excluded = [str(x).strip().casefold() for x in (excluded_value or [])]
    route_a_fails = bool(
        auditor and auditor.executor_id and auditor.executor_id.strip().casefold() in excluded)

    requires_attestation, demand_findings = placement.resolve_field(
        doc, "required_executor_attestation")
    result.findings += demand_findings

    # ROUTE B — the executor comparison. Independently meaningful, and reported independently:
    # route A survives only because it matches on the auditor's NAME, so an agreement between them
    # is worth stating and a disagreement is worth refusing over.
    both_established = bool(auditor and auditor.established
                            and implementer and implementer.established)
    route_b_fails = bool(
        both_established
        and implementer.executor_id.strip().casefold() == auditor.executor_id.strip().casefold())

    if route_a_fails and both_established and not route_b_fails:
        result.findings.append(
            f"SOD routes disagree: the exclusion list bars {auditor.executor_id} from this seat, "
            f"while the executor comparison finds a distinct producer ({implementer.executor_id}). "
            "Both are reported; the exclusion is decisive because it is a named prohibition on this "
            "record, not an inference")
    if route_b_fails and not route_a_fails:
        result.findings.append(
            "SOD routes disagree: the executor comparison fails while the exclusion list does not "
            "bar this party. The exclusion list is only as wide as the names somebody remembered to "
            "write; the comparison is the general control")

    if route_a_fails:
        result.status = FAIL
        result.detail = (f"{auditor.executor_id} occupies the Assurance seat but is named in "
                         "excluded_executors on this very record (PBG-SOD-001, non-waivable)")
        return result

    if not (auditor and auditor.established):
        # NEVER PASS. Whether this is FAIL or NOT_VERIFIED turns on whether the record itself
        # promised an attestation: a record that demands one and lacks it is broken, not merely
        # unproven.
        result.status = FAIL if requires_attestation else NOT_VERIFIED
        result.awaiting_attestation = True
        result.detail = (
            "the executor occupying this Assurance seat is not established by a seat-start "
            "attestation" + (
                f"; external_execution names {auditor_advisory.executor_id}, which is declared "
                "non-authoritative and cannot establish it"
                if auditor_advisory else "")
            + (". This record requires an executor attestation and has none."
               if requires_attestation else ""))
        return result

    if not (implementer and implementer.established):
        result.status = FAIL if requires_attestation else NOT_VERIFIED
        result.detail = (
            f"the executor that produced {candidate[:12]} is not established by any durable "
            "record, so it cannot be shown to differ from the executor auditing it"
            + (f"; the strongest available signal is {implementer.render()}, which is not "
               "conclusive" if implementer else ""))
        return result

    if route_b_fails:
        result.status = FAIL
        result.detail = (
            f"{auditor.executor_id} is assigned {ASSURANCE_ROLE} for {candidate[:12]} and is the "
            f"same executor recorded as producing it ({implementer.evidence}) — PBG-SOD-001, "
            "non-waivable")
        return result

    result.status = PASS
    result.detail = (f"{implementer.executor_id} produced {candidate[:12]}; {auditor.executor_id} "
                     "is auditing it. Distinct parties, both established from durable attestation.")
    return result
