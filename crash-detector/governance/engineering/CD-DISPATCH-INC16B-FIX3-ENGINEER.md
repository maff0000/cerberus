# CD-DISPATCH-INC16B-FIX3-ENGINEER

**role source:** `pbg/roles/engineer.md` — reading it does not grant the role (`PBG-BOOT-001`),
**this dispatch does**.
**authority record:** `CD-ASR-WO3-07`'s `AMBER` at `b4a15d6` (`BL-20260824T124330Z-A307.yaml`,
branch `asr-wo3-07-verdict`), findings **F1** and **F2** · F1 reproduced by the Project Lead with
its control at `BL-20260824T125012Z-0168` · `PO-DECISIONS-0026` ruling 9
**seat identity:** `CD-ENG-WO3-08` — **FRESH.** **Never `CD-ENG-WO3-07` (which built what you are
repairing)**, **never `CD-ASR-WO3-07` (which found F1 and F2 — `PBG-SOD-004`)**, never
`CD-ENG-WO3-01`…`-06`, never `CD-ASR-WO3-01`…`-06`.
**issued by:** `PROJECT_LEAD_SEAT_02` · **increment:** 16B-FIX-3 · **expected return:**
`READY_FOR_ASSURANCE`

---

## 0. THIS IS A NARROW INCREMENT WITH ONE ROOT CAUSE AND TWO SYMPTOMS

**Do not redesign anything.** Three audits have hardened this instrument and each closure held under
the next attack. **Two escapes remain and both are one-line class errors that the auditor has
already prescribed.** Your whole job is to write those two lines, prove they bite, and prove you
broke nothing.

---

## 1. THE LANE

```
branch    wo-3
worktree  /srv/crash-detector-wo3
tip       ba4523e  (16B-FIX-2 — assured AMBER at b4a15d6, banked, NOT accepted; content tip e01b8f5)
base      be0b355  (FROZEN — READ-ONLY)
verdict   b4a15d6 on branch asr-wo3-07-verdict — BL-20260824T124330Z-A307.yaml
```

**READ `BL-20260824T124330Z-A307.yaml` IN FULL FIRST.** Both findings carry the arm, the command and
a prescription **left deliberately unwritten**.

**WRITABLE SCOPE:** `tools/register/check_missing_data_never_calm.py` ·
`contracts/execution/CD-RT-001-MISSING-DATA-NEVER-CALM.md` · `required-tests.yaml` (the `CD-AC-001`
block only) · `plants/WO3-INC16B/**` (**adding** arms; C1–C17 untouched) ·
`governance/engineering/build-log/**` for your own return.

**PROTECTED — ZERO PATHS, PROVED BY COMMAND:** `pbg/**` · `BLUEPRINT.md` · `PID.md` ·
`governance/decisions/**` · `governance/mapping/**` · **both envelope schemas** · `src/**` ·
`tests/**` · `deploy/**` · `db/**` · `tools/**` except your one file · `evidence/**` · everything at
`be0b355`.

---

## 2. FX9 — F1: `_deref` DISCARDS `$ref` SIBLINGS, AND THAT IS A SPEC ERROR, NOT A MISSED LOCATION

**Both contracts declare JSON Schema 2020-12, in which keywords SIBLING to `$ref` are applied.**
`_deref`'s while-loop replaces a node with its `$ref` target **and throws the siblings away at every
hop.** So `FX5`'s conditional-keyword guard — which tests the *resolved* branch — never sees an
`if`/`else` written on the `oneOf` **entry** instead of inside the branch definition. **It is the
exact class FX5 was built to catch, written one position over.**

**REPRODUCED BY THE PROJECT LEAD, WITH ITS CONTROL, ON ITS OWN PLANT:**

