# VERDICT — CD-DISPATCH-META-ASSURANCE-01

**Seat:** `CD-META-01` — Assurance Engineer, read-only, first use on this project.
**Subject:** `PROJECT_LEAD_SEAT_01`'s **reconciliation practice**. Not the product, not the
perimeter, not the WO-2 gate.
**Authority:** PO-DECISIONS-0013 ruling 5 · PO-DECISIONS-0019 ruling 5 · CD-AUTH-0001.
**Written:** 2026-08-23T13:05Z. **Evidence retained at** `/tmp/meta-assurance-01/`.

---

## 0. THE GRADE

# RED

**On the practice.** Confidence: HIGH on everything in §1 and §2, which I measured myself and can
reproduce from pinned artefacts. Scope: §3–§9.

I am not grading the product. I am grading whether this seat's instruments for deciding what is
true actually hold. **They do not hold, and the pass convened to establish that measured the class
recurring, live, inside its own audit window.**

---

## 1. THE SHA, AND IT IS THE FINDING THAT OUTRANKS EVERYTHING ELSE

The dispatch instructed: *"`git rev-parse HEAD` when you start and again when you finish. **IF THEY
DIFFER, THAT IS A FINDING AND IT OUTRANKS EVERYTHING ELSE IN THIS DISPATCH.**"*

```
$ pwd; git -C /srv/crash-detector rev-parse HEAD          # 2026-08-23T12:53Z, my first action
/srv/crash-detector
5e0a873477e62dd254cbab7f03360d480d289c35

$ pwd; git -C /srv/crash-detector rev-parse HEAD          # 2026-08-23T13:05:28Z, my last action
/srv/crash-detector
a31c79978dfdc9ed8200bd702ee0750facac94c3
```

**THEY DIFFER.**

```
$ pwd; git -C /srv/crash-detector log --format='%h %aI %an  %s' 5e0a873..HEAD
/srv/crash-detector
a31c799 2026-08-23T14:02:38+01:00 PROJECT_LEAD_SEAT_01  [CRASH-DETECTOR] PO-DECISIONS-0020
  RULINGS 1+2 CARRIED — PID §6 GAINS CD-AC-017 (v1.1.0 ...)

$ pwd; git -C /srv/crash-detector diff --stat 5e0a873..HEAD
 BLUEPRINT.md                                   |  53 +++-
 PID.md                                         |  22 +-
 governance/engineering/ACTIVE_WORK.yaml        |   6 +-
 .../build-log/BL-20260823T125935Z-0136.yaml    | 278 +++++++++++++++++
 .../check_pid_carried_po_0020_verbatim.py      | 308 +++++++++++++++++
 5 files changed, 658 insertions(+), 9 deletions(-)
```

`a31c799` was authored at **14:02:38 +0100 = 13:02:38Z**. My `git status` snapshot of the worktree
is timestamped **13:02:28Z** — **ten seconds earlier**. The commit landed with the auditor's hands
on the tree.

### 1.1 `CD-PL-F134` IS NOT OPEN. IT IS RECURRING, AND IT IS WORSE THAN THE INSTANCE THAT NAMED IT

The dispatch's own words, committed at `5e0a873` nine minutes before `a31c799`:

> **NOTHING MOVES ON `main` WHILE YOU READ. THIS IS NOT A COURTESY, IT IS `CD-PL-F134`'S OWN NAMED
> REMEDY, AND `CD-PL-F134` IS ON YOUR DOCKET.** … **THAT BOOKKEEPING IS CLOSED … AND YOU ARE
> LAUNCHED AFTER IT.**

`CD-PL-F134`'s original instance was *"two commits, both continuity bookkeeping"* — `ACTIVE_WORK.yaml`
and a follow-up field. **`a31c799` changed `BLUEPRINT.md` and `PID.md`, which are two of my direct
audit targets, by 53 and 22 lines, and added a governed instrument and a build-log entry.** The
recurrence is materially larger than the finding.

**And the remedy the dispatch supplied me was blind to it.** I was told to verify by comparing
`git rev-parse HEAD` at start and finish. That check only fires *after* the damage, and it cannot
see a worktree mutating mid-read at all — I first detected this not through the SHA but because
`governance/engineering/ACTIVE_WORK.yaml` read `blueprint_version: 0.4.0-ACCEPTED` at 585,657 bytes
early in my session and `0.4.1-ACCEPTED` at 588,670 bytes later. **The seat's remedy for
`CD-PL-F134` guards the instance it observed (a commit on `main`) and not the class (the audited
target changing under a read-only seat).** That is `GUARD_THE_INSTANCE_NOT_THE_CLASS`, applied by
the subject to its own finding, and `CD-RULE-004` — this project's own rule — forbids exactly it.

**FINDING `META-01-F01`, HIGH.** `CD-PL-F134` is **RECURRING**. Its declared remedy is a resolution
held in one seat's attention with no freeze mechanism, and it failed on its first application,
inside the audit window it was written for, against an explicit written guarantee, in nine minutes.

### 1.2 AND THE COMMIT THAT MOVED IT IS CONTINUITY-BROKEN

