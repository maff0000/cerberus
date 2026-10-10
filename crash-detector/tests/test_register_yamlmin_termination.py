"""Regression cover for ``tools/register/_yamlmin.py`` — TERMINATION, and the refusals it states.

WHY THIS FILE EXISTS. ``tools/register/_yamlmin.py`` did not terminate on an ordinary
nested-sequence document (``CD-PL-F61``, confirming the seat-raised ``CD-ENG-WO2R-F14``).
Three register checks share that reader — ``check_egress_no_broker.py``,
``check_base_image_digest_pin.py`` and ``check_engine_no_witness_reach.py`` — and all three
returned exit 124 and NO VERDICT on the same input. A gate that cannot return a verdict is
what ``PBG-CI-002``'s "never a skip, for any reason" is aimed at: a hang is a skip of
indefinite length that also stops the pipeline behind it.

WHY EVERY READER CALL HERE IS WALL-CLOCK BOUNDED. A regression test for non-termination that
simply calls the reader would, on a regression, HANG THE WHOLE SUITE instead of failing it —
which is the defect wearing a test's clothes. :func:`bounded` puts a real timer on every call,
so a reintroduced stall arrives as a named FAILURE naming the document, in about a second.

WHAT IS ASSERTED. The RULE, not merely the exit (``CD-ENG-WO2R-F13``, adopted project method):
every refusal below asserts the exception type AND the substance of the reason, because a
document refused for a reason nobody intended has told you nothing.
"""

from __future__ import annotations

import importlib.util
import pathlib
import signal

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
READER_PATH = REPO_ROOT / "tools" / "register" / "_yamlmin.py"

#: Every reader call below must finish well inside this. The stalls this file covers are
#: unbounded, so any value comfortably above a real parse distinguishes them; the real
#: parses here are microseconds and the whole file runs in well under a second.
TIME_BUDGET_SECONDS = 5.0


def _load_reader():
    """Import the standalone reader by path.

    The register checks are stdlib-only scripts that run with no install step, so the reader
    is not an installed module and there is no package to import it from. Loading it by path
    keeps this test measuring THE FILE THE CHECKS ACTUALLY IMPORT rather than a copy.
    """
    spec = importlib.util.spec_from_file_location("_yamlmin_under_test", READER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


yamlmin = _load_reader()


class ReaderDidNotTerminate(AssertionError):
    """The reader ran past its wall-clock budget — the defect this file exists to catch."""


class bounded:
    """Fail, rather than hang, if the body runs past :data:`TIME_BUDGET_SECONDS`.

    ``signal.setitimer`` fires a real ``SIGALRM``. The stall this guards is a pure-Python
    loop, and CPython checks for pending signals between bytecodes, so the handler runs and
    the loop is unwound as an ordinary exception.
    """

    def __init__(self, label: str, seconds: float = TIME_BUDGET_SECONDS):
        self.label = label
        self.seconds = seconds

    def _fire(self, signum, frame):  # noqa: ARG002 - the handler signature is fixed
        raise ReaderDidNotTerminate(
            f"the reader did not terminate within {self.seconds}s on {self.label}. "
            f"This is CD-PL-F61 / CD-ENG-WO2R-F14 reintroduced: a parse loop re-entered at a "
            f"cursor that did not move. See the TERMINATION section of _yamlmin.py."
        )

    def __enter__(self):
        self._previous = signal.signal(signal.SIGALRM, self._fire)
        signal.setitimer(signal.ITIMER_REAL, self.seconds)
        return self

    def __exit__(self, *exc):
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, self._previous)
        return False


def parse(text: str, label: str):
    with bounded(label):
        return yamlmin.parse_block_yaml(text)


def refusal(text: str, label: str) -> str:
    """Parse expecting a stated refusal; return the reason so the caller can assert on it."""
    with bounded(label):
        with pytest.raises(yamlmin.YamlSubsetError) as caught:
            yamlmin.parse_block_yaml(text)
    return str(caught.value)


