# PROJECT RULES — crash-detector

Standing rules that bind every seat on this project. Each carries its source of authority. A rule
sourced to the **Product Authority** may not be relaxed by any seat, including the Project Lead. A
rule sourced to the **Project Lead** is a Level-1 engineering standard: it may be superseded by a
later Project Lead ruling, recorded as a supersession, never by silent departure.

These are enforced **procedurally** where the framework does not yet carry them natively. A
procedural control that is not written down is not a control, which is why this file exists.

---

## CD-RULE-001 — no run record is admitted without its paired assurance verdict

**Source:** PRODUCT AUTHORITY, `PO-GATE-REVIEW-WO2-0001.md` Ruling 1. Effective 2026-08-19.
**Status:** ACTIVE, non-relaxable by any seat.

1. **No run record is admitted at any gate without the paired assurance verdict attached.** The run
   record and the verdict travel together or neither is admitted.
2. **A criterion the Assurance seat holds not-PASS cannot compute PASS**, regardless of which runs
   are admitted. Admitted runs are evidence *offered to* a verdict, never a substitute *for* one.

**Why:** measured on a throwaway copy at the WO-2 gate, admitting `RTR-WO2-0001` made the framework
compute PASS on all five gate criteria — the same five an independent auditor had declined to pass.
The register computes status from runs and does not know what the auditor concluded. That gap is
`CD-FWK-005`, harvested to the framework backlog as **IMP-015 (HIGH)**. Until IMP-015 lands, the gap
is closed by this rule and by a human refusal.

**How the Project Lead enforces it:**

* Before any `latest_admitted_run` is written, the paired Assurance Build Log entry must exist as a
  committed file, and its per-criterion verdicts must be quoted into the admission record.
* Any criterion held not-PASS by that entry is recorded as **not-PASS in the gate declaration**, and
  the gate declaration — not the validator's computed status — is what the Project Lead reports.
* If the validator computes PASS where the auditor held not-PASS, that divergence is reported as a
  defect of the tooling, and the auditor's verdict governs.

## CD-RULE-002 — per-seat commit identity

**Source:** PRODUCT AUTHORITY, `PO-GATE-REVIEW-WO2-0001.md` Ruling 3. Effective 2026-08-19.
**Status:** ACTIVE, non-relaxable by any seat.

**No commit produced by an agent seat may be authored under a human identity.** Ambient git identity
attributes agent work to a human, which falsifies the record of who acted.

**The scheme.** Author *and* committer are set to the acting seat:

| Seat | git author / committer |
|---|---|
| Project Lead | `PROJECT_LEAD_SEAT_01 <project-lead-seat-01@seats.crash-detector.invalid>` |
| Engineer, WO-2 | `CD-ENG-WO2-01 <cd-eng-wo2-01@seats.crash-detector.invalid>` |
| Engineer, WO-2R | `CD-ENG-WO2R-01 <cd-eng-wo2r-01@seats.crash-detector.invalid>` |
| Assurance, WO-2 | `CD-ASR-WO2-01` — **read-only; holds no commit by design** |
| Assurance, WO-2R | `CD-ASR-WO2-02` — **read-only; holds no commit by design** |

Generally: name = the `actor_id` exactly as it appears in the seat's dispatch record; email =
that `actor_id` lower-cased, at `seats.crash-detector.invalid`.

**Why `.invalid`:** RFC 2606 reserves it, so the address is guaranteed undeliverable. A seat
identity must be unmistakably not a mailbox and must never be routable.

**How — and the way that DOES NOT WORK.** Set the four environment variables on the commit
invocation itself:

```
GIT_AUTHOR_NAME=... GIT_AUTHOR_EMAIL=... GIT_COMMITTER_NAME=... GIT_COMMITTER_EMAIL=... git commit ...
```

`git -c user.name=... -c user.email=... commit` **is not sufficient on this host and fails
silently.** Measured 2026-08-19 (`CD-PL-F56`): a commit made that way came out authored
`Matt Scott <rogue@cerberus.local>` and committed `NoustAI-PDA <pda@noustai.com>` — neither of which
is in `/root/.gitconfig`'s `user.*`, so the agent harness injects `GIT_*` identity variables into
the environment, and environment variables beat `-c` config. Nothing warns. The commit simply
carries a human's name.

