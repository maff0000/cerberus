# VERDICT — CD-DISPATCH-META-ASSURANCE-01

**Seat:** `CD-META-01` — Assurance Engineer, read-only.
**IMPORTANT — I AM THE SECOND SEAT BEARING THIS ACTOR ID.** A first `CD-META-01` was live in the
same scratch directory while I worked and banked a `RED` at `f401d48`. See §1. I did not read its
conclusions until after I had taken my own measurements, and I say where I concur and where I
correct it.
**Subject:** `PROJECT_LEAD_SEAT_01`'s reconciliation practice. Not the product, not the perimeter,
not the WO-2 gate.
**Authority:** PO-DECISIONS-0013 ruling 5 · PO-DECISIONS-0019 ruling 5 · CD-AUTH-0001.

---

# 0. GRADE

# RED — ON THE PRACTICE

Confidence **HIGH** on §1, §2, §3 and §5, all of which I measured myself in this tree and in a
pristine clone, and all of which are reproducible from the commands quoted. Scope examined and not
examined is in §8.

The practice does not hold. I am not grading it RED because the record contains faults — a record
that contains faults honestly is healthy. I am grading it RED because **the instruments that decide
what is true in this project produced, during my audit window, a false HIGH finding, a false green
in a dispatch, a duplicate seat, a duplicate entry ID, a duplicate finding ID, and a tip commit from
which the project cannot cold-resume — while the prose describing all of it asserted the opposite.**

---

# 1. THE SHA, AND WHAT IT UNCOVERED — THIS OUTRANKS EVERYTHING ELSE

The dispatch: *"`git rev-parse HEAD` when you start and again when you finish. **IF THEY DIFFER,
THAT IS A FINDING AND IT OUTRANKS EVERYTHING ELSE IN THIS DISPATCH.**"*

```
$ pwd; git rev-parse HEAD            # my first action
/srv/crash-detector
cd79952df1d09e5a09e71809d0c1ea5237f397a9

$ pwd; git rev-parse HEAD            # my last action
/srv/crash-detector
bdf85da5ad89cc8b8fdbe7f61411691f9fb2da3e
```

**THEY DIFFER.** Two commits landed while I read:

```
f401d48  14:14:05  PROJECT_LEAD_SEAT_01  THE META-ASSURANCE SEAT'S VERDICT IS BANKED VERBATIM — RED...
bdf85da  14:16:11  PROJECT_LEAD_SEAT_01  BL-...-0136 — THIS BOUNDARY STOPS. CD-PL-F145 (HIGH): TWO
                                          LIVE PROJECT LEAD SESSIONS ARE COMMITTING TO main...
```

The freeze — *"NOTHING MOVES ON `main` WHILE YOU READ. THIS IS NOT A COURTESY, IT IS `CD-PL-F134`'S
OWN NAMED REMEDY"* — did not hold. It did not hold for the first `CD-META-01` either, twice. **That
is three breaches of the same remedy, in one afternoon, at the boundary convened to grade it.**

## 1.1 WHY IT COULD NOT HAVE HELD — AND THIS IS THE ROOT CAUSE OF MOST OF THIS DOCKET

```
$ pwd; ps -eo pid,etimes,lstart,args | grep 'claude -p'
/srv/crash-detector
1115117  1907s  Sun Aug 23 13:38:01 2026  timeout 21600 claude -p "You are Project Lead ... prompt13"
1149000  1003s  Sun Aug 23 13:53:04 2026  timeout 21600 claude -p "You are Project Lead ... prompt14"
```

**TWO PROJECT LEAD SESSIONS WERE ALIVE SIMULTANEOUSLY ON `main`, BOTH WITH COMMIT AUTHORITY, BOTH
COMMITTING AS `PROJECT_LEAD_SEAT_01`, NEITHER AWARE OF THE OTHER.** The operator wrapper launched
the second at 13:53:04 while the first was 15 minutes into a 6-hour timeout; the first committed
`5e0a873` two seconds later, at 13:53:06.

The Project Lead independently discovered this at 14:16 (`bdf85da`) — **after** I had measured it,
and **after** it had already caused every one of the following:

| Consequence | Evidence |
|---|---|
| `main` moved under two read-only auditors | §1 above; the first seat's own §1 |
| A dispatch declared a freeze it had no power to enforce | `cd79952` vs live PID 1115117 |
| A duplicate `CD-META-01` was launched | two seats, one actor id, one output path |
| Two build-log entries numbered `0136` | `BL-...T125935Z-0136`, `BL-...T131430Z-0136` |
| `CD-PL-F145` minted **twice** | `BL-...T131000Z-0137`, `BL-...T131430Z-0136` |
| A **false HIGH finding**, `CD-PL-F143` | §1.2 |

**`CD-PL-F145` — the finding created to record that a finding ID was minted twice — has itself been
minted twice.** Measured:

```
$ pwd; git grep -ln 'id: CD-PL-F145' HEAD -- governance/engineering/build-log/
HEAD:governance/engineering/build-log/BL-20260823T131000Z-0137.yaml
HEAD:governance/engineering/build-log/BL-20260823T131430Z-0136.yaml
```

That is not rhetoric. The class recurred *inside the artefact created to record its recurrence*,
within five minutes, at both the entry-ID and the finding-ID level.

## 1.2 `CD-PL-F143` IS FALSE, AND IT IS THE MOST IMPORTANT SINGLE FACT IN THIS VERDICT

The re-issue raises `CD-PL-F143`, **HIGH**, against the subject:

> *"NO SEAT EVER RETURNED ANYTHING. THERE IS NO RESULT ARTEFACT ANYWHERE IN THE TREE — MEASURED:
> `find . -iname '*META*'` returns this file and nothing else."*

**The seat had launched. It was alive. It delivered.** When I ran my first command in
`/tmp/meta-assurance-01/` the directory already contained that seat's probes, evidence snapshots, a
pristine clone, and a 39,779-byte verdict in progress — which it finished at 50,118 bytes and which
the Project Lead itself banked 9 minutes later at `f401d48`.

