# WO-3 INCREMENT 16B — THE CONTRAST SET FOR `CD-RT-001-MISSING-DATA-NEVER-CALM`

**Written by `CD-ENG-WO3-05`** under `governance/engineering/CD-DISPATCH-INC16B-ENGINEER.md` §4 D4,
authority `PO-DECISIONS-0026` ruling 9.

**Nothing in this directory is evidence, and nothing in it is assurance.** The patches exist so
that every claim this increment makes is measured **by contrast** rather than asserted from one
side. They are **never applied to the worktree**: each arm below ran in its own throwaway
`git archive | tar -x` extraction under `/tmp`, and the worktree was never mutated (`CD-PL-F154`).

---

## WHY THIS SET EXISTS AND WHY IT IS NOT THE USUAL SHAPE

`16A-FIX` closed a constitutional breach — PID §3.2, *"Missing data must never render as calm"* —
by narrowing the `DEGRADED` and `UNKNOWN` branches of both envelope contracts to
`#/$defs/absent_data_detail_level`. An independent Assurance seat proved that behaviourally.
**Nothing the register read would have noticed if it were undone.**

`C1` below is that undoing, and the table under *"AND WHAT THE REST OF THE REGISTER SAYS ABOUT
THE SAME TREE"* is the whole reason this increment happened.

`C4` is the arm that decides whether the new instrument is a guard or a mute button, and the
dispatch said so in advance: *"C4 IS THE ONE THIS PROJECT'S HISTORY SAYS YOU WILL GET WRONG.
Every previous instance of this class was a guard that could not distinguish 'the forbidden
thing is impossible' from 'everything is impossible.'"*

---

## THE ARMS, AS MEASURED AT TIP `fec0a8e`

Each arm from **its own pristine `git archive fec0a8e | tar -x -C /tmp/...` extraction**.
`git apply`'s **own exit code** is recorded as its own column, because *a patch that does not
apply produces a "violated" arm that is just the clean tree* — the defect `CD-ENG-WO2R3-06-F06`
recorded when a plant silently stopped applying, and this project's established form since.

**The declared command, run verbatim on both arms of every row, is the register's own:**

```
python3 tools/register/check_missing_data_never_calm.py --root .
```

| # | Plant | `git apply` | CLEAN | VIOLATED | violated-arm result | assertion that caught it |
|---|---|---|---|---|---|---|
| **C1** | `C1-FULL-REVERT-OF-16A-FIX.patch` | **0** | **0** | **1** | `FAIL — 8 violation(s)` | `CD-CALM-GATE-001` × 8 |
| **C2** | `C2-ONE-BRANCH-ONE-SURFACE-DEGRADED-PUBLIC.patch` | **0** | **0** | **1** | `FAIL — 2 violation(s)` | `CD-CALM-GATE-001` × 2 |
| **C3** | `C3-CALM-BACK-INSIDE-THE-ABSENT-ENUM.patch` | **0** | **0** | **1** | `FAIL — 8 violation(s)` | `CD-CALM-GATE-001` × 8 |
| **C4** | `C4-VACUITY-NO-DIAL-MAY-EVER-READ-CALM.patch` | **0** | **0** | **1** | `FAIL — 4 violation(s)` | **`CD-CALM-GATE-002` × 4** |
| **C5** | `C5-NO-PATCH-CONTRACTS-DIR-REPOINTED.sh` | **n/a — no patch, and that is the point** | **0** | **3** | `PRECONDITION_NOT_MET` | the DECLARED-LIMIT-1 precondition |

**THE EXIT CODE DISCRIMINATES ON THIS INSTRUMENT.** `0` clean → non-zero violated on all five
arms. No column was substituted and none was needed. **But an exit code of `1` proves only that
the command failed, not that it failed for the reason the plant was planted** (`CD-ENG-WO2R3-F12`:
*two arms exiting 1 for different reasons look identical in a summary table and prove nothing*),
so the last column names the assertion, and every cell is listed by name below.

---

## `C1` — THE FULL REVERT OF `16A-FIX`'S CONSTITUTIONAL NARROWING

Every `"$ref": "#/$defs/absent_data_detail_level"` restored to `"#/$defs/detail_level"` —
**2 occurrences per file, 4 in total, which is the complete revert.** This is the Project
Lead's §2 mutation, reproduced independently here rather than inherited.

**The eight cells, verbatim from the violated arm's own output:**