Also note `git commit --amend` **preserves the original author** even with the environment set;
repairing an already-made commit needs `--author=` as well.

**Verify, do not assume.** After every commit: `git log -1 --format='%an <%ae> | %cn <%ce>'`. A
control whose failure mode is silent is not a control until something looks.


**Why the human's name is removed from the committer field too, not just the author field:** the
harness identity that previously held `committer` (`NoustAI-PDA`) is not a governed actor on this
project — it has no authority record, no dispatch and no role contract. Leaving it in the record
implies an actor that governance cannot account for. The harness is the *mechanism*; the seat is the
*actor*, and the record names actors.

**How it is enforced:** each seat sets `GIT_AUTHOR_*`/`GIT_COMMITTER_*` for its own commits, and the
Project Lead runs a **git log author audit** at every boundary — every commit on the lane must
resolve to a seat identity from the table above, and none to a human. An audit that finds a human
identity is a boundary failure, not a cosmetic one.

## CD-RULE-003 — a seat derives a product quantity or fails closed; it never invents one

**Source:** PROJECT LEAD, from `PBG-AUTH-005` and the precedent already set in
`src/crash_detector/dials/scores.py` (the refusal to impose a score range).
**Status:** ACTIVE.

Where a structural bound requires a **number that carries product meaning** — a range, a ceiling, a
window, a threshold, a weight — the implementing seat must either:

1. **derive** it from already-recorded product intent (PID, BLUEPRINT, a ruled decision), citing the
   clause it derives from; or
2. **fail closed** — refuse to operate without the value, and raise it as an owed Product Authority
   decision.

It must **not** choose a plausible number. An invented bound that later proves wrong rejects
legitimate readings quietly, from inside a constructor, and is worse than no bound.

**Fail closed means fail closed:** absent the value, the code refuses rather than defaults, and the
guard reports `PRECONDITION_NOT_MET` rather than passing.

## CD-RULE-004 — a guard closes its class or DECLARES ITS OWN LIMIT

**Source:** PROJECT LEAD, generalising `CD-D-014`/`CD-D-015` (which required exactly this of
`CD-RT-012-NO-EXECUTION-INTERFACE`) and the assurance caveat that its honesty "should not be
generalised".
**Status:** ACTIVE.

Every guard in `tools/register/` and every declared test in `required-tests.yaml` must, for the
proposition it defends, do **one** of these and say which:

1. **CLOSE THE CLASS** — no route to the violation exists that the guard does not stop, and the
   claim is proved by execution against adversarial variants, not by the guard exiting non-zero on
   one chosen instance; or
2. **DECLARE ITS OWN LIMIT** — a written, enumerated, *measured* boundary in the check header, the
   register entry and the execution contract, **consistently in all three**, each boundary carrying
   a concrete example an auditor can execute, plus an instruction not to read a clean run as proof
   of the proposition.

**What is prohibited is the third thing:** a guard that catches a chosen instance while its register
entry claims the class. That is what produced four AMBER verdicts at the WO-2 gate.

A register entry may not claim more than its guard delivers. Where a criterion rests on several
layers, the entry may not claim that a violation slipping past one layer must fail the others unless
that has been **proved by execution** for the class, not asserted from design intent.

## CD-RULE-005 — every governed timestamp comes from `date -u`

**Source:** PROJECT LEAD, `CD-PL-F55`, `BL-20260819T105500Z-0024`. Effective 2026-08-19.
**Status:** ACTIVE.

Every `entry_id` and every `timestamp_utc` in `governance/` is taken from `date -u +%FT%TZ` and from
nothing else. Not from the wall clock, not from a shell prompt, not from a file mtime, not from
memory of what the time was earlier in the session.

