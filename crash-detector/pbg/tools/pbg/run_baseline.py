"""Host baselines that were OBSERVED, bound to the run that observed them (A-7).

WHAT WAS MEASURED. An authority record declared a host baseline of *19 containers, 14 networks, 14
volumes*. The observed host at grant was 16 / 13 / 14, and the previous audit's host had been
20 / 14 / 14. The declared figure therefore described neither: it was a dispatch-time constant
copied forward and presented as an observation. Reconciling against it would have manufactured a
phantom three-container discrepancy — or absorbed a real three-container leak as expected.

THE SHAPE OF THE DEFECT, which is worth naming because it is not a Docker defect. A number that was
never measured was treated as a measurement, and nothing in the evidence distinguished the two. The
repair is therefore about PROVENANCE, not about Docker: a baseline is a value plus WHO observed it,
WHEN, HOW, and DURING WHICH RUN, and a value missing any of those is not a baseline.

    OBSERVED    captured from this host, at a truthful UTC instant, by a recorded command,
                bound to a named run
    DECLARED    written into a record by a human before the run. NEVER authoritative. Reconcilable
                against an observation, and reported as agreeing or not — but it can never BE the
                observation, and it can never stand in for one.

BOUNDED ON PURPOSE. This is a baseline-recording correction, not a Docker redesign. It observes
through `docker_observe`, whose read-only allowlist already permits exactly `ps`, `network ls` and
`volume ls`; it starts nothing, removes nothing and reconfigures nothing; and it adds no capability
the module did not already have. The wrong figure in the closed record is NOT rewritten — that
record is append-only, and a governance record that quietly corrects its own history teaches the
next reader that records are editable.

COUNTS AND IDENTITIES, BOTH. A count that is unchanged proves nothing on its own: one container
removed and one created reconciles perfectly by arithmetic and is two events nobody saw. Identities
are captured beside the counts, and both deltas are reported.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

OBSERVED = "OBSERVED"
DECLARED = "DECLARED"

#: What each inventory is, and the exact read-only command that produces it. Recorded IN the
#: evidence, because "how was this measured" is the question a stale constant cannot answer.
MECHANISMS = {
    "containers": ("ps", "-a", "--no-trunc", "--format", "{{.ID}} {{.Names}}"),
    "networks": ("network", "ls", "--no-trunc", "--format", "{{.ID}} {{.Name}}"),
    "volumes": ("volume", "ls", "--format", "{{.Name}}"),
}

KINDS = tuple(MECHANISMS)


class BaselineUnavailable(Exception):
    """The host could not be observed. Callers fail closed; they never assume a clean host."""


@dataclass(frozen=True)
class Baseline:
    """One inventory snapshot, and everything needed to judge whether to believe it."""
    run_id: str
    captured_utc: str
    source: str
    identities: dict = field(default_factory=dict)
    mechanism: dict = field(default_factory=dict)
    counts_only: bool = False

    @property
    def authoritative(self) -> bool:
        """Only an observation is authoritative. A declared figure never becomes one by being read."""
        return self.source == OBSERVED

    def counts(self) -> dict:
        return {kind: len(self.identities.get(kind, ())) for kind in KINDS}

    def render(self) -> str:
        lines = [f"HOST BASELINE [{self.source}] run={self.run_id} at {self.captured_utc}"]
        for kind in KINDS:
            lines.append(f"  {kind:<11} {len(self.identities.get(kind, ())):>4}"
                         + ("" if self.counts_only else
                            f"  ({'; '.join(sorted(self.identities.get(kind, ()))[:3])}"
                            + (", …" if len(self.identities.get(kind, ())) > 3 else "") + ")"))
        if not self.authoritative:
            lines.append("  NON_AUTHORITATIVE: declared, not observed. It may be reconciled against "
                         "an observation; it may never stand in for one")
        for kind, command in sorted(self.mechanism.items()):
            lines.append(f"  mechanism   {kind}: {command}")
        return "\n".join(lines)


def utc_now() -> str:
    """Truthful UTC, from the clock, at the moment of the call."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def capture(run_id: str, *, docker=None) -> Baseline:
    """Observe this host NOW, and bind the observation to `run_id`.

    Raises rather than returning a partial snapshot: half a baseline invites the reader to complete
    it from somewhere else, and somewhere else is where the wrong number came from.
    """
    if not run_id:
        raise ValueError("a baseline must be bound to a run; an unbound baseline is a loose number")
    from . import docker_observe

    runner = docker or docker_observe._docker
    identities: dict[str, list[str]] = {}
    mechanism: dict[str, str] = {}
    for kind, command in MECHANISMS.items():
        try:
            out = runner(*command)
        except Exception as exc:                           # DockerUnavailable and friends
            raise BaselineUnavailable(
                f"{kind} could not be observed ({exc}); refusing to record a baseline that was not "
                "measured") from exc
        identities[kind] = sorted(line.strip() for line in out.splitlines() if line.strip())
        mechanism[kind] = "docker " + " ".join(command)
    return Baseline(run_id, utc_now(), OBSERVED, identities, mechanism)


