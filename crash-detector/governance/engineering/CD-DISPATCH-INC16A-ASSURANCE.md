# CD-DISPATCH-INC16A-ASSURANCE

**role source:** `pbg/roles/assurance-engineer.md` — read it; reading it does not grant the role
(`PBG-BOOT-001`), **this dispatch does**.
**authority record:** `PO-DECISIONS-0025` ruling 6 · `PBG-SOD-001` (non-waivable) · `CD-D-180`
**seat identity:** `CD-ASR-WO3-03` — **FRESH.** Never `CD-ENG-WO3-01`, `CD-ENG-WO3-02`,
**never `CD-ENG-WO3-03` (the seat that built this)**, never `CD-ASR-WO3-01`, never `CD-ASR-WO3-02`.
**issued by:** `PROJECT_LEAD_SEAT_02` · **expected return:** `PASS` / `AMBER` / `RED`, with the next
safe gate named.

---

## 1. THE TARGET

```
branch    wo-3
tip       53f639a91088ee42f5ba6c0d269f69782ba2a20a     <- YOUR TARGET, and nothing else
base      116c01f  (increment 15, assured AMBER, banked, not accepted)
frozen    be0b355  (wo-2r3 — must still be exactly this when you finish)
```

**MUTATION IS PROHIBITED** except explicitly safe diagnostic artefacts: scratch trees under `/tmp`,
extractions via `git archive`, and **your own verdict artefact**. `CD-PL-F163` was raised when a
previous dispatch ordered a seat to breach `PBG-CONT-007` by forbidding the very writes continuity
requires; **this dispatch grants you a NARROW WRITE SCOPE for your verdict artefact alone** —
`governance/engineering/build-log/` on your own branch or a diagnostic path you declare. **You touch
no source, no test, no contract, no schema, no deploy file and nothing under `pbg/`.**

**GET YOUR OWN TREE.** Do not audit in `/srv/crash-detector-wo3` — that is the Engineer's worktree.
Use `git worktree add` to a fresh path at `53f639a` in detached HEAD, or `git archive 53f639a | tar
-x` into `/tmp`. **If you extract rather than check out, EXTRACT THE WHOLE TREE** — `CD-PL` history
records a seat producing a DEAD PROBE with both arms reading zero because it worked from a partial
extraction and trusted the result.

---

## 2. WHAT WAS CLAIMED, AND WHAT THE PROJECT LEAD ALREADY RE-MEASURED

The Engineer returned `READY_FOR_ASSURANCE`. **The Project Lead independently reproduced fifteen of
its claims** and recorded them at `governance/engineering/build-log/BL-20260824T081819Z-0159.yaml`.
**READ THAT ENTRY AND THE ENGINEER'S OWN `BL-20260824T080623Z-16WA` / `-16WB` ON THE LANE. THEN
DISTRUST BOTH.** Two seats agreeing is two seats, not a proof — and the Project Lead's own
`CD-PL-F175` at that boundary is a worked example of a reconciliation measurement that was itself
wrong on the first attempt.

**THE FOUR DELIVERABLES:**

| # | What was built |
|---|---|
| **D1** | `PID.md` v1.1.1 carried onto the lane byte-identically; `required-tests.yaml` re-pinned to `sha256:08baf51c…` |
| **D2** | `detail_level` wired **PER-DIAL** into `$defs.dial_reading` on both closed envelope schemas, required in all three union branches, `schema_version` `const` 1.0.0 -> 1.1.0; the misaimed guard (`CD-PL-F169`) replaced |
| **D3** | `deploy/check_portability.py` — six refusals over `deploy/compose.yaml` read as YAML data |
| **D4** | The indicator-mapping registry-data carrier, **zero rows**, carried as a required field of `ConfigSnapshot` |

---

## 3. WHERE TO ATTACK HARDEST. **THESE FOUR ARE RANKED, AND THE RANKING IS REASONED.**

### 3.1 — **`detail_level`, BECAUSE THE GUARD OVER IT WAS MISAIMED UNTIL THIS INCREMENT**

`CD-PL-F169`: the previous absence test asserted only `"detail_level" not in schema["properties"]`
and `not in schema["required"]` — **top level only — so it PASSED on the per-dial attachment, which
is the very option the Product Owner then adopted.** It was *enforced against the rejected option and
unenforced against the proposed one*, for a whole increment, and an auditor found it.

