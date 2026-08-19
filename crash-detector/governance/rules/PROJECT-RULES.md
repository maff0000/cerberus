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
