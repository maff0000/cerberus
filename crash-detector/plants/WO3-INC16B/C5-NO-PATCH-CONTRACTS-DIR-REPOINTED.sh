#!/bin/sh
# =========================================================================================
# C5 — A ROUTE BY WHICH THE LIVE GATE ADMITS A CALM `UNKNOWN` DIAL WITH BOTH REPOSITORY
#      SCHEMAS FULLY INTACT.
#
# *** THIS ARM HAS NO PATCH, AND THAT IS THE ENTIRE POINT. *** C1-C4 change the tree. This one
# changes nothing in the tree at all: the repository's two contracts are BYTE-IDENTICAL to the
# blobs recorded in the commit, before and after, and the gate still admits the document PID
# §3.2 forbids. `envelope_contract.contracts_dir()` honours `$CD_CONTRACTS_DIR`, so the
# contract the gate JUDGES AGAINST is a deployment-time input, not a repository fact.
#
# Written by `CD-ENG-WO3-05` at WO-3 increment 16B under
# `governance/engineering/CD-DISPATCH-INC16B-ENGINEER.md` §4 D4.
#
# NOTHING IN THIS DIRECTORY IS EVIDENCE AND NOTHING IN IT IS ASSURANCE.
# NOTHING HERE IS EVER RUN AGAINST THE WORKTREE (`CD-PL-F154`). Run it against a throwaway
# extraction you made yourself:
#
#     mkdir -p /tmp/c5 && git archive <tip> | tar -x -C /tmp/c5 && cd /tmp/c5
#     sh plants/WO3-INC16B/C5-NO-PATCH-CONTRACTS-DIR-REPOINTED.sh
#
# WHAT IT SHOWS, AND WHAT IT DOES NOT. It shows the route is real and executable. It does NOT
# show a defect in `16A-FIX`, which narrowed the documents correctly. It shows that narrowing
# the documents is not the same act as guaranteeing the running gate reads them — which is
# DECLARED LIMIT 1 of `CD-RT-001-MISSING-DATA-NEVER-CALM`, stated there rather than left to be
# discovered. The instrument REFUSES TO RUN (exit 3) when it is pointed this way. IT DOES NOT
# PREVENT THE ROUTE, and no other artefact in this repository does either:
# **NOT PROVED TO BE CARRIED ANYWHERE.**
# =========================================================================================
set -u

WIDENED="${TMPDIR:-/tmp}/c5-widened-contracts"
rm -rf "$WIDENED"; mkdir -p "$WIDENED"
cp contracts/public_envelope.schema.json contracts/private_envelope.schema.json "$WIDENED/"

python3 - "$WIDENED" <<'PY'
import json, sys
widened = sys.argv[1]
for surface in ("public", "private"):
    path = f"{widened}/{surface}_envelope.schema.json"
    schema = json.load(open(path))
    # The ONLY edit, and it is made to the COPY: the UNKNOWN branch's detail_level goes back
    # to the full vocabulary. The repository's own file is not opened for writing anywhere.
    schema["$defs"]["dial_reading_unknown"]["properties"]["detail_level"] = {
        "$ref": "#/$defs/detail_level"
    }
    json.dump(schema, open(path, "w"), indent=2)
print(f"widened COPY written to {widened}; no repository file was touched")
PY

echo "--- the repository's contracts, as blob ids (compare with git rev-parse <tip>:<path>):"
git hash-object contracts/public_envelope.schema.json contracts/private_envelope.schema.json \
  2>/dev/null || echo "    (no git here — compare sha256sum against the tip's blobs)"

echo "--- THE LIVE GATE, WITH \$CD_CONTRACTS_DIR POINTED AT THE WIDENED COPY:"
CD_CONTRACTS_DIR="$WIDENED" PYTHONPATH=src python3 - <<'PY'
from crash_detector.publication.envelope_contract import (
    ENVELOPE_SCHEMA_VERSION, EnvelopeSurface, PublicationRefused,
    contracts_dir, refuse_unless_publishable)
print("    gate resolves its contracts to:", contracts_dir())
unknown_calm = {
    "state": "UNKNOWN", "reason": "NO_SOURCE_REGISTERED",
    "since_utc": "2026-08-23T12:00:00Z", "missing_inputs": [], "detail_level": "calm",
}
for surface in EnvelopeSurface:
    envelope = {
        "schema_version": ENVELOPE_SCHEMA_VERSION,
        "as_of_utc": "2026-08-23T12:00:00Z", "published_utc": "2026-08-23T12:00:05Z",
        "regime": "CALM", "staleness_window_seconds": 600.0,
        "inputs_used": [], "degraded_inputs": [],
        "config_snapshot_id": "SYNTHETIC-C5-ARM-NOT-A-CONFIG",
        "equity_crash": dict(unknown_calm), "monetary_debasement": dict(unknown_calm),
    }
    if surface is EnvelopeSurface.PRIVATE:
        envelope["classification"] = "PRIVATE"
    try:
        refuse_unless_publishable(envelope, surface=surface)
        print(f"    {surface.value}: *** ADMITTED a calm UNKNOWN dial ***")
    except PublicationRefused as refused:
        print(f"    {surface.value}: REFUSED {refused.reason_class}")
PY

echo "--- THE INSTRUMENT, IN THAT SAME ENVIRONMENT (expect exit 3, PRECONDITION_NOT_MET):"
CD_CONTRACTS_DIR="$WIDENED" python3 tools/register/check_missing_data_never_calm.py --root .
echo "    exit=$?"

echo "--- THE INSTRUMENT, SAME TREE, VARIABLE UNSET (expect exit 0):"
python3 tools/register/check_missing_data_never_calm.py --root . >/dev/null 2>&1
echo "    exit=$?"
