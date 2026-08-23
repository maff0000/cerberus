#!/usr/bin/env python3
"""Engineer's own tests for the scope algebra. NOT assurance (``PBG-SOD-001``, non-waivable).

Run: ``python3 -B tools/coordination/test_scope.py``  -> exit 0 on all-pass, 1 on any failure.

TWO OF THESE CASES ARE HERE BECAUSE THE ALGEBRA CORRECTED ME.
On first run I asserted ``BL-*-03??.yaml`` intersects ``BL-*-02??.yaml`` and that ``x*y``
intersects ``y*x``. The product automaton said DISJOINT for both and the automaton was right:
the first pair would need the last ten characters to be simultaneously ``-03??.yaml`` and
``-02??.yaml``; the second would need character 0 to be simultaneously ``x`` and ``y``. The cases
are retained with the corrected expectation and this note, because a hand-derived expectation that
lost to the instrument is exactly the evidence ``CD-RULE-003`` is about.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scope import ScopeInvalid, overlaps, parse_scope, segments_intersect  # noqa: E402

SEGMENT_CASES = [
    # (a, b, expect_intersect, note)
    ("abc", "abc", True, "identical literals"),
    ("abc", "abd", False, "literals differing in one char"),
    ("*.py", "*.yaml", False, "different fixed suffixes"),
    ("*.py", "scope.py", True, "wildcard vs literal it matches"),
    ("a*c", "ab?c", True, "witness 'abbc'"),
    ("a?c", "abc", True, "single-char wildcard vs literal"),
    ("a?c", "abbc", False, "? is exactly one character"),
    ("BL-*-03*.yaml", "BL-*-02*.yaml", True, "witness 'BL-A-02x-03y.yaml' — both `*` are free"),
    ("BL-*-03??.yaml", "BL-*-02??.yaml", False,
     "CORRECTED BY THE INSTRUMENT: the last ten characters cannot be both suffixes"),
    ("x*y", "y*x", False, "CORRECTED BY THE INSTRUMENT: character 0 cannot be both x and y"),
    ("*", "anything", True, "bare star matches everything in a segment"),
    ("", "", True, "two empty segments"),
    ("", "a", False, "empty segment vs non-empty"),
]

SCOPE_CASES = [
    (["tools/coordination/**"], ["tools/reconciliation/**"], False, "sibling recursive prefixes"),
    (["tools/coordination/**"], ["tools/coordination/scope.py"], True, "prefix contains the file"),
    (["tools/coordination"], ["tools/coordination/scope.py"], False,
     "a LITERAL directory path does NOT cover its contents — write dir/** for that"),
    (["governance/coordination/**"], ["governance/engineering/ACTIVE_WORK.yaml"], False, "disjoint governance subtrees"),
    (["governance/Coordination/**"], ["governance/coordination/**"], True, "CASE_COLLISION, fail closed"),
    (["a/**/b"], ["z/**"], True, "UNDECIDABLE `**` mid-pattern -> fail closed to OVERLAP"),
    (["src/[ab]/x"], ["docs/**"], True, "UNDECIDABLE character class -> fail closed to OVERLAP"),
    (["**"], ["anything/at/all"], True, "bare ** is the whole tree and overlaps everything"),
    (["governance/engineering/build-log/BL-*-03??.yaml"],
     ["governance/engineering/build-log/BL-*-01??.yaml"], False,
     "PER-SEAT BUILD LOG ID BLOCKS ARE PROVED DISJOINT BY THE ALGEBRA — this is ITEM 2(c)'s premise"),
]

INVALID_CASES = [
    (["../etc/passwd"], ".. traversal"),
    (["/etc/passwd"], "absolute path"),
    ([""], "empty entry"),
    (["."], "dot entry"),
    ([], "empty scope list"),
]


def main() -> int:
    failures = 0
    total = 0

    for a, b, expect, note in SEGMENT_CASES:
        total += 1
        got = segments_intersect(a, b)
        if got != expect:
            failures += 1
            print("FAIL segment %-18r %-18r expected=%s got=%s  (%s)" % (a, b, expect, got, note))
        else:
            print("pass segment %-18r %-18r %s  (%s)" % (a, b, got, note))

    for a, b, expect, note in SCOPE_CASES:
        total += 1
        got, hits = overlaps(a, b)
        if got != expect:
            failures += 1
            print("FAIL scope   %-42s %-42s expected=%s got=%s  (%s)" % (a, b, expect, got, note))
            for h in hits:
                print("        %s" % h)
        else:
            print("pass scope   %-42s %-42s %s  (%s)" % (a, b, got, note))

    for entries, note in INVALID_CASES:
        total += 1
        try:
            parse_scope(entries)
        except ScopeInvalid:
            print("pass invalid %-42s refused at parse time  (%s)" % (entries, note))
        else:
            failures += 1
            print("FAIL invalid %-42s WAS ACCEPTED  (%s)" % (entries, note))

    print("")
    print("total=%d failures=%d" % (total, failures))
    print("    produced by: python3 -B tools/coordination/test_scope.py")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
