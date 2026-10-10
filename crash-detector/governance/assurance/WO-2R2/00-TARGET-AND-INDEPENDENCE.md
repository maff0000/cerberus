# CD-ASR-WO2R2-01 — Target verification and independence declaration

seat: CD-ASR-WO2R2-01 (THIRD Assurance seat)
authority: CD-AUTH-0001 / dispatch CD-DISPATCH-WO2R2-ASSURANCE
started_utc: 2026-08-20

## INDEPENDENCE — declared first

- I am not CD-ASR-WO2-01 and not CD-ASR-WO2-02.
- I have never held the ENGINEER role on this project.
- Verified by enumeration of every author on `wo-2-skeleton`:

```
CD-ENG-READER-01, CD-ENG-WO2-01, CD-ENG-WO2R-01, CD-ENG-WO2R2-01,
CD-ENG-WO2R2-02, Matt Scott <rogue@cerberus.local>, PROJECT_LEAD_SEAT_01
```

`CD-ASR-WO2R2-01` appears nowhere in that set. I hold no commit on the branch.
No INDEPENDENCE_CONFLICT. I proceed.

## AUTHENTIC TARGET

| property | observed | source |
|---|---|---|
| dispatched SHA | f30e63cbac6782ec5d7789071ee26be0ba7fe2e5 | dispatch |
| `git rev-parse` | f30e63cbac6782ec5d7789071ee26be0ba7fe2e5 | measured |
| `git cat-file -t` | commit | measured |
| worktree | /srv/crash-detector-wo2r2-audit (detached) | measured |
| `git status --porcelain` | 0 lines | measured |
| tracked files | 392 | measured |
| tree object | 01da44b51e07dfb2e71170f4f19b6db09814b981 | measured |

The authentic target is reached. Verification rests on git content-addressing, which is
strictly stronger than the ad-hoc fingerprint below.

## FINDING ASR3-F01 (LOW, process) — the advertised tree fingerprint is not reproducible

The dispatch records `target_tree_fingerprint:
4012a5c3877591a863b3cc6016f7af9803e6e9309f2128109b81347769037e2a`, described as "sha256 of
the sorted sha256sums of all 392 files", and tells me it "will be re-taken when you return"
so that "mutation is detectable, not merely prohibited".

I attempted 10 plausible constructions of that stated definition on the clean, verified tree:

| # | construction | result |
|---|---|---|
| A | `git ls-files -z \| xargs -0 sha256sum \| sort \| sha256sum` | 80b778eb... |
| B | as A, hashes only | 2e597fab... |
| C | `find`-based, sorted lines | 8af080c8... |
| D | `find`-based, paths sorted first | e5af46c7... |
| E | hashes only, sorted, newline-stripped | add43721... |
| F | `%P` paths sorted, full sha256sum lines | 41ca0518... |
| G | as F, hashes only | fb33175d... |
| H | `git ls-files` sorted, hashes only | fb33175d... |
| I | LC_ALL=C sort of lines | 80b778eb... |
| — | git tree object | 01da44b5... |

**None equals the recorded value.** The string `4012a5c3877591a863b3cc6016f7af9803e6e930`
appears in exactly one place in this repository: the dispatch file that asserts it. It is
recorded in no build log and no evidence artefact.

Effect: the fingerprint as published is a **self-vouching artefact** (`PBG-EVID-001`). Only
the seat that computed it knows the construction, so no independent party — including me —
can confirm the tree matched it at issue, nor confirm it still matches on return. As a
tamper-evidence mechanism it is unfalsifiable in both directions.

This does NOT impair target authenticity: `git rev-parse HEAD` + `git status --porcelain` +
the tree object hash establish the target far more strongly, and they do reproduce.

Recommendation (for the Engineer/PL, not for me to implement): publish the exact command
line alongside any future fingerprint, or drop it in favour of the git tree object hash,
which is reproducible by construction.

## Mutation discipline adopted

- All Python invoked as `python3 -B` (no `__pycache__` written into any audited tree).
- All experiments performed on `git archive`-extracted throwaway copies under /tmp, a
  separate extraction per variant (SD-2). No `git worktree add`.
- No writes anywhere except /srv/crash-detector-wo2r2-evidence/ (SD-1).
