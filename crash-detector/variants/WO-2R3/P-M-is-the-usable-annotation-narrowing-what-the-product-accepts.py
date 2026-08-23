"""CD-PL-F109 — is `usable: Mapping[str, OK]` -> `dict[str, OK]` a NARROWING of what the
product accepts?  ONE AXIS: a Mapping that is NOT a dict, offered to `_evaluate_dial`.
Run in each tree's own copy; the tree is printed."""
import importlib, os, sys, collections.abc
print("TREE PWD:", os.getcwd())
m = importlib.import_module("crash_detector.engine.evaluate")
from crash_detector.engine.config import DialSpec
from datetime import datetime, timezone

class NotADict(collections.abc.Mapping):
    def __init__(self, inner): self._i = dict(inner)
    def __getitem__(self, k): return self._i[k]
    def __iter__(self): return iter(self._i)
    def __len__(self): return len(self._i)

NOW = datetime(2026, 8, 23, tzinfo=timezone.utc)
spec = DialSpec(dial_id="equity_crash", required_input_ids=(), contributing_input_ids=(), model_ref=None)

for label, usable in (("ARM 1  plain dict  (control)", {}),
                      ("ARM 2  Mapping, not a dict", NotADict({}))):
    try:
        r = m._evaluate_dial(spec, usable, NOW)
        print(f"{label}: ADMITTED -> {type(r).__name__}")
    except Exception as exc:
        print(f"{label}: REFUSED  -> {type(exc).__name__}: {str(exc)[:110]}")
