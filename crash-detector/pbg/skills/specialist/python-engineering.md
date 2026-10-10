---
skill_id: SKILL-PYTHON-ENGINEERING
title: Python engineering
version: 1
roles: [ENGINEER, ASSURANCE_ENGINEER]
triggers: [implementing or auditing Python]
prerequisites: [Python 3 available, project dependency policy known]
required_inputs: [target Python version, dependency manifest]
related_controls: [PBG-CI-003, PBG-SEC-002, PBG-ASSURE-017]
references: [SRC-PRIMARY-DOCS, SRC-OWASP-ASVS, SRC-OPENSSF]
---

# Python engineering

## Version and dependencies

State the target Python version explicitly; behaviour differs across minors in ways that matter
(dict ordering guarantees, `datetime` handling, typing syntax). Pin dependencies to exact versions
and commit the lock. Prefer the standard library — every dependency is code you must vouch for.

## The traps that produce real defects

**Mutable default arguments.** `def f(x, items=[])` shares one list across every call. Use `None`
and build inside.

**Naive datetimes.** `datetime.now()` is ambiguous and unorderable across zones. Always
`datetime.now(timezone.utc)`, always ISO-8601 with offset when serialising.

**Bare `except:`** catches `KeyboardInterrupt` and `SystemExit`. Catch the exception you can handle;
let the rest travel.

**Silently swallowing.** `except Exception: pass` is a decision to continue with unknown state.
Make that decision deliberately or not at all.

**String-built subprocess and SQL.** Pass argument lists to `subprocess`, never `shell=True` with
interpolation. Use parameterised queries; never format values into SQL.

**Truthiness on containers and numbers.** `if not x` treats `0`, `""`, `[]` and `None` alike. When
absence and emptiness differ — and in this framework they usually do — test `is None` explicitly.

**Late-binding closures in loops.** `[lambda: i for i in range(3)]` gives three functions all
returning 2. Bind with a default argument.

## Structure

Type hints at module boundaries. Dataclasses for structured returns rather than tuples that lose
their meaning at the call site. `pathlib.Path` over string paths. Context managers for anything
that must be released.

Validate at the boundary into a typed structure, so internal code cannot receive a shape it does
not expect.

## Testing

`pytest`. Test at the seam the behaviour lives, and prove the test fails when that behaviour breaks
(`PBG-ASSURE-017`). Beware fixtures whose isolation expires — a module-scoped fixture mutated by one
test silently changes what every later test is measuring.

Parametrise over the cases that differ in kind, not the ones that differ in value.

## Evidence

`pytest` output with its command line; the mutation result; the pinned dependency manifest.
