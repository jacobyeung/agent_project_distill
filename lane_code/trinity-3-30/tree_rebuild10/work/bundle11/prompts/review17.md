# Independent review (read-only, once) of vehicle N's final kit: build 17b of lane tree_rebuild

You review; you do not fix or design fixes. You run once, read-only, on trinity-1-18; nobody answers questions. Report only verified problems, each with file:line or artifact path and the command or reading that shows it. Your final message is the verdict.

## What N is
A ~9B spatial vision-language model whose chain of thought calls heads inside its own checkpoint (pose, depth, grounding boxes) and answers from what they print. Vehicle P (another trainer of the same lineage) trains leg R1 now: its continuation C' (config identity 774503e2, runtime config identity 9459724f) exports at steps 400 and 600; step 600 is its stop and checkpoint. N must take over from P's step-600 export as init (absolute step 600, P's trained opener rows kept), training on N's own row plan; N's production proof runs first on P's step-400 export, which has no checkpoint (export-only binding, proof mode only).

## Inputs (READ-ONLY)
- Final kit and tree: `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w17b` (`out/BUILD17_REPORT.md`, `out/BUILD16_REPORT.md`, `out/BUILD15_REPORT.md`, `out/TREE.diff`, `work/tree_r1/`, `work/build17/`, `work/build16/`). Earlier build reports and the design record are in `out/`.
- P's configs: `/scratch/jjyeung/orch_n30/tree_rebuild10_w/inputs/p_configs/`, `.../inputs/p_runtime/`, `.../ext/r1_ops/work/`. Row inputs: `/scratch/jjyeung/n30_mirror/rows_r1/out/`, `/scratch/jjyeung/n30_mirror/rows_r2/out/vehN_pool_abs_distance_full/`. Removal lists `.../inputs/records/`; room authority `.../ext/b12/`, `.../inputs/rooms/`; the lane's room check `.../work/k1check/K1R0_CHECK.json`; the lane's confirmation runs `.../work/conf15/`, `.../work/conf16/`.

## Check, in this order
1. Legality: no benchmark answer or benchmark-answer statistic chooses a quantity, quota or threshold; every sealed exclusion holds for every training row N can draw (benchmark scenes 3119aa4a, dev-S1, WITHHELD_80, K1 held-out rooms 4d4736cf, R0 rooms bdb5d402, division 0d28fdd4 train scenes); no trace is answer-only or states a quantity that the frames, a printed tool response or explicit arithmetic does not supply; no fitted selector, rule table, guard or fallback outside the weights is claimed as the model.
2. Handover: N admits P's real A, C, C' configs and C''s runtime config and refuses topology, loss and optimizer changes by name; at step 600 it requires the checkpoint receipt (h.json) and resumes at absolute step 600 with the sampler at the right position; the export-only receipt admits only in proof mode at a non-stop milestone and refuses in a training launch and at the stop; `p_handover_receipt.py` is byte-equal to build 15; the opener witness binds P's export and the step-544 lineage. Look for any path by which a wrong export, a forged receipt, a wrong step or a reset of the opener rows would be admitted.
3. Rows and card: the bound slices and lists (distance aedd3b54 + merged extent receipt, recovery v3, units, s.json, n.json, z.json); no first-seen-list counting row and no totals row can be drawn; card cells against their 4 x eligible / 1,000 ceilings; the plan's largest repeat.
4. Proof mode and operator packet: the job script and request template run what the report claims, in the claimed order, with opaque job-visible names (no project, benchmark, dataset, model or method word anywhere job-visible), and the staging list is complete for the inputs mode q reads.
5. Say what you did not check.

## Rules
- Read-only. No ssh, network, GPU, Git, tmux, scheduler or another agent. Never list, search or grep on /home or /data*. Search inside the inputs above freely. You may run the build's own confirmation commands only if they write nowhere (they write proof folders, so normally do not run them; read their recorded outputs instead).
- Verdict, first line: `GO`, `GO AFTER FIXES` (each fix MUST or SHOULD, with evidence) or `NO-GO` (with the blocking finding). Then at most 40 lines.
