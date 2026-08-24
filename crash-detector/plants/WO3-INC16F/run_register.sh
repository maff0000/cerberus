#!/usr/bin/env bash
# WO-3 INCREMENT 16F — run EVERY `execute:` line of required-tests.yaml IN the given tree.
# Written and run by CD-ENG-WO3-14.
#
# *** THIS IS THE ACCEPTANCE TEST OF THE INCREMENT. *** At `a9e19c3` the per-line rc list on the
# `W5G` and `W5B2` trees was `diff`-IDENTICAL to the clean tip — `TOTAL lines=32 rc0=21
# nonzero=11` on all three, `diff` rc=0 both times, NOT ONE OF THE THIRTY-TWO LINES MOVING —
# while the live gate ADMITTED a 1970-stamped calm dial on both surfaces. That is `A313-F1`.
# The whole of 16F is: run this on a clean extraction of the new tip and on each arm's
# extraction of the same tip, `diff` the two per-line lists, AND THE DIFF MUST NOT BE EMPTY.
#
# It is functionally identical to `plants/WO3-INC16E/run_register.sh`, which this seat also ran
# unmodified for the `A313-F1` reproduction; it is carried here so the 16F plant set is
# self-contained for an auditor who extracts only this directory's tree.
#
# rc is TAKEN FROM THE COMMAND, never from a pipe (`CD-ENG-F02`'s defect class).
# The line count is NOT hard-coded: it is whatever the register declares in the tree named.
#
# usage: run_register.sh <tree>
set -u
TREE="$1"
cd "$TREE" || exit 99
n=0; zero=0; nonzero=0
mapfile -t LINES < <(grep -nE '^[[:space:]]*execute:[[:space:]]*\S' required-tests.yaml)
for entry in "${LINES[@]}"; do
  lineno="${entry%%:*}"
  cmd="${entry#*execute:}"
  cmd="${cmd# }"
  n=$((n+1))
  out=$(eval "$cmd" 2>&1)
  rc=$?          # *** RC FROM THE COMMAND ***
  if [ "$rc" -eq 0 ]; then zero=$((zero+1)); else nonzero=$((nonzero+1)); fi
  tail160=$(printf '%s' "$out" | tr '\n' ' ' | tail -c 160)
  printf 'LINE %02d rc=%d yaml:%s :: %s\n' "$n" "$rc" "$lineno" "$cmd"
  printf '         tail: %s\n' "$tail160"
done
printf 'TOTAL lines=%d rc0=%d nonzero=%d\n' "$n" "$zero" "$nonzero"
