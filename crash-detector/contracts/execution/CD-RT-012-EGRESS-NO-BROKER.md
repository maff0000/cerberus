# Execution contract — CD-RT-012-EGRESS-NO-BROKER

**CD-AC-012** · No execution pathway exists · obligation **MANDATORY** · scope **CLASS** ·
delivered in **WO-2**

This document exists because `REQUIRED-TEST-REGISTER-CONTRACT-v1` check 3 requires every
declared test to name an execution contract that RESOLVES. It states how this test is run
and what its exit codes mean. **It states no result.** The register carries obligations;
status is computed by the validator from the register, the PID and append-only run records,
and there is no field anywhere in this chain in which an author could write a verdict.

## The proposition

cd-engine, cd-public, cd-private and cd-store have no egress at all, and no egress allowlist
anywhere reaches a broker — because no egress allowlist anywhere may name a destination that
is not registered, for that service, in `deploy/egress-destinations.yaml`.

**Rewritten at WO-2R increment 3, closing `CD-ASR-F04` (MEDIUM).** The proposition previously
read "no egress allowlist anywhere *names* a broker", and an independent auditor refuted it
by execution: `198.51.100.24` in place of `api.ibkr.com` exited `0`, because the guard
recognised brokers by NAME and an address has no name to recognise. The Product Owner ruled
(PO-GATE-REVIEW-WO2-0001, Ruling 2) that the check "must resolve what an entry REACHES, not
what it is spelled as", and that it must be closed before any WO-3 egress lane inherits it.

**Extended at WO-2R increment 3b, closing `CD-PL-F59` (MEDIUM).** Increment 3 closed `hosts`
and left the adjacent `pending` field carrying only the broker vocabulary — the layer
`CD-ASR-F04` had already proved insufficient. The Project Lead measured the consequence:
`api.ibkr.com` in cd-collectors' `pending` was refused, and `198.51.100.24` **in the same
slot passed**, exit `0`. The proposition therefore now also holds that **no `pending` entry
anywhere may declare a destination at all**, by `CD-EGRESS-007`. The residue that closure
does *not* cover is declared at boundary 7 and is not claimed to be carried anywhere.

## Command

```
python3 tools/register/check_egress_no_broker.py --root .
```

Run with the working directory set to **the root of a subject tree the auditor extracted
itself** — `git archive <sha> | tar -x -C <tmpdir>`, never the Engineer's worktree. The line
above is verbatim: no path fixing, no editing, no wrapper. There is no run-everything
harness in this repository and there may not be one, because an auditor verifying through a
harness the project wrote is verifying the harness (`PBG-ASSURE-001`).

## Subject

**Two files, both in the subject tree.**

* `deploy/compose.yaml` — the two networks, the per-service egress posture and every
  allowlist entry.
* `deploy/egress-destinations.yaml` — the destination registry: the admissible set. An
  ABSENT registry is a precondition failure (exit `3`), never a pass — with no registry
  there is no admissible set, and a check that read a missing file as "nothing is
  registered, therefore nothing is wrong" would be defeated by deleting it.

## Why it is asserted this way

Source and dependencies are only two of the three ways an order could leave. The third is the
network, and a service that can reach the internet can reach a broker whatever its code says.

**And why DENY BY DEFAULT rather than a better broker matcher.** A matcher recognises
spellings, and the spelling that defeated the previous matcher was an IP address. The next
one is a CIDR, a URL, an unregistered hostname, a punycode host, a hex-dotted address or a
container-network service name. Adding an IP-literal rule would reproduce the same defect one
level up. So the question the check asks is inverted: not "does this entry look like a
broker?", which is undecidable offline, but "did somebody DECLARE this destination, for this
service, with an operator, a purpose and the clause of product intent that authorises it?",
which is set membership. An IP literal then stops being a spelling to catch and is simply not
a destination anyone declared — the check performs **no recognition at all** on an
unregistered entry, so there is no pattern to write around.

**Live resolution is prohibited and that is deliberate** (`CD-PL-F48`, and the WO-2R dispatch
in terms). A check whose verdict depends on DNS or on any network call is not reproducible,
cannot be run offline by an auditor, and therefore cannot be a gate. This check opens no
socket. "What an entry reaches" is decided from data in the tree.

