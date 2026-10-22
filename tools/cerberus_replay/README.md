# CERBERUS replay harness (R2D2, WO-1.3b-II)

Point-in-time replay of the crash detector over the WO-1.17 historical store, scored by the **real** engine code
(`crash_detector.engine.statistics`, `evaluator.resolve`) at a pinned SHA. Rebuilt from the WO-1.3b scratchpad tooling
(`replay.py`/`proof.py`, session 8bae9025, never committed) so it can be re-run whenever the backfill changes.

## Run

```bash
/srv/r2d2/tools/cerberus_replay/fetch_inputs.sh            # engine @ SHA, store snapshot, control series -> ./repo ./data ./control
cd /srv/r2d2/tools/cerberus_replay/harness && python3 -I final_run.py   # writes ../out/results.json
```

`CERBERUS_SHA=<sha> fetch_inputs.sh` re-pins the engine. Inputs are gitignored; `out_reference/` holds the 2026-10-22 results
(`results.json` sha256 `a7f5fe22489fd8217adbe2dbd9ea634bfb65c004ea5ffb53dd4212b8aad2e1f4`, reproduced byte-identically from this directory).

## Modules

| file | role |
|---|---|
| `cerberus_replay.py` | store → point-in-time panel (vintage_date availability, 1-day lag on unrevised series, engine staleness windows), engine bands/weights, S&P forward labels |
| `engine_run.py` | per-day statistics via the real engine; parameterised state machine, **proven identical** to `evaluator.resolve.official_state_for_dial` (0 mismatches / 2,507 days). `Params.lock` is an experiment, off by default |
| `metrics.py`, `perm.py`, `protect.py` | label/permission/“share of decline still ahead at first signal” metrics |
| `control.py`, `single_master.py`, `eval_master.py`, `eval_curve.py`, `eval_lock.py` | **continuous public control series (NOT the store)** for vol/curve master base rates, persistence/exit/lock sensitivity |
| `eval_stats.py`, `eval_count.py`, `eval_rising.py` | breadth/count/`acute_rising` evaluation |
| `final_run.py` | four configurations side by side → `out/results.json` |

## Rules the harness holds

* Never writes to the store (opened `mode=ro`). Store snapshot is identified by sha256.
* Missing inputs are excluded from breadth (engine "Degraded"), never scored 0. `strict_unknown=True` reproduces live UNKNOWN propagation.
* Anything computed from the control series is labelled as such in the report; it is not the WO-1.17 store.
* "Calibration mode" (`variants.calib_rows`) lets `volatility_master` use VIX alone where VIX3M does not exist yet. It is replay-only and never used for the as-deployed verdict.
