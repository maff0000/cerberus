"""A strict, STDLIB-ONLY reader for the subset of YAML ``deploy/compose.yaml`` uses.

WHY THIS EXISTS RATHER THAN ``import yaml``. The register checks are stdlib-only standalone
scripts that must run on any host with a bare interpreter and NO install step. PyYAML
happens to be installed on the DEV host, but it is not a declared dependency of this
project, so a check that needed it would be a check the next host cannot run.

This module is lifted deliberately from ``tests/compose_reader.py``, whose docstring says
"B1 can lift the approach into its standalone script" — with ONE addition: every mapping
key and every sequence item carries the LINE NUMBER it was read from, because a check must
print WHAT it found and WHERE, and "somewhere in compose.yaml" is not where.

It supports block mappings, block sequences of scalars, block sequences of mappings, plain
and quoted scalars, folded and literal block scalars, and comments. It **refuses** rather
than guesses on anything else — non-empty flow collections, tabs, inconsistent indentation
— by raising :exc:`YamlSubsetError`, which every caller turns into a non-zero exit with a
stated reason (``PBG-CI-002``). A parser that guesses at a construct it does not understand
is a check that passes for a reason nobody can state.

YAML merge keys (``<<: *anchor``) are recorded under the literal key ``"<<"`` and are NOT
resolved. Every posture field the checks read is written literally on each service in
``deploy/compose.yaml`` precisely so no merge resolution is needed. A posture that could
only be seen after resolving an anchor would be a posture hiding behind an indirection —
and :func:`unresolved_aliases` reports where such a hiding place exists, so a check can
refuse rather than read a field as absent when it is merely aliased.

TERMINATION IS A PROPERTY OF THE LOOPS, NOT OF THE DOCUMENTS THEY HAPPEN TO MEET.
--------------------------------------------------------------------------------
Every loop in this module drives a single monotone cursor into ``lines`` — a finite list
built once, before parsing starts, and never mutated while a parse is in progress. The
invariant is therefore stated once and enforced everywhere:

    **On every iteration, a loop either leaves (break / return / raise) or moves the
    cursor strictly forward. No loop's continuation condition can be true on a cursor
    that did not move.**

There are exactly two ways a loop body can move the cursor, and both are covered:

1. **The loop moves it itself**, with an unconditional ``index += 1`` on its own path.
2. **The loop delegates** to a sub-parser and adopts the cursor it returns. A sub-parser
   that returns the cursor it was given makes the next iteration bit-for-bit identical to
   this one, for ever — so every delegation goes through :func:`_advance`, which refuses
   a cursor that did not move instead of re-entering on it.

:func:`_advance` is what makes this a closure over the CLASS "an input on which the reader
does not finish", rather than over the particular documents that were tried. It does not
know which shapes stall; it only knows that a stalled cursor is a construct the reader
cannot read at that position, and says so (``YamlSubsetError``) rather than looping. The
one delegation where a still cursor is LEGITIMATE — a mapping key with no block beneath it
— is documented at its call site and gets its progress from rule 1 instead.

Each loop additionally carries an iteration budget of ``len(lines)``. It is unreachable
while rules 1 and 2 hold, and exists so that a future edit which breaks one of them fails
CLOSED with a stated reason at a named line, instead of reintroducing a hang. Termination
is thus not an argument about the current branch set; it is checked while running.

KNOWN LIMIT — nesting deeper than the interpreter's recursion limit raises ``RecursionError``
rather than ``YamlSubsetError``. It terminates, so it is not a hang, but it does not name the
line it could not read. Converting it would move the callers' exit code from 1 to 3, which is
a verdict change, so it is REPORTED (``CD-ENG-READER-F02``) and not taken here.
"""

from __future__ import annotations

import pathlib
from typing import Union

__all__ = [
    "YamlSubsetError",
    "LocDict",
    "LocList",
    "LocStr",
    "parse_block_yaml",
    "load_yaml",
    "line_of",
]

Node = Union[dict, list, str, None]


class YamlSubsetError(Exception):
    """The reader met a construct it does not support, and refused to guess."""


class LocDict(dict):
    """A mapping that remembers which line each key came from."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lines: dict = {}
        self.line: int = 0


class LocList(list):
    """A sequence that remembers which line each item came from."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lines: dict = {}
        self.line: int = 0


