All tests ran on CPU with `/scratch/jjyeung/envs/p1cpu/bin/python -I -s`. No GPU, network, SSH or Git operation ran.

| Check | Result | Evidence |
|---|---|---|
| Existing kit suite | 40 passed | TEST_BASELINE.log |
| Variant suite | 19 passed | TEST_VARIANTS.log |
| Repaired baseline pricing | 152 captures; 19,853 rows | baseline_repaired/COMPLETE.json |
| Baseline prediction parity | Per-item file byte-identical; full route JSON equal | baseline_repaired/VALIDATION.json |
| Independent diagnostics audit | All 484 capture/name groups agree | baseline_repaired/VALIDATION.json |
| GT grant executor parity | 6,846 GT/ever-proposed endpoint rows; zero prediction or score differences | analysis/REPRICE_PARITY.json |
| Ground-truth audit | 93 captures; 1,056 operand instances; 224 misses | analysis/AUDIT_COMPLETE.json |
| Numerical case review | 30 stratified cases, no pixel inspection | CASE_READS_30.jsonl |
| Public CLI dry run | Dense plan produces its bound manifest and estimate without inference | DRY_RUN.log |

The 19 variant tests cover source-score preservation, duplicate suppression, crop-to-parent mask placement, landscape/portrait tile coverage, dense subset parity and refusal, frozen prompt rules, diagnostic-group precedence, prompt relationships, absent-frame gating, the NumPy-integer serialization regression, dense cache resume, zero-inference linker reuse, pricing resume, alias/tile inference adapters, STOP/time/disk/halt boundaries, contract tampering, complete student-gated tile inference on synthetic frames, stale/incomplete presence refusal, the real HF backend’s request schema, and the stub presence reader’s resume behavior. Several tests exercise more than one assertion or stage.

The 40 baseline tests cover the existing route-table pairing and room bootstrap, invalid/stub-score refusal, cache binding, frame hashes, retention parity, overlapping masks, count merging, portrait rasters, and the stall watchdog. The watchdog test terminates only its own disposable test child.

The tests retain their temporary fixtures under work/tests_runs. Synthetic candidates remain marked as stubs and cannot enter deployment route tables. The student-gate fixture uses explicit synthetic presence metadata; its resulting cache remains marked as a stub.

The GPU adapters have not loaded a real checkpoint in this lane. Actual CUDA memory, SAM numerical subset parity, student preprocessing parity, runtime and mask improvements must be checked on the first real GPU capture. The delivered runner refuses mismatched frames, source receipts, cache bindings and dense subsets instead of silently accepting a different baseline. True occlusion and the semantic validity of incomplete annotations remain unverified.
