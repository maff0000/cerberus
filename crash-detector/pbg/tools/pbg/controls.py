"""Canonical control loading and integrity.

controls/*.yaml is the source of truth for control identity, applicability, required outcome and
evidence contract (PBG-FWK-051). Prose documents render these; they do not define them.

Implements PBG-CTRL-001: IDs are unique, never reused, and never tied to document placement.

INDEPENDENT ASSURANCE FINDING U3-3 — WHY EVERY READ IN THIS MODULE IS TYPED.

    controls SCALAR / LIST / WRONG-OBJECT each exited 1 with a raw traceback, no structured
    finding, no file named and no field named:

        File ".../tools/pbg/controls.py", line 63, in all_controls
            cid = record.get("control_id")
        AttributeError: 'str' object has no attribute 'get'

    `controls: null` WAS handled, which made the path look covered. It was not: `or []` guards
    against None and against nothing else, because `"hello" or []` is `"hello"`.

The repair is deliberately NOT a try/except at the crash site. Every reader here goes through
`validation.load_governed_mapping` and `validation.mappings_at`, which are the same accessors the
evidence path uses, so the class is closed in one place rather than repaired one line at a time.

FAIL CLOSED, AND WHOLE. A structurally invalid control document contributes NO controls at all —
not its well-formed neighbours inside the same file, and never a control read from a parent
directory, a sibling project or the current working directory. A control corpus that is quietly
smaller than the files say it is would be a framework that silently stopped enforcing something.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from . import validation as vld

CONTROL_ID_RE = re.compile(
    r"^PBG-(CTRL|AUTH|BOOT|SOD|PID|BP|WORK|CONT|SOV|GIT|CI|DEPLOY|RT|SEC|OBS|DATA|ASSURE|EVID|INC|PORT|FWK)-[0-9]{3}$"
)

#: Retired IDs are recorded here forever. A number is never recycled, even after retirement.
RETIRED_IDS_FILE = "controls/RETIRED_IDS.yaml"


@dataclass(frozen=True)
class ControlIssue:
    control_id: str
    path: str
    reason: str

    def render(self) -> str:
        who = self.control_id or "(file)"
        return f"{self.path}: {who}: {self.reason}"


def load_control_documents(root: Path) -> tuple[dict[str, dict], list[vld.ValidationFinding]]:
    """Every STRUCTURALLY USABLE controls/*.yaml, and every reason one was refused.

    This is the single seam independent Assurance finding U3-3 asks for. Four things happen here and nowhere else:

        CONTAINMENT   the file must RESOLVE inside `root`. A `controls/x.yaml` symlinked to a
                      parent's, a sibling project's or the working directory's control file is
                      refused — "no fallback to a foreign control", judged on where the path lands
                      rather than how it is spelled.
        PARSE         strictly, so a duplicate control declaration is a finding and not a silent
                      last-value-wins.
        ROOT TYPE     the document must be a mapping. SCALAR and LIST die here, named.
        FIELD TYPE    `controls` must be a list OF MAPPINGS. WRONG-OBJECT dies here, named, and one
                      malformed entry refuses the whole document rather than activating the rest.

    A refused document is ABSENT from the returned mapping and PRESENT in the findings. No caller
    can read a control out of a document that did not survive, and no caller can fail to notice
    that one did not.
    """
    documents: dict[str, dict] = {}
    findings: list[vld.ValidationFinding] = []
    root = Path(root)
    controls_dir = root / "controls"
    if not controls_dir.is_dir():
        return documents, findings

    for path in sorted(controls_dir.glob("*.yaml")):
        if path.name == "RETIRED_IDS.yaml":
            continue
        rel = f"controls/{path.name}"
        doc, problems = vld.load_governed_mapping(path, root=root, path_label=rel)
        if problems:
            findings.extend(problems)
            continue
        _records, record_problems = vld.mappings_at(doc, "controls", path=rel, field="controls")
        if record_problems:
            findings.extend(record_problems)
            continue
        documents[rel] = doc
    return documents, findings


def load_control_files(root: Path) -> dict[str, dict]:
    """Load every structurally usable controls/*.yaml. Returns {relative_path: parsed}.

    Backwards-compatible view of `load_control_documents` for callers that already have their own
    reporting surface. It CANNOT raise and it CANNOT return a document a `.get()` would explode on;
    callers that need to report why a file is missing use `load_control_documents` directly.
    """
    return load_control_documents(root)[0]


def control_records(doc: dict, rel: str) -> list[dict]:
    """The `controls:` entries of an already-validated document, typed.

    Never reached with a malformed document — `load_control_documents` refuses those — but it reads
    through the typed accessor anyway, because a second reader that quietly assumed a shape is how
    this class came back the last three times.
    """
    return vld.mappings_at(doc, "controls", path=rel, field="controls")[0]


def load_retired_ids(root: Path) -> set[str]:
    """The retired-ID register, typed. A malformed register retires nothing and says so."""
    return retired_ids_checked(root)[0]


def retired_ids_checked(root: Path) -> tuple[set[str], list[vld.ValidationFinding]]:
    root = Path(root)
    path = root / RETIRED_IDS_FILE
    if not path.is_file():
        return set(), []
    doc, problems = vld.load_governed_mapping(path, root=root, path_label=RETIRED_IDS_FILE)
    if problems:
        return set(), problems
    values, type_problems = vld.sequence_at(doc, "retired", path=RETIRED_IDS_FILE, field="retired")
    if type_problems:
        return set(), type_problems
    return {str(v) for v in values if v is not None}, []


def all_controls(root: Path) -> dict[str, dict]:
    """Flatten to {control_id: record}. Structurally refused documents contribute nothing."""
    return all_controls_checked(root)[0]


def all_controls_checked(root: Path) -> tuple[dict[str, dict], list[vld.ValidationFinding]]:
    """`all_controls`, plus the structural reasons any control document was not read at all.

    Callers that gate on the corpus use THIS one. A caller that takes only the mapping cannot tell
    "there is no such control" apart from "the file declaring it could not be read", and those are
    different facts with different correct responses.
    """
    flat: dict[str, dict] = {}
    documents, findings = load_control_documents(root)
    for rel, doc in documents.items():
        for record in control_records(doc, rel):
            cid = vld.scalar_at(record, "control_id", path=rel, field="control_id")[0]
            if cid:
                flat[str(cid)] = record
    return flat, findings


def structural_issues(root: Path) -> list[ControlIssue]:
    """Every control document that could not be read, as reportable issues.

    independent Assurance finding U3-3's deliverable in one function: the exact file, the exact field, the expected type and
    the observed type, on the surface `pbg validate` already prints — rather than a traceback on
    stderr and exit 1.
    """
    _documents, findings = load_control_documents(root)
    _retired, retired_findings = retired_ids_checked(root)
    return [ControlIssue("", f.path, f"[{f.stage}/{f.code}]"
                         + (f" {f.field}:" if f.field else "") + f" {f.detail}")
            for f in (*findings, *retired_findings)]


def check_integrity(root: Path) -> list[ControlIssue]:
    """Structural checks that a JSON Schema cannot express.

    A structurally unreadable control document is reported FIRST and the corpus is not evaluated on
    top of it. Reporting "no duplicate IDs found" over a corpus that failed to load would be a pass
    obtained by not looking, which is the failure class this whole cycle is about.
    """
    structural = structural_issues(root)
    if structural:
        return structural

    issues: list[ControlIssue] = []
    seen: dict[str, str] = {}
    retired = load_retired_ids(root)

    for rel, doc in load_control_files(root).items():
        domain = vld.scalar_at(doc, "domain", path=rel, field="domain")[0]
        if not domain:
            issues.append(ControlIssue("", rel, "control file has no domain"))
            continue

        for record in control_records(doc, rel):
            cid = str(vld.scalar_at(record, "control_id", path=rel, field="control_id")[0] or "")

            if not CONTROL_ID_RE.match(cid):
                issues.append(ControlIssue(cid, rel, "control_id does not match PBG-<DOMAIN>-<NNN>"))
                continue

            # PBG-CTRL-001: an ID is unique across the whole framework.
            if cid in seen:
                issues.append(
                    ControlIssue(cid, rel, f"duplicate control_id — already defined in {seen[cid]}")
                )
                continue
            seen[cid] = rel

            # PBG-CTRL-001: numbers are never recycled after retirement.
            if cid in retired:
                issues.append(
                    ControlIssue(cid, rel, "control_id was retired and must never be reused")
                )

            # The ID's domain must match the file's declared domain — IDs are conceptual, and a
            # control filed under the wrong domain reintroduces placement-based identity.
            id_domain = cid.split("-")[1]
            if id_domain != domain:
                issues.append(
                    ControlIssue(cid, rel, f"domain {id_domain} does not match file domain {domain}")
                )

            # A superseded control must name its successor, and vice versa.
            status = record.get("status")
            if status == "SUPERSEDED" and not record.get("superseded_by"):
                issues.append(ControlIssue(cid, rel, "status SUPERSEDED requires superseded_by"))
            if record.get("superseded_by") and status != "SUPERSEDED":
                issues.append(ControlIssue(cid, rel, "superseded_by set but status is not SUPERSEDED"))

            # PBG-CTRL-002: a BINDING control cannot rest on the semantic layer alone.
            if record.get("mandatory_or_conditional") == "MANDATORY":
                # Structured axes, not prose. The old form asked whether the control had SAID
                # something about enforcement; a mandatory control could satisfy it with a
                # sentence. This asks whether it has DECLARED a mechanism, and CHECK_REF has to
                # resolve and bind (checked separately).
                discharge = record.get("discharge_mechanism")
                verification = record.get("verification_mechanism")
                if not discharge or not verification:
                    issues.append(
                        ControlIssue(
                            cid,
                            rel,
                            "MANDATORY control declares no discharge or verification mechanism "
                            "(PBG-CTRL-002)",
                        )
                    )

            # PBG-FWK-011: control records never carry a framework version.
            #
            # Typed rather than `or []`: a STRING here would join into its own characters and the
            # regex would then search a string that is technically correct and semantically
            # meaningless — a confident wrong answer instead of an error.
            ref_values, ref_problems = vld.sequence_at(
                record, "authoritative_references", path=rel, field="authoritative_references")
            for problem in ref_problems:
                issues.append(ControlIssue(cid, rel, f"[{problem.stage}/{problem.code}] "
                                                     f"{problem.detail}"))
            refs = " ".join(str(r) for r in ref_values)
            if re.search(r"(?i)\bPBG-2\.\d+\.\d+", refs):
                issues.append(
                    ControlIssue(cid, rel, "authoritative_references carries a framework version (PBG-FWK-011)")
                )

    return issues


def resolve_references(root: Path, text: str) -> list[str]:
    """Return control IDs cited in text that do not exist. Keeps prose honest about IDs.

    independent Assurance finding U3-3's reported traceback arrived HERE, via `cli.py:152`. It no longer can: the corpus is
    loaded through the typed layer, and a corpus that could not be loaded reports every cited ID as
    undefined rather than raising — fail closed, because the alternative is a document whose
    citations were never actually checked passing as though they had been.
    """
    known = set(all_controls(root))
    cited = set(re.findall(r"\bPBG-[A-Z]+-[0-9]{3}\b", text))
    return sorted(cited - known)
