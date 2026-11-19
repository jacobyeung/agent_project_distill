# sb_f64fix3: the two required edits from review sb_f64rev3

Both edits are in, and every rerun gives the required result. `token_audit.summarize` now ranks failed rows that have a known token count among the `longest` candidates, and `mem_pilot.check_audit` still refuses every failed audit, tokenless fetch failures included. `out/FIX2_REPORT.md` now gives every path in full and every owner, and it writes "MISSING: orchestrator assigns" wherever no owner or path is known. The work ran on CPU only on trinity-1-18. Production inputs remain MISSING.

**Edit 2** (`kit/scripts/token_audit.py:314-316`). A record now becomes a candidate when its fields are complete and `tokens` is an integer. Each candidate also carries its `check_row`, so a failed candidate stays visible. A fetch failure has no token count, so it stays out, and `mem_pilot` refuses it as both failed and omitted. The `check_audit` docstring (`kit/scripts/mem_pilot.py:59-62`) now gives the trainer's abort as the only reason for refusal, since the longest list no longer omits every failed row.

**Tests** (`kit/tests/test_pilot_gate.py:91-128`, over the real dry-run encodes). The new test fails three rows, and each one refuses the pilot:
- A routing `check_row` failure ranks among the candidates, with 0 rows omitted.
- A vqa `check_row` failure, lengthened 100 tokens past the rest of its stream, ranks first and holds the audit's maximum, with 0 rows omitted.
- A tokenless pose fetch failure is left out, with 1 row omitted.
The ceiling test also asserts that both of its ceiling rows rank among the candidates. Against fix2's `token_audit.py`, three subtests fail: both `check_row` cases and the encoded ceiling row (`out/fix3/old_token_audit.log`).

**Reruns** (`bash work/scripts/run_fix3_checks.sh`; results in `out/fix3/`).
- The 49 kit tests pass in the workspace (`kit_tests.log`), under the reviewer's runner (`kit_review.json`) and from the extracted archive with its own reader root (`out/fix3_extract_tests.log`).
- Both regressions run 109 tests with 0 failures and the same single error, the MISSING `/scratch/jjyeung/orch_cd/derivgen/review_pool/POOL.jsonl`.
- I rehosted the reviewer's matrices in `work/review3/` and changed only their kit, fixture and output paths (`harness.diff`). `pilot_gate_matrix` and `builder_matrix` meet every required behavior. The failed routing row now ranks in `longest`, with all 16 rows listed, and the audit still refuses.
- `mutation_check` passes all 7 controls and kills 5 of 5 mutants. Its 9,400-token failed row now ranks first.

**Edit 3** (the OPEN table in `out/FIX2_REPORT.md`). The table now gives every path in full and drops the `P` and `CFG` shorthand; `W` now reads lane tree_rebuild (W). The pool producer, the pilot's output directory and operator, and the item 8 evidence paths and operators read "MISSING: orchestrator assigns". The config row now reads "absent or null": `r2_sampling`, `preparation` and the pose, routing and pointing store hashes are absent, and three `r1_training` pins are null. The rest of that report still describes fix2's code.

**Deliverable.** `out/sb_f64fix3.tar` has sha256 `497538448537a699cab0f77ef7b3ef1825d95e6f2b10b8926aa4edc770996ef2` (`out/sb_f64fix3.tar.sha256`). Compared with sb_f64fix2, the kit changes in three files and `SHA256SUMS`, whose 45 entries all verify (`out/fix3/kit.diff`). Fix2's dry-run store embedded fix2 frame paths, so I renamed it to `work/dryrun_sb_f64fix2`; nothing was deleted.
