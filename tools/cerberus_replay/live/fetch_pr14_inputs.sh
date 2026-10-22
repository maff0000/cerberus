#!/usr/bin/env bash
# Lay out R2_SCRATCH for the PR #14 live re-audit.  Usage: R2_SCRATCH=/some/dir fetch_pr14_inputs.sh
# Needs ../fetch_inputs.sh run first against the same directory (creates data/wo117.sqlite and control/{gspc,vix,vix3m}.json, T10Y*.csv),
# then this adds:  repo_pr14/ (PR #14 @ 5864e47), repo_pr14_relaxed/ (same + hy_oas "required": false, REPLAY-ONLY),
#                  control/SKEW.csv, control/DFII10.csv,  harness -> ../harness
set -euo pipefail
R="${R2_SCRATCH:?set R2_SCRATCH}"
SHA="${PR14_SHA:-5864e47}"
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$R/repo_pr14" "$R/control" "$R/live"
ssh root@192.168.11.10 "cd /srv/cerberus-worktrees/wo-1.3b-ii && git archive $SHA crash-detector" | tar -x -C "$R/repo_pr14"
rm -rf "$R/repo_pr14_relaxed"; cp -a "$R/repo_pr14" "$R/repo_pr14_relaxed"
python3 - "$R/repo_pr14_relaxed/crash-detector/deploy/indicator-scaling.json" <<'PY'
import sys,re
p=sys.argv[1]; s=open(p).read()
n=re.sub(r'("hy_oas":\s*\{[^}]*"required":\s*)true', r'\1false', s, count=1)
assert n!=s; open(p,"w").write(n)
PY
curl -sSL -m 60 "https://cdn-api.cboe.com/api/global/us_indices/daily_prices/SKEW_History.csv" -o "$R/control/SKEW.csv"
curl -sSL -m 60 "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFII10" -o "$R/control/DFII10.csv"
ln -sfn "$HERE/../harness" "$R/harness"
cp -f "$HERE"/*.py "$HERE"/launch.sh "$R/live/"
sha256sum "$R/repo_pr14/crash-detector/deploy/indicator-scaling.json" "$R/repo_pr14_relaxed/crash-detector/deploy/indicator-scaling.json" "$R"/control/SKEW.csv "$R"/control/DFII10.csv
