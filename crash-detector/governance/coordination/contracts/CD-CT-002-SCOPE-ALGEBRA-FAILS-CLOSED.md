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

> DECIDES literal paths, recursive `p/**` prefixes, and single-segment `*`/`?` globs — the last by EXACT product-automaton emptiness and not by a heuristic. REFUSES (fails closed to OVERLAP) `**` mid-pattern, character classes and brace expansion. REFUSES at parse time `..`, absolute paths and the empty entry. DECIDES case collision conservatively. DOES NOT DECIDE symlink aliasing textually.

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
