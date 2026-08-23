# PO decisions — two meta-assurance REDs accepted; coordinated parallelism is built, not banned
date: 2026-08-23 · authority: Product Owner (Trinity)

**1. BOTH meta-assurance REDs are ACCEPTED.** Two fresh, independent seats on different
methods (IMP-033 diversity honoured) both graded the reconciliation practice RED: CD-PL-F134
(main moves under a live reader) RECURS; CD-PL-F132 (pointer-in-same-commit) failed at its
fifth application; and the concurrency incident of this afternoon disturbed the first pass's
own reading environment. The convergence of two independent methods is confirmation, not a
shared blind spot. The finding is UPHELD and it is against the OPERATING PRACTICE, mine
included — not against any seat's craft.

**2. THE CAUSE, NAMED AND OWNED: uncoordinated concurrency on the SAME scope.** I dispatched
PO-DECISIONS-0020 (wo2r3n) while PO-DECISIONS-0019 (wo2r3m) was still alive, BOTH pointed at
the WO-2R3 lane and the same increment stream. The record survived only because git's index
lock serialised the writes. My launch-lease lived in the driver and not in my own hand. This
is the PO's error, on the record.

**3. THE RULING — coordinated parallelism, per Matt's direction 2026-08-23:** *multiple PLs /
engineers on non-overlapping fixed tasks is fine, and great if it is faster — just no redoing
each other's work, and discipline that holds.* The invariant is therefore NOT one-writer-at-a-
time. It is: **no two live seats share a TASK or a WRITE SCOPE.** What is built next
(increment 12, the ONLY thing dispatched) is the COORDINATION DISCIPLINE that makes disjoint
parallelism safe and same-scope collision impossible:
- **(a) A WORK-CLAIM registry.** A task is atomically claimed before it is worked; a launch
  refuses to start on an already-claimed task. Two seats can never take the same work.
- **(b) DISJOINT WRITE SCOPES.** Each concurrent seat gets its own worktree/lane for code and
  its OWN record files — per-seat build-log id blocks (closing IMP-023), no shared
  ACTIVE_WORK.yaml edit, no shared sequence. Parallel writers never touch the same bytes.
- **(c) A MERGE / RECONCILIATION step** at the accountable seat that integrates disjoint
  results and asserts no two seats touched the same artefact.
- **(d) A LAUNCH LEASE binding BOTH writers** — the driver AND the PO's own hand — refusing a
  launch whose task or write scope overlaps a live session's; disjoint-scope launches proceed
  freely and in parallel.

**4. F134 and F132 get their REAL fix inside increment 12** — "a prediction is not a carrier"
(the meta-auditor's phrase): a fix that held N times then failed is structural-until-proven.
The claim registry and per-seat scopes remove the shared-file contention both findings live in.

**5. It is built ONCE and harvested to the framework.** This is IMP-013 + IMP-014 + IMP-023 +
IMP-037 converging; Rogue, Helm and Bagman get disciplined parallel seats by declaring it.

**6. Sequence:** increment 12 (coordination discipline) → the NINTH gate on the corrected
three-tier perimeter → parallel disjoint remediation where scopes allow, which is faster and
now safe. Standing: CD-AC-005 RED, CD-AC-002 AMBER, gate SHUT, system safe to leave running.
