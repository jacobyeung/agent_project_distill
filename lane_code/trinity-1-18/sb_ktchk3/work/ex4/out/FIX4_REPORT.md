The tower-frames kit passes all required CPU checks. No GPU work ran.
Edit 1: code/evaluate_v2.py:25, code/evaluate_v2.py:33, code/evaluate_v2.py:53, code/evaluate_v2.py:120 refuse planted decisions before scoring and update; test_plant_A_decision_with_B_bars and test_plant_B_decision_train_complete pass with unchanged trees.
Edit 2: code/process_guard.py:52 checks A/B captures before H freeze; test_plant_H_freeze_after_model_output refuses both late freezes.
Edit 3: scripts/gpu_environment.sh:48 compares memory numerically; test_gpu_padded_memory_refuses_either_reading rejects all eight padded busy fixtures, and test_gpu_padded_idle_boundary_passes accepts 1,024 MiB.
Edit 4: code/test_kit.py:206 freezes a fresh root inside each loop iteration; test_run_b_persists_added_frame_gain passes PASS, FAIL and MISSING cases.
Regressions: code/test_fix3.py:193 adds the plants and valid A-then-B scoring; code/test_fix3.py:301 adds padded readings.
`bash scripts/cpu.sh code/test_kit.py > out/tests_fix4.log 2>&1`: 68/68 PASS; out/TESTS.json and out/FIX3_PROBES.json record the evidence.
`bash scripts/cpu.sh work/run_fix4_probes.py plant > out/plant_fix4.log 2>&1`: all nine original probes rerun; seven file plants and the forged FREEZE refuse without score writes.
`bash scripts/cpu.sh work/run_fix4_probes.py plant2 > out/plant2_fix4.log 2>&1`: 30/30 required file plants refuse with unchanged trees; the duplicate-row probe refuses; 16/16 real price rows round-trip.
The original synthetic gain comparison and five reviewer-designated informational controls remain diagnostic; both bound B report attacks refuse, and the matching-report control succeeds.
Probe wrappers only redirect result writes into this workspace and record input hashes; out/FIX4_plant.json and out/FIX4_plant2.json retain every result.
`bash scripts/cpu.sh code/dryrun.py > out/dryrun_fix4.log 2>&1`: PASS; 296 captures, 9,472 numbering hashes and 450 camera records.
`bash scripts/cpu.sh work/a0_rerun.py > out/a0_fix4.log 2>&1`: 1,037/1,037 full A0 rows and 209/209 row sets; 1,012/1,012 decision rows and 204/204 row sets match.
`bash scripts/cpu.sh work/diff_fix4.py > out/diff_fix4.log 2>&1`: only code/evaluate_v2.py, code/process_guard.py, scripts/gpu_environment.sh, code/test_kit.py and code/test_fix3.py differ among archived sources.
out/FIX4_SOURCE.diff and out/FIX4_DIFF.json confirm the four trial edits exactly, plus the added tests; configs, inputs, vendor and other delivered scripts are byte-identical to sb_ktfix3.tar.
`bash scripts/cpu.sh work/finalize_fix4.py > out/finalize_fix4.log 2>&1` runs unchanged scripts/finalize_v3.py with only its archive destination redirected to sb_ktfix4.tar.
New code_sha256 for GPU_GO.json: `076c5d87ab581e9b49332f9deaea20991cee2b8d989cd2287d1a6160e2b93e9c`. out/CODE_SHA256.json, out/DRYRUN.json and out/GPU_NEED.json bind this hash.
`bash scripts/cpu.sh work/refresh_stage.py > out/stage_fix4.log 2>&1` refreshes local staging hashes and reuses verified external hashes.
`bash -n scripts/cpu.sh scripts/gpu_environment.sh scripts/run_A.sh scripts/run_B.sh scripts/run_C.sh scripts/run_H.sh` passes.
`bash scripts/cpu.sh work/package_fix4.py` writes out/sb_ktfix4.tar and out/sb_ktfix4.tar.sha256; out/FIX4_MEMBERS.json pins every payload member.
`bash scripts/cpu.sh work/verify_fix4.py` checks the delivery, replay counts, code pins, member hashes, source diff and both unchanged reviewed archives; `sha256sum -c out/sb_ktfix4.tar.sha256` verifies the archive.
MISSING: /scratch/jjyeung/orch_n30/sb_kbox2/heldout_labels.json. GPU_GO.json remains an external authorization; no held-out look was consumed.
