"""THE DECLARED DISPOSITIONS — what this seat claims about every site the sweep found.

Read ``tools/sweep/delegated_judgement_sweep.py`` first; this file is its data and has no
behaviour of its own.

**A DISPOSITION IS A CLAIM BY THIS SEAT, NOT SOMETHING THE TOOL VERIFIED.** The tool finds
the sites and asserts that every one of them is declared here and that nothing declared here
has stopped existing. It cannot check whether a disposition is TRUE. That is deliberate and
it is stated first, because the failure this project keeps meeting is a clean run being read
as evidence of a proposition the clean run says nothing about. The runtime evidence for
these claims is ``tests/test_own_terms.py`` and the variants under
``variants/WO-2R2/CLASS-2/``. **The thing to attack here is the disposition text.**

THE FIVE DISPOSITIONS
    ESTABLISHED   the operand was re-established by ``crash_detector.own_terms`` before this
                  operation runs, so what executes is CPython's implementation for an exact
                  base type
    EXACT         the check is exact-type identity, or is over class objects of types this
                  package seals against subclassing, so no supplied implementation can be
                  reached through it
    OWN           both operands were constructed by this module in this scope
    DELEGATED     the deciding operation IS executed by an object this system did not
                  construct. OPEN. The note says so and says under whose authority.
    OUT_OF_BOUND  the sweep reached it and it is DECLARED as outside this increment's scope.
                  Declaring is this seat's CD-RULE-004 obligation; closing would be a scope
                  breach.

TWO REGISTERS, AND THEY ARE NOT THE SAME STRENGTH — said plainly rather than left to be
noticed:

  * :data:`DECLARED_ADMISSIONS` is SITE-LEVEL and exhaustive. It is TIER 1 — every
    ``isinstance``, ``issubclass``, ``hasattr`` and ``getattr`` in the subject closure —
    which is what the dispatch asks for in terms.
  * :data:`DECLARED_MODULE_DISPOSITIONS` is MODULE-LEVEL. It covers TIER 2, the deciding
    operations themselves, which number in the hundreds. A module-level claim is WEAKER
    than a per-site one: it says how operands are established in that module, and a single
    site inside a module can contradict it without this file noticing. It is recorded at
    this granularity because a per-site register of 369 entries would be a register nobody
    reads, and an unread register is a worse instrument than an honest coarse one. THE
    WEAKNESS IS THE LIMIT, and it is repeated in the tool's declared limit.

SITE KEYS. A site is ``(module, enclosing qualname, category, normalised expression)``.
Two textually identical sites in one function collapse to one key, so this register declares
the EXPRESSION rather than each occurrence of it. That is visible in
``SourceRecord.__post_init__``, where ``getattr(self, name)`` appears twice in one loop.
"""

from __future__ import annotations

__all__ = ["DECLARED_ADMISSIONS", "DECLARED_MODULE_DISPOSITIONS"]


# ======================================================================================= #
# TIER 1 — ADMISSION. Every isinstance / issubclass / duck-typed probe in the closure.
# ======================================================================================= #

