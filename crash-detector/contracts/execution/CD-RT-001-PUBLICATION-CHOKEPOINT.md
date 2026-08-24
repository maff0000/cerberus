# `CD-RT-001-PUBLICATION-CHOKEPOINT` — execution contract

**Criterion:** `CD-AC-001` — *"Missing **or stale** input never renders as calm."* · `PID §3.2`,
constitutional in the same words.
**Authority:** `PO-DECISIONS-0031` **ruling 1(ii)**, and `ruling 2` (`Q37`) for the row count.
**New at:** WO-3 increment `16F-CONTROL-ROW-STRENGTH`. **Seat:** `CD-ENG-WO3-14`, dispatch
`CD-D-184`.

> **(ii) No bypass PATH to publication exists.** The five-line early return is a code path that
> skips the gate. There is exactly ONE publication chokepoint and no route reaches publication
> without passing the freshness stage — enforced structurally, so an early return around it
> cannot exist (the *"no undecorated evaluator exists"* principle, applied to the publication
> path).

---

## The proposition

**Within this tree's `src/`, exactly one function executes a write against the `publication`
schema; it judges every declared surface through `refuse_unless_publishable`, unconditionally,
before it writes anything; no `except` handler on that path can swallow the refusal; the gate
reaches the freshness stage unconditionally with no `return` in front of it; and no path through
that stage reaches its end without first enumerating the calm-bearing nodes.**

## Why it is structural when its sibling is deliberately not

`CD-RT-001-STALE-DATA-NEVER-CALM` is BEHAVIOURAL on purpose, and its header says a structural
read is *"precisely what let this class of defect through repeatedly on this project"*. **THAT
REMAINS TRUE AND THAT ROW STAYS BEHAVIOURAL. THIS ROW IS NOT A LICENCE TO MAKE IT STRUCTURAL.**

This row's subject is different **in kind**. It is a claim about **which code routes exist**, and
**no behavioural probe can enumerate routes that nobody calls.** A second function that writes
`publication.public_envelope` without passing the gate is invisible to every probe that drives
the gate — because the probe drives the gate, and that is what makes the other route a bypass.

**MEASURED, AND IT IS THE WHOLE ARGUMENT FOR THE ROW.** Seven arms that defeat the publication
path leave the behavioural row at `PASS` and are all caught here:

| arm | what it does | behavioural row | this row |
|---|---|---|---|
| `C1` | a second function in `src/` writes a publication surface and judges nothing | `rc=0` | `FAIL — 1`, `CD-CHOKE-001` |
| `C2` | the private surface is no longer judged | `rc=0` | `FAIL — 1`, `CD-CHOKE-002` |
| `C3` | the gate calls moved inside an `if` | `rc=0` | `FAIL — 1`, `CD-CHOKE-002` |
| `C4` | an early `return` in `refuse_unless_publishable` in front of every stage | `rc=0` | `FAIL — 1`, `CD-CHOKE-004` |
| `C5` | the `except` handler swallows the refusal and falls through to the write | `rc=0` | `FAIL — 1`, `CD-CHOKE-003` |
| `C6` | **every publication write removed — THE VACUITY ARM** | `rc=0` | `FAIL — 2`, both `CD-CHOKE-000` |
| `C7`/`N1` | a `return` inside the stage keyed on a value outside the sibling row's vocabulary | `rc=0` | `FAIL — 1`, `CD-CHOKE-005` |

## Command

```
python3 -B tools/register/check_publication_chokepoint.py --root .
```

## Assertion codes

| code | what it asserts |
|---|---|
| `CD-CHOKE-000` | **the subject set is non-empty** — a publication write exists, something executes it, the gate exists, and the gate reaches a freshness stage |
| `CD-CHOKE-001` | exactly ONE function in `src/` executes a publication-surface write |
| `CD-CHOKE-002` | the chokepoint judges before it writes, once per declared surface, unconditionally |
| `CD-CHOKE-003` | no `except` handler on the judging path may swallow the refusal — each ends in a `raise` |
| `CD-CHOKE-004` | the gate reaches the freshness stage unconditionally, with no `return` before it |
| `CD-CHOKE-005` | no path through the stage reaches its end without first enumerating the calm-bearing nodes |

**The freshness stage is identified BY THE REFUSAL TOKEN'S VALUE**, read from the running
application and then matched to whichever module-level NAME carries it — so renaming the constant
does not blind this check and does not silently narrow it.

## Exit semantics

`0` clean · `1` violation · `2` usage · `3` **precondition not met, with the reason stated**.
**Never a pass and never a skip** (`PBG-CI-002`). A tree whose `src/` does not import, whose gate
cannot be found by name, or in which no module-level constant carries the freshness refusal token
exits `3` rather than measuring less while looking like a result.

## Declared limits — this row's own sequence, 1 to 7

**DECLARED LIMIT NUMBERS ARE PER REGISTER ROW, NOT PER FILE.** These seven are
`CD-RT-001-PUBLICATION-CHOKEPOINT`'s and they are said identically here, in the header of
`tools/register/check_publication_chokepoint.py` and in `required-tests.yaml` (`CD-RULE-004`,
three places). **Four rows on this criterion now carry a `DECLARED LIMIT 3`; quote the row id
with the number.**