```
$ cd /tmp/meta-assurance-01/a31 && pwd; git rev-parse HEAD
/tmp/meta-assurance-01/a31
a31c79978dfdc9ed8200bd702ee0750facac94c3
newest build-log entry in THIS committed tree: BL-20260823T125935Z-0136.yaml
pointer:                       last_build_log_entry: BL-20260823T124508Z-0135

$ PYTHONPATH=pbg/tools python3 -B -m pbg.cli boot          # pristine --no-hardlinks clone, CD-RULE-008
Verdict          : RED
continuity_state : CONTINUITY_REFERENCE_INVALID/RESUME_BLOCKED
```

**The tip of `main` at the moment I finished is `RESUME_BLOCKED` for every actor who clones it.**

This is `CD-PL-F111` → `CD-PL-F112` → `CD-PL-F132` **for the fourth time**, and the arithmetic
matters more than the fact:

| | remedy | boundaries it survived |
|---|---|---|
| `CD-PL-F111` | *"a resolution not to forget"* | **1** (failed at the next boundary → F112) |
| `CD-PL-F112` | *"the pointer moves in the same commit as the entry it names"*, called **STRUCTURAL** | **8** (failed at the ninth → F132) |
| `CD-PL-F132` | the same convention, re-applied | **4** (failed at the fifth → **`a31c799`, measured here**) |

`ACTIVE_WORK.yaml` at `5e0a873` says, in the seat's own bold: *"FOURTH CONSECUTIVE BOUNDARY SINCE
`CD-PL-F132` … IT HELD EIGHT TIMES BEFORE IT FAILED, AND FOUR IS FEWER THAN EIGHT."* **The fifth
boundary is `a31c799` and it failed.** The seat predicted its own failure in writing and the
prediction changed nothing, because a prediction is not a carrier.

**The half-life is not stable — it is shortening: 8 → 4.** Eleven self-raised findings on this one
class have produced **zero** executable carriers.

**FINDING `META-01-F02`, HIGH.** The `last_build_log_entry` class is **RECURRING**, its "structural
fix" is measurably not structural, and its survival interval is decaying.

**Full population, measured, not argued** — every commit on `main`, pointer vs newest entry in that
same committed tree (`/tmp/meta-assurance-01/probe_pointer.sh`, `pointer_results_final.txt`):

```
193 commits examined; 90 boundary commits (commits that add a new newest entry)
STALE pointer at the committed tree:
  44a56ec  newest 0035  pointer 0036   (pointer AHEAD — CD-PL-F69)
  61e9558  newest 0122  pointer 0121   (CD-PL-F112)
  00ef57e  newest 0131  pointer 0130   (CD-PL-F132)
  a31c799  newest 0136  pointer 0135   (NEW — measured by this seat, 2026-08-23T13:04Z)
stale_at_boundary = 3 of 90
```

`CD-PL-F111` does **not** appear: it was caught pre-commit and never landed. The record is accurate
about that, and I say so.

---

## 2. THE CENTRAL HYPOTHESIS, ANSWERED

> *Does confessing at volume function as a control, or as a substitute for one?*

**IT FUNCTIONS AS A SUBSTITUTE, AND THE RECORD CONTAINS THE PROOF OF WHICH CASES ARE WHICH.**

But the honest answer is sharper than "confession does not work", and the sharper version is the
only part of this verdict that is actionable. **I measured a clean dividing line:**

> **A finding on this project acquires a real carrier if, and only if, its remedy was routed into a
> dispatch with a writable code scope. A finding whose remedy stayed inside the Project Lead's own
> reconciliation practice acquired prose, and only prose — every time, without exception.**

**The good side of the line, and it is genuinely good.** `CD-PL-F100` (the tree-fingerprint recipe)
was routed to an Engineer increment. It produced `tools/audit/tree_fingerprint.py` on the lane —
an executable that **prints every path `.gitignore` excluded**, declares in its own header
*"`.gitignore` CORRECTNESS … the exclusions are PRINTED, not verified"*, and carries
`tests/test_tree_fingerprint.py` with 8 tests. That is a closed class with a declared residue and a
regression lock. **That is this practice working, and it is not nothing.**

**The bad side of the line.** `F111`/`F112`/`F132`/`F134` are all continuity-bookkeeping defects in
the Project Lead's own hands. Their remedies were: a resolution, a convention, a re-applied
convention, and a sentence in a dispatch. **The enforcement surface available to them is empty:**

```
$ pwd; find tools -name '*.py' | wc -l ; ls .git/hooks | grep -v sample | wc -l ; ls -d .github
/srv/crash-detector
4          # instruments, all four hand-invoked
0          # git hooks
ls: cannot access '.github': No such file or directory     # no CI
```

**102 distinct `CD-PL-F` findings in `governance/`. Zero hooks. Zero CI. Four hand-run scripts.**
Nothing on this project can fail a commit. Every control is a thing a seat must remember to run,
which is the precise property `CD-PL-F132` correctly identified as fatal — and the replacement
control `CD-PL-F132` names (*"taking the CD-RULE-008 verdict first in a pristine clone"*) **is
itself a thing a seat must remember to run.** The seat diagnosed the disease and prescribed the
disease.

### 2.1 The findings are not even a set that can be enumerated

