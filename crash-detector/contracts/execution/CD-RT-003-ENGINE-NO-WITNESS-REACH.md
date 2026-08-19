# Execution contract — CD-RT-003-ENGINE-NO-WITNESS-REACH

**CD-AC-003** · Witnesses are side-by-side, never ingredients · obligation **MANDATORY** · scope **CLASS** ·
delivered in **WO-2**

This document exists because `REQUIRED-TEST-REGISTER-CONTRACT-v1` check 3 requires every
declared test to name an execution contract that RESOLVES. It states how this test is run
and what its exit codes mean. **It states no result.** The register carries obligations;
status is computed by the validator from the register, the PID and append-only run records,
and there is no field anywhere in this chain in which an author could write a verdict.

## The proposition

Nothing reachable from **the engine container's root set** reaches witness code, by any import
route.

The root set is **DERIVED and is a UNION**:

* every module the **engine container's declared process** starts — read from
  `deploy/compose.yaml`'s `cd-engine` service and the Dockerfile it names, as
  `entrypoint + command`, with compose overriding the image, a compose `entrypoint` cancelling
  the image `CMD`, and YAML merge keys resolved; **and**
* every module in `src/crash_detector/engine/`, which is BLUEPRINT §13's own subject.

**Neither is a superset of the other, and that is measured rather than assumed.** In WO-2 the
container's process reaches `crash_detector.runtime.lifecycle` and does **not** reach
`crash_detector.engine`, because the WO-2 services start, tick and shut down and evaluate
nothing. Replacing the package root with the derived one would have deleted the guard that
catches the original plant in `evaluate.py`.

## Why the subject is derived and not a constant

**CD-ASR-F05.** An independent auditor appended `from crash_detector.witness.panel import Agrees`
to `deploy/entrypoints/cd_engine.py` — the module that **is** the engine container's process — and
this check exited `0`. The guard's subject was the engine **PACKAGE**, rooted at a constant under
`src/`; the criterion's subject is the engine **CONTAINER**. The file was never read.

The repair is not a second hard-coded path. The walk root **and** the scanned universe are read
out of the artefacts that decide them, so **changing the artefact changes the guard's subject** —
the same property `CD-RT-012-EGRESS-NO-BROKER` already has for its service set. Observed:
changing `ENTRYPOINT` to `/app/entrypoints/cd_public.py` moves the reported root to `cd_public`;
changing it to `-m crash_detector.runtime.engine_main` moves it there and changes the image's
sys.path roots with it.

## Command

```
python3 tools/register/check_engine_no_witness_reach.py --root .
```

Run with the working directory set to **the root of a subject tree the auditor extracted
itself** — `git archive <sha> | tar -x -C <tmpdir>`, never the Engineer's worktree. The line
above is verbatim: no path fixing, no editing, no wrapper. There is no run-everything
harness in this repository and there may not be one, because an auditor verifying through a
harness the project wrote is verifying the harness (`PBG-ASSURE-001`).

## Subject

The import graph of **everything the engine image ships**, built by walking every module's AST and
resolving relative imports against the module's own package. Import PLACEMENT does not evade it: a
function-local import is the same edge as a module-level one.

