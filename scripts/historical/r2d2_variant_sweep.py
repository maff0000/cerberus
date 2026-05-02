"""
Apollo V5 Variant Sweep — R2D2 tooling for gate-relaxation study.

Runs a strategy against a set of config variants on the same sentinel window.
Each variant mutates attributes on the loaded config object in-memory BEFORE
replay. No DB writes to falcon_strategy_*_config. Zero risk to live Falcon.
"""

import argparse
import json
import logging
import sys
import traceback
from datetime import time as _time


def _coerce(current_value, new_value):
    if isinstance(current_value, _time):
        if isinstance(new_value, str):
            parts = new_value.strip().split(":")
            return _time(int(parts[0]), int(parts[1]))
        if isinstance(new_value, _time):
            return new_value
        raise ValueError("cannot coerce to time")
    if isinstance(current_value, bool):
        if isinstance(new_value, bool):
            return new_value
        if isinstance(new_value, str):
            return new_value.strip().lower() in ("true", "1", "yes")
        return bool(new_value)
    if isinstance(current_value, int) and not isinstance(current_value, bool):
        return int(new_value)
    if isinstance(current_value, float):
        return float(new_value)
    if isinstance(current_value, list):
        if isinstance(new_value, list):
            return new_value
        raise ValueError("cannot coerce to list")
    if isinstance(current_value, str):
        return str(new_value)
    return new_value


def _apply_overrides(config_obj, overrides):
    warnings = []
    for attr, raw_value in overrides.items():
        if not hasattr(config_obj, attr):
            warnings.append("SKIP: config has no attribute " + repr(attr))
            continue
        current = getattr(config_obj, attr)
        try:
            coerced = _coerce(current, raw_value)
        except Exception as e:
            warnings.append("SKIP: coerce failed for " + repr(attr) + ": " + str(e))
            continue
        object.__setattr__(config_obj, attr, coerced)
    return warnings


def _summarize(name, stats, calibration, warnings):
    top = ""
    top3 = []
    if stats.decline_reasons:
        r, c = stats.decline_reasons.most_common(1)[0]
        top = r + " (" + str(c) + ")"
        for r, c in stats.decline_reasons.most_common(3):
            top3.append({"reason": r, "count": c})

    buckets = {}
    for conf, b in calibration.buckets.items():
        buckets[int(conf)] = {
            "count": b.count,
            "win_pct": round(b.win_rate * 100, 1),
            "avg_r": round(b.avg_r, 3),
        }

    return {
        "variant": name,
        "cycles": stats.total_cycles,
        "proposals": stats.total_proposals,
        "declines": stats.total_declines,
        "errors": stats.total_errors,
        "ambiguous": calibration.total_ambiguous,
        "no_data": calibration.total_no_data,
        "grade": calibration.grade,
        "top_decline": top,
        "top3_declines": top3,
        "calibration_buckets": buckets,
        "override_warnings": warnings,
    }


def main(argv=None):
    from tradingProteus.apollov5 import __version__
    from tradingProteus.apollov5.config import hermes_target
    from tradingProteus.apollov5.data_loader import load_slice
    from tradingProteus.apollov5.calibration import finalize
    from tradingProteus.apollov5.replay_loop import run_replay
    from tradingProteus.apollov5.run import _build_ctx
    from tradingProteus.apollov5.strategy_registry import load_strategy

    parser = argparse.ArgumentParser(prog="apollov5.variant_sweep")
    parser.add_argument("--strategy", required=True)
    parser.add_argument("--instrument", required=True)
    parser.add_argument("--mode", default="NORMAL")
    parser.add_argument("--from", dest="date_start", required=True)
    parser.add_argument("--to", dest="date_end", required=True)
    parser.add_argument("--timeout-bars", type=int, default=240)
    parser.add_argument("--variants-json", required=True)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.WARNING if not args.verbose else logging.INFO, stream=sys.stderr)

    with open(args.variants_json) as f:
        variants = json.load(f)

    sys.stderr.write("Apollo V5 " + __version__ + " variant_sweep — " + args.strategy + " " + args.instrument + " " + args.date_start + "→" + args.date_end + " | " + str(len(variants)) + " variants\n")

    hermes = hermes_target()
    slc = load_slice(hermes, args.instrument, args.date_start, args.date_end)
    sys.stderr.write("  slice: m5=" + str(len(slc.m5_signals)) + " m15=" + str(len(slc.m15_signals)) + " m1=" + str(len(slc.m1_candles)) + "\n")

    ctx = _build_ctx(verbose=args.verbose)
    results = []

    for variant in variants:
        name = variant.get("name", "unnamed")
        overrides = variant.get("overrides", {})
        worker, config, _snapshot = load_strategy(args.strategy, args.instrument, args.mode)
        warnings = _apply_overrides(config, overrides)

        try:
            stats = run_replay(
                worker=worker, worker_config=config, ctx=ctx,
                slc=slc, mode=args.mode,
                outcome_timeout_m1_bars=args.timeout_bars,
            )
            calibration = finalize(stats.calibration)
            stats.calibration = calibration
            row = _summarize(name, stats, calibration, warnings)
        except Exception as e:
            row = {
                "variant": name,
                "error": type(e).__name__ + ": " + str(e),
                "traceback": traceback.format_exc()[-500:],
                "override_warnings": warnings,
            }

        results.append(row)
        if "error" in row:
            sys.stderr.write("  " + name.ljust(22) + "  ERROR: " + row["error"][:80] + "\n")
        else:
            sys.stderr.write(
                "  " + name.ljust(22)
                + "  cycles=" + str(row["cycles"]).rjust(4)
                + " proposals=" + str(row["proposals"]).rjust(3)
                + " declines=" + str(row["declines"]).rjust(4)
                + " grade=" + row["grade"].ljust(20)
                + " top=" + row["top_decline"][:40] + "\n"
            )
        for w in warnings:
            sys.stderr.write("    [warn] " + w + "\n")

    print()
    print("===R2D2_VARIANT_SWEEP_JSON_START===")
    print(json.dumps({
        "strategy": args.strategy,
        "instrument": args.instrument,
        "mode": args.mode,
        "date_range": [args.date_start, args.date_end],
        "variants": results,
    }, indent=2))
    print("===R2D2_VARIANT_SWEEP_JSON_END===")

    return 0


if __name__ == "__main__":
    sys.exit(main())
