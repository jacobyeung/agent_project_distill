"""Write the requested bounded report from measured receipts."""
from pathlib import Path
from rl_on_n import provenance as P
root=Path(__file__).resolve().parents[1];P.sha(__file__)
tests=P.load(root/'out/TEST_RESULTS.json');cpu=P.load(root/'out/CPU_PROOF.json')
parity=P.load(root/'out/PARITY.json');gate=P.load(root/'out/GATE_CHECK.json')
loop=P.load(root/'out/STEP_LOOP.json');serving=P.load(root/'out/SERVING_CHECK.json')
selection=P.load(root/'out/REPLAY_SELECTION.json')
text=f'''# sb_rlfix2: A4 reader binding and CPU validation

A. Rollouts call the sealed A4 `real.generate_real` with the adapter-installed model and capped hook. `serving.py` verifies the package, settings, descriptor, export pin and staged payload bytes. It builds `real_perception` with candidates_argmax, G3T memo, SAM 3 and the learned selector through A4's actual APIs.
A. The reader's isolated native module scope supplies A4 geometry and decoder helpers while N retains admission and training. Own gravity and own depth for scale are part of the claimed arm. G3T supplies depth for lifting; scale uses A4's positive-depth median ratio.
B. Sampling follows A4's ThinkingBudget: 2,048 thinking callbacks, forced think-close, then 64 answer callbacks; open calls can defer the close by up to 96 callbacks. Natural closes retain deployed behavior. Forced budget IDs are kind `b`; distance and room stop on calls 6 and 2.
C. `scripts/run_greedy_replay.sh` authenticates A4's m200 EXPORT_PIN, installs zero-initialized adapters and compares all tokens and finishes on four journal items per type. Training requires its pinned PASS receipt. GPU replay: NOT RUN (CPU-only task).
D. `reward.py` multiplies both short and route by correctness; the 7-versus-12.19 regression checks correctness 0.2 and total reward 0.24.
E. Pool admission asserts equality of raw and cleaned native prompt IDs and rejects prompt changes.
F. A CPU test executes `train.run` for one step on four sequential stub ranks, including one refusing rank. It exercises the real objective, backward, gradient averaging, optimizer and checkpoint; CUDA/collective transport are mocked.

`bash scripts/run_tests.sh` produced {tests['tests']} tests, {tests['failures']} failures and {tests['errors']} errors (`out/TEST_RESULTS.json`, log alongside).
The same command produced {parity['review_cases']+parity['additional_cases']} scorer cases with {len(parity['mismatches'])} mismatches, admitted {gate['admitted_controls']} training controls with {gate['physical_overlap']} physical overlaps, and checked the exclusion and REMOVE lists (`out/PARITY.json`, `GATE_CHECK.json`, `REMOVE_CHECK.json`).
The same command produced `out/STEP_LOOP.json`: refusal counts {[r['refusals'] for r in loop['ranks']]}, backward counts {[r['backwards'] for r in loop['ranks']]}; every rank updated its adapters using the emulated collective sum.
The same command produced `out/REPLAY_SELECTION.json`: {sum(selection['counts'].values())} actual journal items selected, four per type; no generated replay outputs or PASS claim.
`bash scripts/run_cpu.sh` produced PASS in {cpu['seconds']:.3f} s at {cpu['peak_rss_gib']:.3f} GiB peak RSS, gradient L1 {cpu['gradient_l1']:.6f}, adapter update L1 {cpu['adapter_update_l1']:.6f}, and ratio error {cpu['ratio_error']:.7f} (`out/CPU_PROOF.json`).
The CPU proof uses random real-width layers and synthetic G3T/gravity/scale through A4's decoder. Rewards and reward advantages are [0, 0]. Synthetic rewards [1, 0] supply [0.5, -0.5] solely for the backward test. SAM 3/selector inference, production weights and GPU fit remain untested.
`PYTHONPATH=overlay python -B scripts/serving_check.py` produced the pinned reader/settings/budget/cap receipt (`out/SERVING_CHECK.json`).
`PYTHONPATH=overlay python -B scripts/make_configs.py` produced unbound configs and arithmetic GPU estimates; rates are assumptions.
MISSING: authenticated m200 restore at A4's recorded `/scratch/jjyeung/b01ec87a6f29b/d/e`; its local RESTORE identifies m544. The replay requires `--export-dir` and `--config` whose hashes match EXPORT_PIN.json.
MISSING: `configs/h100_{{4,8}}.json` bindings `source_config`, `pool_config`, `artifact`, `pool`, `grounding.artifact_manifest`, and `greedy_replay`; admitted pool expected at `out/PROMPT_POOL.json`. Qualified init_m544 evidence remains absent from `/scratch/jjyeung/orch_n30/sb_f64/pkg/work/n1fix2/inputs/registry.json`.
`PYTHONPATH=overlay python -B scripts/package.py` produces `out/sb_rlfix2.tar`, `out/SHA256SUMS`, and `out/PACKAGE.json`; `scripts/verify_package.py` verifies archive bytes and validation input hashes.
All Python commands here use `/scratch/jjyeung/envs/p1cpu/bin/python`, nice 10, and OMP/MKL/OPENBLAS=8. No GPU, network, SSH, Git or process-control operation ran. All writes stayed inside this workspace.
'''
assert len(text.splitlines())<=50
(root/'out/REPORT.md').write_text(text)
P.write(root/'out/REPORT_INPUTS.json',dict(command='PYTHONPATH=overlay python -B scripts/report.py',report=P.pin(root/'out/REPORT.md')))
print('Report lines:',len(text.splitlines()))