The scanned universe is the union of `src/` — named as BLUEPRINT §13 names it, so a Dockerfile edit
can never remove it — and every `*.py` the engine Dockerfile's own `COPY` instructions place in the
image, named against the sys.path roots the image itself declares (`ENV PYTHONPATH`, the compose
`environment` override, the entry script's own directory, and `WORKDIR` when `-m` is used).

## Fail-closed clauses

Every derivation that cannot be made is a **non-zero exit with a stated reason and a stable clause
id** — never an empty root set, and never a pass.

| clause | what it refuses |
|---|---|
| `CD-ENGINE-ROOT-101` | `deploy/compose.yaml` absent, unreadable, unparseable, or declaring no services |
| `CD-ENGINE-ROOT-102` | the engine service is absent, or declares no `build` naming a Dockerfile in this tree |
| `CD-ENGINE-ROOT-103` | a `<<` merge key naming an anchor the reader cannot locate at the top level |
| `CD-ENGINE-ROOT-104` | the Dockerfile is absent, unreadable, or declares neither `ENTRYPOINT` nor `CMD` |
| `CD-ENGINE-ROOT-105` | a `COPY` that cannot be resolved statically — `--from=` a stage, a glob, a variable, a missing source, an escape from the build context |
| `CD-ENGINE-ROOT-106` | the declared process is in **shell form**, so what starts is decided by `/bin/sh` at run time |
| `CD-ENGINE-ROOT-107` | the process is not a Python interpreter this check can read, or it names code inline (`python -c`) |
| `CD-ENGINE-ROOT-108` | the process names **no** Python module the image ships — an empty root set |
| `CD-ENGINE-ROOT-109` | two different files claim one module name, so the graph is ambiguous |
| `CD-ENGINE-ROOT-110` | the image ships Python that no declared sys.path root can name |

## Why it is asserted this way

This check guards the product's most consequential separation, and it has now been wrong twice, in
two different ways. Its first cut got the relative-import anchoring wrong and read clean while the
edge existed (CD-ENG-F27). Its second read the wrong subject entirely (CD-ASR-F05). Both are
recorded here because an auditor is entitled to know which guards have already been wrong, and how.

## Declared limit (CD-RULE-004)

Stated identically here, in the header of `tools/register/check_engine_no_witness_reach.py`, and in
`required-tests.yaml`. Each hand-off names a layer that was **measured**, or says **NOT PROVED TO
BE CARRIED ANYWHERE** (CD-RULE-006).

1. **A STATIC READ OF DECLARATIONS AT ONE COMMIT.** No image is built and no container is started
   (RT-B is forbidden in WO-2). A compose **override** file, `docker run --entrypoint`,
   `docker exec`, or an orchestrator manifest that is not `deploy/compose.yaml` are outside the
   subject. **NOT PROVED TO BE CARRIED ANYWHERE**; owed at WO-3, the same residue
   `CD-RT-012-EGRESS-NO-BROKER` declares at its boundary 6.
2. **A SECOND PROCESS STARTED AT RUN TIME** — `subprocess.Popen`, `os.execv` — is not an import
   edge. **PARTIALLY CARRIED, MEASURED:** a dotted witness path in a string literal fires, and a
   non-literal `import_module` fires. For a second process named by a non-witness path, **NOT
   PROVED TO BE CARRIED ANYWHERE**.
3. **IMPORTING WITNESS TYPES IS NOT READING WITNESS DATA**, and this check does not claim
   otherwise — the auditor made that point about E06 itself. **CARRIED** by
   `CD-RT-003-GRANT-MATRIX-LIVE`, which proves `cd_engine` holds no privilege of any kind on schema
   `witness` by any of seven routes in a real PostgreSQL session. A different instrument on a
   different substrate.
4. **THE COMPOSE READER IS A STDLIB-ONLY YAML SUBSET.** A non-empty flow collection —
   `entrypoint: ["python3", "/app/x.py"]` — is not supported and becomes `CD-ENGINE-ROOT-101`, a
   refusal. Fail-closed, but a shape a legitimate author could write, so it is declared rather than
   left to be discovered: write compose sequences in block form. That reader also has a known
   **non-termination** defect (`CD-ENG-WO2R-F14` / `CD-PL-F61`, ruled to a separate bounded dispatch
   by `CD-D-051`) which this check shares and which is **not repaired here and not in scope**.
5. **ONLY THE ENGINE SERVICE'S PROCESS IS A WALK ROOT.** The other five services built from this
   tree are **RESOLVED** — each must name a module the image ships, so a rename or restructure that
   breaks the derivation is loud rather than silent — but they are not roots. **MEASURED:** variant
   `V42` appends the E06 import to `deploy/entrypoints/cd_witness.py` and this check exits `0`,
   PASS 23 assertions. That is not an escape; it is the criterion.
6. **RUN-TIME `sys.path` MUTATION IS NOT DERIVED. This is the derivation's own residue.**
   **MEASURED EXAMPLE (variant `V44`):** `deploy/entrypoints/cd_engine.py` inserts
   `/app/src/crash_detector/witness` into `sys.path` and then writes `import panel`. `panel.py`
   **is** scanned and **is** witness code, but the edge is spelled `panel`, which resolves to no
   module in the graph, and this check exits `0`, PASS 23 assertions, 0 violations.
   **PARTIALLY CARRIED, MEASURED:** the string-literal and dynamic-import clauses are unchanged and
   still bite, and `CD-ENGINE-ROOT-110` closes the neighbouring route of shipping code **off** the
   declared path (variant `V43`, refused, exit 3). **FOR A SHORT-NAME IMPORT OF ALREADY-SCANNED
   WITNESS CODE AFTER A `sys.path` INSERT, NOT PROVED TO BE CARRIED ANYWHERE.**
   **Why it is not closed, stated so the argument can be judged rather than assumed:** closing it
   means either refusing every `sys.path` mutation — which the clean tree itself contains,
   legitimately, in `deploy/entrypoints/_service.py`, so the guard would fire on the product — or
   symbolically evaluating the inserted path, which is interpreting code the check has already said
   it will not follow. Raised by the implementing seat against its own work as `CD-ENG-WO2R-F17`.

## Preconditions

* `python3` 3.11 or later. **Stdlib only** — no install step, no network, no
  virtualenv. A check that needs a package installed is a check the auditor cannot run.
* The subject tree extracted by the auditor, with the working directory set to its root.
  `--root .` is not a default and is not optional: it is there so that the check is always
  pointed at a tree explicitly, and never at whatever directory it happens to sit in.

## Exit semantics

| exit | meaning |
|---|---|
| `0` | CLEAN — assertions were made and all of them held. A run that made ZERO assertions refuses instead, so `0` can never mean "I looked at nothing". |
| `1` | VIOLATION — at least one finding, each printed with its file, its line and why it is one. |
| `2` | USAGE — the command line was wrong. |
| `3` | PRECONDITION NOT MET — the check could not do its job, with the reason on stderr. |

Anything other than `0` is a failure. **The check never skips, for any reason**
(`PBG-CI-002`): a precondition it cannot meet is a non-zero exit with a stated reason,
never a pass.

## Negative control

Any import edge by which something reachable from **the engine container's root set** reaches
witness code — module-level, function-local, aliased, relative or through an intermediate module.
Import PLACEMENT must not evade it: a function-local import is the same edge as a module-level one.
The root set is DERIVED and is a UNION, so the plant may be placed in the engine package, in the
module the `ENTRYPOINT` names, in anything either reaches transitively, in a module named by a
compose `entrypoint:` or `command:` override, or in one named through a YAML merge key — all of
them are the same violation. **A derivation that cannot be made is also a failure and not a pass**,
with a stated `CD-ENGINE-ROOT-1xx` clause id.

Detection is a **contrast**, and the validator computes it as one: the same declared command
must exit `0` on the clean subject and non-zero on the subject with the violation planted.
A clean arm that fails cannot be told apart from a broken harness, and a broken harness
detects nothing — the validator returns `UNDECIDABLE`, never `PASS`.

The negative control for this test is declared as run record **`RTR-WO2-0001`**.
That record does not exist yet. It is the run the **independent Assurance
seat** will produce — a distinct actor from the one that wrote this test. Until it exists
the validator computes `UNDECIDABLE` for this test and the gate stays shut, which is
correct: this seat may declare which run must evidence its guard, and may not supply it.

## What this contract does not claim

It does not claim the test passes. It does not claim the criterion is satisfied. It does not
admit any evidence: `latest_admitted_run` is null in the register and this seat cannot fill
it in, because an implementation may not certify itself (`PBG-SOD-001`, non-waivable).
