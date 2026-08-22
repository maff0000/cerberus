# PO decisions — §D.3 wording corrected; increment 5 re-based from a list to the class; increment 4 dispatched
date: 2026-08-22 · authority: Product Owner (Trinity)

**1. CD-D-115: the §D.3 part 1 wording is CORRECTED, and the implementation stands.** The
operative requirement — *a caller supplies neither* — is met and measured. The wording said
"an engine-owned instant passed as a value" and was incomplete: a single instant cannot
measure an elapsed span, and the timeout refusal needs one. Corrected wording (appended to
BP-AMENDMENT-0001 as a dated correction, not a silent rewrite):

> `clock` becomes an engine-owned instant already established by `ensure_utc` and passed
> as a *value*; where an elapsed span is required, the engine derives it from its OWN
> module-internal monotonic source, which takes no parameter; `sleep` becomes a named
> member of a closed `DelayKind`. **No parameter exists through which a caller clock,
> caller sleep, or caller span can arrive** — that is the requirement; the instant-as-value
> and the internal span are its two instruments.

The seat went beyond the letter in the safe direction and disclosed it rather than reading
its resolution back into the specification. That is the behaviour this project rewards,
and the document in force now says what the code does.

**2. CD-D-114: increment 5's scope is RE-BASED — my own ruling contained a census, and the
census has already been beaten.** PO-DECISIONS-0007 ruling 1 named four types;
`AttemptRecord.__post_init__` is a fifth, found within hours. An enumeration cannot close
a property-defined class — this estate's most expensive lesson, and I applied it to the
kernel while writing a list into my own ruling. Corrected: increment 5's scope is THE
CLASS — every public type in the frozen subject on a judgement path whose field
establishment is body-borne — ENUMERATED BY AN INSTRUMENT at increment-5 start, with its
command and count recorded (CD-RULE-009). The four named types plus `AttemptRecord` are
the floor, not the population. The instrument's enumeration is itself offered to the
fourth Assurance seat to attack.

**3. CD-PL-F82 and CD-PL-F83 noted.** The 24-vs-27 undersell is corrected to the measured
number wherever it appears (documentary, the Project Lead's, folded into increment 4's
items). F83's third route through declared limit 6 strengthens the rewording obligation
already ruled at PO-DECISIONS-0007 ruling 4 — the limit's wording must cover its measured
reach, all three routes.

**4. CD-D-113 through CD-D-117 stand as ruled.** In particular CD-D-116: correctly not
closed — a collection result is not a judgement value, and asserting otherwise to buy
redundancy would be a false statement in a control. CD-ENG-WO2R3-F10 remains owed on the
record.

**5. Increment 4 is DISPATCHED at lane `04cdd34`:** the remaining plants under CD-D-033,
the six documentary items, and — largest — re-measuring that the eight applying plants
still contrast at the current lane head. Then increment 5 under ruling 2's re-based scope,
then the FOURTH fresh Assurance seat over the whole.

**6. Reaffirmed:** CD-AC-002 and CD-AC-005 remain ungraded; reconciliation is not
acceptance, acceptance is not assurance.