```
public/equity_crash/UNKNOWN/calm         *** THE LIVE GATE ADMITTED A UNKNOWN DIAL RENDERING AS CALM. ***
public/equity_crash/DEGRADED/calm        *** THE LIVE GATE ADMITTED A DEGRADED DIAL RENDERING AS CALM. ***
public/monetary_debasement/UNKNOWN/calm  *** THE LIVE GATE ADMITTED A UNKNOWN DIAL RENDERING AS CALM. ***
public/monetary_debasement/DEGRADED/calm *** THE LIVE GATE ADMITTED A DEGRADED DIAL RENDERING AS CALM. ***
private/equity_crash/UNKNOWN/calm        *** THE LIVE GATE ADMITTED A UNKNOWN DIAL RENDERING AS CALM. ***
private/equity_crash/DEGRADED/calm       *** THE LIVE GATE ADMITTED A DEGRADED DIAL RENDERING AS CALM. ***
private/monetary_debasement/UNKNOWN/calm *** THE LIVE GATE ADMITTED A UNKNOWN DIAL RENDERING AS CALM. ***
private/monetary_debasement/DEGRADED/calm *** THE LIVE GATE ADMITTED A DEGRADED DIAL RENDERING AS CALM. ***
```

### *** AND WHAT THE REST OF THE REGISTER SAYS ABOUT THE SAME TREE ***

Every instrument in `tools/register/`, run verbatim on the `C1` violated extraction. **This is
the measurement the increment exists for, and it is reproduced here rather than quoted from the
dispatch:**

```
check_base_image_digest_pin.py                   exit=0  PASS — 13 assertions, 0 violations
check_constructor_field_establishment.py         exit=0  PASS — 113 assertions, 0 violations
check_dockerignore.py                            exit=0  PASS — 22 assertions, 0 violations
check_egress_no_broker.py                        exit=0  PASS — 69 assertions, 0 violations
check_engine_no_witness_reach.py                 exit=0  PASS — 28 assertions, 0 violations
check_exact_type_admission.py                    exit=0  PASS — 36 assertions, 0 violations
check_grant_matrix_live.py                       exit=3  PRECONDITION_NOT_MET  (no store reachable —
                                                         IDENTICAL on the clean tree; discriminates nothing here)
check_judgement_path_doors.py                    exit=0  PASS — 72 assertions, 0 violations
check_lockfile_denylist.py                       exit=0  PASS — 134 assertions, 0 violations
check_missing_data_never_calm.py                 exit=1  FAIL — 8 violation(s)     <-- NEW AT 16B
check_no_blend.py                                exit=0  PASS — 9078 assertions, 0 violations
check_no_execution_interface.py                  exit=0  PASS — 80629 assertions, 0 violations
check_no_numeric_default.py                      exit=0  PASS — 552 assertions, 0 violations
check_schema_closed.py                           exit=0  PASS — 266 assertions, 0 violations
check_sealed_against_forged_establishment.py     exit=0  PASS — 122 assertions, 0 violations
```

**FOURTEEN INSTRUMENTS SAY NOTHING. ONE SAYS IT.** Before this increment there was no line in
that block that read `FAIL`, on a tree where the constitutional guarantee was entirely gone.

---

## `C2` — ONE BRANCH, ONE SURFACE

The `DEGRADED` branch of the **public** contract only — **one line, one file.** `UNKNOWN` stays
narrowed on both surfaces and `DEGRADED` stays narrowed on the private one.

This arm is aimed at an instrument that asks *"is there a narrowing?"* rather than *"is EVERY
missing-data branch on EVERY surface narrowed?"*. Any check that read one branch, or sampled one
surface, or asked whether the definition `absent_data_detail_level` exists at all, passes this
tree.

**The two cells, and they are the right two — public only, DEGRADED only, both dial slots:**

```
public/equity_crash/DEGRADED/calm        *** THE LIVE GATE ADMITTED A DEGRADED DIAL RENDERING AS CALM. ***
public/monetary_debasement/DEGRADED/calm *** THE LIVE GATE ADMITTED A DEGRADED DIAL RENDERING AS CALM. ***
```

Six refusing cells still refused. **A guard that fired everywhere on this tree would be as
uninformative as one that fired nowhere**, and the located failure is what says the instrument
is reading the branch and the surface rather than a global fact.

---

## `C3` — THE `$ref` KEEPS ITS NAME AND LOSES ITS MEANING

All four `$ref`s left exactly as `16A-FIX` wrote them, pointing at
`#/$defs/absent_data_detail_level`. **`"calm"` is added back INSIDE that definition's own enum**,
on both surfaces.

