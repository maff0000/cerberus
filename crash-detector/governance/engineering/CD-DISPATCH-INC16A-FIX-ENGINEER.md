# CD-DISPATCH-INC16A-FIX-ENGINEER

**role source:** `pbg/roles/engineer.md` — read it; reading it does not grant the role
(`PBG-BOOT-001`), **this dispatch does**.
**authority record:** `CD-ASR-WO3-03`'s `RED` verdict at `b7f0439` (`BL-20260824T083556Z-A303`),
reconciled and reproduced by the Project Lead at `BL-20260824T084141Z-0160` ·
`PO-DECISIONS-0025` ruling 5 (`Q29`) and ruling 2 (portability, BINDING)
**seat identity:** `CD-ENG-WO3-04` — **FRESH.** Never `CD-ENG-WO3-01`, `-02`, **never
`CD-ENG-WO3-03` (which built the defect)**, **never `CD-ASR-WO3-03` (which found it —
`PBG-SOD-004`)**, never `CD-ASR-WO3-01`/`-02`, never any `CD-ENG-WO2R3-*`/`CD-ENG-COORD*`.
**issued by:** `PROJECT_LEAD_SEAT_02` · **increment:** 16A-FIX · **expected return:**
`READY_FOR_ASSURANCE`

---

## 0. WHAT THIS IS, IN ONE PARAGRAPH

Increment 16A was assured **`RED`** by an independent seat, **on `D2` and on `D2` alone**. The other
three deliverables PASSED and you do not touch them except where §4 names two gaps. **YOU ARE
CLOSING A REPRODUCED CONSTITUTIONAL BREACH AND NOTHING ELSE.** This is a small, exactly-specified
increment. **Its danger is not difficulty — it is that a plausible fix that does not actually close
the hole would be worse than no fix, because it would close the finding.**

---

## 1. THE LANE

```
branch    wo-3
worktree  /srv/crash-detector-wo3
tip       53f639a  (increment 16A — assured RED, banked, NOT accepted)
base      be0b355  (FROZEN — READ-ONLY. Build forward; never amend, rebase or move it.)
verdict   b7f0439 on branch asr-wo3-03-verdict — governance/engineering/build-log/BL-20260824T083556Z-A303.yaml
```

**WRITABLE SCOPE — DELIBERATELY NARROW, AND NARROWER THAN 16A'S:**
`contracts/public_envelope.schema.json` · `contracts/private_envelope.schema.json` ·
`tests/test_detail_level.py` · `tests/publication_fakes.py` ·
`src/crash_detector/publication/publish.py` · `src/crash_detector/publication/detail_level.py` ·
`deploy/check_portability.py` · `tests/test_deploy_portability.py` ·
`governance/engineering/build-log/**` for your own return record.

**IF YOU NEED A FILE THAT IS NOT ON THAT LIST, STOP AND SAY SO.** Do not widen your own scope —
`CD-PL-F173` is on the record because a seat wrote outside its scope, reverted it, and the clean tip
concealed it. **That seat disclosed it and was right to. Do not create the occasion.**

**PROTECTED — ZERO PATHS, PROVED BY COMMAND ON RETURN:** `pbg/**` · `BLUEPRINT.md` (`CD-D-115`) ·
`PID.md` (carried at 16A and correct — **do not re-carry it**) · `required-tests.yaml` (re-pinned at
16A and `MATCHES` — **touching it re-stales the pin**) · `governance/decisions/**` ·
`src/crash_detector/source_registry.py` and `engine/config.py` (D4 PASSED; leave it alone) ·
`tools/**` · everything at `be0b355`.

---

## 2. THE DEFECT, MEASURED TWICE — BY THE AUDITOR AND BY THE PROJECT LEAD

