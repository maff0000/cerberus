#!/usr/bin/env bash
# P-I — THE HISTORIC `__wrapped__` ATTACK SET, RE-RUN AT THE NEW HEAD. BEFORE AND AFTER.
#
# PO-DECISIONS-0013 ruling 2: *"the historic WO-2R `__wrapped__` attack set is re-run at the new
# head. **Whether this reopens WO-2R routes is answered by that re-run, not by argument.**"*
#
# **WHY THESE ROUTES AND NOT AN ARBITRARY SUBSET.** The fifth Assurance seat's M10 established the
# convergence that makes this item load-bearing: *"the layer that closes V03, E04 and V06 is
# `refuse_a_number_without_its_inputs` — the guard whose `__wrapped__` bypass I demonstrated
# live."* So the set below is (i) the `__wrapped__` probe itself, V24, and (ii) **EVERY** route in
# `variants/WO-2R/CD-ASR-F02-F03/` — the corpus whose closure depends on the guard this increment
# just changed. The directory is READ, not the manifest (CD-PL-F97).
#
# BEFORE = a pristine extraction of the base SHA, where `__wrapped__` was LIVE on the guard.
# AFTER  = this working tree, where it is deleted.
# **EACH ARM RUNS ITS OWN TREE'S OWN EVERYTHING** (CD-PL-F98).
#
#   bash variants/WO-2R3/P-I-the-wrapped-attack-set-re-run.sh
#
# Exits 0 whatever it measures. An instrument that reports (CD-RULE-006).

set -u

BASE_SHA=9f7b7640f692442e22a47ecac3d4a643057729d5
HERE=$(git rev-parse --show-toplevel)
WORK=$(mktemp -d /tmp/cd-P-I-XXXXXX)
trap 'rm -rf "$WORK"' EXIT

git -C "$HERE" archive "$BASE_SHA" | tar -x -C "$WORK" --one-top-level=before
mkdir -p "$WORK/after"
git -C "$HERE" ls-files -z --cached --others --exclude-standard \
  | xargs -0 tar -c -C "$HERE" | tar -x -C "$WORK/after"