DECLARED_ADMISSIONS = {
    # --- the door itself ---------------------------------------------------------------- #
    (
        "crash_detector.time_utc",
        "ensure_utc",
        "ISINSTANCE",
        "isinstance(value, datetime)",
    ): (
        "ESTABLISHED",
        "THE SITE THE FINDING IS ABOUT. It is still an isinstance and it still admits a "
        "subclass — pandas.Timestamp IS one and must be readable. What changed is that the "
        "value returned is rebuilt by own_instant from the supplied object's own C-struct "
        "fields, so this test now admits a SHAPE to be read and no longer admits an object "
        "to be consulted. Nothing after this line calls a method of type(value).",
    ),
    (
        "crash_detector.own_terms",
        "own_instant",
        "ISINSTANCE",
        "isinstance(value, datetime)",
    ): (
        "ESTABLISHED",
        "The shape admission inside the door. What follows reads seven ints through "
        "datetime's own getset descriptors and builds a new exact datetime.",
    ),
    (
        "crash_detector.own_terms",
        "own_utc_offset",
        "ISINSTANCE",
        "isinstance(value, datetime)",
    ): ("ESTABLISHED", "As above; the offset is then rebuilt from timedelta's descriptors."),
    (
        "crash_detector.own_terms",
        "own_utc_offset",
        "ISINSTANCE",
        "isinstance(declared, timedelta)",
    ): (
        "ESTABLISHED",
        "CPython's call_utcoffset already refuses a non-timedelta, so this is a named "
        "refusal rather than an assumption about the interpreter. A timedelta SUBCLASS "
        "reaches here — CPython checks by isinstance — and is rebuilt from days/seconds/"
        "microseconds immediately below, so its __rsub__ never runs.",
    ),
    ("crash_detector.own_terms", "own_float", "ISINSTANCE", "isinstance(value, float)"): (
        "ESTABLISHED",
        "Admits float subclasses on purpose — numpy.float64 is one and a measurement path "
        "that refused it would be broken, not safe — and returns float.__float__(value), "
        "which reads ob_fval from the C struct. The subclass's __float__ never runs.",
    ),
    ("crash_detector.own_terms", "own_float", "ISINSTANCE", "isinstance(value, bool)"): (
        "EXACT",
        "bool is refused ahead of the float test, as at every numeric door in this package: "
        "a False that became a zero divergence measure reads as perfect agreement.",
    ),
    ("crash_detector.own_terms", "own_str", "ISINSTANCE", "isinstance(value, str)"): (
        "ESTABLISHED",
        "Admits str subclasses and returns str.__str__(value), which copies the code points. "
        "The subclass's __eq__, __hash__ and __bool__ never run afterwards.",
    ),
    ("crash_detector.own_terms", "<module>", "DUCK", "getattr(datetime, _name)"): (
        "OWN",
        "Binds datetime's own getset descriptors once at import. The attribute names are a "
        "module constant written out in this file; the object probed is the stdlib base "
        "type, never a supplied one. Resolving them here also means the descriptor set "
        "cannot be swapped between the check and the read.",
    ),
    ("crash_detector.time_utc", "parse_utc", "ISINSTANCE", "isinstance(text, str)"): (
        "ESTABLISHED",
        "Followed by own_str: `candidate.endswith('Z')` decides what instant the text "
        "denotes and endswith is the supplied object's to define.",
    ),
    # --- the sealed metaclasses. Class objects, not values. ------------------------------ #
    (
        "crash_detector.dials.reading",
        "SealedReadingType.__new__",
        "ISINSTANCE",
        "isinstance(base, SealedReadingType)",
    ): (
        "EXACT",
        "Asks whether a base class's METACLASS is this one. The instancecheck is type's, "
        "and the operand is a class object produced by the interpreter from a class "
        "statement, not a value a caller constructed. This is what makes the Reading sum "
        "type unsubclassable, which is why fold's exact-type dispatch has nothing to miss.",
    ),
    (
        "crash_detector.dials.magnitude",
        "SealedMagnitudeType.__new__",
        "ISINSTANCE",
        "isinstance(base, SealedMagnitudeType)",
    ): ("EXACT", "As SealedReadingType.__new__."),
    (
        "crash_detector.dials.provenance",
        "SealedQuantityType.__new__",
        "ISINSTANCE",
        "isinstance(base, SealedQuantityType)",
    ): ("EXACT", "As SealedReadingType.__new__."),
    (
        "crash_detector.serving.dial_presentation",
        "SealedPresentationType.__new__",
        "ISINSTANCE",
        "isinstance(base, SealedPresentationType)",
    ): ("EXACT", "As SealedReadingType.__new__."),
    (
        "crash_detector.dials.reading",
        "seal_reading_type",
        "ISINSTANCE",
        "isinstance(cls, SealedReadingType)",
    ): (
        "EXACT",
        "Runs at import over this module's own three constructors, which the loop below "
        "names explicitly from READING_CONSTRUCTORS. No caller reaches it with anything.",
    ),
    # --- the frozen-value constructors --------------------------------------------------- #
    (
        "crash_detector.dials.provenance",
        "_install",
        "ISINSTANCE",
        "isinstance(dials, frozenset)",
    ): (
        "ESTABLISHED",
        "A shape admission only. The set is then REBUILT as frozenset(own_str(one) for one "
        "in dials), and the one-dial count is taken on the rebuilt set — so neither the "
        "supplied set's __len__ nor its elements' __hash__/__eq__ decide whether two dials "
        "count as one. That comparison is the cross-dial refusal itself.",
    ),
    (
        "crash_detector.dials.magnitude",
        "DialMagnitude.__setstate__",
        "ISINSTANCE",
        "isinstance(provenance, frozenset)",
    ): (
        "ESTABLISHED",
        "A pickle is untrusted input like any other. The members are copied into a tuple "
        "this method builds before being counted and indexed, and the id is then "
        "re-established by _install. It used to read len(provenance) != 1 and "
        "sorted(provenance)[0], both of which the supplied object answered.",
    ),
    (
        "crash_detector.engine.config",
        "ConfigSnapshot.__post_init__",
        "ISINSTANCE",
        "isinstance(window, float)",
    ): (
        "ESTABLISHED",
        "CARRIER MEASURED (CD-RULE-006): StalenessWindow(seconds=window) is constructed two "
        "lines below and refuses anything whose type is not exactly float or int — "
        "tests/test_staleness.py::test_a_float_subclass_that_redefines_comparison_is_not_a_"
        "window. So a subclass admitted here cannot become a usable window. The float field "
        "survives because the envelope publishes the window that was applied as a number.",
    ),
    (
        "crash_detector.engine.config",
        "ConfigSnapshot.__post_init__",
        "ISINSTANCE",
        "isinstance(window, bool)",
    ): ("EXACT", "bool refused ahead of the float test, as at every numeric door here."),
    (
        "crash_detector.source_registry",
        "SourceRecord.__post_init__",
        "ISINSTANCE",
        "isinstance(self.criticality, Criticality)",
    ): (
        "EXACT",
        "Criticality is an enum.Enum with members, which CPython refuses to subclass, so "
        "isinstance and exact type coincide here and no supplied implementation exists to "
        "reach. This is the check that makes the DISPOSABLE prohibition mean anything.",
    ),
    (
        "crash_detector.source_registry",
        "SourceRegistry.ids_with",
        "ISINSTANCE",
        "isinstance(criticality, Criticality)",
    ): ("EXACT", "As above — Criticality cannot be subclassed."),
    (
        "crash_detector.source_registry",
        "SourceRecord.__post_init__",
        "ISINSTANCE",
        "isinstance(self.cadence_seconds, int)",
    ): (
        "DELEGATED",
        "OPEN, AND SMALL, AND SAID RATHER THAN GLOSSED. An int SUBCLASS passes, and "
        "`self.cadence_seconds <= 0` immediately below is then its __le__ to answer, so a "
        "subclass could register a non-positive cadence. IT IS NOT ON A DECIDING PATH FOR "
        "THIS CLASS: cadence is the collector's schedule and no staleness, agreement or "
        "reading-ness judgement reads it in WO-2 — the engine's freshness comes from "
        "StalenessWindow and the source's own as_of. It is left open rather than closed "
        "because closing it is a change to the collector contract, which is not this "
        "increment's bound. NOT PROVED TO BE CARRIED ANYWHERE.",
    ),
    (
        "crash_detector.source_registry",
        "SourceRecord.__post_init__",
        "ISINSTANCE",
        "isinstance(self.cadence_seconds, bool)",
    ): ("EXACT", "bool refused ahead of the int test."),
    (
        "crash_detector.observations",
        "FetchFailed.__post_init__",
        "ISINSTANCE",
        "isinstance(status, int)",
    ): (
        "OUT_OF_BOUND",
        "An int subclass passes and is stored as http_status. REACHED BY THE SWEEP AND "
        "DECLARED, NOT CLOSED: FetchFailed is the outcome that says we could not ask, it "
        "carries no payload and no timestamp, and nothing on the staleness, agreement or "
        "reading-ness paths reads http_status — _latest_usable_ok considers only OK. "
        "NOT PROVED TO BE CARRIED ANYWHERE.",
    ),
    (
        "crash_detector.observations",
        "FetchFailed.__post_init__",
        "ISINSTANCE",
        "isinstance(status, bool)",
    ): ("EXACT", "bool refused ahead of the int test."),
    (
        "crash_detector.observations",
        "Malformed.__post_init__",
        "ISINSTANCE",
        "isinstance(self.instance_path, str)",
    ): (
        "OUT_OF_BOUND",
        "A str subclass passes, and `self.instance_path.startswith('/')` and "
        "`len(self.instance_path)` are then its methods to answer, so the RFC 6901 shape "
        "check and the length ceiling are the supplied object's to satisfy. REACHED BY THE "
        "SWEEP AND DECLARED, NOT CLOSED: Malformed is a record ABOUT a rejected response "
        "and carries nothing value-bearing by design, and no staleness, agreement or "
        "reading-ness judgement reads instance_path. The ceiling protects an append-only "
        "store, which is a store concern and a different increment. "
        "NOT PROVED TO BE CARRIED ANYWHERE.",
    ),
    # --- duck-typed reads. All of them read a name this package wrote. -------------------- #
    (
        "crash_detector.dials.dialset",
        "DialSet.__post_init__",
        "DUCK",
        "getattr(self, field_name)",
    ): (
        "OWN",
        "field_name iterates DIAL_FIELDS, a module constant. It is a loop over this type's "
        "own two declared fields written once instead of twice, not a probe of a supplied "
        "object's surface. The VALUE it fetches is caller-supplied and is admitted on the "
        "next line by exact-type membership in READING_CONSTRUCTORS.",
    ),
    (
        "crash_detector.dials.scores",
        "Contribution.__post_init__",
        "DUCK",
        "getattr(self, field_name)",
    ): (
        "ESTABLISHED",
        "field_name iterates a tuple literal in this file. Both loops now RE-ESTABLISH what "
        "they fetch: the labels through own_str and the two numbers through "
        "require_finite_float, which returns the established float rather than approving "
        "the caller's object.",
    ),
    (
        "crash_detector.engine.config",
        "DialSpec.__post_init__",
        "DUCK",
        "getattr(self, field_name)",
    ): (
        "ESTABLISHED",
        "field_name iterates a tuple literal in this file. Both input-id tuples are rebuilt "
        "through own_str before the duplicate and overlap tests, which are set membership "
        "and were the supplied strings' __hash__/__eq__ to answer.",
    ),
    (
        "crash_detector.source_registry",
        "SourceRecord.__post_init__",
        "DUCK",
        "getattr(self, name)",
    ): (
        "ESTABLISHED",
        "name iterates a tuple literal in this file. Each label is rebuilt through own_str "
        "and written back, so the duplicate-detection set in SourceRegistry and the lookup "
        "in get() hash plain strings.",
    ),
    (
        "crash_detector.serving.dial_presentation",
        "_establish_dial_id",
        "DUCK",
        "getattr(presentation, 'dial_id')",
    ): (
        "ESTABLISHED",
        "Reads this package's own declared field by a literal name, on a value whose "
        "constructor is running, and immediately re-establishes it through own_str. It is a "
        "shared helper rather than a member so it does not widen the declared attribute "
        "surface the two presentation constructors assert by set equality at import.",
    ),
}


