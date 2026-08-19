"""The execution/brokerage vocabulary, declared once. STDLIB ONLY.

CD-AC-012 is the criterion this file serves: "no execution pathway exists ... advisory-only
is structural, not policy". Two register checks read it —
``check_no_execution_interface.py`` over the source and ``check_lockfile_denylist.py`` over
the dependency manifests — and they share it so the two cannot drift apart and leave a gap
between them.

WHY THIS IS A VOCABULARY AND NOT A LIST OF STRINGS TO GREP FOR. A guard that catches only
the exact planted instance and not its class is a defect Assurance is instructed to hunt
(CD-DISPATCH-WO2-ENGINEER, deliverables_block_B.B3). ``place_order`` is one spelling of a
class that also contains ``submitOrder``, ``route_trade``, ``OrderGateway``,
``close_position`` and ``ibkr.com``. So identifiers are TOKENISED — ``placeOrder``,
``place_order`` and ``PLACE_ORDER`` all reduce to ``{place, order}`` — and judged by
COMPOSITION: a verb of execution applied to an object of execution, an object of execution
wearing an interface suffix, or an object of execution carrying an order's data model.

Composition is what keeps the guard honest in both directions. A bare-token rule on
``order`` would condemn ``test_callbacks_run_in_registration_order`` and
``the_filename_pattern_orders_lexically``, both of which are English; a rule on the literal
string ``place_order`` would miss every other spelling. The composite rules fire on neither
piece of English above and on every spelling below.

The denylists are NOT claimed to be exhaustive, and no check here rests on their being so.
They are a floor, and the composite token rules are the part that generalises: a broker SDK
nobody has heard of still has to be imported under a name, and an order still has to be
placed by a function.
"""

from __future__ import annotations

__all__ = [
    "tokens",
    "token_list",
    "EXECUTION_VERBS",
    "EXECUTION_OBJECTS",
    "STRONG_NOUNS",
    "INTERFACE_SUFFIXES",
    "ORDER_DATA_MODEL",
    "BROKER_SDK_DISTRIBUTIONS",
    "BROKER_SDK_MODULES",
    "DEPENDENCY_NAME_TOKENS",
    "judge_identifier",
    "normalise_distribution",
    "judge_distribution",
    # --- shape and prose, added closing CD-PL-F32 ------------------------------------- #
    "ORDER_FIELDS",
    "STRONG_FIELDS",
    "TRANSMISSION_VERBS",
    "TRADEABLE_NOUNS",
    "DESTINATION_NOUNS",
    "classify_field",
    "field_categories",
    "judge_signature",
    "judge_prose",
]


def token_list(identifier: str) -> list:
    """``placeOrder`` / ``place_order`` / ``PLACE_ORDER`` -> ``['place', 'order']``, IN ORDER.

    Order is kept because the shape rules need the flattened form of a name
    (``limit_price`` -> ``limitprice``) to tell a price parameter from a row limit.
    """
    out: list = []
    current: list = []
    for char in identifier:
        if not char.isalnum():
            if current:
                out.append("".join(current))
                current = []
            continue
        if char.isupper() and current and not current[-1].isupper():
            out.append("".join(current))
            current = [char]
            continue
        current.append(char)
    if current:
        out.append("".join(current))
    return [token.lower() for token in out if token]


def tokens(identifier: str) -> set:
    """``placeOrder`` / ``place_order`` / ``PLACE_ORDER`` / ``place-order`` -> {place, order}."""
    return set(token_list(identifier))


#: Verbs that DO something to an order or a position. `execute` is here, and `run`,
#: `handle` and `process` deliberately are not: they are ordinary programming words and a
#: rule containing them would fire on half the codebase and teach a reader to ignore it.
EXECUTION_VERBS = frozenset(
    {
        "place", "submit", "send", "route", "execute", "cancel", "amend", "replace",
        "modify", "fill", "buy", "sell", "short", "cover", "liquidate", "square",
        "close", "open", "enter", "exit", "flatten", "hedge", "rebalance",
    }
)

