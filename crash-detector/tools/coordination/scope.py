#!/usr/bin/env python3
"""THE SCOPE ALGEBRA — ``PO-DECISIONS-0021`` ruling 3(b), increment 12 ITEM 2(a).

A *scope* is a list of repository-relative path globs. This module normalises a scope and answers
one question: **do two scopes overlap?**

WHY THIS IS THE HARD PART OF THE INCREMENT
------------------------------------------
``PO-DECISIONS-0021`` ruling 3 does not ban concurrency. It states the invariant: *"no two live
seats share a TASK or a WRITE SCOPE."* Everything else in increment 12 is bookkeeping around this
predicate. If ``overlaps()`` is wrong in the permissive direction two seats collide; if it is wrong
in the restrictive direction the ruling is not implemented at all, because every parallel launch is
refused and the invariant holds vacuously.

So this module does exactly two things and says which one it did, every time:

* **DECIDES** — it proves overlap or proves disjointness for the glob forms enumerated below.
* **REFUSES** — for every other form it reports ``OVERLAP`` with reason ``UNDECIDABLE``.
  ``CD-RULE-003``: derive or fail closed, never a plausible answer. **An undecided pair is
  reported as overlapping, which costs parallelism and never costs correctness.**

THE FORMS IT DECIDES (and it prints this list on every run — ``CD-RULE-004``)
----------------------------------------------------------------------------
1. **Literal path** — ``governance/coordination/required-tests.yaml``. Matches that path EXACTLY.
   A literal naming a directory does NOT cover the directory's contents; write ``dir/**`` for that.
2. **Recursive prefix** — ``tools/coordination/**``. ``**`` is legal ONLY as the final segment and
   covers every path under the prefix, at any depth, plus the prefix itself.
3. **Single-segment wildcards** — ``*`` and ``?`` anywhere inside one segment, e.g.
   ``governance/engineering/build-log/BL-*-03??.yaml``. ``*`` matches zero or more characters
   WITHIN a segment and never crosses ``/``; ``?`` matches exactly one such character.
   Intersection of two wildcard segments is decided EXACTLY, by product-automaton emptiness —
   not by a heuristic and not by string equality. ``BL-*-03*.yaml`` and ``BL-*-02*.yaml`` DO
   intersect (``BL-A-02x-03y.yaml`` is in both) and this module says so.

THE FORMS IT REFUSES — each one fails closed to OVERLAP / UNDECIDABLE
---------------------------------------------------------------------
* ``..`` in any segment — path traversal. REFUSED at parse time; the scope is INVALID, not merely
  undecided, and :func:`parse_scope` raises.
* an absolute path (leading ``/``) — INVALID at parse time. Scopes are repository-relative.
* ``**`` anywhere but as the whole final segment (``a/**/b``, ``a**b``) — UNDECIDABLE.
* character classes ``[...]`` and brace expansion ``{a,b}`` — UNDECIDABLE.
* a scope entry that is the empty string or ``.`` or ``/`` — INVALID at parse time. A scope that
  means "everything" must be written ``**`` explicitly and will then overlap everything, which is
  the honest answer.

CASE COLLISION — DECIDED, NOT DECLARED
--------------------------------------
Two scopes that are disjoint case-sensitively but overlap when case-folded are reported as
**OVERLAP / CASE_COLLISION**. That is fail-closed and it is correct on a case-insensitive
filesystem. :func:`filesystem_is_case_insensitive` MEASURES the actual behaviour of a given
directory rather than assuming, and the check instruments print the measurement.

SYMLINKS — DECLARED, AND WHERE THE RESIDUE LIVES
------------------------------------------------
This module operates on STRINGS. It cannot see that ``a/x`` and ``b/x`` are the same inode because
``b`` is a symlink to ``a``. :func:`symlinked_components` is provided so the *live* checks
(which do have a worktree) can refuse a scope whose prefix traverses a symlink, and
``check_scope_disjoint.py`` calls it. **For a scope evaluated with no worktree available — the
pure-algebra path — the symlink class is NOT PROVED TO BE CARRIED ANYWHERE** (``CD-RULE-006``),
and this module prints those words.
"""

from __future__ import annotations

import os
import sys
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import Limit, tree_banner  # noqa: E402


