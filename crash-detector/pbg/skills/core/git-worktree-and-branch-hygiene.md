---
skill_id: SKILL-GIT-WORKTREE-AND-BRANCH-HYGIENE
title: Git worktree and branch hygiene
version: 1
roles: [PROJECT_LEAD, ENGINEER]
triggers: [starting bounded work, parallel agent dispatch, reconciling drift]
prerequisites: [repository access, authorised work item]
required_inputs: [work item ID, base branch]
related_controls: [PBG-GIT-001, PBG-GIT-002, PBG-GIT-003, PBG-CONT-008, PBG-WORK-004]
references: [SRC-OPENSSF, SRC-DORA]
---

# Git worktree and branch hygiene

Keeping the repository an honest record, and keeping concurrent agents out of each other's way.

## Branch per authorised work item

```bash
git switch -c work/<WORK-ITEM-ID> <base>
```

Never the default branch. The branch name carries the work item so an arriving agent can connect a
commit to its authority without asking anyone.

## Worktrees for concurrency

Two agents in one working tree will corrupt each other's state — not maybe, eventually.

```bash
git worktree add ../wt-<WORK-ITEM-ID> -b work/<WORK-ITEM-ID> <base>
git worktree list
git worktree remove ../wt-<WORK-ITEM-ID>
```

One worktree per concurrent agent. Each has its own HEAD, index and working tree; they share
history, which is what you want.

## Observing honestly

```bash
git rev-parse HEAD                 # the SHA, read not remembered
git status --porcelain             # empty means clean
git log --oneline -5
```

**A clean status against a stale remote-tracking ref proves nothing.** This has bitten this estate
before: a working copy four commits behind reported no divergence because the ref it compared
against was itself stale. Fetch before you trust a comparison, and if you cannot fetch, say the
comparison is unresolved.

## Discipline

- Stage by name. `git add -A` commits whatever happened to be there.
- Check `git status` against your writable scope before committing.
- Commit messages explain why. The diff already shows what.
- No force push, hard reset, or branch deletion without explicit authority.
- No `--no-verify`. A failing hook is information.

## Evidence

Branch name, exact SHA, working-tree state, the diff.

## Failure behaviour

A repository in an unexpected state is a finding. Report it and reconcile; never silently correct
it, and never route around it.
