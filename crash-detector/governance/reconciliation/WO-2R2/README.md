# WO-2R2 — Project Lead reconciliation probes

**NOTHING IN THIS DIRECTORY IS EXECUTABLE, AND NOTHING IN IT IS ASSURANCE.** These are the probes
the Project Lead ran to reconcile a seat return — its own drivers, on its own pristine
`git archive` extractions, outside every governed worktree. They are stored as `.txt` so that they
are DATA (`PBG-ASSURE-001`). Reconciliation is not certification (`PBG-SOD-001`, non-waivable).

They are recorded for the same reason the WO-2R probes were (CD-D-047): a probe that exists only in
a seat's conversation is not project state (`PBG-CONT-007`), and the next Assurance seat needs the
exclusion set in full so that it can devise routes nobody here has tried. **From the moment they are
written down they prove nothing about any class** — they are a regression floor and an exclusion
list, and fitting a guard to them is worthless.

| probe | what it attacks | measured at 7ac1574 |
|---|---|---|
| PL-Z0 | the false-positive arm: same-dial MEAN of two equity magnitudes | **works** — 0.8 |
| PL-Z1 | `ASR2-002-A` verbatim: a callable `using` carrying a cross-dial mean | **REFUSED** — `UndeclaredReduction`, exact-type check on `reduction` |
| PL-Z2 | the same route, every identifier renamed and the door aliased | **REFUSED** — identical. THE RENAME TEST, taken by the PL |
| PL-Z3 | the ADMISSION door reached from a module in the scanned set, citing TRUE source ids | runtime **NOT REFUSED** (publishes 0.5); `check_no_blend` **FAIL, 2 RULE 4 violations** |
| PL-Z3b | PL-Z3 with the door name assembled at runtime | runtime **NOT REFUSED** (publishes 0.5); `check_no_blend` **PASS, 5292 assertions**; `check_no_numeric_default` **PASS** |
| PL-Z4 | one stateful `ContributionModel` injected into BOTH `DialSpec`s | **NOT REFUSED** — monetary publishes **0.5** from equity 0.9 / monetary 0.1 |
| PL-Z5 | `ASR2-001-A`'s `fold(on_unknown=0.0)` | still returns **0.0** — declared, and pinned by a test |
| PL-Z6 | presenting that number as a dial | **REFUSED** — `DialPresentationRefused`; `NotShown` has no numeric field |

PL-Z3 and PL-Z3b land INSIDE declared boundary 7 of `check_no_blend.py` (residues iii and the
admission-door residue) and were run to MEASURE a declaration rather than to accept it. PL-Z4 is an
independent replication of the seat's own `CD-ENG-WO2R2-V05` / finding `CD-ENG-WO2R2-F03`, written
from the seat's prose without using the seat's driver, and it **CONFIRMS IT**.

Full account, with the numbers and the disposition: `governance/engineering/build-log/`
`BL-20260819T222917Z-0043.yaml`.
