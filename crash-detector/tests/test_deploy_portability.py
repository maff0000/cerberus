"""D3 — the CUT-AND-PASTE PORTABILITY constraint, with both arms on every refusal.

``PO-DECISIONS-0025`` ruling 2 is BINDING: independent container, SQL in movable named
volumes, ALL config via env, cut-and-paste dev (dell) -> prod (cloud), *"the deploy audit
verifies cut-and-paste reproducibility before go-live."*

``tools/audit/check_deploy_portability.py`` is that audit. This file is the evidence that it
WORKS, and the shape of the evidence is the one ``required_evidence`` names: **the same
declared command exiting 0 on the clean subject and non-zero on the violated one.**

*** **EVERY MUTATION IS APPLIED TO A COPY IN A TEMPORARY DIRECTORY. THE REAL
``deploy/compose.yaml`` IS NEVER WRITTEN TO.** *** ``CD-PL-F154`` is what planting in a real
file costs, and a test that mutated the subject would be indistinguishable from the defect
it is testing for.

**AND THERE IS A THIRD ARM WHEREVER A REFUSAL COULD BE VACUOUS.** A rule that refused every
address would satisfy "no host baked in" by making the deployment unpublishable; a rule that
refused every literal would refuse ``TZ: UTC``. So each such rule is shown to ADMIT the thing
it must admit, in the same run in which it refuses the thing it must refuse.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
CHECK = REPO_ROOT / "deploy" / "check_portability.py"
COMPOSE_REL = pathlib.Path("deploy") / "compose.yaml"

EXIT_CLEAN = 0
EXIT_VIOLATION = 1
EXIT_PRECONDITION = 3


def _run(root: pathlib.Path) -> subprocess.CompletedProcess:
    """The ONE declared command, run identically on every subject. A contrast arm that
    invoked the check differently would prove nothing about the clean arm."""
    return subprocess.run(
        [sys.executable, "-B", str(CHECK), "--root", str(root)],
        capture_output=True,
        text=True,
        timeout=120,
    )


def _subject(tmp_path: pathlib.Path, *replacements: tuple[str, str]) -> pathlib.Path:
    """A scratch tree carrying a COPY of the real compose file, optionally mutated.

    Each replacement must match EXACTLY ONCE in the real file. A mutation that silently
    matched zero times would produce a clean subject dressed as a violated one, and the
    test would pass by not testing anything.
    """
    root = tmp_path / "subject"
    (root / "deploy").mkdir(parents=True)
    (root / "contracts").mkdir(parents=True)
    text = (REPO_ROOT / COMPOSE_REL).read_text(encoding="utf-8")
    for old, new in replacements:
        assert text.count(old) == 1, (
            f"the mutation anchor {old!r} appears {text.count(old)} times in the real "
            "compose file; a mutation that does not land makes this arm vacuous"
        )
        text = text.replace(old, new)
    (root / COMPOSE_REL).write_text(text, encoding="utf-8")
    return root


def _load_compose_resolved() -> dict:
    """The compose document WITH merge keys resolved, via the audit's own resolver."""
    sys.path.insert(0, str(REPO_ROOT / "deploy"))
    sys.path.insert(0, str(REPO_ROOT / "tools" / "register"))
    from check_portability import _resolve_merges, anchor_table
    from _yamlmin import load_yaml

    path = REPO_ROOT / COMPOSE_REL
    raw = load_yaml(path)
    return _resolve_merges(raw, raw, anchor_table(path.read_text(encoding="utf-8")))


# ========================================================================================= #
# THE CLEAN ARM. IT COMES FIRST BECAUSE A CLEAN ARM THAT FAILS PROVES ONLY THAT THE HARNESS
# IS BROKEN, AND A BROKEN HARNESS DETECTS NOTHING.
# ========================================================================================= #

def test_the_real_deployment_PASSES_the_portability_audit():
    result = _run(REPO_ROOT)
    assert result.returncode == EXIT_CLEAN, result.stdout + result.stderr
    assert "PASS" in result.stdout


def test_the_clean_arm_is_not_vacuous_it_makes_over_a_thousand_assertions():
    """``Check.done`` refuses a zero-assertion run, but 'more than zero' is a low bar. The
    real number is recorded so a future edit that quietly stops examining most of the
    document is visible as a collapse rather than as a still-green PASS."""
    result = _run(REPO_ROOT)
    line = [l for l in result.stdout.splitlines() if "assertions:" in l][0]
    assert int(line.split(":")[1].strip()) > 500, result.stdout


