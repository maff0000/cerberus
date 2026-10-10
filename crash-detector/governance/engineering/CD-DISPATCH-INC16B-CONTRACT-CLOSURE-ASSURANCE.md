# CD-DISPATCH-INC16B-CONTRACT-CLOSURE-ASSURANCE

**role source:** `pbg/roles/assurance-engineer.md` — reading it does not grant the role
(`PBG-BOOT-001`), **this dispatch does**.
**authority record:** **`PO-DECISIONS-0028`** (committed `fd51710`) rulings 1–4 ·
**`PO-DECISIONS-0027` ruling 5 — THE COMPLETION TEST, WHICH STANDS** · `PO-DECISIONS-0026` ruling 10
· `CD-ENG-WO3-11`'s return `BL-20260824T170252Z-16CC` at `295bdbe`
**seat identity:** `CD-ASR-WO3-11` — **FRESH.** **Never `CD-ENG-WO3-11` (which built the target —
`PBG-SOD-001`, non-waivable)**, never `CD-ASR-WO3-01`…`-10`, never any `CD-ENG-WO3-*`.
**issued by:** `PROJECT_LEAD_SEAT_04` · **increment:** 16B-CONTRACT-CLOSURE ·
**expected return:** `PASS` / `AMBER` / `RED` **with the next safe gate named**

---

## 0. WHAT YOU ARE GRADING, AND WHAT YOU ARE EXPLICITLY NOT

**`PO-DECISIONS-0027` RULING 5 ABOLISHED THE SHAPE CENSUS AND `PO-DECISIONS-0028` KEPT IT
ABOLISHED.** You are **not** graded on, and must **not** produce, a tenth named escape as your
headline. Nine audits did that; the tenth broke the pattern by indicting the completion test itself,
and the Product Owner ruled that the right answer.

**THE COMPLETION CONDITION, VERBATIM, AS IT NOW READS OVER A CLOSED CONTRACT:**

> *** **A DIAL THAT CANNOT PROVE PRESENT-AND-FRESH IS REFUSED BY CONSTRUCTION. A DIAL IN A
> NEVER-BEFORE-NAMED STATE, CARRYING `calm`, IS REFUSED.** ***

`PO-DECISIONS-0028` ruling 2: what changed is **HOW** it is achieved — *"not by a recogniser
searching an open space, but by a CLOSED CONTRACT that makes the space finite and the proof
mandatory."*

**SO GRADE THE CLOSURE ARGUMENT, NOT THE SHAPE COUNT.** The claim under test is a claim about
**exhaustiveness**: that every root property is forced into one of two limbs with no third case, and
that `calm` is unrepresentable on any branch that has not affirmatively proved present-and-fresh.
**An argument like that fails at its PREMISES, not at its examples.** If you find a named escape,
the interesting question is not the escape — it is **which premise it falsifies**.

**AND RULING 5'S OWN CLAUSE BINDS YOU BOTH WAYS:** *"If a further named escape is found after this
test is green, the test was wrong, not the guard incomplete."* **If the closure argument is sound
and you find an escape anyway, say so and indict the argument** — that is what your predecessor did
and it is why this increment exists.

---

## 1. THE TARGET

```
branch    wo-3
worktree  /srv/crash-detector-wo3   (DO NOT MUTATE — extract your own tree, see §2)
target    295bdbe   (entry commit; CONTENT TIP be088c5)
base      8398741   (16B-FIX-5, assured RED at d682ea2 — the BEFORE tip for every comparison)
frozen    be0b355   (READ-ONLY — verify unmoved and do not touch)
return    governance/engineering/build-log/BL-20260824T170252Z-16CC.yaml  — READ IT IN FULL
ruling    governance/decisions/PO-DECISIONS-0028.md at fd51710 on main   — READ IT IN FULL
verdict   d682ea2 on branch asr-wo3-10-verdict (your predecessor's RED)  — READ IT IN FULL
PL record governance/engineering/build-log/BL-20260824T163112Z-0175.yaml — READ IT IN FULL
```

**MUTATION IS PROHIBITED** except safe diagnostic artefacts in a scratch directory you create.
**You write NO line of product code, NO fix, NO patch to the instrument.** If you find the repair,
**write the prescription and leave the line unwritten** (`PBG-SOD-001`). Your predecessors did
exactly this and were graded better for it.

---

## 2. VERIFY THROUGH YOUR OWN TREE, NOT THROUGH THE PROJECT'S

`git archive <sha> | tar -x -C <tmpdir>` and work there. **There is no run-everything harness in
this repository and you must not build one** — an auditor verifying through a harness the project
wrote is verifying the harness (`PBG-ASSURE-001`).

---

## 3. WHAT THE PROJECT LEAD MEASURED ITSELF — RE-DERIVE IT, DO NOT TRUST IT

