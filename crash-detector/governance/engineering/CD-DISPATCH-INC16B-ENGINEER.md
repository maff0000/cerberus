# CD-DISPATCH-INC16B-ENGINEER

**role source:** `pbg/roles/engineer.md` — read it; reading it does not grant the role
(`PBG-BOOT-001`), **this dispatch does**.
**authority record:** `PO-DECISIONS-0026` **ruling 9** (the constitutional fix must be
REGISTER-WIRED, not test-only) and **ruling 7** (increment 16B, sequential single-seat, in the
ruled order — this is item (i) of that order and **nothing else**) · commit `2caa2d7` on `main`,
authored by Matt Scott and by no seat · carried onto this lane verbatim at `20fd1e1`
· `CD-ASR-WO3-04`'s finding **F2**, reproduced by the Project Lead at this dispatch's §2.
**seat identity:** `CD-ENG-WO3-05` — **FRESH.** Never `CD-ENG-WO3-01`/`-02`/`-03`, **never
`CD-ENG-WO3-04` (which built the fix you are now wiring)**, **never `CD-ASR-WO3-04` (which found
F2 — `PBG-SOD-004`)**, never `CD-ASR-WO3-01`/`-02`/`-03`, never any `CD-ENG-WO2R3-*` or
`CD-ENG-COORD*`.
**issued by:** `PROJECT_LEAD_SEAT_02` · **increment:** 16B · **expected return:**
`READY_FOR_ASSURANCE`

---

## 0. WHAT THIS IS, IN ONE PARAGRAPH

16A-FIX closed a constitutional breach and closed it correctly — an independent seat proved that
behaviourally. **But the guarantee it obtained is carried by nothing that the gate reads.** You are
not fixing the constitution again; it is already fixed. **You are making the fix IMPOSSIBLE TO
SILENTLY UNDO**, by building a live instrument the register names and proving by contrast that it
actually discriminates. **The whole danger of this increment is building an instrument that passes
on the clean tree and looks like assurance while discriminating nothing** — which is precisely the
defect you are here to close, rebuilt one level up.

---

## 1. THE LANE

```
branch    wo-3
worktree  /srv/crash-detector-wo3
tip       20fd1e1  (Project Lead record act — PO-DECISIONS-0026 + the mapping carried, verbatim)
prev      b9283b9  (increment 16A-FIX — assured AMBER at 3464956, banked, NOT accepted)
base      be0b355  (FROZEN — READ-ONLY. Build forward; never amend, rebase or move it.)
verdict   3464956 on branch asr-wo3-04-verdict — BL-20260824T093704Z-A304.yaml
ruling    governance/decisions/PO-DECISIONS-0026.md  (IN YOUR TREE as of 20fd1e1 — read it)
```

**WRITABLE SCOPE — NARROW, AND DELIBERATELY SO:**

* `tools/register/check_missing_data_never_calm.py` — **NEW**, the instrument (name is a
  suggestion; if you choose another, say why)
* `contracts/execution/CD-RT-001-MISSING-DATA-NEVER-CALM.md` — **NEW**, its execution contract
* `required-tests.yaml` — **ONLY** the `tests:` list of `CD-AC-001` and the commentary immediately
  around your new entry. See §5 for what inside that file is protected.
* `plants/WO3-INC16B/**` — **NEW**, the contrast set and its `MANIFEST.md`
* `plants/MANIFEST.md` — the top-level index only, if it enumerates directories
* `tests/test_detail_level.py` — **only** for §4 D3, and only additively
* `governance/engineering/build-log/**` — your own return record

**IF YOU NEED A FILE THAT IS NOT ON THAT LIST, STOP AND SAY SO.** Do not widen your own scope.
`CD-PL-F173` is on the record because a seat wrote outside its scope, reverted it, and the clean
tip concealed it. **That seat disclosed it and was right to. Do not create the occasion.**

**PROTECTED — ZERO PATHS, PROVED BY COMMAND ON RETURN:** `pbg/**` · `BLUEPRINT.md` (`CD-D-115`) ·
`PID.md` · `governance/decisions/**` · `governance/mapping/**` · **`contracts/public_envelope.schema.json`
and `contracts/private_envelope.schema.json` — 16A-FIX narrowed them and an independent seat proved
the narrowing correct; *your instrument judges them, it does not touch them*** · `src/**` ·
`deploy/**` · `db/**` · `tools/**` except your one new file · everything at `be0b355`.

---

## 2. THE DEFECT, REPRODUCED BY THE PROJECT LEAD — NOT INHERITED FROM THE VERDICT

