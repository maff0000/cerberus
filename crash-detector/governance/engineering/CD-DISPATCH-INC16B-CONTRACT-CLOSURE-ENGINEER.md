# CD-DISPATCH-INC16B-CONTRACT-CLOSURE-ENGINEER

**role source:** `pbg/roles/engineer.md` — reading it does not grant the role (`PBG-BOOT-001`),
**this dispatch does**.
**authority record:** **`PO-DECISIONS-0028`** (committed `fd51710`, `governance/decisions/`),
**rulings 1, 2, 3 and 4** — `Q33` RULED **(a) CLOSE THE CONTRACT** · `CD-ASR-WO3-10`'s `RED` at
`d682ea2` (`BL-20260824T161155Z-A310.yaml`, branch `asr-wo3-10-verdict`) ·
`PO-DECISIONS-0027` ruling 5 (**STANDS, reframed**) · `PO-DECISIONS-0026` ruling 10
**seat identity:** `CD-ENG-WO3-11` — **FRESH.** Never `CD-ENG-WO3-10` (which built `8398741`),
never `CD-ASR-WO3-10` (which falsified it — `PBG-SOD-004`), never `CD-ENG-WO3-01`…`-09`, never
`CD-ASR-WO3-01`…`-09`.
**issued by:** `PROJECT_LEAD_SEAT_04` · **increment:** 16B-CONTRACT-CLOSURE ·
**expected return:** `READY_FOR_ASSURANCE`

---

## 0. READ THIS FIRST. THIS IS NOT A SIXTH SPELLING PATCH AND IT IS NOT A REPAIR.

**Nine audits have attacked a RECOGNISER and the tenth proved the recogniser cannot win.** The
Product Owner has accepted that finding in full and ruled the architecture, not another shape:

> **`PO-DECISIONS-0028` ruling 1, verbatim:** *"The envelope contract MANDATES that every dial
> carries a well-formed `state` at a CANONICAL PATH (fixed location, not arbitrarily nested), with
> present + freshness semantics REQUIRED by the schema. Then: malformed, missing, mis-spelled,
> over-nested, or `present:false`-stale is REFUSED AT CONTRACT VALIDATION — deny-by-default at the
> schema boundary, which the gate already runs — and within that closed shape the value check is
> sufficient."*

**THE GAP YOU ARE CLOSING, STATED ONCE.** The instrument's `False` means *"nothing here names a
property called `state`"*. The constitution's `REFUSED` means *"this dial cannot prove its data is
present and fresh"*. **Those are different sentences and every remaining escape lives in the
difference.** You are not making the recogniser better at recognising. **You are removing the
recogniser from the load-bearing position and replacing it with a CLOSED PARTITION over a FINITE
SET**, so that there is no open space left to recognise in.

**`8398741` IS PRESERVED. NOTHING IS REVERTED** (`PO-DECISIONS-0028` ruling 3). `FX15` genuinely
closed `A309-F1`; `FX16` passed the audit clean and the auditor would carry it forward unchanged.
**Do not delete `_dial_bearing`, `_declared_names`, `_instance_declared_names` or
`_unreadable_keywords`.** They stay as the SECOND instrument. What changes is that the guarantee no
longer rests on them.

---

## 1. THE LANE

```
branch    wo-3
worktree  /srv/crash-detector-wo3
tip       8398741  (16B-FIX-5 — assured RED at d682ea2, banked, NOT accepted; content tip 16b872c)
base      be0b355  (FROZEN — READ-ONLY. Do not touch it, do not rebase onto it, do not check it out)
verdict   d682ea2 on branch asr-wo3-10-verdict — BL-20260824T161155Z-A310.yaml — READ IT IN FULL
ruling    governance/decisions/PO-DECISIONS-0028.md at fd51710 on main — READ IT IN FULL
```

**WRITABLE SCOPE:**
* `tools/register/check_missing_data_never_calm.py`
* **`contracts/public_envelope.schema.json` and `contracts/private_envelope.schema.json`**
* `contracts/execution/CD-RT-001-MISSING-DATA-NEVER-CALM.md`
* `required-tests.yaml` (**`CD-AC-001` block only**)
* `plants/WO3-INC16B/**` (**ADDING** arms; **C1–C34 UNTOUCHED**)
* `governance/engineering/build-log/**` for your own return, on the lane.