1. **A PUBLICATION WRITE IS RECOGNISED AS AN SQL STATEMENT AGAINST THE `publication` SCHEMA, AND
   NOTHING ELSE** — a string containing `INSERT INTO publication.`, `UPDATE publication.` or
   `DELETE FROM publication.`, executed through a `.execute(...)` call. **A ROUTE THAT PUBLISHED
   BY WRITING A FILE, POSTING TO AN HTTP ENDPOINT, OR CALLING AN ORM THAT BUILDS ITS OWN SQL
   WOULD NOT BE SEEN BY THIS CHECK.** That is a real gap and it is stated rather than implied:
   today the application has no such route (MEASURED — `publication/publish.py` is the only
   writer and it executes literal SQL constants), and the day one is added this limit must be
   re-read before this row is quoted.

2. **IT IS A STRUCTURAL READ AND IT IS NAME-COUPLED IN TWO PLACES**, deliberately and with the
   same trade the behavioural sibling row's `DECLARED LIMIT 3` prices: the gate is found by the
   name `refuse_unless_publishable` (which is EXPORTED — it is in that module's `__all__`), and
   `EnvelopeSurface` is imported to count the surfaces. **RENAMING EITHER MAKES THIS CHECK EXIT
   `3`, DELIBERATELY** — a check that cannot find its authentic target must fail and never wave
   through (`PBG-CI-002`). The freshness stage is NOT name-coupled: it is found by the refusal
   token's VALUE. EXECUTABLE: rename `refuse_unless_publishable` in
   `src/crash_detector/publication/envelope_contract.py` and run the command — exit `3` with the
   reason, never `0`.

3. **"UNCONDITIONAL" IS A LEXICAL PROPERTY, NOT A DATA-FLOW ONE.** A call is unconditional here
   when no `if`, `for`, `while`, conditional expression or boolean short-circuit stands between
   it and its function's body. **THIS IS A SOUND UNDER-APPROXIMATION IN THE DIRECTION THAT
   MATTERS** — it can only ever call a real gate call conditional and go RED, never call a
   conditional one unconditional and go green — but it means a legitimate refactor that puts the
   gate call inside a loop over surfaces **WOULD FAIL THIS ROW** and would need this limit
   re-read and this check deliberately rewritten. That cost is accepted: the alternative is a
   control that an `if not skip_validation:` defeats. EXECUTABLE: arm `C3`.

4. **IT PROVES NOTHING ABOUT WHAT THE GATE DECIDES.** That is the behavioural sibling row
   `CD-RT-001-STALE-DATA-NEVER-CALM`, and this row would be perfectly satisfied by a chokepoint
   that calls a freshness stage whose body is `pass`. MEASURED: arm `N11`, which widens the
   window comparison by a factor of 10^9 so every stale calm dial is admitted, leaves THIS row at
   `PASS` and is caught by the sibling row. **THE TWO ROWS ARE A PAIR AND NEITHER IS A SOLE
   GUARD. QUOTING THIS ONE ALONE IS HALF A REPORT.**

5. **THE STAGE'S SHAPE IS ASSERTED, NOT ITS SEMANTICS.** `CD-CHOKE-005` requires the first
   statement to enumerate through the shared document walk and every early exit to be guarded by
   that enumeration being empty. A stage that did that and then judged wrongly is this row's
   blind spot and the sibling row's subject. MEASURED: arms `N9` (the shared walk no longer
   descends into arrays) and `N13` (the enumeration emptied after the fact by an ordinary
   assignment) both leave THIS row at `PASS` and are caught by the sibling row.

6. **IT READS THE TREE UNDER `--root` AND ONLY `src/`.** A publication route in `tools/`, in
   `tests/`, or in a script outside this repository is outside this check. `tests/` is excluded
   deliberately: a test that writes a publication row through a recording double is not a
   production route, and including it would make this row RED for the wrong reason.

7. **IT IS A CLAIM AT A COMMIT, LIKE EVERY STRUCTURAL CLAIM.** `DECLARED LIMIT 6` of the sibling
   row said the only callers of the gate were `publication/publish.py` lines 276-277 **as a
   measurement at a commit, which is a sentence that goes stale silently.** THIS ROW IS THAT
   SENTENCE TURNED INTO A CONTROL, so it cannot go stale without going RED — but the control
   itself is only as current as the last time the register ran.

## Negative control

**A route that reaches a publication surface without passing the freshness stage, or a path
through the stage that reaches its end without judging a calm-bearing node.** The class includes,
and is not limited to — **AND EVERY NAMED MEMBER BELOW IS A MEASURED ARM WITH ITS rc AND ITS
VIOLATION COUNT, NOT A CLAIM:**

