#!/usr/bin/env bash
# P-Q — `CD-D-166` / `CD-ENG-WO2R3-04-F05`: WHAT DOES THE `gates` FIELD ACTUALLY HOLD?
#
#     bash variants/WO-2R3/P-Q-what-does-the-gates-field-actually-hold.sh
#
# **IT IS AN INSTRUMENT THAT REPORTS AND IT IS NOT A CARRIER** (`CD-RULE-006`). It exits 0
# whatever it measures, it MUTATES NOTHING IN THE WORKTREE, and every arm builds its own
# pristine `git archive` extraction under /tmp and runs THAT TREE'S OWN COPY of the sweep,
# printing the tree's `pwd` and the sweep's own `subject:` line (`CD-PL-F98`: two arms of a
# probe once resolved their root from `__file__` and BOTH ARMS MEASURED THE SAME TREE).
#
# THE FINDING IT MEASURES, VERBATIM (`CD-ENG-WO2R3-04-F05`, upheld in full at
# `PO-DECISIONS-0016` ruling 2):
#
#   "`gates` checks EXISTENCE and DIFFERENT-MODULE and NOTHING ELSE. Nothing checks that the
#    named site is actually DOWNSTREAM, REACHABLE, or RELATED. THE GATING RELATION IS STILL A
#    SEAT'S CLAIM."
#
# FOUR ARMS. THE ORDER MATTERS AND ARM B IS THE ONE THAT DECIDES IT.
#
#   CONTROL   the tree unchanged — so that every later arm's delta is against a measured
#             baseline and not against a remembered one.
#
#   ARM A     THE RENAME TEST. The GATED site's expression is `isinstance(window, float)` in
#             `ConfigSnapshot.__post_init__`. Rename that local from `window` to
#             `staleness_window` — A PURE RENAME. The gating RELATION is untouched: the same
#             admission, in the same function, on the same value, in the same module, gating
#             the same path. **IF THE CRITERION IS STRUCTURAL, NOTHING CHANGES. IF IT IS
#             TEXTUAL, THE ROW REFUSES.**
#
#   ARM B     THE SOUNDNESS TEST, AND THE ONE THE FINDING IS ABOUT. Leave every line of
#             product source alone and repoint `gates` at
#             `crash_detector.time_utc::parse_utc ISINSTANCE: isinstance(text, str)` — a REAL
#             site, in a DIFFERENT module, **and one that gates nothing whatsoever about
#             `_EachOf.refusal`.** The claim is now false. **IF THE CRITERION HOLDS THE
#             RELATION, THIS REFUSES. IF IT HOLDS ONLY EXISTENCE AND MODULE-DIFFERENCE, IT
#             PASSES.**
#
#   ARM C     THE VACUITY CHECK, WHICH THE RENAME TEST DOES NOT GIVE YOU. This project added
#             the rule at the sixth gate: *the rename test proves a criterion is not a
#             VOCABULARY; IT DOES NOT PROVE IT IS NOT VACUOUS. A criterion that always answers
#             "not gated" passes the rename test perfectly and is worthless.* So: point
#             `gates` at a key that exists NOWHERE, and confirm the criterion CAN refuse. A
#             criterion that never refuses is decoration whatever else it does.
#
# **READ THE `rule:` NAME AND NOT THE EXIT CODE.** The sweep exits 1 on this tree already —
# three stale keys and one undeclared module, held stale by `PO-DECISIONS-0017` ruling 2 —
# so every arm here exits 1 and **an exit code tells you nothing at all.** Each arm therefore
# prints the COUNT of `GATES_*` rules it raised, which is the only number that moves.

set -u

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SHA="$(cd "$REPO" && git rev-parse HEAD)"
BASE="/tmp/cd-gates-$$"
DISP="tools/sweep/declared_dispositions.py"
SWEEP="tools/sweep/delegated_judgement_sweep.py"

echo "probe : P-Q — what does the gates field actually hold?"
echo "repo  : $REPO"
echo "sha   : $SHA"
echo "python: $(python3 --version 2>&1)"
echo

extract () {   # $1 = arm name -> echoes the tree path
    local tree="$BASE/$1"
    mkdir -p "$tree"
    ( cd "$REPO" && git archive "$SHA" ) | tar -x -C "$tree"
    echo "$tree"
}

