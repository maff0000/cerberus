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
# ================================================================================================= #
# **`CD-ASR-WO2R3-06-F05` — THIS CARRIER USED TO CORRUPT ITS OWN INPUT, AND THAT IS WHY THIS FILE
# LOOKS THE WAY IT DOES NOW.**
#
# Increment 12 accumulated the scope arguments into a STRING and expanded it UNQUOTED:
#
#     --write-scope) LEASE_ARGS="$LEASE_ARGS --write-scope $2"; shift 2 ;;
#     ...  lease.py ... --pid "$$" $LEASE_ARGS
#                                  ^^^^^^^^^^^ unquoted
#
# Unquoted expansion in POSIX `sh` performs FIELD SPLITTING **and PATHNAME EXPANSION**. **A WRITE
# SCOPE IS A GLOB.** So the shell expanded the seat's DECLARED SCOPE against the FILESYSTEM before
# `lease.py` ever saw it, and there were two regimes and both were wrong:
#
#   (i)  the glob matched 2+ real paths -> extra words -> argparse "unrecognized arguments" -> rc=2,
#        printed to the operator as `LEASE REFUSED (rc=2)`, INDISTINGUISHABLE FROM A GENUINE SCOPE
#        COLLISION. Commissioning that carrier would have refused every real launch and told the
#        operator there was a conflict.
#   (ii) the glob matched EXACTLY ONE real path -> **SILENT SCOPE NARROWING.** A seat typing
#        `docs/alpha/*` got a lease recording `write_scope = [docs/alpha/only.md]`; a second seat
#        then acquired `docs/alpha/other.md` and BOTH SUCCEEDED. **SAME REQUEST, OPPOSITE VERDICTS,
#        AND THE ONLY VARIABLE WAS WHETHER THE SCOPE PASSED THROUGH THIS FILE.** That is a FALSE
#        GREEN manufactured by the binding itself.
#
# THE FIX IS STRUCTURAL AND IT IS THREE THINGS, NOT ONE:
#
#   1. `set -f` — PATHNAME EXPANSION IS DISABLED FOR THE WHOLE SCRIPT. A glob cannot be expanded
#      against the filesystem here because the shell is not permitted to expand globs here at all.
#   2. THE SCOPE ARGUMENTS ARE NEVER PUT IN A STRING. They are carried in the POSITIONAL PARAMETER
#      LIST and passed as `"$@"`, which is not subject to field splitting. There is no `eval` and
#      no quoting scheme to get wrong: a scope containing spaces, tabs, `*`, `?` or `[` arrives at
#      `lease.py` byte-for-byte as the operator typed it.
#   3. `lease.py` now ECHOES the scope it actually RECEIVED at every acquisition, so that if any
#      FUTURE carrier corrupts its input the corruption is visible at the point it happens instead
#      of being discovered by an auditor eleven days later.
#
# `PLANT-COORD-07` measures all of it, with a glob matching >=2 real paths AND a glob matching
# EXACTLY 1 — **the two forms `PLANT-COORD-04` did not exercise, which is why it was 3/3 LIVE over
# a deliverable that was broken for every glob matching a real path.**
# ================================================================================================= #
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

# -f : NO PATHNAME EXPANSION ANYWHERE IN THIS SCRIPT. This is half of the F05 fix and it is not
#      decoration — see the header. Do not remove it to "make a glob work"; a glob is DATA here.
set -euf

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(git -C "$HERE" rev-parse --show-toplevel)

# `$$` is the pid of THIS shell and POSIX keeps it stable inside subshells and functions. Captured
# once, up front, so that the pid the lease names is unambiguously the pid `exec` will hand to the
# seat.
SEAT_PID=$$

LEASE=""
SEAT=""
TASK=""
DRY=0

usage() {
    echo "usage: launch.sh --lease ID --seat S --task T --write-scope G [--read-scope G] [--dry-run] -- COMMAND [ARGS]" >&2
    exit 2
}

# ------------------------------------------------------------------------------------------------
# PASS 1 — read the simple options WITHOUT consuming "$@", which is needed twice more below.
# A state machine over `for a in "$@"`, so that an option VALUE which happens to look like an
# option (including a value that is literally `--`) is read as a value and not as a keyword.
# ------------------------------------------------------------------------------------------------
expect=""
after=0
NCMD=0
NSCOPE=0
for a in "$@"; do
    if [ "$after" -eq 1 ]; then
        NCMD=$((NCMD + 1))
        continue
    fi
    if [ -n "$expect" ]; then
        case "$expect" in
            lease) LEASE="$a" ;;
            seat)  SEAT="$a" ;;
            task)  TASK="$a" ;;
            scope) NSCOPE=$((NSCOPE + 1)) ;;   # carried by PASS 2, which must not lose a byte of it
        esac
        expect=""
        continue
    fi
    case "$a" in
        --lease)       expect=lease ;;
        --seat)        expect=seat ;;
        --task)        expect=task ;;
        --write-scope) expect=scope ;;
        --read-scope)  expect=scope ;;
        --dry-run)     DRY=1 ;;
        --)            after=1 ;;
        *)             usage ;;
    esac
