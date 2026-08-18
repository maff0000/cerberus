"""Required Test Register — the minimal validator (PBGV2-REGISTER-MINIMAL-0001).

Implements contract `REQUIRED-TEST-REGISTER-CONTRACT-v1`: the smallest format that makes
registers interoperable, and the validator that COMPUTES status rather than reading anyone's
assertion of it.

The five checks (contract §4):

1. POPULATION       — the criteria census is derived from the referenced PID independently and
                      compared by `criterion_id`. A PID criterion with no register entry is
                      NOT_EVALUATED and a reported defect. A register entry with no PID lineage
                      is UNTRACED. The register may not define its own population.
2. NEGATIVE CONTROL — every test must reference a run record in which a representative violation
                      of the PROPOSITION was planted and detected. Detection is a CONTRAST: the
                      same declared command passes on the clean subject and fails on the violated
                      one. Evidence that only shows the harness failing (the clean arm fails too,
                      or is absent) yields UNDECIDABLE — never PASS.
3. EXECUTION        — the execution contract is declared and resolvable.
4. INDEPENDENCE     — the run record names the executing party and its independence class.
5. SELF-GRADING     — any status-like field present in the register is a VALIDATION FAILURE,
                      not an input. The register carries obligations; status is computed here.

Statuses are computed, never written: PASS, FAIL, UNKNOWN, UNDECIDABLE, NOT_EVALUATED — and the
derived PID_ACCEPTANCE_SATISFIED, which is a product-assurance status, NOT a kernel lifecycle
state, and carries no authority to alter governed standing.

GATE RULE. Any MANDATORY criterion not PASS means the gate does not open. There is no waiver
flag, and none may be added: the PL may never waive a mandatory criterion. A non-PASS mandatory
criterion is always listed IN FULL in the report — durable visibility is the point.

ACCEPTANCE SEMANTICS AND EXIT CODES. The register's `acceptance_semantics` is prose the Auditor
attacks; the machine-checkable half is the declared `execute` command, which must terminate 0
exactly when those semantics are met. The validator computes from recorded execution facts
(commands and exit codes in run records); it never reads a satisfied/failed assertion.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------------------------- #
# vocabulary
# ---------------------------------------------------------------------------------------------- #

PASS = "PASS"
FAIL = "FAIL"
UNKNOWN = "UNKNOWN"
UNDECIDABLE = "UNDECIDABLE"
NOT_EVALUATED = "NOT_EVALUATED"

#: worst-first: a criterion's status is the worst of its tests' statuses.
_SEVERITY = {FAIL: 0, UNDECIDABLE: 1, UNKNOWN: 2, NOT_EVALUATED: 3, PASS: 4}

OBLIGATIONS = {"MANDATORY", "ADVISORY"}
ORIGINS = {"PID", "DEFECT", "AUDIT", "INCIDENT", "PO_RULING", "CONTROL_HARVEST"}
SCOPES = {"INSTANCE", "CLASS"}
INDEPENDENCE_CLASSES = {"SEAT_INDEPENDENT", "PARTY_INDEPENDENT"}

#: Contract §4 check 5 — the register must not grade itself. Any mapping key in the register
#: whose normalised name lands here (or contains "status") is a validation failure. The set is
#: deliberately wide: the check exists to refuse smuggled results, not to be easy to satisfy.
STATUS_LIKE_KEYS = {
    "status", "state", "result", "results", "verdict", "outcome", "outcomes",
    "passed", "pass", "fail", "failed", "failing", "grade", "graded", "score",
    "green", "red", "amber", "ok", "satisfied", "disposition", "health",
    "conclusion", "evaluation", "assessment",
}

_ALLOWED_TOP = {"register_version", "pid", "latest_admitted_run", "criteria"}
_ALLOWED_PID = {"ref", "content_hash"}
_ALLOWED_CRITERION = {
    "criterion_id", "origin", "obligation", "criterion", "acceptance_semantics",
    "pid_relation", "tests", "supersedes", "superseded_by",
}
_ALLOWED_TEST = {"test_id", "scope", "execute", "execution_contract", "negative_control"}
_ALLOWED_NEGATIVE_CONTROL = {"violation", "evidence_ref"}

_PID_RELATION_RE = re.compile(r"^(DERIVES|NEW_REQUIREMENT|STRENGTHENS\s+(?P<target>\S+))$")

#: A criterion ID as the PID writes them: bold, first cell of a table row. The census is derived
#: from the PID text itself — never from the register (contract §4 check 1).
_PID_ROW_RE = re.compile(r"^\|\s*\*\*(?P<id>[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+)\*\*\s*(?P<rest>[^|]*)\|")
_ADVISORY_RE = re.compile(r"advisory", re.IGNORECASE)

RUNS_RELATIVE = Path("evidence") / "required-tests" / "runs"


# ---------------------------------------------------------------------------------------------- #
# report model
# ---------------------------------------------------------------------------------------------- #

@dataclass
class CriterionReport:
    criterion_id: str
    obligation: str                 # as the register wrote it ("" when register has no entry)
    effective_obligation: str       # after the PID census wins an understatement
    pid_relation: str
    status: str
    defects: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "criterion_id": self.criterion_id,
            "obligation": self.obligation,
            "effective_obligation": self.effective_obligation,
            "pid_relation": self.pid_relation,
            "status": self.status,
            "defects": list(self.defects),
        }


@dataclass
class Report:
    register_path: str
    pid_ref: str | None = None
    pid_hash_declared: str | None = None
    pid_hash_observed: str | None = None
    latest_admitted_run: str | None = None
    run_admissible: bool | None = None
    independence_class: str | None = None
    executing_party: str | None = None
    validation_failures: list[str] = field(default_factory=list)
    defects: list[str] = field(default_factory=list)
    criteria: list[CriterionReport] = field(default_factory=list)
    untraced: list[str] = field(default_factory=list)

    # -- computed ------------------------------------------------------------------------------ #

    @property
    def validation_failed(self) -> bool:
        return bool(self.validation_failures)

    @property
    def pid_hash_ok(self) -> bool | None:
        if self.pid_hash_declared is None or self.pid_hash_observed is None:
            return None
        return self.pid_hash_declared == self.pid_hash_observed

    @property
    def mandatory_not_pass(self) -> list[CriterionReport]:
        return [c for c in self.criteria
                if c.effective_obligation == "MANDATORY" and c.status != PASS]

    @property
    def gate_open(self) -> bool:
        """Contract §4 gate rule. There is no waiver path through this property."""
        if self.validation_failed:
            return False
        if self.pid_hash_ok is False:
            return False
        if self.untraced:
            return False
        if self.defects:
            return False
        return not self.mandatory_not_pass

    @property
    def pid_acceptance_satisfied(self) -> bool:
        """Derived, never asserted. Requires every mandatory criterion PASS (which already
        requires a valid negative control and a run whose independence class is recorded)."""
        return self.gate_open and bool(self.criteria)

    def as_dict(self) -> dict:
        return {
            "command": "pbg required-tests verify",
            "register": self.register_path,
            "pid_ref": self.pid_ref,
            "pid_hash_declared": self.pid_hash_declared,
            "pid_hash_observed": self.pid_hash_observed,
            "pid_hash_ok": self.pid_hash_ok,
            "latest_admitted_run": self.latest_admitted_run,
            "run_admissible": self.run_admissible,
            "executing_party": self.executing_party,
            "independence_class": self.independence_class,
            "validation_failures": list(self.validation_failures),
            "defects": list(self.defects),
            "untraced": list(self.untraced),
            "criteria": [c.as_dict() for c in self.criteria],
            "mandatory_not_pass": [c.criterion_id for c in self.mandatory_not_pass],
            "gate": "OPEN" if self.gate_open else "SHUT",
            "pid_acceptance_satisfied": self.pid_acceptance_satisfied,
        }

    def render(self) -> str:
        lines = [f"pbg required-tests verify — {self.register_path}"]
        lines.append(f"  pid.ref               {self.pid_ref or '(unresolved)'}")
        hash_state = {True: "MATCHES", False: "MISMATCH", None: "(not comparable)"}[self.pid_hash_ok]
        lines.append(f"  pid.content_hash      {hash_state}")
        lines.append(f"  latest_admitted_run   {self.latest_admitted_run or '(null)'}")
        if self.executing_party or self.independence_class:
            lines.append(f"  executed by           {self.executing_party or '(unnamed)'}"
                         f" [{self.independence_class or 'independence class NOT RECORDED'}]")
        lines.append("")
        if self.validation_failures:
            lines.append("VALIDATION FAILED — the register is not a valid input; no status is computed:")
            for finding in self.validation_failures:
                lines.append(f"  ! {finding}")
            lines.append("")
            lines.append("GATE: SHUT")
            lines.append("PID_ACCEPTANCE_SATISFIED: NOT DERIVED")
            return "\n".join(lines)

        for c in self.criteria:
            tag = c.effective_obligation[:1]  # M / A
            lines.append(f"  [{tag}] {c.criterion_id:<14} {c.status}")
            for d in c.defects:
                lines.append(f"        - {d}")
        if self.untraced:
            lines.append("")
            lines.append("UNTRACED register entries (no PID lineage — the register may not define"
                         " its own population):")
            for u in self.untraced:
                lines.append(f"  ! {u}")
        if self.defects:
            lines.append("")
            lines.append("DEFECTS:")
            for d in self.defects:
                lines.append(f"  ! {d}")
        # Durable visibility (PID-AC-007): every non-PASS mandatory criterion, in full, every run.
        not_pass = self.mandatory_not_pass
        if not_pass:
            lines.append("")
            lines.append(f"MANDATORY NOT PASS ({len(not_pass)}) — no waiver exists; "
                         "only PO disposition can move these:")
            for c in not_pass:
                lines.append(f"  ! {c.criterion_id}: {c.status}")
        lines.append("")
        lines.append(f"GATE: {'OPEN' if self.gate_open else 'SHUT'}")
        lines.append("PID_ACCEPTANCE_SATISFIED: "
                     + ("DERIVED" if self.pid_acceptance_satisfied else "NOT DERIVED"))
        return "\n".join(lines)


# ---------------------------------------------------------------------------------------------- #
# check 5 — self-grading refusal
# ---------------------------------------------------------------------------------------------- #

def _normalise_key(key: object) -> str:
    return re.sub(r"[\s_\-]", "", str(key)).lower()


def status_like_keys(document: object, path: str = "") -> list[str]:
    """Every status-like mapping key in the register document, with its location."""
    found: list[str] = []
    if isinstance(document, dict):
        for key, value in document.items():
            where = f"{path}.{key}" if path else str(key)
            norm = _normalise_key(key)
            if norm in STATUS_LIKE_KEYS or any(
                    stem in norm for stem in
                    ("status", "verdict", "result", "outcome", "grade", "score", "disposition")):
                found.append(where)
            found += status_like_keys(value, where)
    elif isinstance(document, list):
        for index, item in enumerate(document):
            found += status_like_keys(item, f"{path}[{index}]")
    return found


# ---------------------------------------------------------------------------------------------- #
# check 1 — the PID census, derived independently
# ---------------------------------------------------------------------------------------------- #

def derive_pid_census(pid_text: str) -> dict[str, dict]:
    """Criterion IDs read from the PID's own text — bold first-cell table rows.

    Returns {criterion_id: {"advisory": bool}}. The register never contributes to this census;
    that is the entire point of check 1.
    """
    census: dict[str, dict] = {}
    for line in pid_text.splitlines():
        match = _PID_ROW_RE.match(line.strip())
        if not match:
            continue
        cid = match.group("id")
        advisory = bool(_ADVISORY_RE.search(match.group("rest") or ""))
        if cid in census:
            # A duplicated ID cannot be a stable primary key; keep first, surface via defect
            # at compare time by marking the census itself suspect.
            census[cid]["duplicated"] = True
            continue
        census[cid] = {"advisory": advisory, "duplicated": False}
    return census


def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------------------------- #
# register loading + schema
# ---------------------------------------------------------------------------------------------- #

def _schema_findings(doc: object) -> list[str]:
    """Structural validation of the register document against the ratified schema. Returns
    findings; any finding is a validation failure (the register is not a valid input)."""
    findings: list[str] = []
    if not isinstance(doc, dict):
        return ["register is not a mapping"]

    for key in doc:
        if key not in _ALLOWED_TOP:
            findings.append(f"unknown top-level field: {key}")

    if doc.get("register_version") != 1:
        findings.append("register_version must be 1")

    pid = doc.get("pid")
    if not isinstance(pid, dict):
        findings.append("pid block missing or not a mapping")
    else:
        for key in pid:
            if key not in _ALLOWED_PID:
                findings.append(f"pid: unknown field: {key}")
        if not isinstance(pid.get("ref"), str) or not pid.get("ref"):
            findings.append("pid.ref missing")
        ch = pid.get("content_hash")
        if not (isinstance(ch, str) and ch.startswith("sha256:")):
            findings.append("pid.content_hash missing or not sha256:…")

    lar = doc.get("latest_admitted_run")
    if lar is not None and not isinstance(lar, str):
        # A reference, never a result (contract §1). A mapping here is a smuggled result.
        findings.append("latest_admitted_run must be a run_id string or null — it is a "
                        "reference, never a result")

    criteria = doc.get("criteria")
    if not isinstance(criteria, list) or not criteria:
        findings.append("criteria missing or empty")
        criteria = []

    seen: set[str] = set()
    for index, entry in enumerate(criteria):
        where = f"criteria[{index}]"
        if not isinstance(entry, dict):
            findings.append(f"{where}: not a mapping")
            continue
        cid = entry.get("criterion_id")
        where = f"criteria[{index}] ({cid})" if cid else where
        for key in entry:
            if key not in _ALLOWED_CRITERION:
                findings.append(f"{where}: unknown field: {key}")
        if not isinstance(cid, str) or not cid:
            findings.append(f"{where}: criterion_id missing")
        elif cid in seen:
            findings.append(f"{where}: duplicate criterion_id — the primary key is assigned once")
        else:
            seen.add(cid)
        if entry.get("origin") not in ORIGINS:
            findings.append(f"{where}: origin must be one of {sorted(ORIGINS)}")
        if entry.get("obligation") not in OBLIGATIONS:
            findings.append(f"{where}: obligation must be MANDATORY or ADVISORY")
        for prose in ("criterion", "acceptance_semantics"):
            if not isinstance(entry.get(prose), str) or not str(entry.get(prose)).strip():
                findings.append(f"{where}: {prose} missing")
        rel = entry.get("pid_relation")
        if not (isinstance(rel, str) and _PID_RELATION_RE.match(rel.strip())):
            findings.append(f"{where}: pid_relation must be DERIVES | STRENGTHENS <id> | "
                            "NEW_REQUIREMENT")
        if not isinstance(entry.get("supersedes", []), list):
            findings.append(f"{where}: supersedes must be a list")
        sb = entry.get("superseded_by")
        if sb is not None and not isinstance(sb, str):
            findings.append(f"{where}: superseded_by must be a criterion_id or null")

        tests = entry.get("tests")
        if not isinstance(tests, list) or not tests:
            findings.append(f"{where}: tests missing or empty")
            tests = []
        for tindex, test in enumerate(tests):
            twhere = f"{where}.tests[{tindex}]"
            if not isinstance(test, dict):
                findings.append(f"{twhere}: not a mapping")
                continue
            for key in test:
                if key not in _ALLOWED_TEST:
                    findings.append(f"{twhere}: unknown field: {key}")
            if not isinstance(test.get("test_id"), str) or not test.get("test_id"):
                findings.append(f"{twhere}: test_id missing")
            if test.get("scope") not in SCOPES:
                findings.append(f"{twhere}: scope must be INSTANCE or CLASS")
            if not isinstance(test.get("execute"), str) or not str(test.get("execute")).strip():
                findings.append(f"{twhere}: execute missing")
            if not isinstance(test.get("execution_contract"), str) or not test.get("execution_contract"):
                findings.append(f"{twhere}: execution_contract missing")
            nc = test.get("negative_control")
            if not isinstance(nc, dict):
                findings.append(f"{twhere}: negative_control missing")
            else:
                for key in nc:
                    if key not in _ALLOWED_NEGATIVE_CONTROL:
                        findings.append(f"{twhere}.negative_control: unknown field: {key}")
                if not isinstance(nc.get("violation"), str) or not str(nc.get("violation")).strip():
                    findings.append(f"{twhere}.negative_control: violation missing")
                if not isinstance(nc.get("evidence_ref"), str) or not nc.get("evidence_ref"):
                    # A run reference, never a boolean someone typed (contract §2).
                    findings.append(f"{twhere}.negative_control: evidence_ref missing — must "
                                    "reference a run record")
    return findings


# ---------------------------------------------------------------------------------------------- #
# run records (check 2 evidence, check 4 independence)
# ---------------------------------------------------------------------------------------------- #

@dataclass
class RunRecord:
    run_id: str
    path: Path
    document: dict | None
    problems: list[str] = field(default_factory=list)

    @property
    def admissible(self) -> bool:
        return self.document is not None and not self.problems

    @property
    def executing_party(self) -> str | None:
        if isinstance(self.document, dict):
            by = self.document.get("executed_by")
            if isinstance(by, dict):
                return by.get("party")
        return None

    @property
    def independence_class(self) -> str | None:
        if isinstance(self.document, dict):
            by = self.document.get("executed_by")
            if isinstance(by, dict):
                return by.get("independence_class")
        return None

    def results_for(self, test_id: str, mode: str) -> list[dict]:
        if not isinstance(self.document, dict):
            return []
        results = self.document.get("results")
        if not isinstance(results, list):
            return []
        return [r for r in results
                if isinstance(r, dict) and r.get("test_id") == test_id and r.get("mode") == mode]


def load_run(runs_dir: Path, run_id: str) -> RunRecord | None:
    """Load one append-only run record. Returns None when the file does not exist —
    a dangling reference loses a pointer, never evidence (contract §1)."""
    path = runs_dir / f"{run_id}.json"
    if not path.is_file():
        return None
    problems: list[str] = []
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return RunRecord(run_id, path, None, [f"unreadable run record: {exc}"])
    if not isinstance(document, dict):
        return RunRecord(run_id, path, None, ["run record is not a mapping"])
    if document.get("run_id") != run_id:
        problems.append(f"run_id inside the record ({document.get('run_id')!r}) does not match "
                        f"the filename ({run_id})")
    by = document.get("executed_by")
    if not (isinstance(by, dict) and isinstance(by.get("party"), str) and by.get("party")):
        problems.append("executed_by.party missing — the run must name the executing party")
    if not (isinstance(by, dict) and by.get("independence_class") in INDEPENDENCE_CLASSES):
        problems.append("executed_by.independence_class missing or not one of "
                        f"{sorted(INDEPENDENCE_CLASSES)} (check 4)")
    if not (isinstance(document.get("candidate"), str) and document.get("candidate")):
        problems.append("candidate missing — the run must name the exact candidate it executed "
                        "against (check 3)")
    if not isinstance(document.get("results"), list):
        problems.append("results missing")
    return RunRecord(run_id, path, document, problems)


def _arm(record: dict | None, name: str) -> dict | None:
    if not isinstance(record, dict):
        return None
    arms = record.get("arms")
    if not isinstance(arms, dict):
        return None
    arm = arms.get(name)
    return arm if isinstance(arm, dict) else None


def _exit_code(arm: dict | None) -> int | None:
    if arm is None:
        return None
    code = arm.get("exit_code")
    return code if isinstance(code, int) else None


# ---------------------------------------------------------------------------------------------- #
# the five checks, computed
# ---------------------------------------------------------------------------------------------- #

def _negative_control_status(test: dict, runs_dir: Path,
                             defects: list[str]) -> str:
    """PASS when the referenced run demonstrates detection by contrast; otherwise UNDECIDABLE.

    Detection is: the declared command exits 0 on the clean subject and non-zero on the subject
    with the representative violation planted. A clean arm that fails — or is absent — cannot be
    told apart from a broken harness, and a broken harness detects nothing: UNDECIDABLE.
    """
    test_id = test.get("test_id")
    ref = (test.get("negative_control") or {}).get("evidence_ref")
    run = load_run(runs_dir, ref)
    if run is None:
        defects.append(f"{test_id}: negative_control.evidence_ref {ref!r} does not resolve to a "
                       f"run record under {runs_dir}")
        return UNDECIDABLE
    if not run.admissible:
        defects.append(f"{test_id}: negative-control run {ref} is inadmissible: "
                       + "; ".join(run.problems))
        return UNDECIDABLE
    results = run.results_for(test_id, "NEGATIVE_CONTROL")
    if not results:
        defects.append(f"{test_id}: run {ref} contains no NEGATIVE_CONTROL result for this test")
        return UNDECIDABLE
    result = results[0]
    baseline, violated = _arm(result, "baseline"), _arm(result, "violated")
    declared = str(test.get("execute", "")).strip()
    for name, arm in (("baseline", baseline), ("violated", violated)):
        if arm is None:
            defects.append(f"{test_id}: run {ref} negative control has no {name} arm — "
                           "detection cannot be distinguished from harness breakage")
            return UNDECIDABLE
        if str(arm.get("command", "")).strip() != declared:
            defects.append(f"{test_id}: run {ref} {name} arm ran {arm.get('command')!r}, not the "
                           f"declared execute command — the evidence does not certify this test")
            return UNDECIDABLE
    base_code, viol_code = _exit_code(baseline), _exit_code(violated)
    if base_code is None or viol_code is None:
        defects.append(f"{test_id}: run {ref} negative control arms carry no integer exit codes")
        return UNDECIDABLE
    if base_code != 0:
        defects.append(f"{test_id}: run {ref} baseline arm failed (exit {base_code}) — the "
                       "harness itself is broken; a broken harness detects nothing")
        return UNDECIDABLE
    if viol_code == 0:
        defects.append(f"{test_id}: run {ref} planted violation was NOT detected "
                       "(violated arm exit 0)")
        return UNDECIDABLE
    return PASS


def _acceptance_status(test: dict, latest: RunRecord | None,
                       latest_ref_present: bool, defects: list[str]) -> str:
    test_id = test.get("test_id")
    if not latest_ref_present:
        return NOT_EVALUATED  # never run; latest_admitted_run is null
    if latest is None:
        return NOT_EVALUATED  # dangling reference — reported once at register level
    if not latest.admissible:
        # Executed by someone, but the record cannot support a determination (check 4).
        return UNKNOWN
    results = latest.results_for(test_id, "ACCEPTANCE")
    if not results:
        return NOT_EVALUATED
    result = results[0]
    declared = str(test.get("execute", "")).strip()
    if str(result.get("command", "")).strip() != declared:
        defects.append(f"{test_id}: admitted run executed {result.get('command')!r}, not the "
                       f"declared execute command {declared!r} — result not attributable")
        return UNKNOWN
    code = result.get("exit_code")
    if not isinstance(code, int):
        defects.append(f"{test_id}: admitted run result carries no integer exit_code")
        return UNKNOWN
    return PASS if code == 0 else FAIL


def _worst(statuses: list[str]) -> str:
    return min(statuses, key=lambda s: _SEVERITY[s]) if statuses else NOT_EVALUATED


# ---------------------------------------------------------------------------------------------- #
# verify
# ---------------------------------------------------------------------------------------------- #

def verify(register_path: Path) -> Report:
    register_path = Path(register_path)
    report = Report(register_path=str(register_path))

    if not register_path.is_file():
        report.validation_failures.append(f"register not found: {register_path}")
        return report
    try:
        doc = yaml.safe_load(register_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        report.validation_failures.append(f"register is not readable YAML: {exc}")
        return report

    # Check 5 first: a register that grades itself is not an input.
    for where in status_like_keys(doc):
        report.validation_failures.append(
            f"status-like field in the register at {where} — the register must not grade "
            "itself (contract §4 check 5)")
    report.validation_failures += _schema_findings(doc)
    if report.validation_failed:
        return report

    project_root = register_path.parent
    runs_dir = project_root / RUNS_RELATIVE

    # Check 1 — derive the census from the PID, independently.
    pid_block = doc["pid"]
    pid_path = (project_root / pid_block["ref"]).resolve()
    report.pid_ref = pid_block["ref"]
    report.pid_hash_declared = pid_block["content_hash"]
    if not pid_path.is_file():
        report.validation_failures.append(
            f"pid.ref does not resolve: {pid_block['ref']} — the population cannot be derived")
        return report
    report.pid_hash_observed = _sha256_file(pid_path)
    if report.pid_hash_ok is False:
        report.defects.append(
            "pid.content_hash does not match the referenced PID — the register's population was "
            "derived from a different document than the one now governing")
    census = derive_pid_census(pid_path.read_text(encoding="utf-8"))
    if not census:
        report.validation_failures.append(
            f"no criteria could be derived from {pid_block['ref']} — an empty census cannot "
            "govern anything")
        return report
    for cid, meta in census.items():
        if meta.get("duplicated"):
            report.defects.append(f"PID census: {cid} appears more than once in the PID — not a "
                                  "stable primary key")

    report.latest_admitted_run = doc.get("latest_admitted_run")
    latest_ref_present = report.latest_admitted_run is not None
    latest = load_run(runs_dir, report.latest_admitted_run) if latest_ref_present else None
    if latest_ref_present and latest is None:
        report.defects.append(
            f"latest_admitted_run {report.latest_admitted_run!r} does not resolve to a run "
            f"record under {runs_dir} — a pointer is lost (evidence, if it existed, was not)")
    if latest is not None:
        report.run_admissible = latest.admissible
        report.executing_party = latest.executing_party
        ic = latest.independence_class
        report.independence_class = ic if ic in INDEPENDENCE_CLASSES else None
        for problem in latest.problems:
            report.defects.append(f"admitted run {latest.run_id}: {problem}")

    # Active register entries: supersession sets superseded_by, never deletes.
    entries = [e for e in doc["criteria"] if e.get("superseded_by") in (None, "")]
    by_id = {e["criterion_id"]: e for e in entries}

    def evaluate_entry(entry: dict) -> tuple[str, list[str]]:
        defects: list[str] = []
        statuses: list[str] = []
        for test in entry["tests"]:
            test_id = test.get("test_id")
            # Check 3 — execution contract declared AND resolvable.
            contract_ref = test.get("execution_contract")
            if not (project_root / contract_ref).is_file():
                defects.append(f"{test_id}: execution_contract {contract_ref!r} does not resolve")
                statuses.append(UNDECIDABLE)
                continue
            # Check 2 — negative control demonstrated by contrast.
            nc_status = _negative_control_status(test, runs_dir, defects)
            # Acceptance execution, computed from recorded facts.
            acc_status = _acceptance_status(test, latest, latest_ref_present, defects)
            statuses.append(_worst([nc_status, acc_status])
                            if nc_status == PASS else _worst([acc_status, UNDECIDABLE]))
        return _worst(statuses), defects

    # PID criteria first, in PID order.
    for cid, meta in census.items():
        entry = by_id.get(cid)
        if entry is None or not str(entry.get("pid_relation", "")).startswith("DERIVES"):
            report.criteria.append(CriterionReport(
                criterion_id=cid,
                obligation="",
                effective_obligation="ADVISORY" if meta["advisory"] else "MANDATORY",
                pid_relation="",
                status=NOT_EVALUATED,
                defects=["PID criterion has no register entry deriving it — reported defect, "
                         "not silent absence (check 1)"],
            ))
            continue
        obligation = entry["obligation"]
        effective = obligation
        defects: list[str] = []
        if not meta["advisory"] and obligation == "ADVISORY":
            defects.append("obligation understated: the PID holds this criterion MANDATORY — "
                           "the register may not weaken its own population")
            effective = "MANDATORY"
            report.defects.append(f"{cid}: obligation understated (register says ADVISORY, "
                                  "PID says MANDATORY)")
        status, eval_defects = evaluate_entry(entry)
        report.criteria.append(CriterionReport(
            criterion_id=cid, obligation=obligation, effective_obligation=effective,
            pid_relation=entry["pid_relation"], status=status,
            defects=defects + eval_defects))

    # Register-only entries: STRENGTHENS (traced through target), NEW_REQUIREMENT (blocked),
    # anything else UNTRACED.
    for entry in entries:
        cid = entry["criterion_id"]
        relation = str(entry["pid_relation"]).strip()
        if cid in census and relation.startswith("DERIVES"):
            continue  # handled above
        if relation == "NEW_REQUIREMENT":
            # §5: an Engineer may not write requirements by finding bugs. Blocked pending PO
            # amendment of the PID; NOT_EVALUATED; the gate does not open on it.
            report.criteria.append(CriterionReport(
                criterion_id=cid, obligation=entry["obligation"],
                effective_obligation=entry["obligation"], pid_relation=relation,
                status=NOT_EVALUATED,
                defects=["NEW_REQUIREMENT is blocked pending PO amendment of the PID"]))
            continue
        match = _PID_RELATION_RE.match(relation)
        target = match.group("target") if match else None
        if relation.startswith("STRENGTHENS"):
            if target not in census:
                report.untraced.append(
                    f"{cid}: STRENGTHENS {target} but {target} is not in the PID census")
                continue
            status, eval_defects = evaluate_entry(entry)
            report.criteria.append(CriterionReport(
                criterion_id=cid, obligation=entry["obligation"],
                effective_obligation=entry["obligation"], pid_relation=relation,
                status=status, defects=eval_defects))
            continue
        # DERIVES with no PID lineage.
        report.untraced.append(f"{cid}: {relation or '(no pid_relation)'} — no PID lineage")

    return report
