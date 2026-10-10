# PROPOSAL — the eleven Class-2 dispositions, DRAFTED AND NOT WRITTEN

**status: DRAFT · awaiting PO ratification of the vocabulary (PO-DECISIONS-0013 ruling 3)**
prepared by: PROJECT_LEAD_SEAT_01 at BL-20260823T013001Z-0114 · authority: CD-D-130, CD-D-157

> **THIS FILE IS NOT THE REGISTER.** The register is
> `tools/sweep/declared_dispositions.py` on branch `wo-2r3`, and **NOT ONE OF THESE ELEVEN IS
> WRITTEN INTO IT.** This document exists so that the moment the Product Owner ratifies the
> vocabulary, the eleven land in one act and nothing waits on the Project Lead.
>
> **WHY IT IS A DRAFT AND NOT A DELIVERY:** PO-DECISIONS-0013 ruling 3 sequences
> *"the Project Lead drafts the extended vocabulary (register-contract change, **PO ratifies
> in-increment**); THEN the eleven are written."* The ratification has not happened, and the
> implementer has formally disagreed with one of the three drafted words. See CD-D-157.

## What the eleven are, and the decomposition they rest on

The Class-2 sweep exits 1 at `af2accb` with **534 sites, 15 violations** — PL-measured, unmoved by
increment 7, which is the correct result because nothing below has been written.

**15 = 13 UNDECLARED ADMISSION + 2 UNDECLARED MODULE.** Ten admission sites plus one module in
`crash_detector.admission` are **the eleven**. Three admission sites plus one module in
`crash_detector.establishment` are **the four**, which are not in scope here and are reported and
not chased — *whether that was the right call is the sixth Assurance seat's to judge.*

The substance below is **the fifth Assurance seat's T8 measurement**, the first and only time any
seat has read the ten sites one at a time. It is attributed to that seat, not claimed by this one.

---

## Category A — one site, and it is a real defect

### 1. `crash_detector.admission::_is_defined_in_a_class_body` — `DUCK: getattr(entry_point, '__qualname__', '')`

**proposed disposition: `DEFECT_OPEN`**

| field | value |
|---|---|
| finding | fifth Assurance seat, T8 Category A (`VERDICT-FIFTH-SEAT.md` §M6) |
| measured reach | one writable attribute, in-process, before decoration; bounded to parameters named in `_RECEIVER_NAMES` (`self`/`cls`) |
| counterfactual | without the assignment: `UndeclaredParameter: free_function2 is a FAULTED door and every call to it is refused` |

**The site falsifies its own shipped docstring**, which says the property *"is not something a
caller can influence"*. One string assignment — `free_function.__qualname__ = "Faked.free_function"`
— turns a FAULTED, always-refusing door into a silently-passing one that reports **no fault**, and
the first argument then arrives unestablished and undeclared.

**The bound is one identifier wide, not zero:** `assert_closed_presentation_surface(cls)` on the
serving path is a real module-level function with a parameter named `cls`.

**Rename test: it is a vocabulary guard on BOTH sides** — defeated by a name (`__qualname__`) and
triggered by a name (`cls`).

> **THIS DISPOSITION CLOSES NOTHING AND IS NOT AN EXEMPTION.** It records a live defect that is
> deliberately still live: **CD-D-153 prohibited increment 7 from fixing it**, because it is not in
> PO-DECISIONS-0013 ruling 6's enumeration and because cleaning it would pre-empt the sixth
> Assurance seat on the most interesting thing in its target. Its remediation is a separate ruling.

---

## Category B — three sites whose consequence is carrier credibility, not product judgement

**proposed disposition for all three: `CARRIER_ONLY`**

### 2. `admission_faults` · 3. `declared_admissions` · 4. `is_admitting_door`

| field | value |
|---|---|
| callers under `src/` | **NONE** — asserted by enumeration, not claimed |
| callers | `tests/test_admission.py`, `tests/test_judgement_path_doors.py`, `tests/test_collector_runner.py` |
| blast radius | a carrier believes a claim an object makes about itself |

**Measured by the fifth seat:** each believes any object carrying the attribute —
`is_admitting_door(Liar()) = True`, `declared_admissions(Liar()) = {'x': 'whatever'}`,
`admission_faults(Liar()) = ()`.

The honest disposition is *"reached only by carriers, and a carrier that asks an object about
itself is a carrier that can be told anything"* — already CD-ENG-WO2R3-F13's subject, arrived at
from the other side. **No pre-existing word said that**, which is why `CARRIER_ONLY` was drafted.

