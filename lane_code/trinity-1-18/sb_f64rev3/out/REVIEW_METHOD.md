The review ran on trinity-1-18, used CPU only, and wrote review artifacts only inside this workspace. The wrapper disables CUDA and network-dependent model loading, sets eight numerical-library threads and nice level 10, and caps virtual memory below 40 GB. No Git, SSH, GPU execution, or process termination was used.

`kit_check.py` adapts the retained reviewer runner to the reviewed kit and adds its new test module. `regression_check.py` retains both reviewer suites and redirects their writes here. Both runners install write guards and retain temporary directories. Test fixture files keep their native schemas; evidence JSONs in `out/` record input hashes.

`static_check.py` hashes and diffs every kit file and every `work/scripts` file, plus the regression script and wrapper. It checks every archive file against disk and every kit checksum. Generated logs, caches, temporary fixtures, and proof trees are not source-code changes. The archive is inspected without extracting or executing it.

`pilot_gate_matrix.py` retains the reviewer’s three controls and original retained encodes, changing only kit/output paths and provenance. `builder_matrix.py` reruns the builder’s expanded four-case matrix, including its explicitly synthetic flag-only ceiling case. `mutation_check.py` creates explicitly synthetic 300/301-row controls from the retained record schema; these test gate logic, not production sampling or admission. Its eight ceiling checks use the real auditor and trainer check_row with two-dimensional token tensors, four streams, and default/overridden ceilings.

The core refusal fix meets sb_f64rev2’s required code change. The task separately asks that longest-row selection include failed rows. The implementation still excludes failures from the summary’s longest list; it only includes them in per-stream counts and max_tokens, then refuses the audit. This distinction is reported explicitly rather than treating refusal as proof of literal list inclusion. No failed audit reached an accepted plan in the controls.

The OPEN-item assessment distinguishes existing configured paths from unassigned future evidence paths. An unknown path or owner is reported as MISSING. This review makes no production readiness or GPU memory claim.

The comparison to sb_f64fix and the mutation variants is retained because the task explicitly requires these designed comparisons.
