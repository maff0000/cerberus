# Recovery Errata - identity scrub (CERBERUS WO-1.2, 2026-10-10)

After the initial import, the Owner decided to remove personal/work email addresses from the public history. The branch history was rewritten (all SHAs changed a second time; `ARCHIVE-COMMIT-MAP.txt` was regenerated and maps original archive SHA to current SHA).

## What changed relative to the archive
- Author/committer metadata: 145 commits authored as "Matt Scott" now show "Rogue <rogue@cerberus.local>"; other personal/work addresses were replaced with non-routable placeholders.
- File text: occurrences of the Owner's personal and work email addresses were replaced with `rogue@cerberus.local`. Affected tip trees differ from the archive only by these substitutions (asr-wo3-13/14/15, main, inc12-coordination, inc13-coordination-fix; other tips are byte-identical).
- Commit messages: SHAs quoted in messages were remapped to the new SHAs. SHAs quoted inside FILE contents remain the ORIGINAL archive SHAs.
- Side effect: prose that distinguished two identities "only by email" (e.g. BL-20260824T204700Z-A313.yaml) now shows the same placeholder for both. Read such passages against the archive.
- Dates, parent topology and all other content are unchanged. The service identity `pda@noustai.com` (committer on ~128 commits) was deliberately retained.

## Ground truth
The original, unmodified archive is `/srv/ARCHIVE/pbgv2-retired-20260829/crash-detector` on the DEV host (not published).