```
$ pwd  # /tmp/meta-assurance-01
distinct CD-PL-F ids referenced anywhere in governance/: 102
ids with a formal 'id:' definition block:                 67
ids referenced but NEVER formally defined:                35
```

Among the 35 with **no finding record anywhere**: `CD-PL-F99`, `CD-PL-F100`, `CD-PL-F112`,
`CD-PL-F113`, `CD-PL-F122`, **`CD-PL-F132`**. **Six of the nine findings the Product Owner named as
my docket cannot be resolved from the record by their own ID.** `CD-PL-F132` — which the dispatch
calls *"the single most load-bearing item on this docket"* — exists only as bold prose inside a YAML
**comment** attached to the `last_build_log_entry` field of `ACTIVE_WORK.yaml`, a file the schema
describes as *"overwritten in place by design"*.

Of the 67 that are defined, the schema is not a schema: the body key is variously `title:`,
`summary:`, `statement:` or `what:`, and only 37 carry an `against:` field.

**FINDING `META-01-F03`, HIGH.** There is **no findings register on this project.** A finding is not
an object with an id, a severity, an owner, a carrier and a status; it is a paragraph. Consequently
nothing can compute "open findings", nothing can detect a recurrence, and **nothing did** — I
detected the fourth recurrence of `F111` with a nine-line shell loop that nobody had written in five
days and 90 boundaries. **This is the single cheapest structural repair available and it is the one
that makes the other repairs checkable.**

### 2.2 The volume of confession is itself now a continuity hazard

```
$ pwd; wc -c governance/engineering/ACTIVE_WORK.yaml
/srv/crash-detector
585657 governance/engineering/ACTIVE_WORK.yaml        # 5,313 lines; 74 "PREVIOUSLY" chains
```

`ACTIVE_WORK.yaml` grew **3,669 → 588,670 bytes in five days — 160×** — because superseded notes are
*"retained IN FULL below because it carries the finding"*. The file that exists so a cold agent can
resume is now 574 KB, most of it a findings archive with no index. `governance/` totals **3.9 MB
≈ 980,000 tokens**, and one `pbg boot` prints **370 KB ≈ 90,000 tokens** of verdict, one field of
which is a multi-thousand-word paragraph.

`CLAUDE.md` requires: *"This project must survive losing you and your context window."* **Measured,
it cannot.** A cold agent cannot read its own resumable state. The confession volume did not just
fail to carry the findings — **it consumed the continuity budget the findings were supposed to
protect.**

**FINDING `META-01-F04`, MEDIUM.** `CONTINUITY_RECOVERY` / `CONTROL_BURDEN`. The retention rule
("retain the note in full, it carries the finding") is a workaround for the missing register in
§2.1, and it has made the continuity record unreadable at exactly the scale where continuity
matters.

---

## 3. THE NINE DOCKETED FINDINGS — CLOSED / OPEN / RECURRING, MEASURED

| Finding | Class | Verdict | The measurement |
|---|---|---|---|
| `CD-PL-F98` | every probe prints the tree it read | **OPEN, honoured by habit** | All four instruments carry `print(f"  tree: {root}")` with the comment `# CD-PL-F98`. It is honoured, it is not enforced — a fifth instrument omitting it fails nothing. I complied with it throughout this pass; **that it is followable is not evidence that it is carried.** |
| `CD-PL-F100` | fingerprint recipe / gitignored sweep | **CLOSED — with a real carrier** | `wo-2r3:tools/audit/tree_fingerprint.py` prints every excluded path, declares its `.gitignore` dependence as a limit, and has 8 tests. **The only docketed item with an executable carrier.** Routed to an Engineer increment — see §2. |
| `CD-PL-F102` | clause (i) undercounts the governed instruments | **RECURRING — in the dispatch that sent me** | Clause (i) of MY dispatch: *"The two instruments here are …"*. Measured at `5e0a873`: `git ls-tree HEAD tools/reconciliation/` returns **three** tracked instruments; `check_lane_governance_citations.py` (EXIT 0, ordered by PO-DECISIONS-0016 r1(b)) is unnamed. A **fourth**, `check_pid_carried_po_0020_verbatim.py`, sat **untracked** in the audited worktree during my read and was committed at `a31c799`. F102's exact class — a completeness claim in the clause whose whole purpose is completeness. |
| `CD-PL-F111` | `last_build_log_entry` stale | **RECURRING** | §1.2. Never landed itself; its class landed four times, most recently `a31c799`, measured by me. |
| `CD-PL-F112` | same fault, next boundary; "structural" fix | **RECURRING** | §1.2. Survived 8, then 4. |
| `CD-PL-F132` | the fix failed at its ninth application | **RECURRING, and the decay is accelerating** | §1.2. 8 → 4. `a31c799` boots **RED / RESUME_BLOCKED**. |
| `CD-PL-F134` | `main` moved under a live auditor | **RECURRING, worse than the original** | §1.1. Nine minutes after the guarantee; product documents this time, not bookkeeping. |
| `CD-PL-F135` | dispatch target named no tree | **RECURRING — twice more in my own dispatch** | (a) `target.sha: 6a15ac5` was stale by one commit at issue and by **two** at my first read (`abafec2`, then `5e0a873`). The Project Lead disclosed this before I found it; **disclosure does not neutralise it, and the dispatch names its own target wrongly on its face.** (b) Clause (i) states measurements *"measured at `6a15ac5`"* for a tree I was to audit at a different SHA. |
| `CD-PL-F136` | one counterfactual arm, banked as a claim about the class | **RECURRING at the meta level** | The seat's own `--counterfactual` for the 0019 carriage check alters one word per sentence — a genuine class (word substitution), correctly claimed. But see §4: I ran two arms it does not run, and one of them **passes while the Blueprint says the opposite of the ruling.** The declared limits cover one direction and not the other. |