**The measurement that produced a HIGH finding searched the one location the dispatch forbade the
artefact to be in.** `mutation:` in the very same file reads: *"you MAY write your own scratch files
under `/tmp/meta-assurance-01/` and you MUST write your verdict there. **DO NOT** touch
`governance/`…"*. The subject then searched `governance/` and the tree, found nothing, and converted
a guaranteed absence into a finding against itself.

This matters far beyond one wrong finding:

- **A confession was manufactured from a measurement that could not have come out any other way.**
  The dispatch warns *"absences are where this project's false greens have lived."* This is the same
  error with the sign flipped: a **false RED**, and false REDs cost as much credibility as false
  greens.
- **It caused real harm.** On the strength of it the dispatch was re-issued, a second seat with the
  same actor id was launched at the same output path, and the first seat's verdict was one `Write`
  away from being destroyed. I preserved it at
  `/tmp/meta-assurance-01/PRESERVED-prior-verdict-captured-by-CD-META-01.md` (sha256
  `e9b72f2c7bf6f75553fd7830849f98e1a676d46ec8df5134754628c79c2bda2c`) before doing anything else.
  **The correction to `PBG-CONT-007` came within one command of causing the `PBG-CONT-007` failure
  it was correcting.**
- The re-issue's own best sentence — *"A FREEZE CONDITIONED ON AN EVENT THAT LEAVES NO EVIDENCE IS A
  DEADLOCK"* — is correct, and was applied to the wrong side. The event left plenty of evidence. The
  seat looked in the wrong place.

**`CD-PL-F143` must be superseded and withdrawn.** Leaving a false HIGH on the docket corrupts every
future count of this seat's fault rate, which is the number this whole programme is trying to move.

---

# 2. THE CENTRAL HYPOTHESIS, ANSWERED IN THE WORDS THE DISPATCH ASKED FOR

> *"DOES CONFESSING AT VOLUME FUNCTION AS A CONTROL, OR AS A SUBSTITUTE FOR ONE?"*

**IT FUNCTIONS AS A SUBSTITUTE FOR ONE. THE RECORD IS DENSE WITH SELF-CRITICISM AND THE UNDERLYING
BEHAVIOUR RECURS.** I say it in those words because the dispatch asked me to if it were true, and I
measured it to be true.

Here is the measurement that settles it. It is one field.

`ACTIVE_WORK.yaml`'s `last_build_log_entry` at HEAD (`bdf85da`) carries an inline comment that reads:

> **"MOVED IN THE SAME COMMIT AS THE ENTRY IT NAMES — FOURTH CONSECUTIVE BOUNDARY SINCE
> `CD-PL-F132`, AND STILL RECORDED AS AN APPLICATION AND NOT AS A DISCHARGED FINDING: IT HELD EIGHT
> TIMES BEFORE IT FAILED, AND FOUR IS FEWER THAN EIGHT."**

That comment is careful, humble, epistemically sophisticated, and **false**. The value of the field
it annotates is:

```
$ pwd; git show HEAD:governance/engineering/ACTIVE_WORK.yaml | grep -m1 '^last_build_log_entry:'
last_build_log_entry: BL-20260823T124508Z-0135
$ pwd; git ls-tree -r --name-only HEAD -- governance/engineering/build-log/ | tail -1
governance/engineering/build-log/BL-20260823T131430Z-0136.yaml
```

**The pointer says 0135. The newest entry is 0136, and 0137 also exists. The confession and the
defect are in the same line of the same file, and the confession is what makes the defect invisible
— because it reads like a check that ran.** No amount of additional candour in that comment would
have moved the value. That is the answer to the question, in one field.

## 2.1 The same result, measured across the whole history rather than at one point

I reconstructed every commit and asked whether `last_build_log_entry` named the newest entry present
in that same tree.

```
commits on main:                                                       197
commits carrying last_build_log_entry:                                 193
commits where the pointer did NOT name the newest entry (STALE):         5
commits that ADD at least one build-log entry ("applications"):          91
applications where the stated remedy did not hold:                       4  (95.6% compliance)
```

The four failures are applications **76, 85, 90 and 91 of 91**:

```
 76  61e9558  added 0122, pointer 0121     <- CD-PL-F112 raised against this
 85  00ef57e  added 0131, pointer 0130     <- CD-PL-F132 raised against this ("ninth application")
 90  a31c799  added 0136, pointer 0135     <- NOT RAISED BY ANYONE
 91  cd79952  added 0137, pointer 0135     <- NOT RAISED BY ANYONE
```

**Read the shape rather than the percentage.** 75 consecutive successes, then a failure, then 8
successes, then a failure, then 4 successes, then **two consecutive failures — the last two
applications in the project's entire history — and neither was raised.**

At application 91 the seat raised **four** findings (`F142`, `F143`, `F144`, `F145`) about
commit-subject overclaim, a missing artefact, a PO-only file write, and an ID collision. **In that
same commit it left stale the field it had itself called "the single most load-bearing item on this
docket", and did not notice.** One `grep` would have caught it. The confession machine was running
at full output and pointed away from the fault.

That is the finding. **Self-finding at this volume consumes the attention that a check would have
used, and it produces the *feeling* of having checked.** Eight successes made the ninth less likely
to be verified, not more — the subject wrote that sentence itself at `CD-PL-F132`, correctly, and
then reproduced the failure twice more.

## 2.2 And the practice that *did* work is not confession

The dispatch notes that `F142`–`F145` were all found by `git show --numstat` — by refusing to trust
prose. Every finding in this verdict was found the same way: by running a command whose output the
subject could not author. **The one habit on this project with a measured catch rate is mechanical
comparison of a claim against its artefact. Candour has a measured catch rate of zero for the class
it most often confesses to.**

---

# 3. THE DISPATCH'S OWN CLAIMS, MEASURED RATHER THAN INHERITED