**Both layers survive and neither is sole.** Layer 1 (`CD-EGRESS-004`) decides what nobody
declared. Layer 2 (`CD-EGRESS-002` — the broker concept vocabulary and the known-operator
denylist) is applied to every registered destination's `host` and `operator`, to every
allowlist entry as written, and to every `pending` entry, and decides what somebody declared
and should not have. `api.ibkr.com` written into an allowlist today fails both.

## The seven invariants

| id | asserted |
|---|---|
| `CD-EGRESS-001` | cd-engine, cd-public, cd-private, cd-store: policy `NONE`, empty `hosts`, attached only to `internal: true` networks. |
| `CD-EGRESS-002` | No host — registered, allowlisted or pending — is a broker, exchange, order-routing endpoint or trading API; and no registered destination's `operator` is one. |
| `CD-EGRESS-003` | Every service declares an `x-egress` block with a valid `policy`, a `hosts` list and an `enforced_by`. |
| `CD-EGRESS-004` | **Deny by default over `hosts`.** Every allowlist entry is character for character the `host` of a destination registered for that service. |
| `CD-EGRESS-005` | **Closed key sets.** `x-egress` = {policy, hosts, pending, enforced_by}; a destination = {id, host, operator, purpose, declared_in, services}; the registry document = {version, contract, destinations}. Asserted by equality, never by a blacklist. |
| `CD-EGRESS-006` | A registered destination is a well-formed, unique, attributable DNS hostname in a POSITIVE permitted shape, with an operator, a purpose and a `declared_in` clause, registered only for services that exist and declare `ALLOWLIST`. |
| `CD-EGRESS-007` | **A pending entry declares an OMISSION, not a destination.** `pending` is present and is a LIST; every entry is a mapping whose key set EQUALS {`declared_in`, `blocked_by`}, both non-empty scalars. This is layer 1 over `pending`, and deliberately **not** `CD-EGRESS-004`'s registry — see below. |

### Why layer 1 over `pending` is not the destination registry

`CD-EGRESS-007` was added closing `CD-PL-F59`, which is `CD-ASR-F04` surviving one field
across: once `CD-EGRESS-004` closed `hosts`, `pending` still carried only the broker
vocabulary, so `api.ibkr.com` written there was refused and `198.51.100.24` **in the same
slot passed**. The obvious repair — require a pending entry to name a registered destination
— is incoherent, because a pending entry exists *precisely because the host is unknown*. It
would be either unsatisfiable or would force an engineering seat to invent the hostname this
project recorded as owed, which `CD-RULE-003` and `PBG-AUTH-005` forbid.

So the closure takes the field's own meaning seriously. A pending entry is the record of an
**absence**: what authorises the future endpoint (`declared_in`) and why the host is not
written (`blocked_by`). **A host is the one thing a pending entry cannot carry**, so the
admissible key set contains no field that can hold one, and it is asserted by *equality*.
`host:`, `endpoint:`, `url:`, `address:`, `target:` and every key nobody has thought of fail
the same clause, without the guard examining the value at all.

*"A pending entry grants nothing"* is true and is not a defence: at WO-2 an allowlist entry
grants nothing either, because both networks are `internal: true`. This check is about
**declarations**, and `pending` is the declaration the WO-3 enforcement lane inherits.

## Declared limit (`CD-RULE-004`)

Stated identically here, in the header of `tools/register/check_egress_no_broker.py` and in
the register entry's `negative_control`. Before this rework **this check had no written
boundary at all**, and the auditor said so in terms — "not covered by any declared limit" —
which is half of why `CD-ASR-F04` exists. Every hand-off names a layer that was **measured**,
or says **NOT PROVED TO BE CARRIED ANYWHERE** (`CD-RULE-006`).

1. **It is a DECLARATION and stops no packet.** Compose has no per-host egress primitive; the
   enforcement lane is owed at WO-3. *Carried, measured:* the topology — both networks are
   `internal: true` and every service is attached only to them. Asserted here by
   `CD-EGRESS-001` for the four no-egress services, and by
   `tests/test_deploy_container_set.py::test_both_networks_are_internal` for both networks.
