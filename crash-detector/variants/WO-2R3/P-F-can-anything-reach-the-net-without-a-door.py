"""P-F — THE REQUIRED IN-PROCESS REACHABILITY MEASUREMENT OF ``_evaluate_dial``.

PO-DECISIONS-0012 ruling 4, made a REQUIRED acceptance item by PO-DECISIONS-0013 ruling 1.
The question, verbatim from the ruling:

    *"can anything in-process reach ``_evaluate_dial`` without passing an established door,
    short of arbitrary code execution (outside the settled threat model)? Does the net's
    post-condition bind everything its open arity admits?"*

**TWO HALVES, SEPARATELY ANSWERED, EITHER CAN FALL ON ITS OWN.** This probe MEASURES. It
does not rule (PBG-AUTH-003) and it does not argue: every row below is a live call whose
outcome is printed, including the rows that fail to construct the reach.

RUN IT AGAINST A TREE, NOT AGAINST AN IDEA (CD-PL-F98)::

    PYTHONPATH=<tree>/src python3 -B variants/WO-2R3/P-F-can-anything-reach-the-net-without-a-door.py

The first line of output is the ``tree:`` provenance of the module actually imported. A
contrast run with the wrong tree on ``sys.path`` is indistinguishable from a fix that does
nothing, and this project has already been bitten by exactly that.

VOCABULARY, so the rows are readable:

* **THE NET** is the object bound to the module-level name ``_evaluate_dial`` after
  decoration — i.e. ``guarded``, the ``_absence_is_never_a_number`` wrapper. Calling it
  runs the post-condition.
* **THE INNER** is the undecorated ``_evaluate_dial`` function. Calling it does NOT run the
  post-condition. Reaching the inner is a bypass of the net; reaching the net is not.
* **AN ESTABLISHED DOOR** is a callable carrying ``@admits(...)`` that binds and refuses its
  arguments BEFORE the body it guards runs.
"""

from __future__ import annotations

import datetime as _dt
import sys
import traceback

RESULTS: list[tuple[str, str, str]] = []


def row(arm: str, question: str, answer: str) -> None:
    RESULTS.append((arm, question, answer))
    print(f"  {arm:<6} {answer}")


def _short(exc: BaseException) -> str:
    return f"{type(exc).__module__}.{type(exc).__name__}: {str(exc).splitlines()[0][:150]}"