```
refuse_unless_publishable(envelope whose equity_crash is an UNKNOWN dial, surface=...)

  PUBLIC   detail_level="calm"      ->  ***ADMITTED***
  PUBLIC   detail_level="banana"    ->  REFUSED  [SCHEMA_VIOLATION] at /equity_crash
  PUBLIC   detail_level REMOVED     ->  REFUSED  [SCHEMA_VIOLATION] at /equity_crash
  PRIVATE  detail_level="calm"      ->  ***ADMITTED***

  contracts/*.schema.json  $defs.detail_level.enum  ->  ['calm','elevated','acute']
```

**PID §3.2 IS CONSTITUTIONAL: *"Missing data must never render as calm."*** With zero registered
sources **every dial is `UNKNOWN`**, so this is not an edge case — it is the only state the product
is currently capable of publishing.

**THE GATE IS WORKING.** It refuses a garbage value and refuses the field's absence. **It admits
precisely the one value the constitution forbids.**

### 2.1 Three things make it `RED` rather than a bug, and you must fix all three

1. **THE SCHEMA CLAIMS THE GUARANTEE IT DOES NOT HOLD.** `$defs.dial_reading`'s own description says
   *"required in every branch INCLUDING UNKNOWN … PID §3.2 is constitutional … and DetailPolicy
   REFUSES CONSTRUCTION when absent_data_level is calm."* **That delegates enforcement to a module
   the envelope never consults.** The same file holds `CD-AC-001` **in the schema** — `UNKNOWN`
   declares no `score` property at all, so an unknown dial carrying a number is *unrepresentable*.
   **THE PROJECT'S OWN PATTERN IS MET FOR ONE CONSTITUTIONAL CLAUSE AND MISSED FOR THE OTHER. MEET
   IT FOR BOTH.**
2. **THE ENFORCEMENT HAS NO CALLER.** `detail_level_for` has **zero real callers in `src/`** — the
   only two grep hits are its own docstring. And `tests/publication_fakes.py:119`'s `unknown_dial()`
   returns `"detail_level": "elevated"` **as a hardcoded literal**, with a comment asserting the very
   guarantee the code does not obtain.
3. **THE REPLACEMENT GUARD CANNOT SEE ITS OWN REMEDY.** The Project Lead applied the fix on a copy —
   narrowing the `UNKNOWN` branch's `detail_level` to `['elevated','acute']` on both contracts —
   and measured: **`calm` becomes REFUSED on both surfaces, AND all 43 `detail_level` tests STILL
   PASS.** *** **A GUARD THAT WOULD NEITHER REQUIRE NOR FORBID ITS OWN REMEDY IS NOT GUARDING THE
   THING IT IS NAMED FOR.** ***

---

## 3. `D2-FIX` — WHAT YOU BUILD

**F1 — MAKE `calm` UNREPRESENTABLE ON THE BRANCHES THAT CARRY MISSING DATA.** On **both** closed
contracts, `UNKNOWN` **and** `DEGRADED` must be unable to carry `calm` **in the schema itself**, the
way `CD-AC-001` is already held. `VALUE` keeps the full vocabulary — a genuinely calm reading with a
real number is the whole point of `calm` existing.

**Two things you must decide and justify rather than guess** (`PBG-AUTH-005` — implementation is
yours, product meaning is not):

* `DEGRADED` carries a score *and* its damage. `detail_level_for` already returns
  `policy.absent_data_level` for it, so **the code already treats it as missing-data**. Confirm that
  by reading the function, then make the contract agree. **If you conclude `DEGRADED` should keep
  `calm`, say so with your reasoning and do not change it** — a wrong narrowing is as bad as the
  hole.
* Whether you narrow with a per-branch `enum` or a separate `$defs` type. **A named type
  (`absent_data_detail_level`) says what it means at every use site; an inline enum says it once.**
  Your call. Justify it.

**F2 — THE GUARD MUST FAIL WHEN F1 IS REVERTED.** Add the arm the current guard does not have: on a
**mutated copy**, restore `calm` to the `UNKNOWN` branch — **the test MUST FAIL.** Do the same for
`DEGRADED` if you narrow it. **THIS IS THE DELIVERABLE THAT MAKES F1 STICK. F1 WITHOUT F2 IS A FIX
THAT THE NEXT REFACTOR SILENTLY UNDOES.**

