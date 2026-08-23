# CD-DISPATCH-INC15-ASSURANCE

**role source:** `pbg/roles/assurance-engineer.md` · **seat identity:** `CD-ASR-WO3-02` — **FRESH.**
Never `CD-ENG-WO3-01`, never `CD-ENG-WO3-02`, never `CD-ASR-WO3-01`. The Engineer and the Assurance
Engineer are never the same agent (`PBG-SOD-001`, **non-waivable**).
**authority record:** `PO-DECISIONS-0024` rulings 2 and 3 · boundary `BL-20260823T190920Z-0155`
**expected return:** `PASS` / `AMBER` / `RED` **with the next safe gate named.**

---

## 1. TARGET

| | |
|---|---|
| **subject SHA** | `116c01f4584c62a244910ac6676c030735596896` |
| **branch / worktree** | `wo-3` · `/srv/crash-detector-wo3` |
| **prior assured tip** | `9b09d2a` (increment 14, `PASS` — `governance/assurance/CD-ASR-WO3-01-VERDICT.md`) |
| **base** | `be0b355` — **FROZEN, read-only to you** |
| **the claim** | *"Group C is built — publication with per-surface closed-schema validation before write, a heartbeat writer, an external probe outside the container set, regime-aware staleness, a public-safe health surface, and `Q26`-compliant alert surfacing with NO external push — and increment 14's register is not regressed."* |

**EXTRACT THE SUBJECT YOURSELF** (`git archive 116c01f | tar -x -C <your tmpdir>`). Do not audit the
Engineer's working tree. **Do not verify through any harness this project wrote** (`PBG-ASSURE-001`)
— note that the test suite **is** such a harness: a passing suite is evidence about the suite unless
you check what the tests actually assert.

---

## 2. WRITE SCOPE — **NARROW, AND DELIBERATELY NOT ZERO**

**You may write EXACTLY ONE governance file:
`governance/assurance/CD-ASR-WO3-02-VERDICT.md`** on `main`, plus your own `/tmp` scratch.

> **WHY THIS DIFFERS FROM THE LAST ASSURANCE DISPATCH.** `CD-DISPATCH-INC14-ASSURANCE` prohibited
> **all** governance writes while `pbg/roles/assurance-engineer.md` **requires** the seat to persist
> its verdict (`PBG-CONT-007`). **That dispatch ordered a seat to breach a non-waivable rule.**
> `CD-ASR-WO3-01` handled it correctly — obeyed, declared the conflict, returned unpersisted — and
> the Project Lead raised **`CD-PL-F163`** against itself for it. **This grant is that finding's
> remedy.** Commit it as `CD-ASR-WO3-02` using `GIT_AUTHOR_*`/`GIT_COMMITTER_*` env vars
> (`git -c user.name=` does not work here).

**EVERYTHING ELSE IS READ-ONLY:** no lane commits, no branch moves, no edits to `src/`, `tests/`,
`required-tests.yaml`, `pbg/`, or any other governance file. **If you think something must change,
that is a finding, not an act.**

---

## 3. WHAT TO GRADE

1. **Increment 14 not regressed.** Register still validates, **18 statuses computed**,
   `latest_admitted_run` **still `null`**, gate **`SHUT`**. **A validation failure is a RED.**
2. **Register edit narrowness.** `CD-AC-002` and `CD-AC-005` rows **untouched**; no rows added,
   removed or renumbered; **no `execution_contract` pointed at a non-existent file** (a non-resolving
   path silently forces `UNDECIDABLE` and **skips negative-control evaluation** —
   `required_tests.py:659-663`).
3. **C1 — two envelopes, each validated against ITS OWN closed schema BEFORE the write.** Check the
   **order**: validation after the write is not this. Check there are genuinely **two** schemas.
4. **C2 — the heartbeat writer exists and cadence ≠ age.** The Engineer claims
   `evaluate_cadence(heartbeats_utc)` has **no parameter through which an age could arrive**.
   **Verify that by introspection, and then try to defeat it** — is there a module-level or
   closure route by which an age reaches the cadence decision anyway?