**Score: 1 CLOSED, 1 OPEN-by-habit, 7 RECURRING.** Six of the seven recurrences are in the seat's own
reconciliation hands; the one CLOSED is the one that went to an Engineer.

### 3.1 The accumulated docket the Product Owner did not name

- **`CD-PL-F99`** (ISSUED/CARRIED gap) — **NOT REACHED as a distinct measurement.** It has no
  finding record (§2.1); I could not locate a definition to test against and I decline to grade it
  from a summary written by the subject. **UNSUPPORTED.**
- **`CD-PL-F113`, `CD-PL-F122`** — **NOT REACHED.** No finding record. Same reason. **UNSUPPORTED.**
- **`CD-PL-F119`, `CD-PL-F120`, `CD-PL-F121`, `CD-PL-F123`, `CD-PL-F124`** — read in full; all are
  measurement-method defects (a false-green factory named as a remedy; an unsound `__slots__`
  criterion; four parse artefacts in three boundaries; a fabricated `baseline_sha` with a note
  falsely asserting it had been resolved; a landed entry naming a commit that does not exist).
  **`CD-PL-F121` is the correct diagnosis of its own class** and it instructs later seats to
  distrust this seat's derived tables. **I followed that instruction: every table in this verdict is
  my own measurement, and I transcribed no number from the record.** The class is **OPEN** — the
  remedy is again attention, and `CD-PL-F123` is `CD-PL-F118` recurring at the next boundary in the
  same field, which is the same shape as F111→F112.
- **`CD-PL-F137`, `CD-PL-F138`, `CD-PL-F139`** (raised at the boundary that dispatched me) — read.
  `F137` (the lane still quotes the superseded two-tier perimeter at `be0b355`) is **correct, open,
  and material to the ninth seat**; see §8. `F138` is answered by §4.2 — **it undercounts.**

---

## 4. THE STANDING INVITATIONS, TAKEN

### 4.1 The carriage check — both arms, and two arms it does not run

```
$ pwd; python3 -B tools/reconciliation/check_blueprint_carried_po_0019_verbatim.py --root .
/srv/crash-detector
  tree: /srv/crash-detector
  10/10 sentences resolve in BOTH files; 1911 normalised characters carried.       EXIT 0

$ ... --counterfactual        0/10 resolve                                          EXIT 1
```

Both arms reproduce. The instrument is well built: it prints its tree, prints its population,
declares three limits, and its counterfactual genuinely fails. **I would not have written it
differently.** Then I ran the arms it does not run, on a pinned clone of `5e0a873` so `/srv` was
never touched:

**ARM 3 — every carried sentence left byte-identical, force inverted by added framing.** I inserted
before the tier sentence: *"THE FOLLOWING SENTENCE IS RECORDED FOR HISTORY AND IS NO LONGER IN
FORCE; THE PERIMETER IS TWO TIERS."*

```
$ cd /tmp/meta-assurance-01/arm && pwd; python3 -B tools/.../check_..._0019_verbatim.py --root .
PO-0019-BLUEPRINT-CARRIED-PO-TEXT-VERBATIM: PASS — every quoted sentence is the Product Owner's own
EXIT=0
```

**The check reports the Product Owner's perimeter carried, while the Blueprint asserts the two-tier
perimeter the ruling exists to correct.** This is inside declared limit 2 and I grade it as
**declared, not concealed** — but the limit's named residue is *"an auditor wanting that half runs
`git diff 7794c15..HEAD` and reads it"*. Under **`CD-RULE-006`**, that residue names a layer that
has not been measured to hold it: the layer is *a human reading a diff*. The honest form the rule
prescribes is **NOT PROVED TO BE CARRIED ANYWHERE**.

**ARM 4 — deletion of ruling content the tuple does not name.** I removed 605 characters of §17
after the carried tier-3 sentence: **PASS, EXIT 0.**

**The population is chosen by the subject.** 1,911 normalised characters are under instrument out of
**2,872** characters in PO-DECISIONS-0019 rulings 1–3 — **66.5 %**. The remaining third is protected
by nothing, and **the check declares the *addition* direction and not the *omission* direction.** A
ruling sentence never carried at all is invisible to it.

**FINDING `META-01-F05`, MEDIUM.** The carriage instrument's declared limits are honest about what a
carriage may have *added* and silent about what it may have *dropped*, while its population is
selected by the seat whose fidelity it certifies (`SELF_REFERENCE_AND_SELF_VOUCHING`). Remedy: derive
`CARRIED` from the ruling file rather than a hand-written tuple, or declare the omission direction
and the 66.5 % under `CD-RULE-004` option 2.

