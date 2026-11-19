The tower-frames kit passes CPU validation. All four required edits are implemented; no GPU work ran.
Edit 1: code/process_guard.py:10 counts scored reports and nested BARS/FREEZE files; test_plant_A_report/B_report/C_report/H_report and test_report_guard_pose_and_nested_receipt refuse them.
Edit 1 ordering: code/evaluate_v2.py:76, code/evaluate_v2.py:140, code/evaluate_v2.py:155, code/camera_pricing.py:82 write per-item files before reports; test_per_item_written_before_reports and test_camera_and_heldout_item_order verify interrupted reporting.
Edit 2: code/process_guard.py:27, code/process_guard.py:44 bind BARS.json to current code independently of FREEZE.json; test_plant_A_planted_FREEZE_after_code_edit refuses a forged receipt for every part.
Edit 2 H freeze: code/runner.py:82 freezes H before A preflight; test_a_freezes_h_before_preflight checks both bars.
Edit 3: code/evaluate_v2.py:102 reads parts/A/PER_ITEM_A_train.jsonl, removes only per-row provenance, and requires equality with A_DISTANCE.txt; test_plant_B_reads_planted_A_DISTANCE refuses both planted scores.
Edit 3 duplicates: code/evaluate_v2.py:85 rejects duplicate (row_id, arm); test_duplicate_row_arm_refuses covers the appended-row probe. B takes only A's C32 baseline arms when assembling gains.
Edit 4: scripts/gpu_environment.sh:10 exports PCI_BUS_ID and runtime/nv; scripts/gpu_environment.sh:36 logs two memory/utilization and compute-app readings 300 seconds apart and refuses either busy reading.
Edit 4 tests: code/test_fix3.py:220 and the following GPU fixtures verify exports, 300-second wait, appended logs, each busy reading, the 1-GiB boundary, and query failures. Fixture mode always exits before GPU execution.
Probe regressions: code/test_fix3.py:20 covers all nine plant.py probes plus the duplicate-row probe; out/FIX3_PROBES.json records refusals and input hashes.
`bash scripts/cpu.sh code/test_kit.py > out/tests_fix3.log 2>&1`: 62/62 PASS.
`bash scripts/cpu.sh code/dryrun.py > out/dryrun_fix3.log 2>&1`: PASS; 296 captures, 9472 numbering hashes, 450 camera records.
`bash scripts/cpu.sh work/a0_rerun.py > out/a0_fix3.log 2>&1`: 1,037/1,037 full A0 rows and 209/209 capture row sets match; 1,012/1,012 decision rows and 204/204 capture row sets match.
A0 checks predictions, re-formatted responses, member frames and boxes; out/fix_validation/a0_rerun_summary.json records both populations and input hashes.
`bash scripts/cpu.sh scripts/finalize_v3.py > out/finalize_fix3.log 2>&1` binds out/CODE_SHA256.json and out/GPU_NEED.json to the passing dry run.
New code_sha256 for inbox/GPU_GO.json: `47ecaeecd8f59f91190b28c05394e9b08ca48a997b86279710f400b099ec0fc2`. No GPU authorization was created.
`bash scripts/cpu.sh work/refresh_stage.py > out/stage_fix3.log 2>&1` refreshes kit hashes in out/STAGE_LIST.tsv; external hashes and the verified trace inventory are reused.
`bash scripts/cpu.sh work/package_fix3.py` computes sequential staging from STAGE_LIST.tsv into out/STAGE_INCREMENTAL.json: A 22.24 GB, +B 3.86 GB, +C 7.59 GB, +H 0.31 GB (decimal).
Run parts one at a time on one node, staged at /scratch/jjyeung/orch_n30/sb_ktfix2. Keep A outputs for B and A/B outputs for H.
The 24e9-byte bound remains unchanged. The reviewer cautions that A10/A10G report about 23.8e9 bytes and are refused; 3090/4090/A5000 pass the memory bound. These are reviewer card figures, not GPU measurements here.
Card and staging source: `sed -n '/6. 24 GB policy:/,/10. Unbacked claims:/p' work/ktchk_probes/REVIEW_VERDICT.md`.
MISSING: /scratch/jjyeung/orch_n30/sb_kbox2/heldout_labels.json. No held-out look was consumed; GPU performance remains unmeasured.
`bash -n scripts/cpu.sh scripts/gpu_environment.sh scripts/run_A.sh scripts/run_B.sh scripts/run_C.sh scripts/run_H.sh` passes.
`bash scripts/cpu.sh work/package_fix3.py` writes out/sb_ktfix3.tar, verifies every member against out/FIX3_MEMBERS.json, and writes out/sb_ktfix3.tar.sha256.
`bash scripts/cpu.sh work/verify_fix3.py` verifies delivery receipts, both replay populations, staging totals, code pins, archive members and the unchanged reviewed archive.
Verify the new archive with `sha256sum -c out/sb_ktfix3.tar.sha256`; out/sb_ktfix2.tar retains its reviewed SHA256.
Writing skill: no-archaeology. No borderline history sentences were retained.
