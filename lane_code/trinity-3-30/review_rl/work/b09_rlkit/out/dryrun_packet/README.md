# RL kit dry run: 200 prompts, one card, one hour

Goal: measure seconds per rollout on both paths, reward and gate rates per type, budget hits and tower errors on the real export, before any round is priced.

## Inputs to bind (ORCH)
1. Export pin and kit config (default: the SFT export the init rule chose; step 544 until D0's export is chosen), staged on the sampling node's /scratch.
2. POOL.jsonl: 200 R0-rl prompts from `rlkit.prompts --limit 200 --seed 17 --frames 32` (brief 10's rows). Weight types to the gap list in brief 09; object_abs_distance is the only type with a head path today.
3. A card: two `nvidia-smi` readings 5+ minutes apart showing it empty; vnice off trinity-0-13.

## Steps
1. `cp SAMPLER.template.json /scratch/.../SAMPLER.json`; fill export, kit_config, artifact_pin, audit_root.
2. `bash run_dryrun.sh SAMPLER.json POOL.jsonl RUN_DIR GPU` (stops itself at 3,300 s; rerun resumes).
3. Reuse check: on 10 head-path prompts, sample once with `factory_config.reuse` 'draw' and once 'clip' into two run dirs; tokens and texts must be byte-equal before 'clip' may be used.
4. Read `RUN_DIR/DRYRUN_MEASURE.json`: `paths.head.sec_mean` and `paths.direct.sec_mean` price a round (10K prompts x 8 draws); `types.*.g_rate` and `budget_hits` show whether the gate and budget fit the export; `free_call_rate` is the unforced head-path rate.

## Expected (brief 09 estimates; the dry run replaces them)
Direct rollout about 0.5 s on an H100 at a 57-token chain, about 1 to 2 s on an A6000; head rollout about 7 s with towers live. 200 x 8 = 1,600 draws fit one hour only if the mean is under 2.2 s; otherwise the run stops at 3,300 s and the measured rates still price the round.