**Why:** the lane's increment-2 entry is `BL-20260819T113000Z-0041`, written by a commit dated
`11:41:56 +0100` — 10:41:56 UTC. The `Z` was British Summer Time wearing a UTC label, so the entry
claimed a moment that had not yet happened, and a later entry stamped from true UTC sorts *before*
it. A build log whose ordering is wrong is a build log that cannot reconstruct a sequence of events,
which is the only thing it is for.

**Neither entry is edited.** Corrections supersede, never edit (`PBG-CONT-003`, non-waivable). The
existing ids stand as written and this rule binds forward. Within each block the **sequence number**
remains the reliable ordering: main from `0023`, the lane from `0040` (`CD-D-036`).

## CD-RULE-006 — a residue declaration must name a layer that has been MEASURED to hold it

**Source:** PROJECT LEAD, `CD-PL-F54`, `BL-20260819T105500Z-0024`. Effective 2026-08-19.
**Status:** ACTIVE.

Where a guard declares a limit under `CD-RULE-004` option 2 and says another layer carries the
residue — "THE TYPE LAYER CARRIES THIS", "THE PUBLICATION BOUNDARY CARRIES THIS" — that sentence is
**a claim requiring its own executed evidence**, recorded with the boundary. The variant must be run
and the other layer's refusal observed.

**Why:** boundary 6 of `check_no_blend.py` stated that the publication boundary refuses a blended
number. Measured, it does not: re-wrapping the blend as a magnitude of one dial gives it a
provenance the gate accepts, and `number_for_dial_slot` returned it. Two declarations each assumed
the other was covering the route, and the route was open. A declaration that misdirects an auditor
to a layer that does not hold is worse than no declaration, because it spends the auditor's attention
somewhere the defect is not.

An unproved hand-off is written as **"NOT PROVED TO BE CARRIED ANYWHERE"**, which is honest and
leaves the residue visible.

## CD-RULE-007 — a continuity write is not complete until `pbg boot` has read it back

**Source:** PROJECT LEAD, `CD-PL-F64`, `BL-20260819T160900Z-0029`. Effective 2026-08-19.
**Status:** ACTIVE.

Any commit that changes `governance/engineering/ACTIVE_WORK.yaml` must re-run

```bash
PYTHONPATH=pbg/tools python3 -B -m pbg.cli boot
```

after the edit and **record the verdict in the Build Log entry for that same boundary**. A follow-up
commit that resolves `continuity_record_commit` from `PENDING` may write **that field and nothing
else**.

**Why:** `ACTIVE_WORK.yaml` was semantically invalid — and `pbg boot` RED with
`CONTINUITY_SEMANTIC_INVALID/RESUME_BLOCKED` — from `30f5c87` through `f7a49e5`, across two whole
increments. `last_completed_checkpoint_sha` and `continuity_record_commit` both read `8ca0eed`, an
equality the schema forbids in terms because the first field "is the last SOURCE checkpoint, NEVER
the commit containing this file, which would be circular". It was introduced by a commit whose
stated purpose was to *repair* the `CD-PL-F36` class in that same field: it correctly resolved
`PENDING`, and in the same two-line diff overwrote the other field with the same value.

Two reconciliations were written on top of a record the framework was already refusing, and neither
noticed, because both edited the file **by hand**. The framework's own writer
(`continuity.checkpoint`) validates, writes a `.tmp`, reads it **back**, validates again, and
refuses the whole update if any stage fails — nothing becomes canonical until it has been read back.
Every hand edit forfeits that guarantee. This rule restores it with one command.

**It closes a class, not an instance.** Banning this field pair would stop one spelling of one
defect; re-running the validator catches any schema or semantic defect the record can carry,
including ones nobody has thought of. The shared door is the read-back, and this is the door.

**It is checkable from the Build Log alone:** an entry that changes a continuity record and records
no boot verdict is a breach visible on its face.

## CD-RULE-008 — the `CD-RULE-007` boot re-run is taken on the COMMITTED tree, not the working tree

**Source:** PROJECT LEAD, `CD-PL-F69` and `CD-PL-F70`, `BL-20260819T185403Z-0037`. Effective 2026-08-19.
**Status:** ACTIVE.

