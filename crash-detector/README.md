# Crash Detector

An **advisory** market-stress instrument. Two dials — equity crash and monetary
debasement — published side by side with external witnesses, never blended, never
executing anything.

This repository is governed by PBGv2. `PID.md` says what and why (its §1 and §3 are
Constitutional); `BLUEPRINT.md` says how. Neither is amended from here.

> **Advisory only.** There is no order, execution or broker interface anywhere in this
> codebase, and its absence is structural rather than a policy anyone has to remember
> (PID §6, CD-AC-012).

---

## Running it, with no install step

Everything runs on the host interpreter. There is no virtualenv, no build backend and no
install step, and that is a load-bearing property rather than a convenience: a check that
needs a network install is not a check anyone can run.

```bash
# import the package
PYTHONPATH=src python3 -c "import crash_detector; print(crash_detector.__version__)"

# run the tests
python3 -m pytest            # pyproject.toml sets pythonpath = ["src"]
```

Target runtime, verified on the DEV host rather than assumed:

| | |
|---|---|
| interpreter | CPython 3.11.2, linux-x86_64 |
| `jsonschema` | 4.10.3 |
| `psycopg2-binary` | 2.9.11 (import name `psycopg2`) |
| `pytest` | 9.0.2 |

Exact pins are in `requirements.txt`; the resolved set with SHA-256 digests is in
`requirements.lock`, whose header records how the digests were obtained and what has *not*
been verified.

**Nothing under `src/` imports a third-party package.** The code delivered so far is
standard library only; `jsonschema` and `psycopg2-binary` are declared for the boundary
validation and the store work that follow.

---

## What is here

```
src/crash_detector/
  time_utc.py              UTC only; naive datetimes are refused, never assumed
  observations.py          the observation record and its four-way fetch outcome
  dials/
    reading.py             Reading := Value | Degraded | Unknown      (CD-AC-001)
    scores.py              two unrelated frozen score types           (CD-AC-002)
    dialset.py             a container with no scalar method          (CD-AC-002)
  engine/
    config.py              the run-level configuration snapshot
    model.py               the contribution-model shape; registry EMPTY by decision
    evaluate.py            evaluate(observations, config, now_utc) -> DialSet, pure
  witness/
    panel.py               WitnessPanel := Agrees | Diverges | Unavailable  (CD-AC-005)
  serving/
    witness_resolver.py    absence and staleness -> UNAVAILABLE, never AGREES
tests/                     unit tests for the above
```

### The design rule everything follows

From `BLUEPRINT.md` §1:

> A doctrinal property is built as a structure that makes its violation inexpressible, and
> is paired with a mutation test that proves the structure bites.

So, concretely:

- **Absence has a name and no numeric fallback.** `Reading` is a sum type with three
  constructors and no common ancestor. There is no `Optional[float]`, no `float | None`,
  no zero default and no previous-value carry-forward anywhere on the dial path.
- **The two dials cannot be combined.** They are unrelated frozen types with no arithmetic
  dunder, no numeric coercion, no ordering and no shared base. `equity + monetary` is a
  `TypeError` from the interpreter, not a rule someone enforces.
- **The witness pipeline never reaches the score.** `crash_detector.engine` imports nothing
  from `crash_detector.witness`, and the store will hold the same separation again in the
  grant matrix.
- **Freshness cannot be faked.** A future-dated observation or panel row is refused rather
  than treated as fresh forever, and a non-finite staleness window is refused rather than
  honoured.

### Both dials currently read UNKNOWN, on purpose

WO-2 ships with **zero ingredient sources registered**. Which inputs feed each dial is
CD-D-005, ruled by the Product Owner as theirs and owed before WO-3 (`BLUEPRINT.md` §16).
With nothing registered, `evaluate` returns `Unknown` for both dials with the reason
`NO_REQUIRED_INPUTS_DECLARED`.

That is the doctrinally correct empty state, not a stub. Zero satisfied requirements is
not "all requirements satisfied", and an engine that answered anything else here would
already be violating CD-AC-001 on its first commit.

---

## Configuration and secrets

Configuration is read from the environment; there are no host-specific absolute paths and
no config file expected outside this tree (`BLUEPRINT.md` §11).

**Secrets are referenced, never reproduced** — not in code, Git, logs, fixtures, evidence
or records (`PBG-SEC-002`, `PBG-EVID-003`, non-waivable). Every secret is named by
environment variable only, for example `CD_STORE_ENGINE_PASSWORD`. No governed record in
this project carries a secret value, and `.env` files are git-ignored.

## Status

WO-2 is in progress on branch `wo-2-skeleton`. What is delivered and what is deliberately
owed is recorded in `governance/engineering/build-log/`, which is the record — not this
file.
