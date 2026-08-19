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

## The six invariants

| id | asserted |
|---|---|
| `CD-EGRESS-001` | cd-engine, cd-public, cd-private, cd-store: policy `NONE`, empty `hosts`, attached only to `internal: true` networks. |
| `CD-EGRESS-002` | No host — registered, allowlisted or pending — is a broker, exchange, order-routing endpoint or trading API; and no registered destination's `operator` is one. |
| `CD-EGRESS-003` | Every service declares an `x-egress` block with a valid `policy`, a `hosts` list and an `enforced_by`. |
| `CD-EGRESS-004` | **Deny by default.** Every allowlist entry is character for character the `host` of a destination registered for that service. |
| `CD-EGRESS-005` | **Closed key sets.** `x-egress` = {policy, hosts, pending, enforced_by}; a destination = {id, host, operator, purpose, declared_in, services}; the registry document = {version, contract, destinations}. Asserted by equality, never by a blacklist. |
| `CD-EGRESS-006` | A registered destination is a well-formed, unique, attributable DNS hostname in a POSITIVE permitted shape, with an operator, a purpose and a `declared_in` clause, registered only for services that exist and declare `ALLOWLIST`. |

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
4. **The vocabulary and the denylist are a floor, not an oracle.** A brokerage on nobody's
   list, under a name carrying no concept token, passes layer 2. It does not pass layer 1
   unless a human registers it: the escape now costs a signed edit to a reviewed registry
   file rather than a quiet line in an allowlist. *Carried, measured:* `V-F04-03` registers
   the address itself and is refused by `CD-EGRESS-006`, exit `1`.
5. **The subject is two files.** Egress obtained by any other means is outside this check:
   `extra_hosts`, a `RUN curl` in a Dockerfile, a sidecar, host networking, a runtime
   `--add-host` or `--network`, or a proxy reached over an internal network. *Partially
   carried:* the four no-egress services' network attachment is asserted here. For
   `extra_hosts` specifically, **NOT PROVED TO BE CARRIED ANYWHERE** — raised against this
   seat's own work as `CD-ENG-WO2R-F12` and owed at WO-3 with the egress lane.
6. **It is a static read of two files at one commit.** No runtime, no image, no running
   container, no packet. A compose override file the check never sees is outside the subject.
   **NOT PROVED TO BE CARRIED ANYWHERE** at WO-2.

**DO NOT READ A CLEAN RUN OF THIS CHECK AS PROOF THAT NO EXECUTION PATHWAY EXISTS.** It was
clean for `E05`.

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
unknown key in an `x-egress` block or in a registry entry; and any egress at all granted to
those four services by policy, by hosts or by attachment to a network that is not
`internal: true`.

The class is **deny by default**: the violation is an entry *nobody declared*, not an entry
that *matched something*.

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