### 4.2 §19's enumeration of authored bytes — **IT IS FALSE, AND `F05` IS STILL RUNNING**

§19's v0.4.0 row: *"**THE PROJECT LEAD'S OWN AUTHORED BYTES ARE EXACTLY:** the version bump and
status block, the two criterion IDs and their §14/§15 table scaffolding, the §14 disclosure
blockquote … and this row."*

I diffed it. The §17 `CD-BP-005` risk column's **headline sentence was rewritten by this seat**:

```
- DELIBERATE IN-PROCESS FORGERY IS NOT PREVENTED AND THE PLATFORM DOES NOT PERMIT PREVENTING IT.
+ DELIBERATE IN-PROCESS CONSTRUCTION OF A FORGED OBJECT CANNOT BE PREVENTED.

$ cd /tmp/meta-assurance-01/pristine && pwd; git rev-parse HEAD    # 5e0a873, pinned
grep -c 'DELIBERATE IN-PROCESS CONSTRUCTION OF A FORGED OBJECT CANNOT BE PREVENTED'
  BLUEPRINT.md                        : 1
  governance/decisions/PO-DECISIONS-0019.md : 0
```

The Product Owner wrote *"Construction cannot be prevented — measured three times, that stands."*
**The replacement headline is a Project Lead paraphrase, in the risk column of `CD-BP-005`, in a
file `CD-D-115` protects from this seat, and it is not in the enumeration.** Faithful in substance;
that is not the test. The test is whether the enumeration that says **EXACTLY** is true.

Second omission, same method:

```
$ grep -c 'the perimeter CORRECTED to three tiers'
  BLUEPRINT.md : 1     governance/decisions/PO-DECISIONS-0019.md : 0
```

— a two-line addition to the `derives_from:` field, which is neither the version bump nor the status
block.

**FINDING `META-01-F06`, MEDIUM.** `CD-ASR-WO2R3-05-F05` is **RECURRING**, and it is recurring inside
the sentence written to repair it. The seat raised `CD-PL-F138` against the one item it noticed (the
§14 blockquote) and the enumeration beside it still omits at least two more, **one of them the
perimeter's top-line sentence.** This is `GUARD_THE_INSTANCE_NOT_THE_CLASS` performed on the seat's
own honesty: **self-finding catches the instance the seat thought of, and an enumeration is exactly
the artefact that must not be written by the party it enumerates.**

### 4.3 This dispatch

Beyond §3's `F135` and `F102` entries: the dispatch poses *"the question none of this project's
rules has been asked"* as *"still unanswered"*. **It was answered, by measurement, eleven days'
work ago, in a verdict this seat banked verbatim.** See §5. That is not a rhetorical device; it is
the failure mode of §6 arriving in the dispatch that commissions the audit of §6.

---

## 5. THE BACKWARD-SWEEP QUESTION — MEASURED, AND IT WAS ALREADY ANSWERED

> *When a rule is adopted on this project, is the record swept backward for the instances that
> motivated it?*

**NO.** Measured against **`CD-RULE-009`** (fingerprints must record their producing command;
PRODUCT AUTHORITY, effective 2026-08-20, motivated by `CD-PL-F78` — an auditor who could not
reproduce a fingerprint in ten attempts):

```
$ pwd  # /srv/crash-detector
PRE-RULE files carrying sha256 fingerprints — commits touching them AFTER 2026-08-20:
  governance/assurance/WO-2/BL-ASR-WO2-01.yaml                   0
  governance/assurance/WO-2R/VERDICT.md                          0
  governance/engineering/build-log/BL-20260819T200314Z-0039.yaml 0
  governance/continuity/WO-2-LANE-SHA-MAP.md                     0
  governance/engineering/build-log/BL-20260819T090500Z-0021.yaml 0
```

**Zero.** No sweep, no supersession record, no enumeration of which pre-rule fingerprints are
unreproducible. `governance/assurance/WO-2R/VERDICT.md:1020` still carries a bare
`50ae34d6…` that its own author says he could not reproduce *"by any sort I tried"* — the exact
motivating class, sitting unswept in the record. `PBG-CONT-003` forbids **editing** landed entries;
it does not forbid a supersession that enumerates them, and none exists.

Note the asymmetry: **`CD-RULE-005` explicitly states its own scope** — *"Neither entry is edited …
this rule binds forward"* — and names its one instance. **`CD-RULE-009` does not**, so a reader
reasonably infers the record was checked. It was not. (I also swept `CD-RULE-005`'s class myself
across all 89 entries on `main`, entry-id timestamp against the true UTC author date of the commit
that added it: no further BST-as-UTC instance on `main`; three entries — 0021, 0022, 0025, all
pre-rule — carry ids stamped 2–7 minutes *ahead* of their own commit, which is a smaller relative of
the same defect and is enumerated here for the first time.)

**AND THE ANSWER WAS ALREADY ON THE RECORD.** `governance/assurance/WO-2R3/VERDICT-EIGHTH-SEAT.md`,
line 958:

> *"**And T23's open question — "when a rule is adopted, is the record swept backward for the
> instances that motivated it?" — I can now answer from measurement: NO.** The sweep-backward has
> never been performed on this project, for any rule."*

