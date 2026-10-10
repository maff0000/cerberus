# PO decisions — the constitutional guard is made AFFIRMATIVE (structural), and liveness ships behind it
date: 2026-08-24 · authority: Product Owner (Trinity)

16B assured AMBER with a finding held to me: the "no calm over unknown" instrument
(CD-CALM-SLOTS-007) is a PATTERN RECOGNISER wearing deny-by-default's clothes — a dead feed
(`feed_liveness: STALE`) carrying `calm` is ADMITTED on both surfaces, because the guard
catches by STATE NAME, not structure. The only difference between a caught tree and an
uncaught one is whether a new dial reuses an old bad-state name. That is guard-the-instance-
not-the-class (ruling 10) reappearing in the constitutional guard itself, and it misses half
of CD-AC-001, whose actual words are "missing **OR STALE** input never renders as calm."

**1. THE CONSTITUTIONAL GUARD IS REBUILT AFFIRMATIVE, not by extending a denylist of bad
state names.** Calm / publishable detail is admitted ONLY when the dial AFFIRMATIVELY
presents data that is both PRESENT and FRESH — a positive precondition the tree must prove.
Everything else — missing, stale, unknown, and any future not-fresh state NOBODY HAS NAMED
YET — defaults to not-publishable-as-calm, regardless of the state's name. This is true
deny-by-default: prove "the data is good," not "the data is not on my list of bad." It is
ruling 10's structural principle applied to the constitution, and it closes CD-AC-001 in
full (missing AND stale, by construction).

**2. ORDERING — the dead-feed detector (`feed_liveness`) ships ONLY AFTER the guard catches
STALE-carrying-calm structurally.** The Project Lead was right to hold 16C: shipping the
liveness detector alongside the hole that hides its own STALE output, in one increment,
would ship a detector whose primary output the gate cannot see. The affirmative-guard fix
(ruling 1) lands FIRST as its own increment with the STALE-carrying-calm plant as its
contrast; the liveness feature follows only once that plant fails.

**3. THE MEMORIAL-IN-TESTS CONTRADICTION IS RESOLVED FOR THE STRUCTURAL INSTRUMENT.** The
guarantee's only surviving catcher on the conditional-branch tree is a pytest literal-name
`$ref` equality — the "memorial in tests" ruling 9 forbade — and it sits under a live
prescription to be REMOVED while another item says KEEP it as the carrier: two items on one
row pointing opposite ways. Resolved: the guarantee is carried ENTIRELY by the affirmative
structural register-wired instrument (ruling 1); the pytest literal-name assertion is
removed once that instrument carries the behaviour. Ruling 9 stands; the "keep it" item is
superseded, not both left live.

**4. Sequence:** 16C = the affirmative-guard rebuild (ruling 1) + the memorial removal
(ruling 3), plant-proved, fresh Assurance seat. THEN the liveness/dead-feed detector
increment (ruling 2). THEN register the indicator rows (the still-owed step). CD-D-181
sequential-only; frozen be0b355 untouched.

**5. STOP ITERATING SHAPES — the completion condition, because three fixes is a spiral.**
The guard has taken FIX, FIX-2, FIX-3, the auditor breaking it each time. That is the census
game on the constitutional guard, and closing a fourth named shape earns a fifth. The guard
is DONE only when it is AFFIRMATIVE AND PROVEN COMPLETE by ONE structural test, not a growing
list: **a dial in a NEVER-BEFORE-NAMED state, carrying `calm`, is REFUSED** — because calm
requires proven-fresh-and-present, and an unrecognised state cannot prove it. If that test
passes, no future shape can escape and the auditor's next attack is EXPECTED to fail by
construction. If a further named escape is found after this test is green, the test was wrong,
not the guard incomplete. No FIX-4 that adds a shape to a denylist is accepted; only the
affirmative rebuild with the unknown-state test closes this.

**6. THE APPROACH IS VALIDATED BY THE 16B-FIX-4 RED ITSELF.** The class inversion is real:
the falsifier passed, five rounds of spelling-patch escapes are closed, and the "whole
register green while a dead feed publishes as calm" hole is shut. The RED is narrow and
named — the class check QUANTIFIES OVER THE WRONG ALPHABET (it misses some keyword values).
That is a bounded correction to the affirmative guard's DOMAIN, not a return to spelling
patches, and the auditor measured the fix: read enum/const object values INTO the declared
set; do NOT move them out of `_INERT_KEYWORDS` (measured to explode the tail). The next
increment applies exactly that, then proves completeness with ruling 5's unknown-state test,
then releases 16C. No sixth spelling patch; the alphabet correction is the last structural
step.

**7. Standing:** two dials never blended; missing AND STALE never render calm (converging on
by-construction, alphabet-correction pending); weights provisional pending backtest; system
safe.
