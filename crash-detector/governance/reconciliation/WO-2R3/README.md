# WO-2R3 — Project Lead reconciliation probes

**NOTHING IN THIS DIRECTORY IS EXECUTABLE, AND NOTHING IN IT IS ASSURANCE.** These are the probes
the Project Lead ran to reconcile a seat return — its own drivers, on its own pristine
`git archive` extractions, outside every governed worktree. They are stored as `.txt` so that they
are DATA (`PBG-ASSURE-001`). Reconciliation is not certification (`PBG-SOD-001`, non-waivable).

They are recorded for the same reason the WO-2R and WO-2R2 probes were (CD-D-047): a probe that
exists only in a seat's conversation is not project state (`PBG-CONT-007`), and the next Assurance
seat needs the exclusion set in full so that it can devise routes nobody here has tried. **From the
moment they are written down they prove nothing about any class** — they are a regression floor and
an exclusion list, and fitting a guard to them is worthless.

## Increment 4 — the fourth route through DECLARED LIMIT 6

Increment 4 reworded DECLARED LIMIT 6 to cover three measured routes and added, in the mechanism's
own words: *"anyone reading this should assume there is a fourth and should look for it rather than
check this list."* The Project Lead read that sentence and looked. **There is a fourth.**

| probe | what it attacks | measured at 4ac159e |
|---|---|---|
| PL-AA0 | first attempt — compare the door's declaration object against the type by identity | **INCONCLUSIVE, and recorded because it is the trap.** The declaration is a `_Exactly` wrapper, not the type; comparing it to a type returns False in BOTH arms and looks like a refusal. A probe that reads a refusal off the wrong object proves nothing. |
| PL-AA1 | **substitute the module a door's declared type is imported FROM, before the package is imported** — `sys.modules["datetime"] = <forgery>`, ONE line, run OUTSIDE the package | **THE DOOR INVERTS.** CONTROL: genuine `datetime` ADMITTED, forgery REFUSED. POISONED: **genuine REFUSED, forgery ADMITTED.** `collect.__admits__["started_utc"].describe()` reads `datetime` in the control arm and `ForgedDatetime` in the poisoned one. |

**WHY IT IS A FOURTH ROUTE AND NOT A RESTATEMENT OF (c).** Route (c) — `CD-PL-F83` — rebinds a name
*inside* the package after import. This one never touches the package at all. `admits` compiles its
declaration against whatever object the name is bound to AT DECORATION TIME, and decoration happens
at import; so control of module resolution BEFORE import is sufficient, and control of code inside
the package is not required. The limit's own framing — *"anything that can execute code inside this
package can reach them"* — states an entry condition **stricter than the one this route meets**.
That is the fifth instance of this project's recurring documentary defect: **a declaration narrower
than its measured reach.** Raised as `CD-PL-F84`, LOW.

**ONE HONEST DIFFERENCE, IN THE MECHANISM'S FAVOUR, AND IT IS RECORDED BECAUSE IT CUTS THE OTHER
WAY.** Route (a2) leaves the introspection surface LYING — `declared_admissions` still reports the
original declaration (`CD-ENG-WO2R3-F13`). This route does NOT: `describe()` truthfully reports
`ForgedDatetime`. A reviewer who asks this door what it requires is told the truth. The seat's own
disclosure about (a2) is therefore not a general property of the mechanism, and the limit should not
be reworded as though it were.

**WHAT THIS PROBE DOES NOT SHOW.** It does not defeat BP-AMENDMENT-0001 §D.3 part 1's claim, which
is about what a CALLER of `collect` can supply; a caller cannot reach `sys.modules` through a
parameter, and the interpreter still refuses `clock` and `sleep`. It is not a gate finding, it
breaks no criterion, and **the remedy is a REWORDING AND NOT A GUARD** (CD-D-080) — pre-import
module substitution defeats every in-process guard ever written, in this codebase or any other, and
a guard against it would be theatre. What is owed is that the limit stop implying a stricter entry
condition than it has.

Full account, with the numbers and the disposition: `governance/engineering/build-log/`
`BL-20260822T174206Z-0057.yaml`.

## The record act (boundary 0117) — the THREE `establishment` sites nobody had read

The fifteen dispositions needed a disposition for three tier-1 sites in
`crash_detector.establishment` that **no seat has ever read one at a time**. The fifth seat's T8
read the ten in `crash_detector.admission`; the four were carried as "reported and not chased"
through three gates. The SIXTH Assurance seat listed the governing question in its own §4 —
*"whether the C1-C6 hostile declaration forms are reachable through
`crash_detector.establishment.establishes(...)` from a caller"* — as something **IT COULD NOT
ESTABLISH**.

The Project Lead would not hand a dispatched Engineer an invented disposition for three sites
nobody had measured, so it measured them. `PL-AB0`, run on a pristine `git archive af2accb`
extraction at `/tmp/cd-pl-probe/tree`, outside every governed worktree, tree line printed on every
arm (CD-PL-F98).

| arm | what it attacks | measured at `af2accb` |
|---|---|---|
| 1 | is `establishes` reachable from ordinary in-process caller code? | **YES.** It is PUBLIC and in `__all__`. Caller-authored class decorated and constructed successfully — so `cls` at BOTH `_declared_field_list` duck sites is a **CALLER-SUPPLIED** operand. **The sixth seat's §4 item 3 is answered, and it answers against the tree.** |
| 2 | the `getattr(cls, '__dataclass_fields__', {})` site, on a hostile `cls` | **THE GATE ADMITS A NON-DATACLASS.** `dataclasses.is_dataclass` is itself a `hasattr` probe. A plain class carrying `__dataclass_fields__ = {}` passes it, and `establishes()(Hostile)` **SUCCEEDS** where the shipped docstring says it `:raises EstablishmentFault:` *"if the subject is not a dataclass … must stop the module importing"*. |
| 3 | the `getattr(field._field_type, 'name', '')` site | **STEERABLE.** A forged `_field_type.name` of `"_FIELD_INITVAR"` drives the InitVar refusal from caller-written data. |
| 4 | is `self` at `getattr(self, name, _ABSENT)` caller-controlled? | **YES.** `crash_detector.observations.OK` — a live governed type — **SUBCLASSES SUCCESSFULLY**, so the instance the site probes can be a caller's. |
| 5 | **the consequence arm** | **A CALLER MINTS A FORGED GOVERNED TYPE.** `is_establishing_type(Hostile)` → **True**; `establishment_faults(Hostile)` → **`()`**, zero faults; `establishment_field_list(Hostile)` → `()`; and **`Hostile` ENTERS `governed_types()`**, which grew **0 → 1**. |

**WHY IT IS THE SAME FACT AS `F-06-R`, NOT A NEW ONE — AND WHY THAT MAKES IT WORSE.** The sixth
seat's sentence was *"the mechanism applies its doctrine to values and violates it one level up, at
the layer that decides what 'established' means."* It wrote that about `crash_detector.admission`.
**It is true of `crash_detector.establishment` as well, through a different probe, in a public
exported entry point, and no document said so.** This is `CD-PL-F104`.

**WHAT THIS PROBE IS NOT.** It is not assurance (`PBG-SOD-001`), not a design, and not a fix. It is
handed to the dispatched Engineer as **EVIDENCE, which that seat is required to re-measure and free
to contradict** — the precedent set for the fingerprint recipe at increment 7. The `governed_types()`
count of 0-before is measured under a **bare import of `establishment` alone**, not under a full
package import, and that limit is stated rather than left to be found.
