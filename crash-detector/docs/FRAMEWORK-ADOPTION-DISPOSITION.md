# PO disposition — framework adoption for DEV, blockers disclosed
date: 2026-08-19 · authority: Product Owner (Trinity), under Matt ratification "issues dealt with as we go"

This project pins PBGv2 release v2.0.0-alpha.1-r1, source commit 681900dc12cf, distribution
digest sha256:dee8eaca3a9e3837... — verified on this filesystem: 113/113 INTEGRITY checks OK.

PROVENANCE.json in pbg/ says suitable_for_adoption: FALSE. That is retained, visible, and
overridden FOR THIS DEV PROJECT ONLY by explicit PO disposition, on these grounds:
1. The blockers demand proof of the exact paths this adoption exists to prove (pl_boot,
   engineer_dispatch, assurance_dispatch) — the crash detector IS the proving application
   (PBGv2 PID v1.1, completion item 8: the cold-start proof).
2. Two blockers concern the opencode runtime, which is not installed anywhere on this estate.
3. This project is Class C, ADVISORY, DEV. Per the ratified consequence rule no preventive
   gate applies; production promotion still requires R2D2 (party-independent) per the declared
   assurance policy in docs/PID.md §8 — distribution assurance lands there.
4. Framework validation RED at build time consists of known, disclosed, open residuals carried
   by the PBGv2 PO (future-stamped build-log entry; the canonical failure set).
This file must remain in the repository. If this project is ever promoted toward production
with these blockers still open, that promotion is BLOCKED until R2D2 has ruled on them.
