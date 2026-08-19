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

`jsonschema` is imported by exactly two modules — `collectors/validation.py` and
`publication/envelope_contract.py` — and in both it is imported at the point of use, so
the rest of the tree imports on the standard library alone. `psycopg2-binary` is declared
for the store work that follows and is not yet imported anywhere.

**Nothing under `src/` imports a network module.** No `socket`, no `ssl`, no `http`, no
`urllib`, no HTTP client — asserted over the whole tree by
`tests/test_collector_boundaries.py`, which scans every import including function-local
ones.

---

## What is here

```
src/crash_detector/
  time_utc.py              UTC only; naive datetimes are refused, never assumed
  observations.py          the observation record and its four-way fetch outcome
  source_registry.py       sources, criticality and the criticality contract
  dials/
    reading.py             Reading := Value | Degraded | Unknown      (CD-AC-001)
    scores.py              two unrelated frozen score types           (CD-AC-002)
    dialset.py             a container with no scalar method          (CD-AC-002)
  engine/
    config.py              the run-level snapshot, carrying the source registry
    model.py               the contribution-model shape; registry EMPTY by decision
    evaluate.py            evaluate(observations, config, now_utc) -> DialSet, pure
  collectors/
    adapter.py             the adapter protocol: fetch and record, never compute
    validation.py          validate once at the boundary; never coerce, never quote
    attempt.py             one row per attempt, and the idempotency key
    runner.py              bounded timeouts and retries; EVERY attempt writes a row
  publication/
    classification.py      the book-adjacent and secret-bearing key registers
    envelope_contract.py   publication REFUSES on an unknown key; it does not filter
  witness/
    panel.py               WitnessPanel := Agrees | Diverges | Unavailable  (CD-AC-005)
  serving/
    witness_resolver.py    absence and staleness -> UNAVAILABLE, never AGREES
contracts/
  public_envelope.schema.json    closed; two dials and the §8 honesty fields, nothing else
  private_envelope.schema.json   closed; the same, plus its PRIVATE classification
tests/                     unit tests, and the in-memory test doubles in collector_fakes.py
```

`schemas/` at the project root is **reserved by the governance framework**. Product JSON
Schemas live in `contracts/` and nowhere else.

`observations.py` and `source_registry.py` sit at the package root rather than under
`collectors/` because they are the *contract between* the collector layer and the engine
rather than a component of either. Putting them under `collectors/` would make
`crash_detector.engine` import the collector package and invert the §5/§7 boundary
(CD-D-008).

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
- **Every fetch attempt writes a row, including the failures.** `OK`, `FETCH_FAILED`,
  `MALFORMED` and `EMPTY` are four distinct outcomes, not three spellings of absence. A
  failed fetch that wrote nothing would be indistinguishable from a fetch that was never
  scheduled and from a source that had nothing to report.
- **A third, combined number has nowhere to be published.** The envelope contracts are
  closed at every level and their properties are an allowlist, so a blend is rejected by
  the schema whatever route computed it. Publication refuses; it does not filter.

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

| Variable | Meaning |
|---|---|
| `CD_CONTRACTS_DIR` | where the envelope contracts live; defaults to `contracts/` resolved relative to the package, so a container may mount them elsewhere without a code change |

**Secrets are referenced, never reproduced** — not in code, Git, logs, fixtures, evidence
or records (`PBG-SEC-002`, `PBG-EVID-003`, non-waivable). Every secret is named by
environment variable only, for example `CD_STORE_ENGINE_PASSWORD`. No governed record in
this project carries a secret value, and `.env` files are git-ignored.

## Status

WO-2 is in progress on branch `wo-2-skeleton`. What is delivered and what is deliberately
owed is recorded in `governance/engineering/build-log/`, which is the record — not this
file.