# --------------------------------------------------------------------------------------- #
# THE STALL CLASS. Every document below returned exit 124 — no value, no exception, no
# verdict — before this repair. Each must now terminate, and terminate with a STATED reason
# naming the line it could not read.
# --------------------------------------------------------------------------------------- #

#: The three-line minimal reproduction recorded in the dispatch. Nothing about it is exotic.
MINIMAL_STALL = "top:\n  - key:\n      - nested\n"

#: PL-T5's shape: `declared_in` written as a list of two authorities. An entirely ordinary
#: edit by someone documenting a second Blueprint reference. This is how the Project Lead met
#: the defect — by accident, on the first probe of that shape.
PL_T5_SHAPE = (
    "pending:\n"
    "  - declared_in:\n"
    '      - "BLUEPRINT $2 - ingredient sources"\n'
    "      - 198.51.100.24\n"
    '    blocked_by: "CD-D-005"\n'
)

#: V30, the variant the previous seat declared at boundary 8 rather than quietly repairing.
V30_SHAPE = "pending:\n  - declared_in:\n      - 198.51.100.24\n    blocked_by: \"CD-D-005\"\n"

#: DEEPER than either of those — the stall reached through four levels rather than two, so a
#: repair that special-cased one depth is caught here.
DEEPER_STALL = "a:\n  - b:\n      - c:\n          - d:\n              - e\n"

#: The stall at the DOCUMENT ROOT rather than beneath a mapping key.
ROOT_STALL = "- key:\n    - nested\n"

#: The inline key carries a SCALAR VALUE and the continuation is still a sequence. This one
#: matters: CD-ENG-WO2R-F14 recorded that a scalar first value "parses FINE" and that the
#: defect was "specifically the first key opening a sequence". That characterisation was too
#: narrow — the trigger is the CONTINUATION line's shape, not the inline key's value. Raised
#: as CD-ENG-READER-F03.
VALUE_BEARING_STALL = "top:\n  - key: value\n      - nested\n"

#: Reached through the block-scalar FOLDER's blind spot rather than through plain nesting:
#: `- key: |` is not recognised as opening a literal block, because the indicator test skips
#: any line beginning `- `. The raw body is handed to the parser as sequence items.
#: Raised as CD-ENG-READER-F04.
BLOCK_SCALAR_STALL = "top:\n  - key: |\n      - nested\n"

#: An ANCHOR in the inline value position, then a nested sequence — the anchor route rather
#: than the plain one (the case CD-ENG-WO2R-F19 left owed, folded in here).
ANCHOR_STALL = "top:\n  - key: &anch\n      - nested\n"

STALLED_BEFORE_THE_REPAIR = {
    "the three-line minimal reproduction": MINIMAL_STALL,
    "PL-T5 (declared_in as a list of two authorities)": PL_T5_SHAPE,
    "V30 (the seat-declared variant at boundary 8)": V30_SHAPE,
    "four levels deep": DEEPER_STALL,
    "at the document root": ROOT_STALL,
    "inline key carrying a scalar value": VALUE_BEARING_STALL,
    "through the block-scalar folder": BLOCK_SCALAR_STALL,
    "through an anchor in value position": ANCHOR_STALL,
}


@pytest.mark.parametrize("label", sorted(STALLED_BEFORE_THE_REPAIR))
def test_a_document_that_once_stalled_now_terminates(label: str) -> None:
    """It finishes. Before the repair every one of these was exit 124 under `timeout`."""
    with bounded(label):
        with pytest.raises(yamlmin.YamlSubsetError):
            yamlmin.parse_block_yaml(STALLED_BEFORE_THE_REPAIR[label])


