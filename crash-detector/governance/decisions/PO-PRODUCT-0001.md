# PO product requirements — the publication surface explains itself
date: 2026-08-22 · authority: Matt (spoken direction, ratified) · recorded by: Product Owner (Trinity)

Ratified product content for the PUBLICATION SURFACE (WO-4). Recorded now so WO-4 is scoped
against it from day one. **NOT WO-2R3 scope; the running seat is untouched.** Data
prerequisites arrive with WO-3 (registered sources). Source: Matt, 2026-08-22, verbatim in
fabric at `trinity:pbgv2:crash_detector:product_req:indicator_explainability:v1`.

**R1 — Every indicator gets its own section**: plain-language description, the actual
calculation, and its dial binding — which dial(s) it feeds, with what weight/criticality.

**R2 — A historic chart per indicator, at the indicator's own relevant window** (days for
fast market series, weeks/months for credit series, quarters for survey series). Every
point carries its first-published timestamp — no backfilled point presented as live track
record (CD-AC-010).

**R3 — Movement and contribution visible at a glance**: what is moving, how quickly (slope
is first-class, CD-AC-011 extended from dials to indicators), the change over time, and the
indicator's CONTRIBUTION to the overall score — level alone is not enough.

**R4 — Combination effects named and explained.** An indicator harmless alone may multiply
in combination. Every combination/multiplier is DECLARED, NAMED and EXPLAINED on the page,
and shown when active — never an implicit interaction inside a formula. Under
BP-AMENDMENT-0001 a combination multiplier IS A MODEL: a named `MappingKind` member with a
registered, provenanced `ModelSpec`, owed its CD-D-005 account like any other mapping. An
unexplained multiplier therefore CANNOT COMPUTE — R4 is enforced by construction, and the
page renders what the registry declares.

**R5 — One historic dial section under the dials pair** (Matt's correction stands: NOT a
chart per dial; the dials themselves are unchanged). Both headline scores tracked over time
in a single section, visibly SEPARATE — never blended, never averaged; the dials fail in
opposite directions and blending cancels the signal. It answers: how has each dial read
over time, how fast is each moving, are they diverging — and, once real events pass, how
the instrument performed against them. Shared axis vs paired panels is a WO-4 rendering
choice taken WITH Matt.

**Review gate (standing):** when R1–R5 first render with real data, the page goes to Matt
for a joint looking-right review BEFORE the publication surface is called done. Rendering
choices are settled in that review.

**Lineage:** governed successor to the ARGUS /playbook page pattern (20 indicators, 10
categories, 8 combination mirror signals). The playbook proved the shape; the detector does
it with provenance and refusals.
