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
    while index < len(lines):
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
            child, index = _parse(lines, index, indent + 1)
            items.lines[len(items)] = line_number
            items.append(child)
            continue
        if ":" in remainder and not remainder.split(":", 1)[0].strip().startswith(("'", '"')):
            key, _, value = remainder.partition(":")
            inline = LocDict({key.strip(): _scalar(value, line_number)})
            inline.line = line_number
            inline.lines[key.strip()] = line_number
            child_indent = indent + 2
            while index < len(lines) and lines[index][1] >= child_indent:
                more, index = _parse_mapping(lines, index, lines[index][1])
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
    while index < len(lines):
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
        child, index = _parse(lines, index, indent + 1)
        mapping[key] = child
    return mapping, index


_BLOCK_SCALAR_INDICATORS = ("|", ">", "|-", ">-", "|+", ">+")


def _fold_block_scalars(raw_lines: list[str]) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    index = 0
    while index < len(raw_lines):
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
        while index < len(raw_lines):
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