#: The objects those verbs act on.
EXECUTION_OBJECTS = frozenset(
    {
        "order", "orders", "trade", "trades", "position", "positions",
        "execution", "executions", "ticket", "tickets", "fill", "fills",
    }
)

#: Words that name an execution facility on their own, with no partner needed. `execution`
#: and `trading` are NOT here — `execution` collides with `cursor.execute` and with the
#: perfectly ordinary "execution of a migration", and a guard that cries wolf is a guard
#: people learn to silence.
STRONG_NOUNS = frozenset(
    {
        "broker", "brokers", "brokerage", "brokerdealer", "brokerdealers",
        "oms", "ems", "orderrouter", "orderrouting", "orderentry",
        "tradingapi", "executionvenue", "fixsession", "fixgateway", "fixengine",
    }
)

#: Suffixes that turn an object of execution into an INTERFACE to one, which is the exact
#: noun CD-AC-012 uses: "the codebase contains no broker/order/execution interface".
INTERFACE_SUFFIXES = frozenset(
    {
        "api", "apis", "client", "clients", "gateway", "gateways", "adapter",
        "adapters", "interface", "interfaces", "connector", "connectors",
        "session", "sessions", "endpoint", "endpoints", "sdk", "rest", "socket",
        "websocket", "ws", "stub", "proxy", "broker", "router", "routers",
    }
)

#: The data model an order has. An `order_id` is an order pathway even with no verb in
#: sight, because something must have created the order that the id identifies.
ORDER_DATA_MODEL = frozenset(
    {
        "id", "ids", "ref", "refs", "side", "qty", "quantity", "price", "limit",
        "stop", "status", "book", "request", "response", "payload", "leg", "legs",
        "venue", "tif", "timeinforce", "notional", "lot", "lots",
    }
)

#: Objects that combine with INTERFACE_SUFFIXES and ORDER_DATA_MODEL.
INTERFACE_OBJECTS = frozenset(EXECUTION_OBJECTS | {"trading", "broker", "brokerage"})

# =================================================================================== #
# SHAPE AND PROSE — added closing CD-PL-F32 (BL-20260819T061400Z-0009).
#
# The escape that produced this section was `submit_instruction(symbol, qty, side)`,
# which passed the composite identifier rules above both WITH and WITHOUT the docstring
# "Route an order to the broker for execution". The instance is not the finding. The
# finding is that the rules above ask only ONE question — "is this NAME an execution
# word?" — and an order-entry path is not primarily a name. It is a SHAPE:
#
#   * a signature that carries an instrument together with a quantity and a side,
#     a price or order type, or a destination that is a venue, broker or exchange;
#   * a verb of transmission applied to a noun that names a tradeable instruction;
#   * a piece of PROSE that says, in plain English, that the thing routes orders.
#
# Any one of those alone is weak. The rules below therefore require COMBINATIONS, and
# each of the three layers is independently sufficient — the escape above is now caught
# by shape with the docstring deleted and by prose with every identifier renamed to `f`.
# =================================================================================== #

#: Nouns naming a tradeable instruction — the thing a transmission verb transmits.
#: A superset of EXECUTION_OBJECTS. `transaction` is DELIBERATELY ABSENT: a database
#: transaction is the commonest word in this codebase's storage layer, and a rule that
#: fired on it would be silenced within a week.
TRADEABLE_NOUNS = frozenset(
    EXECUTION_OBJECTS
    | {
        "instruction", "instructions", "deal", "deals", "bargain", "bargains",
        "basket", "baskets", "rfq", "rfqs", "allocation", "allocations",
        "buyorder", "sellorder", "childorder", "parentorder",
    }
)

#: Verbs of TRANSMISSION — moving an instruction somewhere that acts on it. Wider than
#: EXECUTION_VERBS because the question here is "does this send a tradeable noun
#: somewhere", not "does this name an execution word".
TRANSMISSION_VERBS = frozenset(
    EXECUTION_VERBS
    | {
        "transmit", "dispatch", "forward", "issue", "relay", "lodge", "book",
        "work", "stage", "release", "push", "emit", "raise", "instruct",
    }
)