A structural check that reads the `$ref` TARGET NAME — *"do the DEGRADED and UNKNOWN branches
reference `absent_data_detail_level`?"* — passes this tree completely. So does a `grep`. So does
any assertion phrased against the shape of the document rather than against what the document
admits. **This is the specific defect shape `CD-PL-F169`, `CD-ASR-WO3-02` F06/F07 and
`CD-ASR-WO3-03` are on the record for, and it is why the instrument drives the gate instead of
reading the file.**

Eight cells, the same eight as `C1`: with `calm` inside the target enum, both branches admit it
on both surfaces at both slots.

---

## `C4` — *** THE VACUITY ARM. THE ONE THAT DECIDES WHETHER ANY OF THIS IS WORTH HAVING. ***

`#/$defs/dial_reading_value`'s `detail_level` narrowed to `#/$defs/absent_data_detail_level`
**as well**, on both surfaces. The four missing-data branches stay narrowed exactly as
`16A-FIX` left them.

**On this tree, `calm` is refused everywhere. No dial of any state on any surface can render as
calm at all.** An instrument built only from the proposition *"a calm missing-data dial is
refused"* passes this tree with every assertion satisfied — and it would be certifying a product
that **cannot publish a calm reading of a real number**, which is the base case of the whole
product (PID §4: *"calm = dial + one line"*) and the reason the level exists.

**IT FAILS, AND IT FAILS ON THE ADMITTING ASSERTION AND NOT THE REFUSING ONE:**

```
public/equity_crash/VALUE/calm         MUST ADMIT — but the gate REFUSED it [SCHEMA_VIOLATION] at /equity_crash.
public/monetary_debasement/VALUE/calm  MUST ADMIT — but the gate REFUSED it [SCHEMA_VIOLATION] at /monetary_debasement.
private/equity_crash/VALUE/calm        MUST ADMIT — but the gate REFUSED it [SCHEMA_VIOLATION] at /equity_crash.
private/monetary_debasement/VALUE/calm MUST ADMIT — but the gate REFUSED it [SCHEMA_VIOLATION] at /monetary_debasement.
```

Rule: `CD-CALM-GATE-002`, four times, and **`CD-CALM-GATE-001` fires zero times on this tree** —
which is the correct reading. Nothing forbidden was admitted; something required was refused.

### What the rest of the register, and the suite, say about the `C4` tree

```
every instrument in tools/register/ except check_missing_data_never_calm.py:  exit 0 (or 3 for
    check_grant_matrix_live.py, identically to the clean tree)
check_missing_data_never_calm.py:                                             exit 1, 4 violations
python3 -m pytest tests/ -q:  2 failed, 2005 passed
    FAILED tests/test_detail_level.py::test_the_absent_data_branches_declare_a_vocabulary_that_EXCLUDES_calm[public_envelope.schema.json]
    FAILED tests/test_detail_level.py::test_the_absent_data_branches_declare_a_vocabulary_that_EXCLUDES_calm[private_envelope.schema.json]
```

