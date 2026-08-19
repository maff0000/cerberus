#!/usr/bin/env python3
"""CD-RT-012-EGRESS-NO-BROKER — there is nowhere for an execution pathway to go.

    python3 tools/register/check_egress_no_broker.py --root <subject tree>

CRITERION: CD-AC-012, "no execution pathway exists" (PID §6). PID §2 is constitutional on
this: the detector is advisory-only, and advisory-only is STRUCTURAL, not policy. BLUEPRINT
§2 and §13: "no container's egress allowlist names a broker; engine and both surfaces have
no egress at all."

READS THE POSTURE AS DATA, NOT AS PROSE. ``deploy/compose.yaml`` declares an ``x-egress``
block on every service and declares the contract those blocks answer to in
``x-cd-egress-contract``. ``deploy/egress-destinations.yaml`` declares the registry of
permitted destinations. A comment is not a posture, because a comment cannot be read by the
thing that has to refuse. This check reads both files with a stdlib-only YAML subset reader
and asserts the six invariants against them.

-------------------------------------------------------------------------------------------
WHAT CHANGED, AND WHY. THIS CHECK WAS DEFEATED AND THE REPAIR IS STRUCTURAL.
-------------------------------------------------------------------------------------------
CD-ASR-F04 (MEDIUM). An independent auditor (CD-ASR-WO2-01) put the IP literal
``198.51.100.24`` into cd-collectors' egress allowlist in place of ``api.ibkr.com``, and this
check exited 0 — PASS, 44 assertions, 0 violations, reproduced by this seat at ``cc961bf``
before anything was repaired. It recognised brokers BY NAME and an address has no name to
recognise.

THE REPAIR IS NOT AN IP-LITERAL DETECTOR. That would recognise one more SPELLING, and the
next spelling is a CIDR, a URL, an unregistered hostname, a punycode host, a hex-dotted
address or an internal service name. The structure is DENY BY DEFAULT over a declared,
in-tree destination registry: an allowlist entry is admissible only if somebody REGISTERED
that exact destination for that exact service. An IP literal then stops being a spelling to
catch and is simply not a destination anyone declared — the same thing every other unwritten
form is. THE CHECK PERFORMS NO RECOGNITION ON AN UNREGISTERED ENTRY, so there is no pattern
to write around.

RESOLUTION IS PROHIBITED, DELIBERATELY (CD-PL-F48, and the WO-2R dispatch in terms). A check
whose verdict depends on DNS or on any network call is not reproducible, cannot be run
offline by an auditor and therefore cannot be a gate. "What an entry reaches" is decided from
data in the tree and from nothing else. This check opens no socket.

-------------------------------------------------------------------------------------------
AND THEN IT WAS DEFEATED AGAIN, ONE FIELD ACROSS. CD-PL-F59.
-------------------------------------------------------------------------------------------
The repair above closed ``hosts`` and left ``pending`` carrying only layer 2. The Project
Lead measured the consequence on pristine extractions of ``b60d153``: ``api.ibkr.com`` in
cd-collectors' ``pending`` was REFUSED (exit 1, CD-EGRESS-002), and ``198.51.100.24`` IN THE
SAME SLOT PASSED — exit 0, 53 assertions, 0 violations — as did the same address on a
``host:`` key inside a pending mapping entry. That is CD-ASR-F04 reproduced verbatim one
field across, and the auditor's own sentence about the allowlist — "the check recognises
brokers BY NAME, and an IP literal has no name to recognise" — became true of ``pending``.

THE FIELD WAS ALREADY IN SCOPE AND THAT IS WHY IT COUNTS. This check fired CD-EGRESS-002 on
``pending`` and this header said the vocabulary applied "to every ``pending`` entry, because
a pending entry is a host". Having decided the field was worth guarding, it applied only the
layer CD-ASR-F04 had already proved insufficient. Worse, NONE of the six declared boundaries
mentioned ``pending`` at all, so under CD-RULE-004 the guard neither closed the class nor
declared the limit — and boundary 4 named a compensating LAYER 1 that did not exist for the
field (CD-RULE-006). Both defects are repaired here: CD-EGRESS-007 is layer 1 over
``pending``, and boundary 4 below is CORRECTED to say which layer 1 applies to which field.

THE REPAIR IS NOT THE REGISTRY AGAIN. Mirroring CD-EGRESS-004 onto ``pending`` would be
incoherent: a pending entry exists precisely because the host is UNKNOWN, so requiring it to
name a registered destination would either be unsatisfiable or would force a seat to invent
the hostname this project recorded as owed (CD-RULE-003, PBG-AUTH-005). The closure instead
takes the field's own meaning seriously — a pending entry is a record of an ABSENCE — and
closes its shape by equality, so there is no field in it that can hold a destination at all.
Three further routes of this seat's own devising were open at ``b60d153`` and are now shut:
an unresolved YAML alias into ``pending`` (V25), ``pending`` written as a mapping instead of
a list (V26), and a destination smuggled beneath an admissible key (V27).

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

 CD-EGRESS-004  DENY BY DEFAULT. Every ``hosts`` entry, in every service, is character for
                character the ``host`` of a destination registered in
                ``deploy/egress-destinations.yaml`` whose ``services`` list names that
                service. Anything else is a violation because nobody declared it. THIS IS THE
                LAYER THAT CLOSES CD-ASR-F04, and it closes it for the class rather than for
                the address: the entry is refused without being examined.

 CD-EGRESS-005  CLOSED KEY SETS. ``x-egress`` admits exactly ``policy``, ``hosts``,
                ``pending``, ``enforced_by``; a registered destination admits exactly ``id``,
                ``host``, ``operator``, ``purpose``, ``declared_in``, ``services``; the
                registry document admits exactly ``version``, ``contract``, ``destinations``.
                Any other key is a violation and not an extension. A field the guard does not
                read is a declaration nothing enforces — a posture arriving through
                ``hosts_extra:`` or ``allow:`` would otherwise be invisible to the very guard
                that is supposed to be reading the posture, which is CD-EGRESS-003's own
                argument applied to keys instead of to services.

 CD-EGRESS-006  A REGISTERED DESTINATION IS WELL FORMED AND ATTRIBUTABLE. ``host`` matches a
                POSITIVE permitted shape — two or more DNS labels of lowercase letters,
                digits and hyphens, no leading or trailing hyphen, final label alphabetic and
                at least two characters — so an unrecognised form is a violation rather than
                a silence. ``id`` and ``host`` are unique. ``operator``, ``purpose`` and
                ``declared_in`` are present and non-empty. Every service in ``services``
                exists in compose.yaml and declares policy ALLOWLIST.
                THE SHAPE RULE IS NOT TIDINESS AND IT IS NOT AN IP DETECTOR IN DISGUISE. The
                only offline evidence of what a destination REACHES is its registrable
                domain, which is what the known-operator denylist reads. An address literal
                carries no such evidence, so it cannot be judged by layer 2 at all — and a
                destination that cannot be judged must not be declarable, or the registry
                becomes the hole that the allowlist used to be.

 CD-EGRESS-007  A PENDING ENTRY DECLARES AN OMISSION, NOT A DESTINATION. ``pending`` is
                present and is a LIST; every entry is a mapping whose key set is EXACTLY
                ``declared_in`` and ``blocked_by``, both non-empty scalars. THIS IS LAYER 1
                OVER ``pending``, and it is a different layer 1 from CD-EGRESS-004's because
                a pending entry is not an allowlist entry: it is the record of an endpoint
                whose host is NOT KNOWN, so there is nothing to register and registering it
                would end the pendency. A HOST IS PRECISELY THE THING A PENDING ENTRY
                DECLARES THE ABSENCE OF, so the closure removes the field a destination
                could sit in rather than trying to recognise destinations — ``host:``,
                ``endpoint:``, ``url:``, ``address:``, ``target:`` and every key nobody has
                thought of fail one clause, asserted by EQUALITY with the declared set.

 CD-EGRESS-002  NO host names a broker, an exchange, an order-routing endpoint or a trading
                API. THIS SURVIVES AS A SECOND LAYER AND IS APPLIED IN THREE PLACES: to every
                registered destination's ``host`` and ``operator``, to every ``hosts`` entry
                as written, and to every ``pending`` entry as written. NEITHER LAYER IS SOLE
                — layer 1 catches what nobody declared or what is not the declared shape,
                layer 2 catches what somebody declared and should not have, and
                ``api.ibkr.com`` written into an allowlist OR into ``pending`` today fails
                BOTH.

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
effective egress of every service is none. The check therefore verifies the things that ARE
verifiable in WO-2 — the declared topology, the closure of the declaration against
undeclared destinations, and the absence of any named broker — and says so rather than
implying it has watched a packet.

-------------------------------------------------------------------------------------------
DECLARED LIMIT — WHAT THIS CHECK DOES NOT CATCH, AND WHICH LAYER DOES
-------------------------------------------------------------------------------------------
Required by CD-RULE-004, drawn in the pattern of CD-RT-012-NO-EXECUTION-INTERFACE, whose
declaration an independent auditor examined and judged HONESTLY DRAWN AND DRAWN
CONSERVATIVELY. Before this rework THIS CHECK HAD NO WRITTEN BOUNDARY AT ALL, and the
auditor said so in terms — "not covered by any declared limit" — which is half of why
CD-ASR-F04 exists. Every boundary below carries an example an auditor can execute, and
CD-RULE-006 binds the hand-offs: where a boundary says another layer carries the residue,
that layer was RUN and its refusal OBSERVED; where nothing was measured to carry it, it says
so in those words. The register entry for CD-RT-012-EGRESS-NO-BROKER and this check's
execution contract carry the same list.

**DO NOT READ A CLEAN RUN OF THIS CHECK AS PROOF THAT NO EXECUTION PATHWAY EXISTS.** It was
clean for `E05`, and after `E05` was closed it was still clean for `PL-S3a` — the SAME
address, one field across, in `pending` — which is CD-PL-F59 and is why boundary 4 below
carries a correction and boundaries 7 and 8 exist.

  1  THIS IS A DECLARATION, NOT AN ENFORCEMENT, AND NOTHING HERE STOPS A PACKET. Docker
     Compose has no per-host egress primitive; the lane that makes ALLOWLIST mean more than
     NONE is owed at WO-3. MEASURED EXAMPLE: a process inside cd-collectors opening a socket
     to any address is not seen by this check and would not be seen by it however the
     registry were written.
     WHAT DOES CARRY IT TODAY, MEASURED: the TOPOLOGY. Both networks are declared
     `internal: true` and every service is attached only to them, so no container has a route
     off the host at all. This check asserts that itself for the four no-egress services
     (CD-EGRESS-001), and `tests/test_deploy_container_set.py::test_both_networks_are_internal`
     asserts it for BOTH networks — run by this seat on a pristine extraction, 1 passed of 83
     in that module, exit 0. The registry closes the DECLARATION that the WO-3 lane will
     enforce; it does not pretend to be that lane.

  2  A REGISTERED DESTINATION IS A HUMAN CLAIM AND A FALSE ONE IS NOT DETECTABLE FROM THIS
     TREE. MEASURED EXAMPLE: register `id: DEST-X / host: quiet-data.example.org / operator:
     Quiet Data Ltd` for cd-collectors and name it in the allowlist — this check exits 0, and
     if that hostname in fact resolves to a brokerage edge nothing in this repository can
     know it, because knowing it needs the network and the network is prohibited (boundary 1
     of the reason, CD-PL-F48). NOT PROVED TO BE CARRIED ANYWHERE. What the structure buys is
     not detection but ATTRIBUTION: the claim must be written down at a named line, with an
     operator, a purpose and a `declared_in` clause, and reviewed by a person before it is
     reachable. That is a smaller claim than "the check resolves what an entry reaches", and
     it is the true one.

  3  `purpose` PROSE IS NOT JUDGED. MEASURED EXAMPLE: `purpose: "Route our orders to the
     executing broker"` on an otherwise well-formed destination does not fail this check.
     PARTIALLY CARRIED, MEASURED: the `operator` field IS judged by the same vocabulary and
     denylist as the host, so the archetypal case fails on the operator instead. Prose is
     deliberately left to the human reviewer here rather than scanned, because this project's
     own documentation says on every other page that it places no orders, and a guard that
     fired on its own charter would be switched off — the same argument
     CD-RT-012-NO-EXECUTION-INTERFACE's L3 makes at length about negation suppression.

  4  THE BROKER VOCABULARY AND THE KNOWN-OPERATOR DENYLIST ARE A FLOOR, NOT AN ORACLE —
     AND LAYER 1 IS NOT ONE RULE. IT IS A DIFFERENT RULE IN EACH FIELD, SO SAY WHICH.
     MEASURED EXAMPLE: a real brokerage whose registrable domain is on nobody's list and
     whose name carries no concept token passes LAYER 2 in every field. What stops it then
     depends entirely on WHERE it is written:
       - in `hosts`: LAYER 1 is CD-EGRESS-004, deny by default over the destination
         registry. It does not pass unless a human deliberately registers it, so the escape
         costs a signed edit to a reviewed registry file rather than a quiet allowlist line.
         CARRIED, MEASURED: `E05` puts `198.51.100.24` in cd-collectors' allowlist and is
         refused, exit 1, CD-EGRESS-004.
       - in the REGISTRY: LAYER 1 is CD-EGRESS-006's positive hostname shape. CARRIED,
         MEASURED: `V20` registers `198.51.100.24` as a destination — layer 2 cannot judge
         an address at all — and it is refused, exit 1, CD-EGRESS-006 (and CD-EGRESS-004 on
         the allowlist entry that named it).
       - in `pending`: LAYER 1 is CD-EGRESS-007, the CLOSED ENTRY SHAPE — NOT the registry,
         for the reason given above. CARRIED, MEASURED: `PL-S3a` puts `198.51.100.24` in
         cd-collectors' `pending` and is refused, exit 1, CD-EGRESS-007; `PL-S3c` puts it on
         a `host:` key inside a pending mapping and is refused, exit 1, CD-EGRESS-007.
       - in `pending` PROSE: THERE IS NO LAYER 1. SEE BOUNDARY 7, WHICH IS WHERE THAT
         RESIDUE IS DECLARED. Do not read this boundary as covering it.

     CORRECTION — WHY THIS BOUNDARY IS BEING REWRITTEN (CD-PL-F59, CD-RULE-006). As first
     written, this boundary said flatly that a brokerage passing layer 2 "does not pass LAYER
     1 unless a human deliberately registers it", naming no field. FOR `pending` THAT WAS
     MEASURABLY FALSE: there was no layer 1 over `pending` at all, so an entry passing layer
     2 there passed ENTIRELY, at the cost of exactly one quiet line and no registry edit.
     A boundary that names a compensating layer which does not compensate is worse than no
     boundary, because it spends an auditor's attention where the defect is not — the same
     shape as CD-PL-F54 at increment 2, and the shape CD-RULE-006 exists to forbid. The
     sentence is not softened here; it is made FIELD-SPECIFIC and each field's carrier is
     named with the variant that measured it.

  5  THE SUBJECT IS TWO FILES. Egress obtained by any other means is outside this check
     entirely: a `RUN curl` in a Dockerfile, a sidecar or an image with its own egress, host
     networking, a runtime `--add-host` or `--network`, an `extra_hosts` entry, or a proxy
     reached over an internal network. MEASURED EXAMPLE: `extra_hosts: ["api.ibkr.com:198.51.100.24"]`
     on cd-collectors is not read by this check. PARTIALLY CARRIED, MEASURED: the four
     no-egress services' network attachment IS asserted here, and
     `tools/register/check_base_image_digest_pin.py` and
     `tools/register/check_lockfile_denylist.py` cover other parts of the image supply chain —
     but for `extra_hosts` specifically, NOT PROVED TO BE CARRIED ANYWHERE. It is raised
     against this seat's own work as CD-ENG-WO2R-F12 and owed at WO-3 with the egress lane.

  6  IT IS A STATIC READ OF TWO FILES AT ONE COMMIT. No runtime, no image, no running
     container, no packet. A tree that is clean here can be deployed with a compose override
     file this check never sees. MEASURED EXAMPLE: `docker compose -f compose.yaml -f
     override.yaml up` with an override adding a routed network — outside the subject.
     NOT PROVED TO BE CARRIED ANYWHERE at WO-2; the override surface is owed at WO-3.

  7  THE PROSE INSIDE A PENDING ENTRY IS NOT JUDGED FOR ADDRESSES. CD-EGRESS-007 closes the
     SHAPE of a pending entry, so no FIELD in one can hold a destination; it does not and
     cannot judge the free text of `declared_in` and `blocked_by`, which exist to be read by
     a human reviewer.
     MEASURED EXAMPLE: `blocked_by: "CD-D-005; the source will be 198.51.100.24 once ruled"`
     on cd-collectors leaves this check at exit 0, PASS 69 assertions, 0 violations (variant
     `V29a`).
     PARTIALLY CARRIED, MEASURED: layer 2 IS applied to the flattened text of every pending
     entry, so the archetypal case fails on the name — the same sentence carrying
     `api.ibkr.com` instead is refused, exit 1, CD-EGRESS-002 (variant `V29b`). FOR AN
     ADDRESS LITERAL IN PROSE SPECIFICALLY, NOT PROVED TO BE CARRIED ANYWHERE.
     WHY IT IS NOT CLOSED, STATED SO THE ARGUMENT CAN BE JUDGED RATHER THAN ASSUMED: closing
     it would mean recognising which text tokens look like network endpoints, which is
     spelling recognition and is the exact defect CD-ASR-F04 and CD-PL-F59 both are. This is
     the same boundary as 3 (`purpose` prose), drawn for the same reason. WHAT IS DIFFERENT
     FROM CD-PL-F59, AND THE READER SHOULD WEIGH IT SCEPTICALLY: after CD-EGRESS-007 a
     pending entry has no host-bearing field, so an address in prose is a MENTION and not a
     DECLARATION — but that is an argument about what a future reader would do, and it is NOT
     a measured layer. It is recorded here as an argument, labelled as one, and it is not
     claimed to carry the residue.

  8  A DOCUMENT SHAPE EXISTS ON WHICH THIS CHECK DOES NOT TERMINATE, SO IT RETURNS NO VERDICT
     AT ALL. `tools/register/_yamlmin.py` enters an infinite loop on a block sequence opened
     by the FIRST key of a block-sequence item.
     MEASURED EXAMPLE, minimal: the three lines `top:` / `  - key:` / `      - nested` hang
     `load_yaml`. Reached through this check's own subject by variant `V30`, which writes
     `declared_in:` opening a nested sequence in cd-collectors' `pending`: the check does not
     return within 30 seconds and is killed at exit 124, which is not one of its four
     declared exit codes.
     NOT PROVED TO BE CARRIED ANYWHERE. It is NOT a false clean — the check never reports
     PASS — but non-termination is not a stated refusal either, and a gate that hangs is a
     gate somebody eventually disables.
     PRE-EXISTING AND NOT INTRODUCED BY THIS INCREMENT: it reproduces identically at the
     WO-2R dispatch base `ee8be6b`, before any of this seat's work. It is a defect of the
     shared reader, which `check_base_image_digest_pin.py` also uses, so repairing it changes
     the behaviour of a guard this dispatch does not cover. Raised as CD-ENG-WO2R-F14 and
     ESCALATED rather than fixed here, because this dispatch is bounded to CD-PL-F59 and
     widening scope silently is prohibited.

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

#: The in-tree destination registry. The admissible set is drawn from THIS FILE and from
#: nothing else — not from a constant in this script, and not from the network.
REGISTRY = "deploy/egress-destinations.yaml"

REGISTRY_CONTRACT = "CD-EGRESS-DESTINATION-REGISTRY-v1"

#: The services BLUEPRINT §2 gives no egress at all. Named, so a rename is a visible edit.
NO_EGRESS_SERVICES = ("cd-engine", "cd-public", "cd-private", "cd-store")

VALID_POLICIES = ("NONE", "ALLOWLIST")

#: CD-EGRESS-005. Closed key sets, asserted by EQUALITY against a declared member set rather
#: than by absence of a blacklist. This is increment 1's lesson applied to a declaration: a
#: guard that lists forbidden names is defeated by a name nobody listed, and `hosts_extra:`
#: is a name nobody listed. An unknown key here is a violation, not an extension.
X_EGRESS_KEYS = frozenset({"policy", "hosts", "pending", "enforced_by"})
REGISTRY_DOCUMENT_KEYS = frozenset({"version", "contract", "destinations"})

#: CD-EGRESS-007. The CLOSED key set of a `pending` entry, and the whole of layer 1 over that
#: field. A pending entry declares an OMISSION — an endpoint BLUEPRINT §2 says a service will
#: need, whose host could not be written without inventing it — so its content is (a) the
#: clause that authorises the future endpoint and (b) why the host is not written. A HOST IS
#: PRECISELY THE THING A PENDING ENTRY DECLARES THE ABSENCE OF, so there is no field here that
#: can carry one, and `host:`, `endpoint:`, `url:`, `address:`, `target:` and every key nobody
#: has thought of all fail the same clause: the key set is asserted by EQUALITY, so an
#: unrecognised key is a violation rather than a silence.
PENDING_KEYS = frozenset({"declared_in", "blocked_by"})
DESTINATION_KEYS = frozenset(
    {"id", "host", "operator", "purpose", "declared_in", "services"}
)

#: CD-EGRESS-006. The POSITIVE permitted shape of a declarable destination host. Written as
#: what IS admissible, so an unrecognised form fails; a rule written as what is forbidden is
#: defeated by the next form nobody thought of, which is exactly how CD-ASR-F04 happened.
HOST_LABEL_ALPHABET = frozenset("abcdefghijklmnopqrstuvwxyz0123456789-")
HOST_LABEL_MAX = 63
HOST_MAX = 253

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


def hostname_defect(value: str) -> "str | None":
    """Why ``value`` is NOT a declarable destination hostname, or None.

    A POSITIVE PERMITTED SHAPE, and the distinction from the check this replaces is the
    whole of CD-ASR-F04's repair. The old rule asked "does this look like a broker?" and an
    address literal answered no. This rule asks "is this a DNS hostname somebody could
    attribute to an operator?", and an address literal, a CIDR block, a URL, a wildcard, a
    bare service name, a hex-dotted address and every other form nobody has thought of all
    answer no — not because any of them was recognised, but because none of them is the one
    admissible shape.

    THIS IS NOT AN IP-LITERAL DETECTOR WEARING A COAT. It never asks whether something is an
    address. `198.51.100.24` fails on the same clause as `10.0.0.0/8`, `https://x.example/`
    and `*.example.org`: the shape was not matched. The reason a hostname is the admissible
    shape is stated in CD-EGRESS-006 — the only offline evidence of what a destination
    REACHES is its registrable domain, and an address carries none, so it cannot be judged by
    the broker denylist at all.
    """
    if not isinstance(value, str):
        return f"it is {type(value).__name__}, not a scalar"
    text = str(value)
    if not text:
        return "it is empty"
    if text != text.strip():
        return "it carries leading or trailing whitespace"
    if len(text) > HOST_MAX:
        return f"it is {len(text)} characters, over the {HOST_MAX}-character DNS limit"
    if text != text.lower():
        return (
            "it is not in canonical lower case. A destination is compared to an allowlist "
            "entry character for character, so two spellings of one host would be two "
            "destinations and one of them would be unregistered"
        )
    labels = text.split(".")
    if len(labels) < 2:
        return (
            "it is a single label. An egress destination is a name outside this system, and "
            "a single label is a container-network service name, a search-domain-dependent "
            "short name, or nothing at all"
        )
    for label in labels:
        if not label:
            return "it has an empty label (a leading, trailing or doubled dot)"
        if len(label) > HOST_LABEL_MAX:
            return f"the label `{label}` is over {HOST_LABEL_MAX} characters"
        stray = sorted(set(label) - HOST_LABEL_ALPHABET)
        if stray:
            return (
                f"the label `{label}` carries {', '.join(repr(char) for char in stray)}, "
                "which is outside the admissible alphabet of lowercase letters, digits and "
                "hyphen"
            )
        if label.startswith("-") or label.endswith("-"):
            return f"the label `{label}` begins or ends with a hyphen"
    final = labels[-1]
    if len(final) < 2 or not final.isalpha():
        return (
            f"its final label `{final}` is not an alphabetic top-level domain of at least "
            "two characters. This is the clause an address literal fails, and it fails it "
            "for the reason CD-EGRESS-006 states: a destination whose registrable domain "
            "cannot be read is a destination the known-operator denylist cannot judge, and a "
            "destination nothing can judge must not be declarable"
        )
    return None


def _text(value) -> str:
    """A scalar as stripped text, or "" for anything that is not one."""
    return str(value).strip() if isinstance(value, str) else ""


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

    # -- THE DESTINATION REGISTRY ------------------------------------------------------- #
    # Loaded BEFORE any service is judged, because the admissible set is derived from this
    # artefact and from nothing else. Change the artefact and the guard's subject follows;
    # there is no constant in this file naming a permitted host, and there cannot be one.
    #
    # ABSENT or UNPARSEABLE is a PRECONDITION failure, never a pass. A check that read a
    # missing registry as "nothing is registered, so nothing is wrong" would be defeated by
    # deleting a file, which is the cheapest bypass there is.
    registry_path = root / REGISTRY
    if not registry_path.is_file():
        return check.refuse(
            f"{REGISTRY} does not exist in this subject tree. Every egress allowlist entry "
            "is admissible only by being a REGISTERED destination (CD-EGRESS-004), so with "
            "no registry there is no admissible set and nothing can be judged. An absent "
            "registry must not read as an empty one: an empty registry is a decision "
            "somebody wrote down, and an absent one is a file somebody removed."
        )
    try:
        registry = load_yaml(registry_path)
    except YamlSubsetError as exc:
        return check.refuse(
            f"{REGISTRY} could not be parsed by this reader: {exc}. A registry the check "
            "cannot read is an admissible set the check cannot establish. It refuses rather "
            "than guessing at a construct it does not understand."
        )

    check.asserted()
    stray_document_keys = sorted(set(registry) - REGISTRY_DOCUMENT_KEYS)
    if stray_document_keys:
        check.violation(
            registry_path,
            line_of(registry, stray_document_keys[0]),
            "CD-EGRESS-005: the registry document declares an unknown key",
            f"{REGISTRY} declares {', '.join('`' + key + '`' for key in stray_document_keys)}"
            f", which is not one of {', '.join(sorted(REGISTRY_DOCUMENT_KEYS))}. The key set "
            "is CLOSED and asserted by equality with the declared set, not by absence of a "
            "blacklist: a key the guard does not read is a declaration nothing enforces.",
        )

    check.asserted()
    if _text(registry.get("contract")) != REGISTRY_CONTRACT:
        check.violation(
            registry_path,
            line_of(registry, "contract") or 1,
            "CD-EGRESS-005: the registry declares no known contract",
            f"{REGISTRY} declares contract {registry.get('contract')!r}; this check reads "
            f"{REGISTRY_CONTRACT}. A registry answering to a contract this guard does not "
            "know is a registry whose entry shape this guard cannot assert, and reading it "
            "anyway would be guessing.",
        )

    destinations = registry.get("destinations")
    check.asserted()
    if not isinstance(destinations, list):
        return check.refuse(
            f"{REGISTRY} declares no `destinations` list (found "
            f"{type(destinations).__name__}). An absent list is not an empty one: it is a "
            "field nobody wrote, and it must not read as 'nothing is registered'."
        )

    # by_host maps a registered host to the set of services entitled to name it. It is built
    # ONLY from entries that are themselves well formed: a malformed entry registers nothing,
    # so a broken registry fails closed rather than widening the admissible set.
    by_host: dict = {}
    seen_ids: dict = {}
    for position, entry in enumerate(destinations):
        entry_line = line_of(destinations, position) or line_of(registry, "destinations")

        check.asserted()
        if not isinstance(entry, dict):
            check.violation(
                registry_path,
                entry_line,
                "CD-EGRESS-005: a destination is not a mapping",
                f"destination #{position} could not be read as a mapping, so its six "
                "declared fields cannot be read. Unknown is a violation, not a default.",
            )
            continue

        check.asserted()
        stray = sorted(set(entry) - DESTINATION_KEYS)
        missing = sorted(DESTINATION_KEYS - set(entry))
        if stray or missing:
            check.violation(
                registry_path,
                entry_line,
                "CD-EGRESS-005: a destination's key set is not the declared key set",
                f"destination #{position} declares "
                f"{'unknown key(s) ' + ', '.join(stray) if stray else 'no unknown key'} and "
                f"{'is missing ' + ', '.join(missing) if missing else 'misses nothing'}. A "
                "destination declares EXACTLY id, host, operator, purpose, declared_in and "
                "services. Equality with the declared set, not absence of a blacklist.",
            )
            continue

        identifier = _text(entry.get("id"))
        host = _text(entry.get("host"))
        operator = _text(entry.get("operator"))
        purpose = _text(entry.get("purpose"))
        declared_in = _text(entry.get("declared_in"))
        services_named = entry.get("services")

        check.asserted()
        if not identifier:
            check.violation(
                registry_path,
                line_of(entry, "id") or entry_line,
                "CD-EGRESS-006: a destination has no id",
                f"destination #{position} declares no `id`. A destination that cannot be "
                "named cannot be cited in a decision, a build log entry or a review.",
            )
        elif identifier in seen_ids:
            check.violation(
                registry_path,
                line_of(entry, "id") or entry_line,
                "CD-EGRESS-006: duplicate destination id",
                f"`{identifier}` is already declared at line {seen_ids[identifier]}. Two "
                "destinations under one id make the record ambiguous about which one a "
                "reviewer approved.",
            )
        else:
            seen_ids[identifier] = line_of(entry, "id") or entry_line

        check.asserted()
        defect = hostname_defect(entry.get("host"))
        if defect:
            check.violation(
                registry_path,
                line_of(entry, "host") or entry_line,
                "CD-EGRESS-006: a destination host is not a declarable hostname",
                f"destination `{identifier or position}` declares host "
                f"{entry.get('host')!r}, and {defect}. A destination is declarable only in "
                "the POSITIVE shape CD-EGRESS-006 states — two or more DNS labels of "
                "lowercase letters, digits and hyphens, final label alphabetic. This clause "
                "is not an address detector: it never asks what the value IS, only whether "
                "it is the one admissible shape, so an address, a CIDR, a URL, a wildcard "
                "and a form nobody has thought of all fail it alike.",
            )
            continue

        check.asserted()
        if host in by_host:
            check.violation(
                registry_path,
                line_of(entry, "host") or entry_line,
                "CD-EGRESS-006: duplicate destination host",
                f"`{host}` is registered more than once. Two entries for one host mean two "
                "purposes and two authorising clauses for one route, and a reviewer removing "
                "one would not remove the route.",
            )

        for field_name, field_value in (
            ("operator", operator),
            ("purpose", purpose),
            ("declared_in", declared_in),
        ):
            check.asserted()
            if not field_value:
                check.violation(
                    registry_path,
                    line_of(entry, field_name) or entry_line,
                    f"CD-EGRESS-006: a destination declares no {field_name}",
                    f"destination `{identifier or position}` declares no `{field_name}`. A "
                    "destination with no operator cannot be attributed, one with no purpose "
                    "cannot be reviewed, and one with no `declared_in` clause is a route "
                    "nobody with product authority agreed to.",
                )

        # -- CD-EGRESS-002, LAYER 2 OVER THE REGISTRY ITSELF ---------------------------- #
        # The vocabulary and the known-operator denylist survive here, and this is where
        # they earn their keep now: layer 1 cannot judge a destination somebody DID
        # register, and this does. `operator` is read as well as `host`, so a brokerage
        # cannot be admitted by registering an innocent-looking hostname it owns.
        for field_name, field_value in (("host", host), ("operator", operator)):
            check.asserted()
            reason = judge_host(field_value) if field_value else None
            if reason:
                check.violation(
                    registry_path,
                    line_of(entry, field_name) or entry_line,
                    "CD-EGRESS-002: a REGISTERED destination is a broker",
                    f"destination `{identifier or position}` declares {field_name} "
                    f"`{field_value}`, and {reason} Registering it does not make it "
                    "admissible: deny-by-default decides what nobody declared, and this "
                    "layer decides what somebody declared and should not have.",
                )

        check.asserted()
        if not isinstance(services_named, list) or not services_named:
            check.violation(
                registry_path,
                line_of(entry, "services") or entry_line,
                "CD-EGRESS-006: a destination names no services",
                f"destination `{identifier or position}` declares no `services` list. A "
                "destination registered for nobody grants nothing, and an entry that grants "
                "nothing in a deny-by-default registry is a line waiting to be widened by "
                "somebody who does not know what it was for.",
            )
            services_named = []

        entitled: set = set()
        for service_name in services_named:
            named = _text(service_name)
            check.asserted()
            if named not in services:
                check.violation(
                    registry_path,
                    line_of(entry, "services") or entry_line,
                    "CD-EGRESS-006: a destination names a service that does not exist",
                    f"destination `{identifier or position}` names service `{named}`, which "
                    f"is not declared in {COMPOSE}. A grant to a service nobody runs is a "
                    "grant that becomes live the day somebody adds that name.",
                )
                continue
            service_body = services.get(named)
            service_policy = (
                service_body.get("x-egress", {}).get("policy")
                if isinstance(service_body, dict)
                and isinstance(service_body.get("x-egress"), dict)
                else None
            )
            if str(service_policy) != "ALLOWLIST":
                check.violation(
                    registry_path,
                    line_of(entry, "services") or entry_line,
                    "CD-EGRESS-006: a destination is registered for a no-egress service",
                    f"destination `{identifier or position}` names service `{named}`, which "
                    f"declares policy {service_policy!r}. BLUEPRINT §13 gives cd-engine, "
                    "cd-public, cd-private and cd-store no egress at all, so a destination "
                    "registered for one of them is a declaration that contradicts the "
                    "criterion even before any allowlist names it.",
                )
                continue
            entitled.add(named)

        if host and host not in by_host:
            by_host[host] = entitled
        elif host:
            by_host[host] = by_host[host] | entitled

    check.note(
        f"{len(by_host)} destination(s) registered in {REGISTRY}"
        + (f": {', '.join(sorted(by_host))}" if by_host else " — the admissible set is EMPTY,"
           " which is WO-2's deliverable and not a gap: registering an ingredient source is"
           " CD-D-005 and is owed by the Product Owner (PBG-AUTH-005)")
    )

    # A posture hiding behind an unresolved merge would read as ABSENT. Refuse instead.
    #
    # CD-PL-F59, SECOND ORDER. This filter used to name five fields —
    # {x-egress, networks, ports, policy, hosts} — and `pending` was not among them, for the
    # same reason `pending` was in none of the declared boundaries. THAT LIST WAS AN
    # ENUMERATION OF SPELLINGS, which is the defect this whole rework exists to stop
    # repeating: a field added to the contract tomorrow would be aliasable and unrefused,
    # exactly as `pending` was. It is replaced by the SUBTREE — every field of an x-egress
    # block, at any depth, plus the two topology fields — so the rule is "a posture may not
    # arrive through an indirection this reader does not expand" rather than a list of the
    # postures somebody remembered. Strictly wider: nothing previously refused is now
    # admitted.
    hidden = [
        (trail, alias, line)
        for trail, alias, line in unresolved_aliases(services)
        if "x-egress" in trail or (trail and trail[-1] in {"networks", "ports"})
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

        # -- CD-EGRESS-005: the x-egress key set is CLOSED ----------------------------- #
        # CD-EGRESS-003 argues that a check skipping a service it does not recognise is
        # bypassed by adding a service. The same argument applies one level down: a check
        # reading only the keys it knows is bypassed by adding a key. `hosts_extra:`,
        # `allow:` or `also:` would otherwise sit in the declaration the WO-3 lane inherits,
        # read by nobody and enforced by nothing.
        check.asserted()
        stray_keys = sorted(set(egress) - X_EGRESS_KEYS)
        if stray_keys:
            check.violation(
                compose_path,
                line_of(egress, stray_keys[0]) or egress_line,
                "CD-EGRESS-005: x-egress declares an unknown key",
                f"service `{name}` declares "
                f"{', '.join('`' + key + '`' for key in stray_keys)} inside `x-egress`; the "
                f"contract admits exactly {', '.join(sorted(X_EGRESS_KEYS))}. An unknown key "
                "is a violation and not an extension: a posture arriving through a field "
                "this guard does not read is a posture nothing enforces, and it would be "
                "invisible to the very check that is supposed to be reading the posture.",
            )

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

        # -- THE TWO LAYERS OVER EVERY ALLOWLIST ENTRY ---------------------------------- #
        # Layer 1 (CD-EGRESS-004) decides what nobody declared. Layer 2 (CD-EGRESS-002)
        # decides what somebody declared and should not have. BOTH RUN ON EVERY ENTRY, and
        # neither is sole — `api.ibkr.com` written here fails both, and `198.51.100.24`
        # fails the first without the second ever having to recognise anything about it.
        for position, host in enumerate(list(hosts)):
            host_line = line_of(hosts, position) or egress_line

            # -- CD-EGRESS-004, LAYER 1: DENY BY DEFAULT ------------------------------- #
            check.asserted()
            if not isinstance(host, str):
                check.violation(
                    compose_path,
                    host_line,
                    "CD-EGRESS-004: an allowlist entry is not a scalar",
                    f"service `{name}` declares an allowlist entry of type "
                    f"{type(host).__name__}. An entry is the `host` of a registered "
                    "destination, compared character for character; anything that is not a "
                    "scalar cannot be that, and cannot be registered.",
                )
            else:
                written = str(host)
                entitled = by_host.get(written)
                if entitled is None:
                    check.violation(
                        compose_path,
                        host_line,
                        "CD-EGRESS-004: an allowlist entry is not a registered destination",
                        f"service `{name}` may reach `{written}`, which is not registered in "
                        f"{REGISTRY}. THIS IS A VIOLATION BY DEFAULT: nothing was recognised "
                        f"about `{written}` and nothing needed to be. An egress destination "
                        "is a place somebody declared, with an operator, a purpose and the "
                        "clause of product intent that authorises it — an address literal, a "
                        "CIDR, a URL, a wildcard or a hostname added quietly is not that, "
                        "and neither is a spelling nobody has thought of yet. "
                        f"The admissible set at this commit is "
                        f"{'{' + ', '.join(sorted(by_host)) + '}' if by_host else 'EMPTY'}.",
                    )
                elif name not in entitled:
                    check.violation(
                        compose_path,
                        host_line,
                        "CD-EGRESS-004: a destination is registered, but not for this service",
                        f"service `{name}` may reach `{written}`, which IS registered in "
                        f"{REGISTRY} — but for "
                        f"{', '.join(sorted(entitled)) if entitled else 'no service at all'}"
                        f", not for `{name}`. A registry entry is a grant to named services, "
                        "not a global permit: a destination one service was authorised to "
                        "reach is not thereby authorised for the container that computes the "
                        "dials or for the one that talks to a model.",
                    )

            # -- CD-EGRESS-002, LAYER 2: THE ENTRY AS WRITTEN -------------------------- #
            check.asserted()
            reason = judge_host(str(host))
            if reason:
                check.violation(
                    compose_path,
                    host_line,
                    "CD-EGRESS-002: an allowlist names a broker",
                    f"service `{name}` may reach `{host}`, and {reason} CD-AC-012: no "
                    "execution pathway exists, and advisory-only is structural rather "
                    "than a policy anybody has to keep.",
                )

        # -- THE TWO LAYERS OVER EVERY PENDING ENTRY ------------------------------------ #
        # CD-PL-F59. Until this increment `pending` had layer 2 and NO layer 1, so
        # `198.51.100.24` written there passed exactly as it had passed in `hosts` before
        # deny-by-default arrived — CD-ASR-F04 surviving one field across. Layer 1 here is
        # NOT the destination registry, because a pending entry is not an allowlist entry:
        # it is the record of an endpoint whose host is NOT KNOWN, so there is nothing to
        # register and registering it would end the pendency. Layer 1 is instead the CLOSED
        # ENTRY SHAPE, and it closes the same class by removing the field a destination
        # could sit in rather than by recognising destinations.
        pending_line = line_of(egress, "pending") or egress_line

        check.asserted()
        if not isinstance(pending, list):
            check.violation(
                compose_path,
                pending_line,
                "CD-EGRESS-007: pending is not a list",
                f"service `{name}` declares `pending` as "
                f"{'nothing at all' if pending is None else type(pending).__name__}; the "
                "contract admits a LIST and nothing else. An absent or differently typed "
                "`pending` is not an empty one — it is the whole field disappearing from "
                "this guard's reach, and a check that skips a shape it does not recognise "
                "is bypassed by writing that shape. This is CD-EGRESS-003's own argument "
                "about services, applied to the container of a field instead.",
            )
            pending_entries: list = []
        else:
            pending_entries = list(pending)

        for position, entry in enumerate(pending_entries):
            pending_entry_line = line_of(pending, position) or pending_line

            # -- CD-EGRESS-007, LAYER 1: A PENDING ENTRY DECLARES AN OMISSION ----------- #
            check.asserted()
            if not isinstance(entry, dict):
                check.violation(
                    compose_path,
                    pending_entry_line,
                    "CD-EGRESS-007: a pending entry is not a declaration of an omission",
                    f"service `{name}`'s pending entry #{position} is "
                    f"{type(entry).__name__}, not a mapping. A pending entry declares an "
                    f"OMISSION — {', '.join(sorted(PENDING_KEYS))} — and NOT a destination. "
                    "A bare value here is a place somebody wrote where the record of a "
                    "missing place belongs. NOTHING WAS RECOGNISED ABOUT IT AND NOTHING "
                    "NEEDED TO BE: an address literal, a CIDR, a URL, a wildcard, a "
                    "hostname added quietly and a spelling nobody has thought of yet all "
                    "fail this clause alike, because none of them is the admissible shape.",
                )
            else:
                stray = sorted(set(entry) - PENDING_KEYS)
                missing = sorted(PENDING_KEYS - set(entry))
                if stray or missing:
                    check.violation(
                        compose_path,
                        line_of(entry, stray[0]) if stray else pending_entry_line,
                        "CD-EGRESS-007: a pending entry's key set is not the declared key set",
                        f"service `{name}`'s pending entry #{position} declares "
                        f"{'unknown key(s) ' + ', '.join('`' + key + '`' for key in stray) if stray else 'no unknown key'}"
                        f" and {'is missing ' + ', '.join(missing) if missing else 'misses nothing'}"
                        f". A pending entry declares EXACTLY "
                        f"{' and '.join(sorted(PENDING_KEYS))}, asserted by EQUALITY with "
                        "the declared set rather than by absence of a blacklist. A HOST IS "
                        "THE ONE THING A PENDING ENTRY CANNOT CARRY: it is the record that "
                        "a host is NOT KNOWN, so a `host:`, `endpoint:`, `url:`, "
                        "`address:` or `target:` key here is a destination declared where "
                        "the absence of a destination is the entire content.",
                    )
                else:
                    for field_name in sorted(PENDING_KEYS):
                        check.asserted()
                        field_value = entry.get(field_name)
                        if not isinstance(field_value, str) or not field_value.strip():
                            check.violation(
                                compose_path,
                                line_of(entry, field_name) or pending_entry_line,
                                "CD-EGRESS-007: a pending entry field is not a non-empty scalar",
                                f"service `{name}`'s pending entry #{position} declares "
                                f"`{field_name}` as "
                                f"{'an empty scalar' if isinstance(field_value, str) else type(field_value).__name__}"
                                ". Both fields are prose written for a human reviewer. A "
                                "nested mapping or list beneath an admissible key is a "
                                "structure the key set cannot constrain, and it is where a "
                                "destination would hide once the key set was closed.",
                            )

            # -- CD-EGRESS-002, LAYER 2: THE ENTRY AS WRITTEN, UNCHANGED IN REACH ------ #
            # Kept exactly as it was, over the flattened text of the entry whatever shape
            # it turned out to be. NEITHER LAYER IS SOLE: `api.ibkr.com` written as a bare
            # pending entry fails BOTH — layer 1 because a bare scalar is not the shape,
            # layer 2 because it is a broker — and `198.51.100.24` fails the first without
            # the second ever having to recognise anything about it. That is the same
            # division of labour deny-by-default already has over `hosts`.
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
                        pending_entry_line,
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
    check.note(
        "NO NAME WAS RESOLVED AND NO SOCKET WAS OPENED. The admissible set is derived from "
        f"{REGISTRY} in the subject tree and from nothing else, so this verdict is "
        "reproducible offline at this commit (CD-PL-F48). READ THE DECLARED LIMIT in this "
        "check's header before reading a clean run as proof of CD-AC-012: this check was "
        "clean for the escape that produced CD-ASR-F04 and for CD-PL-F59 one field across, "
        "and the EIGHT boundaries say what it "
        "still does not see and which layer — if any — was MEASURED to see it."
    )

    return check.done(
        f"{len(services)} services and {len(networks)} networks in {COMPOSE}, "
        f"{len(destinations)} registered destination(s) in {REGISTRY}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
