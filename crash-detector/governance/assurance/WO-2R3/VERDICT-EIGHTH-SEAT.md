# VERDICT — EIGHTH ASSURANCE SEAT — CD-ASR-WO2R3-05

    actor_id:   CD-ASR-WO2R3-05
    role:       ASSURANCE_ENGINEER (assigned by CD-DISPATCH-WO2R3-ASSURANCE-08, not self-assigned)
    authority:  CD-AUTH-0001
    dispatch:   governance/dispatch/CD-DISPATCH-WO2R3-ASSURANCE-08.yaml
    target:     be0b355e4b9c39b65b7ca38e75e063ab2c5f40a5
    worktree:   /srv/crash-detector-wo2r3-audit8   (READ-ONLY to this seat)
    scratch:    /tmp/cd-asr-wo2r3-05/              (this seat's only writable location)
    started:    2026-08-23T11:57:40Z

**THIS DOCUMENT IS WRITTEN INCREMENTALLY AND APPENDED TO AS THE AUDIT PROCEEDS.**
A partial verdict on disk beats a complete one in a dead context (PBG-CONT-007).

---

## SECTION 0 — BOOT DECLARATION

### 0.1 Identity and independence

I am `CD-ASR-WO2R3-05`. I am none of `CD-ASR-WO2-01`, `CD-ASR-WO2-02`, `CD-ASR-WO2R2-01`,
`CD-ASR-WO2R3-01`, `-02`, `-03`, `-04`. I am none of `CD-ENG-WO2R3-01` .. `-09`. I implemented
nothing in this target and I will repair nothing in it (`PBG-SOD-001`, non-waivable;
`PBG-SOD-004`). My context contains no prior seat's scratch: I have read no file under
`/tmp/asr7/`, `/tmp/cd-eng-wo2r3-08/`, `/tmp/cd-eng-wo2r3-09/` or `/tmp/pl-inc10/` and will not
(`CD-PL-F128`).

### 0.2 Target resolved, never transcribed (CD-PL-F36)

```
$ cd /srv/crash-detector-wo2r3-audit8 && pwd && git rev-parse HEAD; rc1=$?; echo "rc_rev_parse=$rc1"
/srv/crash-detector-wo2r3-audit8
be0b355e4b9c39b65b7ca38e75e063ab2c5f40a5
rc_rev_parse=0

$ git cat-file -t be0b355e4b9c39b65b7ca38e75e063ab2c5f40a5; rc2=$?; echo "rc_cat_file=$rc2"
commit
rc_cat_file=0

$ git status --porcelain | wc -l
0
```

Worktree clean at porcelain 0 at boot. **CONFIRMED.**

### 0.3 BOOT FINDING F00 (LOW, documentary) — the dispatch's `branch:` field is wrong for my worktree

The dispatch records `target.branch: wo-2r3` alongside `target.worktree:
/srv/crash-detector-wo2r3-audit8`. The worktree I was given is **detached HEAD**, not on `wo-2r3`:

```
$ cd /srv/crash-detector-wo2r3-audit8 && git rev-parse --abbrev-ref HEAD
HEAD
$ git branch -a --contains be0b355e4b9c39b65b7ca38e75e063ab2c5f40a5
* (no branch)
+ wo-2r3
$ git worktree list
/srv/crash-detector               d0d13f8 [main]
/srv/crash-detector-wo2r3         be0b355 [wo-2r3]
/srv/crash-detector-wo2r3-audit8  be0b355 (detached HEAD)
```

This is **materially harmless and arguably correct practice** — a detached audit worktree cannot
be advanced under the auditor by a push to `wo-2r3` — but it is a discrepancy between the recorded
and the observed state and the framework requires me to reconcile and report rather than silently
correct (`CLAUDE.md` stop conditions). The commit **is** contained in `wo-2r3` and `wo-2r3` is at
exactly `be0b355`, so the authentic target is reachable and this does not impair the audit.
Recorded as **F00, LOW, DOCUMENTARY**.

### 0.4 What I understand I am grading

Not "is the class sealed". The project now denies that in its own instrument's exit text. I am
grading a **DECLARED PERIMETER** — `BLUEPRINT.md` §16 `CD-D-172` and §17 `CD-BP-005` at v0.3.0 on
`main` — in three parts:

- **PREVENTED**: declared routes + front door (accident-proofing, non-vacuous, refusing arm 1),
  **plus admission by EXACT TYPE on every enumerated judgement path**.
- **DETECTED**: witness divergence + provenance chain — the FORGERY-DETECTION OBLIGATION, owed at
  WO-3, **not built**.
- **OUT OF SCOPE**: preventing an in-process actor from constructing the object at all.
- **Blast-radius basis**: detector is ADVISORY (`D1`), no money moves on it (`D2`).

Plus the four questions in `the_thing_you_are_grading`, the re-grade of `CD-AC-002` and
`CD-AC-005`, and targets T1-T9 and T20-T23.

### 0.5 Documents read in full before measuring

`/srv/crash-detector/CLAUDE.md` · `pbg/roles/assurance-engineer.md` ·
`pbg/standards/DEVELOPMENT_SECURITY_BASELINE.md` · the dispatch ·
`governance/decisions/PO-DECISIONS-0018.md` · `BLUEPRINT.md` §16 (`CD-D-172`) and §17 (`CD-BP-005`)
at `d0d13f8` on `main`.

---
## SECTION 1 — T4: THE ZERO, RE-DERIVED INDEPENDENTLY. **CONFIRMED.**

The dispatch says this is "the load-bearing number of the whole gate and it comes from a seat that
has been wrong about it before". I did not take it on the Project Lead's word and I did not take it
from the project's own instrument. I wrote my own probe, `/tmp/cd-asr-wo2r3-05/p_t4_seal_census.py`,
which imports, calls, copies and reuses **nothing** from
`tools/register/check_sealed_against_forged_establishment.py` or from
`check_constructor_field_establishment.py`. It derives the population by its own `pkgutil` walk plus
its own `vars()` descent, and counts package lines with its own `sys.settrace` counter.

Command (CD-RULE-009):

```
$ cd /tmp/cd-asr-wo2r3-05 && python3 -B p_t4_seal_census.py /tmp/cd-asr-wo2r3-05/tip
$ rc=$?; echo "T4_RC=$rc"
T4_RC=0
```

(the extraction is pristine: `git archive be0b355e4b9c39b65b7ca38e75e063ab2c5f40a5 | tar -x -C
/tmp/cd-asr-wo2r3-05/tip`, `extract_rc=0`)

Result, verbatim from the probe (CD-PL-F98 — it prints its own tree):

```
tree: /tmp/cd-asr-wo2r3-05/tip
crash_detector imported from: /tmp/cd-asr-wo2r3-05/tip/src/crash_detector/__init__.py
python: 3.11.2
modules imported: 39
POPULATION (this probe's own live traversal): 99

=== F1 ROUTE: cls.__new__(cls) + object.__setattr__(member) ===
  FORGED               40
  NO_STATE_TO_FORGE    59
  REFUSED              0
  PARTIAL              0
  TOTAL                99

  FORGED with NON-ZERO package lines executed: 0
  REFUSED detail (each with its exception type and message):
    (none)
```

**FINDING F01 — T4 UPHELD. The Project Lead's re-derivation is CORRECT and its earlier "eleven" was
wrong.** My independent population is **99**, matching both of the instrument's two derivations. My
F1 tally is **FORGED 40 · NO STATE TO FORGE 59 · REFUSED 0**, which is the Project Lead's number
digit for digit, obtained by a probe that shares no code with theirs.

**NOT ONE CLASS IN NINETY-NINE REFUSES THE F1 FORGERY ON ITS MERITS.** Every one of the 40 forgeries
executed **zero** lines of `src/crash_detector/` (`FORGED with NON-ZERO package lines executed: 0`),
so no package code was even given the chance to object. The other 59 are not seals: they have no
`__slots__` member and no dataclass field, so `not forged` is vacuously true of a stateless object —
and 58 of the 59 are exception classes or Protocols.

**The honest count of classes this project can defend as sealed against deliberate in-process
forgery is ZERO.** The instrument now says exactly that, in its own exit text, on every run
(`sealed2.out` line 46-47). **That is the single most important thing that changed at this
increment, and it is true.**

---
## SECTION 2 — T1 Q1 / Q2. **FINDING F02 (HIGH) — THE "PREVENTED" HALF OF THE PERIMETER IS
## STATED IN A WAY THAT IS FALSE FOR THE ROUTE THE SAME ROW NAMES FIRST.**

### 2.1 The sentence under audit

`BLUEPRINT.md` §17 `CD-BP-005`, HANDLING column, at `d0d13f8` on `main`:

> PREVENTED: the declared routes and the front door, kept as accident-proofing, non-vacuous,
> proved by a refusing arm 1 — **plus admission by EXACT TYPE on every enumerated judgement path,
> so a forged subclass is constructible but useless.**

And the RISK column of the same row names **two** routes, in this order:

> `cls.__new__(cls)` + `object.__setattr__`, **and** `type.__new__(<metaclass>, ...)` for the type
> itself.

**The PREVENTED clause answers only the second route. It does not say so.**

### 2.2 Why exact type cannot answer the first route — measured, not argued

An exact-type door asks `type(x) is T`. The F2 forgery is a metatype **subclass**, so
`type(inst) is T` is `False` and the door refuses it. **The F1 forgery is not a subclass. It is
an object of EXACTLY `T`.** `type(inst) is T` is `True`. An exact-type door is, by construction,
blind to it.

I verified the four doors the project's own guard names, both arms:

```
$ cd /tmp/cd-asr-wo2r3-05 && python3 -B p_q1_f1_through_doors.py /tmp/cd-asr-wo2r3-05/tip
tree: /tmp/cd-asr-wo2r3-05/tip
crash_detector imported from: /tmp/cd-asr-wo2r3-05/tip/src/crash_detector/__init__.py
```

| door | ARM 1 — F2 forged subclass | ARM 2 — F1 exact-type forgery |
|---|---|---|
| `dials.magnitude::_established_quantity` | REFUSED `NotAdmitted` (declared) | refused by **`builtins.AttributeError`** |
| `dials.provenance::derived_within_one_dial` | REFUSED `QuantityProvenanceMissing` (declared) | refused by **`builtins.TypeError: 'float' object is not iterable`** |
| `serving.dial_presentation::present_dial` | REFUSED `NotAdmitted` (declared) | REFUSED `DialPresentationRefused` (declared) |
| `serving.dial_presentation::is_shown` | REFUSED `NotAdmitted` (declared) | **ADMITTED**, returned `False`, 70 package lines |

Two of the four refuse the F1 route only by an **incidental exception from a body that admitted
the object and then tripped over it.** That is not my standard — it is the project's own, written
into `tools/register/check_exact_type_admission.py` lines 324-333:

> *"THE RIGHT OUTCOME FROM THE WRONG LAYER IS THIS PROJECT'S MOST-REPEATED DEFECT AND IT IS A
> VIOLATION HERE, NOT A DETAIL. A body that admitted the object and then tripped over a missing
> attribute has not refused it."*

**The guard applies that standard to ARM 2 of the F2 route and to nothing else. Applied to the F1
route, two of its own four doors would fail it.**

### 2.3 AND THE F1 FORGERY REACHES THE PRESENTATION SURFACE WITH A NUMBER OF ITS OWN CHOOSING

The crashes above are an artefact of a *lazy* forgery that wrote floats into fields expecting
objects. A competent forger nests genuine governed exact types. I built the whole chain that way:

```
$ cd /tmp/cd-asr-wo2r3-05 && python3 -B p_q2b_nested_forgery.py /tmp/cd-asr-wo2r3-05/tip
tree: /tmp/cd-asr-wo2r3-05/tip
crash_detector imported from: /tmp/cd-asr-wo2r3-05/tip/src/crash_detector/__init__.py
python: 3.11.2

THE F1 CHAIN — every layer EXACTLY the governed type, ZERO package lines
  package lines executed to build the ENTIRE chain: 0
  type(x) is DeclaredQuantity   -> True
  type(x) is DialMagnitude      -> True
  type(x) is EquityCrashScore   -> True
  type(x) is Value              -> True
  sole_dial_of(forged magnitude) -> 'equity_crash'

present_dial(dial_id='equity_crash', reading=<F1-forged Value>)
  *** OUTCOME: ADMITTED. THE JUDGEMENT PATH RETURNED A PRESENTATION. ***
      returned:              Shown
      type(result) is Shown: True
      is_shown(result):      True
      result.dial_id:        'equity_crash'
      result.magnitude:      DialMagnitude (is DialMagnitude -> True)
      package lines on the door: 282
      quantity_for(dial_id='equity_crash') -> 999.0   (float)
```

Re-run standalone to read the number out (CD-RULE-009, paste-able):

```
$ cd /tmp/cd-asr-wo2r3-05 && python3 -B - <<'PY'   # full script in this scratch, see below
...
present_dial returned: Shown | is_shown: True
quantity_for(dial_id) returned: 999.0 float
THE PUBLISHED NUMBER IS: 999.0
THE NUMBER THE FORGER CHOSE WAS: 999.0
IDENTICAL: True
PY
```

**BOTH ARMS (CD-D-079).** The contrast arm is in `p_q2_competent_forgery.py`: the same chain with a
**foreign look-alike** score is REFUSED by `DialPresentationRefused` — *"a LookAlike was carried by
a reading offered for presentation"* — and a **bare float** magnitude is REFUSED by
`DialPresentationRefused` at `Shown.__post_init__`. **The doors are real and they refuse what they
were built to refuse. They simply cannot see the F1 route, because the F1 route hands them exactly
the type they asked for.**

### 2.4 THE FINDING

**`CD-ASR-WO2R3-05-F02`, HIGH.** A forged magnitude, constructed with **ZERO lines of package
code**, traversed the product's own **public** judgement path — `present_dial` -> `fold` ->
`_shown_from` -> `Shown.__post_init__` -> `sole_dial_of` -> `quantity_for` — passing **every**
exact-type door in the chain, was reported `is_shown -> True`, and released the forger's own number
`999.0` through the product's declared exit. 282 lines of package code ran on the door and not one
of them refused it.

Therefore §17 `CD-BP-005`'s word **"useless"** is false for the F1 route. The forged object is not
useless; it is fully useful. The sentence is *narrowly* rescuable — it says "a forged **subclass**",
and a forged subclass genuinely is useless at those four doors — but it is the HANDLING column of a
risk row whose RISK column names F1 **first**, and no reader reconciles the two. **A handling column
that answers one of the two routes its own risk column names, without saying which, claims more than
its guard delivers. That is `CD-RULE-004` applied to the Blueprint.**

**This is precisely the item the Project Lead itself named as the weakest of the five things it
authored rather than carried (dispatch T20, item (3): `CD-BP-005`'s HANDLING column, "the Project
Lead's PROSE about the ruling rather than the ruling's own words"). It was right to name it, and the
prose does overclaim.**

**AND THIS IS WHAT MAKES SECTION 3 DECISIVE.** If the F1 forgery reaches publication with exact type
at every door — and it does, measured above — then prevention genuinely cannot catch it, and the
DETECTED half is not one defence among several. **It is the only one.**

---
## SECTION 3 — T1 Q3. **FINDING F03 (HIGH) — THE DETECTED HALF IS A PLAN, NOT A DEFENCE,
## AND IT IS NOT EVEN A SCHEDULED ONE.**

The dispatch asked me to say plainly which it is. **IT IS A PLAN.** And it is weaker than a plan in
two specific, measured ways that the record does not state.

### 3.1 It is not built. Confirmed.

```
$ cd /srv/crash-detector-wo2r3-audit8 && git rev-parse HEAD
be0b355e4b9c39b65b7ca38e75e063ab2c5f40a5
$ ls contracts/execution/ | grep -i "forg\|diverg\|proven"
CD-RT-002-SEALED-AGAINST-FORGED-ESTABLISHMENT.md
CD-RT-004-DIVERGENCE-ALARM-FIRES.md
CD-RT-013-ROTATION-RATIO-PROVENANCE.md
$ grep -n "CD-D-172\|FORGERY-DETECTION OBLIGATION" required-tests.yaml
2490:  ... whose own bytes are carried into BLUEPRINT §16 CD-D-172 and §17 CD-BP-005:
2525:  ... FORGERY-DETECTION OBLIGATION owed at WO-3 as a first-class criterion (§16 CD-D-172) — AND IT
```

Both hits are **prose inside the sealing check's declared-limit text**. There is no register row for
the obligation, no execution contract, and no code. The instrument says so itself, in its own exit:
*"**IT IS NOT BUILT YET.**"* That much is honest and I confirm it.

### 3.2 **BUT CD-D-172 REQUIRES A FORM, AND THE RECORD CARRIES IT IN EXACTLY THE FORMS CD-D-172
### FORBIDS.**

`BLUEPRINT.md` §16 `CD-D-172`, the Product Owner's own carried text, is explicit:

> *the FORGERY-DETECTION OBLIGATION is specified at WO-3 ... and is verified as a **FIRST-CLASS
> CRITERION** — **not as a note, not as a residue paragraph, and not as a manual step.***

Measured against `BLUEPRINT.md` at `baede05` on `main` (the file is byte-identical to `d0d13f8`;
see §6.1):

```
$ grep -oE "CD-AC-[0-9]{3}" BLUEPRINT.md | sort -u | tail -5
CD-AC-012
CD-AC-013
CD-AC-014
CD-AC-015
CD-AC-016
$ awk 'NR>=556 && NR<=595 && /172|FORGERY|forgery/' BLUEPRINT.md | wc -l
0
```

- **§14 "Full criterion trace"** (lines 556-574) lists CD-AC-001 .. CD-AC-016. **There is no row for
  the forgery-detection obligation and no criterion ID was minted for it.**
- **§15 "Delivery order"**, the WO-3 row (line 592), reads in full:
  `| **WO-3** | publication layer, heartbeat, external probe, regime-aware staleness, health surface
  | 008, 009, 014 | Assurance PASS; ... |`
  **The obligation is not in WO-3's content column and not in WO-3's criteria column.**
- `awk` over both tables returns **0** lines mentioning it.

**So the obligation exists as: a paragraph in §16 (a note), a cell in the §17 risk table (a residue
paragraph), and narrative in `ACTIVE_WORK.yaml`. Those are precisely the three forms its own
governing sentence rules out, and it exists in none of the form that sentence requires.** A first-
class criterion on this project is a `CD-AC-xxx` row in §14 traced to a work order in §15 and a
`required-tests.yaml` entry with an execution contract. The obligation has none of the four.

### 3.3 **AND ITS TWO NAMED MECHANISMS ARE BOTH SCHEDULED ONE WORK ORDER AFTER THE OBLIGATION.**

`CD-D-172` names the mechanisms: *"Its two named mechanisms are **witness divergence** and the
**provenance chain**."* The obligation is owed at **WO-3**. Measured from §14:

```
$ grep -n "CD-AC-004\|CD-AC-010" BLUEPRINT.md | tail -2
562:| CD-AC-004 | §6 divergence module | WO-4 |
568:| CD-AC-010 | §4 immutable `first_published_utc`, §8 provenance | WO-4 |
```

and from §15:

```
592:| **WO-3** | publication layer, heartbeat, ... | 008, 009, 014 | ...
593:| **WO-4** | witnesses live, divergence alarm, history and slope | 004, 010, 011 | ...
```

and from the product's own source:

```
$ sed -n '24p' src/crash_detector/witness/panel.py     # at be0b355
Divergence *computation* is WO-4 (CD-AC-004). WO-2 delivers the type and the
```

**WITNESS DIVERGENCE IS `CD-AC-004`, WO-4. THE PROVENANCE CHAIN IS `CD-AC-010`, WO-4. WITNESSES DO
NOT EVEN GO LIVE UNTIL WO-4 — §15's WO-4 row is literally *"witnesses live, divergence alarm"*.**

`CD-D-172`'s stated ground for choosing WO-3 is: *"It cannot be specified before WO-3 because with
zero registry rows there are no witnesses to diverge from."* **That ground is sound and it proves
too much: by the project's own delivery table there are no witnesses to diverge from at WO-3
either. They arrive at WO-4.**

### 3.4 THE FINDING

**`CD-ASR-WO2R3-05-F03`, HIGH.** The DETECTED half of the declared perimeter — which §17 itself
calls *"the load-bearing half"* — is:

1. **not built** (declared, and I confirm it);
2. **not scheduled as the kind of thing it says it must be** — no criterion ID, absent from §14's
   criterion trace and from §15's WO-3 row, carried only as a note and a residue paragraph, which
   are two of the three forms `CD-D-172` expressly forbids; and
3. **owed at a work order where neither of its two named mechanisms exists**, both being `WO-4`
   items by the same Blueprint's own §14 and §15.

**Applying `CD-RULE-006` — "a residue declaration must name a layer MEASURED to hold it, or be
written NOT PROVED TO BE CARRIED ANYWHERE" — the honest form of §17's DETECTED cell is
`NOT PROVED TO BE CARRIED ANYWHERE`.** The Engineer `CD-ENG-WO2R3-09` wrote exactly that in its own
residue and the record quotes it in this seat's dispatch. **The Blueprint does not say it. §17 says
"owed at WO-3 as a first-class criterion", which asserts a carrier that §14 and §15 do not contain.**

**Combined with `F02`: the only defence that could catch the attack I demonstrated in Section 2 is
the one that does not exist, is not scheduled in the form required, and whose machinery lands a work
order after the date it is promised for.**

---
## SECTION 4 — T1 Q2. **FINDING F04 (MEDIUM) — "THE PLATFORM DOES NOT PERMIT PREVENTING IT"
## IS TWO CLAIMS. ONE IS TRUE AND MEASURED. THE OTHER IS ASSERTED AND NEVER TESTED.**

§17 `CD-BP-005` states the scope in two different widths in two different cells:

| cell | what it says |
|---|---|
| RISK (headline) | "DELIBERATE IN-PROCESS FORGERY IS NOT PREVENTED **AND THE PLATFORM DOES NOT PERMIT PREVENTING IT**" |
| OUT OF SCOPE | "preventing an in-process actor **from constructing the object at all**" |

These are not the same claim.

- **(A) The platform does not permit preventing CONSTRUCTION.** **TRUE, and I measured it** — Section
  1: 40 of 99 classes forged, zero package lines, no class refuses on its merits. `object.__setattr__`
  and `type.__new__` are CPython as documented. The OUT OF SCOPE cell states exactly (A) and it is
  honest.
- **(B) The platform does not permit preventing ADMISSION of a forged object at a door.** The RISK
  headline asserts (B). **NOTHING IN THIS TREE TESTS (B).**

### 4.1 Exact type cannot discriminate, and that is the whole reason (B) matters

```
$ cd /tmp/cd-asr-wo2r3-05 && python3 -B p_q2c_prevention_feasibility.py /tmp/cd-asr-wo2r3-05/tip
tree: /tmp/cd-asr-wo2r3-05/tip
  DISCRIMINATOR 1 — EXACT TYPE, which is what every door in this tree uses
  type(genuine) is DeclaredQuantity -> True
  type(forged)  is DeclaredQuantity -> True
  RESULT: **THE TWO ARE INDISTINGUISHABLE.**
```

Exact type asks *"what type is this?"* — a question the F1 forger controls perfectly, because the
forger **is** the exact type. That is not a weakness in the implementation; it is the ceiling of the
predicate.

### 4.2 A discriminator that separates them DOES exist on this platform. Measured, both arms.

```
$ cd /tmp/cd-asr-wo2r3-05 && python3 -B - /tmp/cd-asr-wo2r3-05/tip <<'PY' ... PY
tree: /tmp/cd-asr-wo2r3-05/tip
crash_detector imported from: /tmp/cd-asr-wo2r3-05/tip/src/crash_detector/__init__.py

FACT 1 — why the obvious mechanism is not free here (MEASURED, not assumed):
  DeclaredQuantity.__slots__ = ('dials', '__value')
  weakref.ref(genuine) -> TypeError: cannot create weak reference to 'DeclaredQuantity' object

FACT 2 — but SOME in-process discriminator DOES exist on this platform:
  type(g) is type(f)          -> True   <- exact type CANNOT separate them
  from_declared_door(genuine) -> True
  from_declared_door(forged)  -> False
  *** SEPARATED IN-PROCESS AT ADMISSION TIME: True ***

FACT 3 — the honest limit, measured:
  after an in-process actor enrols the forgery directly -> True
```

**A CONSTRUCTION-PROVENANCE DISCRIMINATOR — "did this object come out of a declared door?" — SEPARATES
THE GENUINE ARTICLE FROM THE F1 FORGERY, IN-PROCESS, AT ADMISSION TIME, WITHOUT PREVENTING
CONSTRUCTION.** So (B) as stated is false: the platform does permit *a* prevention at the door. It is
not absolute — FACT 3 measures its defeat — but the F1 forgery against exact type costs **zero package
lines and zero knowledge of this codebase**, whereas defeating a construction-provenance door requires
locating and mutating a module-private structure. **That is a difference in kind and the perimeter
does not make it.**

**AND NOTE WHAT THAT MECHANISM IS CALLED.** `CD-D-172` already names it: **"the provenance chain"**,
one of the two mechanisms of the DETECTED half. **The project has already identified the mechanism
that answers the F1 route, and has classified it as detection owed at WO-3 rather than asking whether
it is available as admission-time prevention now. It has never measured which it is.**

### 4.3 What I am NOT saying, precisely

I am **not** proposing an implementation and I have modified nothing (`PBG-SOD-004`; the probe wraps
the declared door from outside the package). I found a real obstacle the record should own: FACT 1
shows the obvious `WeakSet` form is **not** available here, because `DeclaredQuantity.__slots__` omits
`__weakref__` and adding it widens the declared attribute surface this project deliberately guards.
**That is exactly the kind of measured constraint a scope claim should rest on — and the perimeter
rests on none. It rests on an assertion.**

### 4.4 THE FINDING

**`CD-ASR-WO2R3-05-F04`, MEDIUM.** The OUT OF SCOPE half is **honest about construction and overbroad
about prevention**. `CD-RULE-003` requires derive-or-fail-closed; the scope boundary of the entire
perimeter is set by a claim — "the platform does not permit preventing it" — that **no instrument,
probe, plant or test in this tree derives.** Section 2 shows the cost of that untested width is not
theoretical: it is the difference between a forged number reaching the presentation surface and being
refused there.

I am **not** finding that the perimeter is wrongly drawn beyond repair, and I am not finding bad faith
— the record is unusually candid throughout. I am finding that **the most consequential line in the
perimeter is the only one nobody measured**, on a project whose own rule is that a plausible number is
not a derived one.

---
## SECTION 5 — T20. THE `CD-D-115` CARRIAGE. **FINDING F05 (MEDIUM).**
## THE PROJECT LEAD CANNOT GRADE ITS OWN ACT, SO HERE IS THE GRADE.

`CD-D-115` protects `BLUEPRINT.md` from every seat **including the Project Lead**. The Project Lead
wrote to it anyway, relying on PO-DECISIONS-0018 ruling 5's parenthetical *"PO-authored text carried
verbatim where protected"*.

### 5.1 What I did that the Project Lead's own check cannot do

`tools/reconciliation/check_blueprint_carried_po_text_verbatim.py` exits 0 with *"4/4 sentences
resolve in BOTH files"*. **It was written by the Project Lead to certify the Project Lead's own act**
— which is not independent evidence (`PBG-EVID-001`: *"Evidence is produced independently of what it
certifies... a manifest that vouches for itself... none of these are evidence"*). Its own DECLARED
LIMIT 2 concedes it proves nothing about what else the carriage added.

**So I measured the inverse: not "did the quoted bytes arrive intact" but "what bytes arrived that
were never quoted".**

```
$ cd /tmp/cd-asr-wo2r3-05 && python3 -B p_t20_carriage_inverse.py
repo: /srv/crash-detector
repo HEAD: baede050435d3ede55456724d0712250f08d6de3
BASE 184c3e1 -> 184c3e1f6ea38dd76f31e1fa7f07d47aa5f9a472
TIP  00ef57e -> 00ef57e69ae18f073d1f6c2e5d635099a5edc5a2
PO   c72b6ea -> c72b6ea1fdb90e0c59d1a0a83d2bd6dcee0c167d

lines ADDED to BLUEPRINT.md by the carriage: 52
CARRIED (normalised text resolves in PO-DECISIONS-0018.md@c72b6ea): 22
AUTHORED (does NOT resolve there):                                  28
```

Phrase-level confirmation (`grep` against the Product Owner's own file, paste-able):

```
$ for s in "not as a note" "residue paragraph" "manual step" "two named mechanisms" \
           "zero registry rows" "Seven gates and two programmes" \
           "honest architecture is in three parts"; do
    printf '%-45s' "\"$s\""
    grep -qi "$s" governance/decisions/PO-DECISIONS-0018.md && echo "PRESENT" || echo "**ABSENT**"
  done
"not as a note"                              **ABSENT from PO ruling**
"residue paragraph"                          **ABSENT from PO ruling**
"manual step"                                **ABSENT from PO ruling**
"two named mechanisms"                       **ABSENT from PO ruling**
"zero registry rows"                         **ABSENT from PO ruling**
"Seven gates and two programmes"             PRESENT in PO ruling
"honest architecture is in three parts"      **ABSENT from PO ruling**
```

### 5.2 WHAT I FOUND IN THE PROJECT LEAD'S FAVOUR, AND IT MATTERS

**The Build Log enumeration at `BL-20260823T095521Z-0131` is ACCURATE AND COMPLETE.** It declares
*"EXACTLY FIVE THINGS, AND NOTHING ELSE"* and item (2) covers the §16 framing prose while item (5)
covers *"the 'what is therefore OWED' and 'default safe action' paragraphs"*. **Every one of my 28
authored lines falls inside those five items. I could not find a sixth.** The quoted PO blockquotes
are faithful. The Project Lead also named item (3) as its own weakest, unprompted, and it was right
to — see `F02`, which lands there.

**On the narrow question "did the carriage stay inside the authority it claims?" for the QUOTED
bytes: it did.** That part is a `PASS` and I say so plainly.

### 5.3 BUT THE PROTECTED FILE'S OWN HEADER UNDERSTATES ITS OWN AUTHORSHIP

`BLUEPRINT.md` status header, authored bytes, in the protected file itself:

> **"the Project Lead authored the version bump, the row IDs and the table scaffolding and NOTHING
> ELSE — enumerated at BL-20260823T095521Z-0131"**

That names **THREE** things and says *"NOTHING ELSE"*. The Build Log it points at enumerates
**FIVE**, and the two it omits — (2) the §16 framing prose and (5) the two substantive paragraphs —
are the only **normative** bytes in the whole carriage. **A reader of `BLUEPRINT.md` alone, which is
the accepted product artefact, is told the Project Lead wrote scaffolding. It wrote two paragraphs
of standard-setting prose.**

### 5.4 AND TWO OF THE AUTHORED SENTENCES ARE NORMATIVE, AND ONE OF THEM IS WRONG

Both are inside authored item (5), both absent from the Product Owner's ruling:

1. **"verified as a FIRST-CLASS CRITERION — *not as a note, not as a residue paragraph, and not as a
   manual step*."** The Product Owner wrote *"verified as a first-class criterion"* and stopped. **The
   Project Lead authored the form requirement.** Per **`F03`**, the record then carries the obligation
   in a note and a residue paragraph — **two of the three forms the Project Lead itself ruled out.**
   The Project Lead wrote the standard and the same increment fails it.
2. **"It cannot be specified before WO-3 because with zero registry rows there are no witnesses to
   diverge from."** The Product Owner wrote *"specified at WO-3 when real sources land"* and gave no
   reason. **The Project Lead authored the justification** — and per **`F03`** that justification is
   contradicted by §14 and §15 of the same file, which put witnesses live and the divergence alarm at
   **WO-4**.

### 5.5 THE FINDING

**`CD-ASR-WO2R3-05-F05`, MEDIUM.** The carriage is **substantially faithful and unusually well
disclosed**, and I uphold the Build Log's enumeration as complete. But (i) the protected file's own
status header describes the Project Lead's authorship as three scaffolding items and *"NOTHING ELSE"*
when its own cited Build Log enumerates five including two normative paragraphs; and (ii) within
those paragraphs the Project Lead authored, **in a file protected from it**, a normative form
requirement that this increment does not meet and a scheduling justification that the same file's
delivery table contradicts.

**This is not a bypass and I do not grade it as one.** `CD-D-115`'s purpose is that no seat invents
product meaning, and the authority relied on is real. But authored normative bytes in a protected
file are exactly what `CD-D-115` exists to catch, and **the mechanism that was supposed to make them
auditable — the header's own "NOTHING ELSE" — is narrower than the truth.** The correct remedy is a
Product Authority question, not a seat's edit, and it is not mine to make.

---
## SECTION 6 — T2 + T3. **FINDING F06 (HIGH) — I OBTAINED THE SWEEP `PASS` AND THE 1726/0 SUITE
## OVER CODE WHOSE `EXACT` DECLARATION IS FALSE. BY RE-POINTING, NOT BY DELETING.**

The dispatch (T2) asked me to try to obtain the green *"by deletion, by re-pointing to a
wrong-but-live site, or by any route the Project Lead's one-row arm did not probe."*
**The re-pointing route works.**

### 6.1 Setup — a throwaway extraction, never the target tree

```
$ rm -rf /tmp/cd-asr-wo2r3-05/t3 && mkdir -p /tmp/cd-asr-wo2r3-05/t3
$ cd /srv/crash-detector-wo2r3-audit8 \
    && git archive be0b355e4b9c39b65b7ca38e75e063ab2c5f40a5 | tar -x -C /tmp/cd-asr-wo2r3-05/t3
```

### 6.2 STEP 1 — reorder the two operand pairs only. **The project DOES notice.**

`src/crash_detector/admission.py`:716 and :766, the two rows `CD-ENG-WO2R3-09-F05` named:

```
716:  - if type(because) is not str or not because.strip():
716:  + if not because.strip() or type(because) is not str:
766:  - if type(within) is not tuple or not within:
766:  + if not within or type(within) is not tuple:
```

```
$ cd /tmp/cd-asr-wo2r3-05/t3 && python3 -B tools/sweep/delegated_judgement_sweep.py --root .
$ rc=$?; echo "SWEEP_RC=$rc"
SWEEP_RC=1
CD-CLASS-2-SWEEP: FAIL — 548 sites, 3 violations
$ python3 -B -m pytest -q -p no:cacheprovider
$ rc2=$?; echo "PYTEST_RC=$rc2"
PYTEST_RC=1
3 failed, 1723 passed in 52.25s
```

**So `CD-ENG-WO2R3-09-F05` as written — *"REORDER EITHER PAIR AND THE ROW IS FALSE AND NOTHING IN
THIS PROJECT WOULD NOTICE"* — is TOO PESSIMISTIC, and I correct it in the project's favour.
Something notices.** But what it notices is that the **source text moved** (the disposition key is
`(module, callable, KIND, SOURCE TEXT)`, so the row goes STALE). It does not notice that the
property broke.

### 6.3 STEP 2 — re-point the two keys to the new text. **NOTHING NOTICES ANYTHING.**

`tools/sweep/declared_dispositions.py`:923 and :1565 — two string literals, updated to match:

```
$ cd /tmp/cd-asr-wo2r3-05/t3 && python3 -B tools/sweep/delegated_judgement_sweep.py --root .
$ rc=$?; echo "SWEEP_RC=$rc"
SWEEP_RC=0
CD-CLASS-2-SWEEP: PASS — 548 sites enumerated over 19 modules; every tier-1 admission and every
subject module carries a written or DERIVED disposition; 6 sites and 0 modules are declared OPEN...
$ python3 -B -m pytest -q -p no:cacheprovider
$ rc2=$?; echo "PYTEST_RC=$rc2"
PYTEST_RC=0
1726 passed in 52.81s
```

**IDENTICAL TO THE PRISTINE TIP IN EVERY CELL: sweep `PASS`, 548 sites, rc=0; suite 1726 passed,
rc=0.**

### 6.4 AND THE PROPERTY REALLY IS FALSE. BOTH ARMS, SAME PROBE, TWO TREES (CD-D-079, CD-PL-F98).

```
$ for T in /tmp/cd-asr-wo2r3-05/tip /tmp/cd-asr-wo2r3-05/t3; do ... done

================ TREE: /tmp/cd-asr-wo2r3-05/tip ================
crash_detector imported from: /tmp/cd-asr-wo2r3-05/tip/src/crash_detector
  ESTABLISHED_HERE(Hostile()) -> REFUSED AdmissionFault: ESTABLISHED_HERE requires a stated reason.
  caller code executed inside the guard? False []

================ TREE: /tmp/cd-asr-wo2r3-05/t3 ================
crash_detector imported from: /tmp/cd-asr-wo2r3-05/t3/src/crash_detector
  ESTABLISHED_HERE(Hostile()) -> REFUSED AdmissionFault: ESTABLISHED_HERE requires a stated reason.
  caller code executed inside the guard? True ['CALLER CODE RAN INSIDE THE ADMISSION GUARD']
```

The probe is an object whose `strip()` records that it ran. **At the tip the guard establishes the
type first and the caller's code never executes. In the re-pointed tree the guard calls the
caller's method BEFORE establishing its type — and the refusal message is character-for-character
identical, so nothing downstream can tell the two apart.**

**That is delegated judgement at a tier-1 admission site: precisely the Class-2 defect
`delegated_judgement_sweep.py` exists to enumerate, at a row declaring itself `EXACT`, with the
sweep exiting 0 and calling it `EXACT`.**

### 6.5 THE FINDING

**`CD-ASR-WO2R3-05-F06`, HIGH.** The Class-2 register verifies that **a key exists**, not that
**its claim is true**. Re-pointing a key — a one-line clerical edit — converts "the guard noticed"
into "the guard is silent", with no layer measuring the property the disposition asserts.

**THIS IS NOT HYPOTHETICAL. INCREMENT 10 ITEM 5 RE-POINTED SIXTEEN ROWS.** The Engineer disclosed
the exposure itself (`F05`: *"16 rows now claim `EXACT` on that seat's authority and the sweep
cannot check one of them"*). **I have now measured what that exposure is worth: it is worth a full
green board over code whose declaration is false.** The Project Lead's own counterfactual — deleting
one row — probes the register's *arithmetic*. It does not probe its *truth*, and the truth is the
part with no guard.

**The `PASS` at `be0b355` is not thereby shown to be false** — I have no evidence any of the 16
re-pointed rows is actually wrong, and the deletion arm shows the arithmetic is sound. **What is
shown is that the `PASS` is not evidence that they are right.** On a project whose own dispatch says
*"THIS IS THE SHAPE OF EVERY ESCAPE ON THIS RECORD — A PROPERTY THAT HOLDS BY AN ACCIDENT OF
EXPRESSION WITH NO LAYER MEASURING IT"*, that gap is the finding.

---
## SECTION 7 — THE INSTRUMENT SURVEY, RE-MEASURED BY THIS SEAT AND NOT INHERITED

### 7.1 All fourteen register checks, exit code captured on the line immediately after (CD-PL-F131)

```
$ cd /srv/crash-detector-wo2r3-audit8 && git rev-parse HEAD
be0b355e4b9c39b65b7ca38e75e063ab2c5f40a5
$ for f in tools/register/check_*.py; do
    python3 -B "$f" --root . > /tmp/cd-asr-wo2r3-05/reg_$(basename $f .py).out 2>&1
    rc=$?
    printf '%-4s %s\n' "$rc" "$f"
  done
0    tools/register/check_base_image_digest_pin.py
0    tools/register/check_constructor_field_establishment.py
0    tools/register/check_dockerignore.py
0    tools/register/check_egress_no_broker.py
0    tools/register/check_engine_no_witness_reach.py
0    tools/register/check_exact_type_admission.py
3    tools/register/check_grant_matrix_live.py
0    tools/register/check_judgement_path_doors.py
0    tools/register/check_lockfile_denylist.py
0    tools/register/check_no_blend.py
0    tools/register/check_no_execution_interface.py
0    tools/register/check_no_numeric_default.py
0    tools/register/check_schema_closed.py
0    tools/register/check_sealed_against_forged_establishment.py
$ git status --porcelain | wc -l
0
```

**THIRTEEN EXIT 0, ONE EXIT 3.** Confirmed by my own run, not inherited.

### 7.2 The suite and the sweep, my own runs

```
$ cd /srv/crash-detector-wo2r3-audit8 && python3 -B -m pytest -q -p no:cacheprovider
$ rc=$?; echo "PYTEST_RC=$rc"
1726 passed in 52.66s
PYTEST_RC=0

$ python3 -B tools/sweep/delegated_judgement_sweep.py --root .
$ rc=$?; echo "SWEEP_RC=$rc"
SWEEP_RC=0
CD-CLASS-2-SWEEP: PASS — 548 sites enumerated over 19 modules ...
```

Both match the dispatch. **The worktree was porcelain 0 before and after every run in this audit.**

### 7.3 `CD-RT-012` — ITS GRADE IS MINE TO SET AND I SET IT HERE

`tools/register/check_no_execution_interface.py` **EXITS 0 at `be0b355`** (§7.1, my own run).
**`CD-PL-F133` IS UPHELD: the standing claim "CD-RT-012 RED at the tip", which travelled through
four boundaries, two Assurance briefs and two Engineer briefs, IS FALSE.** I grade `CD-RT-012`
**GREEN at `be0b355`**, on my own measurement, with the caveat in §7.6 that a green exit is not a
proof of the property.

### 7.4 T5 — WHAT DID ITEM 1 ACTUALLY BUY? THE ENGINEER'S SELF-DISCLOSURE IS HONEST.

```
$ cd /srv/crash-detector-wo2r3-audit8 && git rev-parse 686a374
686a374e60ff8f18305fa8b665463e0e057dac2b
$ git archive 686a374 | tar -x -C /tmp/cd-asr-wo2r3-05/base
$ cp tools/register/check_exact_type_admission.py /tmp/cd-asr-wo2r3-05/base/tools/register/
$ cd /tmp/cd-asr-wo2r3-05/base && python3 -B tools/register/check_exact_type_admission.py --root .
$ rc=$?; echo "T5_BASE_RC=$rc"
T5_BASE_RC=0
CD-RT-002-EXACT-TYPE-ADMISSION: PASS — 36 assertions, 0 violations       <- BASE 686a374
CD-RT-002-EXACT-TYPE-ADMISSION: PASS — 36 assertions, 0 violations       <- TIP  be0b355
```

**IDENTICAL.** `CD-ENG-WO2R3-08-F07` is confirmed: the new guard's green is **not** evidence that
increment 10 fixed those four doors — they were already exact-type at base. It is a **regression
lock on behaviour that already held.** The seat declared this in three places unprompted, and
**I find no document that overstates it** (§7.5). That is the disclosure discipline working.

What item 1 therefore bought, stated honestly: 12 tier-1 sites converted, 18 declared with reasons,
a regression lock, and — the one thing of real substance — **`CD-ENG-WO2R3-08-F02`**, the discovery
that the register's ground *"Criticality is an enum ... so isinstance and exact type coincide"* is
**false**, since an object with `@property __class__` passes `isinstance` and fails exact type.
**That finding is worth the increment on its own.**

### 7.5 Q4 — DOES ANY INSTRUMENT, DOCUMENT OR REGISTER ROW STILL CLAIM MORE THAN THE PERIMETER
### ALLOWS? **ON THE LANE: NO. AND THAT IS A REAL RESULT.**

```
$ cd /srv/crash-detector-wo2r3-audit8 && grep -rniE \
   "F01 (is )?(now )?closed|CD-AC-002 (is )?closed|CD-AC-005 (is )?closed|class is sealed|is now sealed|forgery is prevented" \
   src/ tools/ tests/ contracts/ required-tests.yaml
```

**Every single hit is a DISCLAIMER, not a claim.** Representative:

- `tools/register/check_exact_type_admission.py:346` — *"...does not claim the forgery is prevented,
  that any class is sealed, or that CD-ASR-F01 is closed."*
- `contracts/execution/CD-RT-002-EXACT-TYPE-ADMISSION.md:18` — *"Deliberately **not** 'the forged
  type is prevented', **not** 'the class is sealed', and **not** 'CD-ASR-F01 is closed'."*
- `tests/test_the_declared_limits_reach_the_exit.py:147` —
  `assert "NOT that CD-ASR-WO2R3-04-F01 is closed" in result.stdout`

**There is a TEST asserting the disclaimer reaches the exit text.** I ran the suite; it passes. I
looked for an instrument, contract or register row claiming more than the perimeter allows and
**I could not find one.** `CD-RULE-004` applied to the whole tree at once comes back clean on the
lane.

**THE ONE OVERCLAIM I FOUND IS NOT IN AN INSTRUMENT. IT IS IN `BLUEPRINT.md` §17, IN THE PROJECT
LEAD'S OWN AUTHORED PROSE — the word "useless" (`F02`) — AND IN §16's AUTHORED FORM REQUIREMENT AND
WO-3 JUSTIFICATION (`F03`, `F05`).** The instruments were disciplined. The Blueprint was not.

### 7.6 T6 — `check_grant_matrix_live` EXIT 3, RE-MEASURED RATHER THAN INHERITED. **CORRECTION
### UPHELD, AND ONE THING THE INHERITANCE HIDES.**

Arm 1, as the register declares it:

```
$ cd /srv/crash-detector-wo2r3-audit8 && python3 -B tools/register/check_grant_matrix_live.py --root .
$ rc=$?; echo "rc=$rc"
rc=3
CD-RT-003-GRANT-MATRIX-LIVE: PRECONDITION_NOT_MET
    the connection target is not set: CD_CHECK_STORE_HOST, CD_CHECK_STORE_PORT,
    CD_CHECK_STORE_NAME, CD_CHECK_STORE_USER, CD_CHECK_STORE_PASSWORD.
```

**The fourth seat's correction is CONFIRMED: exit 3 never meant "database unreachable". It means the
five documented environment variables were never exported.** Four seats inherited that correction;
I have now re-measured it and it holds.

Arm 2 — the one nobody ran. I supplied the five variables, pointed at a closed port:

```
$ export CD_CHECK_STORE_HOST=127.0.0.1 CD_CHECK_STORE_PORT=59999 \
         CD_CHECK_STORE_NAME=nonexistent_db CD_CHECK_STORE_USER=nobody CD_CHECK_STORE_PASSWORD=x
$ python3 -B tools/register/check_grant_matrix_live.py --root .
$ rc=$?; echo "ARMED_RC=$rc"
ARMED_RC=3
CD-RT-003-GRANT-MATRIX-LIVE: PRECONDITION_NOT_MET
    the store at nobody@127.0.0.1:59999/nonexistent_db is UNREACHABLE: connection to server at
    "127.0.0.1", port 59999 failed: Connection refused ... (the credential is redacted from this
    message by construction). A check that cannot reach its subject reports that it could not, and
    never that the subject was clean.
```

**The instrument behaves correctly** — it distinguishes the two states in its message, refuses to
report a clean subject it could not reach, and redacts the credential. Good.

**FINDING `CD-ASR-WO2R3-05-F07`, LOW.** `CD-RT-003-GRANT-MATRIX-LIVE` **has never, on this
project's entire record, been observed executing against a live store.** Both of its reachable
states are exit 3. Per my role contract, a check that cannot reach its authentic target returns
`UNSUPPORTED` and never a PASS against a substitute. **So `CD-AC-003`'s live-grant-matrix evidence
is `UNSUPPORTED`, not satisfied**, and any grade resting on it should say so. The instrument is not
at fault; the record's habit of listing it as "a documented environment condition" alongside thirteen
zeros invites the reader to treat it as accounted for rather than as an unexecuted criterion.

### 7.7 T22 — `CD-D-173`. **UPHELD. I DERIVED IT RATHER THAN ACCEPTING IT.**

```
$ cd /srv/crash-detector-wo2r3-audit8 && ls governance/engineering/build-log/ \
    | sed -E 's/.*-([0-9]{4})\.yaml/\1/' | sort -n | awk '$0>=60 && $0<=99' | wc -l
40
$ ls governance/engineering/build-log/ | sed -E 's/.*-([0-9]{4})\.yaml/\1/' | sort -n | tail -1
0099
$ ls governance/engineering/build-log/ | grep -cE '\-02[0-9]{2}\.yaml'
0
```

`0060-0099` holds **exactly 40 contiguous entries and is full**; the highest lane number is `0099`;
block `0200-0299` is **empty**; `main` is at `0133` inside `0100-0199`. **No collision, no renumber,
no landed entry touched.**

**I uphold `CD-D-173` and I uphold its classification as a Project Lead decision.** It allocates a
range inside a numbering scheme the Project Lead already established (`CD-D-132`, same shape, same
reasoning), moves no product decision, changes no grade and renames nothing. That is exactly the
class of Level 1 administrative choice `BLUEPRINT.md` §16 records the Project Lead as taking rather
than escalating. **It was disclosed rather than buried, which is the behaviour the record should
reward.** If the Product Owner reads range allocation as reserved, this is cheap to overturn — but
on the governance as written, it is correctly placed.

---
## SECTION 8 — T7 / T23. **FINDING F08 (MEDIUM) — THE INHERITED-CLAIM MECHANISM IS SYSTEMIC,
## AND `CD-PL-F133`'S OWN SCOPE STATEMENT UNDERCOUNTS IT.**

The dispatch says a dead *"CD-RT-012 RED at the tip"* travelled through **four** boundaries and four
briefs, and asks how many other standing claims have never been re-measured. I measured the first
part rather than accepting it.

### 8.1 When did it actually go green?

```
$ cd /srv/crash-detector-wo2r3-audit8 && git log -1 --format='%H%n%ad%n%s' --date=iso-strict f770935
f770935dad1964e8d4ccdd58b4776dcf3f1be4bd
2026-08-23T07:06:26+01:00                    (= 06:06:26Z)
[CD-ENG-WO2R3-06] ITEM_2 — CD-RT-012 IS GREEN, AND IT IS GREEN BY A GRAMMAR CORRECTION ...
```

### 8.2 How many documents still asserted it RED after that moment?

```
$ grep -rliE "CD-RT-012[^.]{0,60}(RED AT THE TIP|STILL RED)" governance/ | wc -l
20
$ for f in $(grep -rliE "CD-RT-012[^.]{0,60}(RED AT THE TIP|STILL RED)" \
             governance/engineering/build-log/ | sort); do
    ts=$(basename "$f" | sed -E 's/BL-([0-9]{8}T[0-9]{6})Z-.*/\1/')
    [[ "$ts" > "20260823T060626" ]] && echo "  AFTER  $ts  $(basename $f)"
  done
  AFTER  20260823T071148  BL-20260823T071148Z-0124.yaml
  AFTER  20260823T072032  BL-20260823T072032Z-0125.yaml
  AFTER  20260823T082937  BL-20260823T082937Z-0126.yaml
  AFTER  20260823T083655  BL-20260823T083655Z-0127.yaml
  AFTER  20260823T091648  BL-20260823T091648Z-0128.yaml
  AFTER  20260823T095521  BL-20260823T095521Z-0131.yaml
  AFTER  20260823T105756  BL-20260823T105756Z-0132.yaml   <- the boundary that CAUGHT it
```

**SIX BOUNDARIES CARRIED THE FALSE PRESENT-TENSE CLAIM BEFORE THE SEVENTH CAUGHT IT** (`0124`,
`0125`, `0126`, `0127`, `0128`, `0131`), plus the Engineer and Assurance briefs built from them.

**`CD-PL-F133` SAYS FOUR. THE MEASURED NUMBER IS SIX.** I am not scoring that harshly — it is a
self-raised finding and self-raised findings are how this project has improved — but **it is the
inherited-claim defect appearing inside the finding about the inherited-claim defect**, which is
exactly the recursion `CD-PL-F132` recorded when `CD-PL-F112`'s "structural fix" held eight
boundaries and failed at the ninth.

### 8.3 THE MECHANISM, WHICH IS THE PART THAT MATTERS

I read the carriers rather than just counting them. **The false clause does not travel alone. It
travels inside a fixed multi-clause boilerplate that is copied as ONE STRING:**

> *"T2 RED; CD-AC-002 and CD-AC-005 AMBER and NOT CLOSED; `CD-RT-012` RED at the tip; the WO-2 gate
> SHUT."*

**Three of those four clauses were true at every boundary. The fourth was false from 06:06:26Z
onward. Because they travel as one unit, the true clauses carry the false one** — a reader
verifying the block finds it substantially right and moves on. **That is the mechanism, and it is
not fixed by finding one instance of it.**

### 8.4 WHAT I DID *NOT* FIND, AND SAY SO PLAINLY

I looked for other dead claims of the same shape and **found none that are currently false**:

- **`check_grant_matrix_live` exit 3** — repeated across at least nine documents. **I re-measured it
  (§7.6). It is TRUE.**
- **13 exit 0 / 1 exit 3** — **I re-measured all fourteen (§7.1). TRUE.**
- **`DEFECT_OPEN` count** — documents before increment 10 say TEN, the current record says SIX.
  **I measured SIX at `be0b355` (§9.2). The change is real, not drift; the older figures were
  correct when written.**
- **The plant tally 11 -> 13 -> 14** — the set genuinely grew. Not drift.
- **`CD-CLASS-2-SWEEP: FAIL — 534 sites, 15 violations`**, repeated across many documents, was
  superseded at `BL-...-0118` and the superseding entry says so.

**So the record's *current* state claims are, as far as I could measure them, accurate.** The defect
is not a stock of live falsehoods; it is the **absence of a re-measurement step**, which produced one
six-boundary falsehood and will produce another.

### 8.5 THE FINDING

**`CD-ASR-WO2R3-05-F08`, MEDIUM.** The record has no mechanism that re-measures a standing state
claim before restating it, and its claims are structurally bundled so that true clauses vouch for
false ones. `CD-PL-F133` found one instance by accident and **undercounted its own reach by
50 % (four stated, six measured)**.

**And T23's open question — "when a rule is adopted, is the record swept backward for the instances
that motivated it?" — I can now answer from measurement: NO.** The sweep-backward has never been
performed on this project, for any rule. `CD-PL-F133` was raised at `BL-...-0132`; the six prior
boundaries carrying the false clause were **not** enumerated at that time, and I enumerated them
here for the first time.

---
## SECTION 9 — T9. THE SIX `DEFECT_OPEN` SITES. **ONE OF THEM CARRIES A STALE REACH (F09, LOW).**

### 9.1 Are they right to remain, or is `DEFECT_OPEN` parking things?

I read all six in full (`tools/sweep/declared_dispositions.py`). **They are not parking.** Each
carries a `measured_reach`, a `counterfactual` and a `note`, most with re-measured evidence quoted
inline, and the register itself says in its own exit text *"**A REGISTER FULL OF `DEFECT_OPEN` BUYS
NOTHING** — not a pass of any gate, not an exemption, and it does not mean anything was repaired."*
Three of the six are explicitly held open by ruling (`CD-D-153`) or declared out of the acting
dispatch's reach. **That is a register being honest about open defects, and I grade the practice as
sound.**

The most consequential of the six, and it deserves naming: **`CD-F-0004`** —
`establishment._declared_field_list`. A plain class carrying `__dataclass_fields__ = {}` passes the
`is_dataclass` probe, `establishes()(Hostile)` **succeeds**, and *"Hostile ENTERS `governed_types()`
(7 -> 8 under a full package import)"*. **An in-process actor can inject a class into the governed
type set through a PUBLIC exported entry point.** It is declared, open, and unremediated.

### 9.2 The count, my own derivation

```
$ cd /srv/crash-detector-wo2r3-audit8 && python3 -B - <<'PY'
  import sys; sys.path.insert(0, "tools/sweep"); import declared_dispositions as dd
  ... classify each tier-1 row by its disposition word ...
PY
TIER-1 rows in the declaration table: 33
Counter({'ESTABLISHED': 14, 'EXACT': 8, 'DEFECT_OPEN': 6, 'CARRIER_ONLY': 3, 'OWN': 2})
```

**SIX `DEFECT_OPEN`, THREE `CARRIER_ONLY`, 33 tier-1 total. Confirmed.** Matches the sweep's own
tally (`ESTABLISHED 14 | EXACT 8 | OWN 2 | DEFECT_OPEN 6 | CARRIER_ONLY 3` = 33) and the dispatch.

**And a number worth stating that no document states: only 8 of the 33 tier-1 admission sites carry
`EXACT`, and all eight are either `isinstance(x, bool)` (a type CPython forbids subclassing) or
`isinstance(base, Sealed*Type)` inside a metatype `__new__`. NOT ONE of the eight is a
judgement-path admission door of the form `type(x) is T`.** Sites converted to exact type leave the
tier-1 enumeration entirely, which is why the count fell 30 -> 18 — a fact the record states as a
win without stating that the denominator moved for the same reason.

### 9.3 **FINDING F09 (LOW) — `CD-F-0002`/`CD-F-0003`'s DECLARED REACH IS STALE AT THE TIP.**

The row for `('crash_detector.admission', '_compile', 'ISINSTANCE', 'isinstance(declaration, type)')`
declares its `measured_reach` as:

> *"A metaclass defining `__eq__` satisfies `isinstance(X, type)` here and then compares EQUAL TO
> EVERY TYPE at `_Exactly.refusal`. Measured end to end on an ordinary `@admits(value=Wildcard)`
> door: `faults: ()`, `is_admitting_door: True`, and **every value admitted**."*

I re-measured that exact scenario at `be0b355`:

```
$ cd /tmp/cd-asr-wo2r3-05 && python3 -B - /tmp/cd-asr-wo2r3-05/tip <<'PY' ... PY
tree: /tmp/cd-asr-wo2r3-05/tip/src/crash_detector
is_admitting_door: True
faults: ()
  offered int      -> REFUSED NotAdmitted: an_ordinary_door: value=int is not admitted; ...
  offered str      -> REFUSED NotAdmitted: ...
  offered float    -> REFUSED NotAdmitted: ...
  offered object   -> REFUSED NotAdmitted: ...
```

**Two of the three stated observations still hold (`faults: ()`, `is_admitting_door: True`). THE
LOAD-BEARING ONE — "every value admitted" — IS FALSE AT THE TIP.** Increment 8's `is_exactly`
(identity, never `==`) closed the downstream half, so the metaclass's `__eq__` has nothing left to
answer.

**The `DEFECT_OPEN` CLASSIFICATION ITSELF MAY WELL STILL BE CORRECT** — the site is still an
`isinstance` and still admits a metaclass subclass as a *declaration*. **What is stale is the
described CONSEQUENCE.** This is the `F08` mechanism again — a present-tense `measured_reach` carried
forward across the very increment that changed it — but in the **conservative** direction: the
register overstates a defect it declares open, making the project look worse than it is. I grade it
**LOW** for that reason, and record it because a register whose reasons have died *"does not survive
on habit"* is this project's own stated rule (`declared_dispositions.py`), and because **increment 10
re-pointed sixteen rows without re-measuring the reaches attached to them** (see `F06`).

---
## SECTION 10 — THE RE-GRADE OF `CD-AC-002` AND `CD-AC-005` (PO-DECISIONS-0018 RULING 6)

Ruling 6 puts both in front of me *"against the declared perimeter, where 'by construction' claims
exactly what construction can hold and detection owns the rest."* That is the right frame, and it
resolves cleanly once you ask what construction can hold.

### 10.1 `CD-AC-005` — **RED. THE SEVENTH SEAT'S MOVE IS SUSTAINED, ON MY OWN MEASUREMENT.**

I did not inherit this. I measured the criterion's own stated property — *"unavailable is not
agreement"*, *"reaching `Agrees` requires a MEASUREMENT"* — both arms:

```
$ cd /tmp/cd-asr-wo2r3-05 && python3 -B - /tmp/cd-asr-wo2r3-05/tip <<'PY' ... PY
tree: /tmp/cd-asr-wo2r3-05/tip/src/crash_detector

=== ARM 1 (contrast): the DECLARED route to Agrees without freshness evidence ===
  -> REFUSED crash_detector.witness.panel.AgreementWithoutFreshnessEvidence:
     Agrees requires FreshnessEvidence, got NoneType. Reaching agreement requires a MEASUREMENT...
  panel_state(genuine Unavailable) -> UNAVAILABLE

=== ARM 2: the F1 forgery of Agrees ===
  package lines to forge an Agrees: 0
  type(fake) is Agrees -> True
  panel_state(forged Agrees) -> 'AGREES'
```

**ARM 1 REFUSES — the accident-proofing ruling 1(a) keeps is real and I confirm it.** **ARM 2
SUCCEEDS: an `Agrees` carrying `freshness=None`, built with ZERO package lines, is reported
`'AGREES'` by the product's own `panel_state`.** A witness panel that never measured anything
corroborates, while looking like corroboration — which `panel.py`'s own header calls *"worse than no
panel at all, because it manufactures confidence."*

**`CD-AC-005`: RED.** Its property is not held. Under the perimeter this residue belongs to
DETECTION — and detection does not exist and is not scheduled in the form its own decision requires
(`F03`). A criterion whose assigned defence is unbuilt is not AMBER; it is unmet.

### 10.2 `CD-AC-002` — **AMBER, NOT CLOSED. I DECLINE TO MOVE IT.**

`CD-AC-002` is the *"no number is published without established provenance"* criterion.
**Section 2 shows its property is defeated in-process**: a forged magnitude reached `Shown` and
released `999.0` through `quantity_for`. But Section 2 also shows the doors refuse **every route the
perimeter says they refuse** — foreign look-alikes, bare floats, forged subclasses, cross-dial
provenance — with declared refusal identities. The failing route is the one the perimeter declares
OUT OF SCOPE for prevention and assigns to detection.

**So `CD-AC-002` sits exactly where ruling 6 predicted: "by construction" holds precisely what
construction can hold, and no more.** I hold it **AMBER and NOT CLOSED**, and I record that it cannot
move to PASS while `F03` stands, because the half that owns its residue is not built. **I do not move
it to RED**, because unlike `CD-AC-005` its declared-route closure is dense, layered and measured, and
`F04`'s untested prevention question is a scope defect rather than a demonstrated failure of the
criterion's own construction.

### 10.3 `CD-ASR-WO2R3-04-F01` — **NOT CLOSED.** Neither Engineer claimed to close it and I do not
close it. Item 1 narrowed its usefulness at four doors (§7.4) and that is real; the finding stands.

---

## SECTION 11 — T8. THE PLANT SET, RE-APPLIED BY THIS SEAT'S OWN HAND

The plant-drift carrier `PO-DECISIONS-0017` ruling 1 ordered **still does not exist**, so this is
still done by hand at every boundary. I did it by hand. Script:
`/tmp/cd-asr-wo2r3-05/p_t8_plants.sh` — each plant applied to its **own pristine `git archive`
extraction**, clean arm and planted arm both run, `$?` captured on the line immediately after each
command (`CD-PL-F131`).

```
$ bash /tmp/cd-asr-wo2r3-05/p_t8_plants.sh
source tree: /srv/crash-detector-wo2r3-audit8
sha:         be0b355e4b9c39b65b7ca38e75e063ab2c5f40a5
python:      Python 3.11.2

PLANT                                                  apply_rc clean_rc planted_rc VERDICT
CD-RT-001-ABSENCE-RENDERS-UNKNOWN                      0        0        1          EVIDENCE (0 -> 1)
CD-RT-001-AST-NO-NUMERIC-DEFAULT                       0        0        1          EVIDENCE (0 -> 1)
CD-RT-002-AST-NO-BLEND                                 0        0        1          EVIDENCE (0 -> 1)
CD-RT-002-EXACT-TYPE-ADMISSION                         0        0        1          EVIDENCE (0 -> 1)
CD-RT-002-SCHEMA-CLOSED                                0        0        1          EVIDENCE (0 -> 1)
CD-RT-002-TYPE-NO-ARITHMETIC                           0        0        1          EVIDENCE (0 -> 1)
CD-RT-003-ENGINE-NO-WITNESS-REACH                      0        0        1          EVIDENCE (0 -> 1)
CD-RT-003-GRANT-MATRIX-LIVE                            0        3        3          **DEAD — NO CONTRAST**
CD-RT-002-CONSTRUCTORS-ESTABLISH-...-FIELD-LIST        0        0        1          EVIDENCE (0 -> 1)
CD-RT-002-SEALED-AGAINST-FORGED-ESTABLISHMENT          0        0        1          EVIDENCE (0 -> 1)
```

**Ten of fourteen re-applied and measured at the time of writing; the run was still completing when
this section was banked and the remaining four are recorded in `/tmp/cd-asr-wo2r3-05/t8.out`.**
Every plant measured so far applies cleanly (`apply_rc 0`) and produces a genuine contrast
(`0 -> 1`), **except `CD-RT-003-GRANT-MATRIX-LIVE`, which is `3 -> 3` and is therefore NOT A
CONTRAST — exactly as the dispatch declares, and for the reason `F07` gives: the instrument has
never reached its authentic target.** The dispatch's *"ZERO DEAD, 13 EVIDENCE, 1 NOT-A-CONTRAST"* is
consistent with everything I measured.

---
### 11.1 THE COMPLETED PLANT RUN — ALL FOURTEEN. **SUPERSEDES THE PARTIAL TABLE ABOVE.**

```
CD-RT-001-ABSENCE-RENDERS-UNKNOWN                       0   0   1   EVIDENCE (0 -> 1)
CD-RT-001-AST-NO-NUMERIC-DEFAULT                        0   0   1   EVIDENCE (0 -> 1)
CD-RT-002-AST-NO-BLEND                                  0   0   1   EVIDENCE (0 -> 1)
CD-RT-002-EXACT-TYPE-ADMISSION                          0   0   1   EVIDENCE (0 -> 1)
CD-RT-002-SCHEMA-CLOSED                                 0   0   1   EVIDENCE (0 -> 1)
CD-RT-002-TYPE-NO-ARITHMETIC                            0   0   1   EVIDENCE (0 -> 1)
CD-RT-003-ENGINE-NO-WITNESS-REACH                       0   0   1   EVIDENCE (0 -> 1)
CD-RT-003-GRANT-MATRIX-LIVE                             0   3   3   **DEAD — NO CONTRAST**
CD-RT-002-CONSTRUCTORS-ESTABLISH-...-FIELD-LIST         0   0   1   EVIDENCE (0 -> 1)
CD-RT-002-SEALED-AGAINST-FORGED-ESTABLISHMENT           0   0   1   EVIDENCE (0 -> 1)
CD-RT-005-PANEL-UNAVAILABLE-NEVER-AGREES                0   0   1   EVIDENCE (0 -> 1)
CD-RT-012-EGRESS-NO-BROKER                              0   0   1   EVIDENCE (0 -> 1)
CD-RT-012-LOCKFILE-DENYLIST                             0   0   1   EVIDENCE (0 -> 1)
CD-RT-012-NO-EXECUTION-INTERFACE                        0   0   1   EVIDENCE (0 -> 1)
```

**14 patches · `apply_rc` 0 on all 14 · ZERO DEAD · 13 EVIDENCE · 1 NOT-A-CONTRAST.**
**THE DISPATCH'S FIGURE IS CONFIRMED, DIGIT FOR DIGIT, BY MY OWN HAND.**

**And note the last row: `CD-RT-012-NO-EXECUTION-INTERFACE` runs `0 -> 1`.** Its clean arm exits 0
and its planted arm exits 1. **So `CD-RT-012`'s green (§7.3) is NOT vacuous — the instrument still
refuses when the violation is planted.** That is the strongest available evidence that `CD-PL-F133`'s
correction is right and the six-boundary "RED at the tip" was genuinely dead.

---

## SECTION 12 — VERDICT

    target      be0b355e4b9c39b65b7ca38e75e063ab2c5f40a5   (resolved, never transcribed)
    branch      contained in `wo-2r3`; audit worktree detached (F00)
    seat        CD-ASR-WO2R3-05
    verdict     **RED**
    confidence  HIGH on F02/F03/F06 (each demonstrated by execution, both arms).
                MEDIUM on F04/F05/F08. LOW-confidence items are marked as such.

### 12.1 THE VERDICT AND WHY IT IS NOT A VERDICT ABOUT HONESTY

**I was asked to grade a DECLARED PERIMETER, not to ask whether the class is sealed. The perimeter
is a genuine improvement and a genuinely gradeable claim, and the project's instruments have stopped
lying. I found no instrument, contract or register row on the lane that claims more than the
perimeter allows (§7.5) — the first time that has been true on this project. `CD-ENG-WO2R3-08-F07`
and `-09-F05` are honest self-disclosures that I verified and, in one case, corrected in the
project's favour (§6.2).**

**I grade the perimeter RED anyway, on three measured grounds:**

1. **`F02` (HIGH) — the PREVENTED half claims a prevention it does not deliver.** §17 says the
   forged object is *"constructible but useless"*. I built one — every layer a genuine governed
   exact type, **zero package lines** — drove it through the public judgement path, and the
   product's own declared exit released the forger's number `999.0`. **It is not useless. It is
   fully useful.** The clause answers the F2 route while the same row's RISK column names F1 first.
2. **`F03` (HIGH) — the DETECTED half, which §17 itself calls "the load-bearing half", is a plan
   and not a scheduled one.** No criterion ID; absent from §14's criterion trace and §15's WO-3 row;
   carried as a note and a residue paragraph, **two of the three forms `CD-D-172` expressly
   forbids**; and both of its named mechanisms are `WO-4` items by the same Blueprint's own tables.
   **The only defence that could catch `F02` does not exist, is not scheduled in the required form,
   and its machinery lands a work order after the date it is promised for.**
3. **`F06` (HIGH) — the verification substrate can be made green over a false declaration by a
   clerical edit.** I obtained the sweep `PASS` and the full 1726/0 suite over code that delegates
   judgement to caller-supplied objects, by reordering two operands and re-pointing two keys.
   **Increment 10 re-pointed sixteen keys.** The `PASS` at `be0b355` is not thereby shown false —
   it is shown not to be evidence.

**Taken together: the perimeter states a prevention that does not hold for the route it names first,
and assigns the remainder to a defence that does not exist. That is not a declared perimeter. It is
a declared perimeter minus its load-bearing half, and the record does not say so in those words.**

### 12.2 CONTINUATION IMPLICATION — STATED SEPARATELY, AS THE CONTRACT REQUIRES

**What is true and what is safe to do next are different calculations.**

- **The system is SAFE TO LEAVE RUNNING.** §17's blast-radius basis holds *as a scope fact*: the
  detector is ADVISORY (`D1`) and no money moves on it (`D2`). Every finding here requires an actor
  **already executing inside the process**. Nothing I found is remotely reachable, and nothing got
  worse at this increment — increment 10 made the tree strictly more honest.
- **The WO-2 gate must stay SHUT.** `CD-AC-002` AMBER/not closed, `CD-AC-005` RED,
  `CD-ASR-WO2R3-04-F01` not closed, `CD-AC-003`'s live evidence `UNSUPPORTED` (`F07`).
- **No grade should move up on the strength of this increment's green.** §7.4 shows the new guard's
  green is identical at base and tip; §6 shows the sweep's green is obtainable over a false claim.

### 12.3 WHAT I DID NOT EXAMINE, AND WHY

- I did not audit `pbg/` itself, the container/deploy layer, `db/`, `docs/` or `variants/`. Out of
  the dispatched scope.
- I did not attack the §D scoping / `CD-D-105` closure (standing invitation). **I spent the budget on
  T1, T2, T3, T4, T5, T6, T7, T8, T9, T20, T22 and T23 instead, and I say so rather than implying
  coverage I do not have.**
- **T21 (`CD-PL-F114`, the two unresolved citations in `check_dockerignore.py`) — NOT EXAMINED.**
  It lives in `tools/reconciliation/`, which does not exist on the lane at `be0b355`; I confirmed its
  absence rather than assuming it (`ls tools/reconciliation/` -> *No such file or directory*).
  Reaching it means auditing `main`, which is a different target. **`UNSUPPORTED` for this seat.**
- I did not re-derive every one of the 548 sweep sites; I derived the 33 tier-1 rows and the
  disposition tallies.
- **`CD-RT-003-GRANT-MATRIX-LIVE` could not be reached authentically** (no store). `UNSUPPORTED`,
  never a PASS against a substitute.

### 12.4 CONTROL BYPASSES AND FRAMEWORK LIMITATIONS OBSERVED

- **`PBG-EVID-001`** — `check_blueprint_carried_po_text_verbatim.py` is evidence written by the actor
  whose act it certifies. It is useful and its limits are declared, but it is **not independent
  evidence** and should not be cited as closing the `CD-D-115` question. §5 is the independent half.
- **`CD-RULE-006`** — §17's DETECTED cell asserts a carrier (`owed at WO-3 as a first-class
  criterion`) that §14/§15 do not contain. The honest form is **NOT PROVED TO BE CARRIED ANYWHERE**,
  which the Engineer wrote and the Blueprint does not.
- **`CD-RULE-003`** — the perimeter's scope boundary rests on an underived claim (`F04`).
- **No plant-drift carrier exists** (`PO-DECISIONS-0017` ruling 1), so §11 was done by hand for the
  fifth consecutive boundary.

### 12.5 NEXT SAFE GATE

**A PRODUCT AUTHORITY RULING — not another Engineer increment, and not another Assurance seat.**
Nothing here is fixed by building. Three questions are reserved and only the Product Owner can
answer them:

1. **`F02`** — does §17's PREVENTED clause get corrected to say which of the two routes it answers?
   The Project Lead cannot amend it (`CD-D-115`) and I cannot (`PBG-SOD-004`).
2. **`F03`** — does the FORGERY-DETECTION OBLIGATION get a `CD-AC-xxx` id, a row in §14, and a work
   order in §15 that actually contains its two mechanisms? If it stays at WO-3 while witness
   divergence and the provenance chain are WO-4 items, the obligation cannot be verified when it
   falls due.
3. **`F04`** — is *"the platform does not permit preventing it"* retained now that a construction-
   provenance discriminator has been measured to separate the genuine article from the F1 forgery
   in-process?

**Then, and only then, an Engineer increment scoped to whatever that ruling orders — with `F06`
(a guard for the re-pointed rows) as its own bounded item, because that one is buildable now and is
the substrate every other verdict on this project rests on.**

### 12.6 FINDINGS INDEX

| id | sev | subject |
|---|---|---|
| `CD-ASR-WO2R3-05-F00` | LOW | dispatch records `branch: wo-2r3`; audit worktree is detached HEAD |
| `CD-ASR-WO2R3-05-F01` | — | **T4 UPHELD** — the ZERO independently re-derived; PL correct, "eleven" was wrong |
| `CD-ASR-WO2R3-05-F02` | **HIGH** | §17 PREVENTED "useless" is false for the F1 route; forged `999.0` reached the presentation surface |
| `CD-ASR-WO2R3-05-F03` | **HIGH** | DETECTED half unbuilt, no criterion id, absent from §14/§15, mechanisms are WO-4 |
| `CD-ASR-WO2R3-05-F04` | MEDIUM | "platform does not permit preventing it" is two claims; the load-bearing one is underived |
| `CD-ASR-WO2R3-05-F05` | MEDIUM | BLUEPRINT header says PL authored "NOTHING ELSE" but its Build Log enumerates five, two normative |
| `CD-ASR-WO2R3-05-F06` | **HIGH** | sweep `PASS` + 1726/0 obtained over a false `EXACT` declaration by re-pointing keys |
| `CD-ASR-WO2R3-05-F07` | LOW | `CD-RT-003-GRANT-MATRIX-LIVE` never reached its authentic target; `CD-AC-003` evidence `UNSUPPORTED` |
| `CD-ASR-WO2R3-05-F08` | MEDIUM | inherited-claim mechanism is systemic; `CD-PL-F133` states four boundaries, I measured six |
| `CD-ASR-WO2R3-05-F09` | LOW | `CD-F-0002`/`CD-F-0003` declared reach is stale — "every value admitted" is false at the tip |

### 12.7 UPHELD IN THE PROJECT'S FAVOUR — recorded because a verdict that only accuses is not an audit

- **T4's ZERO** — independently re-derived, exact match (§1).
- **The sealing instrument's exit text** — the most honest artefact I have read on this project. It
  fails closed with *"WHAT IT CLAIMS ON THIS RUN: NOTHING"* when given no `--root` (§0/sealed.out).
- **`CD-ENG-WO2R3-08-F07`** — self-disclosure verified: base and tip both `PASS — 36 assertions` (§7.4).
- **`CD-ENG-WO2R3-09-F05`** — I corrected it *in the project's favour*: something does notice a bare
  reorder (§6.2).
- **`CD-PL-F133`** — upheld; `CD-RT-012` graded **GREEN**, and its plant proves the green non-vacuous (§11.1).
- **`CD-D-173`** — upheld and correctly classified (§7.7).
- **T6** — the fourth seat's exit-3 correction re-measured and confirmed (§7.6).
- **The plant set** — 14/14, 13 EVIDENCE, 1 NOT-A-CONTRAST, digit-for-digit as declared (§11.1).
- **Q4** — no instrument, contract or register row on the lane overclaims (§7.5).
- **The T20 Build Log enumeration** — accurate and complete; I could not find a sixth item (§5.2).

---

*Persisted at `/tmp/cd-asr-wo2r3-05/VERDICT-EIGHTH-SEAT.md` (`PBG-CONT-007`).
`CD-ASR-WO2R3-05`, 2026-08-23.*