done
[ -z "$expect" ] || { echo "launch.sh: option --$expect given with no value" >&2; usage; }

[ -n "$LEASE" ] && [ -n "$SEAT" ] && [ -n "$TASK" ] || usage
# **VALIDATED BEFORE THE LEASE IS TAKEN, NOT AFTER.** A launch that cannot run must not leave a
# lease behind: acquiring first and discovering the missing COMMAND afterwards would strand a live
# lease over a seat that never existed, and the next real launch would collide with a ghost.
[ "$NCMD" -gt 0 ] || { echo "launch.sh: no COMMAND given after --" >&2; usage; }
[ "$NSCOPE" -gt 0 ] || { echo "launch.sh: no --write-scope given" >&2; usage; }

# ------------------------------------------------------------------------------------------------
# PASS 2 — acquire the lease. **THE SCOPE ARGUMENTS NEVER BECOME A STRING.**
#
# The function receives the FULL original argv. It rotates the positional list: each scope option
# and its value are APPENDED to the back, every other original entry is dropped, and exactly the
# original count is shifted off the front. What remains in "$@" is the scope arguments alone, in
# order, each one still a single word regardless of what characters it contains.
#
# `"$@"` is expanded with quotes at the call site, so there is no field splitting; `set -f` is in
# force, so there is no pathname expansion. There is no `eval`.
# ------------------------------------------------------------------------------------------------
acquire_lease() {
    _n=$#
    while [ "$_n" -gt 0 ]; do
        case "$1" in
            --write-scope|--read-scope)
                set -- "$@" "$1" "$2"; shift 2; _n=$((_n - 2)) ;;
            --lease|--seat|--task)
                shift 2; _n=$((_n - 2)) ;;
            --dry-run)
                shift; _n=$((_n - 1)) ;;
            --)
                # everything from here to the end of the ORIGINAL argv is the COMMAND. Drop it:
                # shift exactly the remaining original entries and no more, so the accumulated
                # scope arguments sitting behind them are untouched.
                while [ "$_n" -gt 0 ]; do shift; _n=$((_n - 1)); done ;;
            *)
                shift; _n=$((_n - 1)) ;;
        esac
    done
    echo "launch.sh: passing $# lease argument word(s) to lease.py, unsplit and unexpanded"
    python3 -B "$ROOT/tools/coordination/lease.py" --root "$ROOT" acquire \
        --lease "$LEASE" --seat "$SEAT" --task "$TASK" --pid "$SEAT_PID" "$@"
}

echo "launch.sh: worktree=$ROOT  seat=$SEAT  task=$TASK  lease=$LEASE"
echo "launch.sh: acquiring the lease BEFORE anything is started. pid that will be leased: $SEAT_PID"
echo "launch.sh: pathname expansion is OFF for this script (set -f) — a write scope is DATA, not a"
echo "launch.sh: pattern to expand. CD-ASR-WO2R3-06-F05."

# THE LEASE IS ACQUIRED FIRST. `set -e` is deliberately suspended around it so the refusal can be
# reported with its own text rather than killing the script silently.
set +e
acquire_lease "$@"
rc=$?
set -e

if [ "$rc" -ne 0 ]; then
    echo "launch.sh: LEASE REFUSED (rc=$rc). NOTHING IS LAUNCHED." >&2
    echo "launch.sh: the command that would have run was: $*" >&2
    exit "$rc"
fi

# ------------------------------------------------------------------------------------------------
# PASS 3 — reduce "$@" to the COMMAND, by the same rotation, and exec it.
# ------------------------------------------------------------------------------------------------
n=$#
seen_dashdash=0
while [ "$n" -gt 0 ]; do
    if [ "$seen_dashdash" -eq 1 ]; then
        set -- "$@" "$1"; shift; n=$((n - 1)); continue
    fi
    case "$1" in
        --lease|--seat|--task|--write-scope|--read-scope) shift 2; n=$((n - 2)) ;;
        --dry-run)                                        shift; n=$((n - 1)) ;;
        --)                    seen_dashdash=1;           shift; n=$((n - 1)) ;;
        *)                                                shift; n=$((n - 1)) ;;
    esac
done

[ $# -gt 0 ] || { echo "launch.sh: no COMMAND given after --" >&2; usage; }

echo "launch.sh: lease held. exec: $*"

if [ "$DRY" -eq 1 ]; then
    echo "launch.sh: --dry-run, so the lease is held and the command is NOT exec'd."
    exit 0
fi

exec "$@"
