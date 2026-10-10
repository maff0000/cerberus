#!/usr/bin/env bash
# WO-3 INCREMENT 16E — run EVERY `execute:` line of required-tests.yaml IN the given tree.
# Written and run by CD-ENG-WO3-13.
#
# *** THIS IS THE ACCEPTANCE TEST OF THE INCREMENT. *** At 0e80a09 the per-line rc list on the
# D1 tree was `diff`-IDENTICAL to the clean tip — TOTAL lines=30 rc0=19 nonzero=11 on both, NOT
# ONE ROW MOVED. That is A312-F1. The whole of 16E is: run this on a clean extraction of the new
# tip and on a D1 extraction of the same tip, `diff` the two per-line lists, AND THE DIFF MUST
# NO LONGER BE EMPTY.
#
# rc is TAKEN FROM THE COMMAND, never from a pipe (CD-ENG-F02's defect class).
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