def test_a_copy_of_the_real_file_in_a_scratch_tree_also_passes(tmp_path):
    """The harness itself is honest: an UNMUTATED copy passes. Every violated arm below
    differs from THIS subject by exactly one edit, so the exit code is attributable to the
    edit and to nothing about the scratch tree."""
    assert _run(_subject(tmp_path)).returncode == EXIT_CLEAN


# ========================================================================================= #
# RULE 1 — AN ABSOLUTE HOST PATH IS THE CUT-AND-PASTE FAILING ITSELF
# ========================================================================================= #

def test_an_absolute_bind_source_is_REFUSED(tmp_path):
    root = _subject(tmp_path, ("source: ../contracts", "source: /srv/crash-detector/contracts"))
    result = _run(root)
    assert result.returncode == EXIT_VIOLATION, result.stdout
    assert "1: an absolute host path as a bind source" in result.stdout


def test_a_relative_bind_source_that_CLIMBS_OUT_of_the_repository_is_REFUSED(tmp_path):
    """An absolute path spelled portably is still an absolute path."""
    root = _subject(tmp_path, ("source: ../contracts", "source: ../../../../etc"))
    result = _run(root)
    assert result.returncode == EXIT_VIOLATION, result.stdout
    assert "escaping the repository" in result.stdout


def test_the_ADMITTING_ARM_a_relative_source_inside_the_tree_is_accepted(tmp_path):
    """**RULE 1 IS NOT SATISFIED BY REFUSING EVERY BIND MOUNT.** The real file's
    ``../contracts`` is relative and inside the tree, and it is admitted — that is the
    whole clean arm. Here it is moved to a DIFFERENT in-tree relative path, so what is
    demonstrated is that the rule tests the PROPERTY and not one remembered string."""
    root = _subject(tmp_path, ("source: ../contracts", "source: ./deploy/entrypoints"))
    assert _run(root).returncode == EXIT_CLEAN


# ========================================================================================= #
# RULE 2 — DURABLE DATA THAT DOES NOT TRAVEL
# ========================================================================================= #

def test_a_bind_mounted_database_directory_is_REFUSED(tmp_path):
    root = _subject(
        tmp_path,
        ("      - type: volume\n        source: cd-store-data",
         "      - type: bind\n        source: ./cd-store-data"),
    )
    result = _run(root)
    assert result.returncode == EXIT_VIOLATION, result.stdout
    assert "2: durable data outside a named volume" in result.stdout


def test_a_durable_volume_nobody_DECLARED_is_REFUSED(tmp_path):
    """An undeclared volume is created anonymously, and an anonymous volume does not
    travel — it is not even findable by name on the far side of the move."""
    root = _subject(tmp_path, ("        source: cd-store-data", "        source: cd-store-scratch"))
    result = _run(root)
    assert result.returncode == EXIT_VIOLATION, result.stdout
    assert "2: a volume nobody declared" in result.stdout


# ========================================================================================= #
# RULE 3 — A HOST BAKED IN. **THE POSITION IS THE WHOLE JUDGEMENT.**
# ========================================================================================= #

def test_an_address_literal_in_a_config_value_is_REFUSED(tmp_path):
    root = _subject(tmp_path, ("CD_STORE_HOST: cd-store\n      CD_STORE_PORT: \"5432\"\n      CD_STORE_NAME: \"${CD_STORE_NAME:?CD_STORE_NAME must be set}\"\n      CD_STORE_ROLE: cd_collector",
                               "CD_STORE_HOST: 10.11.12.13\n      CD_STORE_PORT: \"5432\"\n      CD_STORE_NAME: \"${CD_STORE_NAME:?CD_STORE_NAME must be set}\"\n      CD_STORE_ROLE: cd_collector"))
    result = _run(root)
    assert result.returncode == EXIT_VIOLATION, result.stdout
    assert "3: an address literal baked into the deployment" in result.stdout


