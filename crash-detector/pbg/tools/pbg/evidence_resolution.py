"""One mechanism for establishing a fact from evidence (A-1, A-2, A-4, A-5).

THE DEFECT, IN ONE SENTENCE. Four resolvers each took the first match — `implementer_of` and
`attested_executor` by sorted evidence path, `manifest.resolve` and `instructions.resolve` by
declared location order — so whichever artefact happened to sort first BECAME the fact, and every
other applicable artefact was read by nobody and reported to nobody.

That is not four defects. It is one defect with four instances, and independent Assurance said so:
`evidence/assurance/…` sorts before `evidence/engineer/…`, so a single file written inside an
auditor's OWN authorised evidence path preempted the true delivery record and PBG-SOD-001 returned
PASS for a seat auditing its own candidate. No code was touched, no governance record altered.

It is also not merely a forgery objection, and that is the part that decides the design. An HONEST
duplicate — an attestation re-issued after a correction, an evidence pack copied between work items,
a manifest kept in two permitted locations — resolves exactly the same silent way. A mechanism that
only defends against malice would still be wrong.

THE RULE THIS MODULE IMPLEMENTS, stated once so that four callers cannot drift apart:

    ENUMERATE     every applicable artefact, never short-circuit on the first
    SCOPE         to the exact subject — this authority, this candidate, this work item
    BOUND         to the evidence area whose owner may lawfully write it
    RECONCILE     duplicates that agree, EXPLICITLY, naming every path
    REFUSE        artefacts that disagree, and name what disagrees with what
    REPORT        in human-readable output, not only under --json
    NEVER         let directory ordering, lexical path order, or "it sorted first" decide truth

A fact that cannot be established is a reason to REFUSE. That is `executors.py`'s own stated rule,
and this module is what makes it true of duplicates as well as of absences.

WHY ORDER STILL EXISTS HERE. Sorting has not been removed; it has been demoted. Sources are walked
in sorted order so results are DETERMINISTIC across filesystems, and a test proves the outcome is
identical when the traversal is reversed. Determinism is a property of the report. It is never the
reason a fact is believed.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from . import continuity
from . import validation as vld

# --- statuses ------------------------------------------------------------------------------------ #

RESOLVED = "RESOLVED"
NOT_FOUND = "NOT_FOUND"
CONFLICT = "CONFLICT"

#: How a duplicate was reconciled. Both are RESOLVED outcomes; neither is silent.
BYTE_IDENTICAL = "BYTE_IDENTICAL"
SEMANTICALLY_IDENTICAL = "SEMANTICALLY_IDENTICAL"
PATH_ALIAS = "PATH_ALIAS"

#: Evidence areas, and which internal role may lawfully write an attestation into each.
#:
#: This is the boundary A-1 asks for: "an auditor must not be able to manufacture a false implementer
#: identity inside its own writable evidence path". An attestation that claims ENGINEER from inside
#: `evidence/assurance/` is not silently ignored — it is EXCLUDED from resolution and REPORTED, which
#: is a refusal rather than a shrug.
ROLE_EVIDENCE_AREAS = {
    "ENGINEER": "engineer",
    "ASSURANCE_ENGINEER": "assurance",
    "PROJECT_LEAD": "governance",
}

EVIDENCE_ROOT = "evidence"


def _sha(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _norm(value) -> str | None:
    """One spelling for one value. `"ALPHA "` and `"alpha"` are one party, and always were."""
    if value is None:
        return None
    text = str(value).strip()
    return text.casefold() or None


# --- what a resolvable artefact is ---------------------------------------------------------------- #

@dataclass(frozen=True)
class Source:
    """One artefact that could carry the fact being sought, and where it physically is."""
    rel_path: str
    real_path: str
    content_sha: str
    doc: dict

    def value(self, field_name: str):
        return self.doc.get(field_name)

    def identity(self, fields: tuple) -> tuple:
        return tuple(_norm(self.doc.get(f)) for f in fields)


@dataclass
class Resolution:
    """The outcome of establishing one fact, including everything that was considered.

    `applicable` is the whole enumerated set, not the survivors. An auditor reading this must be
    able to see what the resolver looked at, not only what it chose.
    """
    kind: str
    status: str = NOT_FOUND
    selected: Source | None = None
    applicable: list[Source] = field(default_factory=list)
    excluded: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    detail: str = ""

    @property
    def resolved(self) -> bool:
        return self.status == RESOLVED and self.selected is not None

    @property
    def conflicted(self) -> bool:
        return self.status == CONFLICT

    @property
    def paths(self) -> list[str]:
        return [s.rel_path for s in self.applicable]

    def render(self) -> str:
        lines = [f"{self.kind}: {self.status}"]
        if self.detail:
            lines.append(f"  {self.detail}")
        if self.selected is not None:
            lines.append(f"  source      {self.selected.rel_path}")
        for path in self.paths:
            if self.selected is None or path != self.selected.rel_path:
                lines.append(f"  considered  {path}")
        lines += [f"  - {f}" for f in self.findings]
        lines += [f"  - excluded: {x}" for x in self.excluded]
        return "\n".join(lines)


# --- reading the evidence tree -------------------------------------------------------------------- #

def read_sources(root: Path, glob: str, *, subdir: str = EVIDENCE_ROOT,
                 required_key: str | None = None) -> tuple[list[Source], list[str]]:
    """Every readable artefact under `<root>/<subdir>` matching `glob`, and every one that is not.

    Parsed with the strict parser, so a duplicate key is a FINDING rather than a silent
    last-value-wins. An unreadable input to a non-waivable control must never be skipped quietly
    (F14) — it is returned separately so the caller can fail closed on it.
    """
    root = Path(root)
    base = root / subdir
    sources: list[Source] = []
    unreadable: list[str] = []
    if not base.is_dir():
        return sources, unreadable

    real_root = root.resolve()
    for path in sorted(base.glob(glob)):
        # STAGE 1 — PATH CONTAINMENT, judged on where the path LANDS rather than how it is spelled.
        # A symlink or alias that leaves PROJECT_ROOT used to be skipped silently by a bare
        # `continue`; a silent skip and a refusal look identical from the outside, and only one of
        # them is a control. The rel_path recorded below is the RESOLVED one, so an artefact reached
        # through a symlinked directory is judged in the area it actually lives in — which is what
        # attack A1-7 walked through.
        try:
            real = path.resolve()
            rel = str(real.relative_to(real_root))
        except ValueError:
            unreadable.append(
                f"{path}: resolves to {path.resolve()}, outside PROJECT_ROOT {real_root}. An "
                "artefact outside the project cannot be the project's evidence")
            continue

        # STAGE 2 — PARSE. Strict, so a duplicate key is a finding rather than last-value-wins.
        try:
            raw = path.read_bytes()
            doc = continuity.parse_strict(raw.decode("utf-8"))
        except (continuity.ContinuityError, OSError, UnicodeDecodeError) as exc:
            unreadable.append(f"{rel}: {exc}")
            continue
        if not isinstance(doc, dict):
            unreadable.append(
                f"{rel}: parsed as {type(doc).__name__}, not a mapping. A governed artefact that is "
                "not a mapping of fields is refused, not skipped")
            continue
        if required_key and not doc.get(required_key):
            continue                                       # not this kind of artefact; not a defect
        sources.append(Source(rel, str(real), _sha(raw), doc))
    return sources, unreadable


def attestation_schema(framework_root: Path) -> tuple[dict | None, list[str]]:
    """The governed seat-attestation schema, or the reason there is none.

    Loaded from the FILE, so the schema is the single statement of the contract. independent Assurance finding A1-R1 is what
    happened when the schema said `assigned_role` was required and the code deciding trust kept its
    own opinion — the two drifted, and the drift was the vulnerability.
    """
    schema, findings = vld.load_schema(
        Path(framework_root) / "schemas" / "seat-attestation.schema.yaml")
    return schema, [f.render() for f in findings]


def area_of(rel_path: str) -> str | None:
    """The evidence area a path sits in: `evidence/<area>/…`."""
    parts = Path(rel_path).parts
    if len(parts) >= 2 and parts[0] == EVIDENCE_ROOT:
        return parts[1]
    return None


@dataclass(frozen=True)
class TrustContext:
    """What an artefact must MATCH, derived from trusted context and never from the artefact.

    THE DOCTRINE independent Assurance finding A1-R1 EXISTS TO ENFORCE: an artefact's content never defines its own lawful
    evidence boundary. The previous implementation read `assigned_role` off the artefact and looked
    the answer up in `ROLE_EVIDENCE_AREAS`; an artefact that declared no role matched no entry, the
    lookup returned None, and the boundary check was skipped entirely. The boundary was OPT-IN, and
    two files exercising that opt-out manufactured a false implementer from inside the auditor's own
    writable path.

    Every expectation here comes from somewhere the artefact cannot reach: the authority record, the
    caller's own knowledge of which fact it is establishing, the canonical evidence-area contract.
    An artefact is measured against them. It does not get a say in what they are.

    A `None` expectation means "the caller genuinely does not constrain this", not "the artefact may
    decide it". The role is the one field with no such licence — `require_declared_role` is True by
    default precisely because its optionality was the vulnerability.
    """
    kind: str = "attestation"
    expected_attestation_type: str | None = None
    expected_role: str | None = None
    expected_authority_id: str | None = None
    expected_seat_id: str | None = None
    expected_work_item: str | None = None
    expected_candidate: str | None = None
    candidate_field: str = "produced_candidate"
    schema: dict | None = None
    require_declared_role: bool = True
    #: independent Assurance finding U3-1. `(Source) -> [ValidationFinding]`, asking whether the AUTHORITY RECORD the
    #: artefact names lawfully grants this seat, work item and candidate relationship. Supplied as a
    #: callable so this module keeps knowing nothing about authority records: an expectation the
    #: caller computed is checkable here, and a record lookup is not.
    #:
    #: `None` means the caller supplied no authority context. It does NOT mean the artefact is
    #: trusted — the caller's scope expectations still run, and a caller that establishes IDENTITY
    #: or CANDIDATE OWNERSHIP must supply this gate. `executors.py` supplies it on both paths.
    authority_gate: object | None = None
    #: independent Assurance finding U3-2. `(Source) -> [ValidationFinding]`, asking whether the COMMIT that introduced the
    #: artefact supports what the artefact claims. Content is a claim; provenance is evidence.
    provenance_gate: object | None = None

    @property
    def expected_area(self) -> str | None:
        """The area derived from the EXPECTED role. Not from the declared one."""
        return ROLE_EVIDENCE_AREAS.get(str(self.expected_role or "")) if self.expected_role else None


def ownership_findings(source: Source, context: TrustContext | None = None
                       ) -> list[vld.ValidationFinding]:
    """Why this artefact may not lawfully carry the fact it claims, if it may not.

    Ordered gates, and the order is the contract (see `validation.STAGES`). Path containment and
    parsing already happened in `read_sources`; this runs schema validation, required-field
    validation, role/path compatibility and scoping, and every failure EXCLUDES the artefact and is
    REPORTED. Excluding without reporting would rebuild the defect one layer down.

    The role gate is the repaired one, and it now fails in four directions rather than one:

        role ABSENT      excluded — the schema requires it and a missing field is not an absent
                         objection
        role UNKNOWN     excluded — an unrecognised role maps to no area, and "maps to no area" must
                         never mean "may be written in any area"
        role != EXPECTED excluded — the authority record says what role this seat holds; an artefact
                         claiming a different one is not evidence about this seat
        area != role's   excluded — the original check, which was correct and simply skippable
    """
    context = context or TrustContext()
    problems: list[vld.ValidationFinding] = []
    path = source.rel_path

    # --- STAGE: schema + required fields ---------------------------------------------------------- #
    if context.schema is not None:
        problems.extend(vld.validate_against_schema(source.doc, context.schema, path=path))

    raw_role = source.doc.get("assigned_role")
    role = str(raw_role or "").strip()
    area = area_of(path)

    # --- STAGE: role / path compatibility --------------------------------------------------------- #
    if not role:
        if context.require_declared_role:
            problems.append(vld.ValidationFinding(
                vld.ROLE_PATH, "ROLE_NOT_DECLARED", path, field="assigned_role",
                detail=("declares no assigned_role, so no evidence-area boundary can be derived for "
                        "it. This is independent Assurance finding A1-R1 exactly: an artefact bounded by nothing was "
                        "previously applicable from ANY evidence area, including an auditor's own. "
                        "It is EXCLUDED, not skipped")))
    elif role not in ROLE_EVIDENCE_AREAS:
        problems.append(vld.ValidationFinding(
            vld.ROLE_PATH, "ROLE_UNKNOWN", path, field="assigned_role",
            detail=(f"declares assigned_role {role!r}, which is not one of "
                    f"{sorted(ROLE_EVIDENCE_AREAS)}. An unrecognised role maps to no evidence area, "
                    "and mapping to no area must never mean lawful in every area")))
    else:
        declared_area = ROLE_EVIDENCE_AREAS[role]
        if area and area != declared_area:
            problems.append(vld.ValidationFinding(
                vld.ROLE_PATH, "AREA_MISMATCH", path, field="assigned_role",
                detail=(f"declares assigned_role {role}, whose evidence area is "
                        f"{EVIDENCE_ROOT}/{declared_area}/, but it is written under "
                        f"{EVIDENCE_ROOT}/{area}/. An attestation written outside its own role's "
                        "evidence area cannot establish that role's fact — that is exactly how an "
                        "auditor's own writable path preempted a delivery record")))
        if context.expected_role and role != str(context.expected_role):
            problems.append(vld.ValidationFinding(
                vld.ROLE_PATH, "ROLE_NOT_EXPECTED", path, field="assigned_role",
                detail=(f"declares assigned_role {role}, but the authority this fact is being "
                        f"scoped to holds {context.expected_role}. The authority record decides "
                        "which role a seat has; a self-declared role is checked against it, never "
                        "trusted in place of it")))

    # The area demanded by TRUSTED context, independent of anything the artefact declares. This is
    # the gate that holds even if every role check above were somehow satisfied.
    expected_area = context.expected_area
    if expected_area and area and area != expected_area:
        problems.append(vld.ValidationFinding(
            vld.ROLE_PATH, "AREA_NOT_EXPECTED", path, field="path",
            detail=(f"is written under {EVIDENCE_ROOT}/{area}/, but the fact being established "
                    f"belongs to a {context.expected_role} seat, whose evidence area is "
                    f"{EVIDENCE_ROOT}/{expected_area}/. The boundary comes from the authority "
                    "record, not from the artefact")))
    if area is None:
        problems.append(vld.ValidationFinding(
            vld.PATH_CONTAINMENT, "OUTSIDE_EVIDENCE_AREA", path, field="path",
            detail=(f"is not inside {EVIDENCE_ROOT}/<area>/, so no owning role can be determined "
                    "for it. An artefact nobody owns establishes nothing")))

    # --- STAGE: scoping ---------------------------------------------------------------------------- #
    #
    # WORK_ITEM_PATH_MISMATCH is retained and is NOT the work-item control. independent Assurance finding U3-1 named its
    # limit exactly: it requires the declared work item to appear in the artefact's own path, which
    # a forger satisfies by choosing the directory name. It catches an evidence pack COPIED into the
    # wrong directory, which is an honest-mistake shape worth catching, and nothing more. The real
    # work-item constraint is the AUTHORITY stage below.
    work_item = str(source.doc.get("work_item") or "").strip()
    if work_item and work_item not in Path(path).parts:
        problems.append(vld.ValidationFinding(
            vld.SCOPE, "WORK_ITEM_PATH_MISMATCH", path, field="work_item",
            detail=(f"declares work_item {work_item}, which does not appear in its own path; the "
                    "artefact and the work item it claims disagree about where it belongs")))
    problems.extend(_scope_findings(source, context))

    # --- STAGE: authority ---------------------------------------------------------------------------- #
    # independent Assurance finding U3-1. Everything above measures the artefact against what the CALLER expected. This asks
    # whether a real, committed authority record lawfully grants what the artefact claims — the
    # stage the declared trust order promised and the implementer path never ran.
    if context.authority_gate is not None:
        problems.extend(context.authority_gate(source))

    # --- STAGE: provenance --------------------------------------------------------------------------- #
    # independent Assurance finding U3-2. Last of the artefact gates, because it is the only one that reads the repository's
    # own history rather than the artefact and the records.
    if context.provenance_gate is not None:
        problems.extend(context.provenance_gate(source))
    return problems


def _scope_findings(source: Source, context: TrustContext) -> list[vld.ValidationFinding]:
    """Authority, work-item, seat and candidate scoping against trusted expectations."""
    out: list[vld.ValidationFinding] = []
    path = source.rel_path
    checks = (
        ("attestation_type", context.expected_attestation_type, "ATTESTATION_TYPE_MISMATCH"),
        ("authority_id", context.expected_authority_id, "AUTHORITY_MISMATCH"),
        ("seat_id", context.expected_seat_id, "SEAT_MISMATCH"),
        ("work_item", context.expected_work_item, "WORK_ITEM_MISMATCH"),
        (context.candidate_field, context.expected_candidate, "CANDIDATE_MISMATCH"),
    )
    for field_name, expected, code in checks:
        if expected is None:
            continue
        actual = source.doc.get(field_name)
        if actual is None or not str(actual).strip():
            out.append(vld.ValidationFinding(
                vld.SCOPE, f"{code}_ABSENT", path, field=field_name,
                detail=(f"the fact being established is scoped to {field_name}={expected!r}, and "
                        "this artefact declares none. An artefact that does not say what it is "
                        "about cannot be about this")))
            continue
        if _norm(actual) != _norm(expected):
            out.append(vld.ValidationFinding(
                vld.SCOPE, code, path, field=field_name,
                detail=(f"declares {field_name}={actual!r}, but the fact being established is "
                        f"scoped to {expected!r}")))
    return out


# --- the primitive every caller shares -------------------------------------------------------------- #

def resolve_unique(kind: str, sources: list[Source], identity_fields: tuple,
                   *, subject: str = "") -> Resolution:
    """Establish ONE fact from every applicable artefact, or refuse and say why.

    `identity_fields` are the fields that MAKE the fact. Two artefacts agreeing on all of them are
    the same fact recorded twice — reconciled explicitly, with every path named. Two that differ on
    any of them are two contradictory facts, which is the definition of a fact that cannot be
    established, and it fails closed.

    There is deliberately no "prefer the better source" tie-break. A ranking is how the defect
    survives: whichever rule decides which copy wins is a rule an attacker or an accident can aim at.
    """
    result = Resolution(kind=kind, applicable=list(sources))
    subject_text = f" for {subject}" if subject else ""

    if not sources:
        result.status = NOT_FOUND
        result.detail = (f"no applicable {kind} evidence{subject_text}; zero applicable facts is "
                         "NOT_VERIFIED, never a pass")
        return result

    # Path aliases first: the same bytes reached through two names is one artefact, not two facts.
    by_real: dict[str, list[Source]] = {}
    for source in sources:
        by_real.setdefault(source.real_path, []).append(source)
    for real, group in sorted(by_real.items()):
        if len(group) > 1:
            names = ", ".join(sorted(s.rel_path for s in group))
            result.findings.append(
                f"{PATH_ALIAS}: {names} are the same file ({real}); counted once")

    distinct = [group[0] for _, group in sorted(by_real.items())]
    distinct.sort(key=lambda s: s.rel_path)

    identities = {source.identity(identity_fields) for source in distinct}
    if len(identities) > 1:
        result.status = CONFLICT
        result.selected = None
        differing = sorted(
            f"{field_name}=" + " vs ".join(
                sorted({str(s.doc.get(field_name)) for s in distinct}))
            for field_name in identity_fields
            if len({_norm(s.doc.get(field_name)) for s in distinct}) > 1)
        for source in distinct:
            result.findings.append(
                f"conflicting {kind}: {source.rel_path} states "
                + ", ".join(f"{f}={source.doc.get(f)!r}" for f in identity_fields))
        result.detail = (
            f"{len(distinct)} applicable {kind} artefacts{subject_text} disagree ("
            + "; ".join(differing) + "). Two contradictory readable records is a fact that cannot "
            "be established, and an unestablished fact is a reason to refuse, never to choose one")
        return result

    if len(distinct) > 1:
        shas = {s.content_sha for s in distinct}
        how = BYTE_IDENTICAL if len(shas) == 1 else SEMANTICALLY_IDENTICAL
        result.findings.append(
            f"{how}: {len(distinct)} copies of the same {kind} fact{subject_text} were reconciled "
            "explicitly — " + ", ".join(s.rel_path for s in distinct)
            + ". They agree on every identifying field, so the fact does not depend on which was "
            "read; no copy is authoritative and none was chosen by path order")

    result.status = RESOLVED
    result.selected = distinct[0]
    result.detail = (f"one coherent {kind} fact{subject_text}, established from "
                     + ("1 artefact" if len(distinct) == 1
                        else f"{len(distinct)} reconciled identical artefacts"))
    return result


def partition(sources: list[Source], predicate,
              context: TrustContext | None = None) -> tuple[list[Source], list[str]]:
    """Applicable artefacts, and the ownership reasons the rest were excluded.

    Exclusion is never silent: every artefact removed from consideration comes back as a rendered
    finding the caller must surface. `context` carries the TRUSTED expectations — without one the
    gates still run, and the role is still mandatory, because the field whose optionality was the
    vulnerability does not become optional again just because a caller passed no context.
    """
    applicable: list[Source] = []
    excluded: list[str] = []
    for source in sources:
        if not predicate(source):
            continue                                       # not about this subject at all
        problems = ownership_findings(source, context)
        if problems:
            excluded.extend(f.render() for f in problems)
            continue
        applicable.append(source)
    return applicable, excluded


# --- the same doctrine, applied to a canonical FILE rather than an attestation ---------------------- #

CANONICAL = "CANONICAL"
SHADOWED = "SHADOWED"
ABSENT = "ABSENT"
DIVERGENT = "DIVERGENT"


@dataclass
class FileResolution:
    """Which of several permitted locations supplied a governed file, and what else was there.

    A-4 and A-5 are this module's other two instances. `pbg-manifest.yaml` and
    `governance/pbg-manifest.yaml` are both permitted; `CLAUDE.md` and `AGENTS.md` are both
    recognised. In each pair the first won SILENTLY and the second was read by nobody and mentioned
    to nobody. Here the second copy is always named, and a second copy that DISAGREES is a refusal.
    """
    kind: str
    status: str
    selected: Path | None = None
    selected_location: str | None = None
    shadowed: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)

    @property
    def divergent(self) -> bool:
        return self.status == DIVERGENT


def resolve_canonical_file(kind: str, project_root: Path, locations: tuple,
                           *, compare_content: bool = True) -> FileResolution:
    """The first PRESENT permitted location, plus every other one that also exists.

    The selection rule is unchanged and deliberately so — `locations` is a declared preference order
    and changing which file wins would be a breaking change nobody asked for. What changes is that
    the losers are ENUMERATED, and that two copies whose bytes differ are DIVERGENT rather than
    quietly reduced to whichever came first.
    """
    root = Path(project_root)
    present = [(loc, root / loc) for loc in locations if (root / loc).is_file()]
    if not present:
        return FileResolution(kind, ABSENT)

    selected_loc, selected = present[0]
    others = [loc for loc, _ in present[1:]]
    result = FileResolution(kind, CANONICAL, selected, selected_loc, shadowed=others)
    if not others:
        return result

    result.status = SHADOWED
    result.findings.append(
        f"{kind}: {selected_loc} is canonical here; {len(others)} further permitted "
        f"location(s) also exist and are NOT read — {', '.join(others)}. Reported rather than "
        "ignored: a governed source that is silently shadowed is a second copy nobody watches")

    if compare_content:
        digests = {}
        for loc, path in present:
            try:
                digests[loc] = _sha(path.read_bytes())
            except OSError as exc:                         # pragma: no cover - defensive
                result.findings.append(f"{kind}: {loc} exists but cannot be read: {exc}")
                result.status = DIVERGENT
                return result
        if len(set(digests.values())) > 1:
            result.status = DIVERGENT
            result.findings.append(
                f"{kind}: the permitted locations do not agree — "
                + ", ".join(f"{loc}={d[:19]}…" for loc, d in sorted(digests.items()))
                + ". One governed fact with two different values cannot be established; the "
                "shadowed copy must be reconciled or removed by whoever owns it")
    return result
