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
the rest of the tree imports on the standard library alone.

`psycopg2-binary` is imported by **exactly one file in this repository**, and that file is
`db/migrate.py`, which is not part of the importable application package. Nothing under
`src/` imports a database driver: `crash_detector.store.migrate` takes an already-open
PEP 249 connection as an argument. A test asserts both.

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
  runtime/
    lifecycle.py           SIGTERM, a bounded clean shutdown, logs to stdout
  store/
    migrations.py          discovering and validating the set; append-only, forward-only
    migrate.py             applying it, against an injected PEP 249 connection
contracts/
  public_envelope.schema.json    closed; two dials and the §8 honesty fields, nothing else
  private_envelope.schema.json   closed; the same, plus its PRIVATE classification
db/
  migrate.py               THE MIGRATION STEP — not any service's startup path
  grant_matrix.json        the BLUEPRINT §4 grant matrix, machine-readable
  migrations/*.sql         seven forward-only migrations, each stating its rollback
deploy/
  compose.yaml             seven services, two networks, the egress posture as DATA
  Dockerfile.*             six images, WRITTEN AND NOT BUILT (RT-B is forbidden in WO-2)
  base-images.json         base image digests, and what has NOT been resolved
  entrypoints/*.py         one thin shim per service over the lifecycle contract
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

## The store, and the migration step

PostgreSQL 16, six schemas and six roles (`BLUEPRINT.md` §4). The migrations are
**append-only and forward-only** and each one states its rollback, or states plainly that
it has none.

```bash
python3 db/migrate.py --plan     # validate the set, report what is pending, write nothing
python3 db/migrate.py --apply    # apply every pending migration, each with its ledger row
```

**This is a dedicated deployment step and it is not any service's startup path**
(`PBG-DATA-002`, `PBG-DATA-003`). The command lives in `db/` rather than inside
`src/crash_detector/`, so no service can reach it by an import even by accident. Migrating
on boot means migrating once per replica, racing the other replicas, with whatever
privileges the service's own role happens to hold.

Two properties are worth knowing before touching this directory:

- **A migration that has been applied is immutable.** The ledger records the SHA-256 of
  each file, comments included, and the runner refuses the whole run if a file has changed
  since it ran. Correct a migration by superseding it, never by editing it.
- **Every migration must be applied by the SAME migrator role.** Migration 7's
  `ALTER DEFAULT PRIVILEGES` is recorded against the role that ran it, so a second
  migrator would attach the default privilege to the wrong grantor.

The migrator is **not** one of the six application roles. It needs `CREATEROLE` and
ownership of the database; no application role has either.

**Roles are created without passwords.** A password in a migration is a secret in Git, and
a secret that was ever committed is compromised regardless of any later deletion
(`PBG-SEC-002`, non-waivable). Authentication therefore fails closed until the deploy step
sets each password from the environment, after migration and outside version control:

```sql
ALTER ROLE cd_engine PASSWORD :'password';   -- value from $CD_STORE_ENGINE_PASSWORD
```

`db/grant_matrix.json` carries the same matrix machine-readably. Three things must agree —
the migration SQL, that declaration, and the live catalogue of a built store — and each
comparison is made by a different instrument.

## The container set

`deploy/` describes seven containers on two networks (`BLUEPRINT.md` §2). **Nothing in it
is built.** The recorded state is `CONTAINER_READY_DESIGN` with
`CONTAINER_BUILD_NOT_YET_AUTHORISED`: `PBG-RT-010` keeps image creation and container
startup as separate, separately authorised actions, and WO-2 authorises neither. Image
build, smoke test and the non-root proof observed on a running container are WO-3 work.

- `cd-engine`, `cd-public`, `cd-private` and `cd-store` have **no egress at all**, enforced
  structurally by attaching them only to networks marked `internal: true`.
- `cd-collectors`, `cd-witness` and `cd-review` carry an explicit allowlist, and **every
  allowlist ships empty**. Naming an ingredient-source host would be registering an
  ingredient source (CD-D-005, the Product Owner's and owed); the witness and model hosts
  are declared in the Blueprint by name and not by address, and this seat does not write a
  hostname it did not verify. Each empty allowlist records what is pending and why.
- The egress posture is **data**, not prose: `services.<name>.x-egress` in
  `deploy/compose.yaml`, readable with the standard library alone.
- Both surfaces bind **127.0.0.1 only** — 8710 public, 8711 private. Nothing is publicly
  reachable until the Product Owner says so (CD-D-006, CD-HOLD-005).
- Base images are pinned **by digest**. `cd-store`'s was resolved on the DEV host with
  `docker image inspect` and recorded in `deploy/base-images.json`; the Python base is
  recorded as `DIGEST_NOT_RESOLVED`, and each Dockerfile takes it as a build argument with
  no default so a build fails closed rather than falling back to a tag.
- **No image declares a `VOLUME`.** The store's named volume is the only durable storage in
  the system and it is declared in `deploy/compose.yaml`. A `VOLUME` in a Dockerfile creates
  an anonymous writable volume wherever that image runs, which is the durable storage class
  leaking into the read-only one (`PBG-RT-013`).

### The SIGTERM contract

`SIGTERM` means shut down cleanly within the grace period, and the handling lives in
`crash_detector.runtime.lifecycle` — in the **application**, because a process that ignores
`SIGTERM` cannot be fixed from outside it.

One property of that module is worth stating here, because it is easy to get wrong and its
failure is silent: **the signal handler acquires no lock.** A Python signal handler runs on
the thread it interrupted, so any lock that thread already holds is one the handler waits on
forever. An earlier version called `threading.Event.set()` from the handler; `set()` takes
the condition lock, `Event.wait()` holds that same lock for a few bytecodes, and a `SIGTERM`
landing in that window wedged the process — measured at 5 of 40 signals (12.5%) before the
fix and 0 of 100 after.

The handler now performs attribute stores only; the loop polls the flag in bounded slices
(`WAIT_SLICE_SECONDS`, 50 ms); and the second-signal path uses `os.write` and `os._exit`
rather than `print` and `SystemExit`, both of which take locks. Anything added to that
handler must obey the same rule.

## Configuration and secrets

Configuration is read from the environment; there are no host-specific absolute paths and
no config file expected outside this tree (`BLUEPRINT.md` §11).

| Variable | Meaning |
|---|---|
| `CD_CONTRACTS_DIR` | where the envelope contracts live; defaults to `contracts/` resolved relative to the package, so a container may mount them elsewhere without a code change |
| `CD_TICK_INTERVAL_SECONDS` | each service's loop interval. **Required**, no in-code default: a cadence nobody chose is a cadence nobody chose, and cadence is monitored (CD-AC-008) |
| `CD_SHUTDOWN_GRACE_SECONDS` | the bounded shutdown budget; defaults to 15.0, and must stay under the platform's `stop_grace_period` |
| `CD_STORE_HOST`, `CD_STORE_PORT`, `CD_STORE_NAME` | the store. **Required**, never defaulted: a default host connects to the wrong store exactly once |
| `CD_STORE_MIGRATOR_USER` | the migrator role — not one of the six application roles |
| `CD_STORE_SSLMODE` | optional; defaults to `prefer` |
| `CD_PYTHON_BASE` | the digest-pinned base image for the six application images. **Required at build time, no default** — see `deploy/base-images.json` |

**Secrets are referenced, never reproduced** — not in code, Git, logs, fixtures, evidence
or records (`PBG-SEC-002`, `PBG-EVID-003`, non-waivable). Every secret is named by
environment variable only. No governed record in this project carries a secret value, and
`.env` files are git-ignored.

The complete set of secret env-var **names**, and only their names:

| Variable | Read by |
|---|---|
| `CD_STORE_MIGRATOR_PASSWORD` | `db/migrate.py`, at the point of use |
| `CD_STORE_COLLECTOR_PASSWORD` | `cd-collectors` |
| `CD_STORE_WITNESS_PASSWORD` | `cd-witness` |
| `CD_STORE_ENGINE_PASSWORD` | `cd-engine` |
| `CD_STORE_PUBLIC_PASSWORD` | `cd-public` |
| `CD_STORE_PRIVATE_PASSWORD` | `cd-private` |
| `CD_STORE_REVIEW_PASSWORD` | `cd-review` |
| `CD_MODEL_API_KEY` | `cd-review` |

## Status

WO-2 is in progress on branch `wo-2-skeleton`. What is delivered and what is deliberately
owed is recorded in `governance/engineering/build-log/`, which is the record — not this
file.
