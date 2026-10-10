"""CARRIER for the MINIMAL FINDINGS REGISTER — ``PO-DECISIONS-0014`` ruling 1.

    *"this project has finding IDs and NO FINDINGS REGISTER, so the `finding` field would be
     an unchecked string. A MINIMAL findings register is created in the same act — id,
     raised_at (boundary SHA), status (OPEN / CLOSED / SUPERSEDED), nothing else — and
     `DEFECT_OPEN.finding` resolves against it or the row refuses. An index, not a system."*

**EVERY CHECK HERE HAS A REFUSING ARM AND A PASSING ARM, AND BOTH ARE RUN.** A resolution
check that has only ever seen ids that resolve has never been shown to resolve anything; a
closed-set check that has only ever seen members has never been shown to close a set. That
symmetry is the whole of this file, and it is why each pair sits next to its partner rather
than in a "negative tests" section somebody can delete.

Every test builds a THROWAWAY COPY of the tree and edits the registers THERE. The
repository's own ``tools/sweep/declared_dispositions.py`` and
``governance/findings/findings-register.json`` are never written to by a test.
"""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SWEEP_REL = pathlib.Path("tools") / "sweep" / "delegated_judgement_sweep.py"
_REGISTER_REL = pathlib.Path("tools") / "sweep" / "declared_dispositions.py"
_FINDINGS_REL = pathlib.Path("governance") / "findings" / "findings-register.json"

#: A site key that does not exist in the swept tree. Using one keeps these tests about the
#: FINDINGS check and not about set equality: the run stays red either way, and every
#: assertion below is about the presence or absence of a NAMED rule, never about the exit code
#: alone. An exit code is the one signal this project has repeatedly proved cannot carry a
#: proposition on its own.
_A_SITE = (
    '("crash_detector.time_utc", "a_probe_site", "ISINSTANCE", "isinstance(x, int)")'
)


@pytest.fixture()
def a_tree():
    root = pathlib.Path(tempfile.mkdtemp(prefix="cd-findings-"))
    for part in ("src", "tools"):
        shutil.copytree(_REPO_ROOT / part, root / part)
    shutil.copytree(
        _REPO_ROOT / "governance" / "findings", root / "governance" / "findings"
    )
    yield root
    shutil.rmtree(root, ignore_errors=True)


def _run(root) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-B", str(root / _SWEEP_REL), "--root", str(root)],
        capture_output=True,
        text=True,
    )


def _add_entry(root, value_literal: str, key_literal: str = _A_SITE) -> None:
    register = root / _REGISTER_REL
    register.write_text(
        register.read_text()
        + f"\n\nDECLARED_ADMISSIONS[{key_literal}] = {value_literal}\n"
    )


def _findings(root):
    return json.loads((root / _FINDINGS_REL).read_text(encoding="utf-8"))


def _write_findings(root, rows) -> None:
    (root / _FINDINGS_REL).write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")


def _defect_open(finding: str) -> str:
    return (
        f'("DEFECT_OPEN", {{"finding": "{finding}", '
        '"measured_reach": "a probe entry written by a carrier", '
        '"counterfactual": "without it the probe entry would not exist"})'
    )


# ------------------------------------------------------------------------------------- #
# THE RESOLUTION CHECK — the ruling's own sentence, both arms.
# ------------------------------------------------------------------------------------- #


def test_a_DEFECT_OPEN_citing_an_id_absent_from_the_register_REFUSES(a_tree):
    """**THE REFUSING ARM THE RULING ASKED FOR IN TERMS.**

    Before this act ``finding`` was a string nobody checked, so a disposition could rest on a
    finding that had never been raised and the instrument would print it without comment.
    """
    _add_entry(a_tree, _defect_open("CD-F-9999"))
    result = _run(a_tree)
    assert result.returncode == 1
    assert "FINDING_DOES_NOT_RESOLVE" in result.stdout, result.stdout[-3000:]
    assert "CD-F-9999" in result.stdout


def test_a_DEFECT_OPEN_citing_a_CLOSED_id_REFUSES(a_tree):
    """**THE SECOND REFUSING ARM, AND IT IS A DIFFERENT MISTAKE FROM THE FIRST.**

    An id that resolves is not enough. A disposition resting on a finding somebody has closed
    is a disposition whose reason has died, which is precisely the ground
    ``PO-DECISIONS-0015`` ruling 4 gave for reversing Category C.
    """
    rows = _findings(a_tree)
    rows.append({
        "id": "CD-F-0099",
        "raised_at": "0" * 40,
        "status": "CLOSED",
    })
    _write_findings(a_tree, rows)
    _add_entry(a_tree, _defect_open("CD-F-0099"))
    result = _run(a_tree)
    assert result.returncode == 1
    assert "FINDING_IS_NOT_OPEN" in result.stdout, result.stdout[-3000:]
    assert "CLOSED" in result.stdout


def test_a_DEFECT_OPEN_citing_an_OPEN_id_does_NOT_refuse(a_tree):
    """**THE PASSING ARM, WITHOUT WHICH THE TWO ABOVE ARE SATISFIED BY A CHECK THAT REFUSES
    EVERYTHING.** A resolution check that never resolves anything is not a resolution check.
    """
    identifiers = [row["id"] for row in _findings(a_tree)]
    assert identifiers, "the register is empty; the arm below would be vacuous"
    _add_entry(a_tree, _defect_open(identifiers[0]))
    result = _run(a_tree)
    assert "FINDING_DOES_NOT_RESOLVE" not in result.stdout, result.stdout[-3000:]
    assert "FINDING_IS_NOT_OPEN" not in result.stdout


