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
        "crash_detector.engine.model",
        "ModelSpec.__post_init__",
        "DUCK",
        "getattr(self, field_name)",
    ): (
        "ESTABLISHED",
        "field_name iterates a tuple literal in this file — the two input-id tuples — not a "
        "probe of a supplied object's surface. Both are rebuilt through own_str and written "
        "back before the duplicate, overlap and subset tests, all of which are set "
        "membership and were otherwise the supplied strings' __hash__/__eq__ to answer. The "
        "subset test in establish_model_for_dial compares these ids against the naming "
        "DialSpec's, which are established the same way at the same door, so both sides of "
        "that comparison are strings this package built.",
    ),
    (
        "crash_detector.engine.model",
        "ModelProvenance.__post_init__",
        "DUCK",
        "getattr(self, field_name)",
    ): (
        "ESTABLISHED",
        "field_name iterates a tuple literal in this file — the type's own three declared "
        "fields, written once instead of three times. Each is rebuilt through own_str and "
        "written back, so the emptiness test below it is on a string this module built. "
        "These fields decide nothing at runtime: they carry CD-D-005's account of a mapping "
        "for a human reader, which is why the disposition rests on establishment and not on "
        "a downstream comparison.",
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

    # ==================================================================================== #
    # THE FIFTEEN — WO-2R3 THE RECORD ACT. `PO-DECISIONS-0015` ruling 4:
    #   *"THE ONE ACT DISPOSITIONS FIFTEEN, NOT ELEVEN ... the instrument's count beats the
    #    ruling's prose ... Category C's six sites are RE-DISPOSITIONED: their stated ground
    #    is falsified by CD-PL-F103, and a disposition whose reason has died does not survive
    #    on habit."*
    #
    # **THIRTEEN SITES BELOW AND TWO MODULES DERIVED FROM THE TIER-2 BLOCK AT THE END OF THIS
    # FILE. TEN OF THE THIRTEEN ARE `DEFECT_OPEN`, AND `DEFECT_OPEN` BUYS NOTHING** — not a
    # pass, not an exemption, not a gate. A register with ten of them is a register honestly
    # describing a system with ten open defects in its admission and establishment mechanisms.
    # If the sweep exits 0 after this act, that is ARITHMETIC over the declaration set and it
    # is not evidence that one line of `src/` changed. NOT ONE LINE OF `src/` CHANGED.
    #
    # The claims are the Project Lead's (`governance/engineering/CD-THE-FIFTEEN-AND-THE-
    # REDRAFT.md` §3), re-measured by the writing Engineer where they are measurements.
    # ==================================================================================== #

    # --- Category A — ONE site. Unchanged from the draft, and it was right. -------------- #
    (
        "crash_detector.admission",
        "_is_defined_in_a_class_body",
        "DUCK",
        "getattr(entry_point, '__qualname__', '')",
    ): (
        "DEFECT_OPEN",
        {
            "finding": "CD-F-0001",
            "measured_reach": (
                "One writable attribute, in-process, before decoration; bounded to parameters "
                "named in `_RECEIVER_NAMES` (`self`/`cls`), which is ONE IDENTIFIER WIDE AND "
                "NOT ZERO — `assert_closed_presentation_surface(cls)` on the serving path is a "
                "real module-level function with a parameter named `cls`. **THE SITE "
                "FALSIFIES ITS OWN SHIPPED DOCSTRING**, which says the property `is not "
                "something a caller can influence`."
            ),
            "counterfactual": (
                "Without the assignment: `UndeclaredParameter: free_function2 is a FAULTED "
                "door and every call to it is refused`."
            ),
            "note": (
                "CD-D-153 prohibited increment 7 from fixing it and this act is prohibited "
                "from fixing it too. Its remediation is a separate ruling and is still owed. "
                "**IT CLOSES NOTHING AND IT IS NOT AN EXEMPTION.**"
            ),
        },
    ),

    # --- Category B — THREE sites. `CARRIER_ONLY` was ratified as drafted. --------------- #
    #
    # **`callable` CARRIES THE CALLABLE'S NAME AND NOT A LIST OF CARRIER FILES**, because the
    # NAME is what `_carrier_only_violations` matches against call expressions in every other
    # swept module. MEASURED BY THE WRITING ENGINEER, both arms, with a product caller of
    # `admission_faults` planted in `engine/evaluate.py`: with the callable's NAME here the
    # check FIRES (`CARRIER_ONLY_HAS_A_PRODUCT_CALLER`); with a list of carrier file paths
    # here **IT DOES NOT FIRE AT ALL**. The carrier file list is prose and lives below in
    # `why_it_is_not_product_judgement`, where prose belongs.
    (
        "crash_detector.admission",
        "admission_faults",
        "DUCK",
        "getattr(door, FAULTS_ATTRIBUTE, ())",
    ): (
        "CARRIER_ONLY",
        {
            "callable": "admission_faults",
            "why_it_is_not_product_judgement": (
                "It believes any object carrying the attribute — `admission_faults(Liar())` "
                "returns `()`. MEASURED over every module under `src/`: no product module "
                "calls it. Its callers are `tests/test_admission.py`, "
                "`tests/test_judgement_path_doors.py` and `tests/test_collector_runner.py`, "
                "and THAT SENTENCE IS PROSE — the enumeration the instrument holds is the "
                "`callable` field, and the build breaks the day a module under `src/` calls "
                "it. The blast radius is a carrier believing a claim an object makes about "
                "itself."
            ),
        },
    ),
    (
        "crash_detector.admission",
        "declared_admissions",
        "DUCK",
        "getattr(door, ADMITS_ATTRIBUTE, {})",
    ): (
        "CARRIER_ONLY",
        {
            "callable": "declared_admissions",
            "why_it_is_not_product_judgement": (
                "`declared_admissions(Liar())` returns `{'x': 'whatever'}`. MEASURED: no "
                "module under `src/` calls it. Same carriers, same blast radius."
            ),
        },
    ),
    (
        "crash_detector.admission",
        "is_admitting_door",
        "DUCK",
        "hasattr(door, ADMITS_ATTRIBUTE)",
    ): (
        "CARRIER_ONLY",
        {
            "callable": "is_admitting_door",
            "why_it_is_not_product_judgement": (
                "`is_admitting_door(Liar())` returns `True`. MEASURED: no module under `src/` "
                "calls it. Same carriers, same blast radius."
            ),
        },
    ),

    # --- Category C — SIX sites. **RE-DISPOSITIONED. THE DRAFT WAS `OUT_OF_BOUND` x6 AND ITS
    #     GROUND IS DEAD.** The draft's ground was *"no caller-controlled route"*, falsified
    #     twice independently — by the sixth seat's `F-06-R` and by `CD-PL-F103`, which
    #     measured the metaclass admission bypass END TO END on an ordinary, source-honest
    #     `@admits(value=int)` door reporting ZERO faults.
    #
    #     **AND THE FIFTH SEAT WAS NOT WRONG, WHICH MATTERS.** Its narrow claim — these are
    #     consumed at decoration from a source-written declaration and there is no caller
    #     route — is CORRECT, and the sixth seat says so in terms. The defect is that "no
    #     caller-controlled route" was THE WRONG TEST: the module's own doctrine is that a
    #     subclass is never trusted, and the DECLARATION vocabulary is admitted by `isinstance`
    #     at all six sites while the VALUE vocabulary is not. `OUT_OF_BOUND` recorded the
    #     weaker half of the fact, and **`OUT_OF_BOUND` IS A SCOPE CLAIM NO INSTRUMENT CAN
    #     FALSIFY** — which is why replacing it with a word carrying a resolvable finding is
    #     not a relabelling.
    # ------------------------------------------------------------------------------------ #
    (
        "crash_detector.admission",
        "_EstablishedHere.__call__",
        "ISINSTANCE",
        "isinstance(because, str)",
    ): (
        "DEFECT_OPEN",
        {
            "finding": ("CD-F-0002", "CD-F-0003"),
            "measured_reach": (
                "A `str` SUBCLASS satisfies this test and then supplies `strip`. F-06-R measured it: a subclass whose `strip` lies gets an UNEXPLAINED EXEMPTION through the one guard that exists to stop exactly that."
            ),
            "counterfactual": (
                "Exact-type identity at the same site refuses the subclass — the discipline "
                "this module already applies to VALUES and does not apply to DECLARATIONS. "
                "F-06-D's own one-line form for the downstream half: "
                "`any(type(value) is t for t in self.types)`."
            ),
            "note": (
                "WAS `OUT_OF_BOUND` IN THE SUPERSEDED DRAFT "
                "(`governance/engineering/CD-PROPOSAL-ELEVEN-DISPOSITIONS.md`, which is NOT "
                "edited — corrections supersede). The draft's ground, *\"no caller-controlled "
                "route\"*, is dead. **NOT FIXED BY THIS ACT AND NOT SCHEDULED TO BE BY IT.**"
            ),
        },
    ),

    (
        "crash_detector.admission",
        "_compile",
        "ISINSTANCE",
        "isinstance(declaration, _Admission)",
    ): (
        "DEFECT_OPEN",
        {
            "finding": ("CD-F-0002", "CD-F-0003"),
            "measured_reach": (
                "An `_Admission` SUBCLASS satisfies this test and then supplies `refusal` and `describe`. F-06-R measured one whose `refusal` returns `None` AND whose `describe()` reports 'exactly PanelRow' — a door that admits everything and reports that it does not."
            ),
            "counterfactual": (
                "Exact-type identity at the same site refuses the subclass — the discipline "
                "this module already applies to VALUES and does not apply to DECLARATIONS. "
                "F-06-D's own one-line form for the downstream half: "
                "`any(type(value) is t for t in self.types)`."
            ),
            "note": (
                "WAS `OUT_OF_BOUND` IN THE SUPERSEDED DRAFT "
                "(`governance/engineering/CD-PROPOSAL-ELEVEN-DISPOSITIONS.md`, which is NOT "
                "edited — corrections supersede). The draft's ground, *\"no caller-controlled "
                "route\"*, is dead. **NOT FIXED BY THIS ACT AND NOT SCHEDULED TO BE BY IT.**"
            ),
        },
    ),

    (
        "crash_detector.admission",
        "_compile",
        "ISINSTANCE",
        "isinstance(declaration, tuple)",
    ): (
        "DEFECT_OPEN",
        {
            "finding": ("CD-F-0002", "CD-F-0003"),
            "measured_reach": (
                "A `tuple` SUBCLASS satisfies this test and then supplies `__iter__`. F-06-R measured one whose `__iter__` yields something other than what `repr` and `len` show."
            ),
            "counterfactual": (
                "Exact-type identity at the same site refuses the subclass — the discipline "
                "this module already applies to VALUES and does not apply to DECLARATIONS. "
                "F-06-D's own one-line form for the downstream half: "
                "`any(type(value) is t for t in self.types)`."
            ),
            "note": (
                "WAS `OUT_OF_BOUND` IN THE SUPERSEDED DRAFT "
                "(`governance/engineering/CD-PROPOSAL-ELEVEN-DISPOSITIONS.md`, which is NOT "
                "edited — corrections supersede). The draft's ground, *\"no caller-controlled "
                "route\"*, is dead. **NOT FIXED BY THIS ACT AND NOT SCHEDULED TO BE BY IT.**"
            ),
        },
    ),

    (
        "crash_detector.admission",
        "_compile",
        "ISINSTANCE",
        "isinstance(declaration, type)",
    ): (
        "DEFECT_OPEN",
        {
            "finding": ("CD-F-0002", "CD-F-0003"),
            "measured_reach": (
                "**C4, VERIFIED BY THE SIXTH SEAT PERSONALLY AND RE-STATED BY CD-PL-F103.** A metaclass defining `__eq__` satisfies `isinstance(X, type)` here and then compares EQUAL TO EVERY TYPE at `_Exactly.refusal`. Measured end to end on an ordinary `@admits(value=Wildcard)` door: `faults: ()`, `is_admitting_door: True`, and every value admitted."
            ),
            "counterfactual": (
                "Exact-type identity at the same site refuses the subclass — the discipline "
                "this module already applies to VALUES and does not apply to DECLARATIONS. "
                "F-06-D's own one-line form for the downstream half: "
                "`any(type(value) is t for t in self.types)`."
            ),
            "note": (
                "WAS `OUT_OF_BOUND` IN THE SUPERSEDED DRAFT "
                "(`governance/engineering/CD-PROPOSAL-ELEVEN-DISPOSITIONS.md`, which is NOT "
                "edited — corrections supersede). The draft's ground, *\"no caller-controlled "
                "route\"*, is dead. **NOT FIXED BY THIS ACT AND NOT SCHEDULED TO BE BY IT.**"
            ),
        },
    ),

    (
        "crash_detector.admission",
        "_type_tuple",
        "ISINSTANCE",
        "isinstance(value, type)",
    ): (
        "DEFECT_OPEN",
        {
            "finding": ("CD-F-0002", "CD-F-0003"),
            "measured_reach": (
                "The same metaclass lever, one function down — `_type_tuple` is what `one_of` and `each_of` compile their declarations through."
            ),
            "counterfactual": (
                "Exact-type identity at the same site refuses the subclass — the discipline "
                "this module already applies to VALUES and does not apply to DECLARATIONS. "
                "F-06-D's own one-line form for the downstream half: "
                "`any(type(value) is t for t in self.types)`."
            ),
            "note": (
                "WAS `OUT_OF_BOUND` IN THE SUPERSEDED DRAFT "
                "(`governance/engineering/CD-PROPOSAL-ELEVEN-DISPOSITIONS.md`, which is NOT "
                "edited — corrections supersede). The draft's ground, *\"no caller-controlled "
                "route\"*, is dead. **NOT FIXED BY THIS ACT AND NOT SCHEDULED TO BE BY IT.**"
            ),
        },
    ),

    (
        "crash_detector.admission",
        "each_of",
        "ISINSTANCE",
        "isinstance(within, tuple)",
    ): (
        "DEFECT_OPEN",
        {
            "finding": ("CD-F-0002", "CD-F-0003"),
            "measured_reach": (
                "A `tuple` subclass passes and then decides its own iteration and its own truthiness at the two tier-2 sites immediately below it."
            ),
            "counterfactual": (
                "Exact-type identity at the same site refuses the subclass — the discipline "
                "this module already applies to VALUES and does not apply to DECLARATIONS. "
                "F-06-D's own one-line form for the downstream half: "
                "`any(type(value) is t for t in self.types)`."
            ),
            "note": (
                "WAS `OUT_OF_BOUND` IN THE SUPERSEDED DRAFT "
                "(`governance/engineering/CD-PROPOSAL-ELEVEN-DISPOSITIONS.md`, which is NOT "
                "edited — corrections supersede). The draft's ground, *\"no caller-controlled "
                "route\"*, is dead. **NOT FIXED BY THIS ACT AND NOT SCHEDULED TO BE BY IT.**"
            ),
        },
    ),

    # --- The three `crash_detector.establishment` sites — READ FOR THE FIRST TIME AT THE
    #     ISSUING BOUNDARY, AND RE-MEASURED HERE BY THE SEAT WRITING THEM.
    #
    #     No seat had read these one at a time. The SIXTH Assurance seat listed the governing
    #     question in its own §4 as something IT COULD NOT ESTABLISH. The Project Lead measured
    #     it (`PL-AB0`, five arms) rather than hand an Engineer an invented disposition, and
    #     handed the result over as EVIDENCE TO BE CONTRADICTED.
    #
    #     **RE-MEASURED INDEPENDENTLY BY CD-ENG-WO2R3-04**, on its own `git archive af2accb`
    #     extraction at /tmp, driver written from the finding text rather than copied, tree
    #     line printed on every arm (CD-PL-F98). **ALL FIVE ARMS REPRODUCE.** One difference,
    #     and it is in the finding's favour: the PL declared `governed_types()` 0 -> 1 under a
    #     BARE import of `establishment` alone and stated that limit; re-run under a full
    #     package import it is **7 -> 8**, so the consequence does not depend on the bare-import
    #     condition. One qualification, and it cuts the other way and is recorded in the
    #     tier-2 rows: `governed_types`, `is_establishing_type`, `establishment_faults` and
    #     `establishment_field_list` are ALL `CARRIER_ONLY` — **no module under `src/` calls any
    #     of them** — so the "FORGED GOVERNED TYPE" is minted into surfaces that only carriers
    #     read. The decoration succeeding on a non-dataclass is unaffected by that and stands.
    # ------------------------------------------------------------------------------------ #
    (
        "crash_detector.establishment",
        "_declared_field_list",
        "DUCK",
        "getattr(cls, '__dataclass_fields__', {})",
    ): (
        "DEFECT_OPEN",
        {
            "finding": "CD-F-0004",
            "measured_reach": (
                "**`establishes` IS PUBLIC AND IN `__all__`.** Ordinary in-process caller code "
                "decorates its own class, so `cls` here is CALLER-SUPPLIED — RE-MEASURED: a "
                "caller-authored frozen dataclass decorated and constructed successfully. The "
                "`dataclasses.is_dataclass` gate above this line is itself a `hasattr` probe: "
                "a plain class carrying `__dataclass_fields__ = {}` passes it and "
                "`establishes()(Hostile)` SUCCEEDS, where the shipped docstring says it "
                "`:raises EstablishmentFault:`. RE-MEASURED: `is_establishing_type(Hostile)` "
                "-> True, `establishment_faults(Hostile)` -> `()`, and Hostile ENTERS "
                "`governed_types()` (7 -> 8 under a full package import)."
            ),
            "counterfactual": (
                "The same arm without the forged `__dataclass_fields__` attribute. RE-MEASURED: "
                "`EstablishmentFault: @establishes was applied to <class 'Honest'>, which is "
                "not a dataclass`, at decoration, and `is_establishing_type(Honest)` -> False. "
                "The class never enters `governed_types()`."
            ),
            "note": (
                "**THIS IS `F-06-R`'s SENTENCE ONE MODULE ACROSS, IN A PUBLIC EXPORTED ENTRY "
                "POINT.** NOT FIXED BY THIS ACT: the `is_dataclass` gate is explicitly out of "
                "this dispatch's reach and its remediation is not yet authorised by anyone."
            ),
        },
    ),
    (
        "crash_detector.establishment",
        "_declared_field_list",
        "DUCK",
        "getattr(field._field_type, 'name', '')",
    ): (
        "DEFECT_OPEN",
        {
            "finding": "CD-F-0004",
            "measured_reach": (
                "The InitVar detection reads a name off an object the caller put in "
                "`__dataclass_fields__`. RE-MEASURED: a forged `_field_type.name` of "
                "`'_FIELD_INITVAR'` STEERS the InitVar refusal from caller-written data — "
                "`_declared_field_list(ForgedCls)` returned `names=() initvars=('x',)`. An "
                "InitVar fault is what makes every construction of a type refuse, so this "
                "steers a type into or out of being FAULTED."
            ),
            "counterfactual": (
                "The same class without the forged `_field_type`: `dataclasses.fields(cls)` "
                "and the real `_FIELD_INITVAR` sentinel decide, and `initvars` is `()`."
            ),
            "note": "NOT FIXED BY THIS ACT.",
        },
    ),
    (
        "crash_detector.establishment",
        "establishes.apply_at_the_boundary.__init__",
        "DUCK",
        "getattr(self, name, _ABSENT)",
    ): (
        "DEFECT_OPEN",
        {
            "finding": "CD-F-0004",
            "measured_reach": (
                "`self` at this site can be a caller's instance: RE-MEASURED, "
                "`crash_detector.observations.OK` — a live governed type chosen from the "
                "package at run time, not named in the driver — SUBCLASSES SUCCESSFULLY, so "
                "the probed instance is the caller's and every attribute this loop reads back "
                "is one the subclass may shadow with a property."
            ),
            "counterfactual": (
                "A type sealed against subclassing at this position refuses the subclass "
                "outright — the remedy this tree already applies to 13 of its 99 governed "
                "types through `__slots__`, and never asked of the other 77 (`F-06-J`)."
            ),
            "note": (
                "NOT FIXED BY THIS ACT. **THE FOURTH ASSURANCE SEAT'S AND THE SIXTH'S BEST "
                "RESULTS BOTH CAME FROM DISBELIEVING A DISPOSITION THE RECORD HAD SETTLED**, "
                "and these three have now been read exactly twice, by two seats, one of which "
                "dispatched the other."
            ),
        },
    ),

    # ==================================================================================== #
    # TIER 2 — THE DECIDING OPERATION, DECLARED PER SITE FOR THE TWO MECHANISM MODULES.
    #
    # **THESE FIFTY ROWS ARE WHAT DERIVES THE MODULE ANSWER FOR `crash_detector.admission`
    # AND `crash_detector.establishment`, AND NEITHER MODULE GETS A MODULE-LEVEL PROSE CLAIM
    # AT ALL** (`PO-DECISIONS-0014` ruling 1, as read at §1.3 of the content document). The
    # sweep DERIVES `DECLARED` for a module whose every distinct tier-2 site key carries an
    # entry here. Remove ONE row and the module goes UNDECLARED again; that arm is run.
    #
    # **THE PRICE, MEASURED BEFORE ONE ROW WAS WRITTEN.** The content document expected the
    # 33 and 17 tier-2 OCCURRENCES to *"collapse to some SMALLER number of distinct site
    # keys"*. **THEY DO NOT COLLAPSE AT ALL: 33 occurrences are 33 distinct keys and 17 are
    # 17.** The ten duplicates in this closure are all in other modules. Fifty rows, exactly.
    #
    # **THIS IS WHERE THE REGISTER'S OWN DECLARED WEAKNESS IS CLOSED FOR THESE TWO MODULES**
    # — *"a module-level claim is WEAKER than a per-site one ... THE WEAKNESS IS THE LIMIT"*.
    # It is closed for exactly the two modules where the strongest claim in the register was
    # resting on the weakest instrument, and NOWHERE ELSE: the other seventeen still take the
    # module route, and that limit still stands for them.
    #
    # **AND WHAT `gates` DOES AND DOES NOT SAY, BECAUSE THE FIELD IS NEW AND WILL BE READ.**
    # The instrument checks that the named site EXISTS in this run's own measured site set and
    # that it is in a DIFFERENT module. **IT DOES NOT CHECK THAT IT IS DOWNSTREAM, REACHABLE,
    # OR RELATED.** The gating relation is a CLAIM BY THIS SEAT; what the machine holds is
    # that the claim points at something real. Both modules' rows name the same downstream
    # point, chosen because it is the tightest true one: `crash_detector.engine.evaluate` is
    # `@admits(config_snapshot=ConfigSnapshot, ...)` and `ConfigSnapshot`/`DialSpec` are
    # `@establishes` types, so if these mechanisms mis-decide, the judgement path runs on an
    # object those tier-1 admissions never ran on. **A UNIFORM `gates` WITHIN A MODULE CARRIES
    # NO PER-SITE INFORMATION AND THAT IS SAID HERE RATHER THAN LEFT TO BE NOTICED**; the
    # per-site facts are in `operand_origin` and `finding`.
    # ==================================================================================== #

    # --- crash_detector.admission: 33 distinct tier-2 site keys, ALL declared. --- #
    (
        'crash_detector.admission',
        '_EachOf.refusal',
        'MEMBERSHIP',
        'type(element) not in self.element',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'CALLER_SUPPLIED',
            "gates": (
                'crash_detector.engine.config',
                'ConfigSnapshot.__post_init__',
                'ISINSTANCE',
                'isinstance(window, float)',
            ),
            "finding": 'CD-F-0003',
            "note": (
                '`not in` over a tuple is `==`, and `==` is delegable to a metaclass. type(element) '
                'is the type of a CALLER-SUPPLIED container element. F-06-D names this idiom at '
                'admission.py:556 and :565 in terms.'
            ),
        },
    ),

    (
        'crash_detector.admission',
        '_EachOf.refusal',
        'MEMBERSHIP',
        'type(value) not in self.within',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'CALLER_SUPPLIED',
            "gates": (
                'crash_detector.engine.config',
                'ConfigSnapshot.__post_init__',
                'ISINSTANCE',
                'isinstance(window, float)',
            ),
            "finding": 'CD-F-0003',
            "note": (
                'As above, on the container itself rather than its elements.'
            ),
        },
    ),

    (
        'crash_detector.admission',
        '_EstablishedHere.__call__',
        'TRUTHINESS',
        'not isinstance(because, str) or not because.strip()',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'SOURCE_DECLARATION',
            "gates": (
                'crash_detector.engine.config',
                'ConfigSnapshot.__post_init__',
                'ISINSTANCE',
                'isinstance(window, float)',
            ),
            "finding": 'CD-F-0002',
            "note": (
                '`because` is written in the source of the declaring module. `because.strip()` is '
                "then the supplied object's method to answer: F-06-R measured a str subclass whose "
                'strip lies obtaining an UNEXPLAINED EXEMPTION through the one guard that exists to '
                'stop exactly that. SOURCE_DECLARATION and not CALLER_SUPPLIED because the operand is '
                'source-written; the defect is named rather than re-labelled.'
            ),
        },
    ),

    (
        'crash_detector.admission',
        '_Exactly.describe',
        'IDENTITY',
        't is type(None)',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'SOURCE_DECLARATION',
            "gates": (
                'crash_detector.engine.config',
                'ConfigSnapshot.__post_init__',
                'ISINSTANCE',
                'isinstance(window, float)',
            ),
            "note": (
                '`is` is the one operation that is NEVER delegated, and `t` iterates a tuple compiled '
                'from a source-written declaration. No supplied implementation exists to reach.'
            ),
        },
    ),

    (
        'crash_detector.admission',
        '_Exactly.refusal',
        'MEMBERSHIP',
        'type(value) in self.types',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'CALLER_SUPPLIED',
            "gates": (
                'crash_detector.engine.config',
                'ConfigSnapshot.__post_init__',
                'ISINSTANCE',
                'isinstance(window, float)',
            ),
            "finding": 'CD-F-0003',
            "note": (
                '**THIS IS admission.py:525, THE EXACT LINE OF F-06-D.** The module states its '
                "doctrine three times -- 'type(value) is not declared, never isinstance' -- and "
                'implements it with `in`, which is `==`, which a metaclass answers. A door declared '
                '@admits(value=Wildcard) admits everything, reports no fault, and tells its own '
                'introspection surface it requires Wildcard.'
            ),
        },
    ),

    (
        'crash_detector.admission',
        '_compile',
        'IDENTITY',
        'declaration is ESTABLISHED_HERE',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'MODULE_CONSTANT',
            "gates": (
                'crash_detector.engine.config',
                'ConfigSnapshot.__post_init__',
                'ISINSTANCE',
                'isinstance(window, float)',
            ),
            "note": (
                "Identity against this module's own sentinel instance, bound once at import."
            ),
        },
    ),

    (
        'crash_detector.admission',
        '_compile',
        'IDENTITY',
        'declaration is None',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'SOURCE_DECLARATION',
            "gates": (
                'crash_detector.engine.config',
                'ConfigSnapshot.__post_init__',
                'ISINSTANCE',
                'isinstance(window, float)',
            ),
            "note": (
                'Identity against the None singleton; the left operand is a source-written '
                'declaration.'
            ),
        },
    ),

    (
        'crash_detector.admission',
        '_faults',
        'COERCION',
        'tuple(found)',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'OWN_CONSTRUCTION',
            "gates": (
                'crash_detector.engine.config',
                'ConfigSnapshot.__post_init__',
                'ISINSTANCE',
                'isinstance(window, float)',
            ),
            "note": (
                '`found` is a list this function appended to in this scope; tuple() runs '
                'list.__iter__.'
            ),
        },
    ),

    (
        'crash_detector.admission',
        '_faults',
        'IDENTITY',
        'parameter.kind is inspect.Parameter.VAR_KEYWORD',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'MODULE_CONSTANT',
            "gates": (
                'crash_detector.engine.config',
                'ConfigSnapshot.__post_init__',
                'ISINSTANCE',
                'isinstance(window, float)',
            ),
            "note": (
                'Identity against a stdlib enum member resolved at import. Identity admits no '
                'implementation.'
            ),
        },
    ),

    (
        'crash_detector.admission',
        '_faults',
        'IDENTITY',
        'parameter.kind is inspect.Parameter.VAR_POSITIONAL',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'MODULE_CONSTANT',
            "gates": (
                'crash_detector.engine.config',
                'ConfigSnapshot.__post_init__',
                'ISINSTANCE',
                'isinstance(window, float)',
            ),
            "note": (
                'As above.'
            ),
        },
    ),

    (
        'crash_detector.admission',
        '_faults',
        'MEMBERSHIP',
        'name not in named',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'CALLER_SUPPLIED',
            "gates": (
                'crash_detector.engine.config',
                'ConfigSnapshot.__post_init__',
                'ISINSTANCE',
                'isinstance(window, float)',
            ),
            "finding": 'CD-F-0001',
            "note": (
                '`named` holds p.name strings taken from inspect.signature(entry_point); '
                '`entry_point` reaches this module from a caller, since `admits` is PUBLIC and in '
                '__all__ and admits(...)(anything) is one line of ordinary in-process code. A str '
                'subclass in that list answers the comparison by reflection.'
            ),
        },
    ),

    (
        'crash_detector.admission',
        '_faults',
        'MEMBERSHIP',
        'parameter.name not in declared',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'CALLER_SUPPLIED',
            "gates": (
                'crash_detector.engine.config',
                'ConfigSnapshot.__post_init__',
                'ISINSTANCE',
                'isinstance(window, float)',
            ),
            "finding": 'CD-F-0001',
            "note": (
                'The left operand is a name read out of a caller-supplied signature; `declared` is '
                'the source-written kwargs mapping. Which side is hostile is the left one.'
            ),
        },
    ),

    (
        'crash_detector.admission',
        '_is_defined_in_a_class_body',
        'COERCION',
        'bool(parent)',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'CALLER_SUPPLIED',
            "gates": (
                'crash_detector.engine.config',
                'ConfigSnapshot.__post_init__',
                'ISINSTANCE',
                'isinstance(window, float)',
            ),
            "finding": 'CD-F-0001',
            "note": (
                "`parent` is derived from getattr(entry_point, '__qualname__', ''), the tier-1 site "
                "that IS Category A. **THIS IS CATEGORY A's TIER-2 COMPANION** and it decides, on one "
                'writable attribute, whether a receiver parameter is skipped and therefore whether '
                'the door is FAULTED at all.'
            ),
        },
    ),

    (
        'crash_detector.admission',
        '_names',
        'IDENTITY',
        't is type(None)',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'SOURCE_DECLARATION',
            "gates": (
                'crash_detector.engine.config',
                'ConfigSnapshot.__post_init__',
                'ISINSTANCE',
                'isinstance(window, float)',
            ),
            "note": (
                'As _Exactly.describe.'
            ),
        },
    ),

    (
        'crash_detector.admission',
        '_signature_parameters',
        'COERCION',
        'list(signature.parameters.values())',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'CALLER_SUPPLIED',
            "gates": (
                'crash_detector.engine.config',
                'ConfigSnapshot.__post_init__',
                'ISINSTANCE',
                'isinstance(window, float)',
            ),
            "finding": 'CD-F-0001',
            "note": (
                '`signature` comes from inspect.signature(entry_point, follow_wrapped=False), and '
                '__signature__ is a writable attribute of a caller-supplied object.'
            ),
        },
    ),

    (
        'crash_detector.admission',
        '_signature_parameters',
        'MEMBERSHIP',
        'parameters[0].kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'CALLER_SUPPLIED',
            "gates": (
                'crash_detector.engine.config',
                'ConfigSnapshot.__post_init__',
                'ISINSTANCE',
                'isinstance(window, float)',
            ),
            "finding": 'CD-F-0001',
            "note": (
                'The right operand is a tuple of stdlib enum members; the left is read out of a '
                'caller-influenced signature and answers the comparison.'
            ),
        },
    ),

    (
        'crash_detector.admission',
        '_signature_parameters',
        'MEMBERSHIP',
        'parameters[0].name in _RECEIVER_NAMES',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'CALLER_SUPPLIED',
            "gates": (
                'crash_detector.engine.config',
                'ConfigSnapshot.__post_init__',
                'ISINSTANCE',
                'isinstance(window, float)',
            ),
            "finding": 'CD-F-0001',
            "note": (
                '_RECEIVER_NAMES is a module constant. The left operand is not. This is the one- '
                "identifier-wide bound Category A's measured_reach names."
            ),
        },
    ),

    (
        'crash_detector.admission',
        '_signature_parameters',
        'TRUTHINESS',
        '_is_defined_in_a_class_body(entry_point) and parameters and (parameters[0].name in _RECEIVER_NAMES) and (parameters[0].kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD))',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'OWN_CONSTRUCTION',
            "gates": (
                'crash_detector.engine.config',
                'ConfigSnapshot.__post_init__',
                'ISINSTANCE',
                'isinstance(window, float)',
            ),
            "note": (
                'The recorded operation is the truthiness of `parameters`, a list THIS function '
                "built, so __bool__ is list's. The conjuncts either side are declared at their own "
                'sites above.'
            ),
        },
    ),

    (
        'crash_detector.admission',
        '_type_tuple',
        'COERCION',
        'tuple(resolved)',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'OWN_CONSTRUCTION',
            "gates": (
                'crash_detector.engine.config',
                'ConfigSnapshot.__post_init__',
                'ISINSTANCE',
                'isinstance(window, float)',
            ),
            "note": (
                '`resolved` is a list built in this scope.'
            ),
        },
    ),

    (
        'crash_detector.admission',
        '_type_tuple',
        'IDENTITY',
        'value is None',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'SOURCE_DECLARATION',
            "gates": (
                'crash_detector.engine.config',
                'ConfigSnapshot.__post_init__',
                'ISINSTANCE',
                'isinstance(window, float)',
            ),
            "note": (
                'Identity against the None singleton.'
            ),
        },
    ),

    (
        'crash_detector.admission',
        '_type_tuple',
        'TRUTHINESS',
        'not resolved',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'OWN_CONSTRUCTION',
            "gates": (
                'crash_detector.engine.config',
                'ConfigSnapshot.__post_init__',
                'ISINSTANCE',
                'isinstance(window, float)',
            ),
            "note": (
                'list.__bool__ on a list built here.'
            ),
        },
    ),

    (
        'crash_detector.admission',
        '_type_tuple',
        'TRUTHINESS',
        'resolved',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'OWN_CONSTRUCTION',
            "gates": (
                'crash_detector.engine.config',
                'ConfigSnapshot.__post_init__',
                'ISINSTANCE',
                'isinstance(window, float)',
            ),
            "note": (
                'As above.'
            ),
        },
    ),

    (
        'crash_detector.admission',
        'admission_faults',
        'COERCION',
        'tuple(getattr(door, FAULTS_ATTRIBUTE, ()))',
    ): (
        "CARRIER_ONLY",
        {
            "callable": 'admission_faults',
            "why_it_is_not_product_judgement": (
                'The tier-2 companion of the Category B tier-1 site in the same function. MEASURED '
                'over every module under src/: no product module calls admission_faults. It believes '
                'any object carrying the attribute -- admission_faults(Liar()) == () -- so the blast '
                'radius is a carrier believing a claim an object makes about itself. Its callers are '
                'tests/test_admission.py, tests/test_judgement_path_doors.py and '
                'tests/test_collector_runner.py, and THAT LIST IS PROSE: the enumeration the '
                'instrument holds is the `callable` field above.'
            ),
        },
    ),

    (
        'crash_detector.admission',
        'admits.apply_at_the_boundary',
        'COERCION',
        'dict(compiled)',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'OWN_CONSTRUCTION',
            "gates": (
                'crash_detector.engine.config',
                'ConfigSnapshot.__post_init__',
                'ISINSTANCE',
                'isinstance(window, float)',
            ),
            "note": (
                '`compiled` is the dict comprehension `admits` built one scope up.'
            ),
        },
    ),

    (
        'crash_detector.admission',
        'admits.apply_at_the_boundary',
        'COERCION',
        'tuple((p.name for p in parameters))',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'OWN_CONSTRUCTION',
            "gates": (
                'crash_detector.engine.config',
                'ConfigSnapshot.__post_init__',
                'ISINSTANCE',
                'isinstance(window, float)',
            ),
            "note": (
                'tuple() over a generator expression written here, iterating a list built here.'
            ),
        },
    ),

    (
        'crash_detector.admission',
        'admits.apply_at_the_boundary',
        'COERCION',
        'tuple(skipped)',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'OWN_CONSTRUCTION',
            "gates": (
                'crash_detector.engine.config',
                'ConfigSnapshot.__post_init__',
                'ISINSTANCE',
                'isinstance(window, float)',
            ),
            "note": (
                '`skipped` is a list built in _signature_parameters and returned.'
            ),
        },
    ),

    (
        'crash_detector.admission',
        'admits.apply_at_the_boundary.door',
        'ARITH',
        "f'{entry_point.__qualname__} is a FAULTED door and every call to it is refused. ' + ' '.join(faults)",
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'OWN_CONSTRUCTION',
            "gates": (
                'crash_detector.engine.config',
                'ConfigSnapshot.__post_init__',
                'ISINSTANCE',
                'isinstance(window, float)',
            ),
            "note": (
                'str.__add__ between two strings this scope built. It composes a REFUSAL MESSAGE and '
                'decides nothing; the refusal itself was decided by `faults` two lines up.'
            ),
        },
    ),

    (
        'crash_detector.admission',
        'admits.apply_at_the_boundary.door',
        'IDENTITY',
        'refusal is not None',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'SOURCE_DECLARATION',
            "gates": (
                'crash_detector.engine.config',
                'ConfigSnapshot.__post_init__',
                'ISINSTANCE',
                'isinstance(window, float)',
            ),
            "finding": 'CD-F-0002',
            "note": (
                "Identity is not delegable, but the VALUE compared is whatever the declaration's "
                'refusal() returned, and F-06-R measured an _Admission SUBCLASS whose refusal returns '
                "None and whose describe() reports 'exactly PanelRow'. The declaration is source- "
                'written, so the origin is SOURCE_DECLARATION and the finding is named rather than '
                'the site being called clean.'
            ),
        },
    ),

    (
        'crash_detector.admission',
        'admits.apply_at_the_boundary.door',
        'MEMBERSHIP',
        'name not in bound.arguments',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'CALLER_SUPPLIED',
            "gates": (
                'crash_detector.engine.config',
                'ConfigSnapshot.__post_init__',
                'ISINSTANCE',
                'isinstance(window, float)',
            ),
            "finding": 'CD-F-0001',
            "note": (
                '`bound.arguments` is a dict inspect built, but its keys and `name` are strings taken '
                'from a caller-influenced signature, and dict membership is their __hash__ and '
                '__eq__.'
            ),
        },
    ),

    (
        'crash_detector.admission',
        'admits.apply_at_the_boundary.door',
        'TRUTHINESS',
        'faults',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'OWN_CONSTRUCTION',
            "gates": (
                'crash_detector.engine.config',
                'ConfigSnapshot.__post_init__',
                'ISINSTANCE',
                'isinstance(window, float)',
            ),
            "note": (
                'tuple.__bool__ on the tuple _faults built. **THIS IS THE WHOLE OF THE FAULTED-DOOR '
                'REFUSAL** and it is one of the few operands in this module nothing outside it can '
                'reach.'
            ),
        },
    ),

    (
        'crash_detector.admission',
        'declared_admissions',
        'COERCION',
        'dict(getattr(door, ADMITS_ATTRIBUTE, {}))',
    ): (
        "CARRIER_ONLY",
        {
            "callable": 'declared_admissions',
            "why_it_is_not_product_judgement": (
                'As admission_faults. MEASURED: no module under src/ calls it. '
                "declared_admissions(Liar()) returns {'x': 'whatever'} -- it believes any object "
                'carrying the attribute.'
            ),
        },
    ),

    (
        'crash_detector.admission',
        'each_of',
        'TRUTHINESS',
        'not isinstance(within, tuple) or not within',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'SOURCE_DECLARATION',
            "gates": (
                'crash_detector.engine.config',
                'ConfigSnapshot.__post_init__',
                'ISINSTANCE',
                'isinstance(window, float)',
            ),
            "finding": 'CD-F-0002',
            "note": (
                "`within` is source-written at the declaration. `not within` is the supplied object's "
                '__bool__/__len__: F-06-R measured a tuple subclass whose __iter__ yields something '
                'other than what repr and len show.'
            ),
        },
    ),

    (
        'crash_detector.admission',
        'each_of',
        'TRUTHINESS',
        'within',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'SOURCE_DECLARATION',
            "gates": (
                'crash_detector.engine.config',
                'ConfigSnapshot.__post_init__',
                'ISINSTANCE',
                'isinstance(window, float)',
            ),
            "finding": 'CD-F-0002',
            "note": (
                'As above, the other arm of the same guard.'
            ),
        },
    ),


    # --- crash_detector.establishment: 17 distinct tier-2 site keys, ALL declared. --- #
    (
        'crash_detector.establishment',
        '_declared_field_list',
        'COERCION',
        'tuple((field.name for field in dataclasses.fields(cls)))',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'CALLER_SUPPLIED',
            "gates": (
                'crash_detector.engine.config',
                'DialSpec.__post_init__',
                'DUCK',
                'getattr(self, field_name)',
            ),
            "finding": 'CD-F-0004',
            "note": (
                '`cls` is caller-supplied: `establishes` is PUBLIC and in __all__ and ordinary in- '
                'process code decorates its own class. RE-MEASURED BY THIS SEAT on a pristine git '
                'archive extraction: decoration of a caller-authored class SUCCEEDS.'
            ),
        },
    ),

    (
        'crash_detector.establishment',
        '_declared_field_list',
        'COERCION',
        "tuple((name for name, field in getattr(cls, '__dataclass_fields__', {}).items() if getattr(field._field_type, 'name', '') == '_FIELD_INITVAR'))",
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'CALLER_SUPPLIED',
            "gates": (
                'crash_detector.engine.config',
                'DialSpec.__post_init__',
                'DUCK',
                'getattr(self, field_name)',
            ),
            "finding": 'CD-F-0004',
            "note": (
                'Iterates a mapping read straight off a caller-supplied class object. RE-MEASURED: a '
                'forged __dataclass_fields__ entry is iterated without complaint.'
            ),
        },
    ),

    (
        'crash_detector.establishment',
        '_declared_field_list',
        'COMPARE',
        "getattr(field._field_type, 'name', '') == '_FIELD_INITVAR'",
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'CALLER_SUPPLIED',
            "gates": (
                'crash_detector.engine.config',
                'DialSpec.__post_init__',
                'DUCK',
                'getattr(self, field_name)',
            ),
            "finding": 'CD-F-0004',
            "note": (
                "RE-MEASURED: a forged _field_type.name of '_FIELD_INITVAR' STEERS the InitVar "
                'refusal from caller-written data -- _declared_field_list(ForgedCls) returned '
                "initvars=('x',)."
            ),
        },
    ),

    (
        'crash_detector.establishment',
        '_faults',
        'COERCION',
        'tuple(found)',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'OWN_CONSTRUCTION',
            "gates": (
                'crash_detector.engine.config',
                'DialSpec.__post_init__',
                'DUCK',
                'getattr(self, field_name)',
            ),
            "note": (
                '`found` is a list built in this scope.'
            ),
        },
    ),

    (
        'crash_detector.establishment',
        '_faults',
        'MEMBERSHIP',
        'name not in declared',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'CALLER_SUPPLIED',
            "gates": (
                'crash_detector.engine.config',
                'DialSpec.__post_init__',
                'DUCK',
                'getattr(self, field_name)',
            ),
            "finding": 'CD-F-0004',
            "note": (
                '`name` iterates initvars and field_names, both derived from the caller-supplied '
                "class's __dataclass_fields__; the membership is those strings' __hash__ and __eq__."
            ),
        },
    ),

    (
        'crash_detector.establishment',
        '_faults',
        'MEMBERSHIP',
        'name not in field_names',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'CALLER_SUPPLIED',
            "gates": (
                'crash_detector.engine.config',
                'DialSpec.__post_init__',
                'DUCK',
                'getattr(self, field_name)',
            ),
            "finding": 'CD-F-0004',
            "note": (
                'The right operand is caller-derived. A field_names tuple steered by a forged field '
                'list decides which declarations are reported as adrift.'
            ),
        },
    ),

    (
        'crash_detector.establishment',
        'declared_establishment',
        'COERCION',
        'dict(_DECLARATIONS.get(cls, ({}, (), ()))[0])',
    ): (
        "CARRIER_ONLY",
        {
            "callable": 'declared_establishment',
            "why_it_is_not_product_judgement": (
                'MEASURED over every module under src/: no product module calls it. It is one of the '
                "introspection surfaces CD-PL-F104's consequence arm reads, which is why its being "
                'carrier-only is recorded here and not left implicit.'
            ),
        },
    ),

    (
        'crash_detector.establishment',
        'establishes.apply_at_the_boundary',
        'COERCION',
        'dict(compiled)',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'OWN_CONSTRUCTION',
            "gates": (
                'crash_detector.engine.config',
                'DialSpec.__post_init__',
                'DUCK',
                'getattr(self, field_name)',
            ),
            "note": (
                '`compiled` is the dict comprehension `establishes` built one scope up.'
            ),
        },
    ),

    (
        'crash_detector.establishment',
        'establishes.apply_at_the_boundary',
        'TRUTHINESS',
        'not dataclasses.is_dataclass(cls)',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'CALLER_SUPPLIED',
            "gates": (
                'crash_detector.engine.config',
                'DialSpec.__post_init__',
                'DUCK',
                'getattr(self, field_name)',
            ),
            "finding": 'CD-F-0004',
            "note": (
                '**THE GATE, AND IT ADMITS A NON-DATACLASS.** dataclasses.is_dataclass is itself a '
                'hasattr probe. RE-MEASURED BY THIS SEAT: a plain class carrying __dataclass_fields__ '
                '= {} passes it and establishes()(Hostile) SUCCEEDS, where the shipped docstring says '
                'it :raises EstablishmentFault:. The caller then holds a FORGED GOVERNED TYPE.'
            ),
        },
    ),

    (
        'crash_detector.establishment',
        'establishes.apply_at_the_boundary.__init__',
        'ARITH',
        "f'{cls.__qualname__} is a FAULTED type and every construction of it is refused. ' + ' '.join(faults)",
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'OWN_CONSTRUCTION',
            "gates": (
                'crash_detector.engine.config',
                'DialSpec.__post_init__',
                'DUCK',
                'getattr(self, field_name)',
            ),
            "note": (
                'str.__add__ between two strings this scope built; it composes a message and decides '
                'nothing.'
            ),
        },
    ),

    (
        'crash_detector.establishment',
        'establishes.apply_at_the_boundary.__init__',
        'IDENTITY',
        'refusal is not None',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'SOURCE_DECLARATION',
            "gates": (
                'crash_detector.engine.config',
                'DialSpec.__post_init__',
                'DUCK',
                'getattr(self, field_name)',
            ),
            "finding": 'CD-F-0002',
            "note": (
                "As the admission door's sibling site: identity is not delegable, but the value came "
                'from a declaration compiled through crash_detector.admission._compile, which admits '
                '_Admission subclasses.'
            ),
        },
    ),

    (
        'crash_detector.establishment',
        'establishes.apply_at_the_boundary.__init__',
        'IDENTITY',
        'value is _ABSENT',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'MODULE_CONSTANT',
            "gates": (
                'crash_detector.engine.config',
                'DialSpec.__post_init__',
                'DUCK',
                'getattr(self, field_name)',
            ),
            "note": (
                "Identity against this module's own sentinel object. Nothing a caller supplies can be "
                'it.'
            ),
        },
    ),

    (
        'crash_detector.establishment',
        'establishes.apply_at_the_boundary.__init__',
        'TRUTHINESS',
        'faults',
    ): (
        "UPSTREAM_OF_THE_PATH",
        {
            "operand_origin": 'OWN_CONSTRUCTION',
            "gates": (
                'crash_detector.engine.config',
                'DialSpec.__post_init__',
                'DUCK',
                'getattr(self, field_name)',
            ),
            "note": (
                'tuple.__bool__ on the tuple _faults built.'
            ),
        },
    ),

    (
        'crash_detector.establishment',
        'establishment_faults',
        'COERCION',
        'tuple(_DECLARATIONS.get(cls, ({}, (), ()))[1])',
    ): (
        "CARRIER_ONLY",
        {
            "callable": 'establishment_faults',
            "why_it_is_not_product_judgement": (
                "MEASURED: no module under src/ calls it. **CD-PL-F104's consequence arm reads this "
                'function**, and this row is where the record says that the surface reporting the '
                "forged type's zero faults is one no product module consults."
            ),
        },
    ),

    (
        'crash_detector.establishment',
        'establishment_field_list',
        'COERCION',
        'tuple(_DECLARATIONS.get(cls, ({}, (), ()))[2])',
    ): (
        "CARRIER_ONLY",
        {
            "callable": 'establishment_field_list',
            "why_it_is_not_product_judgement": (
                'MEASURED: no module under src/ calls it.'
            ),
        },
    ),

    (
        'crash_detector.establishment',
        'governed_types',
        'COERCION',
        'tuple(_DECLARATIONS)',
    ): (
        "CARRIER_ONLY",
        {
            "callable": 'governed_types',
            "why_it_is_not_product_judgement": (
                "MEASURED: no module under src/ calls it. **CD-PL-F104's headline consequence -- "
                "'Hostile ENTERS governed_types()' -- is a statement about a surface only carriers "
                "read.** Re-measured and reproduced by this seat; recorded here so the finding's "
                'reach is neither overstated nor lost.'
            ),
        },
    ),

    (
        'crash_detector.establishment',
        'is_establishing_type',
        'MEMBERSHIP',
        'cls in _DECLARATIONS',
    ): (
        "CARRIER_ONLY",
        {
            "callable": 'is_establishing_type',
            "why_it_is_not_product_judgement": (
                'MEASURED: no module under src/ calls it. Note the membership is over CLASS OBJECTS, '
                "so a metaclass defining __eq__ and __hash__ (F-06-D's lever) makes this function lie "
                '-- carrier credibility, not product judgement, which is exactly what the word '
                'asserts.'
            ),
        },
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
        "ObservationRecord. THE EXCEPTION THIS LINE USED TO DECLARE — 'the one exception is "
        "declared below under model' — IS WITHDRAWN, BECAUSE THE ROUTE IT NAMED NO LONGER "
        "EXISTS: `spec.contribution_model.compute(payloads)` was a call on a caller-supplied "
        "object and is now `compute(model, payloads)`, an engine-owned function over a spec "
        "the engine resolved from a NAME (BP-AMENDMENT-0001 §C).",
    ),
    "crash_detector.engine.config": (
        "ESTABLISHED",
        "dial_id and both input-id tuples are re-established before the membership, "
        "duplicate and overlap tests; specs and both registries are admitted by exact type; "
        "the window's usability is decided by StalenessWindow, which admits by exact type; "
        "model_ref is re-established through own_model_id, so which registry row a dial "
        "resolves to is decided by str.__eq__ between two strings this package built.",
    ),
    "crash_detector.engine.model": (
        "ESTABLISHED",
        "*** THIS DISPOSITION WAS OUT_OF_BOUND AND IS NOW ESTABLISHED. THE PREVIOUS TEXT IS "
        "QUOTED SO A READER OF THE DIFF SEES THE TRANSITION RATHER THAN INFERRING IT: "
        "'ContributionModel is a caller-supplied object whose compute() returns the number a "
        "dial publishes, and one stateful instance injected into BOTH DialSpecs makes the "
        "monetary dial publish the mean of the two (CD-ENG-WO2R2-F03, replicated by the "
        "Project Lead as PL-Z4) … NOT PROVED TO BE CARRIED ANYWHERE.' *** "
        "It is withdrawn because the ROUTE is gone, not because a guard was added: "
        "PO-DECISIONS-0004 ruled the §7 architectural review it deferred to, and "
        "BP-AMENDMENT-0001 §C deletes ContributionModel and CONTRIBUTION_MODELS outright. "
        "No field on this path holds an object or a callable — model_id and dial_id through "
        "own_model_id/own_str, both id tuples elementwise through own_str, mapping by exact "
        "MappingKind membership, parameters and provenance by exact type — so there is no "
        "judgement here delegated to an object this system did not construct. "
        "WHAT IS STILL NOT CLOSED, AND IS DECLARED RATHER THAN CARRIED: a mapping member's "
        "IMPLEMENTATION is code and can be wrong (BLUEPRINT §17 CD-BP-002), and this module "
        "establishes a spec without establishing that the spec's account of itself is TRUE "
        "— that adjudication is CD-D-005 and is the Product Owner's. Neither is a delegated "
        "judgement, which is what this sweep measures, and both are "
        "NOT PROVED TO BE CARRIED ANYWHERE.",
    ),
    "crash_detector.engine.mapping": (
        "EXACT",
        "The executor. It admits its spec by `type(spec) is not ModelSpec` and reads the "
        "MAPPING SLOT rather than trusting the constructor that filled it — "
        "`type(spec.mapping) is not MappingKind` — because object.__setattr__ walks past "
        "frozen and the value is read at the moment it selects a branch. Payload keys are "
        "rebuilt through own_str and both dict levels are copied into dicts this module "
        "built, so no supplied mapping's __getitem__, keys or __eq__ runs while a mapping "
        "executes. It dispatches on an enum member by identity (`is`), not by value or by "
        "name. It holds no module-level mutable state, so nothing carries between dials or "
        "between runs. WO-2 ships one member and it REFUSES: no magnitude is returned on "
        "any path in this module. "
        "DECLARED, NOT CARRIED: these admissions are written in the function BODY and not "
        "yet derived from its signature — BP-AMENDMENT-0001 §D's `admits` mechanism is a "
        "later increment of WO-2R3 — so an edit to the body removes them, which is "
        "CD-ASR-F03's own shape. NOT PROVED TO BE CARRIED ANYWHERE. What does NOT depend on "
        "this body is the §C claim itself: no field can hold code, so with every line here "
        "deleted there is still no caller-supplied callable to execute.",
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
