# WO-1.1 — Retire and archive the legacy ARGUS-coupled crash engine

Date: 2026-10-10 · Executor: Rogue (dispatched by Trinity) · Authority: CERBERUS PID; Matt confirmed the CERBERUS crash detector REPLACES this engine outright (not a fallback).
Host: dell-debian (192.168.11.10).

## Units in scope (service + timer each)
argus-crash-deploy-advisory, argus-monetary-regime-alert, argus-monetary-regime-producer, argus-monetary-tell-boe, argus-monetary-tell-fred, argus-monetary-tell-gold.

Pre-state: 3 services `failed` (deploy-advisory: `argus:lgt:sleeves` missing; regime-alert: Discord webhook HTTP 403; tell-gold), 3 inactive; all 6 timers enabled and firing. The regime-producer was still succeeding hourly (state=WATCH, blindness=True, gold tells STALE, others NOT_FIRED).
Three units (advisory, alert, producer) were symlinks from /etc/systemd/system into /srv-argus-live/ARGUS/ops/; alert had an override.conf drop-in; tell-* were regular files.

## Dependency check (before any stop)
- systemd: grep of /etc/systemd, /usr/lib/systemd, /run/systemd + `list-dependencies --reverse` -> no unit Requires/Wants/After/Before any of the 6. Only hit outside the six: argus-sniper-recompute.service, comment text only. No cron entries (/etc/cron*, crontabs).
- Code/data readers of the published Redis keys (`argus:monetary_regime:state:latest`, `argus:crash:deploy_advisory:latest`, `argus:crash:two_floor_advisory:latest`, `argus:monetary_regime:alert:badge`) in /srv-argus-live/ARGUS:
  - src/api/routes/playbook.py + templates/playbook.html — Playbook GUI; read-only; returns None if key missing, flags `_stale` past max_staleness_days.
  - src/review/playbook_review.py (daily review) — reads regime key; missing -> DORMANT/inert, unreadable/stale -> floored to WATCH + blindness flag (fail-safe, advisory only).
  - src/calc/deployment_engine.py — consumes the regime via the same fail-safe seam.
  All are advisory-only, fail-safe consumers. None write to or depend on the six services running. Effect of retirement: the Playbook crash panel / review crash context go stale (flagged as such) and the last published regime key stays as-is until it ages out. No capital-moving path depends on it.
- Limits of this check: grep covered /srv-argus-live, /etc/systemd, cron; a wider /srv-wide grep timed out and was not completed. Other hosts (e.g. Trinity) were not searched.

## Actions
1. Archived BEFORE stopping (see below).
2. `systemctl stop` + `disable` on all 6 timers and services; `daemon-reload`.
3. `disable` removed the /etc/systemd/system symlinks for advisory/alert/producer (service+timer) and the timers.target.wants links for all 6 timers. The tell-* .service/.timer regular files remain in /etc/systemd/system, disabled. Source in /srv-argus-live/ARGUS (ops/, src/, tests/) was NOT touched. Redis keys NOT touched. Env files NOT touched or copied (secrets).

## Archive
dell-debian:/srv/ARCHIVE/legacy-crash-engine-retired-20261010/ — units/ (resolved copies of all 12 unit files), dropins/ (alert override.conf), launchers/ (6 ops/*.sh), original-symlinks.txt, pre-retirement-unit-file-state.txt, README.md (with restore steps).

## Verification (post)
- `systemctl list-units --failed | grep argus-(crash|monetary)` -> none.
- `systemctl list-timers --all | grep argus-(crash|monetary)` -> none.
- All 6 services inactive; timers inactive, disabled/unloaded.
- Failed-unit count on host 27 -> 24 (exactly the 3 retired failures). The remaining 24 failed units (ares-*, backup-*, neo-*, etc.) are unrelated and untouched.

## Not done / follow-ups
- WO-1.2 not started.
- Stale `argus:*` Redis keys and the dead code in the ARGUS repo are left for a later cleanup decision (ARGUS lane / Matt).
