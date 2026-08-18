"""The non-waivable floor, defined independently of the records it protects.

independent Assurance finding F-12. The runtime guard used to derive the floor from `exception_policy` in controls/*.yaml
-- the same mutable field an attacker edits. A guard that reads its authority from the thing it is
guarding cannot detect the removal of its own authority: relabel a control NON_WAIVABLE ->
TIME_BOUNDED and the floor simply becomes smaller, silently, with no disagreement to report.

This module is the independent authority. It ships. It is compared AGAINST the corpus, never
derived from it. It must not be generated from controls/*.yaml, manifest.yaml, migration
snapshots, tests/ or architecture docs -- those may describe or test the floor, but the floor is
defined here.
"""

from __future__ import annotations

from pathlib import Path

#: The seven. Product Authority, constitutional review 2026-07-29, reaffirmed 2026-08-02.
REQUIRED_FLOOR = {
    "PBG-ASSURE-012": {"title": "No synthetic GREEN",
                       "verification_mechanism": "ASSURANCE_CONTRACT_REF",
                       "modes": ("EVENT_TRIGGERED",)},
    "PBG-BOOT-002": {"title": "No agent self-assigns a role",
                     "verification_mechanism": "CHECK_REF",
                     "verification_ref": "boot.role_assignment_contract",
                     "modes": ("EVENT_TRIGGERED",)},
    "PBG-CONT-003": {"title": "Build Log history is append-only",
                     "verification_mechanism": "CHECK_REF",
                     "verification_ref": "continuity.append_only_fail_closed",
                     "modes": ("PER_WORK",)},
    "PBG-EVID-003": {"title": "No secret material appears in evidence",
                     "verification_mechanism": "CHECK_REF",
                     "verification_ref": "evidence.no_secret_material",
                     "modes": ("PER_WORK",)},
    "PBG-SOD-001": {"title": "Engineer and Assurance Engineer are never the same agent",
                    "verification_mechanism": "CHECK_REF",
                    "verification_ref": "sod.separation_evidence",
                    "modes": ("PER_WORK",)},
    "PBG-SOD-002": {"title": "The Engineer may not claim independent assurance of its own work",
                    "verification_mechanism": "ASSURANCE_CONTRACT_REF",
                    "modes": ("PER_WORK",)},
    "PBG-SOD-004": {"title": "The Assurance Engineer is non-implementing for governed changes",
                    "verification_mechanism": "ASSURANCE_CONTRACT_REF",
                    "modes": ("PER_WORK",)},
}

#: N-3 residual. Pinning posture fields alone left two bypasses independent Assurance proved: setting
#: verification_mechanism CHECK_REF -> NONE disconnected the verifier, and switching
#: applicability.mode to AUTHORING made the control never apply to real work. Both left every
#: previously-pinned value intact.
#:
#: The guard must not be conditional on the mutable value it protects. It therefore carries the
#: EXPECTED mechanism and reference per control, above, and compares -- rather than reading
#: whatever the record currently says and validating that against itself.
REQUIRED_POSTURE = {
    "status": "ACTIVE",
    "exception_policy": "NON_WAIVABLE",
    "mandatory_or_conditional": "MANDATORY",
}


def _neutralisation_problems(cid: str, rec: dict, expected: dict) -> list[str]:
    """Fields whose alteration removes a control from the floor without changing a pinned value."""
    problems = []

    mode = (rec.get("applicability") or {}).get("mode")
    if not mode:
        problems.append(f"{cid} has no applicability mode — it can never be found applicable")
    elif mode not in expected["modes"]:
        problems.append(
            f"{cid} applicability mode is {mode!r}, required one of {list(expected['modes'])} — "
            f"a floor control cannot be moved out of the work it governs")

    if not rec.get("roles"):
        problems.append(f"{cid} binds no roles — it applies to no actor")

    if rec.get("discharge_mechanism") == "NO_MECHANISM":
        problems.append(f"{cid} declares NO_MECHANISM — a floor control cannot be undischargeable")

    actual_mech = rec.get("verification_mechanism")
    if actual_mech != expected["verification_mechanism"]:
        problems.append(
            f"{cid} verification_mechanism is {actual_mech!r}, required "
            f"{expected['verification_mechanism']!r} — the mechanism that protects a floor control "
            f"cannot be changed or removed")

    if expected["verification_mechanism"] == "CHECK_REF":
        ref = rec.get("verification_ref")
        if ref != expected["verification_ref"]:
            problems.append(
                f"{cid} verification_ref is {ref!r}, required {expected['verification_ref']!r}")
        else:
            from . import checks as checks_mod
            try:
                checks_mod.resolve(cid, ref)
            except Exception as exc:
                problems.append(f"{cid} verifier binding is broken: {exc}")
    return problems


def check(root: Path) -> list[str]:
    """Compare the mutable corpus against the shipped floor. Any disagreement is a finding."""
    from . import controls as controls_mod

    problems: list[str] = []
    try:
        corpus = controls_mod.all_controls(root)
    except Exception as exc:
        return [f"floor unverifiable: the control corpus is unreadable ({exc})"]

    # Duplicate detection must run against the raw files: all_controls() is keyed by ID and would
    # silently collapse a duplicate into one entry.
    seen: dict[str, int] = {}
    try:
        import yaml
        for path in sorted((root / "controls").glob("*.yaml")):
            if path.name == "RETIRED_IDS.yaml":
                continue
            doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            for rec in doc.get("controls") or []:
                cid = rec.get("control_id")
                if cid in REQUIRED_FLOOR:
                    seen[cid] = seen.get(cid, 0) + 1
    except Exception as exc:
        return [f"floor unverifiable: control files unreadable ({exc})"]

    for cid, expected in sorted(REQUIRED_FLOOR.items()):
        title = expected["title"]
        count = seen.get(cid, 0)
        if count == 0:
            problems.append(f"{cid} is MISSING from the corpus — required floor: {title}")
            continue
        if count > 1:
            problems.append(f"{cid} is declared {count} times — ambiguous floor definition")
        rec = corpus.get(cid)
        if rec is None:
            problems.append(f"{cid} is present but unreadable")
            continue
        for field, required in REQUIRED_POSTURE.items():
            actual = rec.get(field)
            if actual != required:
                problems.append(
                    f"{cid} {field} is {actual!r}, required {required!r} — the non-waivable floor "
                    f"cannot be relabelled")
        problems.extend(_neutralisation_problems(cid, rec, expected))
        if rec.get("superseded_by"):
            problems.append(f"{cid} is retired via superseded_by — a floor control cannot be retired")

    extra = sorted(set(seen) - set(REQUIRED_FLOOR))
    if extra:                                                # pragma: no cover - defensive
        problems.append(f"unexpected floor members: {extra}")
    return problems
