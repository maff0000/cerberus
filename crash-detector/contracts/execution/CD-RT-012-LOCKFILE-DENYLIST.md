# Execution contract — CD-RT-012-LOCKFILE-DENYLIST

**CD-AC-012** · No execution pathway exists · obligation **MANDATORY** · scope **CLASS** ·
delivered in **WO-2**

This document exists because `REQUIRED-TEST-REGISTER-CONTRACT-v1` check 3 requires every
declared test to name an execution contract that RESOLVES. It states how this test is run
and what its exit codes mean. **It states no result.** The register carries obligations;
status is computed by the validator from the register, the PID and append-only run records,
and there is no field anywhere in this chain in which an author could write a verdict.

## The proposition

**Every distribution named in every dependency manifest is one somebody REGISTERED**, in
`deploy/dependency-registry.yaml`, with a purpose, an authorising clause and a needing surface —
and no registered or manifest distribution is on the broker denylist or carries an execution
token.

*This proposition was rewritten at WO-2R2 increment 3.* It previously read "No dependency
manifest names a broker, exchange or order-routing SDK", which **claimed more than the guard
delivered** and was refuted by execution — see the declared limit below. The old sentence is
quoted rather than removed (`PBG-CONT-003`).

## Command

```
python3 tools/register/check_lockfile_denylist.py --root .
```

Run with the working directory set to **the root of a subject tree the auditor extracted
itself** — `git archive <sha> | tar -x -C <tmpdir>`, never the Engineer's worktree. The line
above is verbatim: no path fixing, no editing, no wrapper. There is no run-everything
harness in this repository and there may not be one, because an auditor verifying through a
harness the project wrote is verifying the harness (`PBG-ASSURE-001`).

## Subject

`pyproject.toml`, `requirements.txt` and `requirements.lock`, plus any `requirements*.txt`,
`*.lock` or `constraints*.txt` the check finds, with distribution names normalised per PEP 503 so
`alpaca_trade_api` and `Alpaca-Trade-API` are the same name — **and
`deploy/dependency-registry.yaml`, the declared registry**, read with the stdlib-only YAML subset
reader. The check prints every manifest it read, the number of distinct distributions it saw and
the size of the admissible set, so a vacuous pass is visible.

## Why it is asserted this way

An execution pathway one `pip install` away is still an execution pathway.

**And a denylist is the wrong shape for it.** `CD-ASR-WO2R-F05` proved that by execution:
`tastytrade-sdk==1.2.0`, a real brokerage's real order-entry SDK, exited `0`. The repair is not a
longer list — the next name is a brand founded next year — but **deny by default over a declared
registry**, the same move that closed the egress allowlist at WO-2R increment 3. A distribution is
admissible because somebody registered it, not because it failed to look like a broker, and
**nothing is recognised about an unregistered distribution**, so there is no pattern to write
around. The denylist and the token rule survive as a **second layer** over the registry and at the
manifest site; neither layer is sole.

## Declared limit (`CD-RULE-004`)

Stated identically here, in the header of `tools/register/check_lockfile_denylist.py`, and in
`required-tests.yaml`. Each hand-off names a layer that was **measured**, or says **NOT PROVED TO
BE CARRIED ANYWHERE** (`CD-RULE-006`).

**What this guard closes** is the class of **UNDECLARED DEPENDENCY** — which is what F05
exercised. **What it does not close** is "a dependency that can reach a broker", which is not
decidable from this tree at all.

1. **A REGISTERED DISTRIBUTION IS A HUMAN CLAIM AND A FALSE ONE IS NOT DETECTABLE HERE.** Someone
   who registers a distribution whose code in fact reaches a broker, under a name the denylist
   does not hold and carrying no execution token, is admitted by layer 1 because it is registered
   and cleared by layer 2 because it is not recognisable. **EXECUTABLE EXAMPLE:** add
   `quiet-market-client==1.0.0` to `requirements.txt` and `requirements.lock` **and** a matching
   six-key entry to `deploy/dependency-registry.yaml`; the check exits `0`. What the structure
   buys is that the claim must be written down, given a purpose, cited to a clause, attributed to
   a surface and reviewed by a person at a named line — **not that it is true**.
   **NOT PROVED TO BE CARRIED ANYWHERE.**