Which brings me to the finding I consider, with §1, the most damaging in this verdict.

---

## 6. THE EIGHTH SEAT'S RED WAS BANKED AND FOUR OF ITS TEN FINDINGS WERE NEVER DISPOSITIONED

The eighth Assurance seat returned **RED** with ten findings, `CD-ASR-WO2R3-05-F00` … `-F09`. The
Project Lead banked the file verbatim, uncommitted-unread, `cmp` rc=0 — **and that part of the
practice is genuinely excellent and I want it on the record as such.**

Then:

```
$ pwd  # /srv/crash-detector
for id in CD-ASR-WO2R3-05-F00 … -F09: files containing it OUTSIDE the verdict file
  → 0   for every one of the ten
```

Not one of the eighth seat's findings is dispositioned anywhere by its own identifier. They are
referenced in short form only:

```
BL-...-0134 (the reconciliation of that verdict):  F01 F02 F03 F05 F06 F07
BL-...-0135:                                        F01 F02 F03 F05 F06
PO-DECISIONS-0019:  F01 F06        PO-DECISIONS-0020:  F03 F05
```

**`F00`, `F04`, `F08` and `F09` appear nowhere, in any form, in any build-log entry, decision or
reconciliation record.** `BL-…-0134` contains no finding-by-finding disposition table; it selects.
Two of the four dropped are MEDIUM. `F04` — *"the load-bearing claim is underived"* — was in fact
substantively resolved by PO-DECISIONS-0019 ruling 2, but nothing links the ruling to the finding,
so no reader can establish that. **`F08` is the backward-sweep answer**, and its loss is why my own
dispatch re-poses a measured question as an open one.

**FINDING `META-01-F07`, HIGH.** The reconciliation of an assurance verdict has **no completeness
obligation**. Findings are answered by narrative selection, not by roll-call. The dispatch warns me
that *"a pass that quietly covers less than its docket is the defect this project has found six
times"* — **the Project Lead committed exactly that defect against the eighth seat's RED, forty
minutes before writing the warning.** Independent findings decay faster than self-raised ones,
because the self-raised ones at least get restated in the next `ACTIVE_WORK` comment.

---

## 7. WHAT I VERIFIED IN THE DISPATCH'S OWN CLAIMS

Clause (i) told me what I would find. `CD-PL-F121` told me to measure it instead. Both arms, my
own trees:

| Claim | Measured |
|---|---|
| `check_blueprint_carried_po_text_verbatim.py` EXIT 0 | **CONFIRMED** |
| `check_..._0019_verbatim.py` EXIT 0; `--counterfactual` EXIT 1 | **CONFIRMED**, both arms |
| pristine `--no-hardlinks` clone boots **GREEN** | **CONFIRMED at `5e0a873`** — `CONTINUITY_MATCH/RESUME_GREEN` |
| worktree boots **AMBER** | **CONFIRMED** — `RESUME_AMBER`, sole `UNAVAILABLE` `roadmap_identity`. Measured on a byte-identical `cp -a` copy, declared here as a **substitute target** because booting `/srv` risks mutation and I am read-only (`PBG-ASSURE-001` — I name it rather than claiming the authentic target). |
| *"~51 untracked operator-wrapper artefacts"* | 54 at my start, 59 at my finish. Approximation fair. |
| *"`main` carries no application code and no test suite"* | **CONFIRMED** |
| *"the two instruments here are …"* | **FALSE — three tracked, four present.** §3, `CD-PL-F102`. |
| *"`6a15ac5` is the target"* | **FALSE by two commits at my first read.** |
| *"nothing moves on `main` while you read"* | **FALSE.** §1. |

---

## 8. THE STRUCTURAL CARRIERS THAT ARE OWED, AND WHERE EACH MUST LIVE

Ordered by ratio of harm prevented to cost. **The first three are writable by seats on this project
today. The fourth is not, and that is the answer nobody has been able to give.**

1. **A FINDINGS REGISTER — `governance/findings/REGISTER.yaml`, plus a validator in
   `tools/reconciliation/`.** One row per finding: `id · severity · against · raised_at ·
   carrier (path, or NOT PROVED TO BE CARRIED ANYWHERE per CD-RULE-006) · status · recurrence_of`.
   The validator fails when a build-log entry cites an id with no row, when a `RECURRING` row has no
   carrier, and when a banked assurance verdict contains a finding id with no row. **Cost: one
   Engineer increment. It fixes §2.1, §6 and §4.2 at once**, and it is the only proposal here that
   makes "does this practice work?" a computable question instead of a narrative one.
   *Writable by an Engineer seat. Nothing blocks it.*

2. **A PRE-COMMIT HOOK IN THE REPOSITORY, COMMISSIONED AS A TRACKED FILE.** `BLUEPRINT.md` §15
   already lists *"pre-commit hook commissioned"* under WO-1 and `.git/hooks/` is empty; `git ls-files`
   shows no tracked hook and no CI. Three checks, each of which would have fired on a defect measured
   in this verdict: (a) if any file under `build-log/` is staged, `last_build_log_entry` must equal
   the newest staged entry — **this alone stops `F111`/`F112`/`F132`/`a31c799`, four findings and
   five days of prose, in about fifteen lines**; (b) every fingerprint added in the diff has a
   producing command within N lines (`CD-RULE-009`); (c) every `CD-PL-F` id cited has a register row.
   *Writable by an Engineer seat today.*

