#!/bin/sh
# ================================================================================================= #
# THE DRIVER BINDING — increment 12 ITEM 4(i), `PO-DECISIONS-0021` ruling 3(d).
#
# The ruling requires the launch lease to bind "the driver AND the PO's own hand". THIS IS THE
# DRIVER HALF, AND IT IS THE HALF THAT IS BUILDABLE INSIDE A SEAT'S SCOPE.
#
#   launch.sh --lease ID --seat S --task T --write-scope G [--write-scope G ...]
#             [--read-scope G ...] [--] COMMAND [ARGS...]
#
# IT ACQUIRES THE LEASE FIRST AND **REFUSES TO `exec` THE SEAT IF THE LEASE IS REFUSED.**
# Non-zero exit, NOTHING LAUNCHED, and the refusal printed with the live lease it collided with.
#
# WHY `exec` AND NOT A SUBSHELL: so that the launched process REPLACES this one and inherits its
# PID. The lease is acquired with `--pid $$`, so the pid the lease names is the pid the seat runs
# under. A lease that names a wrapper's pid dies when the wrapper does and says nothing about the
# seat.
#
# WHAT THIS FILE CANNOT DO, STATED HERE RATHER THAN DISCOVERED LATER (`CD-RULE-004`):
#
#   **IT BINDS ONLY LAUNCHES THAT GO THROUGH IT.** The operator's wrapper on this project
#   (`.wo2r3*-runner.sh`, invoked by an operator `bash -c`) IS NOT IN THIS REPOSITORY. No seat and
#   no framework in this tree can reach it. The second meta-assurance seat measured exactly this
#   (§7.2: *"Nothing in `pbg/`, `governance/` or `tools/` can prevent two Project Lead processes
#   running at once, because the launcher is not in the repository"*).
#
#   So this script is a CARRIER THAT EXISTS AND IS NOT YET COMMISSIONED. It becomes the driver
#   binding the moment the operator's wrapper calls it, and not one moment before. That is `Q12`,
#   it is recorded, and it is not this seat's to close.
# ================================================================================================= #
set -eu

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(git -C "$HERE" rev-parse --show-toplevel)

LEASE=""
SEAT=""
TASK=""
LEASE_ARGS=""
DRY=0

usage() {
    echo "usage: launch.sh --lease ID --seat S --task T --write-scope G [--read-scope G] [--dry-run] -- COMMAND [ARGS]" >&2
    exit 2
}

while [ $# -gt 0 ]; do
    case "$1" in
        --lease)       LEASE="$2"; shift 2 ;;
        --seat)        SEAT="$2";  shift 2 ;;
        --task)        TASK="$2";  shift 2 ;;
        --write-scope) LEASE_ARGS="$LEASE_ARGS --write-scope $2"; shift 2 ;;
        --read-scope)  LEASE_ARGS="$LEASE_ARGS --read-scope $2";  shift 2 ;;
        --dry-run)     DRY=1; shift ;;
        --)            shift; break ;;
        *)             usage ;;
    esac
done

[ -n "$LEASE" ] && [ -n "$SEAT" ] && [ -n "$TASK" ] || usage
[ $# -gt 0 ] || { echo "launch.sh: no COMMAND given after --" >&2; usage; }

echo "launch.sh: worktree=$ROOT  seat=$SEAT  task=$TASK  lease=$LEASE"
echo "launch.sh: acquiring the lease BEFORE anything is started. pid that will be leased: $$"

# THE LEASE IS ACQUIRED FIRST. `set -e` is deliberately suspended around it so the refusal can be
# reported with its own text rather than killing the script silently.
set +e
# shellcheck disable=SC2086
python3 -B "$ROOT/tools/coordination/lease.py" --root "$ROOT" acquire \
    --lease "$LEASE" --seat "$SEAT" --task "$TASK" --pid "$$" $LEASE_ARGS
rc=$?
set -e

if [ "$rc" -ne 0 ]; then
    echo "launch.sh: LEASE REFUSED (rc=$rc). NOTHING IS LAUNCHED." >&2
    echo "launch.sh: the command that would have run was: $*" >&2
    exit "$rc"
fi

echo "launch.sh: lease held. exec: $*"

if [ "$DRY" -eq 1 ]; then
    echo "launch.sh: --dry-run, so the lease is held and the command is NOT exec'd."
    exit 0
fi

exec "$@"
