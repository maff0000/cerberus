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
| `variants/WO-2R2/` | [`variants/WO-2R2/MANIFEST.md`](WO-2R2/MANIFEST.md) | `CD-ENG-WO2R2-01` | CLASS 1. Four rows: `V01`, `V03`, `V04` refused; **`V05` NOT REFUSED and open**. `V02` withdrawn and its id left unused. |

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

**NOTHING ANYWHERE UNDER `variants/` IS EXECUTABLE** — patches and prose only, mode 0664, no
symlinks, no wrapper, no runner (`PBG-ASSURE-001`).