> *** **THE TWO ENVELOPE SCHEMAS WERE PROTECTED FOR YOUR PREDECESSOR AND ARE WRITABLE FOR YOU. THAT
> IS A DELIBERATE SCOPE CHANGE AND ITS AUTHORITY IS `PO-DECISIONS-0028` RULING 1, WHICH ORDERS THE
> MANDATE INTO THE ENVELOPE CONTRACT ITSELF.** *** It is bounded by §3 below. **It is not licence to
> redesign the contracts.** Any edit outside §3 is out of scope — stop and report instead.

**PROTECTED — ZERO PATHS, AND PROVE IT BY COMMAND IN YOUR RETURN:** `pbg/**` · `BLUEPRINT.md` ·
`PID.md` · `governance/decisions/**` · `governance/mapping/**` · `src/**` · `tests/**` ·
`deploy/**` · `db/**` · `tools/**` except your one file · `evidence/**` · `be0b355`.

**`CD-D-181` SEQUENTIAL-ONLY.** You are the only seat running. Do not spawn one.

---

## 2. WHAT I MEASURED MYSELF THIS SESSION, AND WHAT I AM ONLY QUOTING

**`CD-PL-F193`'s rule is binding on this dispatch as much as on you: an inherited finding is a
HYPOTHESIS until it is RUN.** Twelve consecutive dispatches on this row contained a falsehood, and
the last two were mine, both from propagating a claim instead of measuring it (`CD-PL-F202`,
`CD-PL-F203`). So the line is drawn explicitly.

### 2.1 MEASURED BY `PROJECT_LEAD_SEAT_04` IN ITS OWN SHELL, ON A CLEAN `8398741` WORKTREE

Direct in-process calls against `contracts/public_envelope.schema.json`:

```
A310-F1  THE CAP IS NOT FAIL-CLOSED. ONE INTEGER SEPARATES CAUGHT FROM ESCAPED.
         _dial_bearing(schema, {"enum": [<{"state","detail_level":"calm"} nested N deep>]})
           depth  1,5,20,22,23,24  ->  None   (UNDECIDABLE, reported, SAFE)
           depth  25,26,30,40      ->  False  (THE ONLY SILENT ANSWER THE INSTRUMENT HAS)
         _instance_declared_names(<30 deep>) -> {'wrap', INSTANCE_TOO_DEEP};  'state' ABSENT.

A310-F2  ONE STRING.
           {"enum":[{"state":  "SPINDRIFT","detail_level":"calm"}]} -> None   REFUSED
           {"enum":[{"status": "SPINDRIFT","detail_level":"calm"}]} -> False  INVISIBLE

A310-F3  THE CONTROL ADMITS BECAUSE THE RECOGNISER NEVER LOOKED.
           {"enum":[{"present":true,  <fresh stamp>, "detail_level":"calm"}]} -> False
           {"enum":[{"present":false, <STALE stamp>, "detail_level":"calm"}]} -> False
         *** THE IDENTICAL ANSWER. A dial declaring itself ABSENT and STALE, carrying calm,
             is indistinguishable to this instrument from one declaring itself present. ***

BASELINE  PYTHONPATH=src python3 -B tools/register/check_missing_data_never_calm.py --root .
          -> "PASS — 144 assertions, 0 violations", EXIT 0.
```

**All three of `CD-ASR-WO3-10`'s falsifications reproduce exactly. They are FACTS, not inheritance.**

### 2.2 MEASURED, AND IT REDIRECTS THIS INCREMENT — READ IT BEFORE YOU PLAN

I drove `refuse_unless_publishable` on the **UNMODIFIED** `8398741` contracts with eight documents:

```
baseline (control)                          ADMITTED    <- correct, the control works
dial state mis-spelled 'status'             REFUSED [UNKNOWN_KEY]        at /equity_crash
dial carries present:false + stale stamp    REFUSED [UNKNOWN_KEY]        at /equity_crash
dial state missing entirely                 REFUSED [SCHEMA_VIOLATION]   at /equity_crash
dial state over-nested {reading:{state:..}} REFUSED [SCHEMA_VIOLATION]   at /equity_crash
UNKNOWN dial carrying detail_level 'calm'   REFUSED [SCHEMA_VIOLATION]   at /equity_crash
brand-new root slot 'feed_liveness'         REFUSED [UNKNOWN_KEY]        at <root>
never-named state SPINDRIFT carrying calm   REFUSED [SCHEMA_VIOLATION]   at /equity_crash
```

