"""CARRIER for `tools/audit/tree_fingerprint.py` — CD-PL-F100's repair.

**CD-RULE-006: A CHECK REPORTS, A CARRIER FAILS.** The fingerprint instrument reports; this
is the thing that goes red when it regresses. Every test builds its own throwaway git
repository and asserts by CONSTRUCTING the situation, never by reading the instrument's own
opinion of itself.

THE ACCEPTANCE TEST, VERBATIM FROM THE DISPATCH: *"a tree carrying an ignored artefact must
fingerprint identically to the same tree without it, and a tree with one byte of TRACKED
content changed must not. Both arms, measured."*
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import tempfile

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_INSTRUMENT = _REPO_ROOT / "tools" / "audit" / "tree_fingerprint.py"


def _run(root) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-B", str(_INSTRUMENT), "--root", str(root)],
        capture_output=True,
        text=True,
    )


def _fingerprint(root) -> str:
    result = _run(root)
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout.split("FINGERPRINT:")[1].strip()


@pytest.fixture()
def a_tree():
    """A throwaway git repository with a `.gitignore`, one tracked file, and a commit."""
    root = pathlib.Path(tempfile.mkdtemp(prefix="cd-fp-"))
    (root / ".gitignore").write_text(".cache_of_some_kind/\n")
    (root / "product.py").write_text("VALUE = 1\n")
    (root / "nested").mkdir()
    (root / "nested" / "more.py").write_text("OTHER = 2\n")
    subprocess.run(["git", "-C", str(root), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(root), "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-qm", "base"],
        check=True,
    )
    yield root
    shutil.rmtree(root, ignore_errors=True)


def test_an_ignored_artefact_does_not_move_the_fingerprint(a_tree):
    """**ARM ONE OF THE ACCEPTANCE TEST, AND THE WHOLE OF CD-PL-F100.**

    The shipped recipe swept `.pytest_cache/`, which is created by running `pytest` — which
    the dispatch ORDERS the auditor to do — so it fired its maximum-severity alarm ("something
    mutated under you and your verdict is about a tree that no longer exists") at an auditor
    for obeying the dispatch.
    """
    before = _fingerprint(a_tree)
    cache = a_tree / ".cache_of_some_kind"
    cache.mkdir()
    (cache / "anything").write_text("noise from running the suite\n")
    (cache / "more_noise").write_text("and more\n")
    after = _fingerprint(a_tree)
    assert before == after, (
        "AN IGNORED ARTEFACT MOVED THE FINGERPRINT. That is CD-PL-F100 exactly: the "
        "instrument fires its maximum-severity alarm at an auditor for running the suite."
    )


def test_one_byte_of_tracked_content_does_move_it(a_tree):
    """**ARM TWO. Without this, arm one is satisfied by an instrument that returns a
    constant** — which is the shape of every vacuous green this project has caught."""
    before = _fingerprint(a_tree)
    (a_tree / "product.py").write_text("VALUE = 1\n\n")
    after = _fingerprint(a_tree)
    assert before != after, (
        "ONE BYTE OF TRACKED CONTENT CHANGED AND THE FINGERPRINT DID NOT MOVE. The "
        "instrument is not measuring the tree."
    )


def test_an_untracked_product_file_moves_it(a_tree):
    """A NEW file that is not ignored is part of the tree and must be seen. The shipped
    recipe got this right and it is asserted here so the repair cannot lose it."""
    before = _fingerprint(a_tree)
    (a_tree / "brand_new.py").write_text("NEW = 3\n")
    assert _fingerprint(a_tree) != before


def test_it_refuses_outside_a_git_worktree():
    """**REFUSAL ONE, and it is the worst of the three the shell one-liner had.**

    Measured in `/tmp`: `git ls-files` writes `fatal: not a git repository` to stderr, the
    pipeline continues, and `sha256sum` of empty input yields a confident-looking digest —
    **a fingerprint that means "I looked at nothing", indistinguishable from one that means
    "the tree is this".** This project's own `Check.done` already refuses that shape.
    """
    root = pathlib.Path(tempfile.mkdtemp(prefix="cd-fp-nogit-"))
    try:
        result = _run(root)
        assert result.returncode == 3, result.stdout + result.stderr
        assert "not inside a git worktree" in result.stderr
        assert "FINGERPRINT:" not in result.stdout, (
            "it printed a fingerprint for a directory it could not read an ignore "
            "declaration for"
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_it_refuses_a_tracked_file_deleted_from_the_worktree(a_tree):
    """**REFUSAL TWO.** Measured on the shell recipe: `xargs` exits 123, but a pipeline's
    status is its LAST command's, so the one-liner returned 0 and printed a fingerprint for a
    tree that does not hold together."""
    (a_tree / "product.py").unlink()
    result = _run(a_tree)
    assert result.returncode == 3, result.stdout + result.stderr
    assert "could not be read" in result.stderr
    assert "product.py" in result.stderr
    assert "FINGERPRINT:" not in result.stdout


def test_the_exclusions_are_printed_because_that_is_the_answer_to_its_own_weakness(a_tree):
    """**THE KNOWN COST, MADE VISIBLE RATHER THAN ARGUED AWAY.**

    This instrument delegates the ignore decision to git, so it inherits `.gitignore`'s
    correctness. **IT CANNOT VERIFY THAT. WHAT IT CAN DO IS PRINT EVERY PATH IT EXCLUDED** —
    and an exclusion a reader can see is an exclusion a reader can challenge. The shipped
    recipe's *inclusion* of cache files was invisible for exactly as long as nobody printed it.
    """
    cache = a_tree / ".cache_of_some_kind"
    cache.mkdir()
    (cache / "noise") .write_text("x\n")
    result = _run(a_tree)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "EXCLUDED by .gitignore: 1" in result.stdout
    assert ".cache_of_some_kind/noise" in result.stdout


def test_an_ignore_rule_can_never_hide_TRACKED_content(a_tree):
    """**THE MEASURED BOUND ON THIS INSTRUMENT'S KNOWN WEAKNESS, AND IT IS NARROWER THAN THE
    WEAKNESS WAS DISCLOSED AS.**

    The disclosed cost is *"a wrongly-ignored product file becomes invisible to the
    fingerprint"*. **MEASURED, THAT IS TRUE ONLY OF FILES THAT WERE NEVER COMMITTED**, because
    `git ls-files --cached` lists every TRACKED file regardless of any ignore rule. A hostile
    `.gitignore` containing `*` dropped into a source directory removes NOTHING that is
    tracked.

    Asserted here rather than left as a comfortable belief, because **"safer than disclosed"
    is exactly the direction a reader waves through**, and if a future git or a future flag
    changes it this must go red.
    """
    before = _fingerprint(a_tree)
    (a_tree / "nested" / ".gitignore").write_text("*\n")
    after = _fingerprint(a_tree)
    assert before == after, (
        "AN IGNORE RULE REMOVED TRACKED CONTENT FROM THE FINGERPRINT. The bound this "
        "instrument's declared limit relies on has gone, and the limit now understates the "
        "weakness — correct it in all three CD-RULE-004 places."
    )

    # AND THE OTHER HALF, ASSERTED SO THE BOUND IS NOT MISTAKEN FOR A CLOSURE: an UNTRACKED
    # file IS hidden by that same rule. That is the residue, it is real, and the only signal a
    # reader gets is the printed exclusion count.
    (a_tree / "nested" / "never_committed.py").write_text("HIDDEN = 4\n")
    assert _fingerprint(a_tree) == after, (
        "expected an untracked file under a `*` ignore rule to be excluded; if it is now "
        "included, the declared residue is wrong in the safe direction and should be corrected"
    )


def test_it_reproduces_the_historic_shell_recipe_byte_for_byte(a_tree):
    """**A FINGERPRINT INSTRUMENT THAT SILENTLY CHANGED THE VALUE WOULD INVALIDATE EVERY
    RECORDED FIGURE IT WAS BUILT TO PROTECT.**

    The digest must equal what
    `git ls-files -z --cached --others --exclude-standard | sed -z 's|^|./|' |
     LC_ALL=C sort -z | xargs -0 sha256sum | sha256sum`
    produces, so values taken before this instrument existed remain comparable.
    """
    shell = subprocess.run(
        "git ls-files -z --cached --others --exclude-standard "
        "| sed -z 's|^|./|' | LC_ALL=C sort -z | xargs -0 sha256sum | sha256sum",
        shell=True,
        cwd=a_tree,
        capture_output=True,
        text=True,
    )
    assert shell.returncode == 0, shell.stderr
    assert _fingerprint(a_tree) == shell.stdout.split()[0]
