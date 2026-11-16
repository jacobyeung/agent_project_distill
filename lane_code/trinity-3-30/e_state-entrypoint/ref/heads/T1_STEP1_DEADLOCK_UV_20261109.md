# T1 step-1 deadlock: off-frame uv on masked-out depth points (t1_build, 2026-11-09)

## Question
Why did T1 (32 ranks, final-mode C1, FSDP) hang before step 1 twice (job 117371 with hybrid sharding, job 118867 with FULL_SHARD)? In both jobs, 30 ranks spun in NCCL at 100% GPU while GPUs 2 and 6 of one node sat at 0% GPU, blocked CPU-side in futex.

## Answer
The hang was a one-rank ValueError that the trainer turned into a silent deadlock.
- `PointDepthHead.query` (student_pilot/point_depth_head.py) refuses any uv outside [0, 1000], including uv on masked-out points. `PrivateDepth.forward` passed the target uv to it raw.
- A3 rows (lustre `ap/f02f16ad/s/a3v2`) keep off-frame uv such as 1001.0 and -1.28 on masked-out depth points. Masked uv always lie inside [0, 999], and prep and check_row checked only those.
- At step 1, microstep 0, global ranks 10 and 14 held such rows (A3 d1 rows 91060 and 39533). They raised after the LM forward, entered `train()`'s `finally: dist.destroy_process_group()`, and blocked there with no traceback. The other ranks waited in the backward collective.
- Fix (trainer commit 24d528a, branch t1a3 of the t1_build c1mix clone):
  - `PrivateDepth.forward` zeroes the uv of masked-out points before the head. Masked-out points never enter the loss, so loss and gradients are unchanged.
  - `check_row` requires one uv pair per depth label and labelled uv inside [0, 1000], so a bad row is substituted on every rank together.
  - `run_or_exit` makes a rank that raises inside `run_steps` print its traceback and `os._exit(1)`, so the launcher stops the job at once.

## Evidence
- Step-1 plan recomputed with `mixed_indices` (seed 17, world 32). The counts dict follows the prep receipt's sorted stream order: pointing, pose, routing, vqa. The earlier `step1_plan.json` used a different order and was wrong.
- Probe of all 32 ranks' pose rows at microsteps 0 and 1 (`/scratch/jjyeung/orch_cd/t1_build/work/out/probe_uv_step1.out`): at microstep 0, exactly ranks 10 and 14 have uv outside [0, 1000]. Microstep 1 has 4 more such rows, so these rows are common in A3 d1.
- torchrun's c10d rendezvous orders nodes by sorted hostname. Global ranks 10 and 14 are therefore GPUs 2 and 6 of the second sorted host: pool0-1323 of [1108, 1323, 1333, 1396] in 118867, and pool0-0611 of [0488, 0611, 0633, 0786] in 117371. Both jobs hung on exactly those GPUs.
- In the hybrid job, the other 3 nodes had finished their intra-node backward and were stuck initialising the inter-node all_reduce ("nranks 4 Init START", no COMPLETE). The lazy-NCCL-init diagnosis was wrong: hybrid sharding did not cause the hang.
- A1 rows already carry [32,64] zero-mask placeholders (uv 0, mask False), the same form as T0's C1-r `depth_placeholders`.
- A CPU 2-rank gloo FSDP test (`tests/test_c1_masked_uv.py`) uses one A1-only rank and one A3 rank with off-frame masked-out uv. Before the fix it raised the production error on the A3 rank; after the fix it runs 2 steps with equal heads across ranks. Codex Astra review: GO, 1 MINOR (KeyboardInterrupt and SystemExit still reach teardown).

## Options rejected
- Zero-mask placeholders for A1 (the first hypothesis): A1 already has them, so this was not the cause.
- Rewriting the A3 DB to clamp uv: the data is correct (masked-out points), and rewriting ~20 GB of rows plus a new receipt and prep costs about 2 h.
- Dropping the affected A3 rows in prep: they are common among A3 d1 rows, so this would bias the mix.
- Adding only the check_row refusal: it would substitute away half the A3 d1 rows (and with them their supervision) instead of training on them.

## Risks and how we would notice
