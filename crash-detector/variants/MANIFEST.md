# VARIANT CORPUS — INDEX

`CD-DISPATCH-WO2R2-ENGINEER` and the WO-2R dispatch before it both refer to
`variants/MANIFEST.md`. **No such file existed at `50fc231`** — the corpus manifest was
written one level down, at `variants/WO-2R/MANIFEST.md`, and the reference has been read as
though the two were the same file. This index is that file, created rather than assumed, and
it changes nothing about either manifest below.

Reported as a small record defect rather than silently worked around
(`CD-ENG-WO2R2-F01`): a dispatch pointing at a path that does not exist costs the next seat
the same minutes it cost this one.

| tree | manifest | seat | contents |
|---|---|---|---|
| `variants/WO-2R/` | [`variants/WO-2R/MANIFEST.md`](WO-2R/MANIFEST.md) | `CD-ENG-WO2R-01` | 70 `git apply`-able patches + 2 probe records. Denominator SETTLED at 70 by `CD-ASR-WO2-02`; the "71" in that manifest is a transcription defect — the work was done, the count was mis-stated. |
| `variants/WO-2R2/` | [`variants/WO-2R2/MANIFEST.md`](WO-2R2/MANIFEST.md) | `CD-ENG-WO2R2-01` (increments 1–2), `CD-ENG-WO2R2-02` (increment 3) | **FOURTEEN rows in three trees.** `CLASS-1/` four: `V01`, `V03`, `V04` refused; **`V05` NOT REFUSED and open**; `V02` withdrawn and its id left unused. `CLASS-2/` five: `V06`–`V08` refused, **`V09`'s premise REFUTED by its own counterfactual**, **`V10` MEASURED OPEN at both SHAs**. `CD-AC-012/` five: `V11`–`V15`, all refused, **`V11` labelled a VOCABULARY result** and `V12`/`V15` carrying counterfactuals that narrowed the claims made for them. |

| `variants/WO-2R3/` | [`variants/WO-2R3/MANIFEST.md`](WO-2R3/MANIFEST.md) | `CD-ENG-WO2R3-01` .. `-06`, increments 1–8 | **ADDED AT WO-2R3 INCREMENT 8 (`F-06-M`). THIS INDEX WAS BLIND TO AN ENTIRE TREE FOR SEVEN INCREMENTS.** MEASURED at the increment-8 tip with `find`, not copied: **45 entries — 28 `git apply`-able patches (`V16`..`V43`), 12 `.py` probes and 4 `.sh` probes (`P-A`..`P-O`), and that tree's own `MANIFEST.md`.** **THE PROBES ARE WHY THE SENTENCE AT THE FOOT OF THIS PAGE HAD TO BE CORRECTED.** That tree's manifest states each probe's question and its literal command line, and says of every one that it REPORTS and is not a carrier (`CD-RULE-006`). |

**Not indexed here, because they are not this seat's to index and must not be edited by it:**

* `governance/assurance/WO-2/ESCAPED-VARIANTS-KNOWN-SET.md` — the FIRST auditor's ten
  escapes, `E01`..`E10`.
* `governance/assurance/WO-2R/variants/` — the SECOND auditor's six, `ASR2-001-A`,
  `ASR2-002-A`, `ASR2-003-A`, `ASR2-005-A`, `ASR2-012-B`, `ASR2-012-C`.
* `governance/reconciliation/WO-2R/PL-*.txt` on `main` — the Project Lead's own probes.
  DATA, not executable.

**THE WHOLE CORPUS PROVES NOTHING ABOUT ANY CLASS** (`CD-D-047`). It is given in full to
every seat precisely so that fitting a guard to it is worthless; it is a regression floor and
the next auditor's exclusion list, and nothing else.

## WHAT IS UNDER `variants/`, MEASURED — AND THE SENTENCE THIS REPLACES WAS FALSE

**CORRECTED AT WO-2R3 INCREMENT 8 (`F-06-M`). THE SUPERSEDED WORDING, QUOTED AND NOT DELETED**
(CD-RULE-004, PBG-CONT-003):

> **NOTHING ANYWHERE UNDER `variants/` IS EXECUTABLE** — patches and prose only, mode 0664, no
> symlinks, no wrapper, no runner (`PBG-ASSURE-001`).

**IT ASSERTED THE OPPOSITE OF WHAT IS ON DISK, AND HAD DONE SINCE WO-2R3 INCREMENT 2.** Measured
at this tip with `find`, not read off any document:

| | measured |
|---|---|
| `git apply`-able patches | **112** — 70 under `WO-2R/`, 14 under `WO-2R2/`, 28 under `WO-2R3/` |
| runnable probes | **16** — 12 `.py` and 4 `.sh`, ALL of them under `WO-2R3/` |
| files carrying the executable bit | **1** — `WO-2R3/P-L-is-the-CARRIER-ONLY-callable-field-machine-checked.sh`, mode `0775` |
| every other file | mode `0664` |
| symlinks | **0** |

**WHAT THE OLD SENTENCE WAS RIGHT ABOUT, AND IT IS THE HALF THAT CARRIES `PBG-ASSURE-001`:**
**THERE IS NO WRAPPER AND NO RUNNER.** Nothing here applies a patch, nothing here runs a suite,
nothing here iterates the corpus, and nothing here reports a verdict about the product. **THE
SIXTEEN PROBES ARE INSTRUMENTS THAT REPORT AND NONE OF THEM IS A CARRIER** (`CD-RULE-006`):
every one exits `0` whatever it measures, by design, and each states in its own header that it
draws no conclusion. An auditor who runs one has read a measurement, not a verdict — which is a
different thing from what `PBG-ASSURE-001` forbids, and the old sentence collapsed the two.

**WHAT THE OLD SENTENCE WAS WRONG ABOUT IS EXACTLY WHAT AN AUDITOR WOULD RELY ON IT FOR.** A
seat told *"patches and prose only"* has been told there is nothing here to execute and no
reason to look at what it would do if executed. Sixteen files under this tree run code. **THAT
IS DISCLOSED HERE RATHER THAN LEFT TO BE FOUND**, and the executable bit on the one file that
carries it is named rather than rounded off, because *"mode 0664"* was a claim about every file
and was false about one.
