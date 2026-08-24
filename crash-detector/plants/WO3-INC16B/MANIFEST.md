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