#: Where an instruction goes. Any of these as a DESTINATION is a strong signal, because
#: this product has no reason to name a counterparty at all.
DESTINATION_NOUNS = frozenset(
    {
        "broker", "brokers", "brokerage", "dealer", "dealers", "exchange", "exchanges",
        "venue", "venues", "counterparty", "counterparties", "desk", "desks",
        "ecn", "ecns", "darkpool", "mic", "oms", "ems", "clearer", "custodian",
    }
)

#: THE ORDER-ENTRY FIELD SET, by CATEGORY rather than by word. This is the heart of the
#: shape rule: an order-entry signature is recognisable from its FIELDS even when every
#: one of its names has been chosen to avoid a vocabulary.
#:
#: Each entry maps a category to (single tokens, whole flattened names). A parameter is
#: classified if any of its tokens is in the token set, or its flattened form
#: (`limit_price` -> `limitprice`) is in the name set.
ORDER_FIELDS = {
    "instrument": (
        frozenset({
            "symbol", "symbols", "ticker", "tickers", "instrument", "instruments",
            "isin", "cusip", "sedol", "ric", "figi", "conid", "secid",
            "underlying", "underlyings", "epic",
        }),
        frozenset({"security", "securities", "assetid", "contractid", "tradingpair"}),
    ),
    "quantity": (
        frozenset({
            "qty", "quantity", "quantities", "shares", "lots", "notional",
            "nominal", "contracts",
        }),
        frozenset({"size", "ordersize", "tradesize", "amount", "units", "volume", "clipsize"}),
    ),
    # STRONG. A side is buy-or-sell. Nothing in an advisory read-only product needs one.
    "side": (
        frozenset({"side", "sides"}),
        frozenset({
            "direction", "buysell", "sellbuy", "isbuy", "issell", "longshort",
            "bs", "buyorsell", "orderdirection", "tradedirection",
        }),
    ),
    "price": (
        frozenset({"px", "strike"}),
        frozenset({
            "price", "prices", "limitprice", "stopprice", "avgprice", "avergageprice",
            "pegprice", "triggerprice", "fillprice",
        }),
    ),
    # STRONG. An order type or time-in-force exists only to qualify an order.
    "order_type": (
        frozenset({"tif", "timeinforce", "gtc", "ioc", "fok"}),
        frozenset({
            "ordertype", "ordtype", "exectype", "executiontype", "tradetype",
            "goodtillcancelled", "goodtilcancel",
        }),
    ),
    # STRONG. A destination that acts on instructions.
    "destination": (
        DESTINATION_NOUNS,
        frozenset({"destination", "routeto", "executionvenue", "tradingvenue"}),
    ),
    "account": (
        frozenset({"subaccount"}),
        frozenset({"account", "accountid", "portfolio", "portfolioid", "tradingaccount"}),
    ),
}

#: Categories that carry the signal on their own. A quantity beside an instrument is a
#: position report; a SIDE, an ORDER TYPE or a DESTINATION beside them is an order.
#: This split is what keeps `(symbol, quantity, price)` — an ordinary valuation
#: signature — from firing, while `(symbol, qty, side)` fires.
STRONG_FIELDS = frozenset({"side", "order_type", "destination"})


def classify_field(name: str) -> "str | None":
    """Which order-entry field category this parameter/attribute name belongs to, or None."""
    parts = token_list(name)
    if not parts:
        return None
    marks = set(parts)
    flat = "".join(parts)
    for category, (single, whole) in ORDER_FIELDS.items():
        if marks & single or flat in whole:
            return category
    return None


def field_categories(names) -> dict:
    """``{category: [the names that put it there]}`` for a parameter or attribute list."""
    found: dict = {}
    for name in names:
        category = classify_field(name)
        if category is not None:
            found.setdefault(category, []).append(name)
    return found