The dispatch invited this (*"MEASURE THE CLAIMS IN THIS SECTION RATHER THAN INHERITING THEM"*). Four
of its factual claims are wrong.

## 3.1 **"In a pristine `--no-hardlinks` clone it returns GREEN." — FALSE. IT RETURNS RED.**

```
$ pwd; git clone --no-hardlinks -q /srv/crash-detector /tmp/meta-assurance-01/mine-pristine
$ cd /tmp/meta-assurance-01/mine-pristine; pwd; git rev-parse HEAD
/tmp/meta-assurance-01/mine-pristine
cd79952df1d09e5a09e71809d0c1ea5237f397a9
$ PYTHONPATH=pbg/tools python3 -B -m pbg.cli boot        # EXIT 2
Verdict   : RED
  continuity_state             CONTINUITY_REFERENCE_INVALID/RESUME_BLOCKED
```

**Both arms** (`CD-D-079`), in my own clone, one variable changed:

```
8a8cdf2  AMBER  CONTINUITY_DRIFT/RESUME_AMBER
d968b70  AMBER  CONTINUITY_DRIFT/RESUME_AMBER
6a15ac5  AMBER  CONTINUITY_DRIFT/RESUME_AMBER
5e0a873  AMBER  CONTINUITY_DRIFT/RESUME_AMBER
a31c799  RED    CONTINUITY_REFERENCE_INVALID/RESUME_BLOCKED   <- begins here
cd79952  RED    CONTINUITY_REFERENCE_INVALID/RESUME_BLOCKED   <- my target
bdf85da  RED    CONTINUITY_REFERENCE_INVALID/RESUME_BLOCKED   <- current tip
```

And the exact cause, from the framework's own function:

```
STATE : ACTIVE_WORK_STALE
DETAIL: pointer is BL-20260823T124508Z-0135 but the newest entry is BL-20260823T131430Z-0136
        (commit bdf85da5ad89 at ancestry position 198); Active Work describes a superseded state
POLICY: BLOCKED
```

**CONTINUATION IMPLICATION, AND IT IS THE MOST URGENT THING IN THIS DOCUMENT: `main` HAS BEEN
`RESUME_BLOCKED` FOR THREE CONSECUTIVE COMMITS. A COLD AGENT CANNOT BOOT THIS PROJECT FROM ITS OWN
TIP RIGHT NOW.** `PBG-CONT-007`'s guarantee — the thing `CLAUDE.md` says this project must survive —
is currently void, and it is void because of a one-line pointer. The dispatch told me this state was
GREEN. It was measured at an earlier SHA and transcribed forward, which is the exact act
`CD-RULE-003`/`CD-RULE-009` and `CD-PL-F36` ("resolve, never transcribe") prohibit, committed inside
the dispatch that mandates them.

## 3.2 **"There are now THREE instruments here" — there are FOUR, and the omitted one FAILS.**

```
$ pwd; ls tools/reconciliation/
check_blueprint_carried_po_0019_verbatim.py
check_blueprint_carried_po_text_verbatim.py
check_lane_governance_citations.py          <- not enumerated by the dispatch
check_pid_carried_po_0020_verbatim.py

$ pwd; python3 -B tools/reconciliation/check_lane_governance_citations.py   # EXIT 1
CD-LANE-CITATIONS: FAIL — 136 citations, 2 unresolved
  UNRESOLVED PATH   pbg/controls/PBG-SEC-002.yaml   (1 occurrence(s))
```

`CD-D-129` clause i exists so that an auditor is **told in advance** which instruments exit non-zero
by declared state. The one instrument in that directory whose *normal* arm exits 1 is the one the
disclosure omits. I am not grading it — it concerns lane citations and is the ninth seat's — but the
enumeration defect is practice and is mine. **Handed on to the ninth seat in §9.**

## 3.3 **"EACH HAS A `--counterfactual` ARM THAT EXITS 1 BY DESIGN" — one has no such arm at all.**

```
$ pwd; python3 -B tools/reconciliation/check_blueprint_carried_po_text_verbatim.py --counterfactual
error: unrecognized arguments: --counterfactual        # EXIT 2

$ pwd; for f in ...; do grep -c counterfactual $f; done
check_blueprint_carried_po_text_verbatim.py    0
check_blueprint_carried_po_0019_verbatim.py    7
check_pid_carried_po_0020_verbatim.py          8
```

The **oldest** carriage instrument — the `CD-D-172` one, cited across the record and in two prior
dispatches as evidence that the Blueprint carries the Product Owner's bytes — **has never had a
falsifying arm.** Its `PASS` has never been shown capable of becoming a `FAIL`. That is
`CD-PL-F136`'s class exactly ("one arm licenses a claim about one route and the record read it as a
claim about the guard"), except with **zero** arms, and it has been standing longer than any other
instrument here.

## 3.4 The 3/4 claim — **THIS ONE HOLDS.**

```
$ pwd; git ls-tree -r --name-only main | grep 'required-tests\.yaml'
(absent)
$ pwd; git grep -nI '4/4' main -- .     # every hit is a denial, a quotation, or a WO-3 deferral
main:PID.md:130:> WO-3, not here. 4/4 is a WO-3 claim and nobody may make it today.
```

