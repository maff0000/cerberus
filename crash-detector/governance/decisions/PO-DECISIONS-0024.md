# PO decisions — WO-3 base and sequencing ruled; the register repair proceeds; the source set is HELD for Matt
date: 2026-08-23 · authority: Product Owner (Trinity)

The WO-3 scope stopped correctly at product content. Three of its four questions are mine;
the hinge (Q25, the source set) is Matt's and is held.

**1. Q24 — WO-3 BRANCHES FROM the frozen `be0b355`. The circle is resolved.** The
Project Lead's reading is correct and I rule on it: the SHUT gate governs ACCEPTANCE of
CD-AC-002/CD-AC-005, not whether descendant work may branch. A lane frozen for audit is an
immutable BASE, not a prohibition on building forward from it. WO-3 takes `be0b355` as its
base, `be0b355` itself stays frozen and unmodified, and the gate closes when WO-3 delivers
the DETECTED tier onto that line — no circle, because "frozen base" and "withheld
acceptance" are different facts. The seat was right not to unfreeze on its own inference;
this ruling is the authority it waited for.

**2. Q27 — INCREMENTS 14 AND 15 PROCEED NOW, sequential single-seat.** They are blocked on
nothing product-shaped, and both are on the path regardless:
- **Inc 14 — the Required Test Register repair, and it is not cosmetic.** P2 measured that
  the register is INVALID (six schema errors, all in CD-AC-002/CD-AC-005) and has therefore
  **never computed a status for any criterion** — it has been carried through ten gates
  returning nothing, with the adversarial auditors as the true floor (which is exactly why
  the campaign held: IMP-015's doctrine, "the auditor is the floor," was load-bearing in
  fact). Repair the schema to the contract (violation/evidence_ref, not the planted_*
  fields), and — folded in because P3 is masked by P2 — refresh the stale PID pin
  (441d8316 → live 538e30f3) so fixing P2 does not surface P3 as a false regression. The
  register's 16 rows go to 17 (CD-AC-017 DERIVES — in the census, so the amendment path is
  spent; CD-AC-018 STRENGTHENS CD-AC-004), closing the 3/4 carriage of CD-D-172.
- **Inc 15 — publication / heartbeat / probe / staleness / health**, per the plan. Pure
  construction, no product content.

**3. Q26 — the alert channel gets a DEFAULT, adjustable by Matt, not a hard stop.** The
detector is advisory (D1): alerts surface on the publication surface (the page) and a
machine-readable state endpoint, with NO external push channel until Matt names one. This
keeps inc 15 unblocked while leaving the outward channel Matt's to choose later. If Matt
wants a specific channel (email, Discord, a webhook), that is a one-line addition when he
says so.

**4. Q25 — THE SOURCE SET IS HELD FOR MATT. Increment 16 (the sources — the hinge) does
NOT dispatch until Matt names the set.** This is product meaning (CD-D-005, PO-PRODUCT-0001)
and it is his. I explicitly honour the PBG-PID-003 trap the scope named: **no seat reads the
indicator list off the ARGUS /playbook page and calls this answered.** The shape is
inheritable; the list is not. Matt may base the set on the playbook's 20-indicator / 10-
category / 8-combination lineage or define fresh — but it must be his naming, per indicator:
code, calculation, dial binding, criticality, weight, window, and any combination model.
That naming is now the one thing gating the dials' first real numbers and the page.

**5. Sequence:** inc 14 (register repair + PID pin) → inc 15 (publication layer) →
**HOLD for Matt's source set (Q25)** → inc 16 (sources) → inc 17 (CD-AC-017 + post-admission
binding) → inc 18 (CD-AC-018 divergence + forgery-detection obligation) → the WO-3 gate,
where CD-AC-002/CD-AC-005 finally have a valid register AND a built detection tier to close
against. Standing: lane frozen at be0b355, CD-AC-002 AMBER / CD-AC-005 RED unmoved, system
safe to leave running sequentially.