def judge_signature(name: str, parameters, what: str = "function") -> "str | None":
    """Why this SIGNATURE is an order-entry path, or None — reading fields, not names.

    Three rules, each requiring a combination:

    * **S1** an instrument AND a quantity AND at least one strong field. This is the
      classic order ticket: what, how much, which way.
    * **S2** two or more strong fields plus anything else — ``(instrument, venue, tif)``
      has no quantity and is still an order entry point.
    * **S3** a verb of transmission in the NAME plus two or more order fields. The bar
      is lower because the name has already said the thing is sent somewhere.

    The function's own name is NOT required by S1 or S2. That is the point: a callable
    taking an instrument, a quantity and a side is an order-entry path whether it is
    called ``place_order``, ``submit_instruction`` or ``f``.
    """
    parameters = [
        parameter for parameter in parameters if parameter not in ("self", "cls")
    ]
    found = field_categories(parameters)
    categories = set(found)
    strong = categories & STRONG_FIELDS

    def shown() -> str:
        return ", ".join(
            f"{category}=`{'`, `'.join(found[category])}`" for category in sorted(found)
        )

    if {"instrument", "quantity"} <= categories and strong:
        return (
            f"the {what} `{name}` takes an ORDER TICKET: {shown()}. An instrument, a "
            f"quantity and {sorted(strong)[0]} together are an order-entry signature "
            "whatever the callable is named — this rule reads the FIELDS, not the name, "
            "which is why renaming the function does not evade it."
        )

    if len(strong) >= 2 and len(categories) >= 3:
        return (
            f"the {what} `{name}` carries {len(strong)} independent order-only fields "
            f"({', '.join(sorted(strong))}) among {shown()}. Nothing an advisory "
            "read-only product does needs a side, an order type and a venue together."
        )

    verbs = sorted(tokens(name) & TRANSMISSION_VERBS)
    if verbs and len(categories) >= 2:
        return (
            f"the {what} `{name}` applies the transmission verb `{verbs[0]}` to a "
            f"parameter set that is an order's field set ({shown()})."
        )

    return None


# --- PROSE ----------------------------------------------------------------------------- #
#
# A function whose name is neutral but whose own docstring says in plain English that it
# routes orders to a broker is an execution interface by the product's definition, and
# until CD-PL-F32 this check could not see it. It reads prose now.
#
# The old header said prose was deliberately not matched, and the REASON given was sound:
# "a docstring saying `this system places no orders` is not an order interface", and a
# check whose findings are mostly the project's own descriptions of what it refuses to do
# is a check nobody reads. That reason is preserved rather than discarded — it is why the
# prose rule is a tight DIRECT-OBJECT pattern with negation and hypothetical suppression,
# not a keyword scan.

#: Words that may sit between a transmission verb and its object without breaking the
#: direct-object reading. Anything else does: "sends messages in order" is not "sends an
#: order", and the difference is entirely in what sits in the gap.
PROSE_FILLERS = frozenset(
    {
        "a", "an", "the", "this", "that", "these", "those", "its", "his", "her",
        "our", "their", "your", "my", "one", "two", "each", "every", "any", "some",
        "new", "live", "real", "single", "child", "parent", "market", "limit",
        "stop", "buy", "sell", "further", "another", "first", "next", "final",
        "actual", "outgoing", "resting", "working", "pending",
    }
)

#: Negation and refusal. This project's prose is FULL of sentences about what it will not
#: do — the PID's own words are quoted in half the modules — and every one of them must
#: read as clean. A sentence carrying any of these is noted, never failed.
PROSE_NEGATIONS = frozenset(
    {
        "no", "not", "never", "none", "nothing", "nor", "neither", "without",
        "cannot", "cant", "wont", "dont", "doesnt", "didnt", "isnt", "arent",
        "refuse", "refuses", "refused", "refusal", "refusing",
        "forbid", "forbids", "forbidden", "forbidding",
        "prohibit", "prohibits", "prohibited", "prohibition",
        "ban", "bans", "banned", "denylist", "deny", "denies", "denied",
        "absent", "absence", "zero", "free", "nowhere", "reject", "rejects",
        "rejected", "refuses", "must", "advisory",
    }
)

