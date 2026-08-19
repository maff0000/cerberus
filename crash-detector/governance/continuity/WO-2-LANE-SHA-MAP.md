# WO-2 LANE — OLD → NEW SHA MAP (identity re-authoring)

**Authority:** Product Owner Ruling 3, `governance/decisions/PO-GATE-REVIEW-WO2-0001.md`;
`CD-RULE-002`; ordered first by `CD-D-026`; preservation required by `CD-D-027`.
**Performed by:** PROJECT_LEAD_SEAT_01 under CD-AUTH-0001, 2026-08-19.
**Build Log:** `BL-20260819T090500Z-0021`.

## What was done, and what was deliberately NOT done

Every one of the 24 commits on the unmerged lane `wo-2-skeleton` was re-authored from the ambient
human identity to the seat that actually did the work. **Author and committer both.**

| field | before | after |
|---|---|---|
| author | `Matt Scott <rogue@cerberus.local>` | `CD-ENG-WO2-01 <cd-eng-wo2-01@seats.crash-detector.invalid>` |
| committer | `NoustAI-PDA <pda@noustai.com>` | `CD-ENG-WO2-01 <cd-eng-wo2-01@seats.crash-detector.invalid>` |

**Nothing else changed.** Not one tree, not one message byte, not one timestamp. That claim is
proved below rather than asserted.

**`main` was NOT rewritten** (`CD-D-029`). Its 13 checkpoint commits keep the ambient human author.
The Product Owner scoped Ruling 3 to the unmerged lane, rewriting the trunk would invalidate the
checkpoint SHAs the continuity record is built on, and no ruling asks for it. Every **new** commit on
main from `BL-20260819T085500Z-0020` (`80b4a24`) forward carries a seat identity, so the trunk has a
**dated seam** rather than a silent inconsistency. If the PO wants the trunk re-authored too, that is
a separate bounded action and it should happen before anything else is built on the trunk.

## Why the old SHAs still resolve, and must

`governance/engineering/build-log/` names lane SHAs throughout — `3b6edae`, `8723ffb`, `d40e5c6`,
`cbfa7c5`, `11979fb`, `d1abdcc`, `a06e64f`, `66681b2` and more. The standing SHA-resolution step
(`CD-CONT-002`) resolves every recorded SHA against the object database at every boundary, and it
has already caught two fabricated values on this project. **A step that starts failing for a lawful
reason is a step that stops being trusted.**

So: the annotated tag **`wo-2-pre-identity-rework`** is placed at `66681b2`, and every pre-rewrite
commit remains reachable from it, permanently.

**The Build Log entries are NOT edited.** Their text continues to name the old SHAs, which is
correct: Build Log history is not rewritten, corrections supersede (`PBG-CONT-003`, non-waivable).
**This table supersedes; it does not correct.** To resolve a lane SHA recorded before 2026-08-19
08:57 UTC, read it here.

## The method — chosen so the result is provable, not merely plausible

`git filter-branch` and `git filter-repo` were both **declined**. Each rewrites messages and metadata
through a normalising pipeline, and each would have left the "nothing else changed" claim resting on
the tool's good behaviour.

Instead each commit object was **rebuilt by hand** with `git hash-object -t commit -w --stdin`:

* the `tree` line was **copied verbatim** — the same tree OID, so content equality is not compared,
  it is *the same object*;
* the `parent` line was relinked to the new predecessor;
* the `author`/`committer` lines had the identity substituted while the trailing
  `<unix-timestamp> <tz>` was **copied verbatim** from the stored line;
* the message was **copied as raw bytes** after the header terminator, untouched;
* any header field other than `tree`/`parent`/`author`/`committer` would have **raised**. All 24
  commits carry exactly those four and nothing else — checked before the rewrite, not assumed.

**Disclosed:** a first attempt used `git commit-tree`, which appends a newline to a message that
lacks one. It was detected by the byte-comparison below — 24 of 24 messages differed by exactly one
trailing byte — and **discarded before any ref was moved**. Its 24 orphaned objects are unreferenced
and will be garbage-collected. The check that caught it is the reason it is reported here rather than
shipped.

## PROOF — six checks, all passed before any ref was moved

| # | check | result |
|---|---|---|
| 1 | raw message bytes, old vs new, all 24 (`cmp` on the post-header byte range) | **IDENTICAL, 24/24** |
| 2 | tree OID, old vs new, all 24 | **IDENTICAL, 24/24** |
| 3 | author date and committer date (`--date=raw`), all 24 | **IDENTICAL, 24/24** |
| 4 | `git diff 66681b2 <new-head>` | **0 lines** |
| 5 | head tree OID, old vs new | both `38ecc86149532a065280e98239a01fc79144d256` |
| 6 | commit count / merge count on the new lane | **24 / 0** — linear, none lost, none added |