The `pbg boot` re-run that `CD-RULE-007` requires is performed on a **pristine clone at the
committed SHA**, and **that** is the verdict recorded:

```bash
git clone -q --no-hardlinks /srv/crash-detector /tmp/<probe> && cd /tmp/<probe>
PYTHONPATH=pbg/tools python3 -B -m pbg.cli boot
```

A working-tree boot may be run as well. It is not the verdict of record.

**Why — it closes two defects that are the same defect from opposite sides.**

`CD-PL-F69`: `44a56ec` advanced `last_build_log_entry` to an entry it did not commit. Measured on a
clone with one variable changed — entry absent → **RED**, `CONTINUITY_REFERENCE_INVALID/RESUME_BLOCKED`;
the same clone with the file restored → **AMBER**, `CONTINUITY_MATCH`. The committed record was RED
for every actor who cloned it, and the live worktree read fine **because the missing file was sitting
on disk beside it**. Boot's read-back was working. It was pointed at the wrong tree.

`CD-PL-F70`: at the identical SHA, a clean clone boots **GREEN** and the live worktree boots
**AMBER**. One empty untracked file (`touch`) flips GREEN → AMBER and removing it flips back.
`ROADMAP.md` is absent in *both* arms. So the standing explanation carried in this log for many
boundaries — "AMBER, the sole UNAVAILABLE being roadmap_identity" — names a cause that was never
measured. Not a false clean, because AMBER is stricter than the truth; the cost is **masking**, since
a genuine new degradation would arrive looking exactly like the standing one.

The working tree is not the record. A verdict taken from it is a verdict about something other than
what the project ships — too lenient about content, too harsh about state. Reading it off the
committed tree is right in both directions at once, and it enumerates nothing.

**It is checkable from the Build Log alone:** an entry recording a boot verdict must name the SHA the
verdict was taken at, and that SHA must be a commit. A verdict with no SHA, or one that is not the
boundary's own commit, is a breach visible on its face.

**Ordering.** The verdict of the commit carrying an entry cannot be inside that entry. This is the
same ordering problem `CD-RULE-007` already solved: the follow-up commit that resolves
`continuity_record_commit` from `PENDING` records the committed-tree verdict **in its commit
message**. `192fc50` is the worked precedent. No new mechanism.

---

## CD-RULE-009 — an integrity fingerprint records the exact command that produces it

**Source:** PRODUCT AUTHORITY, `PO-DECISIONS-0004.md` Ruling 5. Effective 2026-08-20.
**Status:** ACTIVE, non-relaxable by any seat.
**Transcribed:** 2026-08-22, at the boundary that marked `BP-AMENDMENT-0001` IN FORCE. The ruling
bound from the moment it was made; this file was the place it had not yet been written down, and a
procedural control that is not written down is not a control — which is this file's own first
sentence, applied to this file.

**The rule, in the Product Owner's own words:**

> An integrity fingerprint that does not record its producing command is not an integrity control.
> Every fingerprint records the exact command.

**What it binds, concretely.** Any seat — Project Lead, Engineer or Assurance — that writes a hash,
digest, tree fingerprint or checksum into a dispatch record, a Build Log entry, a verdict, a
manifest row or a commit message writes **beside it the exact command line that produces it**, in a
form a reader can paste. A fingerprint with no command is not evidence and must not be cited as one;
the honest alternative is to state no fingerprint at all.

**Why (`CD-PL-F78`, raised by the third Assurance seat against the Project Lead, and ADOPTED).** The
WO-2R2 assurance dispatch recorded a tree-fingerprint *value* but not the *command* that makes it,
and the auditor could not reproduce it in ten attempts. A number an auditor cannot recompute proves
nothing about the tree it names — it proves only that somebody once computed something.
**Aggravated:** `CD-ASR-WO2-02` had raised the same defect earlier and it was not acted on.

**How it is enforced.** At every reconciliation the Project Lead checks each fingerprint in the
record under review for its paired command, and treats an unpaired one as a finding rather than as
evidence. Every dispatch this rule post-dates carries it in its own prohibitions, so the obligation
reaches the seat and not only the reviewer.
