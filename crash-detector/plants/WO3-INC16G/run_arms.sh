#!/usr/bin/env bash
# WO-3 INCREMENT 16G — one PRISTINE extraction per arm. Written and run by CD-ENG-WO3-15.
#
#   usage: run_arms.sh <sha> [repo]
#
# It is the same method as `plants/WO3-INC16F/run_arms.sh`, and it is carried here so this
# plant set is self-contained for an auditor who extracts only this directory's tree. The two
# method traps earlier seats disclosed against their own work are both refused here:
#
#  1. `CD-ASR-WO3-11` read each patch FROM INSIDE the extracted tree, where it did not exist at
#     the older tip; `git apply` returned 128 and the instrument then ran on an UNPATCHED tree.
#     Here every patch is read from an ABSOLUTE path OUTSIDE every extraction, `git apply`'s rc
#     is TAKEN INTO A VARIABLE AND CHECKED, and a non-zero rc ABORTS THE ARM LOUDLY.
#  2. An instrument that hard-codes a path measures THE LANE whichever tree it is pointed at.
#     Here the tree is `--root`ed explicitly and printed on every line.
#
# *** WHICH INSTRUMENT RUNS IS AN ARGUMENT, NOT AN ASSUMPTION. *** `INSTRUMENTS` selects the
# tree the two checkers are read FROM, so the SAME arms can be run against the BEFORE
# instrument (a pristine extraction of the base) and the AFTER instrument (the lane). That is
# how this set shows `CD-CHOKE-003` MOVES on `Z5`: not by asserting it, by running both.
#
# rc is TAKEN FROM THE COMMAND, never from a pipe (`CD-ENG-F02`'s defect class).
set -u
SHA="$1"
REPO="${2:-$(cd "$(dirname "$0")/../.." && pwd)}"
PLANTS="$REPO/plants/WO3-INC16G"
INSTRUMENTS="${INSTRUMENTS:-$REPO}"
OUT="${OUT:-/tmp/wo3-inc16g-arms}"
mkdir -p "$OUT"
echo "### arms of $SHA · instruments from $INSTRUMENTS · out $OUT"

run_one() {
  local label="$1" patch="$2"
  local tree="$OUT/$label/tree"
  rm -rf "$OUT/$label"; mkdir -p "$tree"
  ( cd "$REPO" && git archive "$SHA" ) | tar -x -C "$tree"
  local rc=$?
  if [ "$rc" -ne 0 ]; then echo "ARM $label ABORTED: git archive rc=$rc"; return 90; fi
  if [ -n "$patch" ]; then
    case "$patch" in /*) ;; *) echo "ARM $label ABORTED: '$patch' is not an absolute path"; return 91;; esac
    ( cd "$tree" && git apply --unsafe-paths -p1 "$patch" )
    rc=$?
    if [ "$rc" -ne 0 ]; then echo "ARM $label ABORTED: git apply rc=$rc  patch=$patch"; return 92; fi
    # *** THE ARM IS PROVED PRESENT IN THE TREE, NOT ASSUMED PRESENT. ***
    grep -c "^ *# $label:" "$tree/src/crash_detector/publication/envelope_contract.py" \
      > "$OUT/$label/marker.txt" 2>&1
    local marker; marker=$(cat "$OUT/$label/marker.txt")
    if [ "$marker" -lt 1 ]; then echo "ARM $label ABORTED: marker not found after apply"; return 93; fi
    echo "ARM $label: git apply rc=$rc, marker lines=$marker"
  else
    echo "ARM $label: CLEAN, no patch"
  fi
  python3 -B "$INSTRUMENTS/tools/register/check_publication_chokepoint.py" --root "$tree" \
      > "$OUT/$label/choke.txt" 2>&1; local c=$?
  python3 -B "$INSTRUMENTS/tools/register/check_stale_data_never_calm.py" --root "$tree" \
      > "$OUT/$label/stale.txt" 2>&1; local s=$?
  printf 'ARM %-7s chokepoint-row rc=%-3d %-58s | stale-row rc=%d %s\n' \
      "$label" "$c" "$(tail -1 "$OUT/$label/choke.txt" | cut -c1-58)" \
      "$s" "$(tail -1 "$OUT/$label/stale.txt" | grep -o '[A-Z]* — .*' | cut -c1-40)"
}

run_one CLEAN ""
for patch in "$PLANTS"/*.patch; do
  label="$(basename "$patch")"; label="${label%%-*}"
  run_one "$label" "$patch"
done
echo "arms under $OUT"