def test_even_LOOPBACK_is_REFUSED_outside_the_two_positions_that_may_carry_it(tmp_path):
    """*** THE ARM THAT PROVES THE RULE IS ABOUT POSITION AND NOT ABOUT A STRING. ***

    ``127.0.0.1`` is admitted in a ``ports`` entry and in ``x-surface/bind`` — CD-HOLD-005
    keeps those deliberately. The SAME characters in a store host are a host baked in, and
    a check that merely allowlisted the literal would wave this through."""
    root = _subject(tmp_path, ("CD_STORE_HOST: cd-store\n      CD_STORE_PORT: \"5432\"\n      CD_STORE_NAME: \"${CD_STORE_NAME:?CD_STORE_NAME must be set}\"\n      CD_STORE_ROLE: cd_witness",
                               "CD_STORE_HOST: 127.0.0.1\n      CD_STORE_PORT: \"5432\"\n      CD_STORE_NAME: \"${CD_STORE_NAME:?CD_STORE_NAME must be set}\"\n      CD_STORE_ROLE: cd_witness"))
    result = _run(root)
    assert result.returncode == EXIT_VIOLATION, result.stdout
    assert "3: an address literal" in result.stdout


def test_the_ADMITTING_ARM_the_declared_loopback_publication_binds_survive(tmp_path):
    """**RULE 3 IS NOT SATISFIED BY REFUSING EVERY ADDRESS.** ``CD-HOLD-005`` keeps two
    loopback binds and ``CD-D-006`` ruled the public route loopback-only on DEV. If this
    rule refused them the deployment could not publish at all, and the audit would be
    enforcing something nobody decided."""
    result = _run(REPO_ROOT)
    assert result.returncode == EXIT_CLEAN
    compose = (REPO_ROOT / COMPOSE_REL).read_text(encoding="utf-8")
    assert "127.0.0.1:8710:8710" in compose
    assert "127.0.0.1:8711:8711" in compose


# ========================================================================================= #
# RULE 4 — NO ARGUS COUPLING
# ========================================================================================= #

def test_an_argus_reference_in_a_KEY_is_REFUSED(tmp_path):
    root = _subject(tmp_path, ("      CD_STORE_ROLE: cd_engine",
                               "      CD_ARGUS_ENDPOINT: \"${CD_ARGUS_ENDPOINT:?set me}\"\n      CD_STORE_ROLE: cd_engine"))
    result = _run(root)
    assert result.returncode == EXIT_VIOLATION, result.stdout
    assert "4: an ARGUS reference" in result.stdout


def test_an_argus_reference_in_a_VALUE_is_REFUSED_and_case_does_not_save_it(tmp_path):
    root = _subject(tmp_path, ("      CD_STORE_ROLE: cd_review", "      CD_STORE_ROLE: ARGUS_shared_role"))
    result = _run(root)
    assert result.returncode == EXIT_VIOLATION, result.stdout
    assert "4: an ARGUS reference" in result.stdout


# ========================================================================================= #
# RULE 5 — ALL CONFIG VIA ENV
# ========================================================================================= #

def test_a_config_literal_where_an_env_reference_belongs_is_REFUSED(tmp_path):
    root = _subject(
        tmp_path,
        ('      CD_STORE_NAME: "${CD_STORE_NAME:?CD_STORE_NAME must be set}"\n      CD_STORE_ROLE: cd_public',
         '      CD_STORE_NAME: crashdetector_prod\n      CD_STORE_ROLE: cd_public'),
    )
    result = _run(root)
    assert result.returncode == EXIT_VIOLATION, result.stdout
    assert "5: a config literal where an env reference belongs" in result.stdout


def test_a_brand_new_undeclared_literal_is_REFUSED_by_DEFAULT(tmp_path):
    """The allowlist DENIES by default. A key nobody has thought of fails, which is the
    only form of this rule that is not a game of listing the mistakes already made."""
    root = _subject(tmp_path, ("      CD_STORE_ROLE: cd_collector", "      CD_UPSTREAM_FEED: dell-lab-feed-01\n      CD_STORE_ROLE: cd_collector"))
    result = _run(root)
    assert result.returncode == EXIT_VIOLATION, result.stdout
    assert "5: a config literal" in result.stdout