> **THE WORD MUST BREAK THE BUILD THE DAY SOMEBODY ADDS AN IMPORT UNDER `src/`.** The implementer
> confirmed this is machine-checked in both directions and called `CARRIER_ONLY` "the best of the
> three", holding that it does **not** collapse into `OUT_OF_BOUND` because *scope claims cannot be
> falsified and reachability claims can.*

---

## Category C — six sites consuming a declaration authored in source at decoration time

**proposed disposition: `OUT_OF_BOUND` for all six — no new word, and that is the point**

| # | site |
|---|---|
| 5 | `_EstablishedHere.__call__` — `isinstance(because, str)` |
| 6 | `_compile` — `_Admission` |
| 7 | `_compile` — `tuple` |
| 8 | `_compile` — `type` |
| 9 | `_type_tuple` — `isinstance(value, type)` |
| 10 | `each_of` — `isinstance(within, tuple)` |

Every one consumes a value a developer wrote inside `@admits(...)` **in the artefact**. The fifth
seat found no route to any of them that a caller controls. **Six of the eleven needed no vocabulary
extension at all** — recorded explicitly, because a vocabulary that grew to cover items the existing
words already fit would be scope creep wearing a taxonomy's clothes.

---

## The module entry — and the "should never have entered the closure" answer is *wrong*

### 11. `crash_detector.admission` — UNDECLARED MODULE, 33 tier-2 sites

**proposed disposition: `UPSTREAM_OF_THE_PATH` — AND THIS IS THE WORD UNDER DISPUTE**

| field | value |
|---|---|
| what it decides downstream | whether a judgement-path door establishes its arguments at all |
| the route | tier-1 admissions inside `admission` gate every `@admits` door on every judgement path |

**The most available disposition was *"it is the mechanism, not a judgement path; it entered the
closure only because judgement modules import it"* — and Category A refutes it.** A tier-1 admission
inside `admission` decides whether a door establishes at all. That is not adjacent to the deciding
path; it is **upstream of every point on it**. The fifth seat: *"`crash_detector.admission` belongs
in the closure, and the sweep denying by default was right, and the reason it was right is stronger
than any record has yet stated."*

> ### ⚠ THE IMPLEMENTER DISAGREES WITH THIS WORD AND THE PROJECT LEAD FINDS THE OBJECTION PERSUASIVE
>
> CD-ENG-WO2R3-03's return: `UPSTREAM_OF_THE_PATH` **binds the MODULE register, not the SITE
> register the other two words bind**, and **both of its fields are prose that cannot be made
> machine-checkable.**
>
> **BY THE PROJECT LEAD'S OWN STATED CONSTRAINT — "no new word may be a synonym for 'not looked
> at'", and the instrument must REJECT a disposition whose mandatory evidence fields are absent — a
> word whose evidence cannot be checked FAILS THE TEST ITS OWN AUTHOR WROTE.**
>
> **THE PROJECT LEAD DRAFTED IT AND NOW BELIEVES IT IS PROBABLY WRONG. IT DOES NOT WITHDRAW IT.**
> Ruling 3 gave the ratification to the Product Owner, and a seat that withdraws its own draft on an
> implementer's objection has quietly taken that ratification back. **THE SUBSTANCE — that this
> module belongs in the closure and must not be dispositioned away — IS NOT IN DOUBT AND IS NOT WHAT
> IS DISPUTED. WHAT IS DISPUTED IS WHETHER A WORD IS THE RIGHT INSTRUMENT FOR SAYING IT.**

---

## Tally, and the one thing this draft asserts about itself

| disposition | count |
|---|---|
| `DEFECT_OPEN` | 1 |
| `CARRIER_ONLY` | 3 |
| `OUT_OF_BOUND` | 6 |
| `UPSTREAM_OF_THE_PATH` *(disputed)* | 1 (the module) |
| **total** | **10 sites + 1 module = the eleven** |

**A SECOND OBJECTION THE IMPLEMENTER RAISED THAT IS BIGGER THAN ANY WORD:** `DEFECT_OPEN`'s
`finding` field is an **unchecked string, because this project has no findings register to resolve
against.** Its fields therefore *restate* a finding instead of *referencing* one — which is the
hand-maintained-summary defect reintroduced by the fix for it. **That gap is real, it is outside
this proposal's scope, and it is put up rather than left for an auditor to find.**

**WHAT THIS DRAFT DOES NOT CLAIM:** that these eleven are correct. They are the Project Lead's
reading of one auditor's measurement, and **the fifth seat's T8 is itself a first-and-only reading
that no second party has checked.** The sixth Assurance seat is being told, in its dispatch, that
the dispositions are a target and not a settled record — the fourth seat's own best result came from
disbelieving a disposition the record had already settled.
