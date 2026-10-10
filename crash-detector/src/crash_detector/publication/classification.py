"""Key classification — what may never appear on the public surface (BLUEPRINT §3).

PID doctrine §3.5 is Constitutional: "Hard public/private split. Market read outward;
anything touching the book stays private." This module holds the register of key
vocabulary that identifies a key as book-adjacent or secret-bearing, and the recursive
scan that finds one anywhere in a candidate envelope.

----

WHERE THIS SITS AMONG THE FIVE SEPARATIONS, AND WHY IT IS NOT THE MAIN ONE.

BLUEPRINT §3 lists five independent separations. The fourth — the closed envelope schema
whose ``properties`` are an allowlist — is TOTAL: it refuses every key nobody declared,
book-adjacent or not, without needing to recognise it. That is the primary instrument and
it needs no vocabulary to work.

This register is a second, independent line, and it earns its place three ways:

* it names the REASON. "``portfolio_value`` is a private-classified key" is an
  actionable refusal; "``portfolio_value`` is not in the allowlist" sends an engineer to
  add it to the allowlist, which is the wrong repair;
* it fires on the day a free-form object is legitimately added to a schema, where the
  allowlist stops being total; and
* it applies to the PRIVATE envelope too for the secret-bearing half. Book data belongs
  in the private envelope; a credential belongs in neither, ever (``PBG-SEC-002``,
  non-waivable).

It is deliberately NOT the thing the closure test relies on. A register of forbidden words
guards the instances someone thought of; the allowlist guards the class. Both, and in that
order of trust.

----

MATCHING, AND ITS LIMITS, STATED.

A key is tokenised — snake_case, camelCase, kebab-case and digit boundaries all split —
and each token is matched against the register. ``portfolioValue``, ``portfolio_value``,
``PORTFOLIO-VALUE`` and ``portfolio``, all match; the concatenation of tokens is checked
too, so ``p_n_l`` reaches ``pnl``.

It will not catch a deliberately obfuscated key, and it is not built to: an adversary
inside the build who wants to exfiltrate the book will not name the field ``holdings``.
The instrument against that adversary is the allowlist, which refuses the obfuscated key
just as flatly for not being on it.
"""

from __future__ import annotations

import re
from collections.abc import Mapping as AbcMapping
from typing import Iterator, Tuple, Union

__all__ = [
    "BOOK_ADJACENT_TOKENS",
    "SECRET_BEARING_TOKENS",
    "CLASSIFICATION_BOOK_ADJACENT",
    "CLASSIFICATION_SECRET_BEARING",
    "key_tokens",
    "classify_key",
    "iter_keys",
]

CLASSIFICATION_BOOK_ADJACENT = "BOOK_ADJACENT"
CLASSIFICATION_SECRET_BEARING = "SECRET_BEARING"

#: Vocabulary that makes a key book-adjacent — "anything touching the book" (PID §3.5).
#: Forbidden on the PUBLIC surface. Legitimate inside the private envelope, which is what
#: the private envelope is for.
#:
#: Chosen to be specific rather than sweeping. ``weight`` is deliberately ABSENT: a
#: contribution weight is a model coefficient and is declared in the public allowlist, and
#: a register that refused it would refuse a legitimate published field — a false positive
#: in a fail-closed check is an outage, and the first response to an outage is to weaken
#: the check.
BOOK_ADJACENT_TOKENS: frozenset[str] = frozenset(
    {
        "account",
        "allocation",
        "book",
        "broker",
        "cost",
        "custodian",
        "drawdown",
        "execution",
        "exposure",
        "fill",
        "holding",
        "holdings",
        "iban",
        "isin",
        "ledger",
        "margin",
        "nav",
        "order",
        "pandl",
        "pnl",
        "portfolio",
        "position",
        "positions",
        "purchase",
        "realised",
        "realized",
        "sedol",
        "sizing",
        "stake",
        "tradeid",
        "trade",
        "trades",
        "unrealised",
        "unrealized",
        "valuation",
        "wallet",
    }
)

#: Vocabulary that makes a key secret-bearing. Forbidden on BOTH surfaces, without
#: exception and with no private side it could legitimately be on: a secret is referenced
#: by environment-variable NAME at the point of use and is never carried in a record
#: (``PBG-SEC-002``, ``PBG-EVID-003``, Standards Baseline §5).
SECRET_BEARING_TOKENS: frozenset[str] = frozenset(
    {
        "apikey",
        "auth",
        "bearer",
        "credential",
        "credentials",
        "passphrase",
        "password",
        "privatekey",
        "pwd",
        "secret",
        "seed",
        "session",
        "signature",
        "token",
    }
)

_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_SEPARATORS = re.compile(r"[^A-Za-z0-9]+")
_DIGIT_BOUNDARY = re.compile(r"(?<=[A-Za-z])(?=[0-9])|(?<=[0-9])(?=[A-Za-z])")


def key_tokens(key: str) -> Tuple[str, ...]:
    """Lowercased tokens of ``key``, split on case, separator and digit boundaries."""
    if not isinstance(key, str):
        raise TypeError(f"a JSON object key must be a str, got {type(key).__name__}")
    spaced = _CAMEL_BOUNDARY.sub("_", key)
    spaced = _DIGIT_BOUNDARY.sub("_", spaced)
    return tuple(part.lower() for part in _SEPARATORS.split(spaced) if part)


def classify_key(key: str) -> Union[Tuple[str, str], None]:
    """``(classification, matched_token)`` if ``key`` is classified, else ``None``.

    Secret-bearing is reported ahead of book-adjacent where a key is both, because it is
    the stricter refusal: a book-adjacent key has a surface it may legitimately appear on
    and a secret-bearing key has none.
    """
    tokens = key_tokens(key)
    # Single tokens, adjacent PAIRS, and the whole key joined. The pairs matter: a
    # register entry like `apikey` is reached from `api_key` by the full join, but
    # `broker_api_key` joins to `brokerapikey` and would slip past a check that only
    # looked at the ends. Matching every adjacent pair catches the compound wherever the
    # register's word sits inside it.
    bigrams = tuple(
        tokens[index] + tokens[index + 1] for index in range(len(tokens) - 1)
    )
    joined = "".join(tokens)
    candidates = tokens + bigrams + ((joined,) if joined else ())

    for token in candidates:
        if token in SECRET_BEARING_TOKENS:
            return (CLASSIFICATION_SECRET_BEARING, token)
    for token in candidates:
        if token in BOOK_ADJACENT_TOKENS:
            return (CLASSIFICATION_BOOK_ADJACENT, token)
    return None


def iter_keys(node: object, pointer: str = "") -> Iterator[Tuple[str, str]]:
    """Every ``(key, json_pointer)`` inside ``node``, at every depth.

    Descends into mappings AND into list elements, because a key nested inside an array
    of objects is exactly as published as one at the root, and a scan that stops at the
    first array is a scan an author can step around by wrapping their field in a list.
    """
    if isinstance(node, AbcMapping):
        for key, value in node.items():
            token = str(key).replace("~", "~0").replace("/", "~1")
            child = f"{pointer}/{token}"
            yield (str(key), child)
            yield from iter_keys(value, child)
    elif isinstance(node, (list, tuple)):
        for index, value in enumerate(node):
            yield from iter_keys(value, f"{pointer}/{index}")
