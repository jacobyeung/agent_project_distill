All required fixes 1–5 and all three optional safeguards are implemented. CPU only; GPU hours used: 0.
Accepted spec: 133e8cfdbb149401767c76fc5908154b9dd106d2a4b580bcca81d207615169aa (`sha256sum inputs/KIT_SPEC_tower_frames_v2.md`).
GPU GO must bind code_sha256 `53ea9d60cfe3302f0100aeec00e51ff04fee9c7417228a20d7af9ff6e7d08988`; `out/CODE_SHA256.json` lists its files.
1. code/evaluate_v2.py:32: missing convert exports yield NO_CONVERT_EXPORT; code/evaluate_v2.py:67: only exported scales enter agreement/stored-rule checks, and each relative error must be ≤1e-4.
2. code/evaluate_v2.py:23: discard MISSING placeholders and retain part bars; code/evaluate_v2.py:118: persist added_frame_gain and its verdict under bars.B.
   scripts/finalize_v3.py:57: finalization writes no placeholder DECISION.json; the inherited placeholder is preserved in work/inherited_DECISION.json outside runtime outputs.
3. code/runner.py:18: Part C requires a standalone GO line before capture work; code/README.md:11 and scripts/finalize_v3.py:63: document and report the missing approval inputs.
4. code/metrics.py:70: only context_pays_pose licenses C64 camera context.
5. code/test_kit.py:139: regressions cover pose sign, A2 direction, lifting arm, DECISION persistence, held-out guard, dense best-frame remapping, and run_a without a convert export.
Optional: code/runner.py:65: check HALTED before admission and write NOT_ADMITTED receipts; code/kbox_hook.py:18: require the complete reference row set.
Claims: scripts/finalize_v3.py:86: response matching re-formats the prediction because kbox4 stores no response text.
Disclosures: scripts/finalize_v3.py:91, code/README.md:19: selector frame counts retain 32/31 divisors at N=64; raw depth AbsRel uses unscaled G3T depth.
Relocation: scripts/cpu.sh:3, scripts/gpu_environment.sh:3 and scripts/run_A.sh:3 (also B/C) resolve this workspace; copied provenance and kbox paths preserve original byte hashes.
Tests: 28/28 PASS — `bash scripts/cpu.sh code/test_kit.py > out/tests_v3.log 2>&1`.
Mutations: 12/12 killed — `bash scripts/cpu.sh work/mutate.py > out/fix_validation/mutations.log 2>&1`.
The reviewer probe's 12 replacements and execution remain unchanged; only workspace/output routing, logs and hashed receipts are adapted. The original is work/reviewer_mutate_original.py.
Dry run: PASS; all 296 captures and 9472 numbering hashes pass — `bash scripts/cpu.sh code/dryrun.py > out/dryrun_v3.log 2>&1`.
A0: 1037/1037 rows match predictions, re-formatted responses, member frames and boxes; all 209/209 capture row sets match — `bash scripts/cpu.sh work/a0_rerun.py > out/fix_validation/a0_rerun.log 2>&1`.
Part A: all 239 train captures complete; each of four arms has 1,037 rows; pose and lifting bars are FAIL with zero deltas, not MISSING — `bash scripts/cpu.sh work/part_a_cpu.py > out/fix_validation/part_a.log 2>&1`.
This CPU self-comparison substitutes stored C64 for C32, caches identical replay calls, and keeps its results under out/fix_validation; it provides no evidence that either context is better. Real GPU decisions remain uncomputed.
Scale: 237/237 available exports agree; agreement_fraction=1.0, maximum relative error=0.0 (same Part A command).
NO_CONVERT_EXPORT: scannetpp/0f69aefe3d and scannetpp/2c7c10379b retain their 12 train rows; missing files are:
- /scratch/jjyeung/k1/run_convert_2/45511ef70c22b11e/geometry.npz
- /scratch/jjyeung/k1/run_convert_2/9baa923934276385/geometry.npz
MISSING launch inputs: /scratch/jjyeung/orch_n30/sb_ktfix/inbox/GPU_GO.json (orchestrator GO), /scratch/jjyeung/orch_n30/sb_ktfix/inbox/DA3_GO.txt, and /scratch/jjyeung/orch_n30/sb_ktfix/inbox/SHARED_GPU_RESERVATION.json.
Shell validation: `bash -n scripts/cpu.sh scripts/gpu_environment.sh scripts/run_A.sh scripts/run_B.sh scripts/run_C.sh`.
Delivery: `bash scripts/cpu.sh work/write_fix_report.py`, then `bash scripts/cpu.sh scripts/finalize_v3.py`; verify `sha256sum -c out/sb_ktfix.tar.sha256`.
The archive contains the fixed code, reports and CPU evidence. No GPU, network, SSH, Git, tmux, process stopping or external writes ran; no mirror was attempted.
All generated result JSON files record input hashes. No revision-history prose was retained in the README or report.