### The author audit Ruling 3 asks for

`git log --format='%an <%ae> | %cn <%ce>' bf8fcf9..<new-head> | sort -u` returns **exactly one line**:

```
CD-ENG-WO2-01 <cd-eng-wo2-01@seats.crash-detector.invalid> | CD-ENG-WO2-01 <cd-eng-wo2-01@seats.crash-detector.invalid>
```

`git log --format='%an%ae%cn%ce' bf8fcf9..<new-head> | grep -icE 'matt|infosecurs|noustai|pda'`
returns **0**. No human identity and no harness identity survives anywhere on the lane, in either
field.

### The independent cross-check that settles it

The assurance entry `BL-ASR-WO2-01.yaml` records the tree fingerprint of the audited target —
sha256 over the sorted sha256sum list of every non-`.git` file:

```
08a474e8ae1aa41b8704c27778ade58353258d90768301958db7b92c4b275ad2
```

That value was **recomputed from a fresh `git archive` extraction of the NEW head** and it
**MATCHES**, over 271 files. The re-authored lane is byte-identical to the tree an independent
auditor actually examined. The AMBER verdict therefore still attaches to this content: re-authoring
did not move the target out from under the audit.

## Attribution basis (`CD-D-028`) — measured, not assumed

`git rev-list main..wo-2-skeleton` returns 24 commits. The changed paths of every one lie in the
Engineer's writable scope (`src/`, `tests/`, `tools/`, `contracts/`, `db/`, `deploy/`, `plants/`,
`required-tests.yaml`, the root manifests) **or** are the Engineer's own Build Log entries attesting
its own increments. **Not one** lane commit touches `governance/dispatch/`, `governance/decisions/`,
`governance/rules/` or `ACTIVE_WORK.yaml` — the Project Lead's exclusive paths. The Project Lead's
checkpoints are all on `main`.

So there is no per-commit attribution judgement to make, and none was invented. The whole lane is one
seat: **CD-ENG-WO2-01**.

## THE MAP

Old SHAs resolve via `git show <old>` while `wo-2-pre-identity-rework` exists. Do not delete that tag.