report () {    # $1 = arm label, $2 = tree
    local label="$1" tree="$2" out rc gates
    out="$( cd "$tree" && python3 -B "$SWEEP" --root . 2>&1 )"
    rc=$?
    gates="$( printf '%s\n' "$out" | grep -cE 'GATES_SITE_DOES_NOT_EXIST|GATES_SITE_IS_IN_THE_DECLARING_MODULE' )"
    echo "=== $label"
    echo "    pwd (this arm's own tree) : $tree"
    echo "    the sweep's own subject   : $( printf '%s\n' "$out" | grep -m1 -E 'SUBJECT SET|subject' )"
    echo "    verdict line              : $( printf '%s\n' "$out" | tail -1 )"
    echo "    EXIT                      : $rc   <- MEANINGLESS HERE, see the header"
    echo "    GATES_* rules raised      : $gates"
    if [ "$gates" -gt 0 ]; then
        printf '%s\n' "$out" | grep -E 'GATES_SITE_DOES_NOT_EXIST|GATES_SITE_IS_IN_THE_DECLARING_MODULE' \
            | head -2 | sed 's/^/      /'
    fi
    echo
}

# ---------------------------------------------------------------------------- CONTROL ----
CONTROL="$(extract control)"
report "CONTROL — the tree unchanged" "$CONTROL"

# ------------------------------------------------------------------------------ ARM A ----
ARMA="$(extract arm-a-rename)"
python3 - "$ARMA" <<'PY'
import pathlib, sys
tree = pathlib.Path(sys.argv[1])
p = tree / "src" / "crash_detector" / "engine" / "config.py"
text = p.read_text()
# A PURE RENAME OF ONE LOCAL, and NOTHING ELSE IN THE FILE IS TOUCHED — the exact statements
# are matched so no docstring, comment or unrelated identifier can be swept up. An auditor
# must be able to read this arm and agree that the RELATION did not move.
EXACT = [
    ("        window = self.staleness_window_seconds\n",
     "        admissible = self.staleness_window_seconds\n"),
    ("        if isinstance(window, bool) or not isinstance(window, float):\n",
     "        if isinstance(admissible, bool) or not isinstance(admissible, float):\n"),
    ('                f"{type(window).__name__}"\n',
     '                f"{type(admissible).__name__}"\n'),
]
for old, new in EXACT:
    assert text.count(old) == 1, f"the subject of ARM A moved; fix the probe: {old!r}"
    text = text.replace(old, new)
# every REMAINING use of the local in that function, matched as a word boundary inside the
# one statement block the rename covers
text = text.replace("if window <= 0.0", "if admissible <= 0.0")
text = text.replace("math.isfinite(window)", "math.isfinite(admissible)")
text = text.replace("StalenessWindow(seconds=window)", "StalenessWindow(seconds=admissible)")
p.write_text(text)
assert "isinstance(admissible, float)" in p.read_text(), "the rename did not land"
print(f"    ARM A rewrote {p} — PURE RENAME of one local, three exact statements")
PY
report "ARM A — THE RENAME TEST (relation unchanged, text changed)" "$ARMA"

# ------------------------------------------------------------------------------ ARM B ----
ARMB="$(extract arm-b-unrelated)"
python3 - "$ARMB" <<'PY'
import pathlib, sys
tree = pathlib.Path(sys.argv[1])
p = tree / "tools" / "sweep" / "declared_dispositions.py"
text = p.read_text()
real = ("""            "gates": (
                'crash_detector.engine.config',
                'ConfigSnapshot.__post_init__',
                'ISINSTANCE',
                'isinstance(window, float)',
            ),""")
assert real in text, "the subject of ARM B moved; fix the probe"
unrelated = ("""            "gates": (
                'crash_detector.time_utc',
                'parse_utc',
                'ISINSTANCE',
                'isinstance(text, str)',
            ),""")
count = text.count(real)
p.write_text(text.replace(real, unrelated))
print(f"    ARM B repointed {count} `gates` claim(s) at a REAL site in a DIFFERENT module")
print("           that gates NOTHING about the declaring site. NO PRODUCT SOURCE TOUCHED.")
PY
report "ARM B — THE SOUNDNESS TEST (text unchanged, relation destroyed)" "$ARMB"

# ------------------------------------------------------------------------------ ARM C ----
ARMC="$(extract arm-c-vacuity)"
python3 - "$ARMC" <<'PY'
import pathlib, sys
tree = pathlib.Path(sys.argv[1])
p = tree / "tools" / "sweep" / "declared_dispositions.py"
text = p.read_text()
real = "'isinstance(window, float)',\n            ),"
assert real in text, "the subject of ARM C moved; fix the probe"
p.write_text(text.replace(real, "'isinstance(nothing_of_the_kind, float)',\n            ),"))
print("    ARM C pointed every `gates` claim at a key that exists NOWHERE")
PY
report "ARM C — THE VACUITY CHECK (can the criterion refuse at all?)" "$ARMC"

echo "artefacts left under $BASE — delete them when you have read them."
echo
echo "THIS PROBE STATES NO CONCLUSION. The four numbers above are the measurement;"
echo "what they mean is argued in the seat's return and in the Build Log entry."