@pytest.mark.parametrize("label", sorted(STALLED_BEFORE_THE_REPAIR))
def test_the_refusal_says_which_line_it_could_not_read(label: str) -> None:
    """A refusal that does not say WHAT it could not read is barely better than silence.

    Asserts the reason, not merely that something was raised (CD-ENG-WO2R-F13).
    """
    reason = refusal(STALLED_BEFORE_THE_REPAIR[label], label)
    assert "this reader cannot read" in reason
    assert "made no progress past" in reason
    assert reason.startswith("line "), reason
    # It names the supported subset, so the author knows how to write it instead.
    assert "block sequences of mappings" in reason


def test_the_minimal_reproduction_names_the_exact_offending_line() -> None:
    """Line 3 is `      - nested`, and that is what the reader must point at."""
    reason = refusal(MINIMAL_STALL, "minimal")
    assert reason.startswith("line 3:"), reason
    assert "- nested" in reason


# --------------------------------------------------------------------------------------- #
# NOTHING THAT PARSED BEFORE MAY STOP PARSING. The repair may only convert a stall into a
# refusal; it may not change any document the reader already read.
# --------------------------------------------------------------------------------------- #


def test_the_real_compose_file_still_parses() -> None:
    """The clean arm. Three register checks read this file and must keep reading it."""
    compose = REPO_ROOT / "deploy" / "compose.yaml"
    with bounded("deploy/compose.yaml"):
        document = yamlmin.load_yaml(compose)
    assert isinstance(document, dict)
    assert "services" in document


def test_a_block_sequence_of_mappings_still_parses() -> None:
    """The near miss recorded at CD-ENG-WO2R-F14: this shape always parsed and still does."""
    document = parse(
        "destinations:\n  - id: D1\n    services:\n      - x\n", "sequence of mappings"
    )
    assert document == {"destinations": [{"id": "D1", "services": ["x"]}]}


def test_nested_anchors_and_merge_keys_still_read_as_before() -> None:
    """Anchors are not resolved and merge keys are recorded literally, exactly as before."""
    document = parse(
        "top:\n  inner:\n    frag: &anch\n      a: 1\n  use:\n    <<: *anch\n", "anchors"
    )
    assert document == {"top": {"inner": {"frag": {"a": "1"}}, "use": {"<<": "*anch"}}}


def test_a_sequence_item_whose_nested_value_is_a_mapping_still_flattens() -> None:
    """PRESERVED DELIBERATELY, not endorsed.

    The reader flattens a mapping nested beneath a sequence item's inline key
    (``CD-ENG-WO2R-F15``, DISCLOSED). That is a partial parse and it is wrong, but changing
    it would change what ``check_egress_no_broker`` DECIDES about variant V27 — out of bounds
    for a termination repair. Pinned here so the behaviour cannot drift unnoticed, and
    re-raised as CD-ENG-READER-F05.
    """
    document = parse("top:\n  - key:\n      sub: 1\n", "flattening")
    assert document == {"top": [{"key": None, "sub": "1"}]}


def test_line_numbers_are_still_recorded() -> None:
    document = parse("a: 1\nb: 2\n", "line numbers")
    assert yamlmin.line_of(document, "a") == 1
    assert yamlmin.line_of(document, "b") == 2


def test_block_scalars_still_fold() -> None:
    document = parse("note: |\n  one\n  two\nafter: x\n", "block scalar")
    assert document == {"note": "one two", "after": "x"}


def test_empty_flow_collections_still_read_as_empty() -> None:
    document = parse("hosts: []\nlabels: {}\n", "empty flow")
    assert document == {"hosts": [], "labels": {}}


def test_unresolved_aliases_still_reports_where_a_posture_could_hide() -> None:
    document = parse("services:\n  a:\n    egress: *hidden\n", "aliases")
    found = yamlmin.unresolved_aliases(document)
    assert [(trail, alias) for trail, alias, _ in found] == [
        (("services", "a", "egress"), "*hidden")
    ]