**`PROJECT_LEAD_SEAT_04` ran all of the following in its own shell before issuing this dispatch.**
They are recorded so you are not re-deriving blind — **and you must still re-derive them, because a
dispatch on this row has contained a falsehood twelve times running and two of those were this
seat's own.**

```
tip 295bdbe, worktree CLEAN            be0b355 UNMOVED (== wo-2r3)
PROTECTED PATHS ZERO                   git diff --stat 8398741..HEAD over pbg/ BLUEPRINT.md PID.md
                                       governance/decisions/ governance/mapping/ src/ tests/
                                       deploy/ db/ evidence/  ->  EMPTY
tools/ touched                         EXACTLY ONE FILE: tools/register/check_missing_data_never_calm.py
contract edits BOUNDED                 numstat 5/2 on EACH schema; the only non-description
                                       change is `"required": ["state"]`
CLEAN TREE                             PASS — 243 assertions, 0 violations, EXIT 0   (was 144)
pytest                                 2007 passed
CC-4 DEPTH TABLE                       depths 1,5,20,22,23,24 -> None (UNCHANGED)
                                       depths 25,26,30,40     -> None (WAS False — FIXED)
ALL 8 CC PATCHES                       git apply rc = 0 at both tips
FIVE ESCAPES, BOTH TIPS                CC-B, CC-C, CC-D, CC-G, CC-H:
                                       @8398741  PASS — 144, 0 violations   (THE ESCAPE)
                                       @295bdbe  FAIL — 2 or 4 violations   (CLOSED)
CC-A / CC-E                            ALREADY FAIL — 2 at 8398741; the return does NOT claim
                                       them as escapes and neither does this dispatch
CC-B WAS A *LIVE* ESCAPE               at 8398741 the live gate ADMITTED, on the public surface,
                                       {"status":"STALE","observed_utc":"2026-08-01T00:00:00Z",
                                        "detail_level":"calm"} — A DEAD FEED RENDERING CALM —
                                       while the instrument reported PASS — 144
DOCUMENT SET UNCHANGED                 the SAME 8 documents give BYTE-IDENTICAL outcomes at
                                       8398741 and at 295bdbe; §6's STOP condition correctly
                                       did not fire
ENTRY VALIDATES                        ok = True, stage complete, errors [] — by DIRECT call
F01 IS REAL                            C16 and C31, both labelled CONTROL, BOTH move
                                       PASS — 144  ->  FAIL — 2 on THIS row
```

### QUOTED, NOT ASSERTED — the PL did **not** run these

* `register 19 rc=0 / 11 non-zero unmoved` · `pbg verify MATCHES / (null) / (17) / GATE: SHUT / 18`.
* The **assertion accounting** `+99 = 27 + 36 + 6 + 30`.
* **`F01`'s sibling-row half**: that `C16` was *already* failing a **sibling register row** at both
  tips (so Rule CC merely makes two rows agree), while `C31`'s sibling row reads `PASS — 280` (so
  `C31` is a **genuine new false positive**). **THE PL VERIFIED ONLY THAT BOTH MOVE ON THIS ROW.
  THE SIBLING-ROW DISTINCTION — WHICH IS THE ENTIRE BASIS FOR TREATING THE TWO DIFFERENTLY — IS
  UNMEASURED BY THE PL. MEASURE IT.**
* The seven-step closure argument in `DECLARED LIMIT 17`, and the 34 limb-(b) live-gate drives.
* Findings `F02`, `F03`, `F04`, `F05` in detail.

---

## 4. ATTACK THE PREMISES. THIS IS THE WHOLE OF YOUR TECHNICAL BRIEF.

**RULE CC** (`_root_limb`, `CD-CALM-ROOT-008`) claims every root property is exactly one of:
**(a)** dict-equal to `{"$ref": "#/$defs/dial_reading"}`, or **(b)** a member of a 9-name frozenset
**and** proved by the live gate to refuse a calm-carrying object. Neither → **VIOLATION**.

Its exhaustiveness rests on **two premises the instrument asserts per surface**:
1. the envelope root declares `additionalProperties: false`;
2. the root declares no keyword outside `_ROOT_STRUCTURAL_KEYWORDS` (measured as
   `$schema $id $defs $comment $anchor $vocabulary title description type additionalProperties
   required properties`).

**GO AT THOSE.** Directions, offered as starting points and **not** as a checklist to complete —
your predecessors' best findings were all things nobody listed:

* **Can either premise be false while the instrument still passes?** That is the whole ballgame.
* **The canonical slot is decided by dict equality against a two-token literal — but what does
  `#/$defs/dial_reading` then RESOLVE TO?** A rotten definition behind a canonical-looking slot is
  the obvious next move. `CC-2`/`CC-3`/`CD-CALM-BRANCHES-006` are supposed to cover it. Do they?
