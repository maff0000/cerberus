# WO-3 INCREMENT 15 — THE TEN CONTRAST PATCHES FOR THE PUBLICATION AND HEALTH SURFACE

**Written by `CD-ENG-WO3-02`** under `governance/engineering/CD-DISPATCH-INC15-PUBLICATION-ENGINEER.md` §6.

**Nothing in this directory is evidence, and nothing in it is assurance.** The patches exist so
that every claim this increment makes is measured **by contrast** rather than asserted from one
side. They are **never applied to the worktree**: each arm below ran in its own throwaway
`git archive | tar -x` extraction under `/tmp`, and the worktree was never mutated.

---

## THE ARMS, AS MEASURED AT TIP `02a170a6c70af9b0597b5478c5c17d91ef416716`

Each arm from **its own pristine `git archive <tip> | tar -x` extraction**. `git apply`'s **own
exit code** is recorded as its own column, because *a patch that does not apply produces a
"violated" arm that is the clean tree* — this project's established form, and the defect
`CD-ENG-WO2R3-06-F06` recorded when a plant silently stopped applying.

| Plant | Declared command run | `git apply` | CLEAN | VIOLATED | violated-arm result |
|---|---|---|---|---|---|
| `P1-VALIDATE-AFTER-THE-PUBLIC-WRITE` | `test_publication_layer.py` | **0** | **0** | **1** | 3 failed, 18 passed |
| `P2-PUBLIC-SURFACE-ADMITS-A-PRIVATE-CLASSIFIED-KEY` | `test_publication_layer.py` | **0** | **0** | **1** | 2 failed, 19 passed |
| `P3-CADENCE-IGNORES-THE-OPEN-INTERVAL` | **`CD-RT-008`'s own** | **0** | **0** | **1** | 4 failed, 23 passed |
| `P4-CADENCE-READS-THE-AGE-OF-A-NUMBER` | **`CD-RT-008`'s own** | **0** | **0** | **1** | 1 failed, 26 passed |
| `P5-REGIME-WINDOW-DOES-NOT-TIGHTEN` | **`CD-RT-009`'s own** | **0** | **0** | **1** | 2 failed, 23 passed |
| `P6-HEALTH-SURFACE-ADMITS-A-DIAL-VALUE` | **`CD-RT-014`'s own** | **0** | **0** | **1** | 2 failed, 35 passed |
| `P7-AN-EXTERNAL-PUSH-CHANNEL-IS-ADDED` | `test_no_external_push.py` | **0** | **0** | **1** | 1 failed, 14 passed |
| `P8-THE-PROBE-IMPORTS-THE-APPLICATION` | **`CD-RT-014`'s own** | **0** | **0** | **1** | 2 failed, 35 passed |
| `P9-MISSING-DATA-RENDERS-AS-CALM` | `test_detail_level.py` | **0** | **0** | **1** | 1 failed, 30 passed |
| `P10-A-DEGRADED-READING-RENDERS-AS-CALM` | `test_detail_level.py` | **0** | **0** | **1** | 1 failed, 30 passed |

**Three of the commands above are the register's OWN declared commands**, run verbatim:

```
CD-RT-008   PYTHONPATH=src python3 -m pytest tests/test_cadence_breach.py -q
CD-RT-009   PYTHONPATH=src python3 -m pytest tests/test_regime_staleness.py -q
CD-RT-014   PYTHONPATH=src python3 -m pytest tests/test_health_surface.py -q
```

**The other four are NOT register commands and are not offered as such.** `test_publication_layer.py`,
`test_no_external_push.py` and `test_detail_level.py` carry no register row — `CD-AC-006`'s row is
sequenced at **WO-5** and names a checker (`tools/register/check_public_artefact_no_private_field.py`)
that **does not exist at this SHA**, and `Q26` and `detail_level` have no criterion of their own.
Stated here rather than left to be inferred from the table.

---

## *** THE COLUMN QUESTION, TAKEN UP EXPLICITLY (dispatch §6, `CD-ENG-WO3-01`'s `F04`) ***

Increment 14's Engineer found that **the verifier exits `2` in all three of its arms, so exit code
alone discriminated nothing**, and substituted columns that did. The dispatch requires this seat to
say whether the same is true here.