# --------------------------------------------------------------------------------------- #
# MALFORMED DOCUMENTS MUST RAISE, AND SAY WHAT THEY COULD NOT READ. Silence and a partial
# parse are both worse than a refusal (the standard set at CD-D-048).
# --------------------------------------------------------------------------------------- #

MALFORMED = {
    "a tab in the indentation": ("a:\n\tb: 1\n", "tab in indentation"),
    "a non-empty flow collection": ("ports: [1, 2, 3]\n", "non-empty flow collections"),
    "a line that is neither a mapping entry nor a sequence item": (
        "a:\n  b: 1\n  loose\n",
        "neither a mapping entry nor a sequence item",
    ),
    "indentation that jumps for no reason": (
        "- a\n    - b\n",
        "unexpected indentation",
    ),
    "an empty document": ("\n# only a comment\n", "empty document"),
}


@pytest.mark.parametrize("label", sorted(MALFORMED))
def test_a_malformed_document_raises_with_its_reason(label: str) -> None:
    text, expected = MALFORMED[label]
    reason = refusal(text, label)
    assert expected in reason, f"{label}: refused for the wrong reason: {reason}"


def test_a_document_that_is_not_a_mapping_at_the_top_is_refused_by_load_yaml(
    tmp_path: pathlib.Path,
) -> None:
    document = tmp_path / "seq.yaml"
    document.write_text("- a\n- b\n", encoding="utf-8")
    with bounded("top-level sequence"):
        with pytest.raises(yamlmin.YamlSubsetError) as caught:
            yamlmin.load_yaml(document)
    assert "is not a mapping at the top level" in str(caught.value)


# --------------------------------------------------------------------------------------- #
# THE INVARIANT ITSELF. The repair is a property of the loops, so it is tested as a property
# and not only through the documents that happen to reach it.
# --------------------------------------------------------------------------------------- #


def test_advance_accepts_a_cursor_that_moved() -> None:
    lines = [(1, 0, "a: 1"), (2, 0, "b: 2")]
    assert yamlmin._advance(lines, 0, 1, "anything") == 1


def test_advance_refuses_a_cursor_that_did_not_move() -> None:
    """The whole repair in one assertion: a still cursor is refused, never re-entered."""
    lines = [(7, 4, "- nested")]
    with pytest.raises(yamlmin.YamlSubsetError) as caught:
        yamlmin._advance(lines, 0, 0, "a nested block")
    reason = str(caught.value)
    assert reason.startswith("line 7:")
    assert "a nested block" in reason
    assert "made no progress past" in reason
    assert "- nested" in reason


def test_advance_permits_a_still_cursor_at_end_of_input() -> None:
    """At end of input the enclosing loop's own bound ends it, so there is no stall."""
    assert yamlmin._advance([], 0, 0, "anything") == 0


def test_the_iteration_budget_still_fails_closed_if_the_guard_is_ever_removed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The backstop is live, not decorative.

    ``_advance`` is what closes the class today. This neuters it — standing in for a future
    edit that drops or bypasses the guard — and proves the reader still REFUSES rather than
    hanging. Termination does not rest on a single call site.
    """
    monkeypatch.setattr(yamlmin, "_advance", lambda lines, before, after, what: after)
    with bounded("budget backstop"):
        with pytest.raises(yamlmin.YamlSubsetError) as caught:
            yamlmin.parse_block_yaml(MINIMAL_STALL)
    reason = str(caught.value)
    assert "made no progress" in reason
    assert "iteration budget" in reason
    assert "internal invariant failure" in reason


def test_the_time_bound_itself_detects_a_hang() -> None:
    """Proves the harness above can actually catch a stall, so a green here means something.

    A regression test for non-termination is only worth its salt if the timer works. This
    runs a loop that never ends and asserts the guard unwinds it.
    """
    with pytest.raises(ReaderDidNotTerminate):
        with bounded("a deliberate spin", seconds=0.25):
            while True:
                pass
