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

* every module the declared process of **every container built from the engine's image** starts.
  The image is anchored at `deploy/compose.yaml`'s `cd-engine` service and identified by its
  **artefact** — the build context plus a byte-identical Dockerfile — not by the service name, so a
  second service built from that image is an engine container whatever it is called
  (`CD-ENGINE-ROOT-004`, closing `CD-PL-F62`). Each process is read as `entrypoint + command`, with
  compose overriding the image, a compose `entrypoint` cancelling the image `CMD`, and YAML merge
  keys resolved; **and**
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
| `CD-ENGINE-ROOT-108` | the process names **no** Python module the image ships — an empty root set; or an engine container starts a module the scanned universe does not hold |
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
   left to be discovered: write compose sequences in block form.

   **The non-termination half of this boundary is DISCHARGED, and it is SUPERSEDED rather than
   erased** (`CD-ENG-READER-F06` / `CD-D-063`, *amended at increment 6*). Until `253c38b` it read:
   *"That reader also has a known non-termination defect (`CD-ENG-WO2R-F14` / `CD-PL-F61`, ruled to
   a separate bounded dispatch by `CD-D-051`) which this check shares and which is not repaired
   here and not in scope."* **That sentence is no longer true.** The reader was repaired at
   `253c38b` under `CD-DISPATCH-WO2R-READER`, and this check — a **third** consumer of the shared
   reader, not the two the governing records named (`CD-ENG-READER-F01`) — now returns a **stated
   refusal** where it used to return no verdict at all.

   **MEASURED at increment 6**, on a pristine extraction of `253c38b` carrying the `R02`/`PL-T5`
   document (`declared_in` written as a list of two authorities), command
   `timeout 120 python3 -B tools/register/check_engine_no_witness_reach.py --root .` →
   **exit 3**, `CD-RT-003-ENGINE-NO-WITNESS-REACH: PRECONDITION_NOT_MET`, clause
   `CD-ENGINE-ROOT-101`, naming `deploy/compose.yaml` line 428 and what could not be read there.
   Previously **exit 124** — no verdict.

   **The residue that replaced it, and it is narrower** — boundary `8b` of
   `CD-RT-012-EGRESS-NO-BROKER`, which this check shares because it shares the reader: **a document
   nested deeper than the interpreter's recursion limit raises `RecursionError` rather than a
   stated refusal.** It **terminates** — neither a hang nor a false clean — but it reports a Python
   traceback instead of a line number and exits `1` rather than the `3` this check uses for *"I
   could not read my subject"*. **MEASURED at increment 6**, on a pristine extraction of `253c38b`
   with ~600 levels of block mapping inserted under `cd-collectors`' `pending` (the exact generator
   is row `R08` of `variants/WO-2R/MANIFEST.md`; the document is ~224 KB, which is why it is not
   carried as a patch) → **exit 1**, `RecursionError: maximum recursion depth exceeded`, raised in
   `tools/register/_yamlmin.py` `_parse_mapping`. **Not repaired** — converting it would move this
   check from exit 1 to exit 3 on an input that already has a verdict; raised by the reader seat as
   `CD-ENG-READER-F02` for a Project Lead ruling.
