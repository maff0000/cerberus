# CERBERUS PR #14 live re-audit (R2D2, 2026-10-22)

Drives the PR's REAL `evaluator.pass_once.one_pass_for_both_dials` (git archive of `wo/CERBERUS-WO-1.3b-II-implementation` @ `5864e47`,
unmodified) over a point-in-time rebuild of the WO-1.17 store.  What is ours is only the store view: before the pass for day *d* a scratch raw
store holds exactly the `raw_reading` rows knowable at *d* (availability rule as in `../harness/cerberus_replay.py`).  The pinned store is opened
`mode=ro` and never written.

    R2_SCRATCH=/some/dir ../fetch_inputs.sh /some/dir        # engine@dfd127e (harness), store snapshot, control series
    R2_SCRATCH=/some/dir ./fetch_pr14_inputs.sh              # PR #14 trees, SKEW + DFII10 control, harness link
    R2_SCRATCH=/some/dir ./launch.sh                         # four configurations x 8 episodes (~25 min on 32 cores)
    R2_SCRATCH=/some/dir python3 -I analyse.py               # (from /some/dir/harness)  coverage map, protection, lock, monetary

| configuration | repo | R2_HIST | R2_ACUTE | meaning |
|---|---|---|---|---|
| A_strict_asis | repo_pr14 | none | strict | the real pass on the store AS IT IS |
| B_strict_liveshaped | repo_pr14 | control | strict | + S&P `history` (260 closes) as the LIVE collector stores it, from the control series (equals the store's S&P on all 2,514 days) |
| C_avail_liveshaped | repo_pr14_relaxed | control | available | + hy_oas no longer a REQUIRED input (one flag in indicator-scaling.json) + acute over the masters that scored. **REPLAY-ONLY; shows the decisions the engine would take were every input present** |
| D_avail_asis | repo_pr14_relaxed | none | available | C on the store as-is: shows the lock cannot release without S&P history |

Other scripts: `calls_test.py` (Rogue's four interpretation calls), `unknown_exit_test.py` (outage shortcut), `control_sim*.py` (PR's resolver + lock +
trend over the CONTINUOUS control series, not the store), `combos.py`, `parity.py` (real pass vs the WO-1.3b-II harness), `misc_checks.py`,
`today.py`/`today_replay.py` (read-only copy of the live DEV feed; dated 2026-10-22).  Control-series results are lower bounds: the control has no
hy_oas, ig_oas or copper_gold.