#: Hypothetical and illustrative framing. A guard, a test and a planted violation all
#: have to DESCRIBE the thing they defend against in order to defend against it.
PROSE_HYPOTHETICALS = frozenset(
    {
        "if", "would", "were", "suppose", "hypothetical", "hypothetically",
        "example", "eg", "ie", "planted", "plant", "plants", "variant", "variants",
        "violation", "violations", "guard", "guards", "check", "checks", "checker",
        "criterion", "pretend", "imagine", "say",
    }
)

#: `order` HAS TWO SENSES IN ENGLISH — an instruction, and a sequence — and the modifier
#: in front of it is what tells them apart. Every word here makes the SEQUENCE sense, and
#: none of them is a trading phrase.
#:
#: TUNED, AND WHY. The first run of the prose rule against the delivered tree produced two
#: findings, both of them "work order": src/crash_detector/__init__.py:1 ("which work order
#: each part is owed to") and db/migrations/0007_grant_matrix.sql:232 ("a later work order
#: adds"). `work` is a genuine transmission verb — a trader works an order into the market
#: — but this project has sixteen work orders and names them constantly, so the collision
#: is certain and the check would have been ignored inside a week. A check that fails on
#: innocent code is as useless as one that passes guilty code.
#:
#: THE TUNING DOES NOT REOPEN THE CLASS. It suppresses ONE BIGRAM in ONE layer: `work
#: order` in L3 prose. `work_order` as an identifier still fails L1; a callable taking an
#: order's field set still fails L2 whatever its comments say; and "works the order",
#: "works an order" and "working the order" all still fail L3, because the modifier rule
#: reads the word IMMEDIATELY before the noun and `the`/`an` are not in this set. What has
#: been given up is the ability to detect an execution pathway announced only in a comment
#: that begins with one of these modifiers — a false negative in the third of three nets.
ORDER_SEQUENCE_MODIFIERS = frozenset(
    {
        "in", "work", "sort", "sorted", "byte", "reverse", "reversed", "descending",
        "ascending", "alphabetical", "lexical", "lexicographic", "chronological",
        "declaration", "registration", "insertion", "evaluation", "dependency",
        "topological", "delivery", "boot", "load", "import", "random", "stable",
        "natural", "canonical", "arbitrary", "priority", "column", "argument",
    }
)

#: What must NOT follow `order` for it to be an instruction: "in order to", "order of
#: magnitude".
ORDER_SEQUENCE_FOLLOWERS = frozenset({"to", "of"})

_PROSE_SPLIT = ".;!?\n\r"


def _prose_words(sentence: str) -> list:
    out: list = []
    current: list = []
    for char in sentence:
        if char.isalnum():
            current.append(char.lower())
            continue
        if current:
            out.append("".join(current))
            current = []
    if current:
        out.append("".join(current))
    return out


def judge_prose(text: str) -> "tuple[str, str] | None":
    """Why this prose states an execution pathway, or None. Returns (reason, sentence).

    Fires on a DIRECT-OBJECT construction only: a transmission verb, then at most three
    words of ordinary determiner/adjective filler, then a noun naming a tradeable
    instruction. "Route an order to the broker for execution" matches; "the order in
    which callbacks run", "sends messages in order" and "in order to" do not, because
    the words in the gap are not filler and `order` followed by `to`/`of` or preceded by
    `in` is excluded outright.

    Suppressed, with the suppression visible to the caller as a note rather than silent:
    any sentence carrying a negation or a hypothetical framing. This project's own
    documentation says repeatedly that it places no orders, and a guard that failed on
    its own charter would be turned off by the second week.
    """
    buffer: list = []
    for char in text:
        if char in _PROSE_SPLIT:
            verdict = _judge_sentence("".join(buffer))
            if verdict:
                return verdict
            buffer = []
            continue
        buffer.append(char)
    return _judge_sentence("".join(buffer))