5. **THE WALK ROOTS ARE THE ENGINE CONTAINER SET, DERIVED BY IMAGE IDENTITY.** *Amended at
   `CD-D-055` closing `CD-PL-F62`.* This boundary used to read "only the engine SERVICE's process
   is a walk root ... the other five are resolved" — it distinguished services **by purpose** in
   prose while the code distinguished **by name**, so it did not contemplate a **second service
   built from the engine's own image**, and an auditor reading it would not have expected that case
   to escape. It was *incomplete*, not false.
   **What the guard now does:** every service that builds the same build context from a
   **byte-identical Dockerfile** as `cd-engine` is an engine container whatever it is called
   (`CD-ENGINE-ROOT-004`), and its process is a walk root; its shipped files are scanned against
   **its own** declared sys.path roots. Services built from a **different** image are RESOLVED only
   — each must name a module its image ships, so a rename or restructure that breaks the derivation
   is loud rather than silent — but they are not roots, and witness code reachable from
   `cd-witness` is correct rather than a violation.
   **MEASURED, four ways, each executable:**
   * `V42` appends the E06 import to `deploy/entrypoints/cd_witness.py`: exits `0`, PASS 23. Not an
     escape; the criterion.
   * `PL-U6b` adds a sixth service `cd-engine-worker` built from `deploy/Dockerfile.engine` whose
     entrypoint imports `crash_detector.witness.panel`. At `be34fe4` it exited `0`, PASS 24 — the
     escape `CD-PL-F62` reports. Here it exits `1`, naming the route
     `crash_detector.witness.panel <- cd_worker`.
   * `V45` adds a seventh service `cd-engine-shadow` from the same Dockerfile with a **clean**
     entrypoint: exits `0`, PASS 27, and the engine container set grows 1 → 2 with the derived roots
     growing `cd_engine` → `cd_engine, cd_shadow`. **The subject follows the artefact**, and a
     legitimate second engine container is not a violation.
   * `V46` copies `Dockerfile.engine` byte-for-byte to `Dockerfile.engine-clone` and builds
     `cd-analytics` from it, reaching witness through the top-level package: exits `1`. The identity
     is the image's **content**, so renaming the file does not evade it.
   **Note on these assertion counts, corrected at increment 5's `CD-ASR-F06` commit.** They were
   measured at the addendum commit `4cae8be`, where the clean arm was PASS 23. At the delivered SHA
   the clean arm is PASS 24 and every example is one higher — `V42` PASS 24, `V44` PASS 24, `V45`
   PASS 28 — because `crash_detector.staleness`, new in the `CD-ASR-F06` commit, is reachable from
   the engine root set so `len(reached)` is one larger. It is **not** witness code and no violation
   is reported. Both numbers are stated rather than one overwritten.

   **What is still outside it:** a service built from a Dockerfile that is **not byte-identical** —
   a near-copy differing by one comment — is a different image by the artefact's own account and is
   not a walk root. Closing that means deciding when two different Dockerfiles "mean" the same
   image, which is a judgement and not a derivation. **CARRIED, MEASURED by the implementing seat
   (`CD-RULE-006`):** the container-set test layer asserts the declared service set by **equality**,
   so it refuses **any** service added to `deploy/compose.yaml` whatever image it builds. On the
   `PL-U6b` tree at `be34fe4` this seat observed **`8 failed, 1184 passed`** —
   `tests/test_runtime_lifecycle.py::test_there_is_one_entrypoint_per_application_service` and seven
   in `tests/test_deploy_container_set.py` (`test_all_seven_services_are_declared`,
   `test_every_service_declares_a_non_root_user`,
   `test_the_declared_uid_matches_the_machine_readable_one`, `test_every_service_has_a_distinct_uid`,
   `test_every_service_declares_its_three_storage_classes`,
   `test_only_the_store_declares_durable_storage`,
   `test_every_build_passes_the_base_image_through_as_a_required_variable`) — while the six other
   static register checks all exited `0`. The carrier is the container-set **test** layer, not the
   register.
6. **RUN-TIME `sys.path` MUTATION IS NOT DERIVED. This is the derivation's own residue.**
   **MEASURED EXAMPLE (variant `V44`):** `deploy/entrypoints/cd_engine.py` inserts
   `/app/src/crash_detector/witness` into `sys.path` and then writes `import panel`. `panel.py`
   **is** scanned and **is** witness code, but the edge is spelled `panel`, which resolves to no
   module in the graph, and this check exits `0`, PASS 23 assertions at `dae6503` and PASS 24 at the
   increment-5 SHA, 0 violations.
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