> **IT IS NOT. THE EXIT CODE DISCRIMINATES ON THIS INSTRUMENT: `0` clean, `1` violated, on all ten
> plants. NO SUBSTITUTION WAS NEEDED AND NONE WAS MADE.**

**ONE COLUMN WAS ADDED, AND IT IS NOT A SUBSTITUTION.** *"Violated-arm result"* records the failure
count, and the per-plant sections below record **which tests failed by name**. An exit code of `1`
proves the command failed; it does not prove it failed **for the reason the plant was planted**. A
plant that broke an import and collapsed the whole module would also exit `1` and would look
identical in a three-column table. So every violated arm below is checked against the test that
carries its proposition, and **in every case the failures are exactly those tests and no others of
an unrelated kind.**

---

## WHAT EACH PLANT VIOLATES, AND WHAT FAILED

### `P1-VALIDATE-AFTER-THE-PUBLIC-WRITE` — *both envelopes judged before either is written*
Removes the private envelope's validation from the pre-write block, leaving the public one. This is
the *"each validated before its own write"* defect rather than *"both before either"*, and its
consequence is a **published public envelope for a cycle whose private counterpart never existed** —
and the public one is the one consumers have already seen.

```
FAILED test_a_PRIVATE_envelope_violating_its_schema_also_writes_NO_PUBLIC_ENVELOPE
FAILED test_each_envelope_is_judged_against_ITS_OWN_contract
FAILED test_a_secret_bearing_key_is_refused_on_BOTH_surfaces
```

**ADMITTING ARM** (in the same module, unpatched): `test_a_conforming_pair_is_written` — a
conforming pair produces exactly one insert into each of the three tables and **no alert**.

### `P2-PUBLIC-SURFACE-ADMITS-A-PRIVATE-CLASSIFIED-KEY` — *`CD-AC-006`*
Flips one identity comparison so the book-adjacent refusal applies to the PRIVATE surface instead of
the PUBLIC one — the boundary inverted rather than removed, which is the version a reader skims past.

```
FAILED test_a_private_classified_key_on_the_public_surface_is_refused
FAILED test_the_same_key_nested_inside_a_dial_is_refused_too
```

**ADMITTING ARM:** `test_a_legitimate_public_envelope_passes_the_same_gate`.

### `P3-CADENCE-IGNORES-THE-OPEN-INTERVAL` — *`CD-AC-008`, the halted-publication case*
Drops the OPEN interval (last heartbeat → now) and keeps every closed one. **A stopped publisher
writes no further heartbeat and therefore creates no further gap**, so the largest closed interval
stays whatever it was while the system was healthy — forever.

```
FAILED test_publication_halted_is_a_breach
FAILED test_the_halt_is_detected_by_the_OPEN_interval_and_not_by_any_closed_one
FAILED test_detection_happens_within_one_publication_cycle_of_the_breach
FAILED test_a_breach_writes_a_durable_alert_row_first
```

**ADMITTING ARM:** `test_a_publisher_on_cadence_raises_nothing` — normal cadence must be quiet, or
the alarm is noise and the first response to it is to switch it off.

### `P4-CADENCE-READS-THE-AGE-OF-A-NUMBER` — *cadence ≠ age*
Adds an `as_of_utc` parameter to `evaluate_cadence`. Nothing reads it; **the widening alone is the
violation**, because the property is that the age of a number has no route into this function at all.

```
FAILED test_evaluate_cadence_CANNOT_BE_GIVEN_the_age_of_a_number
```

**THE TWO CASES THAT COME APART** are measured in the unpatched module, each with **both halves**:
`test_a_stale_number_republished_on_time_has_HEALTHY_cadence_and_STALE_data` and
`test_a_fresh_number_published_late_has_BREACHED_cadence_and_FRESH_data`.

### `P5-REGIME-WINDOW-DOES-NOT-TIGHTEN` — *`CD-AC-009`*
Disables the tightening check in the policy constructor, making **all three** of the register's named
violations constructible at once: the constant window, the inverted window, and the ignored regime.

```
FAILED test_a_constant_window_is_refused
FAILED test_an_inverted_window_is_refused
```

**ADMITTING ARM:** `test_the_same_age_passes_in_calm` beside `test_the_same_age_fails_in_stress`,
with `test_the_two_arms_differ_ONLY_by_the_regime_argument` asserting the contrast is one argument
wide — if the arms differed in the age, the instant or the constructor they would demonstrate
something other than the criterion.

