"""Write the requested bounded report from measured receipts."""
from pathlib import Path
from rl_on_n import provenance as P
root=Path(__file__).resolve().parents[1];P.sha(__file__)
tests=P.load(root/'out/TEST_RESULTS.json');cpu=P.load(root/'out/CPU_PROOF.json')
parity=P.load(root/'out/PARITY.json');gate=P.load(root/'out/GATE_CHECK.json')
loop=P.load(root/'out/STEP_LOOP.json');serving=P.load(root/'out/SERVING_CHECK.json')
selection=P.load(root/'out/REPLAY_SELECTION.json');n_export=P.load(root/'out/N_EXPORT_CHECK.json')
mutants=P.load(root/'runs/fix4/REV3_MUTANTS.json');configs=[P.load(root/f'configs/h100_{w}.json') for w in (4,8)]
if configs[0]['missing_bindings']!=configs[1]['missing_bindings']:raise ValueError('Configs list different MISSING bindings')
missing='\n'.join(f"MISSING `{name}`: expected {spec['expected']}; hash source: {spec['hash_source']}."
                  for name,spec in configs[0]['missing_bindings'].items())
text=f'''# sb_rlfix4: A4 reader binding, replay gate and CPU validation

A. Rollouts call the sealed A4 `real.generate_real` with the adapter-installed model and capped hook. `serving.py` verifies the package, settings, descriptor, export pin, `INPUTS.json` and staged payload bytes.
A. Training loads the policy with A4's `e2e_reader.parity.load_native` inside `reader_runtime()` and builds every prompt with A4's `evalpath.runtime.prompt_batch` from that loader's `info['config']`. The greedy replay calls the same two functions.
A. `build_reader` runs `Artifact.verify()` and then requires the G3T, SAM 3 and selector files to carry the sha256 recorded in A4's `INPUTS.json`. On CPU it has run on a tiny verified artifact with autospec stand-ins for `Sam3Tower`, `_head` and `real_perception`, which binds their signatures and arguments. Real perception, SAM 3 and selector loading remain unrun.
A. Own gravity and own depth for scale belong to the claimed arm; `serving_check.py` derives both from the perception object A4's `real_perception` builds ({serving['own_heads']}).
B. Sampling follows A4's ThinkingBudget: 2,048 thinking callbacks, forced think-close, then 64 answer callbacks; open calls can defer the close by up to 96 callbacks. Forced budget IDs are kind `b`; distance and room stop on calls 6 and 2.
C. `scripts/run_greedy_replay.sh <card>` refuses a non-numeric card or one with more than 1,024 MiB used, requires the interpreter and kit under `/scratch`, and runs `timeout 2h` at nice 10, through vnice on Trinity. `greedy_replay.py` requires an NVIDIA H100 80GB HBM3 and `/scratch` inputs and appends each item to a JSONL, so a rerun skips matched items.
C. The resume key includes the digest of the selected references and the SHA256 of every scanned journal and environment file, and a cached row is reused only if `replay.check_result` finds that it still reproduces its current reference. A changed journal therefore forces a fresh decode.
C. The replay compares tokens, finish, call families and budget firing on 26 A4 m200 journal items: four per type, four whose calls include a gap and two whose budget fired. Training's `require_replay` recomputes group counts from the results, refuses repeated ids, requires the exact selected (id, group, type) set, and checks every result against its current pinned reference; summary fields and `match` flags alone certify nothing. GPU replay: NOT RUN (CPU-only task).
D. `reward.py` multiplies short and route by correctness and scores a `max_calls` or strict-no-answer record 0 even with a correct answer.
E. Pool admission asserts equality of raw and cleaned native prompt IDs; each room-gate layer refuses on its own.
F. `rollout._sample` turns only `generate_real`'s ValueErrors into refusals; alignment errors still raise. When the all-reduced refusals exceed 25% of a step's draws, every rank stops before the optimizer step.
F. `train.py --resume` verifies the checkpoint's JSON pin and config identity, then restores adapters, optimizer, step, cursor and rng; a resumed run equals an uninterrupted one on CPU.

`bash scripts/run_tests.sh` produced {tests['tests']} tests, {tests['failures']} failures and {tests['errors']} errors (`out/TEST_RESULTS.json`, log alongside).
The same command produced {parity['review_cases']+parity['additional_cases']} scorer cases with {len(parity['mismatches'])} mismatches, admitted {gate['admitted_controls']} training controls with {gate['physical_overlap']} physical overlaps, and checked the exclusion and REMOVE lists (`out/PARITY.json`, `GATE_CHECK.json`, `REMOVE_CHECK.json`).
The same command produced `out/STEP_LOOP.json`: refusal counts {[r['refusals'] for r in loop['ranks']]}, backward counts {[r['backwards'] for r in loop['ranks']]}; every rank updated its adapters using the emulated collective sum.
The same command produced `out/REPLAY_SELECTION.json`: {sum(selection['counts'].values())} journal items in groups {selection['counts']}; no generated replay outputs or PASS claim.
`runs/fix4/mutate_rev3.py` reran the 23 sb_rlrev3 mutants listed in `runs/mut/mutate.py` on a private kit copy: {mutants['killed']} of {mutants['total']} killed (`runs/fix4/REV3_MUTANTS.json`).
`bash scripts/run_cpu.sh` produced PASS in {cpu['seconds']:.3f} s at {cpu['peak_rss_gib']:.3f} GiB peak RSS, gradient L1 {cpu['gradient_l1']:.6f}, adapter update L1 {cpu['adapter_update_l1']:.6f}, and ratio error {cpu['ratio_error']:.7f} (`out/CPU_PROOF.json`).
The CPU proof uses random real-width layers and synthetic G3T, gravity and scale through A4's decoder. Rewards and reward advantages are [0, 0]; synthetic rewards [1, 0] supply [0.5, -0.5] solely for the backward test. SAM 3 and selector inference, production weights and GPU fit remain untested.
`PYTHONPATH=overlay python -B scripts/serving_check.py` produced the pinned reader, settings, budget and cap receipt (`out/SERVING_CHECK.json`).
`PYTHONPATH=overlay python -B scripts/n_export_check.py` found that {n_export['finding']} (`out/N_EXPORT_CHECK.json`).
`PYTHONPATH=overlay python -B scripts/make_configs.py` produced `configs/h100_{{4,8}}.json` with the bindings below unset and listed under `missing_bindings`, plus arithmetic GPU estimates whose rates are assumptions.
{missing}
`out/N_EXPORT_REQUIREMENTS.md` lists what the orchestrator must supply before RL can start from an N export.
`PYTHONPATH=overlay python -B scripts/package.py` produces `out/sb_rlfix4.tar`, `out/SHA256SUMS` and `out/PACKAGE.json`; `scripts/verify_package.py` verifies archive bytes and validation input hashes.
All Python commands here use `/scratch/jjyeung/envs/p1cpu/bin/python`, nice 10, and OMP/MKL/OPENBLAS=8. No GPU, network, SSH, Git or process-control operation ran. All writes stayed inside this workspace.
'''
assert len(text.splitlines())<=50
(root/'out/REPORT.md').write_text(text)
P.write(root/'out/REPORT_INPUTS.json',dict(command='PYTHONPATH=overlay python -B scripts/report.py',report=P.pin(root/'out/REPORT.md')))
print('Report lines:',len(text.splitlines()))
