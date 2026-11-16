# Cost packet: one GF-1 step on a real batch, online tower vs cached bank
Status: protocol and analyzer ready; needs (1) the cache patch in the A2 kit (tree_rebuild build 7: apply
`../gf1_cache/gf1_cache_on_b5_ba346bd9.patch`, expose `gf1.cached_bank = {root, dtype: "float32"}` in the kit's run
config), (2) the dense frames on Orchard (`../frame_fetch/SUBMIT.md`), (3) an ORCH GO naming the job.

## Layout measured
The A2 kit as built (k/8d48d580...json): world 4 on one `advanced` node, FSDP, global batch 288 rows
(vqa 128, routing 64, pointing 32, pose 64). Pose rows keep the online tower (augmented dense frames), so the
cache can remove the tower from 224 of 288 rows per step. Stage 1 (connector only, 400 steps) and stage 2
(full, 600 steps) differ in backward cost: measure both.

## Runs (same job, same node, same init, same first rows)
1. Writer: `python -m student_pilot.gf1_cache --run-config <cfg> --rows <the step's non-pose rows> --root /tmp/<tok>/c --dtype float32 --limit 16 > writer.log`, timed with `date +%s` (one GPU).
2. Online, stage 1: trainer `train --smoke-steps 8` with the kit config; keep the metrics JSONL.
3. Cached, stage 1: the same with `cached_bank` set to the writer root (the writer must first cover every clip of the 8 steps; the cache refuses a missing clip, it never falls back).
4. Repeat 2-3 with `r2_stage.stage = 2` if the stage-2 config builds (export/reload of a stage-1 checkpoint is not needed for timing).
5. `python3 analyze.py --online on.jsonl --cached ca.jsonl --world 4 --writer writer.log --writer-seconds S out.json`.
Drop the first 2 steps; median of the remaining 6. The analyzer reports GPU-hours per 1,000 steps for each mode
and the writer's GPU-hours and GB for all 2,741 clips, replacing the guesses 345 (online) and 190 (cached).
Each run is about 8 steps of a 4-GPU node: under 1 GPU-hour in all at the guessed rates.

## Alarm
Peak memory per rank comes from the trainer's own memory probe; cached must not exceed online. If cached is
slower than online, the cache read path (Lustre, 102 MB per clip FP32) is the suspect: report the read time.
