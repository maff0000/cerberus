#!/bin/sh
# Commission PBG's project-owned hooks into THIS repository only.
#
# Independent Assurance finding F23: this script is a thin front end for `pbg hooks install`. It used to run
#
#     git -C "$ROOT" config core.hooksPath tools/hooks
#
# directly, which is the right idea and too few questions. It did not check that $ROOT was the
# repository top level, did not notice a hooksPath another mechanism already owned, offered no
# status and no uninstall, and — the one that matters here — happily wrote from inside a LINKED
# WORKTREE, where a repository-local write lands in the shared config and silently reconfigures the
# main checkout and every sibling worktree.
#
# Two implementations of a governance rule drift, and the copy nobody watches is the one that
# drifts. So there is one implementation, in the shipped package, and this calls it.
#
# A-3: this script is now DELIVERED by build_dist alongside the hook it commissions, so it locates
# the package from its OWN position first. A consuming project vendors PBG at pbg/, and a script
# that only knew the framework's layout was a delivery that could not be used.
set -e
ROOT=$(git rev-parse --show-toplevel)

SELF_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PKG_PARENT=$(dirname -- "$SELF_DIR")          # .../tools/hooks -> .../tools

if [ -d "$PKG_PARENT/pbg" ]; then
    PYTHONPATH="$PKG_PARENT"
elif [ -d "$ROOT/tools/pbg" ]; then
    PYTHONPATH="$ROOT/tools"
elif [ -d "$ROOT/pbg/tools/pbg" ]; then
    PYTHONPATH="$ROOT/pbg/tools"
else
    echo "pbg: cannot locate the pbg package from $SELF_DIR or under $ROOT" >&2
    exit 1
fi
export PYTHONPATH

exec python3 -B -m pbg.cli --root "$ROOT" hooks install "$@"