```
branch def widened; the narrowing written as a SIBLING of $ref on the oneOf entry:
   {"$ref": "#/$defs/dial_reading_unknown",
    "if": {"required": ["render_hint"]}, "then": true,
    "else": {"properties": {"detail_level": {"$ref": "#/$defs/absent_data_detail_level"}}}}

instrument                       PASS — 144 assertions, 0 violations
gate, PUBLIC,  with marker       *** ADMITTED — UNKNOWN dial rendering as CALM ***
gate, PRIVATE, with marker       *** ADMITTED ***
gate, both, CONTROL no marker    REFUSED [SCHEMA_VIOLATION] at /equity_crash
```

*** **AND THE AUDITOR MEASURED THE PART THAT MATTERS MOST: of all 30 `execute:` lines, EXACTLY ONE
MOVES — LINE 2, `tests/test_detail_level.py`. LINE 3, THE REGISTER-WIRED INSTRUMENT, DOES NOT. And
within that file only the five LITERAL-SHAPE assertions fail; the BEHAVIOURAL arm PASSES. THAT IS
THE MEMORIAL STATE RULING 9 EXISTS TO END, REACHED FOR THE THIRD TIME.** ***

**And the auditor closed the obvious wrong fix in advance:** its arm `A2` puts the conditional one
`$ref` deeper behind an innocuous entry and gets the same result — **so inspecting only the `oneOf`
entry is NOT a sufficient fix.**

**BUILD:** make `_deref` **spec-correct** — a `$ref` with siblings is the target *merged with* those
siblings, at **every** hop — so the conditional keywords arrive at `FX5`'s existing guard wherever
they are written and it reports `CD-CALM-BRANCHES-006` as it already does. **A guard that only looks
in one place is the whack-a-mole game `PO-DECISIONS-0026` ruling 10 forbids; fix the resolver, not
the guard.** If full merge semantics are more than this row should absorb, **the deny-by-default
alternative is acceptable and you must say which you chose and why**: treat *any* `$ref` node
carrying siblings as UNBUILDABLE and report it.

---

## 3. FX10 — F2: THE `undecidable` LIMB IS UNREACHABLE FOR A NON-OBJECT `state`

`FX6` made `_dial_bearing` return `None` for an unclassifiable state vocabulary — **but the
`undecidable = True` limb sits inside `if isinstance(state, dict)`.** A `state` spelled as the
boolean schema `true` (legal in 2020-12) drops to `None`, the descent skips it, and the property is
classified **not a dial**. Auditor arm `D1`: instrument `PASS 144/0`, `feed_liveness` in **neither**
list, gate ADMITS `{state: STALE, detail_level: "calm"}` on both surfaces.

**`DECLARED LIMIT 12` does not cover this** — it covers *differently-named* keys, and `D1`'s dial
declares a key literally called `state`.

