"""pbg — PBGv2 command-line surface.

Runs from the project-pinned framework snapshot. There is deliberately no host-global
installation: a globally installed tool would reintroduce the drift that pinning exists to
prevent (PBG-FWK-013).

Implemented so far: validate, version, controls, status (partial).
Not yet implemented: init, boot, adapt, verify, close.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from . import controls as controls_mod
from . import instructions
from . import roots
from . import manifest as manifest_mod
from . import verification
from . import continuity, scanning, versioning

EXIT_OK = 0
EXIT_FAIL = 2
EXIT_USAGE = 4
EXIT_AMBER = 3


def _framework_root(start: Path | None = None) -> Path:
    """Locate the framework root by walking up for VERSION + controls/."""
    here = (start or Path(__file__).resolve()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / "VERSION").is_file() and (candidate / "controls").is_dir():
            return candidate
    raise FileNotFoundError("framework root not found (looked for VERSION + controls/)")


# --------------------------------------------------------------------------------------------- #
# validate
# --------------------------------------------------------------------------------------------- #

def cmd_validate(args: argparse.Namespace) -> int:
    # independent Assurance finding N3. Two roots, two jobs. `root` stays the FRAMEWORK source root — every framework
    # integrity check below reads VERSION, controls/, schemas/ and adapters/ from it. The project
    # checks (PBG-BOOT-001 instructions, PBG-CTRL-004 manifest) use the GOVERNED PROJECT root, which
    # in a vendored install is the directory ABOVE the framework, not the framework itself.
    resolution = roots.resolve(Path(args.root) if args.root else None)
    if not resolution.resolved:
        print("ROOTS: AMBIGUOUS")
        print(f"  {resolution.detail}")
        print(resolution.render())
        return EXIT_USAGE
    root = resolution.framework_root
    project_root = resolution.project_root
    checks: list[dict] = []
    failed = False

    def record(name: str, control_id: str, ok: bool, detail: list[str], severity: str = "RED",
               always_show: bool = False) -> None:
        nonlocal failed
        checks.append(
            {
                "check": name,
                "control_id": control_id,
                "result": "PASS" if ok else "FAIL",
                "severity": severity if not ok else "",
                "always_show": always_show,
                "findings": detail,
            }
        )
        if not ok and severity == "RED":
            failed = True

    # 1. Canonical version authority ---------------------------------------------------------- #
    try:
        canonical = versioning.read_version(root)
        record("version_authority_readable", "PBG-FWK-010", True, [f"VERSION = {canonical}"])
    except (FileNotFoundError, ValueError) as exc:
        record("version_authority_readable", "PBG-FWK-010", False, [str(exc)])
        canonical = None

    # 2. No hand-embedded framework versions -------------------------------------------------- #
    findings = versioning.scan(root)
    record(
        "no_hand_embedded_versions",
        "PBG-FWK-011",
        not findings,
        [f"{f.path}:{f.line}: {f.text} — {f.reason}" for f in findings],
    )

    # 3. manifest.yaml agrees with VERSION ---------------------------------------------------- #
    manifest_path = root / "manifest.yaml"
    fw_manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else None
    mf = versioning.check_manifest(root, fw_manifest)
    record("manifest_version_agrees", "PBG-FWK-010", not mf, [f"{f.reason}" for f in mf])

    # 4. Control-record schema ---------------------------------------------------------------- #
    schema_path = root / "schemas" / "control.schema.yaml"
    schema_errors: list[str] = []
    # independent Assurance finding U3-3. A document that could not be STRUCTURALLY read never reaches the schema validator,
    # so the structural refusals are carried onto this record too. Otherwise a corpus that failed to
    # load reports "every control record is schema-valid" — a pass obtained by having nothing left
    # to check, which is the exact failure class this cycle exists to close.
    control_documents, structural_findings = controls_mod.load_control_documents(root)
    schema_errors += [f.render() for f in structural_findings]
    if schema_path.is_file():
        try:
            import jsonschema

            schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
            validator = jsonschema.Draft202012Validator(schema)
            for rel, doc in control_documents.items():
                for err in sorted(validator.iter_errors(doc), key=lambda e: list(e.path)):
                    loc = "/".join(str(p) for p in err.path)
                    schema_errors.append(f"{rel}:{loc}: {err.message}")
        except ImportError:
            schema_errors.append("jsonschema unavailable — AMBER_FRAMEWORK_CAPABILITY_GAP")
    else:
        schema_errors.append("schemas/control.schema.yaml missing")
    record("control_records_valid", "PBG-FWK-051", not schema_errors, schema_errors)

    # 5. Control-ID integrity ----------------------------------------------------------------- #
    issues = controls_mod.check_integrity(root)
    record("control_id_integrity", "PBG-CTRL-001", not issues, [i.render() for i in issues])

    # 6. Prose cites only real control IDs ----------------------------------------------------- #
    # Widened beyond docs/: role contracts, adapters and the agent-facing files cite control IDs
    # too, and those are the ones an AGENT reads. A role contract citing a control that does not
    # exist is the same defect class as an adapter advertising a command that does not exist --
    # perfectly written prose, operationally broken, invisible until someone acts on it.
    cited_paths: list[Path] = []
    if (root / "docs").is_dir():
        cited_paths += sorted((root / "docs").rglob("*.md"))
    # Every operative artefact, in both formats. The register is YAML and a `standards/*.md`-only
    # glob silently excluded it -- a gap in the very check built to close this class.
    for pattern in ("roles/*.md", "roles/*.yaml", "adapters/**/*.md", "adapters/**/*.yaml",
                    "policies/*.yaml", "policies/*.md", "skills/**/*.md", "skills/**/*.yaml",
                    "standards/*.md", "standards/*.yaml", "templates/*",
                    "PBG.md", "CLAUDE.md", "QUICKSTART.md", "README.md"):
        cited_paths += [p for p in sorted(root.glob(pattern)) if p.is_file()]
    cited_paths = sorted(set(cited_paths))

    dangling: list[str] = []
    for doc_path in cited_paths:
        rel = doc_path.relative_to(root).as_posix()
        if rel.startswith("docs/archaeology/"):
            continue  # archaeology cites PBGv1 register IDs, a different namespace
        body = doc_path.read_text(encoding="utf-8", errors="ignore")
        if "pbg:reference-fixture" in body:
            # Explicitly classified as a negative fixture: the invalid ID is what the test is FOR.
            # A marker, never a blanket directory exemption -- the exemption must be deliberate and
            # visible at the point of use (PA ruling 2026-07-30 s11).
            continue
        missing = controls_mod.resolve_references(root, body)
        dangling.extend(f"{rel}: cites undefined {cid}" for cid in missing)
    record("no_dangling_control_refs", "PBG-CTRL-001", not dangling, dangling, severity="AMBER")

    # 7. Secret scan --------------------------------------------------------------------------- #
    secrets = scanning.scan_secrets(root)
    env_files = scanning.check_env_files(root)
    record(
        "no_secret_material",
        "PBG-EVID-003",
        not secrets and not env_files,
        [s.render() for s in secrets] + [f"{p}: environment file present in tree" for p in env_files],
    )

    # 8. Wrapper classification ---------------------------------------------------------------- #
    declared = (fw_manifest or {}).get("declared_adapters", [])
    wrappers = scanning.classify_wrappers(root, declared)
    bad = [w for w in wrappers if w.severity in ("AMBER", "RED")]
    record(
        "wrapper_classification",
        "PBG-FWK-004",
        not bad,
        [w.render() for w in wrappers],
        severity="RED" if any(w.severity == "RED" for w in wrappers) else "AMBER",
    )

    # 9. Adapter command fidelity (PBG-PORT-003) ------------------------------------------------ #
    # An adapter that names a command the CLI does not provide fails silently until a fresh agent
    # boots and is told to run something that does not exist. Found exactly that: QUICKSTART.md
    # advertised `pbg verify-framework`, which never existed.
    adapter_problems = verification.check_adapter_commands(root, registered_commands())
    record("adapter_command_fidelity", "PBG-PORT-003", not adapter_problems, adapter_problems)

    # F-12: the floor is compared against an INDEPENDENT shipped definition, never derived from
    # the mutable records it protects.
    from . import floor as floor_mod
    floor_problems = floor_mod.check(root)
    record("non_waivable_floor_intact", "PBG-CTRL-002", not floor_problems, floor_problems)

    # F-5: every declared manifest measurement is validated against the live corpus.
    manifest_problems = manifest_mod.validate(root)
    record("manifest_agrees_with_corpus", "PBG-FWK-040", not manifest_problems, manifest_problems)

    # N-8: PBG-SOD-001's verifier returned FAIL while pbg validate returned GREEN. A registered,
    # bound verifier whose result is disconnected from the verdict is decoration. Only the
    # controls that DECLARE a CHECK_REF are executed -- 16, not 127 -- so this stays bounded.
    from . import checks as checks_mod
    verifier_findings, verifier_states, verifier_unrun = [], [], []
    for cid, rec in sorted(controls_mod.all_controls(root).items()):
        if rec.get("verification_mechanism") != "CHECK_REF":
            continue
        ref = rec.get("verification_ref")
        state = checks_mod.execute(cid, ref, root) if ref else None
        if state is None:
            verifier_findings.append(f"{cid}: declares CHECK_REF with no verification_ref")
            continue
        verifier_states.append(f"{cid}={state.state}")
        if state.state in (checks_mod.FAIL, checks_mod.ERROR, checks_mod.STALE,
                           checks_mod.UNVERIFIABLE):
            verifier_findings.append(f"{cid}: verifier {ref} returned {state.state} — {state.detail}")
        elif state.state == checks_mod.NOT_YET_RUN:
            # Not satisfied, but not failed either. O-2: a fresh project has genuinely not run
            # anything yet, and reporting that as RED made every new installation look corrupt.
            # AMBER blocks adoption and mutation without claiming a defect exists.
            verifier_unrun.append(f"{cid}: verifier {ref} has not run — not satisfied")
    checks.append({"check": "bound_verifier_states", "control_id": "PBG-CTRL-005",
                   "result": "INFO", "severity": "", "findings": verifier_states})
    record("bound_verifiers_satisfied", "PBG-CTRL-005", not verifier_findings, verifier_findings)
    record("bound_verifiers_evidenced", "PBG-CTRL-005", not verifier_unrun, verifier_unrun,
           severity="AMBER")

    write_problems = verification.check_snapshot_write_safety(root)
    record("snapshot_write_safety", "PBG-FWK-013", not write_problems, write_problems)

    # 10. Project manifest weakening ------------------------------------------------------------ #
    # independent Assurance finding F-4: this was gated on --project-manifest, so the check that stops a project weakening a
    # mandatory control only ran when someone remembered to ask for it. A control that must be
    # requested is not enforced. It now runs whenever a manifest is discoverable, and the flag only
    # overrides WHERE to look.
    # 9b. Project instruction boundary (independent Assurance finding F21) ------------------------------------------------ #
    #
    # The framework shipped a working contamination detector and pointed it only at behavioural
    # fixtures. It now runs on the root being validated, and its result is a CHECK rather than a
    # note — advisory was the finding.
    ires = instructions.resolve(project_root)
    record("project_instructions_local_only", "PBG-BOOT-001", ires.usable, [ires.render()],
           severity="AMBER", always_show=True)
    record("no_inherited_instruction_files", "PBG-BOOT-001", not ires.contaminated,
           ires.inherited or ["no instruction file above PROJECT_ROOT would be inherited"],
           severity="AMBER", always_show=True)

    # A-5. Which control-like root file was SELECTED, and which recognised sibling was not. The
    # finding was not that the wrong file wins — it is that the loser was never mentioned, so a
    # reader could not tell "ignored" from "never looked for". Reported at default verbosity,
    # because provenance visible only under --json is the reporting half of the same defect.
    record("instruction_sources_unshadowed", "PBG-BOOT-001", not ires.shadowed,
           ires.findings or ["no recognised instruction file at PROJECT_ROOT is shadowed by another"],
           severity="AMBER", always_show=True)
    shadowed_sources = instructions.shadowed_control_files(root)
    record("control_file_sources_unshadowed", "PBG-CTRL-004", not shadowed_sources,
           shadowed_sources or ["no declared control file occupies more than one permitted location"],
           severity="AMBER", always_show=True)
    checks.append({"check": "control_file_classification", "control_id": "PBG-BOOT-001",
                   "result": "INFO", "severity": "", "always_show": True,
                   "findings": [s.render() for s in instructions.classify_control_files(root)]})

    # independent Assurance finding F19: resolution is bounded to PROJECT_ROOT, and says where it looked. The parent-directory
    # candidate is gone — see manifest.MANIFEST_LOCATIONS for why.
    manifest_res = manifest_mod.resolve(
        project_root, Path(args.project_manifest) if args.project_manifest else None)
    # Fail closed, at the severity the state deserves. RESOLVED passes. ABSENT is AMBER: with no
    # manifest, "this manifest does not weaken a mandatory control" is UNESTABLISHED rather than
    # satisfied, and unestablished must not render as a green tick. MALFORMED and
    # OUTSIDE_PROJECT_ROOT are RED: something exists, it was meant to govern this project, and it
    # cannot be used.
    #
    # `always_show` because a check that reports PASS without saying WHAT it validated is the
    # reporting half of F19: the provenance was previously visible only under --json.
    record("manifest_check_reached", "PBG-CTRL-004", manifest_res.usable,
           [manifest_res.render()],
           severity="RED" if manifest_res.blocking else "AMBER", always_show=True)
    if manifest_res.usable:
        pm_issues = manifest_mod.check(root, manifest_res.manifest)
        record(
            "manifest_cannot_weaken",
            "PBG-CTRL-004",
            not pm_issues,
            [i.render() for i in pm_issues],
        )
        checks.append({"check": "manifest_digest", "control_id": "PBG-CTRL-004",
                       "result": "INFO", "severity": "", "always_show": True,
                       "findings": [f"{manifest_mod.digest(manifest_res.manifest)}  "
                                    f"(source: {manifest_res.path})"]})
    elif manifest_res.blocking:
        # The manifest exists and was meant to govern this project, but cannot be used. Naming the
        # control as NOT SATISFIED is the honest report; silently skipping it is how a project ends
        # up believing PBG-CTRL-004 ran.
        record("manifest_cannot_weaken", "PBG-CTRL-004", False,
               [f"not evaluated — {manifest_res.render()}"], severity="AMBER")

    verdict = "RED" if failed else ("AMBER" if any(c["result"] == "FAIL" for c in checks) else "GREEN")
    report = {
        "command": "pbg validate",
        "framework_version": canonical,
        # independent Assurance finding N3 requires the human-readable output to name all four, so an operator can see at a
        # glance WHICH tree each answer came from. `root` is retained for compatibility and is the
        # framework source root it always was.
        "root": str(root),
        "framework_source_root": str(root),
        "governed_project_root": str(project_root),
        "layout": resolution.layout,
        "selected_manifest": str(manifest_res.path) if manifest_res.path else None,
        "selected_instruction_file": str(ires.path) if ires.path else None,
        "verdict": verdict,
        "checks": checks,
    }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        _render(report)
    return EXIT_OK if verdict == "GREEN" else EXIT_FAIL


def _render(report: dict) -> None:
    print(f"pbg validate — {report['framework_version']}")
    print(f"  governed project root  {report.get('governed_project_root')}")
    print(f"  framework source root  {report.get('framework_source_root', report['root'])}")
    print(f"  layout                 {report.get('layout') or '-'}")
    print(f"  selected manifest      {report.get('selected_manifest') or '(none)'}")
    print(f"  selected instructions  {report.get('selected_instruction_file') or '(none)'}")
    print()
    for check in report["checks"]:
        mark = {"PASS": "  ok  ", "FAIL": " FAIL ", "INFO": " info "}[check["result"]]
        sev = f" [{check['severity']}]" if check.get("severity") else ""
        print(f"[{mark}]{sev} {check['check']}  ({check['control_id']})")
        # A PASS that does not say what it validated is not a report (independent Assurance finding F19). Checks carrying
        # provenance opt in to being rendered in the DEFAULT output, not only under --json.
        if check["result"] != "PASS" or check.get("always_show"):
            for finding in check["findings"][:20]:
                print(f"          - {finding}")
            if len(check["findings"]) > 20:
                print(f"          ... {len(check['findings']) - 20} more")
    print()
    print(f"VERDICT: {report['verdict']}")


# --------------------------------------------------------------------------------------------- #
# controls / version
# --------------------------------------------------------------------------------------------- #

def cmd_controls(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve() if args.root else _framework_root()
    flat = controls_mod.all_controls(root)
    if args.json:
        print(json.dumps(flat, indent=2))
        return EXIT_OK
    for cid in sorted(flat):
        rec = flat[cid]
        flag = "M" if rec.get("mandatory_or_conditional") == "MANDATORY" else "c"
        waive = "!" if rec.get("exception_policy") == "NON_WAIVABLE" else " "
        print(f"{flag}{waive} {cid}  {rec.get('title', '')}")
    print(f"\n{len(flat)} controls")
    return EXIT_OK


def cmd_log(args: argparse.Namespace) -> int:
    """Validate every canonical continuity record against its schema and references."""
    root = Path(args.root).resolve() if args.root else _framework_root()
    import subprocess
    shas = set(subprocess.run(["git", "log", "--format=%H"], cwd=root,
                              capture_output=True, text=True).stdout.split()) or None

    subcommand = getattr(args, "subcommand", "validate")
    if subcommand == "rebuild":
        written = continuity.rebuild_projections(root)
        for w in written:
            print(f"regenerated {w.relative_to(root)}")
        return EXIT_OK

    if subcommand == "chronology":
        # Explicit diagnosis of OBS-CONTINUITY-TIMESTAMP-0001: which entries claim a time they
        # cannot have been written at, and what the ordering actually rests on instead.
        newest, chronology = continuity.newest_entry(root)
        print(continuity.render_chronology(chronology))
        future = [i for i in chronology.values() if i["future_stamped"]]
        return EXIT_AMBER if future else EXIT_OK

    failures = 0
    log_dir = root / "governance" / "engineering" / "build-log"
    for path in sorted(log_dir.rglob("*.yaml")) if log_dir.is_dir() else []:
        result = continuity.validate(path.read_text(encoding="utf-8"), "entry", root, git_shas=shas)
        mark = "  ok  " if result.ok else " FAIL "
        print(f"[{mark}] {path.relative_to(root)}")
        if not result.ok:
            failures += 1
            for err in result.errors:
                print(f"          {result.stage}: {err}")
        for u in result.unresolved:
            print(f"          unresolved: {u}")

    aw = root / "governance" / "engineering" / "ACTIVE_WORK.yaml"
    if aw.is_file():
        result = continuity.validate(aw.read_text(encoding="utf-8"), "active_work", root, git_shas=shas)
        print(f"[{'  ok  ' if result.ok else ' FAIL '}] {aw.relative_to(root)}")
        if not result.ok:
            failures += 1
            for err in result.errors:
                print(f"          {result.stage}: {err}")

    # Diagnosed, never silently absorbed. These entries claim a time later than the commit that
    # carries them; ordering ignores the claim, but a reader must be told the claim is false.
    _, chronology = continuity.newest_entry(root)
    for info in sorted(chronology.values(), key=continuity.order_key):
        if info["future_stamped"]:
            print(f"[ note ] {info['entry_id']}: {info['diagnosis'][0]}")

    print()
    print(f"VERDICT: {'GREEN' if not failures else 'RED'}  ({failures} invalid)")
    return EXIT_OK if not failures else EXIT_FAIL


def cmd_resume(args: argparse.Namespace) -> int:
    """Reconcile recorded continuity against observed state before any work begins."""
    root = Path(args.root).resolve() if args.root else _framework_root()
    result = continuity.resume(root)
    print(result.render())
    return EXIT_OK if result.resume_verdict != "RESUME_BLOCKED" else EXIT_FAIL


def registered_commands() -> set[str]:
    """The subcommands the CLI actually provides, read from the parser rather than a list."""
    parser = build_parser()
    for action in parser._actions:                       # noqa: SLF001 - argparse offers no API
        if isinstance(action, argparse._SubParsersAction):   # noqa: SLF001
            return set(action.choices)
    return set()                                          # pragma: no cover - defensive


def cmd_boot(args: argparse.Namespace) -> int:
    """Boot the Project Lead. There is no second boot path."""
    from . import boot as boot_mod

    root = Path(args.root).resolve() if args.root else Path.cwd()
    verdict = boot_mod.pl_boot(root)
    print(verdict.render())
    return {"GREEN": EXIT_OK, "AMBER": EXIT_AMBER}.get(verdict.verdict, EXIT_FAIL)


def cmd_hooks(args: argparse.Namespace) -> int:
    """Commission, inspect or decommission the project-owned validation hook (independent Assurance finding F23)."""
    from . import hooks as hooks_mod

    root = Path(args.root).resolve() if args.root else Path.cwd()
    if args.hooks_command == "install":
        # A-3 step 10. `install(force=...)` existed and the delivered surface could not reach it, so
        # a project whose hooksPath was already owned by another mechanism could be REFUSED and then
        # had no supported way forward. Taking over is a decision, so it stays explicit — and the
        # previous value is saved, which is what makes the takeover reversible.
        state = hooks_mod.install(root, force=args.force)
    else:
        state = {"uninstall": hooks_mod.uninstall,
                 "status": hooks_mod.status}[args.hooks_command](root)
    print(state.render())
    if state.status in (hooks_mod.REFUSED, hooks_mod.NOT_A_REPOSITORY):
        return EXIT_FAIL
    # `status` reports; it does not judge. Only `install` is asserting it achieved something.
    if args.hooks_command == "install" and not state.commissioned:
        return EXIT_FAIL
    return EXIT_OK


def cmd_version(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve() if args.root else _framework_root()
    print(versioning.read_version(root))
    return EXIT_OK


def cmd_status(args: argparse.Namespace) -> int:
    # independent Assurance finding N3. `status` carried the same conflation as `validate`: it printed one "framework root"
    # and called the project unresolved, which in a vendored install was the framework directory
    # being reported as though it were the whole answer.
    resolution = roots.resolve(Path(args.root) if args.root else None)
    if not resolution.resolved:
        print("ROOTS: AMBIGUOUS")
        print(f"  {resolution.detail}")
        print(resolution.render())
        return EXIT_USAGE
    root = resolution.framework_root
    flat = controls_mod.all_controls(root)
    mandatory = sum(1 for r in flat.values() if r.get("mandatory_or_conditional") == "MANDATORY")
    print(f"framework version : {versioning.read_version(root)}")
    print(f"framework root    : {root}")
    print(f"project root      : {resolution.project_root}")
    print(f"layout            : {resolution.layout}")
    print(f"controls defined  : {len(flat)} ({mandatory} mandatory)")
    print("project state     : not resolved — pbg init / pbg boot not yet implemented")
    print()
    print("NOT YET IMPLEMENTED: init, boot, adapt, verify, close.")
    print("This is a declared framework capability gap, not a passing status.")
    return EXIT_OK


# --------------------------------------------------------------------------------------------- #

def cmd_authority(args) -> int:
    """Validate or diagnose authority records (PD-2, F13, F14, F15)."""
    from . import authority as auth
    root = Path(args.root).resolve() if args.root else _framework_root()
    if args.authority_command == "diagnose":
        print(auth.render_diagnosis(auth.diagnose(root)))
        return 0

    if args.authority_command == "seat":
        # Placement Question B, made observable. "Has the executor attested?" is not a yes/no: an
        # authority may lawfully exist before its seat is occupied, and the state that matters is
        # whether the seat ACTED before it attested. Reported per record, because occupation is a
        # property of a seat and its evidence, not of the directory.
        from . import seat as seat_mod

        records = auth.read_records(root)
        worst = EXIT_OK
        for path, doc in sorted(records.items()):
            if not isinstance(doc, dict):
                print(f"{path}\n  UNPARSEABLE — seat occupation cannot be established\n")
                worst = EXIT_FAIL
                continue
            rel = str(Path(path).resolve().relative_to(root))
            state = seat_mod.lifecycle(root, doc, rel)
            print(rel)
            print(state.render())
            print()
            if state.errors:
                worst = EXIT_FAIL
            elif not state.verified and worst == EXIT_OK:
                worst = EXIT_AMBER
        return worst

    if args.authority_command == "separation":
        # SOD-TOOLING-0001. Reported per ASSURANCE record, because separation is a property of a
        # candidate and its two seats, not of the directory.
        from . import executors

        siblings = auth.read_records(root)
        assurance = {rel: doc for rel, doc in siblings.items()
                     if isinstance(doc, dict)
                     and str(doc.get("assigned_role", "")) == executors.ASSURANCE_ROLE}
        if not assurance:
            print("PBG-SOD-001: no ASSURANCE authority record exists, so there is nothing to "
                  "separate yet. This is NOT a pass.")
            return EXIT_AMBER
        worst = EXIT_OK
        for rel, doc in sorted(assurance.items()):
            result = executors.check_separation(root, doc, siblings)
            print(f"{rel}")
            print(result.render())
            print()
            if result.status == executors.FAIL:
                worst = EXIT_FAIL
            elif result.status == executors.NOT_VERIFIED and worst == EXIT_OK:
                worst = EXIT_AMBER
        return worst

    if getattr(args, "paths", None):
        # What the hook asks: judge the records this commit touches, not the whole archive.
        result = auth.validate_paths(root, args.paths)
        if result["ok"]:
            if not args.quiet:
                print(f"AUTHORITY: GREEN  ({len(result['checked'])} staged record(s) valid)")
            return 0
        print("AUTHORITY: INVALID")
        for rel, errors in result["errors"].items():
            print(f"  {rel}")
            for e in errors:
                print(f"    - {e}")
        return 1

    result = auth.validate_all(root)
    if result["ok"]:
        if not args.quiet:
            print("AUTHORITY: GREEN  (all records valid)")
            print()
            print("Enforcement truth:")
            for surface, state in auth.enforcement_truth(root).items():
                print(f"  {surface:52} {state}")
        return 0

    # Two answers, because they are two questions. `may I act` is answered by the ACTIVE record;
    # `is the archive clean` is answered by all of them. Append-only means an invalid CLOSED record
    # stays invalid and stays visible — rewriting it to turn this command green would destroy the
    # evidence the check exists to produce.
    print("AUTHORITY: INVALID")
    for rel, errors in result["errors"].items():
        marker = "  ACTIVE " if rel in result["active_errors"] else "  "
        print(f"{marker}{rel}")
        for e in errors:
            print(f"    - {e}")
    for incomplete in result["checks_not_completed"]:
        print(f"  check_not_completed: {incomplete}")
    print()
    print(f"active_authority_valid : {str(result['active_ok']).lower()}")
    print("Records that are CLOSED remain in append-only history exactly as written. They are "
          "reported, never rewritten, and they neither confer nor withdraw authority.")
    return 0 if (args.active_only and result["active_ok"]) else 1


def cmd_verify_unit(args) -> int:
    """The product path: declaration + Docker observation + effective identity + whole unit."""
    from . import unit_verify
    verdict, context = unit_verify.verify_unit(Path(args.root).resolve() if args.root else _framework_root(), use_runtime=not args.no_runtime)
    print(unit_verify.render(verdict, context))
    print()
    print(f"VERDICT: {'PASS' if verdict.ok else 'FAIL'}")
    return 0 if verdict.ok else 1



def cmd_required_tests(args) -> int:
    """Required Test Register validator (REQUIRED-TEST-REGISTER-CONTRACT-v1).

    COMPUTES the five contract checks; never reads an asserted status. Exit 0 only when the
    gate opens: every mandatory criterion PASS, population traced, register free of self-grading.
    There is no waiver flag, and none may be added (PID-AC-006).
    """
    from . import required_tests

    register = Path(args.register).resolve() if args.register else Path.cwd() / "required-tests.yaml"
    report = required_tests.verify(register)
    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        print(report.render())
    return EXIT_OK if report.gate_open else EXIT_FAIL


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pbg", description="PBGv2 governance tooling")
    parser.add_argument("--root", help="framework root (default: auto-detect)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_val = sub.add_parser("validate", help="validate framework and project integrity")
    p_val.add_argument("--json", action="store_true")
    p_val.add_argument("--project-manifest", help="path to a project manifest to check for weakening")
    p_val.set_defaults(func=cmd_validate)

    p_ctl = sub.add_parser("controls", help="list canonical controls")
    p_ctl.add_argument("--json", action="store_true")
    p_ctl.set_defaults(func=cmd_controls)

    p_log = sub.add_parser("log", help="validate canonical continuity records")
    p_log.add_argument("subcommand", nargs="?", default="validate",
                       choices=["validate", "rebuild", "chronology"])
    p_log.set_defaults(func=cmd_log)

    p_res = sub.add_parser("resume", help="reconcile recorded continuity against observed state")
    p_res.set_defaults(func=cmd_resume)

    p_boot = sub.add_parser("boot", help="boot the application Project Lead")
    p_boot.set_defaults(func=cmd_boot)

    p_hooks = sub.add_parser("hooks", help="commission the project-owned validation hook")
    hooks_sub = p_hooks.add_subparsers(dest="hooks_command", required=True)
    p_hook_install = hooks_sub.add_parser(
        "install", help="commission, using repository-local core.hooksPath only")
    p_hook_install.add_argument(
        "--force", action="store_true",
        help="take over a core.hooksPath this project does not own, saving the previous value so "
             "uninstall can restore it")
    hooks_sub.add_parser("status", help="report whether the hook is commissioned")
    hooks_sub.add_parser("uninstall", help="decommission, restoring any prior local configuration")
    p_hooks.set_defaults(func=cmd_hooks)

    p_ver = sub.add_parser("version", help="print the canonical framework version")
    p_ver.set_defaults(func=cmd_version)

    p_auth = sub.add_parser("authority", help="validate and diagnose authority records")
    auth_sub = p_auth.add_subparsers(dest="authority_command", required=True)
    p_auth_val = auth_sub.add_parser("validate", help="validate every authority record")
    p_auth_val.add_argument("--quiet", action="store_true", help="print only on failure")
    p_auth_val.add_argument("--path", dest="paths", action="append", metavar="REL_PATH",
                            help="validate only these records (the pre-commit hook's mode); "
                                 "repeatable")
    p_auth_val.add_argument("--active-only", action="store_true",
                            help="exit non-zero only when the ACTIVE authority is invalid; "
                                 "invalid CLOSED history is still reported")
    auth_sub.add_parser("diagnose", help="per-record diagnosis; names the corrupt record exactly")
    auth_sub.add_parser("seat",
                        help="seat occupation lifecycle: created, attested, occupied — or acted "
                             "without attesting")
    auth_sub.add_parser("separation",
                        help="PBG-SOD-001: compare the executor that produced each candidate with "
                             "the executor auditing it")
    p_auth.set_defaults(func=cmd_authority)

    p_vu = sub.add_parser("verify-unit",
                          help="verify the compute unit against its declaration AND its running self")
    p_vu.add_argument("--no-runtime", action="store_true",
                      help="declaration only; do not observe the running unit")
    p_vu.set_defaults(func=cmd_verify_unit)

    p_st = sub.add_parser("status", help="summarise framework and project state")
    p_st.set_defaults(func=cmd_status)


    p_rt = sub.add_parser("required-tests",
                          help="Required Test Register: compute status from the PID, the "
                               "register and append-only run records")
    rt_sub = p_rt.add_subparsers(dest="required_tests_command", required=True)
    p_rt_verify = rt_sub.add_parser(
        "verify", help="the five contract checks — population, negative control, execution "
                       "contract, independence, self-grading refusal")
    p_rt_verify.add_argument("--register", help="path to required-tests.yaml "
                                                "(default: ./required-tests.yaml)")
    p_rt_verify.add_argument("--json", action="store_true")
    p_rt_verify.set_defaults(func=cmd_required_tests)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except FileNotFoundError as exc:
        print(f"pbg: {exc}", file=sys.stderr)
        return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
