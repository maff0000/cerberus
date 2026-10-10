# CD-ASR-WO2R2-01 — CD-AC-012, and the `scope: CLASS` question (UV-6)

target: f30e63cbac6782ec5d7789071ee26be0ba7fe2e5

---

## FINDING ASR3-F08 — **HIGH** — CD-AC-012. DENY-BY-DEFAULT IS DEFEATED BY THE SPELLING OF
## A REQUIREMENT LINE. A REAL BROKER SDK, IN A MANIFEST THE CHECK SAYS IT READ, EXITS 0.

All arms measured by me, each on a fresh `git archive` extraction of f30e63c.

| arm | requirement line added to `requirements.txt` | EXIT | result |
|---|---|---|---|
| baseline | — | **0** | PASS — 134 assertions |
| **CONTROL** | `futu-api==9.3.5308` | **1** | **FAIL — 1 violation, CD-DEP-001** |
| **ESCAPE 1** | `-e git+https://github.com/FutuOpen/py-futu-api.git#egg=futu-api` | **0** | **PASS — 134 assertions** |
| **ESCAPE 2** | `-r broker-deps.txt` (containing `futu-api==9.3.5308`) | **0** | **PASS — 134 assertions** |
| **ESCAPE 3** | `sha512==1.0.0` | **0** | **PASS — 134 assertions** |

`futu-api` is the real PyPI SDK of **Futu Holdings / moomoo**, a NASDAQ-listed licensed
broker-dealer; it exposes `trade_ctx.place_order(...)`. It is on no denylist and carries no
execution token — I verified `judge_distribution('futu-api') -> None`.

### THE COUNTERFACTUAL IS EXACT
**Same distribution. Same file. Same check. The only variable is the requirement's
spelling** — and the guard flips from a named CD-DEP-001 refusal to a clean pass.

### AN INDEPENDENT ORACLE CONFIRMS THE DEPENDENCY IS REAL (PBG-EVID-001)
I did not take my own reading of the parser on trust. pip's own requirement parser, on the
identical file:

```
pip parses -> git+https://github.com/FutuOpen/py-futu-api.git#egg=futu-api | editable: True
```

**pip installs it; the guard does not see it.** That is the definition of a control bypass:
a route around the control that the control cannot see.

### WHY THE ASSERTION-COUNT HEURISTIC CANNOT CATCH IT
Every escape reports **exactly 134 assertions** — byte-identical to the clean run. The
"no shrink" check (CD-ASR-WO2R-F16) compares assertion counts to detect a silently degraded
arm. Here the count does not move, because the line was never enumerated. The guard's own
doctrine — *"`exit 0` means 'clean' and 'I looked at nothing' indistinguishably"*
(`tools/register/_support.py:19-20`) — applies at **line** granularity, where nothing
protects it.

### THIS IS INSIDE THE CLASS THE REGISTER STATES, AND OUTSIDE EVERY BOUNDARY
`required-tests.yaml` `negative_control.violation` states the class:

> "THE CLASS THAT IS CLOSED: A DISTRIBUTION NOBODY DECLARED. **Any distribution named in
>  any dependency manifest** — pyproject.toml, requirements.txt, requirements.lock … —
>  whose PEP 503 normalised name is not the `distribution` of a registered entry … **It is
>  refused BY DEFAULT.**"

`futu-api` is named in `requirements.txt`, is registered nowhere, and **is not refused.**
The five declared boundaries cover: (1) truth of a registered claim, (2) content of
`purpose`/`declared_in`, (3) anything **outside** a static read of the declared manifests,
(4) that a dependency is not a pathway, (5) that the registry is in-tree. **Boundary 3
bounds the FILE SET; it says nothing about the EXTRACTION being incomplete WITHIN those
files.** No boundary names the parser. The escapes are inside the declared manifests.

**The structural point:** deny-by-default gives `enumerated ⊆ registered`. The register
claims `declared ⊆ registered`. The gap between *declared* and *enumerated* is the entire
escape surface, and layer 1 cannot close it in principle — a name never extracted is never
tested, so "nothing is recognised" degrades silently into "nothing is examined".

**Corroborating escapes** (same shape, also measured at exit 0, reported for completeness
rather than itemised): `-c pins.txt` constraints include; `./vendor/…whl` local path;
PEP 735 `[dependency-groups]`, `[tool.poetry.dependencies]`,
`[tool.setuptools.dynamic]` and a `setup.py` `install_requires` — the check reads only
three `pyproject.toml` tables while the register says "pyproject.toml" unqualified.