# The route set, READ FROM THE DIRECTORY.
ROUTES=$(cd "$HERE" && ls variants/WO-2R/CD-ASR-F02-F03/*.patch)
ROUTES="variants/WO-2R3/V24-wrapped-attribute-bypass.patch $ROUTES"

apply_arm() {  # $1 = tree copy dir, $2 = patch path (relative to repo root)
  local how=""
  if git -C "$1" apply -p1 "$HERE/$2" 2>/dev/null; then how="git apply"
  elif git -C "$1" apply -p1 -C1 "$HERE/$2" 2>/dev/null; then how="-C1"
  elif (cd "$1" && patch -p1 --fuzz=5 --silent < "$HERE/$2" >/dev/null 2>&1); then how="patch --fuzz=5"
  else how="DID NOT APPLY"; fi
  printf '%s' "$how"
}

measure() {  # $1 = tree.  What the guard does, and what the instruments say.
  local guard wrapped probe
  wrapped=$(cd "$1" && PYTHONPATH=src python3 -B -c "
import importlib
m = importlib.import_module('crash_detector.engine.evaluate')
print('PRESENT' if hasattr(m._evaluate_dial,'__wrapped__') else 'absent')
" 2>/dev/null) || wrapped="import failed"
  # Does the CD-ASR-F03 post-condition still refuse a starved value-bearing reading?
  guard=$(cd "$1" && PYTHONPATH=src python3 -B -c "
import importlib, datetime as dt
m = importlib.import_module('crash_detector.engine.evaluate')
cfg = importlib.import_module('crash_detector.engine.config')
now = dt.datetime(2026,8,23,tzinfo=dt.timezone.utc)
spec = cfg.DialSpec(dial_id='equity_crash', required_input_ids=('src.a',),
                    contributing_input_ids=(), model_ref='never')
def rewritten(spec, usable, now_utc, *a, **k):
    return m.Value(value=object(), as_of_utc=now_utc, inputs_used=('src.a',))
try:
    m._absence_is_never_a_number(rewritten)(spec, {}, now)
    print('*** ACCEPTED ***')
except Exception as exc:
    print('REFUSED ' + type(exc).__name__)
" 2>/dev/null) || guard="import failed"
  # And the same body reached THROUGH __wrapped__, which is the whole question.
  probe=$(cd "$1" && PYTHONPATH=src python3 -B -c "
import importlib, datetime as dt
m = importlib.import_module('crash_detector.engine.evaluate')
cfg = importlib.import_module('crash_detector.engine.config')
now = dt.datetime(2026,8,23,tzinfo=dt.timezone.utc)
spec = cfg.DialSpec(dial_id='equity_crash', required_input_ids=('src.a',),
                    contributing_input_ids=(), model_ref='never')
def rewritten(spec, usable, now_utc, *a, **k):
    return m.Value(value=object(), as_of_utc=now_utc, inputs_used=('src.a',))
g = m._absence_is_never_a_number(rewritten)
w = getattr(g, '__wrapped__', None)
if w is None:
    print('ROUTE ABSENT')
else:
    try:
        w(spec, {}, now); print('*** ACCEPTED THROUGH __wrapped__ ***')
    except Exception as exc:
        print('refused ' + type(exc).__name__)
" 2>/dev/null) || probe="import failed"
  printf '%-9s | %-22s | %s' "$wrapped" "$guard" "$probe"
}

echo "======================================================================================="
echo " P-I — THE HISTORIC \`__wrapped__\` ATTACK SET, BEFORE AND AFTER"
echo " BEFORE = $BASE_SHA (bypass LIVE)"
echo " AFTER  = $HERE working tree (bypass DELETED)"
echo "======================================================================================="
echo
echo "--- THE GUARD ITSELF, BOTH ARMS. This is the row the ruling is about. ---"
echo
printf '%-8s %-9s | %-22s | %s\n' "arm" "__wrapped__" "through the guard" "through __wrapped__"
printf '%-8s ' "BEFORE"; measure "$WORK/before"; echo
printf '%-8s ' "AFTER "; measure "$WORK/after";  echo
echo

echo "--- EVERY ROUTE, BEFORE AND AFTER. Applies + does the suite still catch it? ---"
echo
printf '%-52s %-16s %-22s %-16s %s\n' "route" "BEFORE applies" "BEFORE result" "AFTER applies" "AFTER result"
for route in $ROUTES; do
  name=$(basename "$route" .patch)
  line=""
  for arm in before after; do
    rm -rf "$WORK/r-$arm"; cp -a "$WORK/$arm" "$WORK/r-$arm"
    how=$(apply_arm "$WORK/r-$arm" "$route")
    if [ "$how" = "DID NOT APPLY" ]; then
      result="—"
    else
      out=$(cd "$WORK/r-$arm" && PYTHONPATH=src timeout 600 python3 -B -m pytest -q -p no:cacheprovider tests/ 2>&1 | tail -3)
      if printf '%s' "$out" | grep -q 'failed'; then
        result=$(printf '%s' "$out" | grep -o '[0-9]* failed[^ ]*' | head -1)
        result="CLOSED ($result)"
      elif printf '%s' "$out" | grep -q 'error'; then
        result="CLOSED (collect error)"
      else
        result="**NOT CAUGHT**"
      fi
    fi
    line="$line|$how|$result"
  done
  IFS='|' read -r _ b_how b_res a_how a_res <<< "$line"
  printf '%-52s %-16s %-22s %-16s %s\n' "$name" "$b_how" "$b_res" "$a_how" "$a_res"
done

echo
echo "======================================================================================="
echo " A route reading CLOSED in BEFORE and CLOSED in AFTER did not reopen."
echo " A route reading CLOSED -> **NOT CAUGHT** IS THE HEADLINE OF THIS INCREMENT."
echo "======================================================================================="
exit 0
