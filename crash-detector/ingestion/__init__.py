"""Real-data ingestion for the ratified indicator mapping (CERBERUS WO-1.2b).

This is the ``cd-collectors`` side of BLUEPRINT §5: it fetches and records, it never
computes. It lives OUTSIDE ``src/crash_detector`` on purpose — the application tree opens
no socket and a test (``test_nothing_in_the_application_tree_imports_a_network_module``)
asserts it. The network-bearing code is here; the fail-safe core in ``src/`` is unchanged
and is driven through its own ``collect()`` runner, so every attempt still writes a row,
and only a schema-conforming ``OK`` outcome can ever become a reading.

Import route: ``PYTHONPATH=src:.`` from ``crash-detector/``.
"""