class LocStr(str):
    """A scalar that remembers its line."""

    line: int = 0

    def __new__(cls, value: str, line: int = 0):
        obj = super().__new__(cls, value)
        obj.line = line
        return obj


def line_of(container, key, default: int = 0) -> int:
    """The line a key or index came from, or ``default`` when unknown."""
    lines = getattr(container, "lines", None)
    if isinstance(lines, dict) and key in lines:
        return int(lines[key])
    value = None
    try:
        value = container[key]
    except Exception:  # noqa: BLE001 - the container may be any shape
        value = None
    return int(getattr(value, "line", default) or default)


def _strip_comment(line: str) -> str:
    out: list[str] = []
    quote = None
    previous = ""
    for index, char in enumerate(line):
        if quote is None and char == "#" and (index == 0 or line[index - 1] in " \t"):
            break
        if quote is None and char in "'\"":
            quote = char
        elif quote is not None and char == quote and previous != "\\":
            quote = None
        out.append(char)
        previous = char
    return "".join(out).rstrip()


def _scalar(text: str, line: int) -> Node:
    text = text.strip()
    if not text:
        return None
    if text == "[]":
        empty = LocList()
        empty.line = line
        return empty
    if text == "{}":
        empty_map = LocDict()
        empty_map.line = line
        return empty_map
    if text[0] in "[{":
        raise YamlSubsetError(
            f"line {line}: non-empty flow collections are not supported by this reader: "
            f"{text!r}. Write the value as a block, so it can be read without a YAML engine."
        )
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "'\"":
        return LocStr(text[1:-1], line)
    if text in {"null", "~"}:
        return None
    return LocStr(text, line)


def _indent_of(line: str) -> int:
    if "\t" in line[: len(line) - len(line.lstrip())]:
        raise YamlSubsetError(f"tab in indentation: {line!r}")
    return len(line) - len(line.lstrip(" "))


def _advance(lines, before: int, after: int, what: str) -> int:
    """Adopt a delegated cursor, refusing one that did not move.

    THE TERMINATION INVARIANT, enforced rather than argued. ``before`` is the cursor a
    loop delegated from; ``after`` is the cursor the sub-parser returned. If they are
    equal the sub-parser consumed nothing, so re-entering the loop would repeat this
    iteration unchanged, for ever. That is a stall, and a stall is not a document shape
    to be enumerated — it is the reader meeting a construct it cannot read at this
    position.

    So it says which line it could not read and what it was trying to read there, and
    raises. A stated refusal is the project standard (``CD-D-048``): silence and a partial
    parse are both worse, because a partial parse of a gate's subject makes the gate decide
    on a document nobody wrote.
    """
    if after > before:
        return after
    if before >= len(lines):
        # The enclosing loop's own `index < len(lines)` test ends it on the next
        # evaluation, so there is no stall to refuse here.
        return after
    number, _, text = lines[before]
    raise YamlSubsetError(
        f"line {number}: this reader cannot read {what}. It made no progress past "
        f"{text!r} and refuses rather than guessing. It supports block mappings, block "
        f"sequences of scalars and block sequences of mappings; write the value as a "
        f"block beneath its own key so it can be read without a YAML engine."
    )


def _stalled(lines, index: int, where: str) -> "YamlSubsetError":
    """The iteration budget was spent — a loop ran without making progress.

    Unreachable while :func:`_advance` guards every delegation and every loop increments
    its own cursor. It exists so that a future edit which breaks either rule fails CLOSED,
    at a named line, instead of hanging the caller. A gate that hangs is a gate somebody
    eventually disables.
    """
    if index < len(lines):
        number, _, text = lines[index]
        return YamlSubsetError(
            f"line {number}: {where} made no progress past {text!r} within its iteration "
            f"budget. This is an internal invariant failure in this reader, not a defect "
            f"in the document; it refuses so that a caller gets a verdict."
        )
    return YamlSubsetError(
        f"{where} made no progress within its iteration budget at end of document. This "
        f"is an internal invariant failure in this reader, not a defect in the document."
    )


def _parse(lines, start: int, indent: int):
    if start >= len(lines):
        return None, start
    _, first_indent, first_text = lines[start]
    if first_indent < indent:
        return None, start
    if first_text.startswith("- "):
        return _parse_sequence(lines, start, first_indent)
    return _parse_mapping(lines, start, first_indent)