| member | arm | measured |
|---|---|---|
| a second function in `src/` executes a publication write and judges nothing | `C1` | `FAIL — 1 violation(s)`, exit `1`, `CD-CHOKE-001` |
| one of the two surfaces no longer judged before the write | `C2` | `FAIL — 1 violation(s)`, exit `1`, `CD-CHOKE-002` |
| the gate calls moved inside a conditional | `C3` | `FAIL — 1 violation(s)`, exit `1`, `CD-CHOKE-002` |
| an early `return` in the gate, in front of every stage | `C4` | `FAIL — 1 violation(s)`, exit `1`, `CD-CHOKE-004` |
| the refusal swallowed by an `except` handler that falls through | `C5` | `FAIL — 1 violation(s)`, exit `1`, `CD-CHOKE-003` |
| **every publication write removed — THE VACUITY ARM** | `C6` | `FAIL — 2 violation(s)`, exit `1`, both `CD-CHOKE-000` |
| the whole fourth refusal stage removed from the gate | `D1` | `FAIL — 1 violation(s)`, exit `1`, `CD-CHOKE-000` |
| a five-line early `return` at the top of the stage keyed on `inputs_used` cardinality | `W5G` | `FAIL — 1 violation(s)`, exit `1`, `CD-CHOKE-005` |
| a three-line early `return` at the top of the stage keyed on `regime == "calm"` | `W5B2` | `FAIL — 1 violation(s)`, exit `1`, `CD-CHOKE-005` |
| a `return` inside the stage AFTER the enumeration, keyed on a value outside the sibling row's vocabulary | `C7`/`N1` | `FAIL — 1 violation(s)`, exit `1`, `CD-CHOKE-005` |
| a `continue` inside the node loop keyed on the node's own `contributions` | `N2` | `FAIL — 1 violation(s)`, exit `1`, `CD-CHOKE-005` |
| a `continue` inside the node loop keyed on the node's own `state` | `N5` | `FAIL — 1 violation(s)`, exit `1`, `CD-CHOKE-005` |
| a `continue` inside the node loop keyed on a root value outside the sibling row's vocabulary | `N8` | `FAIL — 1 violation(s)`, exit `1`, `CD-CHOKE-005` |
| a `return` guarded by the enumeration's SIZE rather than its emptiness | `N7` | `FAIL — 1 violation(s)`, exit `1`, `CD-CHOKE-005` |
| the emptiness guard widened with `or <something else>` | `N12` | `FAIL — 1 violation(s)`, exit `1`, `CD-CHOKE-005` |

Each arm is run from **its own pristine `git archive <sha> | tar -x` extraction**, with the patch
read from an ABSOLUTE path outside every extraction and `git apply`'s rc **taken and checked** —
`CD-ASR-WO3-11` disclosed against itself that its runner read patches from inside the extraction,
got rc=128, and then measured an UNPATCHED tree while looking like a result. See
`plants/WO3-INC16F/MANIFEST.md`.

*** AND THE VACUOUS DIRECTION IS EQUALLY A VIOLATION OF THIS ROW, AND FOR A STRUCTURAL CONTROL IT
IS THE DIRECTION THAT GETS MISSED: A CONTROL THAT ASSERTS "EXACTLY ONE CALLER" IS SATISFIED BY A
TREE IN WHICH NOTHING CALLS ANYTHING. *** A tree with no publication write, no gate, or a gate
that reaches no freshness stage **FAILS THIS ROW** — it does not pass by having nothing to say.
MEASURED: arm `C6` gives `FAIL — 2 violation(s)`, both `CD-CHOKE-000`. **The Project Lead recorded
this as the NAMED RISK of ITEM 2 before this file was written.**

Detection is a **contrast**, and the validator computes it as one: the same declared command must
exit `0` on the clean subject and non-zero on the subject with the violation planted. A clean arm
that fails cannot be told apart from a broken harness, and a broken harness detects nothing — the
validator returns `UNDECIDABLE`, never `PASS`.

The negative control for this test is declared as run record **`RTR-WO3-0001`**. That record does
not exist yet. It is the run the **independent Assurance seat** will produce — a distinct actor
from the one that wrote this test. Until it exists the validator computes `UNDECIDABLE` for this
test and the gate stays shut, which is correct: this seat may declare which run must evidence its
guard, and may not supply it.

## For the auditor

Do not read a clean run of this check as proof that nothing stale can be published. It proves
that, **in this tree's `src/`**, exactly one function executes a publication-surface write; that
it judges both surfaces through the gate, unconditionally, before it writes anything; that no
`except` handler on that path can swallow a refusal; that the gate reaches a freshness stage with
no `return` in front of it; and that the stage cannot reach its end without first enumerating the
calm-bearing nodes. **It says nothing whatever about whether the stage's verdict is correct** —
that is `CD-RT-001-STALE-DATA-NEVER-CALM`, and `DECLARED LIMIT 4` says so with a measured arm
beside it.

## What this contract does not claim

It does not claim the test passes. It does not claim the criterion is satisfied. It does not admit
any evidence: `latest_admitted_run` is null in the register and this seat cannot fill it in,
because an implementation may not certify itself (`PBG-SOD-001`, non-waivable).
