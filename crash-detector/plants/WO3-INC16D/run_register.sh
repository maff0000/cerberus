#!/usr/bin/env bash
# CD-ENG-WO3-12 — run all 30 `execute:` lines of required-tests.yaml IN the given tree.
# rc is TAKEN FROM THE COMMAND, never from a pipe (CD-ENG-F02's defect class).
# usage: run_register.sh <tree>
set -u
TREE="$1"
cd "$TREE" || exit 99
n=0
zero=0
nonzero=0
mapfile -t LINES < <(grep -nE '^[[:space:]]*execute:[[:space:]]*\S' required-tests.yaml)
for entry in "${LINES[@]}"; do
  lineno="${entry%%:*}"
  cmd="${entry#*execute:}"
  cmd="${cmd# }"
  n=$((n+1))
  out=$(eval "$cmd" 2>&1)
  rc=$?          # RC FROM THE COMMAND
  if [ "$rc" -eq 0 ]; then zero=$((zero+1)); else nonzero=$((nonzero+1)); fi
  tail160=$(printf '%s' "$out" | tr '\n' ' ' | tail -c 160)
  printf 'LINE %02d rc=%d yaml:%s :: %s\n' "$n" "$rc" "$lineno" "$cmd"
  printf '         tail: %s\n' "$tail160"
done
printf 'TOTAL lines=%d rc0=%d nonzero=%d\n' "$n" "$zero" "$nonzero"