2. **`purpose` AND `declared_in` ARE NOT JUDGED FOR CONTENT.** The guard asserts they are present
   and non-empty. It cannot decide whether the English is honest or whether the cited clause says
   what the entry claims. **NOT PROVED TO BE CARRIED ANYWHERE.**
3. **THIS IS A STATIC READ OF DECLARED MANIFESTS AT ONE COMMIT.** It does not read the installed
   environment, `site-packages`, a vendored directory, a submodule, a committed wheel, a
   `pip install` in a Dockerfile `RUN` line, or anything a base image brings. A broker SDK
   **vendored as source** under `src/` is not a dependency and never appears in a manifest.
   **CARRIER MEASURED:** `CD-RT-012-NO-EXECUTION-INTERFACE` reads `.py` and `.sql` under `src/`,
   `db/`, `deploy/`, `tests/` and `tools/`, so vendored source is in **its** subject set —
   measured at this SHA, exit `0` over **42812 assertions** on the clean tree, its own six
   boundaries unchanged. **For a broker SDK arriving as a compiled wheel or inside a base image,
   NOT PROVED TO BE CARRIED ANYWHERE.**
4. **A DEPENDENCY IS PERMISSION TO IMPORT, NOT A PATHWAY.** The pathway needs somewhere to go.
   **CARRIER MEASURED BY THIS SEAT ON ITS OWN EXTRACTION**, not transcribed from the auditor's
   numbers (`CD-RULE-006`): `deploy/egress-destinations.yaml` declares `destinations: []` — the
   admissible set is **EMPTY, 0 registered destinations** — every service's `x-egress.hosts` is
   empty, and `CD-RT-012-EGRESS-NO-BROKER` exits `0` over **69 assertions**. **Its scope, stated
   honestly:** it carries the **pathway**, not the **dependency**, and it is a **WO-2-state fact
   that WO-3 will change** — the moment a destination is registered this carrier weakens by
   exactly that much. It is not a permanent property and must not be read as one.
5. **THE REGISTRY IS AN IN-TREE FILE AND A COMMIT MAY EDIT IT.** Registering a broker SDK is a
   two-line diff. That is the same residue the egress destination registry carries and it is the
   deliberate design: the structure makes the permission **explicit, attributed and reviewable at
   a named line**, not unforgeable. What it removes is the **silent** admission — which is exactly
   what F05 exercised, since `tastytrade-sdk` needed no registry edit and produced no diff anyone
   had to justify. **CARRIER MEASURED:** layer 2 over the registry refuses a registered
   `ib-insync` (`CD-DEP-002`) and a registered `meridian-fix-connect` on the `fix` token. **For a
   registered distribution layer 2 does not recognise, see boundary 1: NOT PROVED TO BE CARRIED
   ANYWHERE.**

Do not read a clean run of this check as proof that no dependency of this project can reach a
broker. Read it as proof of exactly three things: that every distribution in every declared
manifest was **registered** by somebody, with a purpose and a cited clause; that no registered or
manifest distribution is on the denylist or carries an execution token; and that the registry
holds no permission no manifest uses. It is **not** proof about boundaries 1, 2 or 5.

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

**A distribution nobody declared.** Any distribution named in any dependency manifest —
`pyproject.toml`, `requirements.txt`, `requirements.lock`, or any `requirements*.txt`, `*.lock` or
`constraints*.txt` the check finds — whose PEP 503 normalised name is not the `distribution` of a
registered entry in `deploy/dependency-registry.yaml`. It is refused **by default**, without
anything being recognised about it (`CD-DEP-001`). Also in the class: a **registered** distribution
on the denylist or carrying an execution token (`CD-DEP-002`); a registered distribution appearing
in no manifest (`CD-DEP-003`); a malformed registry entry, which registers nothing (`CD-DEP-005`);
and a missing or unparseable registry, which **refuses** rather than reading as empty.

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