def test_the_shipped_register_resolves_every_finding_it_cites(a_tree):
    """The register as this repository actually ships it. **THE ONE ARM THAT IS ABOUT THE REAL
    SUBJECT AND NOT ABOUT A PROBE ENTRY** — the two rules above must be absent from an
    untouched run, or the act shipped a register citing findings that do not exist.
    """
    result = _run(a_tree)
    assert "FINDING_DOES_NOT_RESOLVE" not in result.stdout, result.stdout[-4000:]
    assert "FINDING_IS_NOT_OPEN" not in result.stdout, result.stdout[-4000:]


# ------------------------------------------------------------------------------------- #
# `nothing else` — THE RULING'S OWN WORDS, MADE A CHECK.
# ------------------------------------------------------------------------------------- #


def test_a_register_row_carrying_ANY_fourth_field_REFUSES(a_tree):
    """*"id, raised_at, status, **nothing else** … An index, not a system."*

    **THIS IS THE CHECK THAT KEEPS THE REGISTER MINIMAL AFTER EVERY SEAT THAT COMES NEXT.** A
    findings register that is allowed to grow a `title` grows a `severity`, then an `owner`,
    and is the hand-maintained summary the ruling created it to stop. The substance of a
    finding lives in the document that raised it.
    """
    rows = _findings(a_tree)
    rows[0]["severity"] = "HIGH"
    _write_findings(a_tree, rows)
    result = _run(a_tree)
    assert result.returncode == 1
    assert "FINDINGS_REGISTER_ROW_MALFORMED" in result.stdout, result.stdout[-3000:]
    assert "severity" in result.stdout


def test_a_register_row_MISSING_a_field_REFUSES(a_tree):
    """The other direction of the same equality: three fields, not "at most three"."""
    rows = _findings(a_tree)
    del rows[0]["status"]
    _write_findings(a_tree, rows)
    result = _run(a_tree)
    assert result.returncode == 1
    assert "FINDINGS_REGISTER_ROW_MALFORMED" in result.stdout, result.stdout[-3000:]


def test_a_status_outside_the_closed_set_REFUSES(a_tree):
    """OPEN / CLOSED / SUPERSEDED is a closed set, and a set nobody can be shown to be outside
    of is not closed."""
    rows = _findings(a_tree)
    rows[0]["status"] = "PROBABLY_FINE"
    _write_findings(a_tree, rows)
    result = _run(a_tree)
    assert result.returncode == 1
    assert "FINDINGS_REGISTER_BAD_STATUS" in result.stdout, result.stdout[-3000:]
    assert "PROBABLY_FINE" in result.stdout


def test_an_ABBREVIATED_raised_at_REFUSES(a_tree):
    """``CD-RULE-009`` and ``CD-PL-F36``: a SHA in a governed record is resolved, never
    transcribed. An abbreviated SHA is the shape a transcription arrives in.

    **DECLARED LIMIT OF THIS CHECK, MEASURED AND NOT GLOSSED:** it proves the SHA is 40
    lower-case hex characters and NOTHING MORE. It does not prove the object exists, and it
    cannot — the sweep runs from an extraction with no repository. A register full of
    well-formed SHAs that name nothing would pass this check. **NOT PROVED TO BE CARRIED
    ANYWHERE**; the carrier for existence is the human resolving each with
    ``git rev-parse`` and ``git cat-file -t``.
    """
    rows = _findings(a_tree)
    rows[0]["raised_at"] = "af2accb"
    _write_findings(a_tree, rows)
    result = _run(a_tree)
    assert result.returncode == 1
    assert "FINDINGS_REGISTER_BAD_SHA" in result.stdout, result.stdout[-3000:]


def test_a_duplicate_id_REFUSES(a_tree):
    """An index with two answers for one id is not an index."""
    rows = _findings(a_tree)
    rows.append(dict(rows[0]))
    _write_findings(a_tree, rows)
    result = _run(a_tree)
    assert result.returncode == 1
    assert "FINDINGS_REGISTER_DUPLICATE_ID" in result.stdout, result.stdout[-3000:]


def test_an_ABSENT_register_REFUSES_rather_than_crashing_the_run(a_tree):
    """**AN INSTRUMENT THAT DIES ON ITS OWN INPUT TELLS AN AUDITOR LESS THAN ONE THAT
    REPORTS.** Deleting the register must not be a way to make the resolution check stop
    complaining, and it must not be a way to make the sweep unrunnable either.
    """
    (a_tree / _FINDINGS_REL).unlink()
    result = _run(a_tree)
    assert result.returncode == 1
    assert "FINDINGS_REGISTER_ABSENT" in result.stdout, result.stdout[-3000:]
    assert "CD-CLASS-2-SWEEP: FAIL" in result.stdout, "the run must still complete and report"


def test_the_shipped_register_is_well_formed_on_every_check_at_once(a_tree):
    """The passing arm for the whole of the register's own shape."""
    result = _run(a_tree)
    for rule in (
        "FINDINGS_REGISTER_ABSENT",
        "FINDINGS_REGISTER_UNREADABLE",
        "FINDINGS_REGISTER_ROW_MALFORMED",
        "FINDINGS_REGISTER_BAD_STATUS",
        "FINDINGS_REGISTER_BAD_SHA",
        "FINDINGS_REGISTER_DUPLICATE_ID",
    ):
        assert rule not in result.stdout, f"{rule}\n{result.stdout[-4000:]}"