def _parse_sequence(lines, start: int, indent: int):
    items = LocList()
    items.line = lines[start][0]
    index = start
    budget = len(lines) - start + 1
    while index < len(lines):
        budget -= 1
        if budget < 0:  # pragma: no cover - unreachable while the invariant holds
            raise _stalled(lines, index, "the block-sequence loop")
        iteration_start = index
        line_number, line_indent, text = lines[index]
        if line_indent < indent:
            break
        if line_indent > indent:
            raise YamlSubsetError(f"unexpected indentation at line {line_number}")
        if not text.startswith("- "):
            break
        remainder = text[2:].strip()
        index += 1
        if not remainder:
            child, moved = _parse(lines, index, indent + 1)
            # Rule 1 supplies the progress here: the `index += 1` above already moved the
            # cursor past the item line, so a still cursor out of `_parse` is a legitimate
            # empty item followed by a dedent. The guard is measured from the top of the
            # ITERATION, not from the delegation, so it passes today and would fire if a
            # future edit ever removed that increment.
            index = _advance(
                lines, iteration_start, moved, "the value of an empty block-sequence item"
            )
            items.lines[len(items)] = line_number
            items.append(child)
            continue
        if ":" in remainder and not remainder.split(":", 1)[0].strip().startswith(("'", '"')):
            key, _, value = remainder.partition(":")
            inline = LocDict({key.strip(): _scalar(value, line_number)})
            inline.line = line_number
            inline.lines[key.strip()] = line_number
            child_indent = indent + 2
            # THE STALL SITE (CD-PL-F61 / CD-ENG-WO2R-F14). This loop re-tests its own
            # condition on the cursor `_parse_mapping` hands back and has no increment of
            # its own, so the delegation is the ONLY source of progress — rule 2 applies in
            # its pure form. `_parse_mapping` returns the cursor untouched whenever the line
            # it is pointed at cannot open a mapping, and the condition is still true, so the
            # loop re-entered at the same offset for ever. It now refuses that line instead.
            merge_budget = len(lines) - index + 1
            while index < len(lines) and lines[index][1] >= child_indent:
                merge_budget -= 1
                if merge_budget < 0:  # pragma: no cover - unreachable while `_advance` holds
                    raise _stalled(lines, index, "the sequence-item merge loop")
                more, moved = _parse_mapping(lines, index, lines[index][1])
                index = _advance(
                    lines,
                    index,
                    moved,
                    "a nested block beneath a key written inline on a block-sequence item",
                )
                if isinstance(more, dict):
                    inline.update(more)
                    inline.lines.update(getattr(more, "lines", {}))
                else:  # pragma: no cover - defensive
                    raise YamlSubsetError("expected a mapping inside a sequence item")
            items.lines[len(items)] = line_number
            items.append(inline)
            continue
        items.lines[len(items)] = line_number
        items.append(_scalar(remainder, line_number))
    return items, index


def _parse_mapping(lines, start: int, indent: int):
    mapping = LocDict()
    mapping.line = lines[start][0]
    index = start
    budget = len(lines) - start + 1
    while index < len(lines):
        budget -= 1
        if budget < 0:  # pragma: no cover - unreachable while the invariant holds
            raise _stalled(lines, index, "the block-mapping loop")
        line_number, line_indent, text = lines[index]
        if line_indent < indent:
            break
        if line_indent > indent:
            raise YamlSubsetError(
                f"unexpected indentation at line {line_number}: {text!r}"
            )
        if text.startswith("- "):
            break
        if ":" not in text:
            raise YamlSubsetError(
                f"line {line_number} is neither a mapping entry nor a sequence item: "
                f"{text!r}"
            )
        key, _, value = text.partition(":")
        key = key.strip()
        if key.startswith(("'", '"')) and key.endswith(("'", '"')) and len(key) >= 2:
            key = key[1:-1]
        value = value.strip()
        index += 1
        if value.startswith("&"):
            value = ""
        mapping.lines[key] = line_number
        if value:
            if value.startswith("*"):
                mapping[key] = LocStr(value, line_number)  # an alias, recorded unresolved
            else:
                mapping[key] = _scalar(value, line_number)
            continue
        # Rule 1 supplies the progress here, and a still cursor is LEGITIMATE: `key:` with
        # no block beneath it is followed by a sibling key at this same indent, which
        # `_parse` correctly declines to consume. The unconditional `index += 1` above has
        # already moved this iteration on, so the loop advances regardless of what `_parse`
        # returns. This is the one delegation in the module that is NOT guarded by
        # `_advance`, and it is stated here rather than left to be re-derived.
        child, index = _parse(lines, index, indent + 1)
        mapping[key] = child
    return mapping, index


