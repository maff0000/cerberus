# Project Lead reconciliation probes — WO-2R

**Nothing in this directory is executable and nothing in it may become executable** (`PBG-ASSURE-001`).
Every file is stored with a `.txt` suffix and mode `644`, as data for a reader to retype. There is no
runner, no wrapper and no harness here, and there may not be one.

**Nothing in this directory is assurance.** These are probes the *Project Lead* wrote while
reconciling an Engineer seat's return. Reconciliation is the Project Lead checking that what a seat
reported is what the repository does. It is not an independent verdict and it does not pre-empt one
(`PBG-SOD-001`, non-waivable). `CD-ASR-WO2-02` decides.

**Everything written down here is, from the commit that added it, part of the KNOWN SET.** It proves
nothing about any class. The next auditor's exclusion set is the union of three lists, and a variant
that appears on any of them is not evidence:

| List | Where | Count |
|---|---|---|
| The WO-2 auditor's escapes | `governance/assurance/WO-2/ESCAPED-VARIANTS-KNOWN-SET.md` | 10 |
| The Engineer's own variants | `variants/WO-2R/MANIFEST.md` (on the lane) | 11 |
| The Project Lead's probes | this directory | 18 |

## What is here

| File | Probes | Outcome |
|---|---|---|
| `PL-Q1-Q3-coercion-and-class-mutation.py.txt` | repr text leak; `math.fsum`, `round`, `operator.index`, `Decimal`, `int`, `complex`, `format`, `str`→`float`; `type.__setattr__` installing `__add__` | eight refused; the repr leak and the class mutation are not |
| `PL-Q4-Q6-launder-rewrap-publish.py.txt` | launder to a float, re-wrap as a magnitude of ONE dial, publish | **none refused** — this is what disproves boundary 6 |
| `PL-Q9-flavour-free-repr-launder.py.txt` | one plausible module that defeats the static arm and the runtime arm together | **not refused; publishes a blend of 0.4 and 0.6 as `equity_crash` 0.5** |

The finding is `CD-PL-F54` (HIGH), recorded in full in
`governance/engineering/build-log/BL-20260819T105500Z-0024.yaml`. The two probes that *are* caught —
the same laundering spelled with the dial names in scope — are recorded in that entry too, because a
finding that does not also show the guard working is not a measurement, it is a complaint.
