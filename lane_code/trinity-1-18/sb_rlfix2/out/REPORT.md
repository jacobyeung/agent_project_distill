# sb_rlfix2: A4 reader binding and CPU validation

A. Rollouts call the sealed A4 `real.generate_real` with the adapter-installed model and capped hook. `serving.py` verifies the package, settings, descriptor, export pin and staged payload bytes. It builds `real_perception` with candidates_argmax, G3T memo, SAM 3 and the learned selector through A4's actual APIs.
A. The reader's isolated native module scope supplies A4 geometry and decoder helpers while N retains admission and training. Own gravity and own depth for scale are part of the claimed arm. G3T supplies depth for lifting; scale uses A4's positive-depth median ratio.
B. Sampling follows A4's ThinkingBudget: 2,048 thinking callbacks, forced think-close, then 64 answer callbacks; open calls can defer the close by up to 96 callbacks. Natural closes retain deployed behavior. Forced budget IDs are kind `b`; distance and room stop on calls 6 and 2.
C. `scripts/run_greedy_replay.sh` authenticates A4's m200 EXPORT_PIN, installs zero-initialized adapters and compares all tokens and finishes on four journal items per type. Training requires its pinned PASS receipt. GPU replay: NOT RUN (CPU-only task).
D. `reward.py` multiplies both short and route by correctness; the 7-versus-12.19 regression checks correctness 0.2 and total reward 0.24.
E. Pool admission asserts equality of raw and cleaned native prompt IDs and rejects prompt changes.
F. A CPU test executes `train.run` for one step on four sequential stub ranks, including one refusing rank. It exercises the real objective, backward, gradient averaging, optimizer and checkpoint; CUDA/collective transport are mocked.

`bash scripts/run_tests.sh` produced 43 tests, 0 failures and 0 errors (`out/TEST_RESULTS.json`, log alongside).
The same command produced 110 scorer cases with 0 mismatches, admitted 233 training controls with 0 physical overlaps, and checked the exclusion and REMOVE lists (`out/PARITY.json`, `GATE_CHECK.json`, `REMOVE_CHECK.json`).
The same command produced `out/STEP_LOOP.json`: refusal counts [0, 2, 0, 0], backward counts [2, 0, 2, 2]; every rank updated its adapters using the emulated collective sum.
The same command produced `out/REPLAY_SELECTION.json`: 20 actual journal items selected, four per type; no generated replay outputs or PASS claim.
`bash scripts/run_cpu.sh` produced PASS in 112.626 s at 14.628 GiB peak RSS, gradient L1 4253.670143, adapter update L1 1.966011, and ratio error 0.0109763 (`out/CPU_PROOF.json`).
The CPU proof uses random real-width layers and synthetic G3T/gravity/scale through A4's decoder. Rewards and reward advantages are [0, 0]. Synthetic rewards [1, 0] supply [0.5, -0.5] solely for the backward test. SAM 3/selector inference, production weights and GPU fit remain untested.
`PYTHONPATH=overlay python -B scripts/serving_check.py` produced the pinned reader/settings/budget/cap receipt (`out/SERVING_CHECK.json`).
`PYTHONPATH=overlay python -B scripts/make_configs.py` produced unbound configs and arithmetic GPU estimates; rates are assumptions.
MISSING: authenticated m200 restore at A4's recorded `/scratch/jjyeung/b01ec87a6f29b/d/e`; its local RESTORE identifies m544. The replay requires `--export-dir` and `--config` whose hashes match EXPORT_PIN.json.
MISSING: `configs/h100_{4,8}.json` bindings `source_config`, `pool_config`, `artifact`, `pool`, `grounding.artifact_manifest`, and `greedy_replay`; admitted pool expected at `out/PROMPT_POOL.json`. Qualified init_m544 evidence remains absent from `/scratch/jjyeung/orch_n30/sb_f64/pkg/work/n1fix2/inputs/registry.json`.
`PYTHONPATH=overlay python -B scripts/package.py` produces `out/sb_rlfix2.tar`, `out/SHA256SUMS`, and `out/PACKAGE.json`; `scripts/verify_package.py` verifies archive bytes and validation input hashes.
All Python commands here use `/scratch/jjyeung/envs/p1cpu/bin/python`, nice 10, and OMP/MKL/OPENBLAS=8. No GPU, network, SSH, Git or process-control operation ran. All writes stayed inside this workspace.