**STATED PLAINLY BECAUSE IT CUTS BOTH WAYS.** The suite does catch `C4` — but in
`tests/test_detail_level.py`, which **before this increment no register `execute:` line ran**.
So at the base tip, `C4` was caught by nothing the gate reads. After 16B it is caught twice, by
`D1` (the live instrument) and by `D3` (that file added to
`CD-RT-001-ABSENCE-RENDERS-UNKNOWN`'s declared command). That is deliberate: `D1` and `D3` are
not the same guard and neither is offered as the other.

---

## `C5` — NO PATCH, NO TREE CHANGE, AND THE GATE STILL ADMITS A CALM `UNKNOWN` DIAL

`C5-NO-PATCH-CONTRACTS-DIR-REPOINTED.sh`. The dispatch asked, if one could be constructed, for
*"a route by which the live gate admits a calm UNKNOWN dial with both schemas fully intact — a
validation path that never reaches the branch."* **One can, and here it is.**

`envelope_contract.contracts_dir()` returns `$CD_CONTRACTS_DIR` when set. Point it at a copy of
the contracts with the `UNKNOWN` branch widened and the running gate admits the document PID
§3.2 forbids, **while the repository's own two files are byte-identical to the blobs in the
commit.** MEASURED at `fec0a8e`:

```
blob ids recorded in the commit fec0a8e:
  46f3a1b7d6c93373b21d2399787e54d08a331c0b   contracts/public_envelope.schema.json
  304a9bf1f6ed204856ea50d70d0495e140bead25   contracts/private_envelope.schema.json
blob ids of those files in the extraction, AFTER the route was exercised:
  46f3a1b7d6c93373b21d2399787e54d08a331c0b
  304a9bf1f6ed204856ea50d70d0495e140bead25          <- IDENTICAL. NOTHING IN THE TREE MOVED.
the widened COPY the gate actually loaded:
  41dff3ba25d37df35e0b516772445aae7e312d7a
  e4d5d3f28c5e9c5d4156e9357c836f3509d680e9

THE LIVE GATE, WITH $CD_CONTRACTS_DIR POINTED AT THE WIDENED COPY:
  gate resolves contracts to: /tmp/inc16b/widened
  public:  *** ADMITTED a calm UNKNOWN dial ***
  private: *** ADMITTED a calm UNKNOWN dial ***

THE INSTRUMENT, SAME ENVIRONMENT:
  CD-RT-001-MISSING-DATA-NEVER-CALM: PRECONDITION_NOT_MET
      the live gate resolves its contracts to /tmp/inc16b/widened, which is NOT
      /tmp/inc16b/run-C5/contracts. ... This check judges the contract the gate ACTUALLY LOADS,
      so it will not report on a tree it is not looking at (DECLARED LIMIT 1).
  exit=3
THE INSTRUMENT, SAME TREE, VARIABLE UNSET:
  exit=0   PASS — 67 assertions, 0 violations
```

### WHAT `C5` LEAVES UNCOVERED, SAID RATHER THAN LEFT TO BE DISCOVERED

**The instrument REFUSES TO RUN on this route. IT DOES NOT CLOSE IT.** Exit `3` is a non-zero
exit with a stated reason and never a pass (`PBG-CI-002`), so a CI job running this check cannot
be fooled by the variable being set under it. But that is a statement about the CHECK, not about
the PRODUCT: **a deployment that sets `$CD_CONTRACTS_DIR` to a widened copy is refused by nothing
in this repository.** No test asserts the variable is unset, no container manifest pins it, and
no instrument reads it. **CARRIER: NOT PROVED TO BE CARRIED ANYWHERE.** It is DECLARED LIMIT 1 of
`CD-RT-001-MISSING-DATA-NEVER-CALM` in all three of its `CD-RULE-004` places, and it is raised to
the Project Lead as a finding rather than repaired here — closing it means deciding whether the
contracts directory is configuration at all, which is a product question and not this seat's
(`PBG-AUTH-005`).

`C5` is also **not** the *"validation path that never reaches the branch"* the dispatch
hypothesised. That would be a route through `refuse_unless_publishable` itself which skips the
`oneOf`. **NONE WAS FOUND, AND THE SEARCH IS STATED SO THAT ITS LIMITS ARE VISIBLE:** the four
checks run in a fixed order and the schema check is unconditional and last, `load_envelope_schema`
raises `ContractUnavailable` rather than returning a permissive schema, and the parent
`dial_reading` closure is a SIBLING of `oneOf` so it cannot short-circuit it. **That is a
reasoned absence and not a proof.** If such a route exists this arm did not find it, and no arm
here covers it.

---

## THE `D3` CONTRAST — MEASURED SEPARATELY, BECAUSE IT IS A SEPARATE CLAIM

`D3` added `tests/test_detail_level.py` to `CD-RT-001-ABSENCE-RENDERS-UNKNOWN`'s declared command.
Both commands run on every violated arm — **the grown one, and the one the register declared
before 16B** — so the growth is shown to do something rather than asserted to:

| arm | `...test_reading.py test_evaluate.py test_dial_presentation.py -q` (**pre-16B**) | `... + tests/test_detail_level.py -q` (**16B**) |
|---|---|---|
| `C1` | **exit 0** — `124 passed` | **exit 1** — `9 failed, 167 passed` |
| `C2` | **exit 0** — `124 passed` | **exit 1** — `5 failed, 171 passed` |
| `C3` | **exit 0** — `124 passed` | **exit 1** — `6 failed, 170 passed` |
| `C4` | **exit 0** — `124 passed` | **exit 1** — `2 failed, 174 passed` |

**The register's pre-16B command for this criterion's runtime arm exits 0 on all four trees.**
Nothing was removed from that command and nothing was reordered; the 124 assertions it already
ran still run and still pass.

---

---

# WO-3 INCREMENT `16B-FIX` — ARMS `C6`–`C10`, ADDED BY `CD-ENG-WO3-06`

Under `governance/engineering/CD-DISPATCH-INC16B-FIX-ENGINEER.md` §7, authority
`CD-ASR-WO3-05`'s `AMBER` at `ca85d8e` (`BL-20260824T104431Z-A305.yaml`), findings **F1, F2, F3**.

**`C1`–`C5` ARE NOT TOUCHED, AND THEY WERE RE-RUN UNCHANGED.** A fix that quietly stops an
existing arm from biting is a regression, and this project has recorded a plant silently ceasing
to apply before (`CD-ENG-WO2R3-06-F06`). Their re-measurement is the first five rows of the table
below and **every count and every catching assertion is identical to the increment-16B MANIFEST
above** — only the CLEAN-arm assertion count moves, `67 -> 144`, because the instrument now
asserts more.

`C6`, `C7`, `C9` are the auditor's trees `E3`, `E2`, `E1` rebuilt from that entry's description
rather than inherited. `C8` is new. **`C10` is a CONTROL and it MUST PASS.**

## THE ARMS, AS MEASURED AT TIP `af3825c`

Each arm from **its own pristine `git archive af3825c | tar -x -C /tmp/...` extraction**. The
worktree was never mutated (`CD-PL-F154`). The declared command, run verbatim on both arms of
every row, is the register's own:

```
python3 tools/register/check_missing_data_never_calm.py --root .
```

| # | Plant | `git apply` | CLEAN | VIOLATED | violated-arm result | assertion that caught it |
|---|---|---|---|---|---|---|
| **C1** | `C1-FULL-REVERT-OF-16A-FIX.patch` | **0** | **0** | **1** | `FAIL — 8 violation(s)` | `CD-CALM-GATE-001` × 8 |
| **C2** | `C2-ONE-BRANCH-ONE-SURFACE-DEGRADED-PUBLIC.patch` | **0** | **0** | **1** | `FAIL — 2 violation(s)` | `CD-CALM-GATE-001` × 2 |
| **C3** | `C3-CALM-BACK-INSIDE-THE-ABSENT-ENUM.patch` | **0** | **0** | **1** | `FAIL — 8 violation(s)` | `CD-CALM-GATE-001` × 8 |
| **C4** | `C4-VACUITY-NO-DIAL-MAY-EVER-READ-CALM.patch` | **0** | **0** | **1** | `FAIL — 4 violation(s)` | **`CD-CALM-GATE-002` × 4** |
| **C5** | `C5-NO-PATCH-CONTRACTS-DIR-REPOINTED.sh` | **n/a — no patch, and that is the point** | **0** | **3** | `PRECONDITION_NOT_MET` | the DECLARED-LIMIT-1 precondition |
| **C6** | `C6-FOURTH-ONEOF-BRANCH-UNKNOWN-HINTED.patch` | **0** | **0** | **1** | `FAIL — 6 violation(s)` | **`CD-CALM-GATE-001` × 4 + `CD-CALM-BRANCHES-006` × 2** |
| **C7** | `C7-DETAIL-LEVEL-DROPPED-FROM-REQUIRED.patch` | **0** | **0** | **1** | `FAIL — 8 violation(s)` | `CD-CALM-GATE-001` × 8 (the **field-absent** rows) |
| **C8** | `C8-OFF-VOCABULARY-LEVEL-ADMITTED.patch` | **0** | **0** | **1** | `FAIL — 8 violation(s)` | `CD-CALM-GATE-001` × 8 (the **off-vocabulary** rows) |
| **C9** | `C9-OPTIONAL-THIRD-SLOT-UNUSUAL-REF.patch` | **0** | **0** | **1** | `FAIL — 2 violation(s)` | **`CD-CALM-SLOTS-007` × 2** |
| **C10** | `C10-CONTROL-SYMMETRIC-FOURTH-LEVEL.patch` — **CONTROL** | **0** | **0** | **0** | **`PASS — 158 assertions, 0 violations`** | **none, and that is the point** |

*** **THE FIRST GENERATION OF `C6`–`C10` DID NOT APPLY, AND THE `git apply` COLUMN IS WHAT CAUGHT
IT.** *** They were produced with `git diff --no-index` and mangled path prefixes;
`git apply` exited **1** on all five, the "violated" extraction was therefore the CLEAN tree, and
all five arms read **`PASS`** — five guards that looked like they had stopped guarding. Regenerated
in this lane's established `diff -ruN a/ b/` form and re-measured. **RECORDED RATHER THAN QUIETLY
CORRECTED: this is `CD-ENG-WO2R3-06-F06` happening for the fifth time on this project, inside the
increment whose own house rule exists to catch it, and the column caught it in the first run.**

## *** THE CONTRAST THAT DECIDES WHETHER THIS FIX IS ANY GOOD ***

**The SUPERSEDED instrument, taken verbatim from `git show cbb81d1:tools/register/check_missing_data_never_calm.py`,
run on each VIOLATED extraction:**

```
C6   SUPERSEDED INSTRUMENT (cbb81d1) on the violated tree: rc=0  PASS — 67 assertions, 0 violations
C7   SUPERSEDED INSTRUMENT (cbb81d1) on the violated tree: rc=0  PASS — 67 assertions, 0 violations
C8   SUPERSEDED INSTRUMENT (cbb81d1) on the violated tree: rc=0  PASS — 67 assertions, 0 violations
C9   SUPERSEDED INSTRUMENT (cbb81d1) on the violated tree: rc=0  PASS — 67 assertions, 0 violations
C10  SUPERSEDED INSTRUMENT (cbb81d1) on the violated tree: rc=0  PASS — 81 assertions, 0 violations
```

**Four holes, four `PASS`es, at the auditor's own `67` every time — and `81` on `C10`, which is
the auditor's `F5` control number exactly.** These are the auditor's trees, rebuilt.

## *** AND THE LIVE GATE, DRIVEN DIRECTLY, WITH ITS CONTROL ON THE CLEAN TREE ***

Not the instrument's opinion — `refuse_unless_publishable` itself, `$CD_CONTRACTS_DIR` unset,
each probe run twice: on the VIOLATED extraction and on the CLEAN extraction of the same tip.

```
C6: UNKNOWN + detail_level='calm' + render_hint='COMPACT'
    VIOLATED   public  *** ADMITTED (returned None) ***      private *** ADMITTED ***
    CLEAN      public  REFUSED [UNKNOWN_KEY] at /equity_crash    private REFUSED
C7: UNKNOWN with NO detail_level key at all
    VIOLATED   public  *** ADMITTED (returned None) ***      private *** ADMITTED ***
    CLEAN      public  REFUSED [SCHEMA_VIOLATION] at /equity_crash    private REFUSED
C8: UNKNOWN + detail_level='banana' (off-vocabulary)
    VIOLATED   public  *** ADMITTED (returned None) ***      private *** ADMITTED ***
    CLEAN      public  REFUSED [SCHEMA_VIOLATION] at /equity_crash    private REFUSED
C9: optional third slot credit_stress, UNKNOWN + detail_level='calm'
    VIOLATED   public  *** ADMITTED (returned None) ***      private *** ADMITTED ***
    CLEAN      public  REFUSED [UNKNOWN_KEY] at <root>          private REFUSED
```

**All four are real escapes on the live gate, not assertion bookkeeping.**

## `C6` — THE FOURTH `oneOf` BRANCH, AND WHY IT IS THE ONE THAT MATTERS

`dial_reading_unknown_hinted` appended to `#/$defs/dial_reading.oneOf` on both contracts: a copy
of the `UNKNOWN` branch whose `detail_level` points at the **full** `#/$defs/detail_level`,
requiring a marker property `render_hint` that is also added to the parent `dial_reading.properties`
so the parent closure admits it. **NO NEW ROOT KEY**, so `check_schema_closed`'s root-properties
allowlist — the thing that catches `C9` — never fires.

### *** AND WHAT THE REST OF THE REGISTER SAYS ABOUT THE SAME TREE ***

All **thirty** `execute:` lines of `required-tests.yaml`, run verbatim, cwd at each tree's root,
`diff`ed against the clean extraction of the same tip:

```
C6  : 3 rc=0 -> 3 rc=1     ONE LINE MOVES, AND IT IS THIS INSTRUMENT. NOTHING ELSE SEES IT.
C7  : 2 rc=0 -> 2 rc=1  and  3 rc=0 -> 3 rc=1
C8  : 2 rc=0 -> 2 rc=1  and  3 rc=0 -> 3 rc=1
C9  : 3 rc=0 -> 3 rc=1  and  6 rc=0 -> 6 rc=1   (line 6 = check_schema_closed, UNDECLARED KEYS)
C10 : 2 rc=0 -> 2 rc=1  ONLY — see the note below; line 3, this instrument, stays rc=0
```

**On `C6`, line 3 is the ONLY line in the entire register that moves.** Before this fix, *no*
line moved: `CD-ASR-WO3-05` measured that tree at `diff` EMPTY across all thirty. **A tree on
which this product publishes the one document its constitution forbids, and now exactly one line
of the register says so.**

The six cells, verbatim from the violated arm:

```
CD-CALM-BRANCHES-006  public : '#/$defs/dial_reading.oneOf' declares MORE THAN ONE branch for
                               the dial state(s) ['UNKNOWN'].
CD-CALM-BRANCHES-006  private: (the same)
CD-CALM-GATE-001      public/equity_crash/UNKNOWN[#/$defs/dial_reading_unknown_hinted]/calm
CD-CALM-GATE-001      public/monetary_debasement/UNKNOWN[#/$defs/dial_reading_unknown_hinted]/calm
CD-CALM-GATE-001      private/equity_crash/UNKNOWN[#/$defs/dial_reading_unknown_hinted]/calm
CD-CALM-GATE-001      private/monetary_debasement/UNKNOWN[#/$defs/dial_reading_unknown_hinted]/calm
```

**BOTH HALVES OF THE `FX1` FIX BITE ON THIS ARM AND THEY BITE INDEPENDENTLY** — the behavioural
half drove a branch nobody wrote by hand, and the deny-by-default structural half reported the
branch set as unrecognised. Either alone would have caught it; that is the point of having both.

## `C7` — `detail_level` DROPPED FROM `required`, BOTH ABSENT BRANCHES, BOTH SURFACES

The `$ref` narrowing is left **fully intact**, so every `calm` row still passes — this arm is
caught *only* by the **field-absent** row, and the field-absent row is one of the two that the
superseded instrument had dropped from the memorial it replaced. All eight cells are
`<no detail_level key>`, four on each surface, two per slot (one per absent-data branch).

**THIS IS THE ARM THAT MAKES A GOVERNED SENTENCE TRUE.** This mutation is a NAMED MEMBER of this
row's own `negative_control` class, under a sentence reading *"The instrument fails on all of
these."* It did not. It now does.

## `C8` — AN ABSENT-DATA BRANCH THAT ACCEPTS AN OFF-VOCABULARY LEVEL

`#/$defs/absent_data_detail_level`'s enum replaced by a `not: {const: "calm"}` predicate, and the
parent `dial_reading.properties.detail_level` opened to a bounded string. **`calm` is STILL
refused on every missing-data branch and `calm` on a `VALUE` is STILL admitted**, so `C1`–`C4`'s
assertions all pass on this tree — it is caught *only* by the **off-vocabulary** row, the second
of the two dropped rows. That isolation is deliberate: an arm that also trips `CD-CALM-GATE-001`
on `calm` would not prove the new row does anything (`CD-ENG-WO2R3-F12`).

## `C9` — THE OPTIONAL THIRD SLOT, SPELLED UNUSUALLY

`credit_stress` added to `properties` but **NOT** to `required` — which is exactly how a dial is
added without breaking existing consumers — with the value `{"$ref": "#/$defs/dial_reading_permissive"}`,
a union whose `DEGRADED` and `UNKNOWN` branches carry the full vocabulary.

```
CD-CALM-SLOTS-007  public : the contract declares dial-bearing root properties ['credit_stress']
                            that are NOT spelled '{"$ref": "#/$defs/dial_reading"}' and are
                            therefore NOT DRIVEN by this instrument
CD-CALM-SLOTS-007  private: (the same)
```

*** **THE INSTRUMENT STILL DRIVES TWO DIAL SLOTS AND NOT THREE.** *** It refuses to be *silent*
about a third; it does not adopt one. `PO-DECISIONS-0026` standing is **two dials, never
blended**, and a third dial slot is a Product Authority decision.

## `C10` — THE CONTROL, AND IT IS NOT A FORMALITY

A **symmetric** PID §4 amendment: `critical` added to `DETAIL_ORDER` in
`src/crash_detector/publication/detail_level.py` **and** to **both** enums (`detail_level` and
`absent_data_detail_level`) in **both** contracts.

```
CLEAN     PASS — 144 assertions, 0 violations   exit 0
VIOLATED  PASS — 158 assertions, 0 violations   exit 0
```

**The table grew by 14 assertions on the day the vocabulary grew, with no edit to the check.**
The superseded instrument measured `81` on the auditor's equivalent tree and the fixed one
measures `158` — both PASS, both grown. **If this arm had gone red, a vocabulary-driven table
would have been replaced by a hard-coded one and the best property this instrument has would have
been thrown away.**

### A NOTE ON `C10` AND REGISTER LINE 2, MEASURED AND NOT GLOSSED

On the `C10` tree the register's **line 2** — `CD-RT-001-ABSENCE-RENDERS-UNKNOWN`'s grown pytest
command — exits `1`: `4 failed, 48 passed` in `tests/test_detail_level.py`
(`test_the_levels_are_exactly_the_three_the_pid_names_in_its_order`, `test_detail_is_monotone_in_risk`,
`test_the_absent_data_branches_declare_a_vocabulary_that_EXCLUDES_calm` on both surfaces).
**THAT IS NOT THIS INSTRUMENT AND IT IS NOT THE `F6` BRITTLENESS EITHER.** Those tests pin PID
§4's three levels **verbatim** and say so in their own words: *"a fourth level is a PID amendment,
not a schema edit."* A tree carrying a fourth level SHOULD make somebody open the register — that
is deliberate friction, not name coupling. It is recorded here so that a future seat meeting a red
line 2 on a fourth-level tree finds it already measured, and does not mistake it for either a
defect in this arm or a second instance of `CD-ASR-WO3-05` F6.

---

## HOW AN AUDITOR REPRODUCES ANY ROW, WITHOUT TRUSTING THIS PAGE

```sh
TIP=fec0a8e                      # or whatever SHA you are auditing
ARM=C4                           # C1 | C2 | C3 | C4

mkdir -p /tmp/audit-$ARM-clean /tmp/audit-$ARM-viol
git archive $TIP | tar -x -C /tmp/audit-$ARM-clean
git archive $TIP | tar -x -C /tmp/audit-$ARM-viol

cd /tmp/audit-$ARM-clean && python3 tools/register/check_missing_data_never_calm.py --root . ; echo "CLEAN exit=$?"

cd /tmp/audit-$ARM-viol
git apply -p1 --verbose plants/WO3-INC16B/$ARM-*.patch ; echo "GIT APPLY exit=$?"   # <- READ THIS ONE
python3 tools/register/check_missing_data_never_calm.py --root . ; echo "VIOLATED exit=$?"
```

**Read the `git apply` exit code before you read anything else.** A patch that has stopped
applying yields a "violated" arm that is the clean tree, exits `0`, and looks in a summary table
exactly like a guard that has stopped guarding. **Four separate increments on this project have
broken a plant and found out only when somebody re-ran the set by hand** (`CD-ENG-WO2R3-06-F06`,
`F-06-L`), and nothing in this repository detects it: the suite does not apply plants, and
neither does any register check. **CARRIER: NOT PROVED TO BE CARRIED ANYWHERE.** A runner over
this directory is not the answer — an auditor verifying through a harness the project wrote is
verifying the harness (`PBG-ASSURE-001`).

`C5` takes no patch; run it as its own header describes.

---

## WHAT THIS SET DOES NOT ESTABLISH

* **It does not establish that `CD-AC-001` is satisfied.** It establishes that one instrument
  discriminates on five trees. The criterion computes `UNDECIDABLE` and the gate is `SHUT`.
* **It is not a census of the ways PID §3.2 could be broken.** Five arms, chosen because four
  were named in the dispatch and the fifth was constructible. A sixth shape nobody has thought
  of is not covered by anything here.
* **Nothing in this directory is a run record.** No arm here is admissible evidence for
  `RTR-WO3-0001`; that run belongs to an independent Assurance seat, and this seat may declare
  which run must evidence its guard and may not supply it (`PBG-SOD-001`, non-waivable).

### AND WHAT `16B-FIX` ADDS TO THAT LIST (`CD-ENG-WO3-06`)

The two sections above were written at increment `16B` and say **five arms**. **THEY ARE NOT
EDITED, BECAUSE THEY WERE TRUE OF THE SET THAT EXISTED THEN AND THIS PROJECT SUPERSEDES RATHER
THAN REWRITES.** As of `16B-FIX` the set is **ten**: the reproduce recipe's `ARM=` takes
`C1 | C2 | C3 | C4 | C6 | C7 | C8 | C9 | C10`, unchanged in every other respect, and `C5` still
takes no patch. **`C10` is the one row where `VIOLATED exit=0` is the CORRECT result** — read the
`C10` section before reporting it.

* **Ten arms is still not a census.** Four of the five new arms exist because an independent
  auditor found them, not because this set anticipated them. **THE SET GREW BY BEING BROKEN**, and
  the honest reading of `C6`'s history is that all five original arms passed the tree `C6`
  describes. An eleventh shape nobody has thought of is not covered by anything here.
* **`C6`-`C9` establish that the instrument discriminates on four trees the SUPERSEDED instrument
  passed.** They do not establish that no fifth escape exists.
* **`C10` establishes that the fix did not buy that discrimination by hard-coding.** It is the
  only arm in this directory whose whole value is in its passing.
* **Nothing here is assurance.** `CD-ENG-WO3-06` built these arms and may not certify them
  (`PBG-SOD-001`, non-waivable). A fresh Assurance seat follows.