**F3 — RE-POINT THE TEST THAT IS NAMED FOR PID §3.2 AT PID §3.2.**
`test_the_UNKNOWN_branch_carries_a_level_and_that_is_the_constitutional_half` is headed *"PID §3.2"*
and asserts only that `score` is absent and `detail_level` is required. **NAMED FOR THE CLAUSE; DOES
NOT TEST THE CLAUSE.** Make it assert the constitutional thing: **an `UNKNOWN` dial carrying `calm`
is REFUSED by `refuse_unless_publishable`, on both surfaces.** *** **AND MAKE IT AN END-TO-END
BEHAVIOURAL ASSERTION THROUGH THE LIVE GATE, NOT A STRUCTURAL ASSERTION ABOUT SCHEMA KEYS. THE
STRUCTURAL ASSERTIONS ARE WHAT LET THIS THROUGH TWICE.** ***

*** **THIS PATTERN NOW HAS THREE RECORDED INSTANCES — `CD-PL-F169`, `CD-ASR-WO3-02` F06/F07, and
this one — AND THIS PROJECT HAS NO CONTROL FOR IT. WHILE YOU ARE IN `tests/test_detail_level.py`,
READ EVERY TEST NAME IN IT AND ASK WHETHER ITS ASSERTIONS DELIVER WHAT ITS NAME CLAIMS. REPORT WHAT
YOU FIND EVEN IF YOU DO NOT FIX IT.** ***

**F4 — THE FAKE MUST NOT HARDCODE THE ANSWER.** `unknown_dial()` should get its level the way real
code would, or — if wiring `detail_level_for` into a test fake is the wrong shape — **say so and
leave a literal that cannot be `calm` by construction**, with the reason recorded. Do not leave a
comment asserting a guarantee the code does not obtain; that is what got us here.

**F5 — SUPERSEDE `publish.py`'s DECLARED LIMIT 2.** It reads *"`detail_level` IS NOT ON EITHER
SURFACE AND IS NOT WRITTEN BY THIS MODULE."* Since 16A it **is** on both contracts. **CORRECT IT BY
SUPERSESSION, NEVER BY DELETION** — say what it said, that it is now false, and what is true
instead: the key is in the contract, and `publish_cycle` still has **zero callers**, so the field
still reaches no surface. **DO NOT WRITE THE CALLER.** The health surface's value axis is still open
and blocks the moment any transport is written; that residual and `CD-PL-F167` must land together
and neither may land alone.

---

## 4. `D3-FIX` — TWO GAPS, BOTH REPRODUCED BY THE PROJECT LEAD

Same class as the `RED`: **a check whose name claims more than its assertions deliver.** Both pass
today with `PASS — 1072 assertions, 0 violations`:

| Gap | Planted | Result |
|---|---|---|
| **A** | `CD_CONTRACTS_DIR: "${CD_CONTRACTS_DIR:-/srv/crash-detector/dell-only/contracts}"` | **PASS, exit 0** — rule 5 stops at the `${` prefix and never inspects the default |
| **B** | `CD_STORE_HOST: postgres.dell.matt.local` (was `cd-store`) | **PASS, exit 0** — the key is allowlisted as "a compose service name" and nothing checks the value is one |

**FIX BOTH.** Rule 1 must reach inside `${VAR:-DEFAULT}` and judge the default as it would judge a
literal. The service-name allowlist must **verify the value is actually a service declared in this
very file**, not merely that the key is on a list. **The auditor proved gap B's probe live by noting
an IPv4 in the *same* key IS caught — so the rule fires, it just cannot see a hostname.**

**BOTH ARMS FOR EACH, ON `/tmp` COPIES, NEVER IN THE REAL FILE** (`CD-PL-F154`). And re-run the
clean arm: **it must still exit 0 on the real file.** A fix that makes the real subject fail is not a
fix.

---

