"""Continuity records — validation on write, never hope on read.

The bootstrap Build Log entry was written, reviewed, committed and described as durable continuity
truth. It was not valid YAML. Nothing found it until a resume tried to parse it, because the same
agent authored and approved it in one pass.

    A continuity system must validate the record at the moment it is created,
    not merely hope the next agent can read it.

Write sequence, in order, with no shortcuts:

    construct → syntax → schema → semantic → reference → secret scan → append-only check
    → write temp → re-parse temp → atomic rename → update views

Nothing becomes canonical until it has been read back from the filesystem and validated again.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from . import scanning

#: BL-<UTC compact>-<short id>. The short id is uppercase alphanumeric rather than hex:
#: 36^4 keeps collision probability low enough that concurrent sub-agents writing in the
#: same second do not need a lock (PBG-CONT-010).
ENTRY_ID_RE = re.compile(r"^BL-[0-9]{8}T[0-9]{6}Z-[0-9A-Z]{4}$")
SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")
UTC_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?Z$")


class ContinuityError(ValueError):
    """A record that must not become canonical."""


# --------------------------------------------------------------------------------------------- #
# Syntax — PyYAML accepts duplicate keys silently. That is not acceptable for a governed record.
# --------------------------------------------------------------------------------------------- #

class StrictLoader(yaml.SafeLoader):
    """SafeLoader that refuses duplicate mapping keys.

    Standard YAML loading silently keeps the last value for a repeated key, so a record can say
    two different things and a reader only ever sees one. In a continuity record that is a silent
    fact-substitution, which is exactly what append-only history exists to prevent.
    """


def _no_duplicate_keys(loader, node, deep=False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ContinuityError(
                f"duplicate key {key!r} at line {key_node.start_mark.line + 1}"
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_duplicate_keys)


def parse_strict(text: str) -> dict:
    """Parse YAML with duplicate keys rejected. Raises ContinuityError on any syntax problem."""
    try:
        doc = yaml.load(text, Loader=StrictLoader)
    except ContinuityError:
        raise
    except yaml.YAMLError as exc:
        raise ContinuityError(f"invalid YAML: {exc}") from exc
    if not isinstance(doc, dict):
        raise ContinuityError("continuity record must be a mapping at the top level")
    return doc


# --------------------------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------------------------- #

@dataclass
class ValidationResult:
    ok: bool
    stage: str
    errors: list[str] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)

    def render(self) -> str:
        head = f"{'VALID' if self.ok else 'REJECTED'} at stage: {self.stage}"
        lines = [head]
        lines += [f"  error      : {e}" for e in self.errors]
        lines += [f"  unresolved : {u}" for u in self.unresolved]
        return "\n".join(lines)


def _schema_errors(doc: dict, schema_path: Path) -> list[str]:
    try:
        import jsonschema
    except ImportError:                                        # pragma: no cover
        return ["jsonschema unavailable — AMBER_FRAMEWORK_CAPABILITY_GAP"]
    schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    return [
        f"{'/'.join(str(p) for p in e.path) or '(root)'}: {e.message}"
        for e in sorted(validator.iter_errors(doc), key=lambda e: list(e.path))
    ]


def _semantic_errors(doc: dict, kind: str, now: datetime | None = None,
                     creating: bool = False) -> list[str]:
    """Checks a schema cannot express.

    `creating` separates the two things this function is asked to do. Judging a record that is
    being WRITTEN may use the present moment. Judging a record already in append-only history may
    not: "you were stamped in the future" is true of several committed entries and always will be,
    and turning that into a permanent RED would leave only history-rewriting or `--no-verify` as
    ways to work — the same trap PD-2 was about. Historical future stamps are DIAGNOSED by
    `entry_chronology` and stripped of any ordering power; they are not retroactively refused.
    """
    errors: list[str] = []

    if kind == "entry":
        # An entry claiming implementation state must reference exact Git identity.
        claims_implementation = doc.get("status") in {"CHECKPOINT", "IN_PROGRESS", "COMPLETE"}
        if claims_implementation and not doc.get("current_sha"):
            errors.append(
                "entry claims implementation state but records no current_sha (PBG-CONT-008)"
            )
        # A correction must name what it corrects, and must not name itself.
        if doc.get("correction_of") == doc.get("entry_id"):
            errors.append("correction_of names the entry itself")
        # The timestamp in the ID must agree with the recorded timestamp.
        eid, ts = doc.get("entry_id", ""), doc.get("timestamp_utc", "")
        if ENTRY_ID_RE.match(eid) and UTC_RE.match(ts):
            if eid[3:18] != ts.replace("-", "").replace(":", "")[:15]:
                errors.append(
                    f"entry_id timestamp {eid[3:18]} disagrees with timestamp_utc {ts}"
                )
        # Naive or non-UTC timestamps.
        if ts and not UTC_RE.match(ts):
            errors.append(f"timestamp {ts!r} is not UTC ISO-8601 with an explicit Z")
        # A record cannot be written before the moment it describes.
        #
        # The other half of OBS-CONTINUITY-TIMESTAMP-0001. Ordering no longer trusts the stamp, so
        # a future stamp can no longer win -- but it can still mislead every human who reads the
        # log, and it is the mechanism by which the whole defect was introduced. Refusing it at
        # write time stops the class here rather than absorbing it forever downstream. Historical
        # entries are untouched: this validates records as they are CREATED.
        stamped = _parse_stamp(ts) if creating else None
        if stamped is not None:
            horizon = (now or datetime.now(timezone.utc)) + FUTURE_STAMP_TOLERANCE
            if stamped > horizon:
                errors.append(
                    f"timestamp_utc {ts} is in the future (now {horizon.isoformat()}, tolerance "
                    f"{FUTURE_STAMP_TOLERANCE}). A continuity record states when something "
                    "happened; a future stamp states when it has not happened yet, and it is how "
                    "an entry buys an ordering position it did not earn (PBG-CONT-002).")

    if kind == "active_work":
        # The two checkpoint fields answer different questions; conflating them is a defect.
        if (doc.get("last_completed_checkpoint_sha")
                and doc.get("last_completed_checkpoint_sha") == doc.get("continuity_record_commit")):
            errors.append(
                "last_completed_checkpoint_sha equals continuity_record_commit — these answer "
                "different questions and must not be the same value"
            )
        for held in doc.get("held_actions", []) or []:
            if isinstance(held, dict) and held.get("silent_execution") != "PROHIBITED":
                errors.append(f"held action {held.get('id')} does not prohibit silent execution")

    return errors


ACTIVE_WORK_CURRENT = "ACTIVE_WORK_CURRENT"
ACTIVE_WORK_STALE = "ACTIVE_WORK_STALE"
ACTIVE_WORK_FORWARD_REFERENCE = "ACTIVE_WORK_FORWARD_REFERENCE"
ACTIVE_WORK_LOG_MISMATCH = "ACTIVE_WORK_LOG_MISMATCH"
ACTIVE_WORK_UNRESOLVED = "ACTIVE_WORK_UNRESOLVED"
NEW_PROJECT_CONTINUITY_NOT_INITIALISED = "NEW_PROJECT_CONTINUITY_NOT_INITIALISED"


@dataclass(frozen=True)
class Continuation:
    """What a currency state permits. Action-aware: truth and safety are separate calculations."""
    normal_resume: bool
    read_only_diagnosis: bool
    mutation_from_this_record: bool
    trusted_checkpoint: bool
    severity: str               # OK | AMBER | BLOCKED
    meaning: str


#: The continuation policy, stated as a table rather than inferred from membership of a tuple.
#: Positional reasoning ("the first three block") is how CURRENT gets mis-described as blocking --
#: the mapping is now explicit per state, and the tests below assert each row independently
#: (Product Authority ruling 2026-07-30 s8, s10).
CURRENCY_CONTINUATION = {
    ACTIVE_WORK_CURRENT: Continuation(
        normal_resume=True, read_only_diagnosis=True, mutation_from_this_record=True,
        trusted_checkpoint=True, severity="OK",
        meaning="the pointer matches the newest entry; resume proceeds subject to every other "
                "authority, integrity and contradiction check"),
    ACTIVE_WORK_STALE: Continuation(
        normal_resume=False, read_only_diagnosis=True, mutation_from_this_record=False,
        trusted_checkpoint=False, severity="BLOCKED",
        meaning="Active Work identifies an older valid state, not the latest; reconciliation is "
                "permitted, mutation based on this record is not"),
    ACTIVE_WORK_FORWARD_REFERENCE: Continuation(
        normal_resume=False, read_only_diagnosis=True, mutation_from_this_record=False,
        trusted_checkpoint=False, severity="BLOCKED",
        meaning="Active Work references an entry that does not exist, commonly because a "
                "multi-write checkpoint sequence was interrupted"),
    ACTIVE_WORK_LOG_MISMATCH: Continuation(
        normal_resume=False, read_only_diagnosis=True, mutation_from_this_record=False,
        trusted_checkpoint=False, severity="BLOCKED",
        meaning="pointer and Build Log are inconsistent in a determinably wrong way"),
    ACTIVE_WORK_UNRESOLVED: Continuation(
        normal_resume=False, read_only_diagnosis=True, mutation_from_this_record=False,
        trusted_checkpoint=False, severity="AMBER",
        meaning="currency cannot be determined because required evidence or capability is "
                "unavailable; this is not a softer synonym for a known mismatch"),
    NEW_PROJECT_CONTINUITY_NOT_INITIALISED: Continuation(
        normal_resume=False, read_only_diagnosis=True, mutation_from_this_record=False,
        trusted_checkpoint=False, severity="AMBER",
        meaning="a genuinely new project with no continuity yet; bootstrap is required, and this "
                "is not a recovery mismatch"),
}


def continuation_for(state: str) -> Continuation:
    """The declared continuation policy for a currency state."""
    try:
        return CURRENCY_CONTINUATION[state]
    except KeyError:                                       # pragma: no cover - defensive
        raise ValueError(f"no continuation policy declared for currency state {state!r}") from None


# --------------------------------------------------------------------------------------------- #
# Chronology — which entry is NEWEST, decided from validated events rather than from a claim
#
# OBS-CONTINUITY-TIMESTAMP-0001, the F15 continuity defect.
#
# Entry IDs embed a UTC stamp, so `sorted(stems)[-1]` was treated as "the newest entry". That is
# only true while every stamp is truthful, and the stamps in this repository are not: entries
# claiming 11:00Z, 14:00Z and 16:00Z were committed at 20:51Z the PREVIOUS DAY, 08:15Z and 09:03Z.
# A later, truthful entry stamped 09:57Z therefore sorted BEHIND them and could never become
# canonical, so Active Work read ACTIVE_WORK_STALE and resume stayed blocked. The available escape
# routes were to future-date the new entry so it out-sorted the false ones -- reproducing the exact
# defect under repair -- or to rewrite the historical entries, destroying append-only evidence.
#
# The real fault is that ordering trusted a value the record's own author supplies. So it stops:
#
#     ordering asks GIT, which records when each entry file actually entered history
#     an entry's claim is used only where no validated chronology exists at all
#     where a claim IS used, a future claim is clamped to now -- it cannot buy rank
#     a claim materially ahead of the commit that carries it is DIAGNOSED, never silently accepted
#
# Nothing is rewritten. The false stamps stay exactly as committed, remain visible in every entry
# and in `pbg log chronology`, and simply stop deciding anything.
# --------------------------------------------------------------------------------------------- #

#: A record is stamped by one machine and committed moments later, sometimes by another. Five
#: minutes absorbs that. Hours do not need absorbing -- they need explaining.
FUTURE_STAMP_TOLERANCE = timedelta(minutes=5)

ENTRY_COMMITTED = "COMMITTED"
ENTRY_UNCOMMITTED = "UNCOMMITTED"
ENTRY_UNVERSIONED = "UNVERSIONED"
ENTRY_MALFORMED = "MALFORMED"

#: How much a status is trusted to place an entry in time, highest first. An uncommitted entry was
#: written into the working tree after everything already in history -- that is an observed fact
#: about the filesystem, not a claim in the record.
_STATUS_TIER = {ENTRY_UNVERSIONED: 0, ENTRY_COMMITTED: 1, ENTRY_UNCOMMITTED: 2}

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def _id_timestamp(entry_id: str) -> datetime | None:
    """The UTC stamp embedded in a BL- id. A CLAIM, used only as a last resort."""
    if not ENTRY_ID_RE.match(str(entry_id or "")):
        return None
    try:
        return datetime.strptime(entry_id[3:19], "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    except ValueError:                                     # pragma: no cover - regex already bounds it
        return None


def _parse_stamp(value) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _ancestry_positions(root: Path) -> dict[str, int] | None:
    """sha -> position in first-parent-to-HEAD ancestry. Topological, so commit DATES cannot
    reorder it: a forged committer date moves the label, not the parentage."""
    out = _git(root, "rev-list", "--topo-order", "--reverse", "HEAD")
    if not out:
        return None
    return {sha: index for index, sha in enumerate(out.split())}


def entry_chronology(root: Path, log_dir: Path | None = None,
                     now: datetime | None = None) -> dict[str, dict]:
    """Place every Build Log entry in time using the strongest evidence available for each.

    Per entry:

        status          COMMITTED / UNCOMMITTED / UNVERSIONED / MALFORMED
        commit          the commit that ADDED the entry file, where git can say
        position        that commit's position in HEAD's ancestry -- the ordering key
        claimed         the timestamp the record asserts about itself
        effective_time  the claim, clamped to now: a future stamp cannot outrank a truthful one
        future_stamped  the claim runs materially ahead of the commit that carries it, or ahead
                        of now where there is no commit
    """
    root = Path(root)
    log_dir = Path(log_dir) if log_dir is not None else (
        root / "governance" / "engineering" / "build-log")
    now = now or datetime.now(timezone.utc)
    ceiling = now + FUTURE_STAMP_TOLERANCE
    positions = _ancestry_positions(root)

    chronology: dict[str, dict] = {}
    if not log_dir.is_dir():
        return chronology

    for path in sorted(log_dir.rglob("*.yaml")):
        entry_id = path.stem
        info: dict = {"entry_id": entry_id, "path": path, "status": ENTRY_UNVERSIONED,
                      "commit": None, "commit_time": None, "position": None,
                      "claimed": None, "claimed_source": None, "future_stamped": False,
                      "diagnosis": []}
        try:
            doc = parse_strict(path.read_text(encoding="utf-8"))
        except ContinuityError as exc:
            info["status"] = ENTRY_MALFORMED
            info["diagnosis"].append(f"unparseable: {exc}")
            info["effective_time"] = _EPOCH
            chronology[entry_id] = info
            continue

        claimed = _parse_stamp(doc.get("timestamp_utc"))
        info["claimed_source"] = "timestamp_utc"
        if claimed is None:
            claimed = _id_timestamp(entry_id)
            info["claimed_source"] = "entry_id" if claimed else None
        info["claimed"] = claimed

        if positions is not None:
            try:
                rel = str(path.resolve().relative_to(root.resolve()))
            except ValueError:                             # pragma: no cover - defensive
                rel = str(path)
            added = _git(root, "log", "--diff-filter=A", "--format=%H", "-1", "--", rel)
            if added and added.split()[0] in positions:
                sha = added.split()[0]
                info["status"] = ENTRY_COMMITTED
                info["commit"] = sha
                info["position"] = positions[sha]
                ctime = _git(root, "show", "-s", "--format=%cI", sha)
                info["commit_time"] = _parse_stamp(ctime)
            else:
                info["status"] = ENTRY_UNCOMMITTED

        reference = info["commit_time"] if info["status"] == ENTRY_COMMITTED else now
        if claimed is not None and reference is not None and claimed > reference + FUTURE_STAMP_TOLERANCE:
            info["future_stamped"] = True
            against = (f"the commit {info['commit'][:12]} that carries it "
                       f"({reference.isoformat()})" if info["status"] == ENTRY_COMMITTED
                       else f"the present time ({reference.isoformat()})")
            info["diagnosis"].append(
                f"FUTURE_STAMPED: claims {claimed.isoformat()}, which is ahead of {against}. "
                "The claim is retained exactly as recorded and is not used to decide order.")

        info["effective_time"] = min(claimed, ceiling) if claimed is not None else _EPOCH
        info["parent_entry_id"] = doc.get("parent_entry_id")
        chronology[entry_id] = info

    # Declared causality. Every entry names the entry it follows, so an entry that NO other entry
    # claims as its parent is a head of the chain -- nothing recorded itself as coming after it.
    # This is the one ordering signal that survives a copy with no .git, and it cannot be bought
    # with a timestamp: a future-stamped entry that something else already supersedes is named as
    # a parent and is therefore not a head, whatever it claims about the clock.
    claimed_parents = {i.get("parent_entry_id") for i in chronology.values()
                       if i.get("parent_entry_id")}
    for entry_id, info in chronology.items():
        info["superseded_by_chain"] = entry_id in claimed_parents
    return chronology


def order_key(info: dict) -> tuple:
    """Newest is greatest.

    Position in git ancestry decides it wherever git can say. The clamped claim only separates
    entries git places identically -- several entries added by one commit, or a tree with no git
    at all. `truthful` is the final guard: at equal effective time a record that did not lie about
    its stamp outranks one that did, so future-stamping can never be the thing that wins.
    """
    return (
        _STATUS_TIER.get(info["status"], -1),
        info["position"] if info["position"] is not None else -1,
        info.get("effective_time") or _EPOCH,
        0 if info["future_stamped"] else 1,
        info["entry_id"],
    )


def newest_entry(root: Path, log_dir: Path | None = None,
                 now: datetime | None = None) -> tuple[str | None, dict]:
    """The genuinely newest entry, and the full chronology it was chosen from.

    A malformed entry is never returned as newest. It cannot be placed in time, and something that
    cannot be placed in time must not be allowed to define the present.
    """
    chronology = entry_chronology(root, log_dir, now)
    placeable = [i for i in chronology.values() if i["status"] != ENTRY_MALFORMED]
    if not placeable:
        return None, chronology
    # Three sources of order, strongest first, and each one narrows the next:
    #
    #   1. declared causality  an entry something else supersedes is not a candidate at all
    #   2. git ancestry        among the candidates, when the entry file actually entered history
    #   3. the clamped claim   only where neither of the above can separate them
    #
    # A cycle would leave no heads. That is a broken chain, not a licence to fall back silently, so
    # the candidate set widens and the ordering below still has to justify itself.
    heads = [i for i in placeable if not i.get("superseded_by_chain")]
    newest = max(heads or placeable, key=order_key)
    return newest["entry_id"], chronology


def render_chronology(chronology: dict) -> str:
    """Explicit diagnosis, including every record whose stamp is not to be believed."""
    if not chronology:
        return "BUILD LOG CHRONOLOGY: no entries"
    lines = ["BUILD LOG CHRONOLOGY — order is decided by commit ancestry, not by entry_id", ""]
    ordered = sorted(chronology.values(), key=order_key)
    for info in ordered:
        stamp = info["claimed"].isoformat() if info["claimed"] else "(no timestamp)"
        commit = f"{info['commit'][:12]}@{info['position']}" if info["commit"] else "-"
        flag = "FUTURE" if info["future_stamped"] else ("BAD" if info["status"] == ENTRY_MALFORMED
                                                        else "  ok  ")
        lines.append(f"  [{flag:6}] {info['entry_id']}  claims {stamp}  commit {commit}  "
                     f"{info['status']}")
        for note in info["diagnosis"]:
            lines.append(f"            {note}")
    placeable = [i for i in ordered if i["status"] != ENTRY_MALFORMED]
    heads = [i for i in placeable if not i.get("superseded_by_chain")]
    newest = max(heads or placeable, key=order_key, default=None)
    lines += ["", f"  chain_heads: {[i['entry_id'] for i in heads] or 'none'}",
              f"  newest: {newest['entry_id'] if newest else '(none placeable)'}"]
    future = [i["entry_id"] for i in ordered if i["future_stamped"]]
    malformed = [i["entry_id"] for i in ordered if i["status"] == ENTRY_MALFORMED]
    lines.append(f"  future_stamped: {future or 'none'}")
    lines.append(f"  malformed: {malformed or 'none'}")
    return "\n".join(lines)


def active_work_currency(doc: dict, log_dir: Path, root: Path | None = None,
                         now: datetime | None = None) -> tuple[str, str]:
    """Classify the Active Work pointer against the canonical Build Log.

    A record can be syntactically valid, schema valid and reference valid while still describing a
    superseded state -- which is unsafe to resume from and, worse, looks green. Existence and
    currency are different questions and are answered separately (PA ruling 2026-07-30 s13).

    "Newest" comes from `newest_entry`, which asks git rather than the entry's own stamp. Before
    that, a truthfully-stamped record could not become canonical while a single future-dated
    historical ID out-sorted it.
    """
    ref = doc.get("last_build_log_entry")
    if not ref:
        return ACTIVE_WORK_UNRESOLVED, "no last_build_log_entry recorded"
    log_dir = Path(log_dir)
    if not log_dir.is_dir():
        return ACTIVE_WORK_UNRESOLVED, f"no Build Log directory at {log_dir}"
    if root is None:
        # governance/engineering/build-log -> the project root three levels up.
        root = log_dir.parent.parent.parent

    newest, chronology = newest_entry(root, log_dir, now)
    if not chronology:
        # UNRESOLVED means "cannot determine", not "determined to be empty". A pointer naming an
        # entry in a log that demonstrably has none is definitively wrong, not unknowable.
        return ACTIVE_WORK_LOG_MISMATCH, f"{ref} does not exist; the Build Log is empty"

    malformed = sorted(eid for eid, i in chronology.items() if i["status"] == ENTRY_MALFORMED)
    if newest is None:
        return (ACTIVE_WORK_UNRESOLVED,
                f"every Build Log entry is unreadable ({malformed}); which state is current "
                "cannot be determined, and an unreadable record must not become the newest by "
                "default")

    suffix = f"; unreadable entries present and excluded from ordering: {malformed}" if malformed \
        else ""

    if ref in malformed:
        return (ACTIVE_WORK_LOG_MISMATCH,
                f"{ref} exists but is unreadable, so the pointer resolves to nothing usable")

    if ref not in chronology:
        # No entry file, so no commit and no chronology -- only the stamp inside the ID. A pointer
        # promising a record later than everything present is a write that never completed.
        promised = _id_timestamp(ref)
        latest_claim = max((i["claimed"] for i in chronology.values() if i["claimed"]),
                           default=None)
        if promised and latest_claim and promised > latest_claim:
            return (ACTIVE_WORK_FORWARD_REFERENCE,
                    f"{ref} is newer than every entry on disk (newest {newest}); "
                    f"the entry it promises was never written")
        return ACTIVE_WORK_LOG_MISMATCH, f"{ref} does not exist in the Build Log{suffix}"

    if ref != newest:
        basis = chronology[newest]
        how = (f"commit {basis['commit'][:12]} at ancestry position {basis['position']}"
               if basis["commit"] else f"claimed {basis['claimed']}")
        return (ACTIVE_WORK_STALE,
                f"pointer is {ref} but the newest entry is {newest} ({how}); "
                f"Active Work describes a superseded state{suffix}")
    return ACTIVE_WORK_CURRENT, f"pointer matches the newest entry {ref}{suffix}"


def _reference_errors(doc: dict, kind: str, root: Path, git_shas: set[str] | None) -> tuple[list[str], list[str]]:
    """Referential validity. Returns (errors, unresolved).

    Schema-valid records can still be operationally false. Where a reference cannot be checked
    here, it is returned as UNRESOLVED rather than quietly accepted.
    """
    errors: list[str] = []
    unresolved: list[str] = []
    log_dir = root / "governance" / "engineering" / "build-log"

    def entry_exists(entry_id: str) -> bool:
        return any(p.stem == entry_id for p in log_dir.rglob("*.yaml"))

    if kind == "entry":
        for field_name in ("parent_entry_id", "correction_of"):
            ref = doc.get(field_name)
            if ref and not entry_exists(ref):
                errors.append(f"{field_name} references {ref} which does not exist")

    if kind == "active_work":
        # Existence is not currency. Measured: two hand-edited updates to this field were no-ops
        # (the edit matched a quoting style the file did not use), log validate stayed GREEN, and
        # the projection described a superseded state for two commits.
        state, detail = active_work_currency(doc, log_dir, root)
        policy = continuation_for(state)
        if policy.severity == "BLOCKED":
            errors.append(f"{state}: {detail} (PBG-CONT-002)")
        elif policy.severity == "AMBER":
            unresolved.append(f"{state}: {detail}")

    for sha_field in ("baseline_sha", "current_sha", "last_completed_checkpoint_sha",
                      "continuity_record_commit"):
        sha = doc.get(sha_field)
        if not sha or sha == "PENDING":
            continue
        if not SHA_RE.match(str(sha)):
            errors.append(f"{sha_field} {sha!r} is not a valid Git object name")
        elif git_shas is None:
            unresolved.append(f"{sha_field} {sha[:9]} not checked — repository unavailable")
        elif not any(known.startswith(sha) or sha.startswith(known) for known in git_shas):
            errors.append(f"{sha_field} {sha[:9]} does not exist in this repository")

    return errors, unresolved


def validate(
    text: str,
    kind: str,
    root: Path,
    schema_dir: Path | None = None,
    git_shas: set[str] | None = None,
    now: datetime | None = None,
    creating: bool = False,
) -> ValidationResult:
    """Full validation in order. Stops at the first stage that fails, and names that stage."""
    schema_dir = schema_dir or (root / "schemas")

    # 1. syntax
    try:
        doc = parse_strict(text)
    except ContinuityError as exc:
        return ValidationResult(False, "syntax", [str(exc)])

    # 2. schema
    schema_file = {"entry": "build-log-entry.schema.yaml",
                   "active_work": "active-work.schema.yaml"}[kind]
    errors = _schema_errors(doc, schema_dir / schema_file)
    if errors:
        return ValidationResult(False, "schema", errors)

    # 3. semantic
    errors = _semantic_errors(doc, kind, now=now, creating=creating)
    if errors:
        return ValidationResult(False, "semantic", errors)

    # 4. reference
    errors, unresolved = _reference_errors(doc, kind, root, git_shas)
    if errors:
        return ValidationResult(False, "reference", errors, unresolved)

    # 5. secrets — reported by class and location, never by value
    findings = scanning.scan_secrets(root, paths=[])       # scan the text, not the tree
    tmp_findings = _scan_text_for_secrets(text)
    if tmp_findings:
        return ValidationResult(False, "secret_scan", tmp_findings)

    return ValidationResult(True, "complete", [], unresolved)


def _scan_text_for_secrets(text: str) -> list[str]:
    """Secret scan over record text. Reports pattern class and line; never the matched value."""
    hits: list[str] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if scanning._PLACEHOLDER.search(line) or scanning.FIXTURE_EXEMPTION.search(line):
            continue
        for name, pattern in scanning.SECRET_PATTERNS:
            if pattern.search(line):
                hits.append(f"line {lineno}: possible {name} (value not shown)")
                break
    return hits


# --------------------------------------------------------------------------------------------- #
# Write — nothing becomes canonical until it has been read back
# --------------------------------------------------------------------------------------------- #

def serialise(doc: dict) -> str:
    """Deterministic serialisation. Agents do not hand-format canonical records."""
    return yaml.safe_dump(doc, sort_keys=False, default_flow_style=False, allow_unicode=True,
                          width=100)


def write_entry(
    doc: dict,
    root: Path,
    git_shas: set[str] | None = None,
    fsync: bool = True,
) -> Path:
    """Validate, write to a temporary file, re-parse it, then atomically place it.

    The re-parse is the point. Serialisation can succeed and still produce a file that does not
    load — which is precisely how the bootstrap entry reached canonical state broken.
    """
    entry_id = doc.get("entry_id", "")
    if not ENTRY_ID_RE.match(str(entry_id)):
        raise ContinuityError(f"entry_id {entry_id!r} does not match BL-<UTC>-<ID>")

    text = serialise(doc)

    result = validate(text, "entry", root, git_shas=git_shas, creating=True)
    if not result.ok:
        raise ContinuityError(f"refused at {result.stage}: {'; '.join(result.errors)}")

    ts = doc["timestamp_utc"]
    target_dir = root / "governance" / "engineering" / "build-log" / ts[0:4] / ts[5:7]
    target = target_dir / f"{entry_id}.yaml"

    # Append-only: an existing entry is never overwritten. Corrections supersede.
    if target.exists():
        raise ContinuityError(
            f"{entry_id} already exists — history is append-only; file a correction entry instead"
        )

    target_dir.mkdir(parents=True, exist_ok=True)
    tmp = target_dir / f".{entry_id}.tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            if fsync:
                try:
                    os.fsync(fh.fileno())
                except OSError:          # pragma: no cover - not all filesystems support it
                    pass

        # Read back what actually landed on disk, and validate it again.
        written = tmp.read_text(encoding="utf-8")
        recheck = validate(written, "entry", root, git_shas=git_shas, creating=True)
        if not recheck.ok:
            raise ContinuityError(
                f"written file failed re-validation at {recheck.stage}: {'; '.join(recheck.errors)}"
            )

        os.replace(tmp, target)          # atomic within a filesystem
    finally:
        if tmp.exists():
            tmp.unlink()

    return target


def new_entry_id(now: datetime, short_id: str) -> str:
    """BL-<UTC compact>-<4 hex>. The caller supplies the id so this stays deterministic."""
    if now.tzinfo is None:
        raise ContinuityError("entry timestamps must be timezone-aware UTC")
    stamp = now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"BL-{stamp}-{short_id.upper()}"


def load_entries(root: Path) -> list[dict]:
    """Every canonical entry, ordered by timestamp then id — never by file position."""
    log_dir = root / "governance" / "engineering" / "build-log"
    entries = []
    for path in sorted(log_dir.rglob("*.yaml")):
        try:
            entries.append(parse_strict(path.read_text(encoding="utf-8")))
        except ContinuityError as exc:
            entries.append({"entry_id": path.stem, "_invalid": str(exc)})
    return sorted(entries, key=lambda d: (d.get("timestamp_utc", ""), d.get("entry_id", "")))


# --------------------------------------------------------------------------------------------- #
# Observation — the tool supplies what it can see, the agent supplies only meaning
# --------------------------------------------------------------------------------------------- #

def _git(root: Path, *args: str) -> str:
    import subprocess
    try:
        r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
        return r.stdout.strip()
    except OSError:                                            # pragma: no cover
        return ""


def observe(root: Path) -> dict:
    """Everything the tool can determine for itself.

    An agent supplying its own branch or SHA is supplying a claim, not an observation. Where the
    tool can see the value it uses what it sees — PBG-CONT-008 wants exact Git identity, and a
    remembered SHA is not identity.
    """
    return {
        "repository": _git(root, "config", "--get", "remote.origin.url") or "local",
        "branch": _git(root, "rev-parse", "--abbrev-ref", "HEAD"),
        "worktree": str(root),
        "current_sha": _git(root, "rev-parse", "HEAD"),
        "working_tree_state": "dirty" if _git(root, "status", "--porcelain") else "clean",
        "known_shas": set(_git(root, "log", "--format=%H").split()),
    }


#: Fields the agent supplies. Anything else is observed or derived, never accepted from input.
ENTRY_SCHEMA_VERSION = 2

AGENT_SUPPLIED = frozenset({
    "action_summary", "status", "next_safe_action", "expected_next_actor", "work_type",
    "phase", "findings", "changes", "tests", "decisions", "blockers", "risks",
    "held_actions", "evidence_references", "correction_of", "parent_entry_id", "defect",
    "implemented", "known_incomplete", "notes",
})


def build_entry(
    root: Path,
    *,
    actor: str,
    role: str,
    authority_id: str,
    content: dict,
    now: datetime,
    short_id: str,
    project: str = "PBGv2",
    causal_owner: str | None = None,
) -> dict:
    """Assemble a canonical entry. The caller never formats YAML."""
    rejected = set(content) - AGENT_SUPPLIED
    if rejected:
        raise ContinuityError(
            f"these fields are observed by the tool and may not be supplied: {sorted(rejected)}"
        )

    obs = observe(root)
    entry = {
        "schema_version": ENTRY_SCHEMA_VERSION,
        "entry_id": new_entry_id(now, short_id),
        "timestamp_utc": now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "record_origin": "TOOLING",
        "tooling_available_at_capture": True,
        "project": project,
        "actor": actor,
        "role": role,
        "causal_owner": causal_owner or actor,
        "authority_id": authority_id,
        "phase": content.get("phase", "UNSPECIFIED"),
        "repository": obs["repository"],
        "branch": obs["branch"],
        "worktree": obs["worktree"],
        "current_sha": obs["current_sha"],
    }
    for key, value in content.items():
        if key != "phase":
            entry[key] = value
    entry.setdefault("status", "IN_PROGRESS")
    return entry


def add_entry(root: Path, **kwargs) -> Path:
    """Generate, validate and atomically write one entry. The whole point of the command."""
    entry = build_entry(root, **kwargs)
    return write_entry(entry, root, git_shas=observe(root)["known_shas"])


# --------------------------------------------------------------------------------------------- #
# Generated projections — views, never inputs
# --------------------------------------------------------------------------------------------- #

def _projection_header(root: Path, generator_version: str) -> list[str]:
    obs = observe(root)
    return [
        "<!--",
        "  GENERATED PROJECTION — do not edit. Regenerate with: pbg log rebuild",
        "  Canonical truth is the YAML under governance/engineering/.",
        f"  source_repository : {obs['repository']}",
        f"  source_sha        : {obs['current_sha']}",
        f"  generator_version : {generator_version}",
        "-->",
        "",
    ]


def render_build_log(root: Path, generator_version: str = "1") -> str:
    """Chronological human view of the canonical entries."""
    lines = _projection_header(root, generator_version)
    lines += ["# Build Log", ""]
    for e in load_entries(root):
        if "_invalid" in e:
            lines += [f"## {e['entry_id']} — UNREADABLE", "", f"> {e['_invalid']}", ""]
            continue
        lines += [
            f"## {e['entry_id']} — {e.get('status','')}",
            "",
            f"- **when** {e.get('timestamp_utc','')} · **actor** {e.get('actor','')} "
            f"({e.get('role','')}) · **authority** {e.get('authority_id','')}",
            f"- **sha** `{(e.get('current_sha') or 'n/a')[:12]}` · **branch** {e.get('branch','')}",
        ]
        if e.get("correction_of"):
            lines.append(f"- **corrects** {e['correction_of']}")
        lines += ["", (e.get("action_summary") or "").strip(), ""]
        if e.get("next_safe_action"):
            lines += [f"**Next safe action:** {e['next_safe_action'].strip()}", ""]
    return "\n".join(lines) + "\n"


def render_active_work(root: Path, generator_version: str = "1") -> str:
    aw_path = root / "governance" / "engineering" / "ACTIVE_WORK.yaml"
    aw = parse_strict(aw_path.read_text(encoding="utf-8"))
    lines = _projection_header(root, generator_version)
    lines += [
        f"# Active Work — {aw.get('project','')}", "",
        f"**Status** `{aw.get('status','')}` · **Phase** {aw.get('current_phase','')} · "
        f"**Block** {aw.get('current_block','')}", "",
        f"- **authority** {aw.get('active_authority_id','')}",
        f"- **branch** {aw.get('branch','')} · **worktree** `{aw.get('worktree','')}`",
        f"- **last checkpoint** `{(aw.get('last_completed_checkpoint_sha') or 'n/a')[:12]}`",
        f"- **last entry** {aw.get('last_build_log_entry','')}",
        "", "## Next safe action", "", (aw.get("next_safe_action") or "").strip(), "",
    ]
    if aw.get("held_actions"):
        lines += ["## Held actions", ""]
        for h in aw["held_actions"]:
            lines.append(f"- **{h.get('id')}** — {h.get('status')} · next: {h.get('next_actor')}")
        lines.append("")
    if aw.get("blockers"):
        lines += ["## Blockers", ""] + [f"- {b}" for b in aw["blockers"]] + [""]
    return "\n".join(lines) + "\n"


def rebuild_projections(root: Path) -> list[Path]:
    """Regenerate the Markdown views from canonical YAML, overwriting any hand-edit."""
    eng = root / "governance" / "engineering"
    written = []
    for name, text in (("BUILD_LOG.md", render_build_log(root)),
                       ("ACTIVE_WORK.md", render_active_work(root))):
        path = eng / name
        path.write_text(text, encoding="utf-8")
        written.append(path)
    return written


# --------------------------------------------------------------------------------------------- #
# Resume classification
# --------------------------------------------------------------------------------------------- #

CONTINUITY_MATCH = "CONTINUITY_MATCH"
CONTINUITY_FILE_MISSING = "CONTINUITY_FILE_MISSING"
CONTINUITY_SYNTAX_INVALID = "CONTINUITY_SYNTAX_INVALID"
CONTINUITY_SCHEMA_INVALID = "CONTINUITY_SCHEMA_INVALID"
CONTINUITY_SEMANTIC_INVALID = "CONTINUITY_SEMANTIC_INVALID"
CONTINUITY_REFERENCE_INVALID = "CONTINUITY_REFERENCE_INVALID"
CONTINUITY_REFERENCE_UNRESOLVED = "CONTINUITY_REFERENCE_UNRESOLVED"
CONTINUITY_SECRET_REJECTED = "CONTINUITY_SECRET_REJECTED"
CONTINUITY_DRIFT = "CONTINUITY_DRIFT"
CONTINUITY_AUTHORITY_CONFLICT = "CONTINUITY_AUTHORITY_CONFLICT"

_STAGE_TO_CLASS = {
    "syntax": CONTINUITY_SYNTAX_INVALID,
    "schema": CONTINUITY_SCHEMA_INVALID,
    "semantic": CONTINUITY_SEMANTIC_INVALID,
    "reference": CONTINUITY_REFERENCE_INVALID,
    "secret_scan": CONTINUITY_SECRET_REJECTED,
}

RECOVERY_MATCH = "RECOVERY_MATCH"
RECOVERY_DRIFT = "RECOVERY_DRIFT"
RECOVERY_UNCOMMITTED_WORK = "RECOVERY_UNCOMMITTED_WORK"
RECOVERY_CONTINUITY_INVALID = "RECOVERY_CONTINUITY_INVALID"
RECOVERY_REFERENCE_UNRESOLVED = "RECOVERY_REFERENCE_UNRESOLVED"
RECOVERY_BOOTSTRAP_REQUIRED = "RECOVERY_BOOTSTRAP_REQUIRED"


@dataclass
class ResumeResult:
    continuity_class: str
    recovery: str
    resume_verdict: str          # RESUME_GREEN | RESUME_AMBER | RESUME_BLOCKED
    findings: list[str] = field(default_factory=list)
    observed: dict = field(default_factory=dict)
    recorded: dict = field(default_factory=dict)

    def render(self) -> str:
        lines = [
            f"Continuity : {self.continuity_class}",
            f"Recovery   : {self.recovery}",
            f"Verdict    : {self.resume_verdict}",
        ]
        for k in ("branch", "current_sha", "working_tree_state"):
            if k in self.recorded or k in self.observed:
                lines.append(f"  {k:<20} recorded={self.recorded.get(k)!r} "
                             f"observed={self.observed.get(k)!r}")
        lines += [f"  - {f}" for f in self.findings]
        return "\n".join(lines)


def resume(root: Path, framework_root: Path | None = None) -> ResumeResult:
    """Reconcile recorded continuity against observed state, and classify precisely.

    A malformed record blocks normal resume but permits read-only diagnosis. It is never ignored
    in favour of an older convenient checkpoint or of conversational memory.

    `framework_root` locates the schemas. In this repository the records and the schemas share a
    root; in a consuming project they do not -- the records are the project's and the schemas are
    the pinned framework's. Defaulting the two to one root made resume work only where PBG happens
    to be developed, which is the one place it matters least.
    """
    aw_path = root / "governance" / "engineering" / "ACTIVE_WORK.yaml"
    if not aw_path.is_file():
        # A brand-new project has no continuity because none has been written yet. That is a
        # bootstrap condition, not a corrupted or contradicted record, and reusing a recovery
        # mismatch state for it would tell an operator to investigate damage that does not exist
        # (PA ruling 2026-07-30 s9).
        log_dir = root / "governance" / "engineering" / "build-log"
        never_started = not log_dir.is_dir() or not any(log_dir.rglob("*.yaml"))
        if never_started:
            return ResumeResult(
                NEW_PROJECT_CONTINUITY_NOT_INITIALISED, RECOVERY_BOOTSTRAP_REQUIRED,
                "RESUME_BLOCKED",
                ["no continuity has been written yet; this is a new project, not a damaged one",
                 "initialise Active Work and the first Build Log entry before resuming"])
        return ResumeResult(CONTINUITY_FILE_MISSING, RECOVERY_CONTINUITY_INVALID, "RESUME_BLOCKED",
                            ["ACTIVE_WORK.yaml is absent but Build Log entries exist; "
                             "the record was lost, not never written"])

    obs = observe(root)
    text = aw_path.read_text(encoding="utf-8")
    schema_dir = (Path(framework_root) / "schemas") if framework_root else None
    result = validate(text, "active_work", root, schema_dir=schema_dir,
                      git_shas=obs["known_shas"])
    if not result.ok:
        return ResumeResult(
            _STAGE_TO_CLASS.get(result.stage, CONTINUITY_SCHEMA_INVALID),
            RECOVERY_CONTINUITY_INVALID, "RESUME_BLOCKED",
            [f"{result.stage}: {e}" for e in result.errors]
            + ["read-only diagnosis and repair proposal permitted; normal resume is not"],
        )

    aw = parse_strict(text)
    findings: list[str] = []
    recorded = {"branch": aw.get("branch"), "worktree": aw.get("worktree"),
                "current_sha": aw.get("last_completed_checkpoint_sha")}

    drift = False
    if aw.get("branch") and aw["branch"] != obs["branch"]:
        findings.append(f"branch drift: recorded {aw['branch']} observed {obs['branch']}")
        drift = True
    ckpt = aw.get("last_completed_checkpoint_sha")
    if ckpt and ckpt not in obs["known_shas"]:
        findings.append(f"checkpoint {ckpt[:9]} is not reachable in this repository")
        drift = True

    uncommitted = obs["working_tree_state"] == "dirty"
    if uncommitted:
        findings.append("uncommitted working-tree changes present")

    if result.unresolved:
        findings.extend(result.unresolved)
        return ResumeResult(CONTINUITY_REFERENCE_UNRESOLVED, RECOVERY_REFERENCE_UNRESOLVED,
                            "RESUME_AMBER", findings, obs, recorded)
    if drift:
        return ResumeResult(CONTINUITY_DRIFT, RECOVERY_DRIFT, "RESUME_AMBER",
                            findings + ["reconcile and report; never silently correct"],
                            obs, recorded)
    if uncommitted:
        return ResumeResult(CONTINUITY_MATCH, RECOVERY_UNCOMMITTED_WORK, "RESUME_AMBER",
                            findings, obs, recorded)
    return ResumeResult(CONTINUITY_MATCH, RECOVERY_MATCH, "RESUME_GREEN", findings, obs, recorded)


# --------------------------------------------------------------------------------------------- #
# Checkpoint
# --------------------------------------------------------------------------------------------- #

def update_active_work(root: Path, changes: dict, *, now: datetime | None = None) -> Path:
    """Apply field changes to Active Work through parse -> validate -> atomic write -> re-parse.

    Exists because hand-editing this file failed silently twice: a string substitution matched a
    quoting style the file did not use, changed nothing, raised nothing, and left the projection
    describing a superseded state. A record that is *generated* cannot fail that way -- the write
    is refused if the result would be invalid, and a no-op change is visible because the caller
    names the field rather than a text fragment (PBG-CONT-002).
    """
    aw_path = root / "governance" / "engineering" / "ACTIVE_WORK.yaml"
    aw = parse_strict(aw_path.read_text(encoding="utf-8"))
    unknown = set(changes) - set(aw)
    if unknown:
        raise ContinuityError(f"refusing to introduce unknown Active Work fields: {sorted(unknown)}")
    aw.update(changes)
    if now is not None:
        aw["updated_utc"] = now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    obs = observe(root)
    text = serialise(aw)
    check = validate(text, "active_work", root, git_shas=obs["known_shas"])
    if not check.ok:
        raise ContinuityError(f"Active Work update refused at {check.stage}: {'; '.join(check.errors)}")

    tmp = aw_path.with_suffix(".tmp")
    tmp.write_text(text, encoding="utf-8")
    if not validate(tmp.read_text(encoding="utf-8"), "active_work", root,
                    git_shas=obs["known_shas"]).ok:      # pragma: no cover - defensive
        tmp.unlink()
        raise ContinuityError("Active Work failed re-validation after write")
    os.replace(tmp, aw_path)
    return aw_path


@dataclass
class CheckpointResult:
    entry_path: Path | None
    entry_id: str | None
    source_checkpoint_sha: str
    clean: bool
    findings: list[str] = field(default_factory=list)

    def render(self) -> str:
        lines = [
            f"Checkpoint : {'CLEAN' if self.clean else 'AMBER'}",
            f"Entry      : {self.entry_id or '(not written)'}",
            f"Source SHA : {self.source_checkpoint_sha[:12] if self.source_checkpoint_sha else 'n/a'}",
        ]
        lines += [f"  - {f}" for f in self.findings]
        return "\n".join(lines)


def checkpoint(
    root: Path,
    *,
    actor: str,
    role: str,
    authority_id: str,
    content: dict,
    now: datetime,
    short_id: str,
    project: str = "PBGv2",
) -> CheckpointResult:
    """Create a durable checkpoint: an entry, an updated Active Work, and regenerated views.

    Three checkpoint identities are kept distinct, because conflating them is how SHA
    self-reference creeps back in:

        source_checkpoint_sha    the source state being checkpointed
        continuity_record_commit the commit containing the continuity record
        active_work_update_commit an optional later commit resolving forward references

    A checkpoint never reports CLEAN while a blocking condition is unresolved.
    """
    obs = observe(root)
    findings: list[str] = []
    clean = True

    if obs["working_tree_state"] == "dirty":
        findings.append("uncommitted changes present at checkpoint time")
        clean = False

    resumed = resume(root)
    if resumed.resume_verdict == "RESUME_BLOCKED":
        findings.append(f"continuity invalid: {resumed.continuity_class}")
        clean = False
    elif resumed.recovery == RECOVERY_DRIFT:
        findings.append("recorded and observed state disagree; reconcile before relying on this")
        clean = False

    entry_content = dict(content)
    entry_content.setdefault("status", "CHECKPOINT")
    path = add_entry(root, actor=actor, role=role, authority_id=authority_id,
                     content=entry_content, now=now, short_id=short_id, project=project)
    entry_id = path.stem

    # Update Active Work to point at the new entry and the source checkpoint.
    aw_path = root / "governance" / "engineering" / "ACTIVE_WORK.yaml"
    aw = parse_strict(aw_path.read_text(encoding="utf-8"))
    aw["updated_utc"] = now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    aw["last_build_log_entry"] = entry_id
    aw["last_completed_checkpoint_sha"] = obs["current_sha"]
    aw["working_tree_state"] = obs["working_tree_state"]

    aw_text = serialise(aw)
    check = validate(aw_text, "active_work", root, git_shas=obs["known_shas"])
    if not check.ok:
        raise ContinuityError(
            f"Active Work update refused at {check.stage}: {'; '.join(check.errors)}"
        )
    tmp = aw_path.with_suffix(".tmp")
    tmp.write_text(aw_text, encoding="utf-8")
    if not validate(tmp.read_text(encoding="utf-8"), "active_work", root,
                    git_shas=obs["known_shas"]).ok:      # pragma: no cover - defensive
        tmp.unlink()
        raise ContinuityError("Active Work failed re-validation after write")
    os.replace(tmp, aw_path)

    rebuild_projections(root)

    return CheckpointResult(path, entry_id, obs["current_sha"], clean, findings)
