"""Structured validation findings, and the safe accessors that produce them.

WHY THIS MODULE EXISTS. Two findings in this cycle are the same defect wearing different clothes.

    independent Assurance finding N4   `manifest.get("project", {}).get(...)` raised AttributeError on a scalar `project`
              key. A raw traceback, exit 1, no governed diagnosis. The `or {}` idiom that appears
              throughout the package guards against None and NOT against a string, a list or an int
              — `"hello" or {}` is `"hello"`, and the next `.get` explodes.

    an independent auditor-A1   an evidence artefact was trusted after `parse_strict` alone. Parsing proves the bytes
              are YAML. It proves nothing about whether the required fields are present, and a
              missing field was read as an absent objection — which is the same shape as F13.

A try/except at the crash site repairs the instance and leaves the class. That pattern is the one
this cycle has now met four times, so the answer here is a SHARED mechanism: one finding type, one
set of accessors that cannot raise, and one schema-driven validator. Every caller that reaches into
governed configuration or governed evidence goes through it.

A structured finding is not a string. It carries the stage that produced it, a stable machine code,
the exact file, the exact field and a human sentence — because "which check refused, and what
exactly did it look at" is the question every one of these findings has to answer.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

# --- stages, in the order a governed artefact must survive them ---------------------------------- #

PATH_CONTAINMENT = "PATH_CONTAINMENT"
PARSE = "PARSE"
SCHEMA = "SCHEMA"
REQUIRED_FIELD = "REQUIRED_FIELD"
ROLE_PATH = "ROLE_PATH"
SCOPE = "SCOPE"
#: independent Assurance finding U3-1. Scope compared an artefact against what the CALLER expected. This stage compares it
#: against what an AUTHORITY RECORD actually grants — does this record exist, is it usable as
#: evidence, does it grant this seat, this work item, this candidate, and in that order.
AUTHORITY = "AUTHORITY"
#: independent Assurance finding U3-2. Content is a claim; the commit that introduced it is evidence. This stage runs last of
#: the artefact gates because it is the only one that reads anything outside the artefact and the
#: records — it reads the repository's own history.
PROVENANCE = "PROVENANCE"
CONFLICT = "CONFLICT"
STRUCTURE = "STRUCTURE"

#: The ordered gate sequence. Stated once, so the ordering is a declared contract rather than the
#: incidental order somebody happened to write the `if`s in.
#:
#: independent Assurance finding U3-1 was exactly a gap in this sequence: the declared contract named an authority and
#: work-item scope stage that the implementer path never ran. AUTHORITY and PROVENANCE are named
#: here so that a stage which exists in the contract and not in the code is a visible discrepancy
#: rather than an invisible one.
STAGES = (PATH_CONTAINMENT, PARSE, SCHEMA, REQUIRED_FIELD, ROLE_PATH, SCOPE, AUTHORITY,
          PROVENANCE, CONFLICT)


@dataclass(frozen=True)
class ValidationFinding:
    """One reason an artefact or a configuration structure may not be used as it stands."""
    stage: str
    code: str
    path: str
    detail: str
    field: str | None = None

    def render(self) -> str:
        where = f"{self.path}" + (f" [{self.field}]" if self.field else "")
        return f"[{self.stage}/{self.code}] {where}: {self.detail}"

    def as_dict(self) -> dict:
        return {"stage": self.stage, "code": self.code, "path": self.path,
                "field": self.field, "detail": self.detail}


# --- accessors that cannot raise ------------------------------------------------------------------ #

def _type_name(value) -> str:
    return type(value).__name__


def mapping_at(container, key: str, *, path: str, field: str | None = None
               ) -> tuple[dict, list[ValidationFinding]]:
    """`container[key]` as a mapping, or an empty mapping and a governed finding.

    Never raises. A value that is ABSENT is not a defect — a manifest need not declare every block.
    A value that is PRESENT and is not a mapping is a defect, because the project wrote something
    there and it cannot mean what the schema says it means.
    """
    field = field or key
    if not isinstance(container, dict):
        return {}, [ValidationFinding(
            STRUCTURE, "CONTAINER_NOT_A_MAPPING", path, field=field,
            detail=(f"expected a mapping to read {field!r} from, found {_type_name(container)}"))]
    if key not in container or container[key] is None:
        return {}, []
    value = container[key]
    if isinstance(value, dict):
        return value, []
    return {}, [ValidationFinding(
        STRUCTURE, "NOT_A_MAPPING", path, field=field,
        detail=(f"{field} must be a mapping of settings; found {_type_name(value)} "
                f"({str(value)[:60]!r}). The value is refused rather than guessed at, and nothing "
                "downstream reads it"))]


def sequence_at(container, key: str, *, path: str, field: str | None = None
                ) -> tuple[list, list[ValidationFinding]]:
    """`container[key]` as a sequence, or an empty list and a governed finding.

    A string is deliberately NOT accepted as a sequence. Iterating a string yields characters, which
    is the kind of silent nonsense that produces a confident wrong answer rather than an error.
    """
    field = field or key
    if not isinstance(container, dict):
        return [], [ValidationFinding(
            STRUCTURE, "CONTAINER_NOT_A_MAPPING", path, field=field,
            detail=(f"expected a mapping to read {field!r} from, found {_type_name(container)}"))]
    if key not in container or container[key] is None:
        return [], []
    value = container[key]
    if isinstance(value, (list, tuple)):
        return list(value), []
    return [], [ValidationFinding(
        STRUCTURE, "NOT_A_SEQUENCE", path, field=field,
        detail=(f"{field} must be a list; found {_type_name(value)} ({str(value)[:60]!r}). A string "
                "is not accepted as a list — iterating one yields characters, which fails silently "
                "rather than loudly"))]


def scalar_at(container, key: str, *, path: str, field: str | None = None
              ) -> tuple[object, list[ValidationFinding]]:
    """`container[key]` as a scalar, or None and a governed finding if it is a container."""
    field = field or key
    if not isinstance(container, dict):
        return None, [ValidationFinding(
            STRUCTURE, "CONTAINER_NOT_A_MAPPING", path, field=field,
            detail=f"expected a mapping to read {field!r} from, found {_type_name(container)}")]
    value = container.get(key)
    if isinstance(value, (dict, list, tuple)):
        return None, [ValidationFinding(
            STRUCTURE, "NOT_A_SCALAR", path, field=field,
            detail=f"{field} must be a single value; found {_type_name(value)}")]
    return value, []


def root_must_be_mapping(document, *, path: str) -> list[ValidationFinding]:
    """The whole document is a mapping, or it is not usable at all.

    A YAML file whose top level is a string or a list parses perfectly and means nothing to a reader
    expecting configuration blocks. That is where the N4 traceback actually began.
    """
    if isinstance(document, dict):
        return []
    if document is None:
        return []                                          # empty declares nothing; not a defect
    return [ValidationFinding(
        STRUCTURE, "ROOT_NOT_A_MAPPING", path,
        detail=(f"the document parsed as {_type_name(document)}, not a mapping of configuration "
                "blocks. Refused as a whole rather than read field by field"))]


def mappings_at(container, key: str, *, path: str, field: str | None = None
                ) -> tuple[list[dict], list[ValidationFinding]]:
    """`container[key]` as a list of MAPPINGS, or nothing usable and a governed finding.

    independent Assurance finding U3-3 is what happens without this. `for record in doc.get("controls", []) or []` survives
    a missing key and a null, and then calls `.get` on whatever the list happens to hold. A list of
    strings iterates perfectly and explodes on the first element with a raw AttributeError that
    names neither the file nor the field.

    NO PARTIAL ACTIVATION. One malformed entry refuses the WHOLE sequence rather than the entry.
    Returning the well-formed neighbours would mean a control corpus that is quietly smaller than
    the file says it is, and a control that silently does not exist is worse than one that loudly
    cannot be read.
    """
    field = field or key
    values, findings = sequence_at(container, key, path=path, field=field)
    if findings:
        return [], findings
    bad = [(index, item) for index, item in enumerate(values) if not isinstance(item, dict)]
    if bad:
        return [], [ValidationFinding(
            STRUCTURE, "ITEM_NOT_A_MAPPING", path, field=f"{field}[{index}]",
            detail=(f"{field}[{index}] must be a mapping of fields; found {_type_name(item)} "
                    f"({str(item)[:60]!r}). The whole {field} sequence is refused rather than "
                    "partially activated — a record that silently does not exist is worse than one "
                    "that loudly cannot be read"))
            for index, item in bad]
    return list(values), []


# --- the one typed reader every governed-document loader shares ------------------------------------ #

def contained_path(path: Path, root: Path, *, path_label: str | None = None
                   ) -> tuple[Path | None, list[ValidationFinding]]:
    """Where the path LANDS, or a finding saying it lands outside the tree that governs it.

    Judged on the resolved location rather than the spelling, because a symlink out of the tree and
    an honest relative path look identical until they are resolved. The same rule `read_sources`
    applies to evidence, applied to configuration.
    """
    path, root = Path(path), Path(root)
    label = path_label or str(path)
    try:
        real = path.resolve()
        real.relative_to(root.resolve())
    except (ValueError, OSError):
        return None, [ValidationFinding(
            PATH_CONTAINMENT, "OUTSIDE_ROOT", label,
            detail=(f"resolves to {path.resolve() if path.exists() else path}, outside the root "
                    f"{root.resolve()}. A document outside the tree it governs is not that tree's "
                    "configuration, and it is refused rather than read"))]
    return real, []


def load_governed_document(path: Path, *, root: Path | None = None, path_label: str | None = None
                           ) -> tuple[object, list[ValidationFinding]]:
    """Read one governed YAML document: contained, strictly parsed, and never raising.

    THE ONE SHARED LAYER. independent Assurance finding U3-3's instruction is explicit that patching the crash site repairs
    the instance and leaves the class, so every reader of an externally supplied YAML or JSON
    document routes through here. It returns the parsed value AND the reasons it may not be used;
    it does not decide what type the caller wanted, because different callers want different types
    and only the caller knows which.

    Strict parsing matters as much as typing: PyYAML keeps the last value for a duplicate key, so a
    control file can declare one control twice and a reader only ever sees one of them.
    """
    from . import continuity                                  # local: continuity has no view of us

    path = Path(path)
    label = path_label or str(path)
    if root is not None:
        real, findings = contained_path(path, root, path_label=label)
        if findings:
            return None, findings
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return None, [ValidationFinding(
            PARSE, "UNREADABLE", label,
            detail=f"cannot be read: {exc}. An unreadable governed document is refused, not skipped")]
    try:
        return yaml.load(text, Loader=continuity.StrictLoader), []
    except continuity.ContinuityError as exc:
        return None, [ValidationFinding(
            PARSE, "DUPLICATE_KEY", label,
            detail=(f"{exc}. A duplicate key silently keeps the last value, so the document says "
                    "two things and a reader sees one"))]
    except yaml.YAMLError as exc:
        return None, [ValidationFinding(
            PARSE, "MALFORMED_YAML", label,
            detail=f"is not valid YAML: {str(exc).splitlines()[0] if str(exc) else exc}")]


def load_governed_mapping(path: Path, *, root: Path | None = None, path_label: str | None = None
                          ) -> tuple[dict, list[ValidationFinding]]:
    """`load_governed_document`, narrowed to the mapping every configuration reader assumes.

    A document whose top level is a scalar or a list is refused AS A WHOLE. That is where the
    independent Assurance finding U3-3 traceback actually began: `doc.get("domain")` on a `str`, with no file named, no
    field named, no expected type, no observed type and no governed exit.
    """
    document, findings = load_governed_document(path, root=root, path_label=path_label)
    if findings:
        return {}, findings
    label = path_label or str(path)
    structural = root_must_be_mapping(document, path=label)
    if structural:
        return {}, structural
    return (document if isinstance(document, dict) else {}), []


# --- schema-driven validation --------------------------------------------------------------------- #

def load_schema(schema_path: Path) -> tuple[dict | None, list[ValidationFinding]]:
    """Read a governed schema. A schema that cannot be read FAILS CLOSED for its callers."""
    schema_path = Path(schema_path)
    rel = str(schema_path)
    if not schema_path.is_file():
        return None, [ValidationFinding(
            SCHEMA, "SCHEMA_MISSING", rel,
            detail=("the governed schema is absent, so no artefact can be schema-validated against "
                    "it. Nothing is admitted on the strength of a schema that is not there"))]
    try:
        doc = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError) as exc:
        return None, [ValidationFinding(
            SCHEMA, "SCHEMA_UNREADABLE", rel, detail=f"the governed schema cannot be read: {exc}")]
    if not isinstance(doc, dict):
        return None, [ValidationFinding(
            SCHEMA, "SCHEMA_MALFORMED", rel,
            detail=f"the governed schema parsed as {_type_name(doc)}, not a mapping")]
    return doc, []


def validate_against_schema(document: dict, schema: dict, *, path: str) -> list[ValidationFinding]:
    """Validate a document against a governed schema, reading the SCHEMA for what is required.

    Deliberately schema-DRIVEN rather than a hand-maintained field list. independent Assurance finding A1-R1 is exactly what
    happens when the schema says a field is required and the code that decides trust keeps its own
    opinion: the two drift, and the drift is the vulnerability. The required fields, enums and consts
    below are read out of the schema file at call time, so there is one statement of the contract.

    `jsonschema` is used when it is importable, for full coverage. It is NOT depended upon: a
    non-waivable control that silently weakens when an optional package is absent would be the same
    defect class again. The native checks below always run and always cover the fields that decide
    trust — presence, emptiness, enum membership and const.
    """
    findings: list[ValidationFinding] = []
    if not isinstance(document, dict):
        return root_must_be_mapping(document, path=path)

    properties = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}

    for name in schema.get("required") or []:
        name = str(name)
        if name not in document:
            findings.append(ValidationFinding(
                REQUIRED_FIELD, "MISSING_REQUIRED_FIELD", path, field=name,
                detail=(f"the governed schema requires {name!r} and the artefact omits it. A missing "
                        "field is not an absent objection — the artefact is EXCLUDED rather than "
                        "treated as unbounded")))
            continue
        value = document.get(name)
        if value is None or (isinstance(value, str) and not value.strip()):
            findings.append(ValidationFinding(
                REQUIRED_FIELD, "EMPTY_REQUIRED_FIELD", path, field=name,
                detail=(f"{name} is required and is present but empty. An explicit null or blank is "
                        "the absence of a value written down, not a value")))

    for name, spec in properties.items():
        if not isinstance(spec, dict) or name not in document:
            continue
        value = document.get(name)
        if value is None:
            continue
        if "const" in spec and value != spec["const"]:
            findings.append(ValidationFinding(
                SCHEMA, "CONST_MISMATCH", path, field=name,
                detail=f"{name} must be {spec['const']!r}; found {value!r}"))
        enum = spec.get("enum")
        if isinstance(enum, list) and value not in enum:
            findings.append(ValidationFinding(
                SCHEMA, "ENUM_VIOLATION", path, field=name,
                detail=(f"{name} must be one of {sorted(str(e) for e in enum)}; found {value!r}. An "
                        "unrecognised value is refused, never treated as unconstrained")))
        expected_type = spec.get("type")
        if expected_type and not _type_ok(value, expected_type):
            findings.append(ValidationFinding(
                SCHEMA, "TYPE_MISMATCH", path, field=name,
                detail=f"{name} must be {expected_type}; found {_type_name(value)}"))

    try:                                                   # pragma: no cover - optional dependency
        import jsonschema
    except ImportError:
        return findings

    stated = {f.field for f in findings if f.stage in (SCHEMA, REQUIRED_FIELD)}
    validator = jsonschema.Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(document), key=lambda e: list(e.path)):
        field = ".".join(str(p) for p in error.path) or None
        # A missing required property reports an EMPTY path, so matching on `field` alone would let
        # it through beside the native finding that already said the same thing. Two findings for
        # one defect dilute the report, and a diluted report is how a real finding gets skimmed past.
        if field is None and error.validator == "required":
            missing = str(error.message).split("'")[1::2]
            if missing and all(name in stated for name in missing):
                continue
        if field in stated:
            continue                                       # already stated natively; do not double
        findings.append(ValidationFinding(SCHEMA, "JSONSCHEMA", path, field=field,
                                          detail=error.message))
    return findings


def _type_ok(value, expected) -> bool:
    types = expected if isinstance(expected, list) else [expected]
    for name in types:
        if name == "string" and isinstance(value, str):
            return True
        if name == "integer" and isinstance(value, int) and not isinstance(value, bool):
            return True
        if name == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
            return True
        if name == "boolean" and isinstance(value, bool):
            return True
        if name == "object" and isinstance(value, dict):
            return True
        if name == "array" and isinstance(value, (list, tuple)):
            return True
        if name == "null" and value is None:
            return True
    return False


def render_findings(findings, *, indent: str = "  ") -> str:
    """One human-readable block. Used by every surface, so reports cannot drift apart."""
    return "\n".join(f"{indent}- {f.render()}" for f in findings)