Extraction: `git archive b9283b9 | tar -x -C /tmp/rev16b`. One mutation, applied to **both**
contracts: every `"$ref": "#/$defs/absent_data_detail_level"` restored to
`"#/$defs/detail_level"` — **2 occurrences per file, 4 in total. That is the complete revert of
16A-FIX's constitutional narrowing.** Then every register instrument, run verbatim:

```
check_base_image_digest_pin.py                exit=0   PASS — 13 assertions, 0 violations
check_constructor_field_establishment.py      exit=0   PASS — 113 assertions, 0 violations
check_dockerignore.py                         exit=0   PASS — 22 assertions, 0 violations
check_egress_no_broker.py                     exit=0   PASS — 69 assertions, 0 violations
check_engine_no_witness_reach.py              exit=0   PASS — 28 assertions, 0 violations
check_exact_type_admission.py                 exit=0   PASS — 36 assertions, 0 violations
check_grant_matrix_live.py                    exit=3   PRECONDITION_NOT_MET (no store reachable —
                                                       IDENTICAL on the clean tree; discriminates nothing here)
check_judgement_path_doors.py                 exit=0   PASS — 72 assertions, 0 violations
check_lockfile_denylist.py                    exit=0   PASS — 134 assertions, 0 violations
check_no_blend.py                             exit=0   PASS — 9078 assertions, 0 violations
check_no_execution_interface.py               exit=0   PASS — 79678 assertions, 0 violations
check_no_numeric_default.py                   exit=0   PASS — 552 assertions, 0 violations
check_schema_closed.py                        exit=0   PASS — 266 assertions, 0 violations
check_sealed_against_forged_establishment.py  exit=0   PASS
```

*** **EVERY RUNNABLE REGISTER-WIRED INSTRUMENT PASSES ON A TREE WHERE THE CONSTITUTIONAL
GUARANTEE IS FULLY REVERTED.** ***

And on the same reverted tree:

```
python3 -m pytest tests/ -q   ->   9 failed, 1998 passed
```

**All nine failures are in `tests/test_detail_level.py`, and no register entry executes that
file.** MEASURED: the register declares 29 `execute:` lines; 15 name `tools/…` instruments and 14
name `pytest` files. `tests/test_detail_level.py` is **not one of the 14.**

**SO THE PO'S RULING 9 IS EXACT, AND SHARPER THAN IT NEEDED TO BE.** The constitutional guarantee
lives in one test file that the gate does not run, behind a wall of instruments that cannot see it
go. **A memorial, not a guard.**

---

## 3. THE ONE THING YOU MAY NOT DO

**DO NOT FIX THIS BY DELETING OR WEAKENING ANYTHING.** The schemas are right. The tests are right.
**You are adding an instrument, wiring it, and proving it bites.** If at any point your change makes
the clean tree fail, or makes `elevated` stop being admitted on an UNKNOWN dial, **you have not
wired a guard, you have broken the only state this product can currently publish.**

---

## 4. WHAT YOU BUILD

### D1 — THE INSTRUMENT (the deliverable; everything else serves it)

A register instrument in this project's house pattern (`--root .`, enumerates and prints its
assertion count, prints violations, **non-zero exit on violation, and never a skip** —
`PBG-CI-002`).

**IT MUST BE BEHAVIOURAL WHERE IT CAN BE, NOT MERELY STRUCTURAL.** A structural read of schema keys
is exactly what let this class through twice (`CD-PL-F169`, `CD-ASR-WO3-02` F06/F07, `CD-ASR-WO3-03`).
**Register instruments on this project ARE permitted to import the application** — MEASURED: four of
them already do (`check_exact_type_admission`, `check_engine_no_witness_reach`,
`check_no_numeric_default`, `check_judgement_path_doors`). *(The "probe must not import the
application" rule is `CD-RT-014`'s, and it binds `tools/probe/external_probe.py` only — an external
probe must be external. It does not bind you.)* **So drive the live gate.**

The proposition it must hold, on **both** surfaces:

```
refuse_unless_publishable( envelope with an UNKNOWN dial, detail_level="calm"     )  MUST REFUSE
refuse_unless_publishable( envelope with a  DEGRADED dial, detail_level="calm"    )  MUST REFUSE
refuse_unless_publishable( envelope with an UNKNOWN dial, detail_level="elevated" )  MUST ADMIT
refuse_unless_publishable( envelope with an UNKNOWN dial, detail_level="acute"    )  MUST ADMIT
refuse_unless_publishable( envelope with a  VALUE   dial, detail_level="calm"     )  MUST ADMIT
```

