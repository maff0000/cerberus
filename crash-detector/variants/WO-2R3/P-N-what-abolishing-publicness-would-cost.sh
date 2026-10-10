#!/usr/bin/env bash
# P-N — WHAT ABOLISHING PUBLICNESS ALTOGETHER WOULD COST THE DOORS CRITERION.
#
# `PO-DECISIONS-0015` ruling 1: "membership moves on REAL PUBLIC BINDINGS AND MEASURED REACH,
# never on an underscore." The narrow reading (a callable that RETURNS A JUDGEMENT VALUE is a
# subject whatever it is spelled) is what WO-2R3 increment 8 implemented. The WIDE reading —
# abolish publicness entirely, because the underscore prevents no reach in Python — is a
# PRODUCT-MEANING boundary (PBG-AUTH-005) and was RAISED rather than taken.
#
# THIS PROBE MEASURES WHAT THE WIDE READING WOULD COST, so the Product Owner rules on a number
# rather than on an adjective. It REPORTS; it is not a carrier (CD-RULE-006) and exits 0.
#
# EACH ARM RUNS ITS OWN TREE'S OWN COPY OF THE INSTRUMENT AND PRINTS THE TREE (CD-PL-F98).
set -u
BASE_SHA="${1:-314592c6c397b4e1f2f03ca84488ce800840ad09}"
LANE="${2:-/srv/crash-detector-wo2r3}"
WORK="$(mktemp -d /tmp/p-n-publicness-XXXXXX)"

for ARM in shipped abolished; do
  DEST="$WORK/$ARM"
  mkdir -p "$DEST"
  ( cd "$LANE" && git archive "$BASE_SHA" ) | tar -x -C "$DEST"
  if [ "$ARM" = abolished ]; then
    python3 - "$DEST" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]) / "tools/register/check_judgement_path_doors.py"
s = p.read_text()
old = '    return not name.startswith("_")\n'
assert s.count(old) == 1, "the publicness test moved; this probe measures nothing"
p.write_text(s.replace(old, '    return True  # PROBE: publicness abolished entirely\n'))
PY
  fi
  echo "=================================================================="
  echo "ARM        : $ARM"
  ( cd "$DEST" && echo "TREE PWD   : $(pwd)" \
      && python3 -B tools/register/check_judgement_path_doors.py --root . 2>&1 \
         | grep -E "SUBJECTS ENUMERATED|EXEMPT:|: (PASS|FAIL) —" )
done
echo "=================================================================="
echo "THIS PROBE STATES NO CONCLUSION. The numbers are in the seat's return and in the"
echo "Build Log, where they can be argued with."
rm -rf "$WORK"
exit 0