DECIDED_FORMS = [
    "LITERAL path with no metacharacter — matches that exact path and nothing under it.",
    "RECURSIVE PREFIX `p/**` — `**` legal ONLY as the final segment; covers `p` and everything under it at any depth.",
    "SINGLE-SEGMENT WILDCARDS `*` and `?` — never cross `/`; pair intersection decided EXACTLY by product-automaton emptiness.",
    "CASE COLLISION — two otherwise-disjoint scopes that collide when case-folded are reported OVERLAP/CASE_COLLISION (fail closed).",
]

REFUSED_FORMS = [
    "`**` anywhere but as the whole final segment (`a/**/b`, `a**b`) -> OVERLAP/UNDECIDABLE.",
    "character classes `[abc]` and brace expansion `{a,b}` -> OVERLAP/UNDECIDABLE.",
    "`..` traversal, absolute paths, and the empty/`.`/`/` entry -> INVALID at parse time (raises).",
    "SYMLINK aliasing between two textually-disjoint scopes -> NOT decided here; see `symlinked_components`.",
]

ALGEBRA_LIMITS = ["DECIDES: " + f for f in DECIDED_FORMS] + ["REFUSES: " + f for f in REFUSED_FORMS]

ALGEBRA_RESIDUE = (
    "symlink aliasing, when this algebra is used WITHOUT a worktree, is NOT PROVED TO BE CARRIED "
    "ANYWHERE. With a worktree it is carried by `check_scope_disjoint.py`, which calls "
    "`scope.symlinked_components()` and REFUSES a scope whose prefix traverses a symlink — that "
    "hand-off is measured by PLANT-COORD-02 arm 3b and is not asserted."
)


class ScopeInvalid(ValueError):
    """A scope entry that is not merely undecidable but malformed. Parsing REFUSES it."""


# ------------------------------------------------------------------------------------------------
# parsing / normalisation
# ------------------------------------------------------------------------------------------------

class Pattern:
    """One normalised glob: a segment list, plus whether it ends in a recursive `**`."""

    __slots__ = ("raw", "segments", "recursive", "undecidable_reason")

    def __init__(self, raw: str, segments: List[str], recursive: bool,
                 undecidable_reason: Optional[str] = None):
        self.raw = raw
        self.segments = segments
        self.recursive = recursive
        self.undecidable_reason = undecidable_reason

    def __repr__(self) -> str:
        return "Pattern(%r)" % self.raw


_UNDECIDABLE_CHARS = ("[", "]", "{", "}")


def parse_pattern(raw: str) -> Pattern:
    if raw is None:
        raise ScopeInvalid("scope entry is null")
    s = raw.strip()
    if s == "" or s in (".", "/", "./"):
        raise ScopeInvalid("scope entry %r is empty or means the whole tree implicitly; "
                           "write `**` if that is what you mean" % raw)
    if s.startswith("/"):
        raise ScopeInvalid("scope entry %r is absolute; scopes are repository-relative" % raw)
    if s.startswith("./"):
        s = s[2:]
    while "//" in s:
        s = s.replace("//", "/")
    s = s.rstrip("/")
    segs = s.split("/")
    if any(seg == ".." for seg in segs):
        raise ScopeInvalid("scope entry %r contains `..`; path traversal is refused, not decided" % raw)
    if any(seg == "" for seg in segs):
        raise ScopeInvalid("scope entry %r has an empty segment" % raw)

    reason = None
    recursive = False
    if segs[-1] == "**":
        recursive = True
        segs = segs[:-1]
        if not segs:
            # bare `**` — the whole tree. Legal and decidable: it overlaps everything.
            segs = []
    for seg in segs:
        if "**" in seg:
            reason = "`**` is legal only as the whole final segment; found it inside %r" % seg
        for ch in _UNDECIDABLE_CHARS:
            if ch in seg:
                reason = "character class / brace expansion %r is not decided by this algebra" % ch
    return Pattern(raw, segs, recursive, reason)


def parse_scope(entries: Iterable[str]) -> List[Pattern]:
    out = [parse_pattern(e) for e in entries]
    if not out:
        raise ScopeInvalid("an empty scope is refused: a seat with no declared write scope writes nothing, "
                           "and that must be said explicitly, not left blank")
    return out


# ------------------------------------------------------------------------------------------------
# single-segment glob intersection, decided EXACTLY by product-automaton emptiness
# ------------------------------------------------------------------------------------------------

# NFA transition kinds
_LIT = "lit"
_ANY = "any"
_EPS = "eps"


