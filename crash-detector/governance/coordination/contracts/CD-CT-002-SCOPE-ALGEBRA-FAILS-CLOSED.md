# EXECUTION CONTRACT — `CD-CT-002-SCOPE-ALGEBRA-FAILS-CLOSED`

> **This is place 2 of the three `CD-RULE-004` requires.** Place 1 is the limit block the
> instrument prints AFTER its verdict from a `finally`, on every exit path. Place 3 is the row in
> `governance/coordination/required-tests.yaml`. **THE THREE MUST AGREE. A REGISTER ENTRY MAY NOT
> CLAIM MORE THAN ITS GUARD DELIVERS**, and two prior seats on this project were found short
> exactly here.

| | |
|---|---|
| **delivers** | PO-DECISIONS-0021 ruling 3(b) — parallel writers never touch the same bytes |
| **instrument** | `tools/coordination/scope.py` |
| **supporting** | `tools/coordination/test_scope.py` |
| **invocation** | `python3 -B tools/coordination/scope.py --a G --b G [--expect overlap|disjoint]` |
| **plant** | `governance/coordination/plants/PLANT-COORD-02.run.sh` |
| **closes its class?** | **NO.** It declares its limit — `CD-RULE-004` option 2. |
| **arms** | 4 |
| **last run** | LIVE — 4/4 arms contrasted |

## 1. WHY THIS CONTROL EXISTS

Everything in increment 12 reduces to one predicate: do two scopes overlap? Wrong in the
permissive direction, two seats collide. Wrong in the restrictive direction, **ruling 3 is not
implemented at all**, because every parallel launch is refused and the invariant holds vacuously.

## 2. THE DECLARED LIMIT — VERBATIM, AND IT MUST MATCH THE OTHER TWO PLACES

> DECIDES literal paths, recursive `p/**` prefixes, and single-segment `*`/`?` globs — the last by EXACT product-automaton emptiness and not by a heuristic. **DECIDES PARENT-PATH CONTAINMENT: a shorter non-recursive pattern whose every segment intersects a longer one names a PARENT of what the longer names, and is reported OVERLAP/PARENT_PATH, because a write to a parent path reaches its children.** REFUSES (fails closed to OVERLAP) `**` mid-pattern, character classes and brace expansion. REFUSES at parse time `..`, absolute paths and the empty entry. DECIDES case collision conservatively. DOES NOT DECIDE symlink aliasing textually.

### 2b. THE ONE RULE THAT CHANGED AT INCREMENT 13 — `CD-ASR-WO2R3-06-F11`

**A DIRECTORY WAS CALLED DISJOINT FROM ITS OWN CONTENTS.** `overlaps(['tools/coordination'],
['tools/coordination/scope.py'])` returned `False`; so did `overlaps(['a/*'], ['a/b/c'])` and
`overlaps(['governance/*'], ['governance/coordination/ACCOUNTABLE-SEAT.yaml'])`. `claim.py`
compensated by refusing a bare existing-directory LITERAL, but that guard **exempted every wildcard
form of the same hazard**, and `lease.py` had no such guard at all.

**MATCHING AND OVERLAP ARE DIFFERENT QUESTIONS AND INCREMENT 12 CONFLATED THEM.** A literal still
MATCHES exactly one path — `dir/**` is still how you say you mean the subtree — but it is never
DISJOINT from what lies beneath it. The algebra is textual and its pure-algebra path has no
worktree, so it cannot ask whether the parent is a directory today, and *"not a directory yet"* is
not a property a coordination control may rest on: `CD-RULE-003`, fail closed.

**THE AUTOMATON IS NOT TOUCHED.** The product-automaton segment intersection, the recursive-prefix
rule and the case-collision rule are exactly as increment 12 wrote them, and the ninth Assurance
seat found them correct on every form it put to them. **`F11` IS THIS ONE DEPTH RULE AND NOTHING
ELSE.** `test_scope.py` carries the case that asserted the OLD answer with its expectation INVERTED
and the reason written at the case — that expectation WAS the defect, and this suite had a GREEN
TEST OVER IT.

## 3. THE RESIDUE (`CD-RULE-006`)

> SYMLINK ALIASING, when the algebra is used WITHOUT a worktree, is NOT PROVED TO BE CARRIED ANYWHERE. With a worktree it is carried by check_scope_disjoint.py via scope.symlinked_components(), and that hand-off is MEASURED by PLANT-COORD-02 arm 3b.

**A residue declaration must name a layer MEASURED to hold it, or be written "NOT PROVED TO BE
CARRIED ANYWHERE". A declaration that misdirects an auditor to a layer that does not hold is
worse than no declaration, because it spends the auditor's attention somewhere the defect is not.**

## 4. HOW TO EXECUTE THE CONTRAST

1. `python3 -B tools/coordination/test_scope.py` — 27 cases, expected 0 failures.
2. Two live claims whose scopes overlap only BELOW the first segment -> refused; `git apply` the
   fail-open mutation -> admitted.
3. Two genuinely disjoint scopes -> admitted, and the asymmetric write-vs-READ pair -> refused.

**A PLANT THAT PASSES BOTH ARMS IS DEAD AND IS WORSE THAN NO PLANT.** If an arm will not
contrast, the runner prints `*** DID NOT CONTRAST ***` and the plant verdict is
`NOT A CONTRAST`. It does not quietly report success.