*** **THE REPLACEMENT GUARD WAS WRITTEN BY THE SAME SEAT THAT WIRED THE FEATURE. THAT IS THE
OBVIOUS PLACE FOR A SECOND VACUITY TO HIDE, AND IT IS WHY THIS IS FIRST.** ***

Attack it: does the new guard actually fail when it should? Mutate a copy so `detail_level` sits at
envelope top level — does it fail? Remove it from `dial_reading` — does it fail? Remove it from
**only the `UNKNOWN` branch** — does it fail? **Build an envelope that publishes an `UNKNOWN` dial
with `detail_level: "calm"` and see whether anything in the system refuses it.** PID §3.2 is
constitutional — *"Missing data must never render as calm"* — and with zero registered sources
`UNKNOWN` is the only branch reachable in production today. **If a calm level can ride on an unknown
dial through any path, that is a `RED` and it does not matter how many tests pass.**

And check the `CD-AC-002` half is not merely absent but **unreachable**: is there any function,
helper, comprehension or dict-build anywhere that takes both dials' readings and returns one level,
one number or one ordering? `CD-AC-002` is about the existence of the function, not the word "blend".

### 3.2 — **THE D3 CLEAN ARM, BECAUSE A 1072-ASSERTION PASS IS WHERE A VACUOUS PASS LIVES**

`check_portability.py --root .` prints `PASS — 1072 assertions, 0 violations` over a file its own
author believed compliant. **A check that has never refused the real subject is a check nobody has
tested against the real subject.** The Project Lead planted ONE violation (a relative bind rewritten
absolute) and got 6 violations and exit 1. **THAT IS ONE ARM OF SIX RULES.**

Plant against **every** rule independently, on copies: durable data on a bind instead of a named
volume; a hostname or IP literal beyond the two declared loopback binds; an `argus` reference; a
literal where an env reference belongs; a secret-looking value. **And plant the admitting arms too**
— a check that refuses everything satisfies its invariant vacuously. **Then ask the harder question:
what portability failure would this check NOT catch?** An env var with a dell-specific *default*
baked into `${VAR:-/srv/...}`? A digest pinned to an image that exists only in this host's local
cache? **Name what it misses; that is worth more than confirming what it catches.**

### 3.3 — **`F03`'s HISTORY BREACH, BECAUSE NO INSTRUMENT THIS PROJECT OWNS WOULD HAVE CAUGHT IT**

The Engineer wrote 445 lines into `tools/` at `cd0fc24` — **outside its declared writable scope** —
and removed them at `33efbf7`. **Net `tools/` diff is 0. The tip is clean. Every scope instrument
here measures the tip.** The only reason this is on the record is that the seat that did it chose to
say so.

Verify it in history yourself. Then **sweep the whole range `116c01f..53f639a` commit by commit for
any OTHER path that was touched and reverted** — `pbg/`, `BLUEPRINT.md`, `governance/decisions/`,
anything at `be0b355`. **The seat disclosed one. Find out whether it disclosed all of them.** This is
the highest-value adversarial question in this increment and it is cheap to answer.

### 3.4 — **THE D4 CARRIER'S REFUSALS, EVERY ONE OF WHICH GUARDS A ROW THAT DOES NOT EXIST**

Zero rows are registered. So **every refusal in the carrier is currently unexercised by real data**,
and its only evidence is tests written by its author against synthetic fixtures. Attack the
refusals directly: a binding naming two dials at once; a bound dial with no polarity; a missing,
zero or negative staleness window; a tier outside `{x3,x2,x1}`; absent provenance; a `PENDING` row
asked to render as a value. **And the forgery the codebase has been bitten by before:** an object
with a `__class__` property wearing each new enum — `source_registry.py:174-200` records that
`isinstance` consults `__class__` and that exactly this forgery was **live and admitted** at
`ids_with` until increment 10. **Plant it against every new enum and every new record type.**

Also verify the anti-fixture control: the Engineer claims no synthetic identifier can reach the
shipped data file and that `PLANT_SYNTH_*` is the only fixture vocabulary. **Test that claim by
trying to get one in.**