3. **AN AUDIT FREEZE THAT IS A MECHANISM AND NOT A SENTENCE.** `CD-PL-F134`'s remedy must stop being
   a promise. The cheapest honest form: the dispatch names a **tag**, the Project Lead's boundary
   procedure refuses to commit while a `governance/dispatch/ACTIVE-AUDIT.lock` exists, and the
   auditor works from `git clone --no-hardlinks` at that tag rather than from `/srv` at all. **A
   read-only seat should never be pointed at a live worktree** — I was, and the target changed under
   me twice before I noticed. *Writable by a seat; the lock file is `governance/`.*

4. **THE ONE THAT LIES OUTSIDE EVERY SEAT'S SCOPE — and I am naming it because the dispatch asked
   me to name it even if the answer is `pbg/`.**
   `pbg boot` **detects** `ACTIVE_WORK_STALE` and does so reliably: it is the mechanism that caught
   this class three times, and it caught `a31c799` for me. **But a detector that must be remembered
   is not a control**, and this project has now measured that proposition four times. What is owed
   is a framework-level **write path**: `pbg` must own the "close a boundary" transaction — write
   the entry, move the pointer, validate, read back, refuse the whole update on any failure —
   exactly as `continuity.checkpoint` already does for the fields it owns. `CD-RULE-007`'s own text
   says this: *"the framework's own writer validates, writes a `.tmp`, reads it **back**, validates
   again, and refuses the whole update if any stage fails … **Every hand edit forfeits that
   guarantee.**"* The project's answer was a rule telling seats to re-run the validator by hand.
   **That is the forfeit, restated as a procedure.**
   **This lives in `pbg/`, which is pinned read-only to every seat here (`PBG-FWK-013`), so no seat
   on this project can write it, and no amount of Project Lead diligence can substitute for it.** It
   belongs in a bounded framework dispatch against PBG itself, audited by a seat that did not
   implement it. **Until it exists, item 2 is the local stand-in and should be built anyway.**

**And one thing that must NOT be a carrier:** another rule in `PROJECT-RULES.md`. There are nine.
That file's own first sentence — *"a procedural control that is not written down is not a control"* —
is true and has been over-read into its converse. **Writing it down is not enough either.** `CD-RULE-007`
and `CD-RULE-008` are written down, correct, and were both breached by `a31c799`.

---

## 9. WHAT I DID NOT REACH — NAMED PLAINLY

- **`CD-PL-F99` (the ISSUED/CARRIED gap), `CD-PL-F113`, `CD-PL-F122`** — **UNSUPPORTED.** No finding
  record exists for any of them (§2.1). I will not grade a finding from the subject's summary of it,
  and `CD-PL-F121` instructs later seats not to. Their absence is itself evidence for
  `META-01-F03`.
- **The lane at `be0b355`, the product, the perimeter's soundness, `CD-AC-002`/`CD-AC-005`, the
  forgery findings** — deliberately out of scope; the ninth seat grades them.
- **The worktree boot arm** was taken on a byte-identical copy, not on `/srv` (§7). Declared, not
  hidden.
- **I did not attempt to establish whether `a31c799` was already in flight when the dispatch was
  written.** The mtimes show `PID.md` modified at 12:56:03Z, three minutes after the dispatch commit
  — consistent with work beginning after the auditor launched. I state the timing and draw no
  inference about intent. **Intent does not change the measurement, and the finding is about a
  missing mechanism, not a missing virtue.**
- **`governance/` is 3.9 MB.** I read the four instruments in full, `PROJECT-RULES.md` in full, the
  eighth seat's verdict in the sections that bear on practice, `BL-…-0134` and `BL-…-0135` in full,
  and targeted regions of the rest. **I did not read all 89 build-log entries in full**, and where
  I needed a fact about all 89 I computed it rather than reading it.

---

## 10. WHAT WOULD HAVE TO CHANGE, IN ONE PARAGRAPH

**The Product Owner called this audit a reward for the habit of finding against oneself. It is not,
and the habit is not the thing that needs protecting.** Self-finding at this volume is doing real
work — it produced `CD-PL-F132`'s decay-curve diagnosis, which is the most accurate sentence anyone
has written about this project, and `CD-PL-F100`'s carrier, which is the best artefact in the tree.
But **the practice has no step between "finding" and "next boundary" in which a carrier is
demanded, and so the modal outcome of a finding is a paragraph.** The evidence is not rhetorical: on
the one class where the remedy was routed to a seat with a writable code scope, the class closed and
stayed closed; on the four classes that stayed in the Project Lead's own hands, the record now holds
eleven findings, three superseding remedies, one explicit written prediction of the next failure —
and the failure happened anyway, during the audit, ten seconds after I photographed the tree.
**Change one thing and the rest follows: make a finding an object with a mandatory carrier field
that a validator can fail on, and stop accepting a sentence as that carrier.** Everything else in §8
is a consequence.

---

## 11. RETURN