### MITIGATION, MEASURED NOT ASSUMED — and it is real
A dependency is permission to import, not a pathway. `deploy/egress-destinations.yaml`
declares `destinations: []` — **0 registered destinations** — and both compose networks are
`internal: true`. **The product harm at WO-2 is contained.** What is wrong is the register's
description of what a clean run proves. That containment is a WO-2-state fact the Engineer
itself flagged as temporary (boundary 4: "the moment a destination is registered this
carrier weakens by exactly that much").

---

## FINDING ASR3-F09 — **MEDIUM** — a CD-RULE-004 three-place disagreement **inside the
## repair for a CD-RULE-004 defect**, in the load-bearing word.

The declared limit asserts it is "Stated identically here, in `required-tests.yaml` and in
`contracts/execution/CD-RT-012-LOCKFILE-DENYLIST.md`". On `scope` it is not:

| place | says |
|---|---|
| `required-tests.yaml:1082` | `scope: CLASS` |
| `contracts/execution/CD-RT-012-LOCKFILE-DENYLIST.md:3` | `scope **CLASS**` |
| `tools/register/check_lockfile_denylist.py:111` | **"THIS CHECK'S SCOPE IS `DECLARED_SURFACE`, NOT `CLASS`, AND THE REGISTER NOW SAYS SO."** |
| same file:114 | "Before this rework the register declared `scope: CLASS`" |

**Both of the source's sentences are false at this SHA.** The register declares
`scope: CLASS` right now; it was not changed. `DECLARED_SURFACE` is not a framework value
(`SCOPES = {"INSTANCE","CLASS"}`) and appears nowhere outside that one file.

Worse, line 669 emits it into **every clean run's evidence artefact** — I reproduced it on
all five arms above:

```
note: SCOPE IS DECLARED_SURFACE, NOT CLASS.
```

So the PASS output an auditor files as evidence **directly contradicts the register row
that the PASS is evidence for**. The code was written as though the argument had gone the
other way and the register had been amended; it was not.

---

## UV-6 — MY RULING ON `scope: CLASS`. This was assigned to me to settle.

**The seat's reasoning is honest and I record that first.** The framework offers only
`{INSTANCE, CLASS}` (`pbg/tools/pbg/required_tests.py:62`), `pbg/` is protected, and there
is genuinely no third value. `INSTANCE` **would** be a different falsehood — deny-by-default
over a declared registry is structurally the opposite of instance-catching, and the shift
from a 61-name list to a registry is a real advance that genuinely generalises (a typosquat,
a renamed fork and a brand invented tomorrow all fail for the same structural reason). The
seat flagged its own conflict of interest by name as `CD-ENG-WO2R2-02-F02` and invited
overruling. That is exactly right conduct.

**I OVERRULE IT, on evidence rather than on preference.**

`scope` in the register is a claim about **what a clean run proves**, not about what shape
the mechanism has. The mechanism's shape is CLASS-like; the evidence a clean run supplies is
not. `scope: CLASS` is **not sustainable as currently evidenced**, because the class as
written in the entry is refuted by execution at this SHA by **three independent one-line,
manifest-only edits**, none of which any boundary names, and one of which (`futu-api` via
`-e`) is a real brokerage's real order-entry SDK that pip will install.

The precedent the seat leans on (`CD-RT-012-NO-EXECUTION-INTERFACE`, also `CLASS` with a
written boundary) holds only where the boundary actually names the escape route. Here it
does not.

**What this ruling does NOT say:** it does not say `INSTANCE` is correct — it is not, and
switching to it would trade one false statement for another. **The defect is not the value
in the field; it is that neither available value is true, and the entry does not say so
where the gate reads it.** The honest remedies (the Engineer's to choose, not mine —
PBG-SOD-004) are either to repair the extraction so `declared == enumerated` (or refuse on
any construct the parser does not understand, the posture the registry loader already takes),
or to add a sixth boundary naming the extraction gap with these executable examples and a
MEASURED-or-NOT-PROVED carrier. Either way the three places must be made to agree, and the
runtime note must stop contradicting the register.

---

## WHAT I CONFIRMED WORKING ON CD-AC-012

* All three declared CD-AC-012 tests **CONTRAST 0 → 1** on my own harness
  (`CD-RT-012-NO-EXECUTION-INTERFACE`, `CD-RT-012-LOCKFILE-DENYLIST`,
  `CD-RT-012-EGRESS-NO-BROKER`).
* **Deny-by-default genuinely works on what it enumerates.** The control arm caught
  `futu-api` by CD-DEP-001 without recognising anything about it — that is the right shape,
  and it is a real improvement over the denylist it replaced. My finding is that the
  enumeration, not the decision rule, is where the class leaks.
* **RW-4 answered: declared boundary 1 is open by construction and I re-executed it.**
  `tastytrade-sdk==1.2.0` in both manifests plus a registry entry with a plausible purpose
  → **exit 0, PASS, 149 assertions.** Honestly declared, honestly executed. **On its own,
  that shape IS compatible with a scoped PASS** — it is a limit that cannot be closed
  offline without an oracle that does not exist, and a network check is rightly prohibited
  (CD-PL-F48). It is not what fails this criterion. ASR3-F08 is.