_BLOCK_SCALAR_INDICATORS = ("|", ">", "|-", ">-", "|+", ">+")


def _fold_block_scalars(raw_lines: list[str]) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    index = 0
    budget = len(raw_lines) + 1
    while index < len(raw_lines):
        # Rule 1: this loop increments unconditionally, immediately, before any branch can
        # `continue`. The budget states that as a checked fact rather than an inspection.
        budget -= 1
        if budget < 0:  # pragma: no cover - unreachable while the invariant holds
            raise YamlSubsetError(
                f"line {index + 1}: the block-scalar folding loop made no progress within "
                f"its iteration budget. This is an internal invariant failure in this "
                f"reader, not a defect in the document; it refuses so that a caller gets "
                f"a verdict."
            )
        raw = raw_lines[index]
        number = index + 1
        index += 1
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        stripped = _strip_comment(raw)
        if not stripped.strip():
            continue
        body = stripped.strip()
        indicator = body.rpartition(":")[2].strip() if ":" in body else ""
        is_block = (
            ":" in body
            and indicator in _BLOCK_SCALAR_INDICATORS
            and not body.startswith("- ")
        ) or (body.startswith("- ") and body[2:].strip() in _BLOCK_SCALAR_INDICATORS)
        if not is_block:
            out.append((number, stripped))
            continue
        key_indent = _indent_of(stripped)
        parts: list[str] = []
        # Rule 1 again: every path through this body either breaks or increments.
        body_budget = len(raw_lines) - index + 1
        while index < len(raw_lines):
            body_budget -= 1
            if body_budget < 0:  # pragma: no cover - unreachable while the invariant holds
                raise YamlSubsetError(
                    f"line {index + 1}: the block-scalar body loop made no progress within "
                    f"its iteration budget. This is an internal invariant failure in this "
                    f"reader, not a defect in the document."
                )
            candidate = raw_lines[index]
            if not candidate.strip():
                index += 1
                parts.append("")
                continue
            if _indent_of(candidate) <= key_indent:
                break
            parts.append(candidate.strip())
            index += 1
        folded = " ".join(part for part in parts if part)
        folded = folded.replace("\\", "\\\\").replace('"', "'")
        prefix = body[: body.rindex(":") + 1] if ":" in body else body
        out.append((number, " " * key_indent + f'{prefix} "{folded}"'))
    return out


def parse_block_yaml(text: str) -> Node:
    """Parse the supported subset. Raises :exc:`YamlSubsetError` on anything else."""
    lines: list[tuple[int, int, str]] = []
    for number, stripped in _fold_block_scalars(text.splitlines()):
        if stripped.lstrip().startswith("---"):
            continue
        lines.append((number, _indent_of(stripped), stripped.strip()))
    if not lines:
        raise YamlSubsetError("empty document")
    node, consumed = _parse(lines, 0, lines[0][1])
    if consumed != len(lines):
        raise YamlSubsetError(
            f"stopped at line {lines[consumed][0]}: {lines[consumed][2]!r}"
        )
    return node


def load_yaml(path: pathlib.Path) -> dict:
    document = parse_block_yaml(pathlib.Path(path).read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise YamlSubsetError(f"{path} is not a mapping at the top level")
    return document


def unresolved_aliases(node, trail=()) -> list:
    """Every ``*alias`` value in the document, with the path that reaches it.

    A check reads a posture field by name. If that field could arrive through an
    unresolved merge, the check would read it as ABSENT — which is exactly how a posture
    hides behind an indirection. Callers use this to refuse rather than to guess.
    """
    found: list[tuple[tuple, str, int]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if isinstance(value, str) and value.startswith("*"):
                found.append((trail + (key,), str(value), line_of(node, key)))
            else:
                found.extend(unresolved_aliases(value, trail + (key,)))
    elif isinstance(node, list):
        for position, value in enumerate(node):
            if isinstance(value, str) and value.startswith("*"):
                found.append((trail + (position,), str(value), line_of(node, position)))
            else:
                found.extend(unresolved_aliases(value, trail + (position,)))
    return found
