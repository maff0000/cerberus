# CD-D-186 — ENGINEER DISPATCH, WO-3 INCREMENT 16G: THE FOUR TRUE-REGARDLESS FINDINGS

**Dispatch id:** CD-D-186
**Issued at:** 2026-08-25T05:59:19Z, by `PROJECT_LEAD_SEAT_09`, at `fa334b9` on `main`
**Seat:** `CD-ENG-WO3-15` — **A FRESH ENGINEER IDENTITY.** You have never held a seat on this project.
**Role source:** `pbg/roles/engineer.md` — the canonical local contract. Read it. Reading it does not
grant the role; **this dispatch grants it** (`PBG-BOOT-001`, `PBG-BOOT-002`).
**Authority record:** `CD-AUTH-0001`, carried through `PO-DECISIONS-0032` (commit `c734cb1`, Product
Owner, ratified by Matt).
**Expected return:** `READY_FOR_ASSURANCE`, at a named content SHA.

---

## 1. WHY THIS INCREMENT EXISTS

`Q41` is disposed. The Product Owner chose **ACCEPT-AND-RELEASE**: the guard at `7ac11c9` is accepted
with its scope declared, and the insider-source-weakening residual (`CD-ASR-F14-01`) is assigned to the
assurance/detection tier as later-hardening.

**THIS INCREMENT IS NOT THAT DECISION AND DOES NOT DEPEND ON IT.** Every item below was **TRUE
WHATEVER `Q41` WAS RULED**. They are owed corrections to records that are wrong today.

> **`CD-ASR-F14-01` IS OUT OF SCOPE AND YOU MAY NOT REOPEN IT.** Do not build a coverage property, a
> code-structure invariant, or any new guard mechanism. `PO-DECISIONS-0032` ruling 3 records it as owed
> later-hardening. **A seat that "improves" it here is working outside its dispatch.**

---

## 2. YOUR SCOPE — EXACT

| | |
|---|---|
| Repository | local, `/srv/crash-detector` |
| Branch | **`wo-3`** |
| Worktree | **`/srv/crash-detector-wo3`** |
| Base | `c475b8e` (content tip `7ac11c9`) |

**WRITABLE — and nothing else:**

- `tools/register/check_stale_data_never_calm.py`
- `tools/register/check_publication_chokepoint.py`
- `contracts/execution/CD-RT-001-STALE-DATA-NEVER-CALM.md`
- `contracts/execution/CD-RT-001-PUBLICATION-CHOKEPOINT.md`
- `required-tests.yaml`
- `plants/WO3-INC16G/` (new — your negative controls)
- `governance/engineering/build-log/` (your own return entry only)

**FORBIDDEN — a write here ends the increment:**

- **`src/`** — *** **THE DECLARED STOP OF THIS INCREMENT IS THAT `src/` DOES NOT MOVE.** *** The
  product is not defective and you are not repairing it.
- `pbg/` — pinned, read-only, non-waivable.
- `contracts/*.json` — the shipped envelope schemas. Byte-identical at return.
- `PID.md`, `BLUEPRINT.md`, `governance/decisions/`, `governance/mapping/`.
- The `wo-2r3` branch — **FROZEN at `be0b355`.** Do not touch, merge or rebase it.

---

## 3. THE FOUR ITEMS

### ITEM 1 — `CD-ASR-F14-02`: a declared limit that is false in the reassuring direction

`DECLARED LIMIT 9` closes by reassuring the reader that the residual it has just admitted is caught by
the sibling structural row. **THAT REASSURANCE IS FALSE**, and the auditor built the counterexample.

The clause, as it stands in the instrument header:

> *"It is caught by the sibling STRUCTURAL row `CD-RT-001-PUBLICATION-CHOKEPOINT` (`CD-CHOKE-005`),
> **AND THE TWO ROWS ARE A PAIR FOR EXACTLY THIS REASON.**"*

**WHY IT IS FALSE:** arm `Z7` is a `return`-shaped bypass on the publication path that the structural
row does **NOT** catch — the `return` sits inside `_iter_nodes`, the SHARED DOCUMENT WALK, and
`CD-CHOKE-005` walks `_refuse_stale_calm` only. The sentence is true of `return`s in ONE FUNCTION and
is written as a claim about a CLASS. `LINE 06 rc=0`, gate admissions 2, published 1.

**THE THREE `CD-RULE-004` PLACES**, located and confirmed present by the Project Lead:

1. `tools/register/check_stale_data_never_calm.py` — around lines 263-266
2. `required-tests.yaml` — around lines 1475-1478
3. `required-tests.yaml` — **AND AGAIN** in the row-level summary, around lines 1642-1643
4. `contracts/execution/CD-RT-001-STALE-DATA-NEVER-CALM.md` — the counterpart clause

> **NOTE THE ROW-LEVEL SUMMARY IS A FOURTH SITE IN A THREE-PLACE RULE. FIND THEM ALL. `grep` for the
> reassurance, not for the line number — the numbers above are this seat's reading and may drift.**

**WHAT TO DO:** **SUPERSEDE, NEVER EDIT** (`PBG-CONT-003`, non-waivable). The false sentence stays
readable beside its correction, with **arm `Z7` NAMED** as the thing that falsifies it. The adjacent
sentence — *"NEITHER ROW CLOSES IT ALONE AND THE RETURN DOES NOT CLAIM OTHERWISE"* — **IS TRUE AND
HONEST AND MUST SURVIVE.** It is the closing reassurance that is wrong, not the disclosure.

**Write the correction so it is true of the CLASS, not of one function.** If you cannot state a true
sentence about what the structural row catches, say what it catches and stop there. **A limit that
admits it does not know is worth more than one that reassures.**

### ITEM 2 — `CD-ASR-F14-03`: `CD-CHOKE-003` does not inspect its own gate's handlers

`CD-CHOKE-003` (`tools/register/check_publication_chokepoint.py`, around lines 57, 255, 535-556)
states:

> *"No `except` handler on the JUDGING PATH may swallow the refusal — each ends in a `raise`"*

**AND IT DOES NOT INSPECT `refuse_unless_publishable`'s OWN HANDLERS.** Arm `Z5` puts a
`try/except PublicationRefused` around the freshness stage *inside the gate*, re-raising only when
`config_snapshot_id != "BYPASS"`. Result: `LINE 06 rc=0`, gate admissions 2, published 1, **all
thirty-three register lines `diff`-identical.**

**ITS STATED SCOPE IS WIDER THAN ITS IMPLEMENTED SCOPE.** That is the defect.

**WHAT TO DO:** make the implemented scope match the stated scope — `CD-CHOKE-003` must reach
`refuse_unless_publishable`'s own exception handlers, not only `publish_cycle`'s. **This is the one
real guard change in this increment and it is bounded.**

**IT NEEDS A NEGATIVE CONTROL.** Land the `Z5` shape as an executable arm under `plants/WO3-INC16G/`
and show the row **MOVES** on it. A guard change with no arm that bites is a claim, not a control.

**AND CHECK THE VACUITY DIRECTION**: the row must still PASS on the clean tree. A control that fails
on everything catches nothing.

### ITEM 3 — `CD-ASR-F14-04`: the word `CLOSED`, deleted by edit

At `a9e19c3`, all three `CD-RULE-004` places read:

```
...THE VALUE VOCABULARY IS A CLOSED WRITTEN LIST
```

At `7ac11c9`, `required-tests.yaml` **alone** reads `...A WRITTEN LIST`. The other two are unchanged.
**THE WORD WAS REMOVED BY EDIT, WITH NO VERBATIM QUOTE OF THE PRIOR HEADING ANYWHERE IN THAT FILE**,
which is what `PBG-CONT-003` forbids — and the deleted word makes the limit's statement **WEAKER**,
because a "closed" written list is a stronger admission of narrowness than "a written list".

> **MEASURE THIS YOURSELF BEFORE YOU ACT ON IT.** The Project Lead's first measurement — a naive
> `grep -ci "closed written list"` — **APPEARED TO REFUTE THE AUDITOR**, because the text is
> line-wrapped differently in each of the three files. The whitespace-normalised re-run confirmed the
> auditor exactly. Use:
> ```
> git show <sha>:<file> | sed 's/^[[:space:]]*#*[[:space:]]*//' | tr '\n' ' ' | tr -s ' ' \
>   | grep -o "VOCABULARY IS A[A-Z ]*WRITTEN LIST"
> ```

**WHAT TO DO:** restore three-place agreement **BY DISCLOSED SUPERSESSION AND NOT BY A SILENT
RE-EDIT.** The record must show that the word was removed, that the removal was found, and that it was
put back — not merely end up with the word present. **A silent restoration would be the same class of
act as the deletion.**

### ITEM 4 — `CD-ASR-F14-05`: a figure that does not reproduce