*** **EVERY SHAPE THE RULING NAMES IS ALREADY REFUSED AT DOCUMENT VALIDATION AGAINST THE CLEAN
CONTRACT.** *** That is not a reason to do less. **It is the precise statement of what this
increment is for**, and you must hold it in your head the whole time:

> **THE DOCUMENT-LEVEL CLOSURE IS REAL BUT IT IS AN ACCIDENT OF THE CURRENT CONTRACT TEXT, NOT A
> GUARANTEE. EVERY ONE OF THE NINE ESCAPES IN THIS CHAIN WAS A *CONTRACT EDIT*, NOT A DOCUMENT.**
> The auditor's attack has never been "publish this document"; it has been "add this slot to the
> schema, and watch the whole 30-line register stay GREEN while the gate then admits a dead feed as
> calm." **YOUR JOB IS TO MAKE THE DOCUMENT-LEVEL CLOSURE AN INVARIANT THAT SURVIVES CONTRACT
> EDITS — to make it impossible to write a contract that opens the hole without the register going
> RED.** That is what "mandate the canonical shape, deny by default at the boundary" means here.

### 2.3 QUOTED, NOT ASSERTED — I HAVE NOT RUN THESE

* `CD-ASR-WO3-10`'s claim that `8398741` is *"strictly better than `dd40407`"* and that *"nothing
  should be reverted"* — carried from the verdict and from `PO-DECISIONS-0028` ruling 3. **UNRUN.**
* `CD-PL-F203`'s corrected fact — that the root closure comes from the `dial_reading` **wrapper**'s
  `additionalProperties: false` and **not** from a per-dial check upstream of the schema, so *"a new
  root slot that is not a `dial_reading` DOES NOT INHERIT THAT CLOSURE"*. I read
  `_refuse_classified_keys` and it classifies secret-bearing and surface-restricted vocabulary and
  nothing else, which is consistent — **but I have not built the tree that tests the consequence.**
  **VERIFY IT YOURSELF BEFORE YOU RELY ON IT**; §3 does not depend on it being true.
* The claim that `FX16` is sound because `not in _READABLE_KEYWORDS` has exactly one executable
  occurrence. **UNRUN BY ME.** Re-derive it if you touch that function.

---

## 3. THE WORK. FOUR ITEMS, AND ITEM `CC-1` IS THE INCREMENT.

### CC-1 — THE ROOT PARTITION. **THIS IS THE ARCHITECTURAL CLOSE.**

Today `CD-CALM-SLOTS-007` asks an open-space question and compares two sets:

```python
found        = every root property spelled EXACTLY {"$ref": "#/$defs/dial_reading"}
dial_bearing = every root property _dial_bearing() answers True about
if set(dial_bearing) != set(found):  violation
```

*** **A ROOT PROPERTY THE RECOGNISER ANSWERS `False` ABOUT IS IN NEITHER SET, SO THE COMPARISON IS
SATISFIED AND THE SLOT IS INVISIBLE.** *** That is the hole, exactly, and it is why `status`, the
`enum`-spelled dial, the 25-deep nest and `present:false` all pass: they are not *recognised*, so
they are not *compared*.

**REPLACE THE QUESTION. Do not ask "which root properties are dials?" — ask, of every root property
there is, "is this one of the two things a root property is ALLOWED to be?"**

> **RULE CC — THE CANONICAL DIAL SHAPE.** Every property of an envelope contract's root
> `properties` is **EXACTLY ONE** of:
>
> **(a) a CANONICAL DIAL SLOT** — spelled literally `{"$ref": "#/$defs/dial_reading"}`, that one
> key and no sibling keyword; or
>
> **(b) a DECLARED NON-DIAL PROPERTY** — its name is a member of a **finite written allowlist** in
> the instrument, and it is **AFFIRMATIVELY PROVED incapable of carrying a `detail_level`** (see
> below).
>
> **ANYTHING ELSE IS A VIOLATION.** No recogniser is consulted. There is no third case and no
> silence.