## 5. YOUR ACCEPTANCE TEST — THE PROJECT LEAD'S OWN PROBE, RUN BY YOU

```python
# On BOTH surfaces, for an UNKNOWN dial:
#   detail_level="calm"      MUST be REFUSED        <- today: ADMITTED. This is the fix.
#   detail_level="elevated"  MUST be ADMITTED       <- the non-vacuity arm
#   detail_level="banana"    MUST be REFUSED        <- the probe is live
#   detail_level REMOVED     MUST be REFUSED        <- presence still required
```

**PASTE THE OUTPUT OF THAT PROBE, ALL FOUR ROWS, BOTH SURFACES, IN YOUR RETURN.** *** **AND THE
SECOND ARM MATTERS AS MUCH AS THE FIRST: IF `elevated` STOPS BEING ADMITTED YOU HAVE NOT FIXED THE
HOLE, YOU HAVE CLOSED THE BRANCH. A CONTRACT THAT REFUSES EVERY UNKNOWN DIAL SATISFIES PID §3.2
VACUOUSLY AND BREAKS THE ONLY STATE THIS PRODUCT CAN CURRENTLY PUBLISH.** ***

---

## 6. WHAT IS NOT IN THIS INCREMENT

`Q30` (the mapping content) · `Q31` (Redis) · `Q32` (the staleness ceiling — **and note the auditor
made it sharper: the store schema already separates liveness from relevance, no code reads the
liveness half, so the staleness window is currently the ONLY dead-feed detector and widening the
ceiling would silently delete it. That is the Product Authority's and NOT yours**) · any indicator
row · any `MappingKind` member · the `src/` entrypoint or the `publish_cycle` caller · `D1` and `D4`,
which PASSED · anything under `pbg/`, including `CD-PL-F171`.

---

## 7. YOUR RETURN

**BOOT FIRST** and declare the verdict you get, including a `RED` inherited from the frozen base's
`ACTIVE_WORK.yaml` — known, outside your scope, diagnose and do not repair.

Required: the §5 probe output in full, both surfaces, all four rows · every guard arm with its
**failing** arm demonstrated on a mutated copy · `D3`'s two gaps with both arms **and** the clean arm
still at exit 0 · the full test count before and after (**no regression from 1990**) · the register
verifier still `MATCHES` / 18 / `GATE: SHUT` (**you did not touch it; prove you did not**) · a scope
proof by command over every protected path · **ONE commit identity**, verified by
`git log --format='%an' 53f639a..HEAD | sort -u` · **your declared limits (`CD-RULE-004`)** · and
**your findings against this dispatch.**

**Every claim about code backed by a command whose output you paste.** `CD-PL-F170` names the
pattern five times on this project — *a partial measurement promoted to a confident statement about
code and placed in a binding record*. **Read the whole file. Run the probe. Then write the sentence.**

**Commit identity — `git -c user.name=` DOES NOT WORK on this host:**
```
GIT_AUTHOR_NAME=CD-ENG-WO3-04 GIT_AUTHOR_EMAIL=cd-eng-wo3-04@seats.crash-detector.invalid \
GIT_COMMITTER_NAME=CD-ENG-WO3-04 GIT_COMMITTER_EMAIL=cd-eng-wo3-04@seats.crash-detector.invalid \
git commit -m "..."
```

**COMMIT AT EVERY BOUNDARY** (`PBG-CONT-007`). **YOU DO NOT CERTIFY YOUR OWN WORK** — a separate
fresh Assurance seat follows (`PBG-SOD-001`, non-waivable).

**STOP AND RETURN — do not improvise — if:** the fix requires a file outside §1's scope · it requires
a `BLUEPRINT` or `PID` change · narrowing `DEGRADED` turns out to be wrong · you cannot make
`elevated` stay admitted while `calm` is refused · or you find any statement in this dispatch to be
false. **THE LAST ONE HAS HAPPENED ON FOUR OF THE LAST SIX DISPATCHES AND THE SEAT WAS RIGHT EVERY
TIME.**