The register file is genuinely absent from `main` and nothing on `main` asserts 4/4. **This claim is
sound and I could not refute it.** I note that the dispatch's own suggested command (`grep
required-tests`) returns two `governance/assurance/**/required-tests/runs/*.json` paths and would
mislead a reader into thinking the register is present; the precise claim is about
`required-tests.yaml` and is correct.

---

# 4. THE INVITED ATTACKS, TAKEN

## 4.1 ARM 2 OF `check_pid_carried_po_0020_verbatim.py` IS DEFEATED. TWICE. DEMONSTRATED, NOT ARGUED.

The dispatch: *"CAN YOU CONSTRUCT A REINTRODUCTION OF THAT SENTENCE, AS NORMATIVE PROSE, THAT ARM 2
PASSES? If you can, say so."* **I can. Here it is.**

Arm 2b's entire definition of "mention versus use" is this:

```python
before = bp[max(0, site - 2):site]
after  = bp[site + len(needle):site + len(needle) + 2]
if '"' not in before or '"' not in after:      # <- a MENTION is a quote mark within 2 bytes
    unquoted.append(site)
```

**Quotation marks carry no normative force.** A document may state a binding requirement and quote
the operative clause inside it. I copied `PID.md`, `BLUEPRINT.md` and `PO-DECISIONS-0020.md` into a
scratch root and appended to the Blueprint:

> ## §17.9 — BINDING
>
> Every seat MUST carry the forgery-detection obligation as a first-class criterion, *"not as a
> note, not as a residue paragraph, and not as a manual step"*. This requirement is normative and
> binds the Project Lead, every Engineer and every Assurance seat. Non-compliance is a RED.

```
$ pwd; python3 -B .../check_pid_carried_po_0020_verbatim.py --root /tmp/meta-assurance-01/attack
  ARM 2 — THE REMOVAL: F05's sentence survives only as a MENTION, never as a USE
    [REMOVED ] 2a — the original normative construction is ABSENT
    [MENTIONS] 2b — all 5 survival(s) are quoted mentions, not uses
EXIT=0
```

**EXIT 0.** The `F05` sentence is back, in the document's own binding voice, addressed to every seat,
with a RED attached to non-compliance — and the check that exists to prove it was removed reports it
as a quoted mention.

**A second, simpler defeat: paraphrase.** Arm 2 tests one literal string.

> The forgery-detection obligation SHALL take a first-class criterion form: neither as a note, nor
> as a residue paragraph, nor as a manual step. This binds every seat.

```
EXIT=0    PO-0020-PID-AMENDED-AND-F05-REMOVED-VERBATIM: PASS
```

**Arm 2 guards the instance, not the class** (`GUARD_THE_INSTANCE_NOT_THE_CLASS`, and `CD-RULE-004`
requires a guard to close its class *or declare its own limit* — it declares three limits and none
of them is this one). Its declared limits are honest and thorough about *words versus bytes* and
*completeness*; they say nothing about the fact that its central cleverness is a two-byte lookaround.
**This is a real finding and the dispatch said it would rather have it from me than not at all.**

## 4.2 THE PID §6 AMENDMENT — `CD-PL-F144` UNDERSTATES THE PROBLEM, AND I SAY SO AS INVITED

The defence recorded at `CD-PL-F144` is *"the normative sentence in it is the PO's, quoted, and the
rest is measurement."* Tested byte by byte against `git diff a31c799^..a31c799 -- PID.md`:

**`PID.md` line 130, in the seat's own voice, not quoted, not attributed:**

> **"4/4 is a WO-3 claim and nobody may make it today."**

```
$ pwd; grep -rn 'nobody may make it' governance/decisions/
(zero matches — it is not the Product Owner's, anywhere)
```

*"nobody may"* is a prohibition binding every actor on the project. It is **a seat-authored normative
sentence in a file whose own frontmatter reads `amendment: PO only`.** It is *consistent* with the
Product Owner's ruling and it is not *from* it. `CD-PL-F144` should be re-graded on that basis.

For balance, two things in that diff I checked and cleared: `NEW_REQUIREMENT` **is** the Product
Owner's word (`PO-DECISIONS-0020.md:17`), and the `CD-AC-017` §6 row is carried verbatim. The one
other seat-authored placement claim — *"Its durable home is therefore the Required Test Register's
`pid_relation` field"* — is a derivation from the ruling and I do not press it.

## 4.3 THE §19 AUTHORED-BYTES ENUMERATION — SUBSTANTIALLY ACCURATE

Resolving each diff hunk to the heading above it **in the Blueprint as it stood at that commit**:

```
v0.4.0  7794c15..8a8cdf2   frontmatter 18 · §14 12 · §15 2 · §17 1 · §19 1
v0.4.1  abafec2..a31c799   §16 28 · frontmatter 19 · §19 1
```

The v0.4.0 row's claims (§17 restated to three tiers, §14/§15 gain `CD-AC-017`/`CD-AC-018`) resolve
to real hunks; §17's single added line is the long `CD-BP-005` table row and does carry the
three-tier text. The `F05` removal is real and is one line. **I could not refute this enumeration and
I do not find against it.** The §16/§17 label discrepancy the seat disclosed itself is visible in my
mapping and I confirm the disclosure was warranted.

---

# 5. THE BACKWARD-SWEEP QUESTION — MEASURED, AND IT WAS ALREADY ANSWERED

> *"WHEN A RULE IS ADOPTED ON THIS PROJECT, IS THE RECORD SWEPT BACKWARD FOR THE INSTANCES THAT
> MOTIVATED IT?"*

## **NO.** Measured on `CD-RULE-002`.

`CD-RULE-002` (per-seat commit identity) was adopted at `80b4a24`, 2026-08-19T09:55. Its own
statement: *"No commit produced by an agent seat may be authored under a human identity. Ambient git
identity attributes agent work to a human, **which falsifies the record of who acted**."*

```
$ pwd; git log --format='%an' 80b4a24^ | sort | uniq -c
     22 Matt Scott
$ pwd; git log --format='%an' 80b4a24..HEAD | sort | uniq -c
    127 PROJECT_LEAD_SEAT_01
     49 Matt Scott
```

**Twenty-two commits — the entire first two days of seat work — are authored under a human
identity.** Those are precisely the instances that motivated the rule. Nothing in `governance/`
enumerates them, reconciles them, or notes that the record of who acted is falsified for that span.
The rule closed the practice forward and the motivating population was never touched.

## 5.1 And the answer itself was not swept forward, which is worse

```
$ pwd; grep -n 'SWEPT BACKWARD' governance/assurance/WO-2R3/VERDICT-SEVENTH-SEAT.md
711: ...**NO.** CD-PL-F124 found it for SHAs in governance/. I HAVE NOW FOUND THE SAME ANSWER,
     INDEPENDENTLY, FOR CARRIER CITATIONS IN src/ AND tools/. Two populations, same rule, same
     result. THAT IS NOT A COINCIDENCE AND IT SHOULD BE TREATED AS A PROGRAMME-LEVEL FINDING.

$ pwd; grep -n 'still unanswered' governance/dispatch/CD-DISPATCH-META-ASSURANCE-01.yaml
154:  Carried forward from BL-...-0128 and still unanswered...
```

**The seventh Assurance seat answered this question, with two independent populations, banked it on
`main`, and explicitly asked for it to be escalated. The dispatch that launched me — written after
that verdict was banked — calls the question "still unanswered."** My answer is the third
independent confirmation, on a third population.

**The project does not sweep backward, and it does not carry forward either.** An answer delivered
by an independent auditor into the record did not survive to the next dispatch. That is the same
mechanism as `CD-PL-F139`: *a correction that lives only in a record nobody is forced to read is not
a carrier.* It applies to auditors' answers exactly as it applies to the subject's own findings, and
**that generalisation is the most important thing in this section**: the problem is not the Project
Lead's memory. It is that this project has no forcing function on *any* reader.

## 5.2 One rule where the forward sweep partly worked, for contrast

`CD-PL-F98` (every probe prints the tree it read):

```
build-log entries BEFORE F98 (n=62):   0 mention pwd
build-log entries AFTER  F98 (n=30):  17 mention pwd
```

Forward adoption is real and substantial — 0% to 57%. Backward sweep is zero. **This is the profile
of every rule I measured: real forward effect, no backward effect, and no mechanism preventing the
forward effect from decaying.**

---

# 6. VERDICT ON EACH DOCKETED FINDING — CLOSED / OPEN / RECURRING, MEASURED

I read each in its own build-log entry and did not use any derived table (`CD-PL-F121`).

## The Product Owner's nine

| # | Class | Verdict | The measurement |
|---|---|---|---|
| **F98** | probe must print its own tree | **OPEN** | 0/62 entries before → 17/30 after. Adopted forward, never swept backward, no mechanism. |
| **F100** | fingerprint recipe / gitignored sweep | **NOT REACHED** — see §8. I will not grade it from the subject's summary. |
| **F102** | instruments exiting non-zero by declared state, undisclosed | **RECURRING** | §3.2: four instruments exist, three were disclosed, and the undisclosed one is the one that exits 1. Identical shape to F102 ("thought there was ONE, there are TWO"). |
| **F111** | `last_build_log_entry` went stale | **RECURRING** | §2.1. Stale at applications 90 and 91 of 91; stale at HEAD now. |
| **F112** | same fault at the very next boundary; remedy called STRUCTURAL | **RECURRING** | §2.1. The "structural fix" is a convention; it has now failed 4 times in 91, twice consecutively, most recently unnoticed. |
| **F132** | the structural fix failed at its ninth application | **RECURRING, AND WORSE THAN WHEN RAISED** | It failed at 9, held 4, then failed twice consecutively. **F132's own failures were caught; applications 90 and 91 were not caught by anyone** — the detection that caught F111/F112/F132 (`CD-RULE-008` pristine-clone boot) was not run at these two boundaries. |
| **F134** | `main` moved under a live read-only auditor | **RECURRING, THREE TIMES TODAY** | Twice under the first `CD-META-01` (`a31c799`, `cd79952`), once under me (`f401d48`, `bdf85da`). §1. The named remedy is unenforceable while two PLs are live — §1.1. |
| **F135** | a dispatch target that named no tree | **CLOSED for the instance, OPEN for the class** | This dispatch names its tree, branch and SHA-resolution procedure correctly. But it contains **four fresh factual defects** (§3.1–3.3, §5.1). The dispatch-defect class is **RECURRING**; the specific "no tree" defect is closed. |
| **F136** | one counterfactual arm licensed a claim about the guard | **RECURRING, AND MEASURED WORSE** | §3.3: an instrument with **zero** arms is cited across the record as evidence. §4.1: an instrument with arms has one that I defeated twice. |

## The accumulated docket

| # | Class | Verdict | The measurement |
|---|---|---|---|
| **F99** | the ISSUED / CARRIED gap | **RECURRING — and it produced the sharpest instance in the project's history** | `5e0a873` declared the seat "ISSUED AND OUT"; nothing recorded the carry. `CD-PL-F143` then declared the *result* absent while it existed. §1.2. Mentioned in exactly **one** build-log file since it was raised. |
| **F113** | a measurement that reported the wrong exit status | **NOT SEPARATELY REACHED**; the mechanical lesson (assign `RC=$?` immediately) is visibly applied in later entries. |
| **F119, F120** | unsound measurement criteria in product enumeration | **NOT REACHED** — product-measurement findings; §8. |
| **F121** | this seat's derived tables are artefacts of the parse | **RECURRING** | §3.1–3.3: three false factual claims in one derived disclosure section, in the dispatch that cites `CD-PL-F121` as the reason to distrust its derived tables. The instruction to distrust was correct; the table was still wrong. |
| **F122** | — | **NOT REACHED** — no separable finding record located; §8. |
| **F123, F124** | fabricated / dangling SHAs in landed entries | **INSTANCE STILL LIVE, CLASS OPEN** | I swept all 147 SHA-valued fields in all 91 entries: **2 do not resolve**, both in `BL-20260819T064300Z-0011.yaml` (`baseline_sha` and `current_sha` = `17d77219dd3f…`). Correctly not edited (history is not rewritten) — but **`pbg log` returns `VERDICT: GREEN (0 invalid)` with a dangling SHA in a landed entry**, so the framework validator does not see this class. That is a control gap, not just a record scar. |
| **F137** | lane register still quotes the two-tier perimeter | **OUT OF SCOPE — handed to the ninth seat**, §9. |
| **F138** | seat's own prose in a protected file | **RECURRING** | §4.2: the same shape recurred in `PID.md` at the next boundary, and this time the sentence is normative, which F138's instance was not. |
| **F139** (original) | a stale belief survived the context boundary | **RECURRING, MECHANISM CONFIRMED, AND NOW GENERALISED** | The subject's own account is accurate. §5.1 shows the same mechanism destroying an *auditor's answer*, which is a strictly larger problem than a seat's stale belief. |
| **F142** | commit subject asserts more than its tree | **OPEN** | The class is intrinsic to prose commit subjects; no carrier exists. |
| **F143** | "ISSUED AND OUT" with no artefact | **FALSE — WITHDRAW IT.** §1.2. |
| **F144** | seat wrote into PO-only `PID.md` | **UNDERSTATED — RE-GRADE.** §4.2. |
| **F145** | finding IDs minted twice, no allocator | **RECURRING WITHIN 5 MINUTES OF BEING RAISED** | §1.1: two entries numbered `0136`; `CD-PL-F145` itself minted twice. |

**Tally: 0 CLOSED. 1 FALSE. 1 UNDERSTATED. 5 OPEN. 11 RECURRING. 6 NOT REACHED.**

---

# 7. THE STRUCTURAL CARRIERS THAT ARE OWED, AND WHERE EACH MUST LIVE

The dispatch called this the most valuable thing I could produce, and said the honest answer might
be `pbg/`. **It is partly `pbg/` — but the sharpest answer is smaller and cheaper than anyone on this
project has realised, and one of the three lies outside the repository entirely.**

## 7.1 THE CARRIER ALREADY EXISTS IN `pbg/`. IT WORKS. IT IS NOT WIRED TO THE GATE.

This is the finding I most want on the record, and it **corrects** the first `CD-META-01`, which
wrote *"`.git/hooks/` is empty; `git ls-files` shows no tracked hook and no CI"* and concluded a hook
must be built. That premise is wrong:

```
$ pwd; git config --local --get core.hooksPath
pbg/tools/hooks
$ pwd; git ls-files | grep hooks/
pbg/tools/hooks/install.sh
pbg/tools/hooks/pre-commit          # tracked, executable, COMMISSIONED AND ACTIVE
```

**A pre-commit hook is installed and running on every commit in this repository.** And here is its
entire scope:

```sh
STAGED=$(git diff --cached --name-only --diff-filter=ACMR | grep '^governance/authority/' || true)
[ -n "$STAGED" ] || exit 0
```

```
$ pwd; grep -rn 'ACTIVE_WORK\|build-log\|engineering' pbg/tools/hooks/
(no matches)
```

So:

- **The DETECTOR exists in `pbg/` and is excellent.** `continuity.active_work_currency()` returns
  `ACTIVE_WORK_STALE` with policy `BLOCKED`, precisely and with a helpful message. It caught
  `F111`, `F112` and `F132`, and it caught `a31c799`, `cd79952` and `bdf85da` for me.
- **The GATE exists in `pbg/`, is commissioned, and runs on every commit.**
- **THEY ARE NOT CONNECTED.** The gate greps for one directory and waves the continuity records
  through. Every one of the four stale-pointer commits passed a live pre-commit hook.

**What is owed is not a new control. It is three lines in
`pbg/tools/hooks/pre-commit` extending the staged-path filter to `governance/engineering/` and
calling the currency validator that is already sitting in the same package.** That would have made
`F111`, `F112`, `F132`, `a31c799`, `cd79952` and `bdf85da` **impossible** — four findings, five days
of prose, three consecutive `RESUME_BLOCKED` commits.

**AND NO SEAT ON THIS PROJECT MAY WRITE IT.** `pbg/` is pinned read-only (`CLAUDE.md`, non-waivable;
`PBG-FWK-013`). **This is the answer nobody has been able to give, and it is much cheaper than the
question implied.** It requires a bounded framework dispatch against PBG itself, implemented by an
Engineer and certified by a seat that did not implement it (`PBG-SOD-001`).

**Interim carrier that IS inside a seat's scope, and should be built anyway:** a project-owned
`tools/hooks/pre-commit` that (a) `exec`s the PBG hook so authority validation is not lost, then
(b) runs the currency check, commissioned by pointing `core.hooksPath` at it. `tools/` is seat-
writable (three instruments already live there). **It moves a PBG-owned setting, so it needs Product
Owner authorisation and must be recorded as a deliberate divergence, not slipped in.**

I concur with the first seat's §8 item 4 (PBG should own the whole "close a boundary" transaction —
write entry, move pointer, validate, read back, refuse on any failure) and regard it as the correct
long-form answer. **§7.1 is the version that could ship this week.**

## 7.2 THE CARRIER THAT LIES OUTSIDE THE REPOSITORY ALTOGETHER — AND NO SEAT AND NO FRAMEWORK CAN REACH IT

**Nothing in `pbg/`, `governance/` or `tools/` can prevent two Project Lead processes running at
once, because the launcher is not in the repository.** The wrapper (`.wo2r3*-runner.sh`, invoked by
an operator `bash -c`) launched PL session B while PL session A had 5.5 hours left on its timeout.
Neither process can see the other; both commit as `PROJECT_LEAD_SEAT_01`; `CD-RULE-002` does not
help because it guards *human-versus-agent*, not *actor-versus-actor* — one identity, two actors, and
the record of who acted is falsified again by a route the rule does not cover.

**This is the true root cause of `CD-PL-F134` (all three of today's breaches), `CD-PL-F143`,
`CD-PL-F145` (both of them), the duplicate `0136` entries, and the duplicate `CD-META-01` seat.**
Grading them as separate reconciliation failures by the Project Lead is, in my judgement, **partly
unjust** — several are downstream of a concurrency the seat had no instrument to detect and no
authority to prevent. I say that having found against the seat everywhere else in this document.

**Where it must live:** the operator's launch wrapper, plus a repository-visible trace so the
condition is *detectable* from inside even though it is not *preventable* from inside. Minimum
viable form, and it is cheap:

1. **A lease.** The wrapper acquires an exclusive lock (`flock` on a file under `/srv/`) before
   launching a PL, and refuses to launch while one is held. *Outside the repository. Operator only.*
2. **A liveness trace in the tree.** Each PL session writes its PID, start time and wrapper timeout
   to `governance/continuity/SESSIONS/<pid>.yaml` at boot, and boot **refuses** if another entry is
   live (`ps` on the recorded PID). *Inside seat scope. Detects what it cannot prevent.*
3. **Per-session commit identity.** `CD-RULE-002`'s scheme should be `PROJECT_LEAD_SEAT_01/<pid>` or
   a per-session suffix, so that two live sessions are visible in `git log` instead of merged. *Inside
   seat scope; needs Product Owner ratification since `CD-RULE-002` is PO-sourced.*

## 7.3 AN ID ALLOCATOR AND A FINDINGS REGISTER — INSIDE SCOPE, NOTHING BLOCKS IT

The subject deliberately left this unwritten and handed it to me. **My answer: write it, but not as a
third self-prescribed fix — write it as a check that runs in the gate of §7.1, not in a seat's
attention.** A uniqueness check over `governance/engineering/build-log/` covering **both** entry
sequence numbers and `CD-PL-F` ids would have caught the duplicate `0136` and both `F145`s in under
a second. It belongs in `tools/`, wired to the hook. **Wherever it lives, it must be *executed by
something that is not a seat deciding to execute it* — that is the whole lesson of this docket.**

I also concur with the first seat's proposal of a `governance/findings/REGISTER.yaml` with a
`carrier` column that must read a path or the literal `NOT PROVED TO BE CARRIED ANYWHERE`
(`CD-RULE-006`). **Its real value is that it makes "does this practice work?" a computable question.**
My §6 tally — 0 closed, 11 recurring — took me a full pass to produce and should be one command.

## 7.4 WHAT MUST **NOT** BE THE CARRIER

**Another rule in `PROJECT-RULES.md`, and another paragraph in a build-log entry.** There are nine
rules. `CD-RULE-007` and `CD-RULE-008` are written down, correct, and prescribe exactly the
pristine-clone boot that would have caught `a31c799`, `cd79952` and `bdf85da` — and all three
shipped anyway. **The record already contains every correct instruction. Adding a twelfth confession
or a tenth rule is the failure mode this dispatch told me not to reproduce.**

---

# 8. WHAT I DID NOT REACH — NAMED PLAINLY

*A pass that quietly covers less than its docket is the defect this project has found six times. I
am not adding a seventh.*

- **`CD-PL-F100`** (fingerprint recipe / gitignored-sweep defect) — **NOT REACHED.** I did not
  reconstruct the fingerprint recipe or test the gitignored sweep. I refuse to grade it from the
  subject's summary of it (`CD-PL-F121`). **It remains ungraded by this pass.**
- **`CD-PL-F119`, `CD-PL-F120`** — **NOT REACHED.** Both concern soundness of product-class
  enumeration criteria (`__slots__` / `__setstate__`). Reaching them means auditing the perimeter,
  which is the ninth seat's and explicitly out of my scope.
- **`CD-PL-F113`, `CD-PL-F122`** — **NOT SEPARATELY REACHED.** I could not isolate a standalone
  finding record for `F122`; `F113`'s mechanical lesson is visibly applied but I did not verify it
  across every later measurement.
- **`pbg validate`** — I ran `pbg boot` and `pbg log` but **did not run `pbg validate`**, so the
  dispatch's claim that it "RETURNS AMBER FOR THE SAME DECLARED REASON" is **unverified by me**.
  Given that the parallel claim about `pbg boot` proved false, **this claim should be treated as
  unmeasured, not as inherited.**
- **`pbg resume` anomaly — reported, not diagnosed.** In my pristine clone `pbg resume` returned
  `NEW_PROJECT_CONTINUITY_NOT_INITIALISED / RECOVERY_BOOTSTRAP_REQUIRED / RESUME_BLOCKED` — i.e. it
  reported this project as *never initialised* — while `pbg boot` in the same directory read the
  continuity records correctly. One of the two is wrong about root detection. **I did not chase it.
  It is a framework limitation worth a separate look** (`CONTROL_NOT_VERIFIABLE` in that narrow
  respect).
- **The first `CD-META-01`'s verdict** — I read only its §0, §1, §8 and its section headings, after
  taking my own measurements. **I did not audit it.** Where we differ (§7.1) I have shown my
  evidence; where I have not checked it, I make no claim either way.
- **Portability** — `pbg boot` in my clone printed `repository /srv/crash-detector` while
  `worktree` correctly showed the clone path. Noted, not pursued.
- **The whole product lane**, `CD-AC-002`/`CD-AC-005`, the three-tier perimeter, `be0b355`, the
  forgery findings, the WO-2 gate — **deliberately untouched**, per scope.

---

# 9. HANDED ON TO THE NINTH ASSURANCE SEAT — NAMED, NOT GRADED

1. **`tools/reconciliation/check_lane_governance_citations.py` EXITS 1 on `main` right now**: *"136
   citations, 2 unresolved"*, including `pbg/controls/PBG-SEC-002.yaml`. It was **not** disclosed in
   my `CD-D-129` clause i briefing. If your dispatch also enumerates "three instruments", **it has
   inherited the same defect — measure `ls tools/reconciliation/` yourself.**
2. **`check_blueprint_carried_po_text_verbatim.py` has no `--counterfactual` arm** (§3.3). If your
   dispatch cites it as evidence that the Blueprint carries the PO's bytes — and
   `CD-DISPATCH-WO2R3-ASSURANCE-08.yaml:124` does — **that evidence has never been falsified.**
3. **`CD-PL-F137` is live**: `required-tests.yaml` on the lane at `be0b355` still quotes the
   two-tier perimeter as the Product Owner's order, while `BLUEPRINT.md` on `main` says three tiers.
4. **The PID content hash moved** `441d83166b2f3d0c` → `538e30f3bf4f1803` at `a31c799`. **Any
   Required Test Register pinned to the old hash is not a valid input and must be re-pinned.** The
   lane register is one such.
5. **`main` is `RESUME_BLOCKED`** (§3.1). If your dispatch tells you a pristine clone boots GREEN,
   **run it yourself before you believe it.**

---

# 10. CONTINUATION IMPLICATION — WHAT IS TRUE VERSUS WHAT IS SAFE TO DO NEXT

**These are different calculations and I am keeping them apart.**

**What is true:** the reconciliation practice is RED. Confession is substituting for control. Eleven
of the eighteen classes I could grade are recurring, none is closed, one docketed finding is false,
and the record's own tip cannot be booted.

**What is safe to do next, in this order:**

1. **STOP COMMITTING TO `main` UNTIL EXACTLY ONE PROJECT LEAD IS LIVE.** `bdf85da` already declares
   this boundary stopped; that is correct and it should hold. §7.2.
2. **BANK THIS VERDICT AND THE FIRST SEAT'S SIDE BY SIDE, VERBATIM, BEFORE READING EITHER**
   (`CD-D-143`). Two `CD-META-01` verdicts exist; **neither supersedes the other and the second must
   not be filed as a correction of the first.** They were produced independently and they diverge on
   §7.1, which matters.
3. **MOVE THE POINTER.** `last_build_log_entry` → the newest entry, in the commit that does it, and
   verify with `pbg boot` **in a pristine clone at the resulting SHA** before declaring the boundary
   closed (`CD-RULE-008`, which already says this). **`main` cannot be cold-resumed until this is
   done, and that is the only item here that is genuinely urgent.**
4. **Supersede `CD-PL-F143` as FALSE** and re-grade `CD-PL-F144`. §1.2, §4.2.
5. **Resolve the duplicate `0136` entries and the duplicate `CD-PL-F145`** by supersession, never by
   edit.
6. **Raise the `pbg/` hook defect as a bounded framework dispatch** (§7.1). It is the single highest
   harm-prevented-per-line item on this docket and **no seat here may write it.**
7. **Only then** dispatch the ninth Assurance seat, with §9 in its briefing.

**A PASS is not an acceptance and this is not a PASS** (`PBG-AUTH-003`). Acceptance is the Product
Owner's alone.

---

# 11. RETURN

```
target        /srv/crash-detector  main
              START  cd79952df1d09e5a09e71809d0c1ea5237f397a9
              FINISH bdf85da5ad89cc8b8fdbe7f61411691f9fb2da3e     *** THEY DIFFER ***
verdict       RED — on the Project Lead's reconciliation practice
confidence    HIGH on §1, §2, §3, §5; MEDIUM on §6 rows marked from single measurements
scope         reconciliation practice, continuity instruments, the three carriage checks, the
              dispatch itself, the PID §6 amendment, the §19 enumeration, the backward-sweep
              question. NOT the product, the perimeter, the lane, or the WO-2 gate.
not examined  F100, F119, F120, F122, F113 (partial), `pbg validate`, the first seat's verdict
              beyond four sections — all named in §8
bypasses      pre-commit hook commissioned but scoped to one directory (§7.1); no concurrency
              interlock anywhere in or out of the repository (§7.2); `pbg log` GREEN with a
              dangling SHA in a landed entry (§6)
next gate     one live Project Lead → move the pointer → pristine-clone boot GREEN → bank both
              meta verdicts → withdraw F143 → framework dispatch for the hook → ninth seat
```

**Mutation:** none. I created nothing outside `/tmp/meta-assurance-01/`, ran no `git add`, `commit`,
`checkout` or any write against `/srv/crash-detector`, and took no lock. All `git checkout` calls in
this pass were inside my own clone at `/tmp/meta-assurance-01/mine-pristine`. `pbg boot` was verified
non-mutating (`git status --porcelain` → 0 after running it).

**ONE DEVIATION FROM MY DISPATCH, DECLARED HERE AND NOT IN A FOOTNOTE.** The dispatch instructs me to
write to `/tmp/meta-assurance-01/VERDICT-META-ASSURANCE-01.md`. **I DID NOT WRITE THAT PATH.** It was
already occupied by the first `CD-META-01`'s verdict, which was still being written when I arrived,
and writing it would have destroyed another seat's product — the precise `PBG-CONT-007` failure this
dispatch was re-issued to correct. **A filename in a dispatch does not outrank another seat's
evidence.** My verdict is at:

- `/tmp/meta-assurance-01/VERDICT-CD-META-01-SECOND-SEAT.md`
- `/tmp/meta-assurance-01/VERDICT-META-ASSURANCE-01-SECOND-SEAT.md` (identical copy)

*(No sha256 is quoted for this file here: a fingerprint written inside the artefact it fingerprints
cannot be correct — `PBG-EVID-001`, evidence must be independent of what it certifies. Take it with
`sha256sum` against whichever copy you bank, and record it in the banking commit.)*

**The collision itself is evidence for §1.1 and should be read as such: two seats, one actor id, one
mandated output path, and the only thing that prevented data loss was an auditor checking before
writing.**

**Preserved evidence** (the first seat's verdict, captured before I wrote anything, in case my write
had collided with its own):
`/tmp/meta-assurance-01/PRESERVED-prior-verdict-captured-by-CD-META-01.md`
sha256 `e9b72f2c7bf6f75553fd7830849f98e1a676d46ec8df5134754628c79c2bda2c` (39,779 bytes, its
in-progress state at 13:09Z; its final banked state is 50,118 bytes at `f401d48`).

---

*`CD-META-01` (second seat of that id). Read-only. This verdict is my own work and my standing is in
what I declined to establish as much as in what I did.*