5. **C3 — the probe is genuinely OUTSIDE the container set.** Not a compose service, no Dockerfile,
   imports nothing from `crash_detector`, no DB credential, no SQL. **Run it against a live socket
   and then kill the socket: it must still return a verdict.** A probe that dies with the thing it
   watches has reported nothing (`PBG-EVID-001`, `PBG-DEPLOY-002`).
6. **C4 — regime-aware staleness.** The same age that passes in calm must fail in stress.
7. **C5 — the health surface is PUBLIC-SAFE.** *** **TRY TO GET A VALUE OUT OF IT.** *** A dial
   value, witness reading, source name or private-envelope key on the health surface is a
   `CD-AC-006` breach wearing an ops hat. Degraded state must be explained by **CLASS, never
   VALUE**. **This is the highest-yield place to attack in this increment — attack it.**
8. **C6 / `Q26` — NO EXTERNAL PUSH EXISTS.** Not disabled, not flagged, **not present**. No
   `urllib`/`socket`/`http`/`smtplib`/`requests` import on any `src/` publication path.
   `deploy/egress-destinations.yaml` **unmodified**. `alert.event` rows written **first** and
   **durably**; the table is **append-only** — verify no UPDATE/DELETE route was opened.
9. **NO SOURCE REGISTERED** — not one row, not a placeholder, **not a fixture** (`Q25` is Matt's).
   **The Engineer disclosed one `INSERT INTO raw.source_registry` string inside an `ast.parse(...)`
   at `tests/test_publication_layer.py:405`, in a vacuity guard. VERIFY IT IS PARSED AND NEVER
   EXECUTED.**
10. **`CD-AC-002` / `CD-AC-005` did not move.** And **no blending**: no single expression consuming
    both dial types. **No route from `Unavailable` to `Agrees`** — a publication layer is exactly
    where an absent witness gets quietly rendered as agreement. **Look for it.**
11. **Containment:** one identity from `9b09d2a`, porcelain empty, `wo-2r3` still `be0b355`,
    `pbg/` byte-identical at tip/base/`main`, `PID.md`/`BLUEPRINT.md`/`governance/decisions/`
    untouched.
12. **THE TEN PLANTS ARE NON-VACUOUS.** Re-apply them yourself in pristine extractions. The Engineer
    added a **failing-test-names** column on the reasoning that *"exit 1 proves the command failed,
    not that it failed for the planted reason — a plant that broke an import would look identical."*
    **TEST THAT REASONING: does each violated arm fail on exactly the tests carrying its
    proposition, or does any of them fail for an incidental reason?**

---

## 4. GRADE THE PROJECT LEAD TOO

- **`Q29` / the Engineer's `F03`:** `detail_level` is built and **reaches no surface**. Verify it is
  genuinely unwired, that a test **enforces** its absence from both schemas, and that the boundary's
  account is accurate. **Is stopping here defensible, or is it an unfinished deliverable dressed as
  a question?** Say which.
- **`CD-PL-F165`:** the Project Lead's dispatch §3 asserted "C4 is an extension, not a greenfield"
  and the Engineer measured that all six `regime` mentions were prose. **Confirm or refute.**
- **Was `PBG-CONT-003` honoured** across `BL-...-0152`/`0153`/`0154`/`0155` — **superseded, never
  edited**? Check the git history of each.
- **Does `BL-...-0155` overstate anything?** It is generous about this Engineer. **If the record
  claims more than was measured, that is the finding this project values most.**

---

## 5. RETURN

`PASS` / `AMBER` / `RED`, **with the next safe gate named**, plus every command and **what it
actually printed**, findings with severities and measurements, and **anything you could not verify
stated as UNVERIFIED rather than assumed**.

**Do not grade on the Project Lead's summary or the Engineer's return. GRADE ON WHAT YOU RUN.**