**WHY THIS IS COMPLETE AND THE RECOGNISER WAS NOT, AND YOU MUST BE ABLE TO ARGUE THIS FROM THE CODE
IN YOUR RETURN:** the root `properties` object has a **finite, enumerable key set**; the partition
is **exhaustive by construction** (member-of-allowlist is decidable by string equality, and
canonical-slot is decidable by dict equality against a two-token literal); and the root carries
`additionalProperties: false`, so a document cannot introduce a root key the contract does not
declare. **The alphabet is closed, so "everything else" is a set the instrument can name without
having to recognise anything.** `A310-F2` and `A310-F3` are not *closed* by this — **they are
UNREACHABLE**, because `status`, `{"enum":[...]}`, a 25-deep nest and `present:false` are all root
properties that are neither (a) nor (b).

**LIMB (b)'s AFFIRMATIVE PROOF IS A VALUE CHECK AND THAT IS THE RULING'S OWN WORDS — *"within that
closed shape the value check is sufficient."*** A written allowlist of names is a denylist wearing
an allowlist's clothes if nothing proves the named properties are really not dials. So for **each**
allowlisted non-dial root property, on **each** surface, drive the **LIVE GATE**: replace that
property's value with a calm-carrying object (at minimum `{"detail_level": "calm"}`, and one
variant nesting it) and **require `refuse_unless_publishable` to REFUSE**. A root property that
ADMITS a calm-carrying object **is not a non-dial property**, whatever the allowlist says. Finite:
the allowlist × 2 surfaces × the variants. Count every one with `check.asserted()`.

**THE ALLOWLIST IS DERIVED, NOT INVENTED.** It is the root properties the contracts declare today
that are not dial slots. **Adding a name to it is a PRODUCT act, not yours** (`PBG-AUTH-005`): if
the contract grows a root property that is neither a canonical dial slot nor already on the list,
the instrument must go **RED and stay RED** until a human rules on it. Say so in the violation text.

### CC-2 — THE CANONICAL PATH, MANDATED IN THE CONTRACT AND ENFORCED BY THE INSTRUMENT

Inside `#/$defs/dial_reading` the canonical path for the discriminator is **`properties.state`, at
depth one, and the branch-level `properties.state.const`**. Nowhere else. Mandate it:

**In BOTH contract files** (this is the `PO-DECISIONS-0028` ruling 1 mandate, and it is the only
reason the schemas are writable):
1. `#/$defs/dial_reading` gains `"required": ["state"]` — the canonical path stated as an assertion
   rather than left to be implied by the branches.
2. A normative clause in `#/$defs/dial_reading`'s `description` and in the root `description`
   naming **Rule CC** and the canonical path, and naming the instrument that enforces it.

> *** **A `description` IS NOT AN ENFORCEMENT POINT AND THIS CONTRACT ALREADY CARRIES A SUPERSEDED
> NOTE SAYING SO IN ITS OWN WORDS** *** — `absent_data_detail_level`'s description records that
> exact error from 16A, where the guarantee was *"asserted only in PROSE"* and the gate admitted a
> calm UNKNOWN dial on both surfaces. **The prose states the mandate; `CC-1` and `CC-3` enforce it.
> Do not write a sentence in a schema and count it as a control.**

**In the instrument**, assert structurally, per surface, counted:
* `#/$defs/dial_reading` resolves, is `additionalProperties: false`, declares `properties.state`,
  and requires `state`;
* **every** `oneOf` branch is `additionalProperties: false`, requires `state`, and declares
  `properties.state.const` as a string — **a branch that does not is a VIOLATION, never a silence**
  (`_branch_states` already withholds a state from an unreadable branch; make the *absence* of the
  canonical path its own named violation rather than folding it into the existing one);
* **every** branch requires **at least one property whose subschema resolves to
  `#/$defs/utc_timestamp`** — the freshness stamp. **A branch that requires no timestamp cannot
  prove freshness and must be a VIOLATION.** (Measured by me: `VALUE` and `DEGRADED` require
  `as_of_utc`, `UNKNOWN` requires `since_utc` — the NAMES differ per branch, so assert the
  **presence of a required `utc_timestamp`-typed property**, not a fixed name. Do not rename
  anything in the contracts to make a fixed name work; that is a document-set change and it is out
  of scope.)

### CC-3 — THE AFFIRMATIVE VALUE CHECK OVER THE CLOSED ALPHABET. **THIS IS RULING 5, MADE ACHIEVABLE.**

Now that the branch set is the whole alphabet, the affirmative requirement is finally expressible:

> **A branch may reference the calm-bearing `#/$defs/detail_level` IF AND ONLY IF its
> `properties.state.const` is a member of `PRESENT_STATES` *and* the branch requires a freshness
> stamp. EVERY OTHER BRANCH MUST reference `#/$defs/absent_data_detail_level`.**

**That is the affirmative form.** It does not ask "is this state on my list of bad ones?" — it asks
"has this branch PROVED present-and-fresh?", and a branch that has not, gets a `detail_level`
vocabulary from which `calm` is **absent**. A never-before-named state must arrive as a new branch;
a new branch's state is **not** in `PRESENT_STATES`; therefore it **cannot** carry `calm`. **BY
CONSTRUCTION, over a CLOSED set, and not by recognition over an open one.**

Assert it per branch per surface, counted, with the violation text naming the branch and the state.

### CC-4 — `A310-F1`, FAIL CLOSED. BOUNDED, AND CORRECT UNDER ANY ANSWER.

`INSTANCE_WALK_CAP` copied `_dial_bearing`'s number and not its handling. `_dial_bearing`'s own cap
returns `None`; `_instance_declared_names` returns `INSTANCE_TOO_DEEP`, **a sentinel with zero
executable consumers**, so reaching the cap is a **silent success** — and `DECLARED LIMIT 15`'s own
heading, *"REACHING THE CAP IS NOT A SILENT SUCCESS"*, says the opposite of what the code does.

**Make the cap fail CLOSED**: when `INSTANCE_TOO_DEEP` is among the names `_declared_names`
collected, the node is **UNDECIDABLE** (`undecidable = True` in `_dial_bearing`), never `False`.
**ACCEPTANCE IS ONE MEASUREMENT:** depth 25, 26, 30 and 40 must move `False` → `None`, and depths
1–24 must be **unchanged**. `Rule CC` makes deep nesting unreachable at the root anyway — **fix the
cap regardless**, because a cap that fails open is a defect whether or not anything reaches it.

**And correct `DECLARED LIMIT 15`'s text** to what the code then does. Do not leave a heading
asserting a property the code has only just acquired.

---

## 4. THE PLANTS. **PAIRED, AND A CONTROL FOR EVERY ARM.**

Add to `plants/WO3-INC16B/` — **C1–C34 are untouched and must all still bite**:

| arm | tree | REQUIRED OUTCOME |
|---|---|---|
| `CC-A` | root slot `feed_liveness` spelled `{"enum":[<LIVE>,<STALE …"detail_level":"calm">]}` | instrument **FAIL**, `CD-CALM-SLOTS-007` |
| `CC-B` | the same dial with the discriminator spelled **`status`** | instrument **FAIL** — `A310-F2` |
| `CC-C` | the same dial with `{"present": false, <stale stamp>, "detail_level":"calm"}` | instrument **FAIL** — `A310-F3` |
| `CC-D` | the same dial nested **25 deep** | instrument **FAIL** — `A310-F1` |
| `CC-E` | a 4th `oneOf` branch, state `SPINDRIFT`, referencing calm-bearing `#/$defs/detail_level` | instrument **FAIL** — `CC-3`, **RULING 5'S OWN TEST** |
| `CC-F` | **CONTROL.** the same 4th branch referencing `absent_data_detail_level` | gate **REFUSES** calm on it |
| `CC-G` | a branch with its freshness stamp dropped from `required` | instrument **FAIL** — `CC-2` |
| `CC-H` | **CONTROL.** an allowlisted non-dial root property widened to admit an object | instrument **FAIL** — `CC-1(b)` |
| `CC-I` | **VACUITY CONTROL.** the clean tree | **`PASS`, EXIT 0**, and the assertion count **stated** |

**`CC-F` AND `CC-I` ARE NOT OPTIONAL AND ARE NOT DECORATION.** An instrument that fails on
everything is not a guard, it is a brick. **A plant set with no passing control cannot tell the
difference.**

**EVERY PLANT IS A `git apply` PATCH THAT AN AUDITOR APPLIES ITSELF**, in the established form, with
its `rc` and its measured before/after in `plants/WO3-INC16B/MANIFEST.md`. **Report the rc of every
`git apply` you ran. A patch that did not apply is not a plant, it is a file.**

---

## 5. HOW YOU WILL BE GRADED. **ONE COMPLETION CONDITION, AND IT IS THE PRODUCT OWNER'S.**