```
target        /srv/crash-detector, branch main
              START  5e0a873477e62dd254cbab7f03360d480d289c35
              FINISH a31c79978dfdc9ed8200bd702ee0750facac94c3     ** THEY DIFFER **
verdict       RED — on the PRACTICE
confidence    HIGH (§1, §2, §4.2, §5, §6 — all reproduced from pinned artefacts)
scope         the Project Lead's reconciliation practice. NOT the product, the perimeter,
              the WO-2 gate, or the lane at be0b355.
```

**Findings raised by this seat**

| id | sev | statement |
|---|---|---|
| `META-01-F01` | **HIGH** | `CD-PL-F134` RECURRING — `main` moved during this read-only audit, against an explicit written guarantee, touching two audit targets. Its remedy guards the instance, not the class. |
| `META-01-F02` | **HIGH** | `CD-PL-F111`/`F112`/`F132` RECURRING for the fourth time at `a31c799`, which boots **RED / RESUME_BLOCKED** in a pristine clone. "Structural fix" survival: 8 boundaries, then 4. |
| `META-01-F03` | **HIGH** | No findings register. 102 ids, 67 defined, 35 undefined including six of the nine on this docket. Recurrence is not computable and was not computed. |
| `META-01-F07` | **HIGH** | Four of the eighth seat's ten findings — two MEDIUM, including the one that answered this dispatch's "unanswered" question — were never dispositioned in any form. |
| `META-01-F04` | MEDIUM | `ACTIVE_WORK.yaml` 3,669 → 588,670 bytes in five days; `governance/` ≈ 980k tokens; one boot ≈ 90k tokens. The continuity record cannot be read by the cold agent it exists for. |
| `META-01-F05` | MEDIUM | The carriage instrument's population is chosen by the subject; 66.5 % of rulings 1–3 by character; the omission direction is undeclared; its residue layer is a human reading a diff — `CD-RULE-006` requires **NOT PROVED TO BE CARRIED ANYWHERE**. |
| `META-01-F06` | MEDIUM | §19's *"AUTHORED BYTES ARE EXACTLY"* is false — at minimum the rewritten `CD-BP-005` headline and the `derives_from` addition. `CD-ASR-WO2R3-05-F05` recurring inside its own repair. |
| `META-01-F08` | LOW | `CD-RULE-009` binds forward only and does not say so, unlike `CD-RULE-005`. Zero pre-rule fingerprint files touched since adoption; a fingerprint its own author could not reproduce still stands unmarked. |

**Control bypasses / framework limitations observed.** `pbg boot` detects `ACTIVE_WORK_STALE` and
does it well; it cannot prevent it, because the boundary write is a hand edit and `pbg/` is
read-only to every seat here. **That is a genuine framework limitation, not a seat's failure**, and
it is the carrier owed at §8 item 4. `CONTROL_NOT_VERIFIABLE` for the class as currently structured.

**Continuation implication — and it is deliberately narrower than the grade.** RED on the practice
does **not** block the product lane, and I do not recommend blocking it. What is unsafe is the
**next boundary**, and only that:

1. **`a31c799` is `RESUME_BLOCKED` right now.** A `CD-RULE-007`/`008` follow-up must land and the
   pristine-clone boot verdict must be recorded before anything else. *(If the Project Lead lands
   that follow-up after this verdict is banked, the correction is welcome and does not retire
   `META-01-F02` — the finding is about the window existing at the tip for the fourth time, not
   about whether it was eventually closed.)*
2. **Do not dispatch the ninth Assurance seat against a live `/srv` worktree.** Tag the target, hand
   it a clone. Item 3 of §8 costs an hour and this pass is the second consecutive audit to be
   compromised by its absence.
3. **The ninth seat must be told what §6 found**, or it will inherit `F00`/`F04`/`F08`/`F09`
   undispositioned. **Handing on rather than grading, as instructed:** `CD-PL-F137` is correct and
   material — `required-tests.yaml` on the lane at `be0b355` still quotes the superseded two-tier
   perimeter *as the Product Owner's order*, so **an auditor reading only the lane will grade against
   a perimeter that no longer governs.** That belongs in the ninth dispatch's clause (i), and clause
   (i) must this time enumerate the instruments by `git ls-tree` and not from memory.

**Next safe gate.** The findings-register increment (§8 item 1) with the pre-commit hook (§8 item 2)
in the same dispatch, to an **Engineer** seat, audited by someone who is not me and not the Project
Lead. It is the smallest change that would have caught six of the eight findings above before they
were written down.

---

**On my own standing.** The dispatch instructed me not to produce a twelfth honest confession, and
warned that agreeing with the subject's own admissions and praising the candour is the failure mode.
I have tried to obey it by measuring rather than reading, and by writing nothing here I did not run
a command for. Where the Project Lead was right I have said so plainly and specifically —
`CD-PL-F132`'s diagnosis, `CD-PL-F100`'s carrier, the verbatim banking of a RED verdict it had not
read, the four instruments' declared limits. **None of that changes the grade, because the grade is
not about whether this seat tells the truth about itself. It plainly does, at length. The grade is
about whether telling the truth about itself has been made to change what happens next, and the
measurement taken during this audit is that it has not.**

`CD-META-01`, 2026-08-23T13:05Z.