def test_the_ADMITTING_ARM_a_new_env_REFERENCE_is_accepted(tmp_path):
    """**RULE 5 IS NOT SATISFIED BY REFUSING EVERY NEW VARIABLE.** The same new key, given
    as a ``${}`` reference, is admitted — so what the rule tests is the FORM of the value
    and not the novelty of the key."""
    root = _subject(tmp_path, ("      CD_STORE_ROLE: cd_collector", "      CD_UPSTREAM_FEED: \"${CD_UPSTREAM_FEED:?set me}\"\n      CD_STORE_ROLE: cd_collector"))
    assert _run(root).returncode == EXIT_CLEAN


def test_the_ADMITTING_ARM_declared_container_internal_constants_survive(tmp_path):
    """``TZ: UTC`` and ``PYTHONPATH: /app/src`` are literals and must stay literals: they
    are inside the image and cannot differ between the dell and the cloud. A rule that
    refused them would be demanding that the deployment parameterise its own filesystem."""
    result = _run(REPO_ROOT)
    assert result.returncode == EXIT_CLEAN
    compose = (REPO_ROOT / COMPOSE_REL).read_text(encoding="utf-8")
    assert "TZ: UTC" in compose
    assert "PYTHONPATH: /app/src" in compose


# ========================================================================================= #
# RULE 6 — SECRETS BY NAME, NEVER BY VALUE (PBG-SEC-002, NON-WAIVABLE)
# ========================================================================================= #

def test_a_secret_bearing_key_carrying_a_LITERAL_is_REFUSED(tmp_path):
    root = _subject(
        tmp_path,
        ('      CD_STORE_COLLECTOR_PASSWORD: "${CD_STORE_COLLECTOR_PASSWORD:?CD_STORE_COLLECTOR_PASSWORD must be set}"',
         '      CD_STORE_COLLECTOR_PASSWORD: NOT-A-REAL-SECRET-PLANTED-BY-A-TEST'),
    )
    result = _run(root)
    assert result.returncode == EXIT_VIOLATION, result.stdout
    assert "6: a secret-looking value rather than a name" in result.stdout


def test_the_refusal_does_NOT_reproduce_the_offending_value(tmp_path):
    """*** ``PBG-SEC-002`` IS NON-WAIVABLE AND A REFUSAL IS A GOVERNED ARTEFACT. ***

    A check that reports ``password 'hunter2' is a literal`` has published the secret into
    every CI log that ever runs it. The finding names the POINTER and never the value.
    """
    planted = "NOT-A-REAL-SECRET-PLANTED-BY-A-TEST"
    root = _subject(
        tmp_path,
        ('      CD_STORE_COLLECTOR_PASSWORD: "${CD_STORE_COLLECTOR_PASSWORD:?CD_STORE_COLLECTOR_PASSWORD must be set}"',
         f'      CD_STORE_COLLECTOR_PASSWORD: {planted}'),
    )
    result = _run(root)
    assert result.returncode == EXIT_VIOLATION
    assert planted not in result.stdout + result.stderr


def test_the_ADMITTING_ARM_a_secret_given_as_an_env_var_NAME_is_accepted():
    """Every ``*_PASSWORD`` in the real file is a ``${NAME:?…}`` reference, and the clean
    arm admits all of them. Rule 6 refuses the VALUE, never the reference."""
    assert _run(REPO_ROOT).returncode == EXIT_CLEAN
    compose = (REPO_ROOT / COMPOSE_REL).read_text(encoding="utf-8")
    assert '"${CD_STORE_COLLECTOR_PASSWORD:?CD_STORE_COLLECTOR_PASSWORD must be set}"' in compose


# ========================================================================================= #
# *** THE ANTI-VACUITY ARM. THE ONE THAT WOULD HAVE MADE ALL OF THE ABOVE MEANINGLESS. ***
# ========================================================================================= #

def test_the_check_REFUSES_rather_than_passes_when_merge_keys_cannot_be_resolved(tmp_path):
    """``_yamlmin`` records ``<<: *anchor`` UNRESOLVED. Measured on the real file, that
    leaves every one of the six service bind mounts as the mapping ``{'<<': ...}`` —
    **no source, no target, nothing to judge.** A check that walked that tree would examine
    six field-less mounts, find nothing wrong, and print a confident PASS.

    So resolution is a PRECONDITION with its own arm: break the anchor and the check must
    exit NON-ZERO with a stated reason (``PBG-CI-002``), never 0 and never a skip.
    """
    root = _subject(tmp_path, ("x-cd-contracts-mount: &cd-contracts-mount",
                               "x-cd-contracts-mount: &cd-contracts-mount-renamed"))
    result = _run(root)
    assert result.returncode == EXIT_PRECONDITION, result.stdout + result.stderr
    assert "PRECONDITION_NOT_MET" in result.stderr
    assert "names no anchor" in result.stderr


