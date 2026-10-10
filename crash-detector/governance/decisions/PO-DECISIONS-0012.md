# PO decisions — CD-D-146 ruled: `guarded` is a NET, not a DOOR
date: 2026-08-22 (ruled in fabric at the evening boundary, committed at this one) · authority: Product Owner (Trinity)

**1. `guarded` is NOT a §D.1 door — it is a POST-CONDITION CONTROL, a NET, and its
arity-openness is LOAD-BEARING.** CD-ASR-F03's own lesson: a fixed-arity wrapper stops
guarding the moment the evaluator grows an argument. Forcing `@admits` onto it would
convert the net into a door and lose the net. §D.1's class is PUBLIC entry points;
`guarded` is a function-local binding, never importable, reachable only through doors that
already establish. The static name-heuristic and runtime reachability disagreed about
whether it is public at all, and reachability is the truth.

**2. Two populations, both instrumented.** The doors instrument's membership clause is
corrected from NAME-PREFIX (a vocabulary — CD-PL-F74's own conviction) to REACHABILITY.
A second declared population is created: NETS — function-local post-condition guards on
judgement paths — enumerated and asserted exactly as doors are, each with its
post-condition named. "Not a door" must never again mean "not seen." Zero unclassified
interceptors on any judgement path.

**3. The RED doors row and the two failing tests are resolved BY THE RECLASSIFICATION** —
after the next assurance pass, never by exemption or weakening. The Engineer's refusal of
all three green-making routes was correct and is commended.

**4. This ruling is attackable, and the attack is assigned:** can anything in-process
reach `_evaluate_dial` without passing an established door, short of arbitrary code
execution (outside the settled threat model)? Does the net's post-condition bind
everything its open arity admits? If either lands, ruling 1 falls, `guarded` becomes a
door, and CD-ASR-F03 is redesigned.

*Recorded note:* the fifth seat's rename measurement (two lines, 1 violation → 0, runtime
identity unchanged) arrived after this ruling was written to fabric and independently
supports ruling 2's diagnosis — the check was name-driven. Its counter-reading is disposed
through ruling 4, made a REQUIRED measurement by PO-DECISIONS-0013.