#: Irregular forms worth having. Prose inflects; a vocabulary that only knows the
#: infinitive reads "sent the order to the broker" as clean.
_IRREGULAR_VERBS = {"sent": "send", "sends": "send", "sending": "send"}


def _is_transmission_verb(word: str) -> bool:
    """``route``/``routes``/``routed``/``routing``/``sent`` all reach ``route``/``send``."""
    if word in TRANSMISSION_VERBS:
        return True
    if _IRREGULAR_VERBS.get(word, "") in TRANSMISSION_VERBS:
        return True
    for suffix, replacements in (
        ("ing", ("", "e")),
        ("ed", ("", "e")),
        ("en", ("", "e")),
        ("es", ("", "e")),
        ("s", ("",)),
    ):
        if not word.endswith(suffix) or len(word) <= len(suffix) + 1:
            continue
        stem = word[: -len(suffix)]
        for tail in replacements:
            if stem + tail in TRANSMISSION_VERBS:
                return True
        if suffix in ("ing", "ed") and len(stem) > 2 and stem[-1] == stem[-2]:
            if stem[:-1] in TRANSMISSION_VERBS:
                return True
    return False


#: Forms of `be` and `get`, for the passive-voice pattern.
BE_FORMS = frozenset(
    {"is", "are", "was", "were", "be", "been", "being", "get", "gets", "got", "becomes"}
)


def _is_adverbial(word: str) -> bool:
    """`successfully`, `immediately` — an adverb between a noun and its verb."""
    return word.endswith("ly") and len(word) > 4


def _is_past_participle(word: str) -> bool:
    """A past participle of a transmission verb: `routed`, `submitted`, `sent`, `driven`.

    The participle FORM is required. Without it "the position was open" — where `open` is
    a transmission verb in its bare form — would read as an execution statement, and it is
    an ordinary adjective.
    """
    if word == "sent":
        return True
    if word in TRANSMISSION_VERBS:
        # A BARE FORM IS NOT A PARTICIPLE. `open` ends in `en` and is a transmission
        # verb; "the position was open" is an adjective and must stay clean.
        return False
    if not (word.endswith("ed") or word.endswith("en")):
        return False
    return _is_transmission_verb(word)


def _tradeable_at(words: list, position: int) -> bool:
    """Is the word at ``position`` a tradeable noun in its INSTRUCTION sense?"""
    word = words[position]
    if word not in TRADEABLE_NOUNS:
        return False
    if word.startswith("order"):
        previous = words[position - 1] if position else ""
        following = words[position + 1] if position + 1 < len(words) else ""
        if previous in ORDER_SEQUENCE_MODIFIERS or following in ORDER_SEQUENCE_FOLLOWERS:
            return False
    return True


