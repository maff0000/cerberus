# CERBERUS

A combined wealth-management, day-trading, and market-crash-detection system — built by adopting proven open-source components where they're genuinely good, and reserving custom build effort for the handful of things nothing off-the-shelf does honestly.

**This repo is public deliberately**, so that ChatGPT (acting as Architect/thinking partner on the broader programme this sits inside) can view the build directly and help, without anything being pasted back and forth by hand. If you're reading this as that Architect: welcome, start with `PID.md`, and see "How to help" below.

## What CERBERUS actually is right now

Three Epics, one authorised PID:

1. **Crash Detector rebuild** — **the active priority.** CERBERUS's crash detector **replaces** ARGUS's legacy, currently-failing crash-engine services outright (confirmed by the Owner, 2026-10-10) — this is not a parallel option sitting alongside the old one, it's the successor. The design itself is sound and already Owner-signed (two dials — equity crash / monetary debasement — deliberately never blended, ~24 mapped indicators); the problem was never the design, it's that the standalone build was orphaned mid-increment when its old governing framework (PBGv2) was retired, and never actually deployed. 342 commits of real engineering work from that attempt are salvageable, archived on dell-debian, and are being recovered here rather than re-derived from scratch.
2. **wealth tooling** — a small set of adopted research/due-diligence tools (OpenBB, a personal research console, an on-demand due-diligence agent, a monthly committee-cycle tool) feeding Matt's own long-term portfolio review. Not started yet.
3. **US-equities day trading** — currently paused pending reconciliation with a separate, more mature project (ARGCAT) that already does most of this. Don't duplicate it; see `PID.md` §3 for the full reasoning.

Full detail, scope, risk register, and the authorisation record: **[`PID.md`](PID.md)**. Read it before touching anything — it is the product-authority document, not a suggestion.

## Governance

This project runs under **[FORGE](https://github.com/maff0000)** (ask the Delivery Lead for the framework repo if you need the doctrine itself) — a lightweight PID → PL → Engineer/Auditor delivery-control loop. No orchestration daemon, no queue: Durable truth is git history, not a database or a chat thread. The **Delivery Lead (FORGE PL) is Rogue** — Argus-adjacent, dell-debian infrastructure is his standing lane. Trinity holds product ownership and sequencing; Matt is final authority on everything in the Owner Review Points list in `PID.md` §6.

**Why this project exists in this shape:** the crash detector's first attempt died because its build artifacts lived only on local disk with zero GitHub remote — 342 real commits, never backed up off one machine, orphaned the moment the framework underneath it was retired. This repo existing, public, from day one, with a real remote and a real PID, is the direct fix for that failure mode.

## Security

This is a **public repository with real governance content and real financial context.** Hard rules, no exceptions:
- No secrets, API keys, credentials, account numbers, or connection strings ever committed — `.gitignore` covers the obvious cases, but review every diff before it leaves a local machine.
- No production data, no real account balances, no PII beyond what's already a matter of public record about this project's existence.
- A credential scan (gitleaks or equivalent) runs before every push where it's available.
- Infrastructure specifics (internal hostnames, IPs, SSH details) stay out of this repo — reference them by role/name, not address, the way `PID.md` already does.

## How to help (for the Architect / anyone reviewing)

Read `PID.md` in full first — it has the Epics, the risk register, the open Owner Review Points, and exactly what's authorised vs. not. The current live work is Epic 1 (crash detector). If you're reviewing a specific pull request or work order, check it against `PID.md` §9 (Definition of Done: implemented, independently audited by a fresh reviewer, live-tested, evidence committed) before treating anything as finished — "merged" and "deployed" are different claims here, deliberately.