`BL-20260824T223344Z-16FC` records `PASS — 142088 assertions, 0 violations   (was: 122)`. **THE TIP
FIGURE REPRODUCES. THE `(was: 122)` DOES NOT.** Two independent seats (`CD-ASR-WO3-13`,
`CD-ASR-WO3-14`) measured **97** at `a9e19c3`.

**THE FIGURE IS WIDER THAN THE VERDICT RECORDED — THIS IS THE PROJECT LEAD'S OWN MEASUREMENT AND YOU
SHOULD CHECK IT:** `122` is also written into **`DECLARED LIMIT 11`** in the instrument header
(`check_stale_data_never_calm.py`, around line 290: *"`0.77 s` at `a9e19c3` for 122 assertions"*) and
in `required-tests.yaml` (around line 1499). **SO THIS IS A `CD-RULE-004` THREE-PLACE CORRECTION AND
NOT A ONE-LINE BUILD-LOG SUPERSESSION.**

**WHAT TO DO:** **RUN IT YOURSELF AT `a9e19c3` AND WRITE WHAT YOUR OWN SHELL PRINTS** (`CD-PL-F193` —
an inherited claim is a hypothesis until run). **DO NOT COPY `97` FROM THIS DISPATCH.** Use a
throwaway worktree at `a9e19c3` so the lane is not disturbed:

```
git worktree add /tmp/inc16g/base a9e19c3
python3 tools/register/check_stale_data_never_calm.py --root /tmp/inc16g/base
```

Then correct the figure in every place it appears, **by supersession**, and state the command that
produced your number beside it. If your measurement is **not** 97, **say so and do not round to the
auditors' figure** — three seats disagreeing is a finding, not an error to be tidied.

---

## 4. HOW YOU MUST WORK

- **`PBG-SOD-001` IS NON-WAIVABLE.** You build; you do not grade. A **fresh** Assurance seat grades
  this — and it will not be `CD-ASR-WO3-14`, which raised these findings and may not grade their
  repair.
- **SUPERSEDE, NEVER EDIT**, in every record. This increment is *about* a record edited rather than
  superseded. **Committing that same act while fixing it would be the finding of the increment.**
- **MEASURE, DO NOT INHERIT.** Every figure you write carries the command that produced it and the
  `rc` taken from that command.
- **RAISE FINDINGS AGAINST YOUR OWN WORK.** `CD-ENG-WO3-14` did, and it is why its return was
  auditable. A return with zero self-findings will be read as a return that did not look.
- **COMMIT ON THE `wo-3` LANE UNDER YOUR OWN SEAT IDENTITY** (`Q40`). `git -c user.name=` does **NOT**
  work on this host — use the environment:
  ```
  GIT_AUTHOR_NAME=CD-ENG-WO3-15 GIT_AUTHOR_EMAIL=cd-eng-wo3-15@seats.crash-detector.invalid \
  GIT_COMMITTER_NAME=CD-ENG-WO3-15 GIT_COMMITTER_EMAIL=cd-eng-wo3-15@seats.crash-detector.invalid \
  git commit ...
  ```
  Verify with `git log -1 --format=%an` **after** the commit. Do not assume it took.
- **Beware unquoted heredocs and `git commit -m`**: they silently delete backticked words from
  governance records on this host. Use a quoted heredoc (`<<'EOF'`) or write the file directly.

## 5. DECLARED STOPS — return immediately, do not improvise

1. **If closing `CD-ASR-F14-03` requires touching `src/`.** Return and say so. `src/` not moving is
   this increment's declared stop, and a guard change that needs the product to change is a
   Product Authority question, not an Engineer decision.
2. **If a correction you are asked to make turns out to be false when you measure it.** Say so with
   the command. **You are not obliged to fix something that is not broken, and this dispatch can be
   wrong.**
3. **If the true-regardless items turn out to depend on `Q41` after all.** Return.

## 6. WHAT YOU RETURN

A build-log entry under `governance/engineering/build-log/`, in this project's established form,
recording: what you changed and where, **every figure with its command and `rc`**, your no-regression
measurements (`src/` zero paths, `contracts/*.json` byte-identical, `pbg/` zero paths, `wo-2r3`
unmoved), the arms you built and the fact that they **bite**, the vacuity direction, your findings
against your own work, and the content SHA. Return `READY_FOR_ASSURANCE`.

**YOUR RETURN IS BANKED AS AN INPUT AND IS NOT AN ACCEPTANCE** (`PBG-AUTH-003`).
