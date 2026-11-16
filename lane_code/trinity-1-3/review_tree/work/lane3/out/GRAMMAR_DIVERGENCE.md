# Grammar divergence

The shared validator is byte-identical to the supplied copy; its binding is `work/tree_r1/student_pilot/r2_grammar.py:SHARED_SHA256`. The wrapper calls `validate_trace`, preserves native event masking and retains the stricter explicit-label dialect needed by build-1 fixtures. The original shared test file runs unchanged through an import-path adapter in `work/build2/run_tests.py`.

**duplicate object across lines**

```text
Locate: the chair is seen in frame 2.
Locate: the chair is seen in frame 3.
Relate: the chair is to the right.
```

Shared result: accept. Tree wrapper: refuse.

**explicit-label relation without Locate**

```text
Relate: the chair is to the right.
```

Shared result: accept. Tree wrapper: refuse.

**frame stated in seconds**

```text
The chair is seen in frame 2 seconds.
```

Shared result: accept. Tree wrapper: refuse.

**single-line count before a list**

```text
Locate: chair a is seen in frame 1.
Locate: chair b is seen in frame 2.
Step: list [chair a; chair b]; count = 3.
```

Shared result: number_not_allowed. Tree wrapper: refuse.

The explicit-label no-Locate refusal is a compatibility restriction, not a new requirement on the shared prose dialect. Native call parameters are checked by the event parser, then represented as `<call>` for lexical validation. For example, `<gap rule="box_grid_5cm">` after inline response tags otherwise exposes the rule-name digit to the shared quantity checker. The original event bytes, response spans and training masks remain unchanged.

The wrapper also refuses a response without a corresponding masked event, a later response used to justify an earlier number, a call after a failed response, and deployed-selector training responses. These checks need native event structure, which the shared lexical API does not own. Examples and mutations are in `work/tree_r1/tests/test_r2_families.py`, `test_r2_refusals.py` and `test_r2_edges.py`.
