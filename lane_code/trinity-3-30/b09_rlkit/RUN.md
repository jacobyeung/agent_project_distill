# RL kit (rlkit-v1): how to run a round

Code: `/scratch/jjyeung/orch_n30/b09_rlkit` (L). Python: `/scratch/jjyeung/envs/p1cpu/bin/python` with `PYTHONPATH=L`. Nothing here runs without an ORCH GO and a registered card. Inputs and outputs live on node-local `/scratch`.

## Inputs
- Export r: weights pin (`path`, `sha256`) and its kit config (frame layout; 32 or 64 frames). Round 0 starts from the SFT export the init rule chose.
- Prompt pool: `python -m rlkit.prompts --rows R0_RL_ROWS.jsonl --allow-scenes R0_RL_SCENES.txt --frames 32 --out POOL.jsonl` (brief 10's R0-rl rows; benchmark sources and excluded scenes are refused).
- Held-out set for the floor: R0-dev prompts built the same way; they must share no id or scene with the pool.

## Round r
1. **Sample** (one 48 GB card per shard, resumable per draw): fill `out/dryrun_packet/SAMPLER.template.json`, then `python -m rlkit.sampler --config SAMPLER.json --prompts POOL.jsonl --out RUN_r --shard i/n`. Off trinity-0-13 prefix `/data3/shared/scripts/vnice/vnice.sh`. A stopped shard resumes when the same command runs again; a changed config is refused.
2. **Floor** (round 0, then whenever the export changes): sample the held-out set into `RUN_r_dev`, then `python -m rlkit.floor --run RUN_r_dev --prompts DEV.jsonl --pool POOL.jsonl --out FLOOR_r.json`. FLOOR_r.md shows how each n_min was set.
3. **Baselines**: `python -m rlkit.baselines constants --fit TRAIN.jsonl --pool POOL.jsonl --out CONST.json`; `... shuffle --pool POOL.jsonl --out POOL_SHUF.jsonl`, sampled like step 1 into `RUN_r_shuf`; after step 4, `... collapse --pool POOL.jsonl --select SEL_r --out COLLAPSE_r.json`.
4. **Mode (a)**: `python -m rlkit.select --run RUN_r --prompts POOL.jsonl --tree L/grpo_tree --round r --floor FLOOR_r.json --out SEL_r`. Only `vqa_rows.jsonl` trains: it goes through the intake (frame pins) and the sealed SFT trainer unchanged, with the every-rank CPU first batch. `program_candidates.jsonl` waits for a ground-truth re-render; `quarantine.jsonl` waits for brief 08's amendment.
5. **Mode (b)** (not runnable yet): compute ref log probs with `grpo_loss.sequence_logprobs` on the SFT export, write rows with `rlkit.grpo.to_row` and `write_stream_db`, and train them through the patched trainer `L/grpo_tree` (`grpo_rows.py` in `Rows.get`, `grpo_loss.py` in the forward). A membership manifest for these databases and its own review come first.
6. **Export r+1**, then the stop rule below, then round r+1.

## Reward
r = c x g - min(lam x max(0, n - n_min) / n_ref, 0.5 x c x g); r = 0 when c x g = 0. c = MRA or option exact match; g = termination, validator a41ba191, provenance and counterfactual replay (`rlkit/gate.py`); n = model-generated tokens (printed responses are free); n_min from FLOOR_r.json, else the group's shortest right trace of the path. Defaults: lam 0.2, n_floor 12, n_ref = median right-trace length per type.

## Stop rule (registered before a run)
After round 1's update: the dev-S1 direct read and the guard read against the round's init. Stop if F1 fails, if reward rises while the dev read falls, or if any type's grammar-pass rate (g) drops below 95%.

## Tests (CPU)
`bash L/rltests/run_grpo.sh rltests.test_sampler rltests.test_reward rltests.test_floor rltests.test_grpo rltests.test_select rltests.test_baselines rltests.test_e2e rltests.test_prompts rltests.test_grpo_rows`