# ======================================================================================= #
# TIER 2 — THE DECIDING OPERATION, declared at MODULE granularity. Weaker. Labelled so.
# ======================================================================================= #

DECLARED_MODULE_DISPOSITIONS = {
    "crash_detector.own_terms": (
        "OWN",
        "This module IS the door. Every operand it decides anything about is either a "
        "primitive it has just read out of a C struct through a base-type descriptor, or a "
        "value it has just constructed from those primitives.",
    ),
    "crash_detector.time_utc": (
        "ESTABLISHED",
        "Every operand reaches its operation through ensure_utc, including both operands of "
        "the one subtraction (age_seconds). format_utc's endswith runs on the output of "
        "datetime.isoformat on an established value.",
    ),
    "crash_detector.staleness": (
        "ESTABLISHED",
        "StalenessWindow admits its seconds by EXACT TYPE and stores float(declared), and "
        "covers() insists on a plain int or float for the age — which costs no caller "
        "anything now, because age_seconds returns timedelta.total_seconds on an "
        "established timedelta. FreshnessEvidence puts both timestamps through ensure_utc "
        "and requires the window by exact type. UNCHANGED BY THIS INCREMENT except in what "
        "reaches it: this module always judged values, and it is the other operand that was "
        "open.",
    ),
    "crash_detector.witness.panel": (
        "ESTABLISHED",
        "The three constructors re-establish every field before judging it: timestamps "
        "through ensure_utc, measurements through _own_finite_float, and Unavailable.reason "
        "through own_str before `not in UNAVAILABLE_REASONS`. Agrees requires "
        "FreshnessEvidence by exact type, and panel_state dispatches on exact type.",
    ),
    "crash_detector.serving.witness_resolver": (
        "ESTABLISHED",
        "PanelRow re-establishes state, every measures key and both timestamps. The age is "
        "computed by age_seconds from established operands; `row.state == _STATE_AGREES` "
        "compares two plain strings; _finite_measure returns a plain float; render_panel "
        "dispatches on exact type through a dict keyed by class objects of types built in "
        "this package.",
    ),
    "crash_detector.serving.dial_presentation": (
        "ESTABLISHED",
        "dial_id, reason and missing_inputs are re-established at both constructors and at "
        "present_dial; the magnitude is admitted by exact type; the score is admitted by "
        "exact-type membership in SCORE_TYPES; the presentation surface is re-verified at "
        "every consumer boundary.",
    ),
    "crash_detector.dials.reading": (
        "ESTABLISHED",
        "fold and is_value dispatch on exact type identity against a frozenset of class "
        "objects, and the constructors are unsubclassable, so the class objects can only be "
        "the three. Timestamps go through ensure_utc and the reason labels through "
        "_own_reason. The declared-surface comparisons are set operations over strings read "
        "from a class dictionary — this package's own class dictionary, re-verified rather "
        "than trusted, which is boundary A of this module's own declared limit.",
    ),
    "crash_detector.dials.dialset": (
        "EXACT",
        "Every decision here is an exact-type test: the reading by membership in "
        "READING_CONSTRUCTORS, the payload by `type(reading.value) is not expected`. Both "
        "operand types are sealed against subclassing, so the class objects compared are "
        "necessarily this package's own.",
    ),
    "crash_detector.dials.provenance": (
        "ESTABLISHED",
        "The provenance set is rebuilt from own_str'd elements at _install, so every later "
        "set-equality comparison — which is the whole cross-dial refusal — hashes plain "
        "strings. require_finite_float returns the established float, so the reductions "
        "(math.fsum, max, min) compute on numbers this module holds rather than on objects "
        "whose __lt__ and __add__ a caller wrote. The reduction itself is admitted by exact "
        "type against an enum.Enum the interpreter closes.",
    ),
    "crash_detector.dials.magnitude": (
        "ESTABLISHED",
        "dial_id is re-established at _install and at quantity_for before the set-equality "
        "comparisons that decide which dial a number belongs to; the quantity is admitted "
        "by exact type; __setstate__ counts and indexes a container this method built. "
        "sole_dial_of's sorted() runs over a provenance set whose single element was "
        "established at install.",
    ),
    "crash_detector.dials.scores": (
        "ESTABLISHED",
        "The magnitude is admitted by exact type and its provenance compared by set "
        "equality against a module constant; Contribution re-establishes both labels and "
        "both numbers. The two score types share no ancestor and neither subclasses float.",
    ),
    "crash_detector.engine.evaluate": (
        "ESTABLISHED",
        "The outcome is admitted by EXACT type; both sides of the latest-observation "
        "comparison and every element of the oldest-as-of min() are put through ensure_utc; "
        "the window is a StalenessWindow and not a float, so a private helper cannot be "
        "called with an unadmitted quantity; the absence post-condition dispatches on exact "
        "type. `source_id in usable` compares strings established at DialSpec and at "
        "ObservationRecord. THE ONE EXCEPTION IS DECLARED BELOW under model.",
    ),
    "crash_detector.engine.config": (
        "ESTABLISHED",
        "dial_id and both input-id tuples are re-established before the membership, "
        "duplicate and overlap tests; specs and the registry are admitted by exact type; "
        "the window's usability is decided by StalenessWindow, which admits by exact type.",
    ),
    "crash_detector.engine.model": (
        "OUT_OF_BOUND",
        "*** DECLARED OPEN, DELIBERATELY NOT CLOSED, ON THE PRODUCT AUTHORITY'S RULING. *** "
        "ContributionModel is a caller-supplied object whose compute() returns the number a "
        "dial publishes, and one stateful instance injected into BOTH DialSpecs makes the "
        "monetary dial publish the mean of the two (CD-ENG-WO2R2-F03, replicated by the "
        "Project Lead as PL-Z4). At the level of doctrine that IS this class — a judgement "
        "delegated to an object the system did not construct, one operand across — and that "
        "resemblance is exactly why it is not closed here. PO-DECISIONS-0003 ruled it closed "
        "by CONSTRUCTION at a different altitude: BLUEPRINT §7 architectural review as the "
        "mandatory first item of WO-3, plus the CD-D-005 ingredient register. Building a "
        "model guard in this increment would be the fourth clever guard against a class the "
        "Product Authority has ruled is not closed by guards (CD-D-075). DECLARING it is "
        "this seat's CD-RULE-004 obligation; CLOSING it would be the scope breach. "
        "NOT PROVED TO BE CARRIED ANYWHERE.",
    ),
    "crash_detector.observations": (
        "ESTABLISHED",
        "source_id is re-established before it is used as a dict key or tested for "
        "membership; timestamps go through ensure_utc; the outcome sum type is discriminated "
        "by exact-type dict lookup and ObservationRecord refuses a non-member. The two "
        "OUT_OF_BOUND admissions on FetchFailed and Malformed are declared per site above.",
    ),
    "crash_detector.source_registry": (
        "ESTABLISHED",
        "The three labels are re-established before the duplicate set and the lookups that "
        "the criticality contract rests on; records are admitted by exact type; criticality "
        "is an enum the interpreter closes. The cadence_seconds int-subclass site is "
        "declared DELEGATED per site above, with the reason it is not on a deciding path.",
    ),
}