*** **THE LAST THREE ROWS ARE NOT DECORATION — THEY ARE THE ANTI-VACUITY ARMS AND THEY MATTER AS
MUCH AS THE FIRST TWO.** An instrument that only checks "calm is refused" is satisfied by a contract
that refuses everything, and by a contract in which no dial can ever read calm at all. **Assert what
must still be ADMITTED, in the instrument itself, or the instrument is a mute button with a
certificate.** ***

### D2 — WIRE IT INTO THE REGISTER

Add it as a test under **`CD-AC-001`**, whose criterion text is literally *"Missing or stale input
never renders as calm."* — the home is not a judgement call. Follow the two entries already there:
`test_id` · `scope` · `execute` · `execution_contract` · `negative_control.violation` ·
`negative_control.evidence_ref`. **Write the DECLARED LIMIT comment above it (`CD-RULE-004`) — what
your instrument does NOT catch, with an example an auditor can execute.** Every other entry in that
file carries one; an entry without one is the claim that you found no limit, which nobody will
believe and which would be a finding against you.

*** **DISCLOSE THIS AND DO NOT ENGINEER AROUND IT.** Your new row **will compute `UNDECIDABLE`**,
because `negative_control.evidence_ref` must name a run record that does not exist — MEASURED: all
18 criteria are `UNDECIDABLE` today for exactly this reason, and `GATE: SHUT`. **THAT IS CORRECT.**
The Engineer does not produce or admit its own run record (`PBG-SOD-001`, non-waivable). Register-wiring
makes the guarantee *machine-checkable and gate-visible*; it does not make it *computed*. **Say so
in plain words in your return.** If you find yourself creating a file under
`evidence/required-tests/runs/`, **stop — you are forging assurance.** ***

### D3 — GROW `CD-RT-001-ABSENCE-RENDERS-UNKNOWN`'s DECLARED COMMAND, ADDITIVELY

`tests/test_detail_level.py` holds nine assertions of the constitutional clause and **the register
runs none of them.** Add that file to the existing `execute:` line for
`CD-RT-001-ABSENCE-RENDERS-UNKNOWN`. **This is precedent, not invention:** the same entry's command
GREW by `tests/test_dial_presentation.py` at WO-2R2 increment 1c, and its own comment records that
*"nothing was removed from the command"*. **Remove nothing. Reorder nothing.** Update that comment
to say what grew and why, in the form it already uses.

**D3 IS SECONDARY AND MUST NOT BE OFFERED AS D1.** The PO ruled the guarantee must be carried by
*"a live instrument, not a memorial in tests"*. D3 stops the memorial being unread; **D1 is the
guard.** If D3 turns out to be wrong — if adding that file to a `CLASS`-scoped runtime entry
misstates what that entry evidences — **say so with your reasoning and do not do it.**

### D4 — THE CONTRAST SET (this is how you prove D1 is not theatre)

Under `plants/WO3-INC16B/`, with a `MANIFEST.md` in the established table form: `git apply`'s **own
exit code as its own column** (a patch that silently stops applying yields a "violated" arm that is
just the clean tree — `CD-ENG-WO2R3-06-F06`), each arm from **its own pristine
`git archive <tip> | tar -x -C /tmp` extraction**, **never applied to the worktree** (`CD-PL-F154`).

**Your instrument MUST exit non-zero on every one of these:**

| # | The plant | What it catches |
|---|---|---|
| **C1** | The full revert of §2 — all four `$ref`s back to `#/$defs/detail_level` | the baseline hole. **Today every register instrument passes this.** |
| **C2** | Revert **one branch on one surface only** (e.g. `DEGRADED`, public) | an instrument that asks "is there a narrowing?" instead of "is EVERY missing-data branch on EVERY surface narrowed?" |
| **C3** | Keep the `$ref`s; add `"calm"` back **into the `absent_data_detail_level` enum** | an instrument that reads the `$ref` target's NAME and never opens it |
| **C4** | Narrow **`VALUE`** as well, so no dial can ever read `calm` on any branch | *** **THE VACUITY ARM.** An instrument that passes this is not guarding PID §3.2, it is enforcing silence. `calm` on a real number is the entire reason `calm` exists. *** |

**C4 IS THE ONE THIS PROJECT'S HISTORY SAYS YOU WILL GET WRONG.** Every previous instance of this
class was a guard that could not distinguish "the forbidden thing is impossible" from "everything is
impossible."

**If you can construct one, add C5: a route by which the live gate admits a calm UNKNOWN dial with
both schemas fully intact** — a validation path that never reaches the branch. If you cannot, **say
you could not, and say what that leaves uncovered.** Do not report an arm you did not run.

### D5 — THE NON-VACUITY ARM ON THE REAL TREE