#: `19 containers, 14 networks, 14 volumes` and every ordering of it.
_DECLARED = re.compile(r"(\d+)\s+(containers?|networks?|volumes?)", re.I)


def parse_declared(text: str, *, run_id: str = "<unbound>",
                   captured_utc: str = "<unstated>") -> Baseline:
    """A baseline written into a record by hand, marked for what it is.

    Deliberately NOT given a truthful timestamp or a real run id. A declared figure that looked like
    an observation is the whole defect; dressing it in the same fields would rebuild it.
    """
    identities = {kind: [] for kind in KINDS}
    counts = {}
    for number, noun in _DECLARED.findall(text or ""):
        counts[noun.lower().rstrip("s") + "s"] = int(number)
    for kind in KINDS:
        identities[kind] = [f"<declared #{i + 1}>" for i in range(counts.get(kind, 0))]
    return Baseline(run_id, captured_utc, DECLARED, identities,
                    {"source": "declared in a record; no command was run"}, counts_only=True)


@dataclass
class Reconciliation:
    status: str
    detail: str
    run_id: str | None = None
    count_deltas: dict = field(default_factory=dict)
    created: dict = field(default_factory=dict)
    removed: dict = field(default_factory=dict)
    findings: list[str] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return self.status == "RECONCILED"

    def render(self) -> str:
        lines = [f"HOST RECONCILIATION: {self.status}", f"  {self.detail}"]
        if self.run_id:
            lines.append(f"  run         {self.run_id}")
        for kind in KINDS:
            before, after = self.count_deltas.get(kind, (0, 0))
            mark = " " if before == after else "!"
            lines.append(f" {mark}{kind:<11} {before:>4} -> {after:<4}")
            for name in sorted(self.created.get(kind, ())):
                lines.append(f"      created  {name}")
            for name in sorted(self.removed.get(kind, ())):
                lines.append(f"      removed  {name}")
        lines += [f"  - {f}" for f in self.findings]
        return "\n".join(lines)


def reconcile(before: Baseline, after: Baseline, *, expected: dict | None = None) -> Reconciliation:
    """Compare two observations OF THE SAME RUN, by identity as well as by count.

    Refuses on three things, each of which has produced a false clean bill somewhere:

        a DECLARED figure on either side      it was never measured
        two different run ids                 the two snapshots are not about the same thing
        equal counts with different members   arithmetic that reconciles while the host changed
    """
    expected = expected or {}
    for role, baseline in (("before", before), ("after", after)):
        if not baseline.authoritative:
            return Reconciliation(
                "REFUSED",
                f"the {role} baseline is {baseline.source}, not an observation of this host. A "
                "dispatch-time figure is never reconciled against — it is the thing that produces "
                "phantom discrepancies and absorbs real ones",
                findings=[f"{role} baseline is NON_AUTHORITATIVE"])
    if before.run_id != after.run_id:
        return Reconciliation(
            "REFUSED",
            f"the baselines belong to different runs ({before.run_id} and {after.run_id}); a "
            "before and an after that were not bound to one run do not bound anything")

    result = Reconciliation("RECONCILED", "the host is exactly as this run found it",
                            run_id=before.run_id)
    unexpected = False
    for kind in KINDS:
        was = set(before.identities.get(kind, ()))
        now = set(after.identities.get(kind, ()))
        result.count_deltas[kind] = (len(was), len(now))
        created = sorted(now - was)
        removed = sorted(was - now)
        allowed = set(expected.get(kind, ()))
        result.created[kind] = created
        result.removed[kind] = removed
        for name in created + removed:
            if not any(token in name for token in allowed):
                unexpected = True
                result.findings.append(
                    f"UNEXPECTED {kind[:-1]} change: {name} was not declared as this run's own")
        if len(was) == len(now) and (created or removed):
            result.findings.append(
                f"{kind}: the COUNT is unchanged while the MEMBERS changed — one removed and one "
                "created reconciles perfectly by arithmetic and is two events nobody saw")

    if unexpected:
        result.status = "UNRECONCILED"
        result.detail = ("the host changed in ways this run did not declare; cleanup and "
                         "attribution must be resolved before the run is trusted")
    elif any(result.created[k] or result.removed[k] for k in KINDS):
        result.status = "RECONCILED_WITH_DECLARED_CHANGES"
        result.detail = "every change is attributable to artefacts this run declared as its own"
    return result


def compare_declared(observed: Baseline, declared: Baseline) -> list[str]:
    """State whether a record's declared figure matches the host — WITHOUT believing it.

    The output is always a report and never a verdict. This is what should have happened to
    19 / 14 / 14: not silently reconciled against, and not silently ignored either.
    """
    findings = [
        "the declared baseline is NON_AUTHORITATIVE: it was written into a record, not observed, "
        "and it is compared here only so a stale constant is visible rather than trusted"]
    observed_counts, declared_counts = observed.counts(), declared.counts()
    for kind in KINDS:
        if observed_counts[kind] != declared_counts[kind]:
            findings.append(
                f"{kind}: the record declares {declared_counts[kind]} and this run OBSERVED "
                f"{observed_counts[kind]}. The observation stands; the declared figure is reported "
                "as stale rather than reconciled against")
    return findings
