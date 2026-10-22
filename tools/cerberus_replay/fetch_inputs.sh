#!/usr/bin/env bash
# Rebuild the inputs the CERBERUS replay harness reads.  Usage: fetch_inputs.sh [ROOT]   (default: this directory)
# Layout produced:  ROOT/repo/crash-detector  (engine @ pinned SHA)   ROOT/data/wo117.sqlite  (store snapshot)
#                   ROOT/control/*            (continuous public series; NOT the store)
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "$0")" && pwd)}"
SHA="${CERBERUS_SHA:-dfd127e}"                    # WO-1.17 branch head the WO-1.3b-II verdict was run against
mkdir -p "$ROOT/repo" "$ROOT/data" "$ROOT/control"
ssh root@192.168.11.10 "cd /srv/cerberus-worktrees/wo-1.17 && git archive $SHA crash-detector" | tar -x -C "$ROOT/repo"
ssh root@192.168.11.10 'python3 -c "
import sqlite3
s=sqlite3.connect(\"file:/srv/cerberus/wo117-data/wo117_historical.sqlite?mode=ro\",uri=True); d=sqlite3.connect(\"/tmp/r2_snap.sqlite\"); s.backup(d); d.close()"'
scp -q root@192.168.11.10:/tmp/r2_snap.sqlite "$ROOT/data/wo117.sqlite"
for s in "%5EGSPC:gspc" "%5EVIX:vix" "%5EVIX3M:vix3m"; do
  curl -s -m 60 -A "Mozilla/5.0" "https://query1.finance.yahoo.com/v8/finance/chart/${s%%:*}?period1=0&period2=2000000000&interval=1d" -o "$ROOT/control/${s##*:}.json"
done
for s in T10Y3M T10Y2Y BAA10Y; do
  curl -s -m 60 "https://fred.stlouisfed.org/graph/fredgraph.csv?id=$s&cosd=1982-01-01" -o "$ROOT/control/$s.csv"
done
sha256sum "$ROOT/data/wo117.sqlite" "$ROOT"/control/*
