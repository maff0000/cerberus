#!/bin/bash
# =================================================================================================
# CC-I — THE VACUITY CONTROL. IT IS NOT DECORATION AND IT IS NOT OPTIONAL.
#
# *** AN INSTRUMENT THAT FAILS ON EVERYTHING IS NOT A GUARD, IT IS A BRICK, AND A PLANT SET WITH
# NO PASSING CONTROL CANNOT TELL THE DIFFERENCE. ***
#
# CC-A..CC-H are eight trees on which this instrument MUST go RED. This arm is the one on which it
# MUST go GREEN, and it carries the same weight as any of them: without it, every red above is
# satisfied by an instrument that has simply stopped being able to say yes.
#
# It is a `.sh` and not a `.patch` because IT MUTATES NOTHING — that is the whole point. C5 is the
# established precedent for a non-patch arm in this directory.
#
# WHAT IT PROVES, SPECIFICALLY, AND WHY IT IS THE ROOT-LEVEL GREEN CONTROL FOR `RULE CC`:
#   * `RULE CC` does NOT fire on the nineteen root properties the two contracts legitimately
#     declare (10 public + 11 private, of which 4 are canonical dial slots and 17 are allowlisted
#     non-dial properties across the two surfaces);
#   * `RULE CC`'s limb (b) is NOT vacuous: all 34 live-gate probes REFUSE, and the two baseline
#     controls ADMIT, so the refusals are attributable to the probe and not to a broken baseline;
#   * `CD-CALM-CANON-009` and `CD-CALM-FRESH-010` do NOT fire on the six branches (three per
#     surface) the clean contracts declare — the `VALUE` branch still MAY carry `calm`, which is
#     `PID §4`'s base case and the reason `calm` exists at all.
#
# THE DECLARED EXPECTATION, AND AN AUDITOR SHOULD READ THE COUNT AND NOT ONLY THE WORD "PASS":
#
#     CD-RT-001-MISSING-DATA-NEVER-CALM: PASS — 243 assertions, 0 violations     exit 0
#
# 243 IS 144 + 99. The 99 are accounted exactly, and the accounting is part of the control: a
# "PASS" whose assertion count has silently fallen is an instrument that has stopped looking.
#     27  RULE CC structural   — 2 root-closure premises + 10/11 root properties + 1 limb(a)==driven,
#                                per surface
#     36  RULE CC limb (b)     — 2 baseline ADMIT controls + 34 calm-carrying-probe REFUSALS
#      6  CD-CALM-CANON-009    — 3 union-level assertions per surface
#     30  CC-2/CC-3 per branch — (4 canonical-path + 1 affirmative-value) x 3 branches x 2 surfaces
#
# =================================================================================================
set -u
ROOT="${1:-.}"
cd "$ROOT" || { echo "CC-I: cannot cd to $ROOT"; exit 2; }

echo "CC-I — VACUITY CONTROL, on an UNMUTATED tree at $(pwd)"
echo "commit: $(git rev-parse HEAD 2>/dev/null || echo '<not a git tree>')"
echo "worktree dirty: $(git status --porcelain 2>/dev/null | wc -l) file(s)"
echo

PYTHONPATH=src python3 -B tools/register/check_missing_data_never_calm.py --root .
rc=$?

echo
echo "exit code taken FROM THE COMMAND and never from a pipe: $rc"
if [ "$rc" != "0" ]; then
  echo "CC-I: *** FAILED. THE INSTRUMENT IS RED ON A CLEAN TREE. ***"
  echo "     Every RED arm in this set is now uninterpretable: an instrument that fails on the"
  echo "     unmutated contracts cannot tell 'the forbidden thing is impossible' from"
  echo "     'everything is impossible'."
  exit 1
fi
echo "CC-I: PASSED — the instrument is GREEN on the clean tree, so the eight RED arms mean something."
