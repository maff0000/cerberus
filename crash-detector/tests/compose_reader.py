"""A strict, STDLIB-ONLY reader for the subset of YAML ``deploy/compose.yaml`` uses.

WHY THIS EXISTS RATHER THAN ``import yaml``.

The egress posture has to be "a declared, machine-readable thing a register check can read
out of the compose file". The register checks (deliverable B1) are **stdlib-only standalone
scripts**, and PyYAML — though it happens to be installed on this host — is not among the
dependencies this project declares. A test that proved the posture readable via PyYAML
would be proving it with an instrument the actual check cannot use, which is not proof of
anything the check needs.

So this reader is the demonstration: the posture in ``deploy/compose.yaml`` is extractable
with nothing but the standard library. B1 can lift the approach into its standalone script.

WHAT IT SUPPORTS, AND WHAT IT REFUSES.

Block mappings, block sequences of scalars, block sequences of mappings, plain and quoted
scalars, folded and literal block scalars (``>``, ``|``, ``>-``, ``|-``), and comments.
That is the whole of it.

It **refuses** rather than guesses on anything else — flow collections, tabs, inconsistent
indentation. A parser that guesses at a construct it does not understand is a check that
passes for a reason nobody can state (``PBG-CI-002``: a precondition it cannot meet is a
non-zero exit with a stated reason, never a pass and never a skip).

YAML merge keys (``<<: *anchor``) are recorded under the literal key ``"<<"`` with the
anchor name as the value, and are NOT resolved. Every field this reader is used to check —
``x-egress``, ``ports``, ``networks``, ``user``, ``x-uid``, ``x-storage`` — is written
literally on each service in ``deploy/compose.yaml`` precisely so that no merge resolution
is needed to read the posture. A posture that could only be seen after resolving an anchor
would be a posture hiding behind an indirection.
"""

from __future__ import annotations

import pathlib
from typing import Union

__all__ = ["ComposeParseError", "parse_block_yaml", "load_compose"]

Node = Union[dict, list, str, None]


class ComposeParseError(Exception):
    """The reader met a construct it does not support, and refused to guess."""


def _strip_comment(line: str) -> str:
    """Remove a trailing comment, respecting quotes.

    Naive ``split('#')`` would cut a URL or a shell fragment in half, and this reader is
    used on a file whose values include both.
    """
    out: list[str] = []
    quote: str | None = None
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


def _scalar(text: str) -> Node:
    text = text.strip()
    if not text:
        return None
    if text == "[]":
        # The EMPTY flow sequence is supported, and it is the only flow construct that is.
        # `hosts: []` is the canonical way to write "this allowlist admits nothing", and
        # forcing it into block form would mean writing an empty block, which YAML spells
        # as nothing at all — indistinguishable from a field somebody forgot.
        return []
    if text == "{}":
        return {}
    if text[0] in "[{":
        raise ComposeParseError(
            f"non-empty flow collections are not supported by this reader: {text!r}. "
            "Write the value as a block, so it can be read without a YAML engine."
        )
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "'\"":
        return text[1:-1]
    if text in {"true", "false"}:
        return text
    if text in {"null", "~"}:
        return None
    return text


def _indent_of(line: str) -> int:
    if "\t" in line[: len(line) - len(line.lstrip())]:
        raise ComposeParseError(f"tab in indentation: {line!r}")
    return len(line) - len(line.lstrip(" "))


def _parse(lines: list[tuple[int, int, str]], start: int, indent: int) -> tuple[Node, int]:
    """Parse the block at ``indent`` starting at ``lines[start]``. Returns (node, next)."""
    if start >= len(lines):
        return None, start

    _, first_indent, first_text = lines[start]
    if first_indent < indent:
        return None, start

    if first_text.startswith("- "):
        return _parse_sequence(lines, start, first_indent)
    return _parse_mapping(lines, start, first_indent)


def _parse_sequence(
    lines: list[tuple[int, int, str]], start: int, indent: int
) -> tuple[list, int]:
    items: list[Node] = []
    index = start
    while index < len(lines):
        _, line_indent, text = lines[index]
        if line_indent < indent:
            break
        if line_indent > indent:
            raise ComposeParseError(f"unexpected indentation at line {lines[index][0]}")
        if not text.startswith("- "):
            break
        remainder = text[2:].strip()
        index += 1
        if not remainder:
            child, index = _parse(lines, index, indent + 1)
            items.append(child)
            continue
        if ":" in remainder and not remainder.split(":", 1)[0].strip().startswith(("'", '"')):
            key, _, value = remainder.partition(":")
            inline = {key.strip(): _scalar(value)}
            # A sequence item that opens a mapping: its remaining keys are indented past
            # the "- ".
            child_indent = indent + 2
            while index < len(lines) and lines[index][1] >= child_indent:
                more, index = _parse_mapping(lines, index, lines[index][1])
                if isinstance(more, dict):
                    inline.update(more)
                else:  # pragma: no cover - defensive
                    raise ComposeParseError("expected a mapping inside a sequence item")
            if inline.get(key.strip()) is None and len(inline) == 1:
                # `- key:` with the value on following lines
                pass
            items.append(inline)
            continue
        items.append(_scalar(remainder))
    return items, index


def _parse_mapping(
    lines: list[tuple[int, int, str]], start: int, indent: int
) -> tuple[dict, int]:
    mapping: dict[str, Node] = {}
    index = start
    while index < len(lines):
        line_number, line_indent, text = lines[index]
        if line_indent < indent:
            break
        if line_indent > indent:
            raise ComposeParseError(
                f"unexpected indentation at line {line_number}: {text!r}"
            )
        if text.startswith("- "):
            break
        if ":" not in text:
            raise ComposeParseError(
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
            # An anchor declaration. The anchor NAME is not the value; the block that
            # follows is. Recorded unresolved: this reader never expands an alias, so a
            # posture that could only be seen after expansion would read as absent, which
            # is why every posture field in deploy/compose.yaml is written literally.
            value = ""
        if value:
            if value.startswith("*"):
                mapping[key] = value  # an alias, recorded unresolved
            else:
                mapping[key] = _scalar(value)
            continue
        child, index = _parse(lines, index, indent + 1)
        mapping[key] = child
    return mapping, index


_BLOCK_SCALAR_INDICATORS = ("|", ">", "|-", ">-", "|+", ">+")


def _fold_block_scalars(raw_lines: list[str]) -> list[tuple[int, str]]:
    """Collapse ``key: >`` / ``key: |`` blocks into one quoted logical line.

    Done on the RAW lines, before comments are stripped, because a ``#`` inside a folded
    description is content and not a comment. The folded text is not used for any
    posture decision — every field this reader is used to check is a plain scalar or a
    list — but folding it wrongly would still be reading the file wrongly, and a reader
    that is right only about the parts somebody remembered is the defect this whole
    project is about.
    """
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
    """Parse the supported subset. Raises :exc:`ComposeParseError` on anything else."""
    lines: list[tuple[int, int, str]] = []
    for number, stripped in _fold_block_scalars(text.splitlines()):
        if stripped.lstrip().startswith("---"):
            continue
        lines.append((number, _indent_of(stripped), stripped.strip()))
    if not lines:
        raise ComposeParseError("empty document")
    node, consumed = _parse(lines, 0, lines[0][1])
    if consumed != len(lines):
        raise ComposeParseError(
            f"stopped at line {lines[consumed][0]}: {lines[consumed][2]!r}"
        )
    return node


def load_compose(path: pathlib.Path) -> dict:
    document = parse_block_yaml(pathlib.Path(path).read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ComposeParseError(f"{path} is not a mapping at the top level")
    return document
