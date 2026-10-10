#!/usr/bin/env python3
"""THE EXTERNAL PROBE — **it runs OUTSIDE the container set** (CD-AC-008, CD-AC-014).

    python3 tools/probe/external_probe.py --health-url http://127.0.0.1:8710/health

===========================================================================================
*** WHY THIS FILE IS NOT A SERVICE, NOT AN IMAGE, AND NOT IN THE PACKAGE ***
===========================================================================================
BLUEPRINT §8, ``PBG-EVID-001``, ``PBG-DEPLOY-002``:

    *"The check that detects it runs OUTSIDE the container set — a process inside the
    system reporting that the system is publishing is SELF-CERTIFICATION."*

**A PROBE THAT DIES WITH THE THING IT WATCHES HAS REPORTED NOTHING.** That sentence is the
design, and every one of the following is a consequence of it rather than a style choice:

1. **IT IS NOT A SERVICE IN ``deploy/compose.yaml``.** Adding it there — even as a separate
   service on a separate network — puts it inside the unit that fails. ``docker compose
   down`` stops it along with everything it was watching, and the last thing it would ever
   report is health. **There is no ``x-egress`` block for it because there is no service for
   it.** A test parses ``compose.yaml`` and asserts it is absent.

2. **IT HAS NO ``Dockerfile``.** It is a host process, run by whatever schedules things on
   the host: cron, a systemd timer, an operator's terminal, a second machine.

3. **IT IMPORTS NOTHING FROM ``crash_detector``.** Not one name. An observer that shares
   code with the thing it observes is not an independent observer — if the application's own
   parsing of its own health document is wrong, a probe built on that parsing is wrong in
   exactly the same way and cannot see it. So the three key names this file reads are
   **written out here as literals**, duplicated from the application on purpose. That
   duplication is the point (``PBG-ASSURE-001``: *"an auditor verifying through a harness
   the project wrote is verifying the harness"*).

4. **IT HOLDS NO DATABASE CREDENTIAL AND ISSUES NO QUERY.** It cannot read
   ``publication.heartbeat``, ``alert.event`` or any envelope. It sees exactly what an
   outside party sees: **the public surface, over HTTP, unauthenticated.** No ``psycopg``,
   no DSN, no ``PGPASSWORD``, no private envelope, no internal API.

5. **THE UNREACHABLE CASE IS ITS MOST IMPORTANT VERDICT, NOT ITS ERROR PATH.** If the whole
   container set is down there is nothing to ask, and the probe must still be able to say
   so. ``ConnectionRefusedError`` is not an exception to be logged and swallowed here; it is
   the answer :data:`EXIT_UNREACHABLE`, and it is the one an inside-the-set checker can
   never produce because it is not running either.

===========================================================================================
THE BUDGET IS PID §5 AND IT IS NOT CHOSEN HERE
===========================================================================================
    *"Assurance latency budget: pipeline/publication failure independently detectable
    ≤ 15 minutes"* — ``PID.md`` §5, RATIFIED 2026-08-18, CD-D-003 resolved.

**INDEPENDENTLY is the operative word and this file is what makes it true.** 900 seconds is
the default for ``--max-publication-age-seconds`` and it is the ONLY default in this file
that carries a number, because it is the only one written down in ratified text. The probe's
own interval — how often the host runs it — is the operator's, and running it once per 15
minutes is the loosest schedule that can satisfy the clause.

===========================================================================================
EXIT CODES — AND WHY "UNREACHABLE" IS NOT "UNKNOWN"
===========================================================================================
    0  HEALTHY      the surface answered and reports itself live and not degraded
    1  DEGRADED     the surface answered and reports degradation, or its last publication
                    is older than the budget allows
    2  UNREACHABLE  *** nothing answered. The detector is not serving. ***
    3  PROBE_FAULT  the probe was misconfigured, or the answer was not a health document

**``UNREACHABLE`` IS A DETECTION AND EXITS NON-ZERO.** A probe that treated "I could not
reach it" as "no information, no opinion" would go quiet at exactly the moment the system
died — which is the silent failure the whole product exists to avoid, reproduced inside the
instrument built to catch it (``PBG-CI-002``: where a check cannot reach its authentic
target it must FAIL, never wave through).

``PROBE_FAULT`` is separate from ``UNREACHABLE`` on purpose. "Nobody is listening" and "I was
pointed at the wrong URL" have different causes and different fixes, and an operator reading
one while looking at the other wastes the time the exit code exists to save.

===========================================================================================
WHAT IT DOES NOT PROVE
===========================================================================================
* **It reads what the surface SAYS about itself.** A detector that is up, publishing
  nonsense, and truthfully reporting ``live: true`` exits ``0`` here. What the probe adds
  that no inside process can is the two facts that need no cooperation: **something is
  listening**, and **the last publication instant it reports is within the budget.**
* **It does not prove the container set is what answered.** Anything bound to that address
  would do. Confirming the responder is the deployment is the deployment's problem, and on
  this lane the container set is not built (``CONTAINER_READY_DESIGN``).
* **NOT PROVED TO BE CARRIED ANYWHERE:** that any host actually runs this on a schedule. The
  probe is delivered; the cron entry is a deployment act nobody has been authorised to take.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

EXIT_HEALTHY = 0
EXIT_DEGRADED = 1
EXIT_UNREACHABLE = 2
EXIT_PROBE_FAULT = 3

#: PID.md §5, RATIFIED. The ONLY number in this file derived from ratified text, and the
#: only one with a default.
PID_ASSURANCE_LATENCY_BUDGET_SECONDS = 900.0

#: *** DUPLICATED FROM THE APPLICATION ON PURPOSE — SEE POINT 3 OF THE MODULE DOCSTRING. ***
#: This probe imports nothing from `crash_detector`. If these names drift from the health
#: surface, the probe reports PROBE_FAULT rather than silently agreeing with a document it
#: no longer understands.
KEY_LIVE = "live"
KEY_DEGRADED = "degraded"
KEY_DEGRADED_CLASSES = "degraded_classes"
KEY_LAST_PUBLICATION = "last_publication_utc"


def _parse_utc(text: str) -> datetime:
    """ISO-8601 with an explicit ``Z``. A naive timestamp is refused, never assumed local."""
    if not isinstance(text, str) or not text.endswith("Z"):
        raise ValueError("timestamp is not ISO-8601 UTC with an explicit Z")
    return datetime.fromisoformat(text[:-1]).replace(tzinfo=timezone.utc)


def probe(
    health_url: str,
    *,
    timeout_seconds: float,
    max_publication_age_seconds: float,
    now_utc: "datetime | None" = None,
) -> tuple:
    """``(exit_code, verdict, detail)``. Never raises for a condition it can name.

    ``now_utc`` is an argument so a historical evaluation replays exactly — the same choice
    the whole freshness path makes (BLUEPRINT §7).
    """
    observed = now_utc or datetime.now(timezone.utc)

    # ---------------------------------------------------------------- IS ANYTHING THERE?
    try:
        request = urllib.request.Request(
            health_url, headers={"Accept": "application/json"}, method="GET"
        )
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            status = response.status
            body = response.read()
    except urllib.error.HTTPError as error:
        # It answered, with a refusal. That is reachable-but-unhealthy, not unreachable.
        return (
            EXIT_DEGRADED,
            "DEGRADED",
            f"the health surface answered HTTP {error.code}",
        )
    except (urllib.error.URLError, OSError, ValueError) as error:
        # *** THE VERDICT THAT NO PROCESS INSIDE THE CONTAINER SET CAN EVER PRODUCE. ***
        # Connection refused, DNS failure, timeout, host down: nothing is serving. The
        # probe is still running, because it was never part of what failed.
        return (
            EXIT_UNREACHABLE,
            "UNREACHABLE",
            f"nothing answered at {health_url}: {type(error).__name__}",
        )

    if status != 200:
        return (EXIT_DEGRADED, "DEGRADED", f"the health surface answered HTTP {status}")

    # ------------------------------------------------------------- IS IT A HEALTH DOCUMENT?
    try:
        document = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return (EXIT_PROBE_FAULT, "PROBE_FAULT", "the answer was not JSON")
    if not isinstance(document, dict):
        return (EXIT_PROBE_FAULT, "PROBE_FAULT", "the answer was not a JSON object")
    if KEY_LIVE not in document or KEY_LAST_PUBLICATION not in document:
        return (
            EXIT_PROBE_FAULT,
            "PROBE_FAULT",
            "the answer is missing the keys this probe reads; it may not be a health "
            "document, or the surface changed shape without this probe being updated",
        )

    # ------------------------------------------------------------------- WHAT DOES IT SAY?
    if document.get(KEY_LIVE) is not True:
        return (EXIT_DEGRADED, "DEGRADED", "the health surface does not report itself live")

    if document.get(KEY_DEGRADED) is True:
        classes = document.get(KEY_DEGRADED_CLASSES) or []
        # The CLASSES are reported. There is no value on this surface to report instead,
        # and this probe would not print one if there were.
        return (EXIT_DEGRADED, "DEGRADED", f"reported degradation classes: {classes}")

    # --------------------------------- AND THE ONE FACT THAT NEEDS NO COOPERATION: PID §5.
    last_published = document.get(KEY_LAST_PUBLICATION)
    if last_published is None:
        return (
            EXIT_DEGRADED,
            "DEGRADED",
            "the surface reports no publication has ever happened",
        )
    try:
        published_at = _parse_utc(last_published)
    except ValueError:
        return (
            EXIT_PROBE_FAULT,
            "PROBE_FAULT",
            f"{KEY_LAST_PUBLICATION} is not an ISO-8601 UTC timestamp",
        )

    age = (observed - published_at).total_seconds()
    if age > max_publication_age_seconds:
        return (
            EXIT_DEGRADED,
            "DEGRADED",
            f"the last publication is {age:.1f}s old and the PID §5 budget is "
            f"{max_publication_age_seconds:.1f}s",
        )

    return (
        EXIT_HEALTHY,
        "HEALTHY",
        f"live, not degraded, last publication {age:.1f}s ago",
    )


def main(argv: "list | None" = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Observe the crash detector's PUBLIC health surface from outside the container "
            "set. Holds no database credential and issues no query."
        )
    )
    parser.add_argument(
        "--health-url",
        required=True,
        help="the unauthenticated health endpoint, e.g. http://127.0.0.1:8710/health",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=10.0,
        help="bounded, so a hung surface is UNREACHABLE rather than a hung probe",
    )
    parser.add_argument(
        "--max-publication-age-seconds",
        type=float,
        default=PID_ASSURANCE_LATENCY_BUDGET_SECONDS,
        help="PID §5 assurance latency budget (default 900 = 15 minutes)",
    )
    arguments = parser.parse_args(argv)

    if not arguments.health_url.startswith(("http://", "https://")):
        print(
            "PROBE_FAULT: --health-url must be an http(s) URL", file=sys.stderr, flush=True
        )
        return EXIT_PROBE_FAULT

    exit_code, verdict, detail = probe(
        arguments.health_url,
        timeout_seconds=arguments.timeout_seconds,
        max_publication_age_seconds=arguments.max_publication_age_seconds,
    )
    stream = sys.stdout if exit_code == EXIT_HEALTHY else sys.stderr
    print(f"{verdict}: {detail}", file=stream, flush=True)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
