"""Publication contracts — the refusal path (BLUEPRINT §3, §8; deliverable A7).

WO-2 delivers the two closed envelope contracts and the function that refuses a candidate
against them. **It does not deliver the publication layer**: building envelopes, writing
``publication.public_envelope``, raising the ``alert.event`` row on a refusal and serving
any of it are WO-3. The guard lands first, because a doctrine-bearing structure that
arrives after the feature it guards has already been retrofitted (BLUEPRINT §13).

Nothing in this package writes, serves, binds a port or opens a socket. It reads two JSON
files from ``contracts/`` and raises.

This package deliberately imports nothing from :mod:`crash_detector.witness`, so wiring it
into :mod:`crash_detector.engine` in WO-3 cannot introduce an engine-to-witness edge by
the back door (CD-AC-003).
"""

from crash_detector.publication.classification import (
    BOOK_ADJACENT_TOKENS,
    CLASSIFICATION_BOOK_ADJACENT,
    CLASSIFICATION_SECRET_BEARING,
    SECRET_BEARING_TOKENS,
    classify_key,
    iter_keys,
    key_tokens,
)
from crash_detector.publication.dial_scalar import (
    PUBLISHABLE_DIAL_SLOTS,
    DialProvenanceRefused,
    number_for_dial_slot,
)
from crash_detector.publication.envelope_contract import (
    CONTRACTS_DIR_ENV_VAR,
    ENVELOPE_SCHEMA_VERSION,
    REFUSAL_NON_FINITE_NUMBER,
    REFUSAL_NON_JSON_VALUE,
    REFUSAL_NOT_A_JSON_OBJECT,
    REFUSAL_PRIVATE_CLASSIFIED_KEY,
    REFUSAL_SCHEMA_VIOLATION,
    REFUSAL_SECRET_BEARING_KEY,
    REFUSAL_UNKNOWN_KEY,
    ContractUnavailable,
    EnvelopeSurface,
    PublicationRefused,
    contracts_dir,
    load_envelope_schema,
    refuse_unless_publishable,
    schema_path_for,
)

__all__ = [
    "BOOK_ADJACENT_TOKENS",
    "CLASSIFICATION_BOOK_ADJACENT",
    "CLASSIFICATION_SECRET_BEARING",
    "CONTRACTS_DIR_ENV_VAR",
    "ContractUnavailable",
    "DialProvenanceRefused",
    "ENVELOPE_SCHEMA_VERSION",
    "EnvelopeSurface",
    "PUBLISHABLE_DIAL_SLOTS",
    "PublicationRefused",
    "REFUSAL_NON_FINITE_NUMBER",
    "REFUSAL_NON_JSON_VALUE",
    "REFUSAL_NOT_A_JSON_OBJECT",
    "REFUSAL_PRIVATE_CLASSIFIED_KEY",
    "REFUSAL_SCHEMA_VIOLATION",
    "REFUSAL_SECRET_BEARING_KEY",
    "REFUSAL_UNKNOWN_KEY",
    "SECRET_BEARING_TOKENS",
    "classify_key",
    "contracts_dir",
    "iter_keys",
    "key_tokens",
    "load_envelope_schema",
    "number_for_dial_slot",
    "refuse_unless_publishable",
    "schema_path_for",
]