**BUILD (the auditor's prescription):** a root property that **declares** a `state` key must reach
the `undecidable` limb **whatever the shape of that key's subschema** — object, boolean, or
anything else. **Declaring `state` is the trigger; being an object is not a precondition.** That is
the Project Lead's FX6 ruling applied where it was meant to reach.

---

## 4. FX11 — TWO SENTENCES THAT ARE BIGGER THAN THE CODE

The auditor found the overshoot **honestly priced but imprecisely worded**: `D2`
(`run_provenance.pipeline.state`) and `D3` (`jurisdiction.state` — a US state code) **both turn the
constitutional instrument RED**, and the declared sentence *"nor on a legitimate optional root object
that is not a dial"* **presents one shape as a class.**

**The Project Lead's FX6 ruling STANDS — a false positive costs one seat one look; a false negative
costs the constitution.** **BUILD: correct the SENTENCE, not the behaviour**, by supersession, in
all three `CD-RULE-004` places, and **name `jurisdiction.state` as the worked example** — a reader
meeting a red instrument on a US state code should find it already measured.

---

## 5. YOUR CONTRAST SET

Added under `plants/WO3-INC16B/`, **C1–C17 untouched**, MANIFEST form with **`git apply`'s own exit
code as its own column**, **every arm from its own pristine extraction** (`CD-PL-F154`):

| # | Arm | Must |
|---|---|---|
| **C18** | conditional keywords sibling to `$ref` on the `oneOf` entry (auditor `A1`) | **FAIL** |
| **C19** | the same, one `$ref` deeper behind an innocuous entry (auditor `A2`) | **FAIL** |
| **C20** | `state` as the boolean schema `true` on a third root property (auditor `D1`) | **FAIL** |
| **C21** | *(CONTROL — MUST STILL PASS)* the symmetric fourth level, i.e. C10/C15 re-run | **PASS** |

**RE-RUN C1–C17 UNCHANGED.** `C10`/`C15` at `PASS — 158`, `C6` at `FAIL — 6`, `C11` at `FAIL — 32`,
`C14` at `FAIL — 2`, `C16` at `PASS — 144`, `C17` at `FAIL — 32` are the ones that would show a
regression first. **A fix that quietly stops an existing arm from biting is a regression.**

---

## 6. WHAT IS NOT IN THIS INCREMENT

**Do not implement 16C**, and do not add any root property, dial state or schema edit — the
contracts are protected and every plant lives in `/tmp`. Also out: `CD-PL-F180` / the contract-bytes
route and the instrument's **exit 3**, both settled by three auditors · `STALENESS_WINDOW_CEILING_SECONDS`
(16C) · the no-blend closure, host-coupling, version discrimination (16D) · registering any
indicator row (16E) · `pbg/`.

**`DECLARED LIMIT 12` (the differently-named discriminator) is NOT yours to close.** The auditor
judged it **honestly drawn** — a residue named accurately before an auditor found it — and it is a
condition on 16C's dispatch, not a defect here.

---

## 7. YOUR RETURN

**BOOT FIRST**; the inherited `RED` (`ACTIVE_WORK.yaml`, blob `ce0803c3`, six seats) is the frozen
base's — **diagnose, do not repair.**

Each item backed by a command whose output you paste:

1. **C18, C19, C20 each FAILING** with violation codes; **C21 PASSING**.
2. **C1–C17 re-run and unchanged**, with `C6`, `C10`, `C11`, `C14`, `C16`, `C17` called out.
3. Clean worktree exit **0**, with the assertion count and any change to it explained.
4. `pytest tests/ -q` — **no regression from 2007**; `tests/test_detail_level.py` still **52**.
5. Register: `MATCHES` · **18** · `GATE: SHUT` · `latest_admitted_run (null)`.
6. **Which `_deref` remedy you chose and why** — spec-correct merge, or deny-by-default.
7. The FX11 supersession in all three places, quoting what it said and what is true instead.
8. Scope proof by command over every protected path.
9. **ONE identity**, `git log --format='%an' ba4523e..HEAD | sort -u`.
10. **Your declared limits**, including any new one.
11. **Your findings against this dispatch.**

**Commit identity — `git -c user.name=` DOES NOT WORK on this host:**
```
GIT_AUTHOR_NAME=CD-ENG-WO3-08 GIT_AUTHOR_EMAIL=cd-eng-wo3-08@seats.crash-detector.invalid \
GIT_COMMITTER_NAME=CD-ENG-WO3-08 GIT_COMMITTER_EMAIL=cd-eng-wo3-08@seats.crash-detector.invalid \
git commit -m "..."
```

**COMMIT AT EVERY BOUNDARY** (`PBG-CONT-007`). **YOU DO NOT CERTIFY YOUR OWN WORK.**

**STOP AND RETURN if:** a fix needs a file outside §1 · the spec-correct `_deref` turns the clean
tree or any existing arm red · FX10's trigger fires on something legitimate in the clean tree ·
**or you find any statement in this dispatch to be false.** *** **SEVEN CONSECUTIVE DISPATCHES ON
THIS LANE HAVE CONTAINED A FALSE STATEMENT A SEAT CAUGHT, INCLUDING TWO IN THE LAST ONE. ASSUME THIS
ONE DOES TOO. If the falsehood does not touch what you must build, you may continue and say so —
that judgement was confirmed at `CD-PL-F192` and is precedent.** ***