The instrument **must exit 0 on the clean worktree**, and `pytest tests/ -q` must be **2007 passed,
0 failed** — MEASURED at `b9283b9` and unchanged by anything in your scope. **A fix that makes the
real subject fail is not a fix.**

---

## 5. WHAT IS PROTECTED *INSIDE* `required-tests.yaml`

You are writing in a file that is pinned. **Do not touch:**

* the `pid:` block and its `content_hash: sha256:08baf51ca5a34b4e15be11b4ffe3e4e5ac271291247ace7e8fcabb7b0e8dab9f`
* `latest_admitted_run: null` — **not yours to fill in, ever**
* any `criterion_id`, `criterion:`, `obligation:`, `origin:` or `pid_relation:` — **the census is
  derived from PID §6 and you may not add, remove or reword a criterion.** You are adding a TEST
  under an existing criterion, which is a different act.
* every other criterion's entries

**PROVE ON RETURN** that `pid.content_hash` still reads `MATCHES`, that the criterion count is still
**18**, and that the gate is still **SHUT**:

```
PYTHONPATH=/srv/crash-detector/pbg/tools python3 -B -m pbg.cli required-tests verify --register required-tests.yaml
```

**A run that turns anything green is a run you must stop and report, not bank.**

---

## 6. WHAT IS NOT IN THIS INCREMENT

Ruled items **2 through 6 of `PO-DECISIONS-0026` ruling 7 are 16C and later, and are NOT YOURS:**
the three-quantity liveness/relevance/publish model and `STALENESS_WINDOW_CEILING_SECONDS` (**do not
touch that constant — deleting the only dead-feed detector to widen a window is the exact error the
PO's ruling 5 exists to prevent**) · the structural closure of the no-blend guard · the host-coupling
defaults · the version discrimination (`schema_version` / the `1.1.0` URN — **F1 is real and it is
16D; leave the `$id` alone**) · **registering any indicator row from `governance/mapping/indicator_mapping.yaml`,
which is 16E** · the `publish_cycle` caller · anything under `pbg/`.

**The mapping file is in your tree so that the authority record is readable, and for no other
reason. Register nothing.**

---

## 7. YOUR RETURN

**BOOT FIRST** and declare the verdict you get, including any `RED` inherited from the frozen base's
`ACTIVE_WORK.yaml` — known, outside your scope, **diagnose and do not repair**.

Required, each backed by a command whose output you paste:

1. The five-row §4 D1 proposition table, **both surfaces**, from your instrument's own run.
2. **Every C-arm**: `git apply` exit code, clean-arm result, violated-arm result. **C4 explicitly.**
3. The instrument at exit **0** on the clean worktree.
4. `pytest tests/ -q` before and after — **no regression from 2007**.
5. The register verifier: `pid.content_hash MATCHES` · **18** criteria · `GATE: SHUT` ·
   `latest_admitted_run (null)`.
6. A scope proof by command over **every** protected path in §1 and §5.
7. **ONE commit identity**, verified by `git log --format='%an' 20fd1e1..HEAD | sort -u`.
8. **Your declared limits (`CD-RULE-004`)** — what your instrument does not catch.
9. **Your findings against this dispatch.**

**Every claim about code backed by a command whose output you paste.** `CD-PL-F170` names the
pattern on this project repeatedly — *a partial measurement promoted to a confident statement about
code and placed in a binding record.* **Read the whole file. Run the probe. Then write the sentence.**

**Commit identity — `git -c user.name=` DOES NOT WORK on this host:**
```
GIT_AUTHOR_NAME=CD-ENG-WO3-05 GIT_AUTHOR_EMAIL=cd-eng-wo3-05@seats.crash-detector.invalid \
GIT_COMMITTER_NAME=CD-ENG-WO3-05 GIT_COMMITTER_EMAIL=cd-eng-wo3-05@seats.crash-detector.invalid \
git commit -m "..."
```

**COMMIT AT EVERY BOUNDARY** (`PBG-CONT-007`). **YOU DO NOT CERTIFY YOUR OWN WORK** — a separate
fresh Assurance seat follows (`PBG-SOD-001`, non-waivable).

**STOP AND RETURN — do not improvise — if:** the instrument needs a file outside §1 · it needs a
`PID` or `BLUEPRINT` change · you cannot make C4 fail without also breaking D5 · adding a test row
moves `pid.content_hash` off `MATCHES` or moves the criterion count off 18 · D3 turns out to
misstate what `CD-RT-001-ABSENCE-RENDERS-UNKNOWN` evidences · **or you find any statement in this
dispatch to be false. THAT LAST ONE HAS HAPPENED ON FOUR OF THE LAST SIX DISPATCHES AND THE SEAT
WAS RIGHT EVERY TIME.**
