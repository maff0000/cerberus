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
]


def tokens(identifier: str) -> set:
    """``placeOrder`` / ``place_order`` / ``PLACE_ORDER`` / ``place-order`` -> {place, order}."""
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
    return {token.lower() for token in out if token}


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

    verbs = sorted(marks & EXECUTION_VERBS)
    objects = sorted(marks & EXECUTION_OBJECTS)
    if verbs and objects:
        return (
            f"`{identifier}` applies the execution verb `{verbs[0]}` to `{objects[0]}`. "
            "That is an order pathway however it is spelled."
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