2. **A registered destination is a human claim, and a false one is not detectable from this
   tree.** A hostname that in fact resolves to a brokerage edge cannot be recognised without
   the network, and the network is prohibited. **NOT PROVED TO BE CARRIED ANYWHERE.** What
   the structure buys is *attribution* — a named line, an operator, a purpose, an authorising
   clause, reviewable before it is reachable — not detection. That is a smaller claim than
   "the check resolves what an entry reaches", and it is the true one.
3. **`purpose` prose is not judged.** *Partially carried, measured:* the `operator` field is
   judged by the same vocabulary and denylist as the host, so the archetypal case fails on
   the operator (variant `V-F04-04`). Prose is left to the human reviewer because this
   project's own documentation says on every other page that it places no orders, and a guard
   that fired on its own charter would be switched off.
4. **The vocabulary and the denylist are a floor, not an oracle — and layer 1 is not one
   rule. It is a different rule in each field, so say which.** A brokerage on nobody's list,
   under a name carrying no concept token, passes layer 2 *in every field*. What stops it
   then depends entirely on where it is written:
   * in `hosts` — layer 1 is `CD-EGRESS-004`, deny by default over the registry. The escape
     costs a signed edit to a reviewed registry file rather than a quiet allowlist line.
     *Carried, measured:* `E05` puts `198.51.100.24` in cd-collectors' allowlist and is
     refused, exit `1`, `CD-EGRESS-004`.
   * in the **registry** — layer 1 is `CD-EGRESS-006`'s positive hostname shape. *Carried,
     measured:* `V20` registers the address itself and is refused, exit `1`, `CD-EGRESS-006`.
   * in `pending` — layer 1 is `CD-EGRESS-007`, the closed entry shape, **not** the registry.
     *Carried, measured:* `PL-S3a` (a bare `198.51.100.24` pending entry) and `PL-S3c` (the
     same address on a `host:` key inside a pending mapping) are both refused, exit `1`,
     `CD-EGRESS-007`.
   * in `pending` **prose** — **there is no layer 1.** See boundary 7. Do not read this
     boundary as covering it.

   **Correction, and why this boundary is rewritten (`CD-PL-F59`, `CD-RULE-006`).** As first
   written it said flatly that a brokerage passing layer 2 "does not pass layer 1 unless a
   human deliberately registers it", naming no field. For `pending` that was *measurably
   false*: there was no layer 1 over `pending` at all, so an entry passing layer 2 there
   passed entirely, at the cost of one quiet line and no registry edit. A boundary naming a
   compensating layer that does not compensate is worse than no boundary — it spends an
   auditor's attention where the defect is not. The sentence is not softened here; it is made
   field-specific, and each field's carrier is named with the variant that measured it.
5. **The subject is two files.** Egress obtained by any other means is outside this check:
   `extra_hosts`, a `RUN curl` in a Dockerfile, a sidecar, host networking, a runtime
   `--add-host` or `--network`, or a proxy reached over an internal network. *Partially
   carried:* the four no-egress services' network attachment is asserted here. For
   `extra_hosts` specifically, **NOT PROVED TO BE CARRIED ANYWHERE** — raised against this
   seat's own work as `CD-ENG-WO2R-F12` and owed at WO-3 with the egress lane.
6. **It is a static read of two files at one commit.** No runtime, no image, no running
   container, no packet. A compose override file the check never sees is outside the subject.
   **NOT PROVED TO BE CARRIED ANYWHERE** at WO-2.
7. **The prose inside a pending entry is not judged for addresses.** `CD-EGRESS-007` closes
   the *shape* of a pending entry, so no **field** in one can hold a destination; it does not
   judge the free text of `declared_in` and `blocked_by`, which exist to be read by a human
   reviewer. *Measured example:* `blocked_by: "CD-D-005; the source will be 198.51.100.24
   once ruled"` leaves the check at exit `0`, PASS 69 assertions (variant `V29a`).
   *Partially carried, measured:* layer 2 is applied to the flattened text of every pending
   entry, so the archetypal case fails on the name — the same sentence carrying
   `api.ibkr.com` is refused, exit `1`, `CD-EGRESS-002` (variant `V29b`). **For an address
   literal in prose specifically, NOT PROVED TO BE CARRIED ANYWHERE.**
   *Why it is not closed:* closing it would mean recognising which text tokens look like
   network endpoints, which is the spelling recognition that `CD-ASR-F04` and `CD-PL-F59`
   both are. This is boundary 3 (`purpose` prose) drawn again for the same reason. What is
   different from `CD-PL-F59` — and an auditor should weigh it sceptically — is that after
   `CD-EGRESS-007` a pending entry has no host-bearing field, so an address in prose is a
   *mention* and not a *declaration*. That is an argument about what a future reader would
   do. **It is recorded as an argument and is not claimed to be a layer.**