def _judge_sentence(sentence: str) -> "tuple[str, str] | None":
    words = _prose_words(sentence)
    if len(words) < 2:
        return None
    marks = set(words)
    if marks & PROSE_NEGATIONS or marks & PROSE_HYPOTHETICALS:
        return None

    destination = sorted(marks & DESTINATION_NOUNS)
    where = f" and names the destination `{destination[0]}`" if destination else ""

    def hit(phrase: str, voice: str) -> tuple:
        return (
            f"this prose says, {voice}, that the code `{phrase}`{where}. A thing that "
            "describes itself as routing orders is an execution interface by "
            "CD-AC-012's definition regardless of what it is called — the identifiers "
            "are not the only place an interface declares itself.",
            sentence.strip()[:200],
        )

    # A — ACTIVE VOICE: verb, at most three words of filler, tradeable noun.
    for index, word in enumerate(words):
        if not _is_transmission_verb(word):
            continue
        for offset in range(1, 4):
            position = index + offset
            if position >= len(words):
                break
            candidate = words[position]
            if not _tradeable_at(words, position):
                if candidate not in PROSE_FILLERS:
                    break
                continue
            return hit(f"{word} {candidate}", "in the active voice")
        # a verb with no tradeable object is ordinary English; keep looking.

    # B — PASSIVE VOICE: tradeable noun, a form of `be`, a past participle of a
    # transmission verb. ADDED AFTER FRESH VARIANT FV-14 ESCAPED PATTERN A: "Each bargain
    # was routed to the desk" puts the object BEFORE the verb, and a direct-object rule
    # cannot see it. The escape was a real gap in the class, not a wording accident, and
    # this is the fix for the class rather than for the sentence.
    for index, word in enumerate(words):
        if word not in BE_FORMS:
            continue
        noun = None
        for back in range(1, 4):
            position = index - back
            if position < 0:
                break
            if _tradeable_at(words, position):
                noun = words[position]
                break
            if words[position] not in PROSE_FILLERS and not _is_adverbial(words[position]):
                break
        if noun is None:
            continue
        for forward in range(1, 4):
            position = index + forward
            if position >= len(words):
                break
            candidate = words[position]
            if _is_past_participle(candidate):
                return hit(f"{noun} {word} {candidate}", "in the passive voice")
            if candidate not in PROSE_FILLERS and not _is_adverbial(candidate):
                break

    # C — NOMINALISED: a tradeable noun immediately followed by a transmission verb in
    # its -ing form. "order routing", "position closing", "ticket forwarding" — no finite
    # verb anywhere, so neither A nor B sees them.
    for index in range(len(words) - 1):
        if not _tradeable_at(words, index):
            continue
        following = words[index + 1]
        if following.endswith("ing") and _is_transmission_verb(following):
            return hit(f"{words[index]} {following}", "as a noun phrase")

    return None

#: Broker, exchange and order-routing SDKs as they are named on PyPI. Normalised per PEP
#: 503 before comparison, so `alpaca_trade_api` and `Alpaca-Trade-API` match alike.
BROKER_SDK_DISTRIBUTIONS = frozenset(
    {
        "ib-insync", "ibapi", "ibpy2", "ib-async", "ibridgepy", "tws-api",
        "alpaca-trade-api", "alpaca-py", "alpacahq",
        "ccxt", "ccxtpro", "cryptofeed",
        "oandapyv20", "oanda-api-v20", "v20", "tpqoa",
        "tda-api", "schwab-py", "schwabdev",
        "robin-stocks", "pyrh", "webull", "tastytrade", "tastyworks",
        "python-binance", "binance-connector", "binance-futures-connector",
        "krakenex", "pykrakenapi", "coinbase", "coinbase-advanced-py", "cbpro",
        "pybit", "bybit-api", "okx", "python-okx", "kucoin-python", "gate-api",
        "bitmex", "deribit-api", "bitstamp-python-client",
        "kiteconnect", "upstox-python-sdk", "smartapi-python", "fyers-apiv2",
        "questrade-api", "degiro-connector", "saxo-openapi", "tradier",
        "quickfix", "simplefix", "quickfix-py", "pyfixmsg",
        "backtrader-ib", "nautilus-trader", "lean", "quantconnect-stubs",
        "metatrader5", "mt5linux", "xtb-api", "iqoptionapi",
    }
)

#: The same SDKs as they are named at the IMPORT site, which is often not the distribution
#: name. `pip install ib_insync` gives `import ib_insync`; `pip install python-binance`
#: gives `import binance`.
BROKER_SDK_MODULES = frozenset(
    {
        "ib_insync", "ib_async", "ibapi", "ibpy", "ibridgepy",
        "alpaca_trade_api", "alpaca",
        "ccxt", "cryptofeed",
        "oandapyV20", "oandapyv20", "v20", "tpqoa",
        "tda", "schwab", "schwabdev",
        "robin_stocks", "pyrh", "webull", "tastytrade",
        "binance", "krakenex", "coinbase", "cbpro", "pybit", "okx", "kucoin",
        "bitmex", "deribit_api", "bitstamp",
        "kiteconnect", "upstox_client", "SmartApi", "fyers_apiv2",
        "questrade", "degiro_connector", "saxo_openapi", "tradier",
        "quickfix", "simplefix", "pyfixmsg",
        "nautilus_trader", "MetaTrader5", "mt5linux",
    }
)