def _seg_nfa(seg: str) -> Tuple[int, Dict[int, List[Tuple[str, Optional[str], int]]], int]:
    """Build an epsilon-NFA for one segment glob. `*` -> ANY* , `?` -> ANY, else literal char."""
    trans: Dict[int, List[Tuple[str, Optional[str], int]]] = {}
    state = 0

    def add(src: int, kind: str, ch: Optional[str], dst: int) -> None:
        trans.setdefault(src, []).append((kind, ch, dst))

    for ch in seg:
        if ch == "*":
            add(state, _ANY, None, state)          # self-loop: zero or more
            add(state, _EPS, None, state + 1)
            state += 1
        elif ch == "?":
            add(state, _ANY, None, state + 1)
            state += 1
        else:
            add(state, _LIT, ch, state + 1)
            state += 1
    return 0, trans, state


def _closure(states: Set[int], trans: Dict[int, List[Tuple[str, Optional[str], int]]]) -> frozenset:
    stack = list(states)
    seen = set(states)
    while stack:
        s = stack.pop()
        for kind, _ch, dst in trans.get(s, ()):
            if kind == _EPS and dst not in seen:
                seen.add(dst)
                stack.append(dst)
    return frozenset(seen)


def _step(states: frozenset, ch: str, trans) -> frozenset:
    nxt: Set[int] = set()
    for s in states:
        for kind, tch, dst in trans.get(s, ()):
            if kind == _LIT and tch == ch:
                nxt.add(dst)
            elif kind == _ANY:
                nxt.add(dst)
    return _closure(nxt, trans)


def _outgoing_literals(states: frozenset, trans) -> Set[str]:
    out: Set[str] = set()
    for s in states:
        for kind, tch, _dst in trans.get(s, ()):
            if kind == _LIT and tch is not None:
                out.add(tch)
    return out


def segments_intersect(a: str, b: str) -> bool:
    """Do the two single-segment globs have at least one common match? DECIDED, not guessed.

    Product-automaton reachability. At each product state the alphabet is finite: the concrete
    literal characters available from either side, plus ONE fresh character standing for "any
    character neither side names", which is exactly what is needed to exercise `*`/`?` edges.
    """
    if a == b:
        return True
    sa, ta, fa = _seg_nfa(a)
    sb, tb, fb = _seg_nfa(b)
    start = (_closure({sa}, ta), _closure({sb}, tb))
    seen = {start}
    stack = [start]
    while stack:
        pa, pb = stack.pop()
        if fa in pa and fb in pb:
            return True
        lits = _outgoing_literals(pa, ta) | _outgoing_literals(pb, tb)
        # one representative for "every other character"
        fresh = None
        for cand in "\x01abcdefghijklmnopqrstuvwxyz0123456789":
            if cand not in lits:
                fresh = cand
                break
        alphabet = set(lits)
        if fresh is not None:
            alphabet.add(fresh)
        for ch in alphabet:
            nxt = (_step(pa, ch, ta), _step(pb, ch, tb))
            if not nxt[0] or not nxt[1]:
                continue
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return False


# ------------------------------------------------------------------------------------------------
# pattern overlap
# ------------------------------------------------------------------------------------------------

OVERLAP = "OVERLAP"
DISJOINT = "DISJOINT"


def patterns_overlap(a: Pattern, b: Pattern) -> Tuple[bool, str]:
    """Return ``(overlaps, reason)``. Fails CLOSED: undecidable -> ``(True, 'UNDECIDABLE: ...')``."""
    if a.undecidable_reason:
        return True, "UNDECIDABLE: %s (in %r) — fail closed per CD-RULE-003" % (a.undecidable_reason, a.raw)
    if b.undecidable_reason:
        return True, "UNDECIDABLE: %s (in %r) — fail closed per CD-RULE-003" % (b.undecidable_reason, b.raw)

    k = min(len(a.segments), len(b.segments))
    for i in range(k):
        if not segments_intersect(a.segments[i], b.segments[i]):
            # decided disjoint on the segment-sensitive comparison; now the case-fold check
            if segments_intersect(a.segments[i].casefold(), b.segments[i].casefold()):
                return True, ("CASE_COLLISION: segment %d of %r and %r differ only by case; on a "
                              "case-insensitive filesystem they are the same path — fail closed"
                              % (i, a.raw, b.raw))
            return False, "DISJOINT: segment %d differs (%r vs %r)" % (i, a.segments[i], b.segments[i])

    if len(a.segments) == len(b.segments):
        return True, "OVERLAP: identical depth and every segment intersects"
    if len(a.segments) < len(b.segments):
        shorter, longer = a, b
    else:
        shorter, longer = b, a
    if shorter.recursive:
        return True, ("OVERLAP: %r is a recursive prefix of %r" % (shorter.raw, longer.raw))
    return False, ("DISJOINT: %r is %d segments deep and not recursive, so it cannot reach %r"
                   % (shorter.raw, len(shorter.segments), longer.raw))