8. **CLOSED, and replaced by the narrower boundary 8b.** This boundary read *"a document shape
   exists on which this check does not terminate, so it returns no verdict at all"*, because
   `tools/register/_yamlmin.py` re-entered a parse loop at a cursor that had not moved.
   Repaired at the reader under `CD-DISPATCH-WO2R-READER` (`CD-PL-F61`, confirming the
   seat-raised `CD-ENG-WO2R-F14`), by making progress a property of the loops rather than of
   the documents they happen to meet: every delegated cursor goes through `_advance`, which
   refuses one that did not move and names the line, and each loop carries an iteration budget
   that fails closed if a future edit ever breaks that.
   **The examples that used to hang now return a verdict.** The three lines `top:` /
   `  - key:` / `      - nested`, and variant `V30` through this check's own subject, both give
   exit `3` `PRECONDITION_NOT_MET` naming the line that could not be read.
   **Correction, superseding rather than editing (`PBG-CONT-003`):** the earlier text said the
   reader was shared with **one** other check. It is shared with **two** —
   `tools/register/check_base_image_digest_pin.py` **and**
   `tools/register/check_engine_no_witness_reach.py` — so **three** declared gate commands
   returned no verdict on the same input, not two. Raised as `CD-ENG-READER-F01`.

8b. **A document nested deeper than the interpreter's recursion limit raises `RecursionError`
   rather than a stated refusal.** It **terminates** — this is neither a hang nor a false clean
   — but it reports a Python traceback instead of a line number and a statement of what could
   not be read, and it exits `1` rather than the `3` this check uses for *"I could not read my
   subject"*.
   **Measured example:** ~600 levels of block mapping under `cd-collectors`' `pending`. The
   exact generator is row `R08` of `variants/WO-2R/MANIFEST.md`. Observed exit `1`,
   `RecursionError: maximum recursion depth exceeded`, **identically before and after** the
   reader repair, on all three checks that share the reader.
   **Deliberately not repaired.** Converting it to `YamlSubsetError` would move this check from
   exit `1` to exit `3` on an input that already has a verdict, and the reader dispatch puts a
   verdict change out of bounds and instructs the seat to report rather than take it. Raised as
   `CD-ENG-READER-F02` for a ruling.

**DO NOT READ A CLEAN RUN OF THIS CHECK AS PROOF THAT NO EXECUTION PATHWAY EXISTS.** It was
clean for `E05`, and after `E05` was closed it was still clean for `PL-S3a` — the same
address, one field across, in `pending`. That is `CD-PL-F59`, and it is why boundary 4 above
carries a correction and boundaries 7 and 8 exist.

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

## Negative control

Any entry in any service's egress allowlist that is **not a registered destination for that
service**; any registered destination whose `host` or `operator` is a broker, exchange or
order-routing operator; any registered destination that is not a well-formed, attributable
DNS hostname, or that is registered for cd-engine, cd-public, cd-private or cd-store; any
unknown key in an `x-egress` block or in a registry entry; **any `pending` that is not a
list, and any pending entry that is not a mapping declaring exactly `declared_in` and
`blocked_by` as non-empty scalars**; and any egress at all granted to those four services by
policy, by hosts or by attachment to a network that is not `internal: true`.

The class is **deny by default**: the violation is an entry *nobody declared*, not an entry
that *matched something*. In `hosts` that means an entry nobody **registered**; in `pending`
it means an entry that is not the declared **shape** — because a pending entry records that
a host is *not known*, so there is nothing to register and no field that may hold one.

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
