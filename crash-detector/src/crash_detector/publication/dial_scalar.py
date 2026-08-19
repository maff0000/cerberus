"""The publication gate for a dial magnitude (CD-AC-002, closing CD-ASR-F01).

    number_for_dial_slot(slot, magnitude) -> float

**THE ONE PLACE a dial magnitude becomes a number that may be published**, and the place
where "exactly one dial" stops being a property of the code and becomes a comparison of
data.

----

WHY THIS EXISTS AS WELL AS THE CLOSED SCHEMA.

CD-AC-002 has two structural refusals on the public surface and they are independent:

1. **the closed envelope schema** (``contracts/public_envelope.schema.json``,
   CD-RT-002-SCHEMA-CLOSED). ``additionalProperties`` is ``false`` at every level and
   ``properties`` is an allowlist, so a third combined key — ``combined_stress``,
   ``overall``, ``blended_score``, anything — has nowhere to be written. An independent
   auditor tested this mitigation specifically and confirmed **it holds**: neither of the
   two working blends could reach the published artefact through the validated envelope
   without also failing this check (`CD-ASR-F01`, ``mitigation_that_does_hold``).

   Its LIMIT is stated in the schema's own description and is real: it constrains the
   SHAPE of what is published, so it cannot see a blended number assigned to
   ``equity_crash.score``, because that key is legitimately a number.

2. **this gate**, which closes exactly that limit. A number reaches a dial slot only by
   being released from a :class:`~crash_detector.dials.magnitude.DialMagnitude` whose
   provenance is **exactly the dial of the slot it is being written into**. A blend has no
   such provenance — it cannot have one, because a magnitude's provenance is always
   exactly one dial by construction and there is no combinator that unions two — so a
   blend cannot be OFFERED to the envelope, never mind accepted by it.

Neither layer is sole (BLUEPRINT §17, risk CD-BP-001, PO-accepted). The register entry for
CD-AC-002 no longer claims that a violation slipping past one layer must fail the others:
that claim was refuted by execution and its replacement says only what each layer does.

----

WHAT THIS DELIVERS IN WO-2, AND WHAT IT DOES NOT.

The publication LAYER — building envelopes, writing ``publication.public_envelope``,
serving any of it — is WO-3, exactly as for the rest of this package. What lands here is
the gate, written and tested now because the guard has to exist before the thing it guards
(BLUEPRINT §13). Nothing here writes, serves, binds a port or opens a socket.

**FOR THE WO-3 ENVELOPE BUILDER, IN TERMS:** a dial reading's ``score`` is obtained by
calling :func:`number_for_dial_slot` with the envelope key it is going into. It is not
obtained by reading a number off anything. If a future builder assigns a bare number to a
dial slot without coming through here, this gate is not what stops it — the schema is, and
the schema cannot tell one number from another. That residue is stated in the declared
limit of ``tools/register/check_no_blend.py`` and in the register, and it is the reason
this gate is written as the ONLY route rather than as a validator that runs afterwards.
"""

from __future__ import annotations

from crash_detector.dials.dialset import DIAL_IDS
from crash_detector.dials.magnitude import (
    CrossDialCombination,
    DialMagnitude,
    sole_dial_of,
)

__all__ = [
    "PUBLISHABLE_DIAL_SLOTS",
    "DialProvenanceRefused",
    "number_for_dial_slot",
]

#: The envelope keys a dial magnitude may be published into. It IS ``DIAL_IDS`` — the
#: public envelope's dial keys are the dial ids — bound to a name of its own here so that
#: a reader of this module can see that the set is derived from the dial vocabulary and
#: not from a list typed out beside the schema. Two. A third is a PID amendment.
PUBLISHABLE_DIAL_SLOTS: tuple = DIAL_IDS


class DialProvenanceRefused(CrossDialCombination):
    """A number was offered for publication whose provenance is not exactly one dial.

    A subclass of :exc:`~crash_detector.dials.magnitude.CrossDialCombination`, and
    therefore of ``TypeError``, so that a caller catching the cross-dial refusal catches
    it here too and cannot come to treat the publication boundary as the lenient one.
    """


def number_for_dial_slot(slot: str, magnitude: "DialMagnitude") -> float:
    """The bare number for ONE dial slot of the public envelope, or a refusal.

    Refuses, in this order and each for its own reason:

    * a slot that is not one of the declared dial slots. Deny by default: a magnitude
      published under a key nobody declared is a combined figure by another name, and the
      guard does not need to recognise the key to refuse it;
    * anything that is not exactly a :class:`DialMagnitude` — a bare ``float`` most of
      all. A bare number arriving here has already lost its provenance, and a number
      whose dial is in doubt has lost the property that makes it worth publishing;
    * a magnitude whose provenance is not exactly one dial;
    * a magnitude whose one dial is not the dial of this slot.

    The last two are the whole of the "unpublishable" half of CD-AC-002's closure, and
    they are a comparison of DATA. They do not read the expression that produced the
    magnitude, so they hold however it was reached: through an attribute, a ``getattr``
    over string slots, a dict, a comprehension, a helper several calls away, a value
    round-tripped through JSON, or a route nobody has thought of.
    """
    if slot not in PUBLISHABLE_DIAL_SLOTS:
        raise DialProvenanceRefused(
            f"{slot!r} is not a publishable dial slot. The declared slots are "
            f"{list(PUBLISHABLE_DIAL_SLOTS)}, and PID §3.1 admits no third figure "
            "derived from both: 'Two dials, never blended.'"
        )
    try:
        dial_id = sole_dial_of(magnitude)
    except CrossDialCombination as refusal:
        # Re-raised as this boundary's own exception, so that everything this gate
        # refuses answers to one name and a caller cannot come to treat "not a magnitude"
        # and "not one dial" as different kinds of failure. The original refusal, with
        # its reason, is chained.
        raise DialProvenanceRefused(
            f"nothing may be published into the {slot!r} slot without the provenance "
            f"that says it belongs there: {refusal}"
        ) from refusal
    if dial_id != slot:
        raise DialProvenanceRefused(
            f"a magnitude whose provenance is {dial_id!r} was offered for the {slot!r} "
            "slot. The two dials fail in opposite directions, so publishing one dial's "
            "number under the other's key is the same defect as blending them, reached "
            "by a shorter road (CD-AC-002, CD-ASR-F01)."
        )
    return magnitude.quantity_for(slot)