def test_the_resolved_document_actually_carries_the_mount_fields():
    """The positive half of the same proposition, asserted on the real file: after
    resolution the contracts mount HAS a source and a target. Without this, the arm above
    proves only that a broken anchor is detected, not that a working one is used."""
    sys.path.insert(0, str(REPO_ROOT / "deploy"))
    sys.path.insert(0, str(REPO_ROOT / "tools" / "register"))
    from check_portability import _resolve_merges, anchor_table
    from _yamlmin import load_yaml

    path = REPO_ROOT / COMPOSE_REL
    raw = load_yaml(path)
    unresolved = raw["services"]["cd-engine"]["volumes"][0]
    assert set(unresolved) == {"<<"}, unresolved  # THE VACUOUS STATE, reproduced

    document = _resolve_merges(raw, raw, anchor_table(path.read_text(encoding="utf-8")))
    mount = document["services"]["cd-engine"]["volumes"][0]
    assert mount["type"] == "bind"
    assert mount["source"] == "../contracts"
    assert mount["target"] == "/contracts"
    assert mount["read_only"] == "true"


# ========================================================================================= #
# THE THING THE AUDIT DELIBERATELY DOES NOT CLAIM
# ========================================================================================= #

def test_there_is_no_redis_SERVICE_and_this_records_that_as_OPEN_not_as_DONE():
    """*** ``PO-DECISIONS-0025`` RULING 2 NAMES REDIS. THIS DESIGN HAS NONE. ***

    ``BLUEPRINT`` §2's container set does not contain it; it has no declared purpose, no role
    in the grant matrix and no egress posture. **This test asserts the ABSENCE as the measured
    current state so the gap lives in the suite and not only in a Build Log** — it is NOT an
    assertion that the absence is correct. Adding a service to ``BLUEPRINT`` §2 is a Product
    Owner act (``CD-D-115``). Raised as ``Q31``. When Redis is ruled on this test fails, and
    whoever adds the service has to say so here.

    **IT LOOKS FOR A SERVICE AND A CLIENT, NOT FOR THE WORD.** The first draft of this test
    grepped for the string and failed on ``deploy/indicator-mapping.json`` — the file whose
    header RECORDS that Redis is owed under ``Q31``. A test that cannot tell a dependency from
    the documentation of its absence would punish exactly the disclosure this project wants,
    and the fix is to name what a Redis actually IS: a service, an image, a client import, a
    URL scheme, or its port.
    """
    document = _load_compose_resolved()
    services = document["services"]
    assert not [name for name in services if "redis" in name.lower()], sorted(services)
    for name, spec in services.items():
        assert "redis" not in str(spec.get("image") or "").lower(), name

    signatures = ("import redis", "from redis", "redis://", "rediss://", "6379")
    hits = []
    for relative in ("src", "deploy", "db", "contracts"):
        for path in (REPO_ROOT / relative).rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8").lower()
            except (UnicodeDecodeError, OSError):
                continue
            for signature in signatures:
                if signature in text:
                    hits.append(f"{path.relative_to(REPO_ROOT)}: {signature!r}")
    assert hits == [], (
        "a Redis CLIENT, URL or port has appeared in the tree. PO-DECISIONS-0025 r2 names "
        f"Redis and BLUEPRINT §2 does not declare it, so this is Q31 arriving: {hits}"
    )


def test_the_absence_of_redis_is_DOCUMENTED_and_not_merely_true():
    """**THE OTHER HALF, AND THE ONE A SILENT OMISSION WOULD FAIL.**

    The dispatch was explicit that Redis must be neither added nor QUIETLY OMITTED. An
    absence nobody wrote down is indistinguishable from an absence nobody noticed, so this
    asserts that the gap is stated where a reader will meet it.
    """
    audit = (REPO_ROOT / "deploy" / "check_portability.py").read_text(encoding="utf-8")
    assert "Q31" in audit and "REDIS" in audit.upper()
    mapping = (REPO_ROOT / "deploy" / "indicator-mapping.json").read_text(encoding="utf-8")
    assert "Q31" in mapping