* **`oneOf` spelled otherwise.** `_branch_states` reads `oneOf`. What does `anyOf`, `allOf`, or an
  `if/then/else` union do — refuse, or go quiet?
* **Limb (b) is proved with TWO probe shapes** (`CALM_BEARING_PROBES`, flat and nested). **The
  Engineer names this as its own closure boundary: a SAMPLE, NOT A CLASS.** Is a third shape
  admitted by an allowlisted property?
* **`$id` is on the structural allowlist** on a measured property of *these* contracts (both declare
  a non-dereferenceable `urn:`, every `$ref` is a local `#/` fragment). **That is a premise about the
  current text, not a law.** Break it.
* **`$defs` is structural** — so anything may be defined there. Is definition-without-reference
  genuinely inert?
* **The freshness assertion is by TYPE (`#/$defs/utc_timestamp`), not by name.** Can a branch
  satisfy it with a stamp that is required but meaningless?

**AND GRADE THE FALSE-POSITIVE COST HONESTLY, BECAUSE IT IS THE REAL PRICE OF THIS DESIGN.** `C16`
and `C31` both move `PASS -> FAIL`. The ruled direction is explicit — *"a false positive costs one
seat one look at one contract; a false negative costs the constitution"* — **but `C31` was the
control that proved a present-and-fresh dial is ADMITTED, and if it now fails for an unrelated
reason, the instrument may have lost the arm that stopped it being vacuous.** `CD-CALM-VACUITY-000`
exists precisely to catch "silence enforced" masquerading as "guarantee held". **Is this increment
strictly stronger, or has it traded a false negative for a blind spot?** Say which, and measure it.

---

## 5. ALSO REQUIRED OF YOU

* **Grade the Engineer's five self-raised findings.** `F05` claims **no engineer return on this lane
  has ever validated `ok=True`** and that this one does. Verify both halves.
* **`F02` is an honest disclosure of a harness bug** (`dial or unknown_dial()` — `{}` is falsy, so it
  reported ADMITTED about a document it never built). **Confirm the re-measurement was actually
  redone and that no surviving number rests on the broken harness.**
* **Validate the return entry yourself, by DIRECT call.** `pbg log validate` validates ZERO entries
  and prints GREEN — it is useless and using it is itself a finding. The working form:
  `continuity.validate(text, 'entry', Path('.'), schema_dir=Path('<repo>/pbg/schemas'))`.
* **Confirm ONE seat identity** on every commit in `8398741..295bdbe`, and **zero protected paths**.
* **Grade this dispatch.** Four of the last five audits raised findings against the dispatch that
  briefed them and every one was justified. **If §3 contains a falsehood, that is a finding and the
  PL wants it.**

---

## 6. YOUR RETURN

A build-log entry, banked on **your own branch** `asr-wo3-11-verdict`, `record_type` per your role
contract, **ONE seat identity**, validated `ok = True` by direct call **before** you commit, and
carrying: the verdict (`PASS`/`AMBER`/`RED`) · **the next safe gate, named** · every command with
its exit code · each finding with the tree that produces it and the arm that reproduces it · your
grade of the closure argument **and of its stated boundary** · your grade of the false-positive cost
· and your answer to the completion condition in §0, **in its own words rather than as a score**.

**`status:` must be a value the schema permits** — twelve exist and neither `READY_FOR_ASSURANCE`
nor `WAITING_ENGINEER` is among them (`CD-PL-F204`; the PL itself tripped the sibling version of
this at `CD-PL-F205` this session). Use `WAITING_PRODUCT_AUTHORITY` or `WAITING_PROJECT_LEAD`'s legal
equivalent and say the rest in prose.

Commit as `CD-ASR-WO3-11` using `GIT_AUTHOR_*`/`GIT_COMMITTER_*` environment variables —
`git -c user.name=` does **not** work on this host. Write commit messages to a file and use
`git commit -F`: unquoted heredocs and `-m` silently delete backticked words here.

---

## 7. WHAT A GREEN RELEASES — AND WHY YOU MUST NOT LET THAT WEIGH ON THE VERDICT

On `PASS`: 16C releases → the liveness/dead-feed detector → the 30 indicator rows that have been
blocked for three sessions. **THAT PRESSURE IS REAL AND IT IS EXACTLY WHY IT IS NAMED HERE RATHER
THAN LEFT TO PRESS SILENTLY.** Nine audits have refused to be hurried by it. **A `RED` that is right
is worth more to this project than a `PASS` that is early, and the Product Owner has said so twice
in writing.**

**Nothing downstream moves on your verdict alone**: the Project Lead banks it, and the Product
Authority disposes.