### `P6-HEALTH-SURFACE-ADMITS-A-DIAL-VALUE` — *`CD-AC-014` / `CD-AC-006`*
Adds one key to the closed `HEALTH_KEYS` allowlist. That is the whole of the leak: a health endpoint
carrying a dial value is a `CD-AC-006` breach wearing an ops hat.

```
FAILED test_the_five_observables_are_independently_readable
FAILED test_a_dial_value_on_the_health_surface_is_refused
```

**ADMITTING ARM:** liveness, both timestamps, a declared regime and a declared degraded CLASS all
pass — `test_the_five_observables_are_independently_readable` on the clean arm, and
`test_every_declared_degraded_class_is_admitted`.

### `P7-AN-EXTERNAL-PUSH-CHANNEL-IS-ADDED` — *`Q26`*
Adds `import smtplib` to the alerting module. **The import alone is the violation**; no send call is
needed, because the ruling is that the channel does not exist, not that it is switched off.

```
FAILED test_the_application_tree_imports_nothing_outside_the_declared_surface
```

**ADMITTING ARM:** `test_the_scan_admits_the_genuine_article`. And note the deny-by-default
property: the same guard catches `slack_sdk` and `discord`, **which appear nowhere in its
vocabulary**, plus `subprocess` and `ctypes`, which are on no list of network modules.

### `P8-THE-PROBE-IMPORTS-THE-APPLICATION` — *`PBG-EVID-001`, independence*
Makes the external probe import `crash_detector.health`. An observer that shares code with the thing
it observes is wrong in exactly the same way as the thing it observes and cannot see it.

```
FAILED test_the_probe_imports_nothing_from_the_application
FAILED test_the_probe_runs_without_the_application_package_importable
```

The second failure is the substantive one: the probe stops being deployable to a machine that does
not have the application on it, which is where an independent observer belongs.

### `P9-MISSING-DATA-RENDERS-AS-CALM` — *PID §3.2, constitutional*
Disables the constructor refusal, so a policy mapping `Degraded`/`Unknown` to `calm` becomes
declarable.

```
FAILED test_a_policy_that_renders_absent_data_as_calm_is_REFUSED
```

### `P10-A-DEGRADED-READING-RENDERS-AS-CALM` — *PID §3.2, THE SUBSTANTIVE ARM*
**P9 alone was not enough and this is recorded because it was noticed, not because it was avoided.**
P9 breaks only the *declaration* check; the runtime tests use a policy that names `elevated`, so they
pass unchanged. P10 makes `on_degraded` read the score and ignore the damage, so a **`Degraded`
reading scoring 0.01 actually renders as `calm`** — which is *"rendering stale or missing data as
calm"*, the behaviour PID §4 lists as prohibited.

```
FAILED test_a_degraded_reading_never_renders_as_calm_even_with_a_tiny_score
```

**AND ITS CONTRAST, WHICH IS WHAT MAKES IT MEAN ANYTHING:**
`test_the_SAME_score_on_a_VALUE_reading_does_render_as_calm`. Same number, same dial, same policy —
**only the constructor moved**, and the answer changed. So the refusal is caused by the damage and
not by the threshold.

---

## WHAT THIS SET DOES NOT PROVE

* **It does not admit any evidence.** `latest_admitted_run` is `null` in `required-tests.yaml` and
  this seat did not touch it. All three of this increment's criteria remain **`UNDECIDABLE`**, and
  that is the correct status: an implementation may not certify itself (`PBG-SOD-001`, non-waivable).
* **It does not prove the plants will keep applying.** `plants/MANIFEST.md` records that **four
  separate increments have broken a plant and found out only when somebody re-ran the set by hand**,
  and that the carrier for that is **NOT PROVED TO BE CARRIED ANYWHERE**. This set is subject to the
  same standing defect, and no runner over this directory was written — that is the wrapper
  `PBG-ASSURE-001` forbids this seat to write.
* **It does not prove any of this runs in a deployment.** The container set is not built
  (`CONTAINER_READY_DESIGN`), there is no live PostgreSQL on this lane, and no host is measured
  running the external probe on a schedule.
