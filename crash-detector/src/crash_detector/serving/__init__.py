"""The serving layer — where the two pipelines meet, and only there (BLUEPRINT §6, §8).

``cd-public`` and ``cd-private`` **serve**: they read rows and render them. They compute no
dial value, hold no evaluation code, and will hold no grant that would let them.

"Side-by-side" in the PID is literal: the public response is assembled here from two rows
written by two different roles from two different pipelines. Nothing merges them upstream,
because no component holds the grants to.

WO-2 delivers :mod:`crash_detector.serving.witness_resolver` — the absence and staleness
mapping for CD-AC-005. The envelope serving path and the dial rendering resolver land in
WO-3 with the publication layer.
"""

__all__: list[str] = []