---

## 4. THE THREE THINGS THAT MUST STILL BE TRUE, AND YOU VERIFY THEM RATHER THAN ASSUME THEM

1. **NO SOURCE IS REGISTERED.** Not a row, not a placeholder, not a fixture. Grep for real series
   identifiers across `src/`, `tests/`, `contracts/` and every data file. `SLOOS` and `NDFI` should
   appear **only as prose citing the ruling**. **If you find one as DATA, that is a `RED`.**
2. **NOTHING WAS BYPASSED AND NOTHING REGRESSED.** The register still validates, still computes 18,
   still reads `GATE: SHUT` with `latest_admitted_run (null)`. `be0b355` unmoved. `pbg/` at zero
   paths. **Run the tests at BOTH ends yourself** — the Project Lead measured 1882 at `116c01f` and
   1990 at the tip; reproduce both or contradict them.
3. **`CD-AC-002` STAYS AMBER-NOT-CLOSED AND `CD-AC-005` STAYS RED.** Nothing in 16A was permitted to
   move either. **Verify no grade moved by inspection, not by trusting the record.**

---

## 5. `Q32` — VERIFY IT, BECAUSE IT IS THE FINDING THAT MATTERS MOST AND IT CAME FROM THE SEAT ITSELF

The Engineer raised, and the Project Lead reproduced, that
`STALENESS_WINDOW_CEILING_SECONDS = 900.0` **refuses every window the ratified mapping requires** —
quarterly, monthly, daily and even **hourly** all raise `StalenessWindowOutOfRange`. **This blocks
16B independently of the mapping content.**

**REPRODUCE IT.** Then attack the *reasoning*, which is where an auditor is worth most: the Project
Lead adopted the reading that a **liveness ceiling** (how long a dead feed may masquerade as fresh)
and a **relevance window** (how often the series moves) are two different quantities sharing one
unit. **Is that right?** Is there a path by which a wide relevance window really would let a dead
feed read fresh — in which case the ceiling is correct and the *mapping* is what needs rethinking?
**Say which, and say what you measured to decide.** Neither the Engineer nor the Project Lead may
cut this; **you may not either** — it is Product Authority — **but a well-measured auditor's opinion
on it is exactly what the Product Authority needs and does not have.**

---

## 6. YOUR RETURN

**BOOT FIRST** and declare the verdict you actually get, including a `RED` inherited from the frozen
base's `ACTIVE_WORK.yaml` — that inheritance is known, is outside your scope, and you diagnose and
do not repair it.

**`PASS` / `AMBER` / `RED`, with the next safe gate named.** And:

* **Every finding with the command that produced it, output pasted.** Confidence stated per finding.
* **Both arms of every plant**, and the admitting arm wherever a refusal could be vacuous.
* **What you did NOT verify** (`CD-RULE-004`). There is no live PostgreSQL on this project and
  publication is tested against a recording double — **so atomicity, the `CHECK` constraints as
  executed and the append-only `GRANT` posture are UNSUPPORTED for a running instance.** Say so, and
  say what else you left.
* **Findings against this dispatch.** If the Project Lead's ranking in §3 sent you to the wrong
  place, say so. **Three of the last five seats found real errors in their own instructions and were
  right where the Project Lead was wrong.**

**A `PASS` IS NOT ACCEPTANCE** (`PBG-AUTH-003`, `CD-D-180`). Acceptance is the Product Authority's.

**COMMIT YOUR VERDICT.** A verdict that exists only in your conversation is not project state
(`PBG-CONT-007`) — and note that the `pbg log` CLI **cannot validate this project's build log**
(`CD-PL-F171`, a framework defect, reported and not yours to repair), so validate your entry by
direct call to `continuity.validate` with `schema_dir=pbg/schemas` before you commit it.

**Commit identity — `git -c user.name=` DOES NOT WORK on this host:**
```
GIT_AUTHOR_NAME=CD-ASR-WO3-03 GIT_AUTHOR_EMAIL=cd-asr-wo3-03@seats.crash-detector.invalid \
GIT_COMMITTER_NAME=CD-ASR-WO3-03 GIT_COMMITTER_EMAIL=cd-asr-wo3-03@seats.crash-detector.invalid \
git commit -m "..."
```
