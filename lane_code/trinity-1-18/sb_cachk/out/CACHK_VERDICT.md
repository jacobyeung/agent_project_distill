GO — the patched kit is ready for the guarded GPU pass; GPU performance and carry bars remain unmeasured.
Part 1 used the archive's unchanged code; file:line references below refer to work/extract/kit_v2. Details: out/check/PART1_VERDICT.md.
1. DONE — mc_track_io.py:38; mc_price.py:33,87. test_object_record_positive_empty_carries passes; the empty stub counts 760 added members and zero correct.
2. DONE — mc_phrase.py:38,58,91; mc_seeds.py:64. Actual-schema/fallback tests pass; contract_audit finds zero mismatches among 320 phrase rows; seed masks match on 209/209 captures.
3. DONE — mc_preflight.py:14; mc_staging.py:27. test_preflight_phrase_hash_against_seed_provenance and preflight pass with the producer's folds, decision and bars hashes.
4. DONE — mc_track_pass.py:59,209,221,294; launch_gpu.sh:60. Contract audit rejects both KILLED launches; test_main_saves_budget_on_exception and binding/ledger tests pass.
5. DONE — mc_track_pass.py:83,105,310,356. test_units_are_arm_major, test_unit_cost_counts_its_own_embedding and projection/drop tests pass.
6. DONE — gpu_inner.sh:9,14; mc_track_pass.py:136. Cache/timing tests pass; the four-column second-reading probe refuses 1,025 MiB; launcher tests preserve the remaining timeout.
7. DONE — mc_staging.py:27,71; launch_gpu.sh:50. Self-contained staging/vendor tests and CPU preflight pass. The original receipt totals 14,924,708,860 bytes; patched staging totals 14,924,717,613 bytes (14.925 GB; 13.900 GiB).
8. DONE — mc_population.py:16,40; mc_summary.py:58,121,166. Population/completeness tests and check_receipts.py confirm 204 captures/1,012 decision rows; 209/1,037 are reported beside them.
9. DONE — mc_summary.py:121,133,148,214. test_frame_spacing_by_dataset and the reproduced summary cover all three datasets, mask measurements and native frame spacing.

Archive: python -B work/verify_archive.py confirms all 1,560 packaged kit_v2/in/out files match the copied workspace, with SHA256 per file; source tar hash c5fbb8b12f31b1f09931821cf8ac39c6edb5b8b477db0f7135c3521f5f01b31e matches its receipt.
Tests: bash work/review/review_run.sh p1cpu tests_run.py gives 74 passes after regenerating location-specific staging; the patched pytest command in out/check/EVIDENCE.json gives 109 passes, including 35 guard tests.
Reproduction: bash work/review/reproduce.sh reproduces step 0 and both original stubs, then fails because it omits the new empty stub. bash work/review/complete_checks.sh adds that fixture and population generation; all nine parity checks pass.
Step 0 gives 390/538 = 72.4907% at tau 0.25 and 2,310/2,310 predicate cases. Seed-stub A0 parity is 1,037/1,037 (56.7695); raster parity is 1,037/1,037 for both A2 (73.9730) and fused_cf (78.6210). Frame checks pass on 209 captures/13,376 files.
Contracts: bash work/review/review_run.sh p1cpu contract_audit.py and contract_audit_4col.py reject KILLED overrides and the busy second reading. Their summary_required_* fields are legacy literals; the effective counts are independently verified.
Exclusions: python -B work/check_receipts.py verifies R0 bdb5d402, dev-S1 969cdb56, BENCH v2 3119aa4a, withheld-80 634820b4 and teacher_k1 4d4736cf (nested authority pin). Only withheld-80 hits: five captures/four rooms/25 rows, excluded from decisions.

Guard: out/GUARD.patch and kit_v2/mc_score_guard.py:10,13 bind the unchanged edff8724b27328f6874b4adb0dd93727cc70fdfd4ddf2fb301cf572a46ceaaf4 freeze hash. Every scoring/summary entry and launcher refuses missing/tampered bars or existing output scores before writing.
Guard tests check nonzero exits and identical output snapshots; pricing also rejects per-capture score files. The launcher checks before creating its directory/logs. Patch application reproduces all 32 patched kit files exactly (out/check/PATCH_APPLY.json).
Fresh-output validation: bash work/patched_check.sh reproduces every stub parity check and passes preflight. A final-summary code check succeeds once; repeating it refuses without changing any output (out/check/REAL_RERUN_REFUSAL.json). Use fresh scoring destinations.
Staging: PYTHONNOUSERSITE=1 bash kit_v2/run_cpu.sh sam3 ../work/import_audit.py builds the model with zero attempted /home or /data* accesses and no nonlocal modules. The launcher already sets this variable; CPU checks must set it too. The CPU-only tower adaptation is not a GPU dependency.
Memory: bash kit_v2/run_cpu.sh sam3 ../work/static_check.py counts 3,449,659,104 tensor bytes across 1,465 keys. Batch one and 64 cached frames give an estimated 7.410 GB including assumed activations/context. A 24 GB native-bf16 card is plausible; CUDA peak remains MISSING.
GPU need: the same static_check.py computes 0.80031 GPU-h for S_A0/D64 and 2.45160 GPU-h for all arms. The 2.0 h cumulative stop keeps the first three arms at assumed rates (1.98022 h); the first-ten-capture receipt must replace those rates and drop trailing arms as needed.
Launch constraints remain two readings 300 s apart, at most 1,024 MiB occupied, native bf16, pinned local vnice, and timeout at the remaining budget. No GPU, network, SSH, Git or process termination was used. The producer's full-capture CPU step 4 remains PARTIAL.
Delivery: out/sb_cachk.tar contains the patched kit and receipts; out/sb_cachk.tar.sha256 pins the archive. out/check/EVIDENCE.json records commands and input hashes.
