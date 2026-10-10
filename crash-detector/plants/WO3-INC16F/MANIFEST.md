# WO-3 INCREMENT 16F — PLANT SET

**Increment:** `16F-CONTROL-ROW-STRENGTH` · **Dispatch:** `CD-D-184` · **Seat:** `CD-ENG-WO3-14`
**Authority:** `PO-DECISIONS-0031` rulings 1 and 2
**Base:** `a9e19c39830557105d646408590487c75dd6b5bd`
**Instrument freeze (ITEM 4's honesty depends on this being a SHA):**
`6491b645dbeb66fd768a7054149489bc1d927ec6`
**Content tip these figures were measured at:** `7ac11c9789e86625e91ea163c72404288e91d023`
**Content preserved:** `0e80a09` and `ed7263a` — **nothing under `src/` changed and nothing was
reverted.** `git diff --name-only a9e19c3 7ac11c9 | grep -c '^src/'` -> **0**.

---

## What this plant set exists to measure

**`A313-F1` (HIGH): the freshness guarantee was TRUE at `a9e19c3` and its alarm probed ONE POINT
in document-space.** The instrument built every candidate by filling each root property with the
FIRST value of a closed vocabulary its subschema accepted, so all 72 documents carried the same
single value for every root property. A five-line early return keyed on any other root property
therefore left the live gate admitting a 1970-stamped calm dial on both surfaces while **all 32
register `execute:` lines were `diff`-identical**.

**`CD-PL-F193`: AN INHERITED CLAIM IS A HYPOTHESIS UNTIL IT IS RUN. This seat reproduced it
before writing a line** — its own patches, its own argv-parameterised probe, its own pristine
extractions, `git apply` rc taken and checked, inserted lines `grep`-confirmed present:

```
CLEAN a9e19c3 : 24 probe rows, 0 MUST-ADMIT rows refused, STALE-CALM ADMISSIONS = 0
W5G           : STALE-CALM ADMISSIONS = 4  (every two-input row, BOTH SURFACES)
W5B2          : STALE-CALM ADMISSIONS = 2  (the regime="calm" row,  BOTH SURFACES)
D1 (control)  : STALE-CALM ADMISSIONS = 16

register CLEAN : TOTAL lines=32 rc0=21 nonzero=11
register W5G   : TOTAL lines=32 rc0=21 nonzero=11   diff rc=0 — NOT ONE ROW MOVES
register W5B2  : TOTAL lines=32 rc0=21 nonzero=11   diff rc=0 — NOT ONE ROW MOVES
register D1    : TOTAL lines=32 rc0=19 nonzero=13   — exactly two lines move, both 16E's rows
```

**The absolute admission counts differ from `PROJECT_LEAD_SEAT_07`'s (8 and 8) because the ROW SET
of the probe differs, not because the tree does.** The qualitative claim reproduces exactly: on
both weakenings a 1970-stamped and a 2099-stamped calm dial are ADMITTED on BOTH SURFACES, every
MUST-ADMIT baseline still admits, and every register line is unmoved. **The `D1` control returns
`32/19/13` and moves exactly two lines, so the empty `diff` is a measurement and not a dead pipe.**

## Files

| file | what it is |
|---|---|
| `run_arms.sh <sha> [repo]` | one pristine `git archive \| tar -x` extraction per arm; patch read from an **ABSOLUTE path outside every extraction**; `git apply` rc **taken into a variable and checked**; the arm **ABORTED LOUDLY** on any non-zero. Runs both rows and the probe on each arm. |
| `run_register.sh <tree>` | runs EVERY `execute:` line the register declares in the named tree. rc **TAKEN FROM THE COMMAND**, never from a pipe (`CD-ENG-F02`'s defect class). The line count is **not hard-coded**. **This script is the acceptance test.** |
| `eng14_probe.py <tree>` | this seat's own live-gate probe, 24 rows. **It takes the tree as `argv[1]`** and prints the resolved `crash_detector.__file__` on its last line. |

### *** THE TWO METHOD TRAPS THIS SET EXISTS NOT TO FALL INTO ***

1. **`CD-ASR-WO3-11` disclosed against itself** that its runner read each patch **from inside the
   extracted tree**, where it did not exist at the older tip; `git apply` returned **128**, and the
   instrument then ran on an **UNPATCHED** tree — **measuring nothing while looking like a result.**
   Here every patch is read from an absolute path outside every extraction and every `git apply` rc
   is taken and checked.
2. **`plants/WO3-INC16D/probe_16d.py` HARD-CODES `sys.path.insert(0,
   "/srv/crash-detector-wo3/src")`** and therefore measures **THE LANE** whichever tree it is
   pointed at. `eng14_probe.py` takes the tree as `argv[1]`.

**`plants/WO3-INC16D/` AND `plants/WO3-INC16E/` ARE BYTE-UNCHANGED.** The arms that produced the
two AMBERs are not re-cut by the increment that answers them. `D2`, `D3` and `D4` below are the
**16D patches, applied unmodified** to extractions of this tip.

---

## The two rows, and why the arm table has two rc columns

| row | kind | subject |
|---|---|---|
| `CD-RT-001-STALE-DATA-NEVER-CALM` | **BEHAVIOURAL** | what the gate DECIDES about a document — now over the SPACE of documents, not one point |
| `CD-RT-001-PUBLICATION-CHOKEPOINT` | **STRUCTURAL** | which code ROUTES EXIST — no behavioural probe can enumerate routes nobody calls |

**NEITHER COVERS THE OTHER, AND THE ARM TABLE IS THE PROOF. MEASURED, COUNTED FROM THE TABLE
BELOW:** **EIGHT** arms (`C1` `C2` `C3` `C4` `C5` `C6` `N1` `N8`) defeat the publication path or
the stage with the BEHAVIOURAL row at `rc=0` and the STRUCTURAL row at `rc=1`; **FIVE** arms
(`D2` `D4` `N9` `N11` `N13`) defeat the verdict with the STRUCTURAL row at `rc=0` and the
BEHAVIOURAL row at `rc=1`. **A REPORT THAT QUOTES ONE OF THE TWO ROWS IS HALF A REPORT.**

## The arms, each from its own pristine extraction of `7ac11c9`

`git apply` rc = **0**, taken into a variable and checked, on **every** arm below.
`stale` = `CD-RT-001-STALE-DATA-NEVER-CALM`; `choke` = `CD-RT-001-PUBLICATION-CHOKEPOINT`;
`gate` = stale-calm admissions on this seat's 24-row probe.

### Inherited arms — the four `D` plants, 16D's patches applied unmodified

| arm | stale | choke | gate | reading |
|---|---|---|---|---|
| `D1` | `FAIL — 20` | `FAIL — 1` `CD-CHOKE-000` | **16** | the whole fourth stage removed |
| `D2` | `FAIL — 8` | `PASS` | **6** | naive `age > window`; a FUTURE stamp admitted |
| `D3` | `FAIL — 15` | `FAIL — 1` `CD-CHOKE-005` | 0 | slot-reading instead of the node walk |
| `D4` | `FAIL — 2` | `PASS` | 0 | the NEWEST stamp governs |

### The `A313-F1` class — the arms 16E's row could not see

| arm | stale | choke | gate | reading |
|---|---|---|---|---|
| `W5A` | `FAIL — 20` | `FAIL — 1` `CD-CHOKE-005` | **16** | `if not candidate.get("degraded_inputs"): return`. **At 16E this arm was MISSED by the instrument row and caught only by the pytest witness. It is now caught by BOTH new rows.** |
| `W5B2` | `FAIL — 20` | `FAIL — 1` `CD-CHOKE-005` | **2** | `if candidate.get("regime") == CALM_DETAIL_LEVEL: return`. **At 16E: register `diff`-identical.** |
| `W5G` | `FAIL — 24` | `FAIL — 1` `CD-CHOKE-005` | **4** | `if len(candidate.get("inputs_used") or []) > 1: return`. **At 16E: register `diff`-identical.** |
| `W5C` | `PASS` | `PASS` | **0** | the refusal token renamed to `FRESHNESS_ADVISORY`. **NOT A BREACH AND NOT INFLATED INTO ONE: the gate still refuses, nothing stale-calm is published, `CD-AC-001` is not touched.** What changes silently is the PUBLIC diagnostic contract — `REFUSAL_STALE_CALM` is in `__all__` and a consumer keying on the literal `"STALE_CALM"` stops seeing it. **RECORDED AS AN OBSERVATION.** Both rows read the token from the module under test, so neither can see the rename; the structural row derives the stage from the token's VALUE, which makes it rename-proof for FINDING the stage and blind to the rename ITSELF. |

### `C` — the publication-path arms. ITEM 2's acceptance

**Every one of these leaves the BEHAVIOURAL row at `rc=0`.**

| arm | stale | choke | reading |
|---|---|---|---|
| `C1` | `PASS` | `FAIL — 1` `CD-CHOKE-001` | a second function in `src/` writes `publication.public_envelope` and judges nothing |
| `C2` | `PASS` | `FAIL — 1` `CD-CHOKE-002` | the private surface is no longer judged before the write |
| `C3` | `PASS` | `FAIL — 1` `CD-CHOKE-002` | both gate calls moved inside an `if` |
| `C4` | `PASS` | `FAIL — 1` `CD-CHOKE-004` | an early `return` in `refuse_unless_publishable` in front of every stage. **LIVE ESCAPE, MEASURED: a document with no `regime` at all carries a 1970 calm dial to ADMITTED on both surfaces, having been judged by nothing.** |
| `C5` | `PASS` | `FAIL — 1` `CD-CHOKE-003` | the `except` handler swallows the refusal and falls through to the write |
| `C6` | `PASS` | `FAIL — 2` both `CD-CHOKE-000` | **THE VACUITY ARM.** Every publication write removed. A control that asserts "exactly one caller" is satisfied by a tree in which nothing calls anything — **this arm is why `CD-CHOKE-000` exists, and the Project Lead recorded it as the NAMED RISK of ITEM 2 before this file was written.** |

### `N` — the shapes invented AFTER the instruments were frozen at `6491b64`

**`CD-D-184` ITEM 4: "invent at least three further weakening shapes AFTER your instrument is
finished and frozen, keyed on properties and values you did not have in mind while building it,
and run them. Report what happened whether or not it flatters you."** Twelve were invented. The
freeze is a commit so the claim is auditable rather than asserted.

| arm | stale | choke | reading |
|---|---|---|---|
| `N1` | **`PASS`** | `FAIL — 1` `CD-CHOKE-005` | `if candidate.get("config_snapshot_id") == "BYPASS": return`, AFTER the enumeration. **IT ESCAPES THE BEHAVIOURAL ROW AND IT IS A LIVE ESCAPE: 1970-calm ADMITTED on both surfaces.** `"BYPASS"` is a value OUTSIDE the declared vocabulary, which is `DECLARED LIMIT 9` exactly. Caught structurally. |
| `N2` | `FAIL — 24` | `FAIL — 1` | `continue` keyed on the calm-bearing node's own `contributions` cardinality |
| `N3` | `FAIL — 20` | `FAIL — 1` | `return` keyed on the root `degraded_inputs` cardinality being 2 |
| `N4` | `FAIL — 20` | `FAIL — 1` | `return` keyed on the root `as_of_utc` being far in the future |
| `N5` | `FAIL — 12` | `FAIL — 1` | `continue` keyed on the calm-bearing node's own `state`. **Caught by LIMB B only** — the calm branch pins `state` with a `const`, so LIMB A has no alternative admissible value for it. |
| `N6` | `FAIL — 6` | `FAIL — 1` | **A CONJUNCTION:** `regime == "acute" AND len(inputs_used) == 2`. Neither half alone moves the verdict. **Caught by `CD-STALE-INVARIANT-011` — the LIMB B PAIRWISE pass, and by nothing else on that row. The pairwise pass earned its keep on a shape it was not built against.** |
| `N7` | `FAIL — 55` | `FAIL — 1` | `if len(calm_nodes) > 1: return` — keyed on THE ENUMERATION ITSELF, which is the one guard `CD-CHOKE-005` permits at all. **It is caught because the permitted guard is an EMPTINESS test and not a SIZE test**, and behaviourally it is caught eight ways over. gate admissions **16**. |
| `N8` | **`PASS`** | `FAIL — 1` `CD-CHOKE-005` | `continue` keyed on a root value OUTSIDE the vocabulary. **AT THE FREEZE `6491b64` THIS ARM ESCAPED BOTH ROWS AND PUBLISHED A 1970-STAMPED CALM DIAL ON BOTH SURFACES. RAISED BY THIS SEAT AGAINST ITS OWN WORK AS `CD-ENG-F16F-01`.** See below. |
| `N9` | `FAIL — 4` | `PASS` | the shared document walk no longer descends into arrays |
| `N11` | `FAIL — 23` | `PASS` | the window comparison widened by 10^9 — the stage enumerates correctly and then judges wrongly. gate admissions **10**. **`DECLARED LIMIT 4` of the structural row, measured.** |
| `N12` | `FAIL — 20` | `FAIL — 1` | the emptiness guard widened to `if not calm_nodes or regime == "acute": return`. **An adversarial test of the tightening that answered `N8`, invented after it, and caught.** |
| `N13` | `FAIL — 20` | `PASS` | NO early exit at all — the enumeration simply emptied afterwards by an ordinary assignment |

## *** `CD-ENG-F16F-01` — THE FINDING THIS SEAT RAISED AGAINST ITS OWN WORK ***

`CD-CHOKE-005` says, in its own words, *"no path through the freshness stage reaches its end
without enumerating the calm-bearing nodes."* **At the freeze `6491b64` it checked `return` and
did not check `continue` or `break` — one of the three ways to leave a node unjudged.** Arm `N8`,
invented after the freeze, walked straight through the gap: `rc=0` on both rows, and a 1970-stamped
calm dial ADMITTED on both surfaces.

**The rule was completed on its own stated terms** — `return`, `continue` and `break` are the three
ways, and the assertion now covers all three — **and the whole sequence is on the record rather
than quietly corrected.** Arms `N2`, `N5` and `N8` are the `continue` family; `N12` was invented
afterwards specifically to attack the fix and is caught.

**THIS IS THE SAME SHAPE AS `CD-ENG-F16E-01`**, which the previous Engineer raised against itself
— a guard written inverted, leaving a whole limb dead while looking like coverage. **A structural
rule that names one of three exit forms is a rule that looks complete and is not.**

## What is NOT claimed

- **The shipped product is NOT breached at `a9e19c3` or at `7ac11c9`.** On the clean tip this
  seat set out to admit a stale calm reading and could not: 24 probe rows, both surfaces,
  **STALE-CALM ADMISSIONS = 0**, 0 MUST-ADMIT rows refused.
- **16E is a large, real improvement and nothing about `a9e19c3` should be reverted.** Before it,
  `D1` moved nothing; after it, `D1` moved two register lines. Both facts are true.
- **`W5C` is an observation, not a breach**, and is not inflated into one.
- **Three-way conjunctions are covered by neither row** (`DECLARED LIMIT 10`).
- **A publication route that is not SQL against the `publication` schema is invisible to the
  structural row** (`DECLARED LIMIT 1`).