`PO-DECISIONS-0027` ruling 5 **STANDS** (`PO-DECISIONS-0028` ruling 2), reframed: unchanged in what
it requires, changed only in HOW it is achieved — *"not by a recogniser searching an open space, but
by a CLOSED CONTRACT that makes the space finite and the proof mandatory."*

> *** **A DIAL THAT CANNOT PROVE PRESENT-AND-FRESH IS REFUSED BY CONSTRUCTION. A DIAL IN A
> NEVER-BEFORE-NAMED STATE, CARRYING `calm`, IS REFUSED.** ***

**YOU ARE NOT GRADED ON A SHAPE COUNT.** The census is abolished and adding a tenth shape to a list
earns an eleventh. **You are graded on whether the CLOSURE ARGUMENT holds** — whether every root
property is forced into limb (a) or limb (b) with no third case, and whether `calm` is
unrepresentable on any branch that has not affirmatively proved present-and-fresh.

**MAKE THE ARGUMENT FROM THE CODE, IN YOUR RETURN, AND NAME ITS BOUNDARY.** Your predecessor's
argument was graded **SOUND IN FORM with its enumeration CORRECT and re-derived**, and false in
exactly one universal claim — and the auditor said *"a wrong argument that could be CHECKED is worth
more than a right assertion that could not."* **Write the checkable one.** Enumerate the answer
sites. Name what your closure does **not** cover. **If you cannot make the argument, say so and
return `READY_FOR_ASSURANCE` with it named as unproved — do not assert it.**

---

## 6. STOP CONDITIONS. **RETURN, DO NOT IMPROVISE.**

* **The admitted DOCUMENT SET changes.** `CC-2`'s `"required": ["state"]` should be a strict no-op —
  every branch already requires `state` — so the set of documents the gate admits **must be
  unchanged**. **MEASURE IT, do not assume it.** If it changes, **STOP AND REPORT**: that is a
  consumer-visible contract change and a `schema_version` question, and **the version is pinned in
  `src/crash_detector/publication/envelope_contract.py`, which is PROTECTED FROM YOU.** Do not bump
  it, do not work around it.
* **Rule CC cannot be stated without a third case.** If the partition needs an "and also" limb, the
  closure is not a closure. **Return and say so** rather than shipping a two-limb rule with a
  silent escape hatch.
* **Any question of what a new state MEANS** — `PBG-AUTH-005`, product meaning, not yours.
* **`be0b355` moves, or any protected path gains a diff.** Prove zero by command either way.
* **You find that `CC-1` requires editing `src/**` or `tests/**`.** Out of scope. Report it.

**DO NOT REMOVE THE MEMORIAL.** `PO-DECISIONS-0027` ruling 3 conditions the removal of the pytest
literal-name assertion on the structural instrument carrying the behaviour. **IT DOES NOT CARRY IT
UNTIL A FRESH ASSURANCE SEAT SAYS IT DOES.** Removing it now would delete the only surviving catcher
on the strength of a guarantee that has just been falsified. **Leave `tests/` alone entirely.**

**DO NOT RELEASE 16C.** No liveness detector, no `feed_liveness` in a contract as a real slot, **not
one indicator row** from `governance/mapping/indicator_mapping.yaml`. Those follow a GREEN, and the
GREEN is not yours to declare (`PBG-SOD-001`, non-waivable).

---

## 7. YOUR RETURN

A build-log entry on the lane, `record_type: ENGINEER_RETURN`, `status: READY_FOR_ASSURANCE`,
`schema_version: 2`, ONE seat identity, validated `ok=True` **before** you commit it — and
**validate it by a direct call, not via `pbg log validate`, which validates zero entries and prints
GREEN**. Carry: the exact SHA · every command you ran **with its exit code** · the `CC-4`
before/after depth table · the assertion count on the clean tree, before and after · every plant's
`git apply` rc and outcome · **the closure argument and its named boundary** · the document-set
measurement from §6 · a `git diff --stat` proving the protected paths are zero · and **every finding
you raise against your own work.**

**THE SEATS ON THIS ROW KEEP CATCHING EACH OTHER'S UNMEASURED CLAIMS, AND THAT IS LUCK WEARING A
CONTROL'S CLOTHES. MEASURE EVERYTHING YOU SAY.**