def main() -> int:
    import importlib

    # NOT `import crash_detector.engine.evaluate as ev`: `crash_detector.engine.__init__`
    # re-exports the FUNCTION `evaluate`, which shadows the submodule attribute of the same
    # name. That binding silently hands back a function, and a probe that then reads
    # `ev.__file__` gets an AttributeError rather than a wrong answer — this time. Resolve
    # the module explicitly so the `tree:` line is the module's own (CD-PL-F98).
    ev = importlib.import_module("crash_detector.engine.evaluate")
    from crash_detector.engine.config import DialSpec
    from crash_detector.engine.model import MappingKind, ModelProvenance, ModelSpec
    from crash_detector.observations import OK

    print(f"tree: {ev.__file__}")
    print(f"python: {sys.version.split()[0]}")
    print()

    net = ev._evaluate_dial
    now = _dt.datetime(2026, 8, 23, tzinfo=_dt.timezone.utc)

    # A spec whose required inputs ARE all present and which NAMES a model. The
    # post-condition's premise (`required_inputs_are_all_present`) is TRUE for this pair,
    # so the post-condition will NOT refuse whatever the body returns.
    spec_satisfied = DialSpec(
        dial_id="equity_crash",
        required_input_ids=("src.a",),
        contributing_input_ids=(),
        model_ref="a-model-the-registry-never-resolved",
    )
    usable_satisfied = {"src.a": OK(payload={"n": 1}, source_as_of_utc=now)}

    # A spec whose required inputs are NOT present. The post-condition's premise is FALSE,
    # so a value-bearing reading here MUST be refused.
    spec_starved = DialSpec(
        dial_id="equity_crash",
        required_input_ids=("src.a",),
        contributing_input_ids=(),
        model_ref="a-model-the-registry-never-resolved",
    )
    usable_starved: dict = {}

    # ============================================================================ #
    print("HALF (a) — CAN ANYTHING IN-PROCESS REACH IT WITHOUT PASSING AN ESTABLISHED DOOR?")
    print()
    print("  A0 is the COUNTERFACTUAL ARM (CD-D-079): the route the ruling says is the only one.")
    # ---------------------------------------------------------------- A0
    try:
        ev.evaluate(
            observations=[],
            config_snapshot=_DuckConfig(),  # type: ignore[arg-type]
            now_utc=now,
        )
        row("A0", "public door `evaluate` with a duck config", "NOT REFUSED  <- the door did not establish")
    except Exception as exc:  # noqa: BLE001
        row("A0", "public door `evaluate` with a duck config", f"REFUSED at the door -> {_short(exc)}")

    # ---------------------------------------------------------------- A1
    try:
        obtained = getattr(ev, "_evaluate_dial")
        row("A1", "getattr(module, '_evaluate_dial')", f"OBTAINED -> {obtained!r}"[:160])
    except Exception as exc:  # noqa: BLE001
        row("A1", "getattr", f"FAILED -> {_short(exc)}")

    # ---------------------------------------------------------------- A2
    try:
        exec("from crash_detector.engine.evaluate import _evaluate_dial", {})
        row("A2", "`from ... import _evaluate_dial` (the 'never importable' claim)", "IMPORTED — the private name IS importable")
    except Exception as exc:  # noqa: BLE001
        row("A2", "from-import of the private name", f"REFUSED -> {_short(exc)}")

    # ---------------------------------------------------------------- A3
    # CALL the net with an argument NO door established: a duck spec. The question is not
    # only WHETHER something refuses but WHEN — a refusal that arrives after the body has
    # already run is not a door, and the difference is the whole of §D.1 ("established AT
    # THE DOOR ... so an edit to this body cannot remove them").
    #
    # The duck RECORDS every attribute the body reads off it. If that list is non-empty at
    # the moment of refusal, the body ran with an unestablished operand.
    touched: list[str] = []

    class _DuckSpec:
        def __getattr__(self, name):  # a duck answers anything, and remembers being asked
            touched.append(name)
            if name == "required_input_ids":
                return ()
            if name == "dial_id":
                return "equity_crash"
            return None

    try:
        reading = net(_DuckSpec(), {}, now)
        row(
            "A3",
            "call the NET with a duck spec no door established",
            f"BODY RAN AND RETURNED {type(reading).__name__} — NOTHING REFUSED AT ALL",
        )
    except Exception as exc:  # noqa: BLE001
        row(
            "A3",
            "call the NET with a duck spec no door established",
            f"refused -> {_short(exc)}",
        )
    row(
        "A3b",
        "WHEN did the refusal arrive — before or after the body?",
        (
            f"the body read {len(touched)} attribute(s) off the unestablished duck BEFORE "
            f"anything refused: {touched}. THE REFUSAL IS THE POST-CONDITION'S OWN @admits "
            "DOOR, WHICH RUNS AFTER THE BODY RETURNS."
            if touched
            else "the body read nothing off the duck — refusal preceded the body"
        ),
    )

    # ---------------------------------------------------------------- A4
    # A HOSTILE ADAPTER: code that imports NOTHING from crash_detector and reaches the
    # module object through `sys.modules`. This is the declared-foreign actor, not a
    # developer at a REPL.
    try:
        stolen = sys.modules["crash_detector.engine.evaluate"]._evaluate_dial
        same = stolen is net
        row("A4", "hostile adapter via sys.modules, importing nothing", f"OBTAINED, identical object: {same}")
    except Exception as exc:  # noqa: BLE001
        row("A4", "hostile adapter via sys.modules", f"FAILED -> {_short(exc)}")

    # ---------------------------------------------------------------- A5
    # THE INNER, via __wrapped__ — the M3 route. This BYPASSES the net.
    if hasattr(net, "__wrapped__"):
        inner = net.__wrapped__
        row("A5", "the INNER via `__wrapped__` (bypasses the net)", f"PRESENT -> {inner!r}"[:160])
        try:
            got = inner(spec_starved, usable_starved, now)
            row("A5b", "call the INNER on a starved spec", f"POST-CONDITION NOT RUN -> returned {type(got).__name__}")
        except Exception as exc:  # noqa: BLE001
            row("A5b", "call the INNER on a starved spec", f"raised -> {_short(exc)}")
    else:
        row("A5", "the INNER via `__wrapped__` (bypasses the net)", "ABSENT — this route does not exist")

    # ---------------------------------------------------------------- A6
    # THE INNER, via __closure__ — DECLARED LIMIT 6, true of every Python decorator.
    cells = [c.cell_contents for c in (net.__closure__ or ()) if callable(getattr(c, "cell_contents", None))]
    if cells:
        row("A6", "the INNER via `__closure__` cells (DECLARED LIMIT 6)", f"PRESENT -> {cells[0]!r}"[:160])
    else:
        row("A6", "the INNER via `__closure__` cells", "no callable cell found")

    # ============================================================================ #
    print()
    print("HALF (b) — DOES THE NET'S POST-CONDITION BIND EVERYTHING ITS OPEN ARITY ADMITS?")
    print()
    print("  The net takes (spec, usable, now_utc, *extra, **extra_by_name).")
    print("  The post-condition reads THREE things: (spec, usable, reading).")
    print()

    # ---------------------------------------------------------------- B0
    # The post-condition DOES hold on the axis it was written for. Counterfactual arm.
    try:
        ev.refuse_a_number_without_its_inputs(
            spec_starved, usable_starved, ev.Value(value=object(), as_of_utc=now, inputs_used=("src.a",))
        )
        row("B0", "post-condition on a starved spec + value-bearing reading", "NOT REFUSED")
    except Exception as exc:  # noqa: BLE001
        row("B0", "post-condition on a starved spec + value-bearing reading", f"REFUSED -> {_short(exc)}")

    # ---------------------------------------------------------------- B1
    # `*extra` carries `model` to the evaluator. `required_inputs_are_all_present` reads
    # `spec.model_ref` — a NAME on the spec — and NEVER the ModelSpec object that actually
    # decides the magnitude. So: is the model the post-condition reasons about the model
    # the body computes with?
    fake_model = ModelSpec(
        model_id="a-model-the-registry-never-resolved",
        dial_id="equity_crash",
        required_input_ids=("src.a",),
        contributing_input_ids=(),
        mapping=MappingKind.UNSPECIFIED,
        parameters={},
        provenance=ModelProvenance(
            stands_for="whatever the caller says it stands for",
            account="supplied by the caller through *extra and resolved by nothing",
            decided_by="the caller",
        ),
    )
    premise = ev.required_inputs_are_all_present(spec_satisfied, usable_satisfied)
    row("B1a", "post-condition premise for (satisfied spec, present inputs)", f"required_inputs_are_all_present = {premise}")
    row(
        "B1b",
        "does the premise read the *extra model at all?",
        "NO — it reads spec.required_input_ids, spec.model_ref (a NAME) and usable. "
        "The ModelSpec that decides the magnitude is not an argument to it.",
    )
    try:
        got = net(spec_satisfied, usable_satisfied, now, fake_model)
        row("B1c", "call the NET with a caller-supplied model through *extra", f"RETURNED {type(got).__name__} — post-condition did not refuse")
    except Exception as exc:  # noqa: BLE001
        row("B1c", "call the NET with a caller-supplied model through *extra", f"raised -> {_short(exc)}")

    # ---------------------------------------------------------------- B2
    # WHAT BOUNDS B1 TODAY, MEASURED BY EXHAUSTION — not assumed, and not argued.
    #
    # `model` reaches exactly one consumer: `compute(model, payloads)`. `MappingKind` is
    # closed BY THE LANGUAGE (an Enum with members cannot be extended). So the set of
    # outcomes a caller-supplied model can produce is FINITE AND ENUMERABLE, and this arm
    # enumerates it rather than reasoning about it. If every member RAISES, then no
    # `*extra` model can change what the evaluator RETURNS, because on that path the
    # evaluator does not return at all.
    row("B2", "MappingKind members shipped", f"{[m.name for m in MappingKind]} — closed by the language")
    from crash_detector.engine.mapping import compute as _compute

    outcomes = []
    for member in MappingKind:
        probe_model = ModelSpec(
            model_id="probe",
            dial_id="equity_crash",
            required_input_ids=("src.a",),
            contributing_input_ids=(),
            mapping=member,
            parameters={},
            provenance=ModelProvenance(
                stands_for="a probe", account="a probe", decided_by="a probe"
            ),
        )
        try:
            result = _compute(probe_model, {"src.a": {}})
            outcomes.append(f"{member.name}: RETURNED {type(result).__name__}")
        except Exception as exc:  # noqa: BLE001
            outcomes.append(f"{member.name}: raised {type(exc).__name__}")
    row("B2b", "every MappingKind member through `compute`, exhaustively", "; ".join(outcomes))
    row(
        "B2c",
        "so can an *extra model change what the evaluator RETURNS at this tree?",
        (
            "NO — every member of the closed mapping set RAISES, so the *extra-influenced "
            "path has no return statement a caller can reach. **THE BOUND IS `compute`'s "
            "OWN @admits DOOR PLUS A MAPPING SET WITH NO COMPUTING MEMBER — A PRODUCT GAP "
            "(CD-D-005 OWED) — AND NOT THE POST-CONDITION.**"
            if all("raised" in o for o in outcomes)
            else "YES — at least one member returns; the post-condition cannot see which "
            "model produced it. **THE HOLE IS LIVE.**"
        ),
    )

    # ---------------------------------------------------------------- B3
    # An arbitrary keyword through `**extra_by_name`.
    try:
        got = net(spec_starved, usable_starved, now, unexpected_keyword=object())
        row("B3", "arbitrary `**extra_by_name` through the net", f"ACCEPTED -> {type(got).__name__}")
    except TypeError as exc:
        row("B3", "arbitrary `**extra_by_name` through the net", f"stopped by the INNER's arity -> {_short(exc)}")
    except Exception as exc:  # noqa: BLE001
        row("B3", "arbitrary `**extra_by_name` through the net", f"raised -> {_short(exc)}")

    # ---------------------------------------------------------------- B4
    # `now_utc` is positional, is forwarded, and is read by NO door and by no post-condition.
    class _DuckClock:
        def __getattr__(self, name):  # pragma: no cover
            return lambda *a, **k: None

    try:
        got = net(spec_starved, usable_starved, _DuckClock())
        row("B4", "a duck `now_utc` through the net", f"ACCEPTED -> {type(got).__name__}; the post-condition never reads now_utc")
    except Exception as exc:  # noqa: BLE001
        row("B4", "a duck `now_utc` through the net", f"raised -> {_short(exc)}")

    print()
    print("=" * 96)
    print(f"{len(RESULTS)} arm(s) measured against {ev.__file__}")
    print("=" * 96)
    return 0


class _DuckConfig:
    """Answers everything `evaluate` asks a ConfigSnapshot, and is not one."""

    def window(self):
        return None

    def spec_for(self, dial_id):
        return None

    def model_for(self, dial_id):
        return None


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:  # pragma: no cover
        traceback.print_exc()
        raise SystemExit(2)
