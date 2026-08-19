# W6 — AUDIT OF DECLARED LIMITS (CD-RULE-004 / CD-RULE-006)

Target SHA: 50fc23177f790164c3fc3604ccee51663e755c70
Read-only tree: /srv/crash-detector-wo2r-audit
Method: read the three place-texts in full for every guard that declares a limit —
  (i) the check script header, (ii) the `# DECLARED LIMIT` comment block above the register
  entry in required-tests.yaml, (iii) contracts/execution/<TEST-ID>.md.
Then, per numbered boundary: (a) executable example present & reproduces, (b) carrier named
and MEASURED (not merely asserted), (c) three places agree in SUBSTANCE.

## Inventory of guards under tools/register/ (11 scripts, 9 with register entries)

| script | register test_id | header DECLARED LIMIT? |
|---|---|---|
| check_no_numeric_default.py | CD-RT-001-AST-NO-NUMERIC-DEFAULT | YES, 6 boundaries (hdr line 97) |
| check_no_blend.py | CD-RT-002-AST-NO-BLEND | YES (hdr line 140) |
| check_schema_closed.py | CD-RT-002-SCHEMA-CLOSED | NO header section |
| check_engine_no_witness_reach.py | CD-RT-003-ENGINE-NO-WITNESS-REACH | YES, "SIX" (hdr 160) |
| check_grant_matrix_live.py | CD-RT-003-GRANT-MATRIX-LIVE | NO header section |
| check_no_execution_interface.py | CD-RT-012-NO-EXECUTION-INTERFACE | YES, 6 (hdr 67) |
| check_lockfile_denylist.py | CD-RT-012-LOCKFILE-DENYLIST | NO header section |
| check_egress_no_broker.py | CD-RT-012-EGRESS-NO-BROKER | YES, 8 (hdr 163) |
| check_base_image_digest_pin.py | (CD-BUILD-CONTEXT-RESTRICTED, not a WO-2 register test row) | NO |
| check_dockerignore.py | (same) | NO |
| check_public_artefact_no_private_field.py | CD-RT-006-... | NOT DELIVERED (file absent) |

(WORK IN PROGRESS — appended as read.)

---
## FINDINGS LOG (appended as found)

### F-W6-01 (egress) — DANGLING EXECUTABLE EXAMPLE `V-F04-04`
contracts/execution/CD-RT-012-EGRESS-NO-BROKER.md:137, boundary 3:
  "the archetypal case fails on the operator (variant `V-F04-04`)."
`grep -rn "V-F04-04" /srv/crash-detector-wo2r-audit` returns EXACTLY ONE hit — that line.
No such variant exists in variants/WO-2R/, in the MANIFEST, or anywhere else.
The variant that actually measured it is `V21-innocent-host-broker-operator.patch`
(MANIFEST row V21, refused exit 1, CD-EGRESS-002 layer 2 on `operator`).
Three-places status: header b3 says "PARTIALLY CARRIED, MEASURED" and names NO variant;
register b3 says "the `operator` field is, which is measured to carry the archetypal case"
and names NO variant; contract b3 names a variant id that does not resolve.
=> (a) FAIL for the contract text as written; the underlying measurement DOES exist under a
different id, so the substance is true but the citation is unusable to an auditor.

### F-W6-02 (egress) — BOUNDARY COUNT DISAGREES WITH ITSELF INSIDE ONE REGISTER ENTRY
required-tests.yaml:864 (comment above the entry):
  "THIS CHECK HAS A DECLARED LIMIT, in NINE numbered boundaries (1..8, 8b and 9), stated
   identically in the header ..., in the execution contract, and below"
