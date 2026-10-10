#!/usr/bin/env bash
# WO-3 INCREMENT 16F — one PRISTINE extraction per arm, for the whole plant set.
# Written and run by CD-ENG-WO3-14.
#
#   usage: run_arms.sh <sha> [repo]
#
# *** THE TWO METHOD TRAPS THIS SET EXISTS NOT TO FALL INTO, BOTH DISCLOSED BY EARLIER SEATS
# AGAINST THEIR OWN WORK: ***
#
#  1. `CD-ASR-WO3-11` read each patch FROM INSIDE the extracted tree, where it did not exist at
#     the older tip; `git apply` returned 128 and the instrument then ran on an UNPATCHED tree —
#     measuring nothing while looking like a result. Here every patch is read from an ABSOLUTE
#     path outside every extraction, `git apply`'s rc is TAKEN INTO A VARIABLE AND CHECKED, and
#     a non-zero rc ABORTS THE ARM LOUDLY.
#  2. `plants/WO3-INC16D/probe_16d.py` HARD-CODES a `sys.path.insert` to the lane and therefore
#     measures THE LANE whichever tree it is pointed at. `eng14_probe.py` takes the tree as
#     `argv[1]` and prints the resolved `crash_detector.__file__` on its last line.
#
# Each arm runs, IN ITS OWN TREE:
#   · the behavioural row   `tools/register/check_stale_data_never_calm.py --root <tree>`
#   · the structural row    `tools/register/check_publication_chokepoint.py --root <tree>`
#   · this seat's live-gate probe, 24 rows, both surfaces
# The FULL per-line register rc list is taken separately by `run_register.sh <tree>`, so that
# the expensive whole-register pass can be run on the arms that need it.
set -u
SHA="$1"
REPO="${2:-$(cd "$(dirname "$0")/../.." && pwd)}"
PLANTS="$REPO/plants/WO3-INC16F"
OUT="${OUT:-/tmp/wo3-inc16f-arms}"
mkdir -p "$OUT"

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
    echo "ARM $label: git apply rc=$rc  patch=$patch"
    if [ "$rc" -ne 0 ]; then echo "ARM $label ABORTED: git apply rc=$rc"; return 92; fi
  else
    echo "ARM $label: CLEAN, no patch"
  fi
  python3 -B "$REPO/tools/register/check_stale_data_never_calm.py" --root "$tree" \
      > "$OUT/$label/stale.txt" 2>&1; local s=$?
  python3 -B "$REPO/tools/register/check_publication_chokepoint.py" --root "$tree" \
      > "$OUT/$label/choke.txt" 2>&1; local c=$?
  python3 -B "$PLANTS/eng14_probe.py" "$tree" > "$OUT/$label/probe.txt" 2>&1
  printf 'ARM %-6s stale-row rc=%d  chokepoint-row rc=%d  %s\n' \
      "$label" "$s" "$c" "$(grep 'STALE-CALM ADMISSIONS' "$OUT/$label/probe.txt")"
}

run_one CLEAN ""
for patch in "$PLANTS"/*.patch; do
  label="$(basename "$patch")"; label="${label%%-*}"
  run_one "$label" "$patch"
done
echo "arms under $OUT"