| # | OLD (pre-rewrite, reachable via tag) | NEW (re-authored) | commit subject |
|---|---|---|---|
| 01 | `3b6edae5139093c85e95a49bd001f0158f83a36f` | `b85e38efc2b6a9f22ac4448661c2a617c3fee6f9` | WO-2 increment 1/7 — A1 repository skeleton, A2 dial types, A3 witness |
| 02 | `8723ffbf71fedf0de6a229a4865a3c79283f9782` | `9daa63bbb153214562d83f3cade1bc371b0d8084` | WO-2 increment 2/7 — A4 collector framework + A7 closed envelope contr |
| 03 | `d40e5c6e96d65ef204bed6018dbe58dadcd556b0` | `16943f917e46b07301e417128afcbb474407623c` | WO-2 increment 3/7 — A5 store schema and grant matrix, A6 container se |
| 04 | `7e9b46ee19499b75c8d3d17038d011defe1ee028` | `83d602298315fbd4128696c41bb3340ba7fdbcf9` | WO-2 increment 3/7 Build Log — CD-ENG-WO2-01 attests d40e5c6; CD-OB-00 |
| 05 | `9e0b1803204510386743ef1daf76c6c25736452b` | `b0d8484549cb3dc4f858fa3c31f9194c5cc8e462` | WO-2 B1 (1/2) — register checks: numeric-default, no-blend, schema-clo |
| 06 | `c63621b752d0c2a08df7f419d9c162361b20a110` | `3b26411f83bb35ec239f808aae195c1b5442ef31` | WO-2 B1 (2/2 part A) — execution-interface, lockfile denylist, digest  |
| 07 | `ccdee2a48647a00edd9d6282e3c78ed26c40dc9f` | `7f150bac5c105398f41e237ade7e8dd536ed1a3d` | WO-2 B1 — CD-RT-003-GRANT-MATRIX-LIVE promoted to a durable check (CD- |
| 08 | `cbfa7c5bb777d2111634a456bd8255592652b154` | `844271796b98b88945738b0f7100e02d8a8772ac` | WO-2 B1 — CD-ENG-F30: the deploy secret sweep died on a .pyc |
| 09 | `3f038665bdd8d79509dbe61d52176d02aee47de7` | `dd1564d83e8e98aaa761ecaf31c4bb857ae25c53` | WO-2 increment 4/7 Build Log — CD-ENG-WO2-01 attests cbfa7c5; CD-OB-00 |
| 10 | `8cf2f96e7b948725a5bb5e9b68e07f01667579f2` | `a434d8606b9e073cd6a3401d40a149664b695c6b` | WO-2 CD-PL-F32 CLOSED — the execution-interface check now reads shape  |
| 11 | `11979fb0c827a0b96ffb3b6813daefedfc7c89ea` | `4e1d449dc96e78e667be63bc53c2a1328d4809ac` | WO-2 B2 — the Required Test Register over all sixteen PID criteria |
| 12 | `9a1a15923e61f6d472a1c1600598fad4ec971b46` | `ed9ac3c17cf36ad55da7c73244593070309f7f01` | WO-2 increment 5/7 Build Log — CD-ENG-WO2-01 attests 11979fb; CD-PL-F3 |
| 13 | `d1abdcc9732dc14ebc92a9d69622a4558355e0a9` | `51336d737f9d2eb8c3547180995be1a7ed2fbc47` | WO-2 increment 6a — CD-PL-F38 closed, and the guard now DECLARES ITS O |
| 14 | `68b524b580b1e9602357c706e974ae541cd8630c` | `c8e0ce9da5c3a65337e0422ba688b64e02047d78` | WO-2 increment 6a Build Log — CD-ENG-WO2-01 attests d1abdcc; CD-D-014  |
| 15 | `19dce05ba01ad65d875145fe6b30c9ac0cd2bd36` | `d47a0a086bc53cb244958ae92219fa7c2b656572` | WO-2 B3 — CD-AC-001 planted violations (2 of 11) |
| 16 | `6b16128e162c829b7ab56e9bb0b970aae7bebc22` | `9b47f0b4f71345aa6e3d6b2cc3aa20d30f577604` | WO-2 B3 — CD-AC-002 planted violations (5 of 11) |
| 17 | `de34e338584b52118c0d2f4415eefd2413774788` | `d98e44f4c4e0931b2be431d74b3dae5fd9f3ec1c` | WO-2 B3 — CD-AC-003 planted violations (7 of 11); RT-A exercised |
| 18 | `6bb9cd63e0e855a32f7841274c95216b506c23f4` | `a2c4e771748ab63e39c118f307f061e87708f0e4` | WO-2 B3 — CD-AC-005 planted violation (8 of 11) |
| 19 | `2cada019f7b109b89687a1156684d738f1950cea` | `80d17735c0d7193a5aac68615d2ee191d560ac58` | WO-2 B3 — CD-AC-012 planted violations (11 of 11); B3 COMPLETE |
| 20 | `a06e64f0db710613ff079f5f0c260a0f3c65cca5` | `3f7f82131a1c9243d491bf1d2c43ea114e2e2d97` | WO-2 CD-ENG-F40 — the printed note now matches the declared limit |
| 21 | `9aea4ef2ea93d237045c1b986bcb365dc4c17b4c` | `980925c857630c0355ff6d2f08baae921bb8c948` | WO-2 increment 6b Build Log — CD-ENG-WO2-01 attests a06e64f |
| 22 | `3a50ed61bb11f066b38455a6dd77c3e75626f454` | `000702fd6163792bcbaf0feca435d2ccce42e0ce` | WO-2 increment 7 — B4 stage 1: the CLEAN ARM, this seat's own run |
| 23 | `9c2adfa2cd57fa6967afd462aa229662c25f2159` | `3de80f8f61dbd6809f652eff53e47cdc40f31f72` | WO-2 increment 7 — B4 stage 2: the TEN plant arms that need no store |
| 24 | `66681b27ed650321f6b9e325fbc05712a754cc7d` | `ee8be6be38696f389a610bc948992a71ad81f892` | WO-2 increment 7 — B4 stage 3: the RT-A live-store arm, findings, retu |

**Lane head:** `66681b27ed650321f6b9e325fbc05712a754cc7d` → `ee8be6be38696f389a610bc948992a71ad81f892`
**Lane base (unchanged, on main):** `bf8fcf987340cbca7468a0f152c4bd62433f1cc4`
**Preserved at tag:** `wo-2-pre-identity-rework` → `66681b27ed650321f6b9e325fbc05712a754cc7d`

## Consequences for the next seats

* **The WO-2R Engineer** starts from `ee8be6be38696f389a610bc948992a71ad81f892` on branch `wo-2-skeleton`, worktree
  `/srv/crash-detector-wo2`. It commits as `CD-ENG-WO2R-01` — a **new** actor_id, because it is a
  new seat on a new dispatch, and the record should show which seat closed which class.
* **The WO-2R Assurance seat** audits whatever SHA the rework returns. `66681b2` is **historical**:
  it is the target of the *superseded* AMBER verdict, not of the re-audit.
* **`/srv/crash-detector-wo2-audit`** is still detached at `66681b2` and is now **stale**. It is
  left in place, untouched, because the first audit's verdict still stands as a record and its target
  should remain inspectable. A **fresh** read-only worktree will be created for the re-audit at the
  new target SHA.
