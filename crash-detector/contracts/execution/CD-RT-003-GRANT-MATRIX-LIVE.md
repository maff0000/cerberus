# Execution contract — CD-RT-003-GRANT-MATRIX-LIVE

**CD-AC-003** · Witnesses are side-by-side, never ingredients · obligation **MANDATORY** · scope **CLASS** ·
delivered in **WO-2**

This document exists because `REQUIRED-TEST-REGISTER-CONTRACT-v1` check 3 requires every
declared test to name an execution contract that RESOLVES. It states how this test is run
and what its exit codes mean. **It states no result.** The register carries obligations;
status is computed by the validator from the register, the PID and append-only run records,
and there is no field anywhere in this chain in which an author could write a verdict.

## The proposition

Read out of a LIVE PostgreSQL catalogue, cd_engine holds no privilege of any kind on schema witness, by any of the seven routes a privilege can arrive.

## Command

```
python3 tools/register/check_grant_matrix_live.py --root .
```

Run with the working directory set to **the root of a subject tree the auditor extracted
itself** — `git archive <sha> | tar -x -C <tmpdir>`, never the Engineer's worktree. The line
above is verbatim: no path fixing, no editing, no wrapper. There is no run-everything
harness in this repository and there may not be one, because an auditor verifying through a
harness the project wrote is verifying the harness (`PBG-ASSURE-001`).

## Subject

A store built by applying the SUBJECT TREE's own migrations, in filename order, with plain SQL — deliberately NOT through `db/migrate.py`, because a check must not depend on the correctness of the thing it is checking. Then the catalogue itself, and finally a session opened AS cd_engine so that PostgreSQL does the refusing.

## Why it is asserted this way

A GRANT that was written and a GRANT that is held are different facts. Where the migration text and the catalogue disagree, the catalogue wins and the migration is wrong.

## Preconditions

* `python3` 3.11 or later. **Stdlib only** — no install step, no network, no
  virtualenv. A check that needs a package installed is a check the auditor cannot run.
* The subject tree extracted by the auditor, with the working directory set to its root.
  `--root .` is not a default and is not optional: it is there so that the check is always
  pointed at a tree explicitly, and never at whatever directory it happens to sit in.

## Exit semantics

| exit | meaning |
|---|---|
| `0` | CLEAN — assertions were made and all of them held. A run that made ZERO assertions refuses instead, so `0` can never mean "I looked at nothing". |
| `1` | VIOLATION — at least one finding, each printed with its file, its line and why it is one. |
| `2` | USAGE — the command line was wrong. |
| `3` | PRECONDITION NOT MET — the check could not do its job, with the reason on stderr. |

Anything other than `0` is a failure. **The check never skips, for any reason**
(`PBG-CI-002`): a precondition it cannot meet is a non-zero exit with a stated reason,
never a pass.

## Connection target — BY NAME, NEVER BY VALUE

The store is named in the environment. **The password is read by NAME at the point of use;
its VALUE is never printed, logged or written anywhere by the check, and any occurrence of
it in a driver error message is redacted before that message is shown** (`PBG-SEC-002`,
`PBG-EVID-003`, `PBG-CONT-009`, all non-waivable). No value of any of these belongs in this
document, in the register, in a run record or in the Build Log.

    CD_CHECK_STORE_HOST      e.g. 127.0.0.1 — and 127.0.0.1 only (CD-D-006)
    CD_CHECK_STORE_PORT
    CD_CHECK_STORE_NAME      the database to migrate and probe
    CD_CHECK_STORE_USER      a role that may CREATE ROLE and CREATE SCHEMA and read pg_authid
    CD_CHECK_STORE_PASSWORD

Additional dependency: `psycopg2` (2.9.11 is present on the commissioned host). An absent
driver, an unset variable, a refused connection, a failed migration or a subject tree with
no migrations in it each produce **exit 3 with the reason stated** — never a skip. A check
that skips when the store is down reports success on every host where nobody started a
database, which is most of them.

## Negative control

Any privilege of any kind reaching cd_engine on schema witness, planted in the subject tree's migrations. The class has seven routes and the plant may take any of them: the schema privilege, table or column privileges, sequence or function privileges, a grant to PUBLIC that cd_engine inherits, membership of a role that holds one, a default privilege that would grant it on a future object, ownership of the schema or of anything in it, or the SUPERUSER / BYPASSRLS role attributes.

Detection is a **contrast**, and the validator computes it as one: the same declared command
must exit `0` on the clean subject and non-zero on the subject with the violation planted.
A clean arm that fails cannot be told apart from a broken harness, and a broken harness
detects nothing — the validator returns `UNDECIDABLE`, never `PASS`.

The negative control for this test is declared as run record **`RTR-WO2-0001`**.
That record does not exist yet. It is the run the **independent Assurance
seat** will produce — a distinct actor from the one that wrote this test. Until it exists
the validator computes `UNDECIDABLE` for this test and the gate stays shut, which is
correct: this seat may declare which run must evidence its guard, and may not supply it.

## What this contract does not claim

It does not claim the test passes. It does not claim the criterion is satisfied. It does not
admit any evidence: `latest_admitted_run` is null in the register and this seat cannot fill
it in, because an implementation may not certify itself (`PBG-SOD-001`, non-waivable).
