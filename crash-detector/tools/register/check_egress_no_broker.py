#!/usr/bin/env python3
"""CD-RT-012-EGRESS-NO-BROKER — there is nowhere for an execution pathway to go.

    python3 tools/register/check_egress_no_broker.py --root <subject tree>

CRITERION: CD-AC-012, "no execution pathway exists" (PID §6). PID §2 is constitutional on
this: the detector is advisory-only, and advisory-only is STRUCTURAL, not policy. BLUEPRINT
§2 and §13: "no container's egress allowlist names a broker; engine and both surfaces have
no egress at all."

READS THE POSTURE AS DATA, NOT AS PROSE. ``deploy/compose.yaml`` declares an ``x-egress``
block on every service and declares the contract those blocks answer to in
``x-cd-egress-contract``, with three invariants. A comment is not a posture, because a
comment cannot be read by the thing that has to refuse. This check reads the file with a
stdlib-only YAML subset reader and asserts the three invariants against it.

WHAT IS ASSERTED
-----------------
 CD-EGRESS-003  EVERY service declares an ``x-egress`` block with a ``policy``, a ``hosts``
                list and an ``enforced_by``. A service with none is a VIOLATION and not a
                default — a check that skips a service it does not recognise is a check an
                author bypasses by adding a service. The policy must be NONE or ALLOWLIST;
                any other value is a violation, not an unknown to be tolerated.

 CD-EGRESS-001  cd-engine, cd-public, cd-private and cd-store declare ``policy: NONE`` with
                an EMPTY ``hosts`` list, and are attached only to networks declared
                ``internal: true``. The topology is what makes "no egress" structural: a
                container attached only to internal networks has no route off the host
                whatever code runs in it. A service in this set that gains a non-internal
                network has gained egress, whatever its policy says.

 CD-EGRESS-002  NO ``hosts`` entry, in any service, names a broker, an exchange, an
                order-routing endpoint or a trading API — and neither does any ``pending``
                entry, because a pending entry is a host somebody intends to add.

BUILT FOR THE CLASS, NOT THE INSTANCE. CD-EGRESS-002's own wording insists on it: "the
check that establishes this must judge the CLASS — the question is what kind of thing lives
there, not whether its name contains a string somebody thought of." So a host is judged
three ways, and any one of them condemns it:

  1  its DOMAIN LABELS are matched against a vocabulary of brokerage and market-execution
     concepts (broker, exchange, order, execution, trade/trading, venue, oms/ems, fix,
     clearing, settlement, margin, futures, options, derivatives, custody…), tokenised on
     ``.``, ``-`` and ``_`` so ``order-api.example.com`` and ``api.orders.example.com``
     hit alike;
  2  its registrable domain is matched against a denylist of KNOWN broker and exchange
     operators, because ``ibkr.com`` contains no concept word at all and is the single most
     likely real-world instance;
  3  the same vocabulary is applied to the URL PATH when a host is written as a URL, so
     ``api.example.com/v1/orders`` is caught even though its host is innocent.

WHAT THIS CHECK DOES NOT CLAIM. It reads a DECLARATION. BLUEPRINT §2 and the compose file
itself disclose that Docker Compose has no per-host egress primitive, so an ALLOWLIST is
enforced by a lane owed at WO-3 and, in WO-2, every network is ``internal: true`` and the
effective egress of every service is none. The check therefore verifies the two things that
ARE verifiable in WO-2 — the declared topology and the absence of any named broker — and
says so rather than implying it has watched a packet.

EXIT: 0 clean · 1 violation, with file and line · 2 usage · 3 precondition not met.
Never a skip, for any reason (PBG-CI-002).
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _support import Check, parse_root, resolve_root  # noqa: E402
from _yamlmin import (  # noqa: E402
    YamlSubsetError,
    line_of,
    load_yaml,
    unresolved_aliases,
)

CHECK_ID = "CD-RT-012-EGRESS-NO-BROKER"

COMPOSE = "deploy/compose.yaml"

#: The services BLUEPRINT §2 gives no egress at all. Named, so a rename is a visible edit.
NO_EGRESS_SERVICES = ("cd-engine", "cd-public", "cd-private", "cd-store")

VALID_POLICIES = ("NONE", "ALLOWLIST")

#: Concepts that make a host an execution venue rather than a data source. Matched against
#: tokenised domain labels and URL path segments, never as a substring — a substring rule
#: would condemn `reorder` and miss `order-api`.
BROKER_CONCEPT_TOKENS = frozenset(
    {
        "broker", "brokers", "brokerage", "brokerdealer",
        "order", "orders", "orderentry", "orderrouting", "routing",
        "execution", "executions", "execute", "exec",
        "trade", "trades", "trading", "trader",
        "exchange", "exchanges", "venue", "venues", "ecn", "darkpool",
        "oms", "ems", "fix", "fixapi", "fixgateway",
        "clearing", "clearinghouse", "settlement", "custody", "custodian",
        "margin", "leverage", "futures", "options", "derivatives", "swaps",
        "position", "positions", "portfolio", "account", "accounts",
        "buy", "sell", "bid", "ask", "fill", "fills",
    }
)

#: Registrable domains of known brokers, exchanges and order-routing operators. This exists
#: because concept matching alone would pass `ibkr.com` — the likeliest real instance —
#: which contains no concept word. Neither rule is sufficient; both are cheap.
BROKER_DOMAINS = frozenset(
    {
        "interactivebrokers.com", "interactivebrokers.co.uk", "ibkr.com", "ibkr.co.uk",
        "alpaca.markets", "tradier.com", "tdameritrade.com", "schwab.com",
        "schwabapi.com", "etrade.com", "fidelity.com", "robinhood.com",
        "webull.com", "tastytrade.com", "tastyworks.com", "lightspeed.com",
        "saxobank.com", "saxomarkets.com", "oanda.com", "forex.com", "ig.com",
        "cmcmarkets.com", "plus500.com", "etoro.com", "xtb.com", "pepperstone.com",
        "binance.com", "binance.us", "coinbase.com", "pro.coinbase.com", "kraken.com",
        "bitstamp.net", "bitfinex.com", "gemini.com", "okx.com", "bybit.com",
        "kucoin.com", "huobi.com", "gate.io", "deribit.com", "bitmex.com",
        "nyse.com", "nasdaq.com", "cmegroup.com", "cboe.com", "lseg.com",
        "eurex.com", "ice.com", "theice.com", "tradeweb.com", "marketaxess.com",
        "zerodha.com", "kite.zerodha.com", "upstox.com", "angelone.in", "fyers.in",
        "questrade.com", "wealthsimple.com", "degiro.com", "trading212.com",
    }
)


def _labels(value: str) -> set:
    """Domain labels and path segments, tokenised on ``.``, ``-``, ``_``, ``/``."""
    cleaned = value.strip().lower()
    for prefix in ("https://", "http://", "tcp://", "wss://", "ws://"):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix) :]
    cleaned = cleaned.split("@")[-1]
    tokens: set = set()
    current: list = []
    for char in cleaned:
        if char.isalnum():
            current.append(char)
        else:
            if current:
                tokens.add("".join(current))
                current = []
    if current:
        tokens.add("".join(current))
    return tokens


def _registrable(value: str) -> set:
    """Every dotted suffix of the host part, so a subdomain of a broker is caught too."""
    cleaned = value.strip().lower()
    for prefix in ("https://", "http://", "tcp://", "wss://", "ws://"):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix) :]
    host = cleaned.split("/")[0].split(":")[0].split("@")[-1]
    parts = host.split(".")
    return {".".join(parts[index:]) for index in range(len(parts)) if parts[index:]}


def judge_host(value: str) -> "str | None":
    """Return the reason this host is an execution venue, or None."""
    tokens = _labels(value)
    hit = sorted(tokens & BROKER_CONCEPT_TOKENS)
    if hit:
        return (
            f"its name carries the execution concept(s) {', '.join(hit)}. An allowlist "
            "entry is a host this system may talk to, and this one is an order-routing "
            "or trading endpoint by its own name."
        )
    suffixes = _registrable(value)
    known = sorted(suffixes & BROKER_DOMAINS)
    if known:
        return (
            f"{known[0]} is a known broker, exchange or order-routing operator. It "
            "carries no concept word at all, which is precisely why a vocabulary rule "
            "alone would let it through."
        )
    return None


def main() -> int:
    args = parse_root(CHECK_ID, __doc__)
    root, code = resolve_root(CHECK_ID, args.root)
    if root is None:
        return code

    check = Check(CHECK_ID, root)
    compose_path = root / COMPOSE

    if not compose_path.is_file():
        return check.refuse(
            f"{COMPOSE} does not exist in this subject tree. There is no declared egress "
            "posture to read, and an absent posture must not read as a safe one."
        )

    try:
        document = load_yaml(compose_path)
    except YamlSubsetError as exc:
        return check.refuse(
            f"{COMPOSE} could not be parsed by this reader: {exc}. A posture the check "
            "cannot read is a posture the check cannot verify. It refuses rather than "
            "guessing at a construct it does not understand."
        )

    services = document.get("services")
    if not isinstance(services, dict) or not services:
        return check.refuse(
            f"{COMPOSE} declares no services. Nothing was examined."
        )

    networks = document.get("networks")
    if not isinstance(networks, dict) or not networks:
        return check.refuse(
            f"{COMPOSE} declares no networks, so 'attached only to internal networks' "
            "cannot be established."
        )

    internal_networks = {
        name
        for name, body in networks.items()
        if isinstance(body, dict) and str(body.get("internal", "")).lower() == "true"
    }

    # A posture hiding behind an unresolved merge would read as ABSENT. Refuse instead.
    hidden = [
        (trail, alias, line)
        for trail, alias, line in unresolved_aliases(services)
        if trail and trail[-1] in {"x-egress", "networks", "ports", "policy", "hosts"}
    ]
    if hidden:
        rendered = "; ".join(
            f"{'/'.join(str(part) for part in trail)} -> {alias} (line {line})"
            for trail, alias, line in hidden
        )
        return check.refuse(
            "a posture field is supplied through an unresolved YAML alias and this reader "
            f"does not expand aliases: {rendered}. Read literally the field would appear "
            "ABSENT, which is how a posture hides behind an indirection. Write it out on "
            "the service."
        )

    for name, body in sorted(services.items()):
        if not isinstance(body, dict):
            check.violation(
                compose_path,
                line_of(services, name),
                "CD-EGRESS-003: service is not a mapping",
                f"service `{name}` could not be read as a mapping, so its posture is "
                "unknown. Unknown is a violation, not a default.",
            )
            continue

        service_line = line_of(services, name)

        # -- CD-EGRESS-003: every service declares a posture --------------------------- #
        check.asserted()
        egress = body.get("x-egress")
        if not isinstance(egress, dict):
            check.violation(
                compose_path,
                service_line,
                "CD-EGRESS-003: no x-egress block",
                f"service `{name}` declares no `x-egress` block. Every service declares "
                "one, with no exception and no default: a check that skipped a service it "
                "did not recognise would be bypassed by adding a service.",
            )
            continue

        egress_line = line_of(body, "x-egress") or service_line
        policy = egress.get("policy")
        hosts = egress.get("hosts")
        pending = egress.get("pending")

        check.asserted()
        if not isinstance(policy, str) or str(policy) not in VALID_POLICIES:
            check.violation(
                compose_path,
                line_of(egress, "policy") or egress_line,
                "CD-EGRESS-003: policy is not one of the declared values",
                f"service `{name}` declares policy={policy!r}; the contract admits only "
                f"{' or '.join(VALID_POLICIES)}. An unrecognised policy is a violation, "
                "not an unknown to be tolerated.",
            )

        check.asserted()
        if hosts is None or not isinstance(hosts, list):
            check.violation(
                compose_path,
                line_of(egress, "hosts") or egress_line,
                "CD-EGRESS-003: no hosts list",
                f"service `{name}` declares no `hosts` list. An absent list is not an "
                "empty one: it is a field nobody wrote, and it must not read as 'nothing "
                "is reachable'.",
            )
            hosts = []

        check.asserted()
        if not egress.get("enforced_by"):
            check.violation(
                compose_path,
                egress_line,
                "CD-EGRESS-003: no enforced_by",
                f"service `{name}` names no instrument that makes its policy true. A "
                "policy nothing enforces is a claim.",
            )

        # -- CD-EGRESS-001: the four services with no egress at all --------------------- #
        if name in NO_EGRESS_SERVICES:
            check.asserted(3)
            if str(policy) != "NONE":
                check.violation(
                    compose_path,
                    line_of(egress, "policy") or egress_line,
                    "CD-EGRESS-001: a no-egress service declares egress",
                    f"service `{name}` must declare policy NONE (BLUEPRINT §2 and §13: "
                    f"the engine and both surfaces have no egress at all); it declares "
                    f"{policy!r}.",
                )
            if list(hosts):
                check.violation(
                    compose_path,
                    line_of(egress, "hosts") or egress_line,
                    "CD-EGRESS-001: a no-egress service names hosts",
                    f"service `{name}` names {len(list(hosts))} host(s) — "
                    f"{', '.join(str(host) for host in hosts)} — under a policy that must "
                    "reach nothing at all.",
                )
            attached = body.get("networks")
            attached_list = (
                [str(item) for item in attached] if isinstance(attached, list) else []
            )
            if not attached_list:
                check.violation(
                    compose_path,
                    service_line,
                    "CD-EGRESS-001: no declared network attachment",
                    f"service `{name}` declares no `networks` list, so 'attached only to "
                    "internal networks' cannot be established. Structural absence of "
                    "egress is a property of the topology, and the topology must be "
                    "written down.",
                )
            else:
                routed = [
                    network
                    for network in attached_list
                    if network not in internal_networks
                ]
                if routed:
                    check.violation(
                        compose_path,
                        line_of(body, "networks") or service_line,
                        "CD-EGRESS-001: attached to a network that is not internal",
                        f"service `{name}` is attached to {', '.join(routed)}, which "
                        "is/are not declared `internal: true`. A container attached to a "
                        "routed network has egress by attachment, whatever its policy "
                        "says — and policy is a declaration while attachment is a route.",
                    )

        # -- CD-EGRESS-002: no allowlist anywhere names a broker ------------------------ #
        for position, host in enumerate(list(hosts)):
            check.asserted()
            reason = judge_host(str(host))
            if reason:
                check.violation(
                    compose_path,
                    line_of(hosts, position) or egress_line,
                    "CD-EGRESS-002: an allowlist names a broker",
                    f"service `{name}` may reach `{host}`, and {reason} CD-AC-012: no "
                    "execution pathway exists, and advisory-only is structural rather "
                    "than a policy anybody has to keep.",
                )

        if isinstance(pending, list):
            for position, entry in enumerate(pending):
                check.asserted()
                text = (
                    " ".join(f"{key} {value}" for key, value in entry.items())
                    if isinstance(entry, dict)
                    else str(entry)
                )
                for word in text.split():
                    reason = judge_host(word)
                    if reason and "." in word:
                        check.violation(
                            compose_path,
                            line_of(pending, position) or egress_line,
                            "CD-EGRESS-002: a pending entry names a broker host",
                            f"service `{name}`'s pending list names `{word}`, and "
                            f"{reason} A pending entry grants nothing today and is a host "
                            "somebody intends to add tomorrow, which is the same "
                            "decision made earlier.",
                        )
                        break

    check.note(
        f"networks declared internal: {', '.join(sorted(internal_networks)) or 'NONE'}"
    )
    check.note(
        "this check verifies a DECLARATION and the topology behind it. BLUEPRINT §2 and "
        "compose.yaml both disclose that Compose has no per-host egress primitive, so an "
        "ALLOWLIST is enforced by a lane owed at WO-3. No packet was observed and none is "
        "claimed."
    )

    return check.done(f"{len(services)} services and {len(networks)} networks in {COMPOSE}")


if __name__ == "__main__":
    raise SystemExit(main())