#: Tokens that condemn a DISTRIBUTION name even when the distribution is unknown. A
#: dependency is a much smaller, much more deliberate surface than source code, so this can
#: be blunter than the source rules without crying wolf: nobody adds `trade-api` to a
#: lockfile by accident.
DEPENDENCY_NAME_TOKENS = frozenset(
    {
        "broker", "brokerage", "brokers",
        "order", "orders", "orderrouting",
        "trade", "trades", "trading", "trader",
        "execution", "exec", "oms", "ems", "fix",
        "exchange", "brokerapi", "tradeapi", "quantconnect",
    }
)


def judge_identifier(identifier: str) -> "str | None":
    """Why this identifier names an execution interface, or None.

    Four composite rules. None of them fires on a single ordinary token, which is what
    lets the check be run over the whole tree without being ignored.
    """
    marks = tokens(identifier)
    if not marks:
        return None

    standalone = sorted(marks & STRONG_NOUNS)
    if standalone:
        return (
            f"`{identifier}` names {', '.join(standalone)} — a brokerage or order-routing "
            "facility, which needs no verb to be one."
        )

    # A VERB OF TRANSMISSION APPLIED TO A TRADEABLE NOUN. Both sides were widened
    # closing CD-PL-F32 — TRANSMISSION_VERBS and TRADEABLE_NOUNS rather than
    # EXECUTION_VERBS and EXECUTION_OBJECTS — but WIDENING THE LISTS IS NOT THE FIX and
    # is not relied on: `submit_instruction(symbol, qty, side)` is caught by
    # judge_signature with every one of these words removed, and by judge_prose with
    # every identifier renamed to `f`. The lists close the narrow case of a transmission
    # verb applied to a tradeable noun in a callable that takes NO arguments at all,
    # where there is no signature to read.
    verbs = sorted(marks & TRANSMISSION_VERBS)
    objects = sorted(marks & TRADEABLE_NOUNS)
    if verbs and objects:
        return (
            f"`{identifier}` applies the transmission verb `{verbs[0]}` to the tradeable "
            f"noun `{objects[0]}`. That is an order pathway however it is spelled."
        )

    interface_objects = sorted(marks & INTERFACE_OBJECTS)
    suffixes = sorted(marks & INTERFACE_SUFFIXES)
    if interface_objects and suffixes:
        return (
            f"`{identifier}` is an INTERFACE (`{suffixes[0]}`) to `{interface_objects[0]}`. "
            "CD-AC-012's words are 'no broker/order/execution interface' and this is one."
        )

    model = sorted(marks & ORDER_DATA_MODEL)
    if objects and model:
        return (
            f"`{identifier}` carries an order's data model (`{objects[0]}` + "
            f"`{model[0]}`). Something must have created the order this describes."
        )

    return None


def normalise_distribution(name: str) -> str:
    """PEP 503 normalisation: lowercase, runs of ``-_.`` collapsed to a single ``-``."""
    out: list = []
    previous_separator = False
    for char in name.strip().lower():
        if char in "-_.":
            if not previous_separator:
                out.append("-")
            previous_separator = True
            continue
        previous_separator = False
        out.append(char)
    return "".join(out).strip("-")


def judge_distribution(name: str) -> "str | None":
    """Why this distribution is a broker SDK, or None."""
    normalised = normalise_distribution(name)
    if not normalised:
        return None
    if normalised in BROKER_SDK_DISTRIBUTIONS:
        return (
            f"`{name}` is a known broker, exchange or order-routing SDK. Its presence in "
            "a dependency manifest is an execution pathway one import away."
        )
    hits = sorted(tokens(normalised) & DEPENDENCY_NAME_TOKENS)
    if hits:
        return (
            f"`{name}` carries the execution token(s) {', '.join(hits)} in its "
            "distribution name. The denylist is a floor, not an oracle: a broker SDK "
            "nobody has heard of is still named after what it does."
        )
    return None
