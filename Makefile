# R2D2 — install/sync targets
# Re-deploys git-tracked files to live system locations after pull.
# Live system = /opt/r2d2/ (scripts) + /etc/systemd/system/ (units).
# Git repo = /srv/r2d2/ (canonical source).
#
# After git pull or fresh checkout: `make install` then `make enable-timers`.
# To pull live changes BACK into git (drift sweep): `make sync-from-live` then commit.

REPO       := /srv/r2d2
LIVE_OPT   := /opt/r2d2
LIVE_SYS   := /etc/systemd/system

.PHONY: help install install-scripts install-systemd enable-timers disable-timers sync-from-live status

help:
	@echo "R2D2 install/sync targets:"
	@echo "  make install            — copy git -> /opt/r2d2/ and /etc/systemd/system/, daemon-reload"
	@echo "  make install-scripts    — copy git -> /opt/r2d2/ only"
	@echo "  make install-systemd    — copy git -> /etc/systemd/system/ + daemon-reload"
	@echo "  make enable-timers      — systemctl enable --now all r2d2-* timers"
	@echo "  make disable-timers     — systemctl disable --now all r2d2-* timers"
	@echo "  make sync-from-live     — copy live -> git (use before commit if live drifted)"
	@echo "  make status             — list timer states + last fires"

install: install-scripts install-systemd

install-scripts:
	@mkdir -p $(LIVE_OPT)/maintenance
	cp -v $(REPO)/maintenance/*.py $(LIVE_OPT)/maintenance/
	cp -v $(REPO)/watchers/*.py $(LIVE_OPT)/
	chmod +x $(LIVE_OPT)/maintenance/*.py $(LIVE_OPT)/*.py

install-systemd:
	cp -v $(REPO)/systemd/*.service $(REPO)/systemd/*.timer $(LIVE_SYS)/
	systemctl daemon-reload

enable-timers:
	systemctl enable --now r2d2-maintenance-drift.timer r2d2-maintenance-sample-growth.timer r2d2-maintenance-weekly.timer r2d2-maintenance-correlation-tracker.timer

disable-timers:
	systemctl disable --now r2d2-maintenance-drift.timer r2d2-maintenance-sample-growth.timer r2d2-maintenance-weekly.timer r2d2-maintenance-correlation-tracker.timer

sync-from-live:
	cp -v $(LIVE_OPT)/maintenance/*.py $(REPO)/maintenance/
	cp -v $(LIVE_OPT)/tdr_*.py $(LIVE_OPT)/nowic_at_*.py $(REPO)/watchers/
	cp -v $(LIVE_SYS)/r2d2-maintenance-*.service $(LIVE_SYS)/r2d2-maintenance-*.timer $(REPO)/systemd/
	cp -v $(LIVE_SYS)/r2d2-tdr-watcher.* $(LIVE_SYS)/r2d2-nowic-at-watcher.* $(REPO)/systemd/

status:
	@systemctl list-timers 'r2d2-*' --no-pager
