#!/usr/bin/env python3
import re

path = "/srv-dev/worktrees/r2d2-apollov5-study/tradingProteus/apollov5/strategy_registry.py"
with open(path) as f:
    content = f.read()

new_entries = """
    "ny_thrust_m5": StrategySpec(
        plugin_id="ny_thrust_m5",
        worker_import="falcon.strategies.ny_thrust.worker",
        worker_class="NyThrustWorker",
        config_import="falcon.strategies.ny_thrust.config",
        config_loader="load_ny_thrust_config_from_db",
    ),
    "exhaustion_reversal_m5": StrategySpec(
        plugin_id="exhaustion_reversal_m5",
        worker_import="falcon.strategies.exhaustion_reversal.worker",
        worker_class="ExhaustionReversalWorker",
        config_import="falcon.strategies.exhaustion_reversal.config",
        config_loader="load_exhaustion_reversal_config_from_db",
    ),
    "fib_rejection_m15": StrategySpec(
        plugin_id="fib_rejection_m15",
        worker_import="falcon.strategies.fib_rejection.worker",
        worker_class="FibRejectionWorker",
        config_import="falcon.strategies.fib_rejection.config",
        config_loader="load_fib_rejection_config_from_db",
    ),
    "sweep_reclaim_m5": StrategySpec(
        plugin_id="sweep_reclaim_m5",
        worker_import="falcon.strategies.sweep_reclaim.worker",
        worker_class="SweepReclaimWorker",
        config_import="falcon.strategies.sweep_reclaim.config",
        config_loader="load_sweep_reclaim_config_from_db",
    ),
    "sweep_reclaim_m15": StrategySpec(
        plugin_id="sweep_reclaim_m15",
        worker_import="falcon.strategies.sweep_reclaim.worker",
        worker_class="SweepReclaimM15Worker",
        config_import="falcon.strategies.sweep_reclaim.config",
        config_loader="load_sweep_reclaim_config_from_db",
    ),
"""

m = re.search(r"REGISTRY = \{.*?\n\}", content, re.DOTALL)
assert m, "Cannot find REGISTRY dict"
registry_block = m.group(0)
new_block = registry_block[:-2] + new_entries + "}"
content = content.replace(registry_block, new_block)

with open(path, "w") as f:
    f.write(content)
print("Patched registry with 5 new plugins")

import subprocess
r = subprocess.run(["grep", "-oE", 'plugin_id="[^"]+"', path], capture_output=True, text=True)
lines = sorted(set(r.stdout.splitlines()))
print(f"Total plugins now: {len(lines)}")
for l in lines:
    print("  " + l)