required-tests.yaml:894 (the entry's own negative_control.violation, ~20 lines later):
  "stated in full in the header ..., in the execution contract and here, in EIGHT boundaries:"
...and then enumerates (1)(2)(3)(4)(5)(6)(7)(8)(8b)(9) = TEN items.
Header of check_egress_no_broker.py also carries 1..8, 8b, 9 = TEN.
=> "EIGHT" is stale and is inside the load-bearing field (negative_control), not the comment.
This is the count the W6 dispatch itself inherited ("check_egress_no_broker declares eight").

### F-W6-03 (engine-no-witness-reach) — THE REGISTER STATES THE **SUPERSEDED, KNOWN-DEFECTIVE**
### TEXT OF BOUNDARY 5 AS IF IT WERE THE CURRENT LIMIT
This is the CD-PL-F71 shape: the SAME sentence doing OPPOSITE work in two of three places.

required-tests.yaml, CD-RT-003-ENGINE-NO-WITNESS-REACH negative_control, boundary (5),
lead sentence, stated flat and unquoted as the present tense of the limit:
  "(5) Only the ENGINE service's process is a WALK ROOT; the other five are RESOLVED so a
   rename is loud, but witness code reachable from cd-witness is correct and not a violation."

check_engine_no_witness_reach.py header, boundary 5, marks that identical wording as the
WITHDRAWN text and the CAUSE OF CD-PL-F62:
  " 5  THE WALK ROOTS ARE THE ENGINE CONTAINER SET, DERIVED BY IMAGE IDENTITY — AMENDED AT
      CD-D-055 CLOSING CD-PL-F62, AND THE PREVIOUS TEXT OF THIS BOUNDARY IS WHY.
      It used to read "ONLY THE ENGINE SERVICE'S PROCESS IS DERIVED AS A ROOT ... the other
      five services' entrypoints are RESOLVED but are not walk roots"."

contracts/execution/CD-RT-003-ENGINE-NO-WITNESS-REACH.md, boundary 5, agrees with the header:
  "5. **THE WALK ROOTS ARE THE ENGINE CONTAINER SET, DERIVED BY IMAGE IDENTITY.** *Amended at
   `CD-D-055` closing `CD-PL-F62`.* This boundary used to read "only the engine SERVICE's
   process is a walk root ... the other five are resolved""

=> Two of three places QUOTE the sentence as superseded; the register ASSERTS it. The register
does go on to say "AMENDED AT CD-D-055 CLOSING CD-PL-F62: the previous text of this boundary
distinguished services BY PURPOSE..." — but it never marks the LEAD sentence as being that
previous text, so a reader of the register reads a WITHDRAWN and MEASURABLY INCOMPLETE scope
statement as the current declared limit. This is a SCOPE disagreement (service-name scope vs
image-identity scope), not a wording nit: it is exactly the scope whose narrowness let
PL-U6b escape at be34fe4.

### F-W6-04 (engine-no-witness-reach + base_image_digest_pin) — A DECLARED, DELIBERATELY
### UNFIXED READER DEFECT IS DECLARED FOR ONE GUARD AND NOT FOR THE TWO GUARDS THAT SHARE IT
check_egress_no_broker.py boundary 9 (and register, and contract) declares the shared reader's
SILENT FLATTENING of a mapping nested beneath a sequence item's INLINE key — "A QUIET WRONG
PARSE, DECLARED HERE AT INCREMENT 6 UNDER CD-D-062 AND DELIBERATELY NOT FIXED" — and says in
terms:
  "NOT PROVED TO BE CARRIED ANYWHERE for the defect at large, either. Everything above is
   about THIS criterion's two artefacts. The reader is shared with
   check_base_image_digest_pin.py and check_engine_no_witness_reach.py, and this seat did
   NOT sweep their subjects."
MEASURED ABSENCE: `grep -n "flatten|FLATTEN|CD-D-062|inline key|READER-F05|READER-F08"` over
  tools/register/check_engine_no_witness_reach.py
  contracts/execution/CD-RT-003-ENGINE-NO-WITNESS-REACH.md
  tools/register/check_base_image_digest_pin.py
  required-tests.yaml lines 468-604 (the engine register entry)
returns ZERO hits in all four.
check_engine_no_witness_reach's declared limits are 1..6 and its boundary 4 inherits ONLY
egress boundary 8b (RecursionError), not boundary 9. check_base_image_digest_pin.py has no
DECLARED LIMIT section at all.
The engine check's subject IS deploy/compose.yaml, which contains sequences of mappings, so
the defect can fire on it; whether it can produce a FALSE CLEAN there is UNDETERMINED — nobody
swept it and nobody declared it. A reader of CD-RT-003-ENGINE-NO-WITNESS-REACH's three
place-texts cannot learn that this guard reads its subject with a reader known to mis-parse.

### F-W6-02 (STRENGTHENED) — "EIGHT" IS ALSO PRINTED BY THE CHECK ON EVERY CLEAN RUN
tools/register/check_egress_no_broker.py:1275 — inside the note the check emits on every run:
  "READ THE DECLARED LIMIT in this check's header before reading a clean run as proof of
   CD-AC-012: ... and the EIGHT boundaries say what it still does not see and which layer —
   if any — was MEASURED to see it."
MEASURED (my run, /tmp/w6/base, exit 0, 69 assertions): that note is printed verbatim.
So the count is wrong in the check's own OUTPUT and in the register's negative_control, and
right (implicitly, by enumeration 1..8/8b/9 = TEN) in the header body and the contract.

### F-W6-05 (no_blend) — THE CD-RULE-006 DISCHARGE SENTENCE SAYS THE OPPOSITE THING IN
### TWO OF THREE PLACES. THIS IS THE CD-PL-F71 SHAPE, VERBATIM.
tools/register/check_no_blend.py (header, closing the declared limit):
  "EVERY "CARRIES THIS" ABOVE HAS BEEN RE-MEASURED **AT THIS COMMIT**, not inherited from the
   increment that wrote it (CD-RULE-006)."
required-tests.yaml (comment above CD-RT-002-AST-NO-BLEND):
  "EVERY "CARRIES THIS" ABOVE WAS RE-MEASURED **AT THE COMMIT THAT WROTE IT**, not inherited
   (CD-RULE-006)."
contracts/execution/CD-RT-002-AST-NO-BLEND.md:
  "**EVERY "CARRIES THIS" ABOVE WAS RE-MEASURED AT THE COMMIT THAT WROTE IT**, not inherited
   (CD-RULE-006)."
"at this commit" = the CD-RULE-006 discharge. "at the commit that wrote it" = the INHERITED
measurement CD-RULE-006 exists to forbid, and the trailing "not inherited" then contradicts
its own subject clause. Two of three places carry the weaker/self-contradicting form.
I therefore RE-MEASURED THE CARRIERS MYSELF at 50fc231 (see F-W6-06) rather than accept either.

### F-W6-06 — CARRIERS I RE-MEASURED MYSELF AT 50fc231 (throwaway extraction /tmp/w6/base)
no_blend b1 (E01 shape), type-layer carrier:
  (DialMagnitude + DialMagnitude) -> TypeError: unsupported operand type(s) for +:
  'DialMagnitude' and 'DialMagnitude'   -- CARRIED, verbatim as declared.
no_blend b2 (E02 shape), type-layer carrier:
  sum([e,m]) -> TypeError: unsupported operand type(s) for +: 'int' and 'DialMagnitude'
  -- CARRIED, verbatim as declared.
no_blend b6, re-entry carrier:
  quantity_for both, add -> 0.5 NOT refused (as declared, PL-Q1a honest);
  DialMagnitude(dial_id="equity_crash", quantity=0.5) -> QuantityProvenanceMissing
  "a bare number (0.5) was offered as dial 'equity_crash''s magnitude" -- CARRIED.
no_blend b7, declared NOT CARRIED AT RUNTIME — I CONFIRMED THE RESIDUE IS REAL:
  observed_for_dial(dial_id=EQUITY, quantity=0.5, inputs_used=("fabricated",)) ->
  DialMagnitude -> number_for_dial_slot(EQUITY, m) -> 0.5 PUBLISHED. Declaration honest.
no_numeric_default b1, runtime carrier: I planted the dynamic-constructor Value on the
  missing_required branch of engine/evaluate.py. AST check EXIT 0 (as declared); the
  EVALUATE-MISSING probe raised
  AbsenceYieldedAValue: dial 'equity_crash' produced Value ... required inputs were not all
  present -- CARRIED, verbatim as declared.
no_numeric_default b3: plant in src/crash_detector/publication/summary.py -> EXIT 0;
  identical plant in src/crash_detector/dials/ -> EXIT 1, "F: unrecognised magnitude
  provenance". Contrast reproduces exactly.
no_execution_interface b3: docstring "The engine must send each instruction to the broker"
  -> EXIT 0; the same sentence without `must` -> EXIT 1 with the L3 finding. Reproduces exactly.
egress b9 (PL-X10a): parse_block_yaml("top:\n  - key:\n      sub: 1\n") ->
  {'top': [{'key': None, 'sub': '1'}]}. Reproduces exactly.
egress b1 topology carrier: tests/test_deploy_container_set.py -k internal -> 1 passed. MEASURED.
egress b5 extra_hosts, declared NOT PROVED TO BE CARRIED ANYWHERE — I CONFIRMED AND WIDENED IT:
  with `extra_hosts: ["api.ibkr.com:198.51.100.24"]` added to cd-collectors, ALL of
  check_egress_no_broker (0), check_no_execution_interface (0), check_lockfile_denylist (0),
  check_engine_no_witness_reach (0) AND the whole 83-test tests/test_deploy_container_set.py
  suite (83 passed) are clean. Nothing in the tree sees it. Declaration honest.
grant_matrix_live: `python3 tools/register/check_grant_matrix_live.py --root .` — the exact
  register `execute:` line — EXIT 3 PRECONDITION_NOT_MET, "the connection target is not set".
numeric_default contract b4 example DOES NOT REPRODUCE EXACTLY: the contract says
  "`observations.py:99` and `witness_resolver.py:168` are printed as NOTES on every clean
  run". MEASURED at 50fc231: observations.py:99 correct; the second note is
  src/crash_detector/serving/witness_resolver.py:**170**, not 168. Two lines off.
  (Header and register give no line numbers, so only the contract is wrong.)

### F-W6-07 (schema_closed) — THE SAME BOUNDARY NAMES THREE DIFFERENT CARRIER SETS IN
### THREE DIFFERENT PLACES, AND THE EXECUTION CONTRACT HAS NO DECLARED LIMIT AT ALL
The boundary: the schema constrains SHAPE, so it cannot see a blended number assigned to
`equity_crash.score` (a key that is legitimately a number).
PLACE 1 — required-tests.yaml, CD-RT-002-SCHEMA-CLOSED negative_control:
  "Its LIMIT is stated in the schema's own description and is unchanged: ... That case is
   covered by THE PUBLICATION PROVENANCE GATE (crash_detector.publication.dial_scalar),
   evidenced by CD-RT-002-TYPE-NO-ARITHMETIC."
PLACE 2 — contracts/public_envelope.schema.json:5 (the place PLACE 1 points to as canonical):
  "That case is refused by the two other independent instruments — THE SCORE TYPES define no
   arithmetic dunder and share no numeric base, and THE REGISTER'S AST NO-BLEND CHECK flags a
   single expression consuming both dial types"
PLACE 3 — tools/register/check_schema_closed.py header: NO declared-limit section. It says
  instead "The behavioural half is covered, and covered properly, by
  tests/test_envelope_contracts.py and tests/test_publication_refusal.py".
PLACE 4 — contracts/execution/CD-RT-002-SCHEMA-CLOSED.md: NO declared-limit section at all.
  Its only related sentence is "the types and the AST check both live in Python".

SUBSTANCE PROBLEMS:
(i) THE CARRIER NAMED IN THE SCHEMA IS ONE THAT WAS MEASURED NOT TO CARRY IT. The schema
    names "the register's AST no-blend check" as a carrier. That check's own register entry
    was DOWNGRADED FROM `scope: CLASS` TO `scope: INSTANCE` at WO-2R precisely because it
    cannot close this class (E01 and E02 both exit 0 on it), and check_no_blend's own
    boundaries 1, 2 and 6 say so with measured examples. The schema text is pre-CD-ASR-F01
    and was not re-measured.
(ii) The register's assertion that the schema limit "is unchanged" is true of the schema file
    but the register's OWN sentence substitutes a DIFFERENT carrier (dial_scalar / re-entry)
    for the two the schema names. Neither text mentions the other's carrier.
(iii) The carrier the register names (dial_scalar) is the one that was MEASURED FALSE at
    CD-PL-F54 and only re-closed by the re-entry (QuantityProvenanceMissing). The register
    does not say that; it points at CD-RT-002-TYPE-NO-ARITHMETIC, which does.
=> (b) verdict for this boundary: carrier is MEASURED in one place (register, via
   TYPE-NO-ARITHMETIC), ASSERTED-AND-REFUTED in the schema, and ABSENT in the check header
   and the execution contract. This is a CD-PL-F54/F59-class defect in the SCHEMA text.

### F-W6-08 (no_execution_interface) — THE NAMED STRUCTURAL CARRIER IS NARROWER THAN THE
### RESIDUE IT IS OFFERED FOR
All three places name the same "what carries the rest": this check + LOCKFILE-DENYLIST +
EGRESS-NO-BROKER + "the network posture itself (BLUEPRINT §2, §13): cd-engine, cd-public,
cd-private and cd-store have no egress at all, so a perfectly euphemised pathway INSIDE THE
ENGINE still has nowhere to send an order."
The residue (boundaries 1-5) is a euphemised or non-.py/.sql execution pathway ANYWHERE in
src/, db/, deploy/, tests/, tools/ — which includes cd-collectors, cd-witness and cd-review.
Those three are NOT in the four no-egress services (deploy/compose.yaml: cd-collectors and
cd-witness both declare `policy: ALLOWLIST`). The carrier sentence, read literally, does not
reach them.
What DOES reach them is `internal: true` on both networks — which IS measured
(tests/test_deploy_container_set.py::test_both_networks_are_internal, 1 passed, my run) —
but that sentence appears only in check_egress_no_broker's boundary 1, NOT in any of
CD-RT-012-NO-EXECUTION-INTERFACE's three place-texts. So the carrier as written is a
narrower claim than the residue it is offered for; the wider claim exists and is measured,
but in another guard's declaration.
Severity: LOW-MEDIUM. Not an unmeasured carrier — a mis-scoped one.

### F-W6-09 (grant_matrix_live) — CLASS SCOPE, NO DECLARED LIMIT, AND THE REGISTER HIDES
### THE PRECONDITIONS THAT MAKE THE COMMAND UNRUNNABLE AS WRITTEN
required-tests.yaml:603-616 is the ONLY delivered entry containing NO limit text of any kind
(grep for LIMIT / BOUNDAR / NOT PROVED / DOES NOT CATCH over the entry: zero hits).
It declares `scope: CLASS` and `execute: python3 tools/register/check_grant_matrix_live.py
--root .` — a line visually identical to the eight self-contained static checks.
MEASURED: that exact line at 50fc231 exits 3, PRECONDITION_NOT_MET.
The check's HEADER (not the register) discloses that it needs a LIVE PostgreSQL supplied by
five environment variables, a role that "may CREATE ROLE and CREATE SCHEMA, and may read
pg_authid — in practice that means the cluster superuser", and that it APPLIES THE SUBJECT
TREE'S MIGRATIONS to that database. It also discloses a genuine limit-shaped fact:
  "A connection that cannot read [pg_authid] is REFUSED rather than allowed to report an
   absence it did not observe: a check whose own privileges hide part of the catalogue is
   reporting on its blind spot."
NONE of that is in the register or, so far as the register reader can tell, anywhere.
This matters for (b) elsewhere: check_engine_no_witness_reach boundary 3 hands the DATA half
of CD-AC-003 to this check with the unqualified word "**CARRIED**, and it is a different
instrument on a different substrate" — in all three of its place-texts. That carrier is a
check that cannot be run without a live superuser session, and RTR-WO2-0001 does not exist.
The carrier is therefore MEASURABLE but, on the record in this tree, NOT MEASURED at 50fc231.

### F-W6-10 (engine b3) — THE HIGHEST-VALUE UNMEASURED CARRIER
tools/register/check_engine_no_witness_reach.py, boundary 3:
  " 3  IMPORTING WITNESS TYPES IS NOT READING WITNESS DATA, and this check does not claim
      otherwise. The auditor made that point about E06 itself. The data half of CD-AC-003 is
      CD-RT-003-GRANT-MATRIX-LIVE, which PROVES ``cd_engine`` holds no privilege of any kind
      on schema ``witness`` by any of seven routes, IN A REAL POSTGRESQL SESSION. CARRIED,
      and it is a different instrument on a different substrate."
required-tests.yaml (identical substance): "(3) IMPORTING WITNESS TYPES IS NOT READING
  WITNESS DATA ... that half is CARRIED by CD-RT-003-GRANT-MATRIX-LIVE, a different
  instrument on a different substrate."
contract (identical): "**CARRIED** by `CD-RT-003-GRANT-MATRIX-LIVE`, which proves `cd_engine`
  holds no privilege of any kind on schema `witness` by any of seven routes in a real
  PostgreSQL session."
All three places agree with each other — and all three use the UNQUALIFIED word CARRIED,
present tense, with no "MEASURED AT", no run reference, no evidence_ref.
COUNTER-EVIDENCE IN THIS TREE:
 * my run at 50fc231: the carrier's own declared command exits 3 PRECONDITION_NOT_MET.
 * governance/engineering/build-log/BL-20260819T193519Z-0049.yaml:144,151 —
   "CD-RT-003-GRANT-MATRIX-LIVE   clean 3   planted 3   (PRECONDITION_NOT_MET both arms)"
   "CD-RT-003-GRANT-MATRIX-LIVE's CONTRAST was again NOT re-run for want of a live store."
 * the carrier's own register entry declares NO limit and names evidence_ref RTR-WO2-0001,
   which does not exist.
Every OTHER carrier sentence in this corpus is qualified — "CARRIED, MEASURED", "PARTIALLY
CARRIED, MEASURED", or "NOT PROVED TO BE CARRIED ANYWHERE". This one is not, and it is the
one whose measurement is absent. Under CD-RULE-006 as the guards themselves state it
("where a boundary says another layer carries the residue, that layer was RUN and its refusal
OBSERVED"), boundary 3 is the one boundary in the corpus that does not meet its own rule.
I could not determine whether the carrier WOULD refuse; I determined only that the record in
this tree does not show it doing so at this SHA.

---
## BOUNDARY TABLE — (a) executable example · (b) carrier measured · (c) three places agree

Legend (b): M = named carrier, MEASURED (by the seat and/or by me) · NP = "NOT PROVED TO BE
CARRIED ANYWHERE", declared as such (correct under CD-RULE-006) · A = carrier ASSERTED, no
measurement found · n/a = no carrier named and none implied.

### CD-RT-001-AST-NO-NUMERIC-DEFAULT — 6
| b | (a) | (b) | (c) |
|1 dynamic constructor | YES, I RAN IT (AST 0 / runtime AbsenceYieldedAValue) | M (runtime layer, by me) | AGREE |
|2 helper trace | yes, not run | M (this check, deny-by-default) | AGREE |
|3 outside two tiers | YES, I RAN IT (0 in publication/, 1 in dials/) | n/a — contract alone says "nothing, at WO-2" | AGREE (contract more explicit) |
|4 class A off dial path | PARTIAL — contract cites witness_resolver.py:168, actual is :170 | n/a | contract example stale by 2 lines |
|5 computed-but-wrong | yes, not run | n/a — contract alone says "nothing yet" | AGREE |
|6 runtime/config/data | yes | M (same post-condition mechanism as b1) | AGREE |

### CD-RT-001-ABSENCE-RENDERS-UNKNOWN — 1
| type.__setattr__ residue | YES, in all 3 places | M (consumer boundaries; V04) | AGREE |

### CD-RT-002-TYPE-NO-ARITHMETIC — 1
| released float + admission door | yes (PL-Q1a) | M (re-entry, by me) / NP (door) | AGREE |

### CD-RT-002-AST-NO-BLEND — 7
|1 inter-procedural | YES (E01) | M (type layer, BY ME) | AGREE |
|2 dynamic attribute | YES (E02) | M (type layer, BY ME) | AGREE |
|3 RULE 2 allowlist | yes | M (type layer) | carrier dropped from the numbered item in register AND contract; recovered in each closing paragraph |
|4 scanned set | yes | n/a | AGREE |
|5 source not behaviour | yes | M (type layer) | carrier dropped from numbered item in register; recovered in closing |
|6 released float / exits many | YES (PL-Q4..Q9, V16a/b) | M (re-entry, BY ME); prior carrier explicitly WITHDRAWN | AGREE — exemplary |
|7 admission door | YES (V12) — I CONFIRMED it publishes 0.5 | NP, stated in terms | AGREE — exemplary |
| closing CD-RULE-006 attestation | — | — | **DISAGREE — F-W6-05** |

### CD-RT-002-SCHEMA-CLOSED — 1
| shape-not-value | none | contradictory: M (register) / A-and-refuted (schema) / absent (header, contract) | **DISAGREE — F-W6-07** |

### CD-RT-003-ENGINE-NO-WITNESS-REACH — 6 declared (+1 undeclared)
|1 static/override | yes | NP | AGREE |
|2 second process | none runnable | M partial / NP rest | AGREE |
|3 import != read | none | **A — F-W6-10, THE UNMEASURED CARRIER** | AGREE with each other, all three wrong together |
|4 YAML subset + reader | YES (R02/PL-T5, R08) | M | AGREE |
|5 walk roots | YES (V42/PL-U6b/V45/V46) | M (container-set test layer) | **DISAGREE — F-W6-03** |
|6 sys.path mutation | YES (V44) | M partial / NP for short-name import | AGREE |
|(9) reader flattening | — | — | **ABSENT FROM ALL THREE — F-W6-04** |

### CD-RT-003-GRANT-MATRIX-LIVE — 0 declared
| — | — | — | **NO LIMIT IN THE REGISTER; command unrunnable as written — F-W6-09** |

### CD-RT-005-PANEL-UNAVAILABLE-NEVER-AGREES — 4
|1 ceiling not operating window | yes | NP | AGREE |
|2 clock trust | YES (now_utc ten years back) | NP | AGREE |
|3 object.__setattr__ / forged Agrees | YES (PL-W5, PL-W3) | NP — "No layer was measured refusing a forged Agrees" | AGREE — exemplary |
|4 envelope window field | yes | NP | AGREE |

### CD-RT-012-NO-EXECUTION-INTERFACE — 6
|1 euphemism | history, not a runnable example | composite carrier, mis-scoped — F-W6-08 | AGREE |
|2 work_order suppression | none runnable | A (L2 named, no variant measured) | AGREE |
|3 L3 suppression | YES, I RAN IT — reproduces exactly | L1/L2 as third net | AGREE |
|4 motion chain >8 | none runnable | n/a | AGREE |
|5 not .py/.sql | none named; I MEASURED the extra_hosts case — nothing in the tree sees it | composite carrier, mis-scoped — F-W6-08 | AGREE |
|6 runtime | none | composite | AGREE |
| guard-file exclusion ("TWO PATHS ARE EXCLUDED") | — | — | in header + contract Subject; ABSENT from the register |

### CD-RT-012-LOCKFILE-DENYLIST — limit in 2 of 3 places
| "floor, not an oracle" | none | n/a | **ABSENT FROM THE REGISTER — sub-task** |

### CD-RT-012-EGRESS-NO-BROKER — 10 (1-8, 8b, 9)
|1 declaration not enforcement | yes | M (topology; I re-ran test_both_networks_are_internal) | AGREE |
|2 false registered destination | yes | NP | AGREE |
|3 purpose prose | contract cites **V-F04-04, which does not exist** (real one is V21) | M partial | **DISAGREE — F-W6-01** |
|4 vocabulary floor, per field | YES (E05, V20, PL-S3a, PL-S3c) | M per field | AGREE — this is the CD-PL-F59 repair, done properly |
|5 subject is two files | YES — I MEASURED extra_hosts: 4 guards + 83 tests all clean | NP for extra_hosts | contract drops the word MEASURED and the two sibling checks the header names |
|6 static read / override | yes | NP | AGREE |
|7 pending prose | YES (V29a/V29b) | M partial / NP for address literal | AGREE — exemplary |
|8 CLOSED, superseded by 8b | yes | — | AGREE |
|8b RecursionError | YES (R08) | declared, not repaired | AGREE |
|9 reader flattening | YES — I REPRODUCED PL-X10a EXACTLY | M partial (8/8 sweep) / NP for a future optional field / NP for the defect at large | AGREE — exemplary |
| boundary COUNT | — | — | **DISAGREE — F-W6-02 (EIGHT vs TEN)** |

TOTAL: 43 numbered boundaries across 11 register entries.

---
## BOUNDED SUB-TASK — scope: CLASS with no declared limit in the REGISTER

EXACTLY THREE delivered entries. This is independently confirmed by the implementing seat's
own open finding CD-ENG-WO2R-F29 (MEDIUM, "OPEN — ESCALATED, deliberately not taken"),
governance/engineering/build-log/BL-20260819T193519Z-0049.yaml:363-386, which names the same
three. It is OPEN at the delivered SHA.

Mechanical scan (entry = `- test_id:` through its `evidence_ref:`; case-insensitive):
  LIMIT / BOUNDAR / NOT PROVED / DOES NOT CATCH — all zero for:
    CD-RT-003-GRANT-MATRIX-LIVE  (line 603)
    CD-RT-012-LOCKFILE-DENYLIST  (line 821)
  and BOUNDAR/NOT PROVED zero, LIMIT present only as a delegating one-liner for:
    CD-RT-002-SCHEMA-CLOSED      (line 435)

### 1. CD-RT-012-LOCKFILE-DENYLIST — YES, IT MISDESCRIBES, AND THE SAME SENTENCE DOES
###    OPPOSITE WORK IN TWO PLACES (a second CD-PL-F71 instance)
check_lockfile_denylist.py header — the clause is a LIMIT, an incompleteness disclosure:
  "The denylist is explicitly a FLOOR and not an oracle, and the check says so in its own
   output RATHER THAN LETTING A READER ASSUME COMPLETENESS."
required-tests.yaml:826 (and, identically, the contract's Negative control) — the same clause
is the PREMISE OF A CLASS-WIDENING CLAIM:
  "The denylist is a floor and not an oracle, SO THE CLASS INCLUDES an SDK nobody has heard
   of: a distribution name carrying an execution token MUST FAIL as surely as a named one."
A register-only reader sees `scope: CLASS` plus "the class includes an SDK nobody has heard
of" and reads a closed class. It is not closed. MEASURED BY ME at 50fc231 in /tmp/w6/base:
  `quietbridge==1.2.3` appended to requirements.lock -> EXIT 0, PASS 16 assertions
  `ib-insync==0.9.86` appended to requirements.lock  -> EXIT 1
The guard catches (i) 61 named distributions and (ii) names carrying an execution token. A
broker SDK with a neutral name is neither, and NO PLACE-TEXT NAMES A CARRIER FOR IT.
The check itself prints the disclosure on every run ("the denylist carries 61 named
distributions and is a FLOOR, not an oracle"); the register does not carry it.

### 2. CD-RT-003-GRANT-MATRIX-LIVE — YES, AND MORE SERIOUSLY
See F-W6-09 and F-W6-10. The register entry conceals (i) that the declared command cannot
run without a live PostgreSQL and five named environment variables — MEASURED: exit 3;
(ii) that it needs a role that may CREATE ROLE, CREATE SCHEMA and read pg_authid, "in
practice ... the cluster superuser"; (iii) that it APPLIES THE SUBJECT TREE'S MIGRATIONS to
that database, i.e. it MUTATES a live store — the only register command that mutates anything;
(iv) the pg_authid blind-spot refusal, which is a limit in substance.
A register-only reader reads a self-contained `python3 tools/register/...` line
indistinguishable in form from the eight offline static checks, and a CLASS claim over seven
privilege routes with no boundary and no precondition. It is also the carrier that
CD-RT-003-ENGINE-NO-WITNESS-REACH's boundary 3 hands its residue to, in all three places,
with the unqualified word CARRIED.

### 3. CD-RT-002-SCHEMA-CLOSED — MISDESCRIBES BY DELEGATION AND BY NAMING A REFUTED CARRIER
The register carries one sentence and delegates: "Its LIMIT is stated in the schema's own
description AND IS UNCHANGED". The place it delegates to (public_envelope.schema.json:5) names
carriers that (a) differ from the ones the register itself then names, and (b) include the AST
no-blend check, which was measured not to close this class and whose own scope was demoted
CLASS -> INSTANCE for that reason. The execution contract has no declared limit at all.
See F-W6-07.

### VERDICT ON THE SUB-TASK QUESTION
Yes — for all three, a reader relying only on the register is misdescribed, and the
misdescription is in the direction of over-claiming (a CLASS scope with an undisclosed
residue). For LOCKFILE-DENYLIST and GRANT-MATRIX-LIVE the residue is real and I measured it.
For SCHEMA-CLOSED the residue is real but is covered elsewhere; what is wrong is the
signpost.
