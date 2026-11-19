# GO AFTER FIXES

The CPU gate rejects the required bad audits, but the literal failed-row inclusion requirement and exact-path/owner handoff remain incomplete. Production inputs are still MISSING.

1. **Core gate fix passes.** `mem_pilot.py:72-85` re-derives complete stream counts, refuses every failure/ceiling violation, and accepts tripwire-only rows. Failures beyond both capped lists and forged cached counts also refuse.
2. **Required edit — longest list.** `kit/scripts/token_audit.py:314` still excludes every failed row from `longest`; only `max_tokens` includes their known token counts. No failed audit is accepted, but this does not satisfy the task’s literal “longest-row selection includes failed rows.”
   Include failed records with known token counts in the ranked candidates; continue refusing tokenless fetch failures and all failed audits. Update `kit/tests/test_pilot_gate.py:89-105` to test failed-candidate inclusion and refusal, including a maximum-length failed row. Regenerate checksums/archive after code edits. Owner: kit builder.
3. **Required edit — handoff table.** In `out/FIX2_REPORT.md`, assign the pool producer and exact output paths/operators for items 4 and 8. Those assignments are MISSING; the orchestrator must supply them. Expand each path and owner in the table; `OPEN_ITEMS.md` lists verified input locations and unassigned fields.
   Change “all null” to “absent or null”: `r2_sampling`, `preparation`, and three stream-hash keys are absent. Owner: report author.

**Independent results** (commands run from `/scratch/jjyeung/orch_n30/sb_f64rev3`):
- `bash run_cpu.sh static_check.py`: archive SHA256 `472d7775378a82ee365f11aa531f25b065129e339be1a3157abe1b85d24c6f89`; all 58 archive files match disk and all 45 checksum entries pass. `out/static_review.json` binds inputs.
- The complete kit diff changes only `scripts/mem_pilot.py`, new `tests/test_pilot_gate.py`, and `SHA256SUMS`. Outside the kit, only the two reviewed wrapper paths change; regression code is identical. See `out/tree.diff`.
- `bash run_cpu.sh kit_check.py`: 49 tests pass, with no skips (`out/kit_review.json`).
- `bash run_cpu.sh regression_check.py baseline` and `bash run_cpu.sh regression_check.py patched`: each runs 109 tests, zero failures, one error for MISSING `/scratch/jjyeung/orch_cd/derivgen/review_pool/POOL.jsonl`; neither suite is fully passing.
- `bash run_cpu.sh pilot_gate_matrix.py`: all three reviewer controls pass; passing/tripwire audits accept and a failed-check audit refuses (`out/pilot_gate_matrix.json`).
- `bash run_cpu.sh builder_matrix.py`: all four builder controls pass, including flag-only ceiling refusal (`out/builder_matrix.json`).
- `bash run_cpu.sh mutation_check.py`: 5/5 mutants killed: remove failed counts, remove ceiling counts, reject tripwires, disable refusal, and trust cached counts. Seven independent controls pass on the unmutated gate (`out/mutation_review.json`).
- The same command exercises eight real-auditor ceiling cases; all refuse. `token_audit.audit:119,128-130` and trainer `check_row:1326-1330` use the same ceiling, before stream-specific returns. For normal two-dimensional batches, a real audit cannot emit `over_ceiling=true` with `check_row=ok`.
- `summarize` does mark the synthetic flag-only record launch-ready, but the pilot gate rejects it. This is not a real-audit bypass.

No reviewed files were edited. `out/OPEN_ITEMS.md` preserves exact production input paths and known owners; unassigned evidence paths/owners remain MISSING. Actual first batches, full token audit, GPU pilot, and reader evidence remain prerequisites for launch.
`bash run_cpu.sh finalize_review.py` validates these results and writes `out/REVIEW_INPUTS.json`; every review evidence JSON carries input SHA256s. `out/REVIEW_METHOD.md` records test scope and adaptations.
