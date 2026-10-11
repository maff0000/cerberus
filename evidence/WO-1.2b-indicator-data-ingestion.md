# WO-1.2b — Real data ingestion: close-out evidence

- Audited commit: 44052b88438a512eed01e793fd13f6f060623a06 (fresh Forge Auditor, isolated worktree, zero inherited context, 2026-10-11).
- Verdict: **AMBER, no RED.** Claims reproduced: 2129 tests pass; collector computes nothing; `src/` opens no sockets; live run 27/27 sources OK; classification 17 LIVE / 7 DERIVED / 1 PARTIAL / 5 NOT_TRACTABLE; egress = the 4 registered hosts; gitleaks clean (tree + 593 commits).
- Findings and disposition:
  1. A failing latest fetch did not surface (in-window stale data read LIVE) — **FIXED**: report state `FEED_FAILING`; test added.
  2. Yahoo partial intraday bar could be locked in as the close — **FIXED**: bars dated today are dropped; test added.
  3. STATUS wording "17 produce a real number" overclaimed — **FIXED**.
  4. PyYAML undeclared — **FIXED** (requirements.txt; lock not regenerated).
  5. Ingestion not wired into containers — noted, addressed by later WOs.
  6. Point-in-time/revision handling (first print never replaced) — noted, not fixed.
- After reconciliation: 2131 tests pass.