def scopes_overlap(a: Sequence[Pattern], b: Sequence[Pattern]) -> Tuple[bool, List[str]]:
    """Return ``(overlaps, evidence_lines)``. Overlaps if ANY pattern pair overlaps."""
    hits: List[str] = []
    for pa in a:
        for pb in b:
            ov, reason = patterns_overlap(pa, pb)
            if ov:
                hits.append("%s  <>  %s   %s" % (pa.raw, pb.raw, reason))
    return (len(hits) > 0), hits


def overlaps(a: Iterable[str], b: Iterable[str]) -> Tuple[bool, List[str]]:
    """Convenience entry point on raw string scopes."""
    return scopes_overlap(parse_scope(a), parse_scope(b))


# ------------------------------------------------------------------------------------------------
# measured filesystem properties — MEASURED, never assumed
# ------------------------------------------------------------------------------------------------

def filesystem_is_case_insensitive(directory: str) -> Tuple[bool, str]:
    """MEASURE it. Returns ``(insensitive, producing_command_description)``."""
    probe = os.path.join(directory, ".cd-case-probe-UPPER")
    alias = os.path.join(directory, ".cd-case-probe-upper")
    try:
        with open(probe, "w"):
            pass
        result = os.path.exists(alias)
    finally:
        try:
            os.unlink(probe)
        except FileNotFoundError:
            pass
    return result, ("python3 -c \"open('%s','w').close(); import os; print(os.path.exists('%s'))\""
                    % (probe, alias))


def symlinked_components(root: str, pattern: Pattern) -> List[str]:
    """Return the literal path prefixes of ``pattern`` that are symlinks in ``root``.

    Only LITERAL leading segments can be checked — once a wildcard appears the prefix is not a
    single path. That bound is part of the declared limit.
    """
    found: List[str] = []
    parts: List[str] = []
    for seg in pattern.segments:
        if any(ch in seg for ch in "*?[]{}"):
            break
        parts.append(seg)
        p = os.path.join(root, *parts)
        if os.path.islink(p):
            found.append("/".join(parts))
    return found


# ------------------------------------------------------------------------------------------------
# CLI — so the algebra is invocable and its limit is printed on every exit path
# ------------------------------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Scope algebra — decide whether two scopes overlap.")
    ap.add_argument("--a", action="append", default=[], help="a path glob in scope A (repeatable)")
    ap.add_argument("--b", action="append", default=[], help="a path glob in scope B (repeatable)")
    ap.add_argument("--expect", choices=["overlap", "disjoint"], default=None,
                    help="assert the outcome; exit 1 if the algebra disagrees")
    ap.add_argument("--measure-fs", metavar="DIR", default=None,
                    help="measure case-insensitivity of DIR and print it with its command")
    args = ap.parse_args(argv)

    with Limit("tools/coordination/scope.py", ALGEBRA_LIMITS, ALGEBRA_RESIDUE):
        tree_banner()
        if args.measure_fs:
            ins, cmd = filesystem_is_case_insensitive(args.measure_fs)
            print("filesystem_case_insensitive(%s) = %s" % (args.measure_fs, ins))
            print("    produced by: %s" % cmd)
        if not args.a or not args.b:
            print("VERDICT: NOTHING COMPARED (need --a and --b)")
            return 0 if args.measure_fs else 2
        try:
            pa, pb = parse_scope(args.a), parse_scope(args.b)
        except ScopeInvalid as exc:
            print("VERDICT: SCOPE_INVALID — %s" % exc)
            return 2
        ov, hits = scopes_overlap(pa, pb)
        print("A = %s" % args.a)
        print("B = %s" % args.b)
        print("VERDICT: %s" % (OVERLAP if ov else DISJOINT))
        for h in hits:
            print("   %s" % h)
        if not ov:
            for x in pa:
                for y in pb:
                    _, why = patterns_overlap(x, y)
                    print("   %s  <>  %s   %s" % (x.raw, y.raw, why))
        if args.expect:
            want = (args.expect == "overlap")
            if want != ov:
                print("ASSERTION FAILED: expected %s, algebra says %s" % (args.expect, OVERLAP if ov else DISJOINT))
                return 1
        return 1 if ov and args.expect is None else 0


if __name__ == "__main__":
    sys.exit(main())
