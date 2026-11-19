Build 1b is complete. All 46 unittest methods pass. The standard-library trace run covers 413/414 executable source lines (99.76%). The public validate_trace, validate_row, Violation, RULES, and CLI interfaces remain unchanged.

The implementation is [work/trace_grammar.py](../work/trace_grammar.py). Tests are in [work/test_trace_grammar.py](../work/test_trace_grammar.py), and [work/run_coverage.py](../work/run_coverage.py) measures coverage without third-party packages.

| Fix | Behavior and regression evidence |
|---|---|
| stated_estimate | Frame indices and Step labels never count as estimates. The webcam/frame 20 example passes with answer 20. Frame lists remain subject to exhaustive_frames; invalid frames and labels retain their own violations. “It is about 20 across.” still fails, including when frame 20 occurs on the same line. |
| number_word | Fraction quantities such as a fifth, a tenth, three quarters, two thirds, one fifth, and a half of fail. A cardinal constant in the question cannot license an entire fractional phrase. Ordinal order and halfway between objects pass; halfway to a meter fails. |
| letter_restatement | Explicit inline choices fail in direct rows and in program rows before a Call. The same program choices pass after a Call. TV, Bob, pronoun I, and quoted question strings do not trigger the rule. Mixed lines still undergo number-word checks. |

The five Build 1b regression methods are test_build1b_estimate_structural_numbers, test_build1b_fraction_quantities, test_build1b_fraction_position_and_ordinals, test_build1b_inline_choices, and test_build1b_choice_names_and_quotes. The required failing-before run executed all 46 methods against the unmodified validator and produced 22 failing assertions, including failures for each requested fix. The passing-after run executed the same 46 methods successfully. Both runs are retained in [TEST_build1.txt](TEST_build1.txt).

The full suite also passes all nine required fixtures, mutations for all 15 rule IDs, the 15 Appendix A rejection fixtures, arithmetic and provenance checks, layout and type inference checks, and CLI streaming tests. CLI tests use in-memory streams and cover malformed rows, limits, bounded oversized-row handling, and per-rule examples.

Executed test commands on trinity-1-13:

```text
/scratch/jjyeung/envs/planner_local_v1/bin/python -I -s -B work/test_trace_grammar.py
/scratch/jjyeung/envs/planner_local_v1/bin/python -I -s -B work/run_coverage.py
```

The final ordinary test run reports:

```text
Ran 46 tests in 0.153s

OK
```

The coverage run reports:

```text
Ran 46 tests in 0.775s

OK
trace_grammar.py: 413/414 executable lines covered (99.76%)
Missing executable lines: 511
```

[Coverage output](COVERAGE_trace_grammar.txt) records the full traced test run. Coverage uses stdlib trace execution counts and its executable-line finder, excluding synthetic module line 0. Line 511 is the __main__ dispatch. The tests invoke main directly; no separate CLI subprocess smoke test was run for Build 1b. No pytest or coverage package was used.

Known limits: This validator checks lexical evidence and provenance. It cannot verify visual grounding, instance identity, tool authenticity, or dimensional correctness. Entity matching, fraction recognition, spatial uses of halfway, and option-choice cues remain lexical heuristics. Quoted strings containing a question mark or matching the supplied question are excluded from choice detection. Unfamiliar paraphrases may fail or escape detection. Numeric bounds, count provenance, question constants, and the special three-dimensions exception retain their existing checks. [The design record](DESIGN_RECORD_build1_validator.md) documents these choices.

Only the permitted implementation, test, report, design-record, and test-output paths were written. No SSH, GPU, Git, network, other agent, or deletion operation was used. The coverage runner required no change.

The failing-before/passing-after comparison is retained because the user explicitly requires that evidence.

SHA-256 of work/trace_grammar.py: `49e814ebfa1a4a4b3b1dc865c4ee715ae65b6f80aa3d5c8d28e5c649f6d1a635`.
