# WO-2R increment 6 — the Project Lead's clean-arm baseline, captured BEFORE delivery

**Captured by:** PROJECT_LEAD_SEAT_01, 2026-08-19, at the resumption boundary
`BL-20260819T185403Z-0037`, **after** the increment-6 dispatch was issued at `44a56ec` and
**before** the seat had written anything.

**Subject:** lane `wo-2-skeleton` at `253c38bd4db58433e5209a222c0ce27429079156` — the execution base
of increment 6.

**Why it exists.** Increment 6 is the register-and-contract sweep and **it writes no logic**. Its
whole obligation is therefore negative: *nothing may move*. A sweep that moves a verdict is not a
sweep. A negative claim cannot be checked without a before-number, and a before-number taken from the
seat's own report is not a control. These numbers were measured by the Project Lead on its own
pristine extractions of `253c38b`, with no seat in the loop.

This file is **DATA**. Nothing in it is executable (`PBG-ASSURE-001`). It is read at reconciliation
and it is not edited afterwards — a correction supersedes (`PBG-CONT-003`).

## How it was measured

Two independent scratch trees, neither of them the lane worktree, so nothing here could disturb a
running seat:

```
git -C /srv/crash-detector archive 253c38b | tar -x -C /tmp/inc6-base      # no .git, for pytest
git clone -q --no-hardlinks -b wo-2-skeleton /srv/crash-detector /tmp/inc6-git   # .git, for plants
```

`python3 -B` and `-p no:cacheprovider` throughout: running pytest inside a governed tree writes
`__pycache__` and `.pytest_cache` and is mutation by effect (`PBG-RT-001`).

## 1 — the full suite

```
cd /tmp/inc6-base && PYTHONPATH=src python3 -B -m pytest -q -p no:cacheprovider
```

**1325 passed in 8.50s.**

Node-id inventory, so that "ZERO removed" can be proved rather than asserted:

```
cd /tmp/inc6-base && PYTHONPATH=src python3 -B -m pytest -q -p no:cacheprovider --collect-only \
  | grep "::" | sort > nodeids.txt
```

- **1325** node ids
- `sha256(nodeids.txt)` = `d0996f358cc3e5f5dacee8c4c1f99d944a0b0358a352b02ec0650c162abee4e7`

The list itself is not committed — it is re-derivable from `253c38b` by the command above, and the
digest proves any re-derivation is the same list. A re-derivation whose digest differs means the
extraction is wrong, not that the baseline moved.

## 2 — the ten declared register commands

```
cd /tmp/inc6-base && python3 -B tools/register/<check>.py --root .
```

| check | exit | assertions |
|---|---|---|
| `check_no_numeric_default` | 0 | 377 |
| `check_no_blend` | 0 | 4855 |
| `check_schema_closed` | 0 | 242 |
| **`check_engine_no_witness_reach`** | **0** | **24** |
| `check_no_execution_interface` | 0 | 38847 |
| `check_lockfile_denylist` | 0 | 15 |
| `check_egress_no_broker` | 0 | 69 |
| `check_base_image_digest_pin` | 0 | 13 |
| `check_dockerignore` | 0 | 22 |
| `check_grant_matrix_live` | 3 | — (`PRECONDITION_NOT_MET`, no live store) |

**`check_engine_no_witness_reach` at 24 assertions / exit 0 IS THE PROSE-ONLY LEASH** on the one
scope extension this increment carries. It is measured here, at the base, by the Project Lead — so
the leash is checked against a number the seat did not supply.

`check_grant_matrix_live` at exit 3 is the correct state with no live store: the derivation refuses
before any verdict is reached. Per `CD-ENG-WO2R-F18`, exit 3 is a *derivation* refusal and arrives
before a *violation* at exit 1; the two must not be collapsed into "non-zero".

## 3 — the eleven commands for criteria WO-2 does not deliver

Two of the declared `execute:` lines name checks that do not exist at this SHA:

```
python3: can't open file '.../check_public_artefact_no_private_field.py': [Errno 2] ...  -> exit 2
python3: can't open file '.../check_first_published_immutable.py':        [Errno 2] ...  -> exit 2
```

That is the required behaviour, not a defect: each terminates **non-zero naming an absent subject**,
and **none passes vacuously**. Recorded so that a seat reporting "exit 0" on either of these is
caught, and so that an auditor does not read the absence as an omission.

## 4 — the eleven plants

```
cd /tmp/inc6-git && git apply --check plants/<criterion>/<id>.patch
```

**11 of 11 apply cleanly at the base.**

```
plants/CD-AC-001/CD-RT-001-ABSENCE-RENDERS-UNKNOWN.patch
plants/CD-AC-001/CD-RT-001-AST-NO-NUMERIC-DEFAULT.patch
plants/CD-AC-002/CD-RT-002-AST-NO-BLEND.patch
plants/CD-AC-002/CD-RT-002-SCHEMA-CLOSED.patch
plants/CD-AC-002/CD-RT-002-TYPE-NO-ARITHMETIC.patch
plants/CD-AC-003/CD-RT-003-ENGINE-NO-WITNESS-REACH.patch
plants/CD-AC-003/CD-RT-003-GRANT-MATRIX-LIVE.patch
plants/CD-AC-005/CD-RT-005-PANEL-UNAVAILABLE-NEVER-AGREES.patch
plants/CD-AC-012/CD-RT-012-EGRESS-NO-BROKER.patch
plants/CD-AC-012/CD-RT-012-LOCKFILE-DENYLIST.patch
plants/CD-AC-012/CD-RT-012-NO-EXECUTION-INTERFACE.patch
```

`git apply --check` proves a plant **applies**. It does not prove it **contrasts**; the contrast is
run at reconciliation on throwaway copies. A plant that applies but no longer fails is a plant that
has stopped being a plant (`CD-ENG-WO2R-F13`: assert the expected rule id, not merely a non-zero
exit).

## What this baseline entitles the reconciliation to conclude

Only this: whether increment 6 moved anything it was forbidden to move. It says nothing about whether
the seat's declarations are *true* — that is the reading work, and it is the part of a declaration
sweep no number can do. **A declaration sweep is the easiest increment to fake, precisely because
nothing it produces fails a test.**
