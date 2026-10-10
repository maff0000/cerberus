# WO-1.2 — Recover the orphaned crash-detector build into CERBERUS

Date: 2026-10-10 · Executor: Rogue (FORGE PL, dispatched by Trinity) · Branch: `wo/CERBERUS-WO-1.2-crash-detector-recovery` (NOT merged; awaiting Auditor pass)

## What landed
- **All 586 commits** of the retired PBGv2 crash-detector repository (19 branches + 1 tag, 2026-08-18 → 2026-08-25), history-preserving, under `crash-detector/`. Verified: every one of the 586 imported SHAs is an ancestor of the WO branch head.
- The dispatch said "342 commits". That is only the archive's `main` branch, which holds governance records and **no source code**. The implementation (`src/`, `tests/`, `db/`, `deploy/`, `plants/`, `variants/`) is on the never-merged `wo-3` branch; importing `main` alone would have recovered the paperwork and lost the code. Both are imported.
- `crash-detector/STATUS.md` — status, design, real-vs-scaffolded, what is needed to finish. `crash-detector/ARCHIVE-COMMIT-MAP.txt` — original → imported SHA.
- Top-level `README.md` updated with a map and the corrected description.

## Mechanism
1. Mirror-cloned the archive (no writes to the archive) → `git filter-repo --to-subdirectory-filter crash-detector` on the clone (rewrites paths in every commit so `git log --follow` works; SHAs change, map kept).
2. On the WO branch (from `main` @ `e9752d5`): `merge --allow-unrelated-histories` of archive `main`; merge of archive `wo-3` (clean, no conflicts); octopus merge of the 12 single-commit Assurance-verdict branches `asr-wo3-03..14`; `-s ours` merge of tag `wo-2-pre-identity-rework` (24 commits found only under the tag — pre-AMBER-rework WO-2 state; tree unchanged).
3. No archive file was edited. `git log --follow crash-detector/PID.md` reaches 2026-08-18; `--follow` on `crash-detector/src/crash_detector/admission.py` shows its WO-2R3 history.

## Security: full-history scan (before any push)
- `gitleaks detect --log-opts="--all"` on the mirror of the archive: **582 commits scanned (rest are empty/merge), no leaks.** Also run on the archive's `main` alone: no leaks.
- Independent regex sweep over every added line in all history (private-key headers, AWS/GitHub/Slack/OpenAI-style tokens, JWTs, credentialed DB/Redis URLs, quoted password/secret/api_key/token assignments): **no hits**.
- Whole-tree + history sweep for internal infrastructure detail: no private IPs or credentials. Residual items, **not secrets**, disclosed for the Auditor/Owner's judgement:
  - **Commit metadata carries the Owner's email addresses** (a work address and a personal one, in author/committer fields of ~200 commits) plus a service-account identity. Public-record-of-authorship, not credentials, but it is now public. Removing it would mean rewriting history; left as-is pending a decision.
  - A handful of mentions of the hostname `dell-debian` and `/srv/...` paths in governance prose, and test fixtures using `postgres.dell.matt.local` / `10.11.12.13` as *negative* examples for a portability check. No addresses of real hosts.
  - The README rule "infrastructure specifics stay out of this repo" is therefore not literally met inside `crash-detector/governance/` history prose. Judged non-sensitive; flagged.
- Final `gitleaks detect --log-opts=HEAD` over the finished WO branch (587 commits scanned, including the CERBERUS history and these docs): **no leaks found**.

## Verification
- `PYTHONPATH=src python3 -m pytest -q tests` on a clean `git archive` of the merged `crash-detector/`: **2,099 passed** (CPython 3.11.2, 70 s, no network).

## Not done / open
- No audit of any code. Contents are recovered, not re-reviewed. The *claims* in the imported governance records are the original authors' and have not been independently re-verified by this WO.
- Nothing deployed; nothing run against live data (the code has no data collectors yet — see STATUS.md §4).
- Tag `wo-2-pre-identity-rework` exists only as merged history; no tag is pushed.
- `refs/archive/*` helper refs created on the dell-debian working clone are local-only and are not pushed.
- Items needing an Owner/Architect decision are in STATUS.md §5 (framework choice, indicator count 24 vs 30, assurance ownership).
