The kit is BLOCKED. The required Python lacks torch and safetensors, so the all-arm dry run did not pass.
The package contains a tested GT dry-run runner and fixed-math kernels; full all-arm orchestration remains incomplete.
No full train pass, selector fitting, train rule selection, or held-out evaluation ran.

Commands: `bash run.sh dryrun.py > out/box_ladder/dryrun.log 2>&1`; `bash run.sh -m unittest -v test_box_math`.
Command for all MRA/paired bounds below: `bash run.sh finalize.py` (reads dry-run PER_ITEM.jsonl).
Dry run: 58.834 seconds; peak process RSS 219.770 MiB; CUDA disabled; one numerical thread.
Six numerical unit tests passed. The dry run produced 68 records: 17 arms/variants on four rows in two physical rooms.
Captures: arkitscenes/41048124 and scannetpp/036bce3393; all four stored S4+G1+bestspread rows match exactly.
All five rules equal best1 on synthetic single-member data and eight real-object single-frame restrictions.
GT fused geometry ran and answered all four rows. A0 parity and the >=95% StageOne choice test are MISSING.

These dry-run numbers cannot select a rule. Bootstrap: paired shared rows, item weights, 10,000 room draws, seed 20261119.
| Dry-run arm | MRA | Delta vs A2 | Paired 95% bounds |
|---|---:|---:|---|
| A2_gt_masks | 90.00 | +0.00 | [+0.00, +0.00] |
| A3_gt_fused_vote2_best | 97.50 | +7.50 | [+0.00, +10.00] |
| A3_gt_fused_vote2 | 95.00 | +5.00 | [+0.00, +6.67] |
| A3_gt_fused_allspread | 82.50 | -7.50 | [-10.00, -6.67] |
| A3_gt_fused_trim | 92.50 | +2.50 | [+0.00, +3.33] |
| A6_gtgeo_single | 87.50 | -2.50 | [-3.33, +0.00] |
| A6_gtgeo_fused | 92.50 | +2.50 | [-20.00, +10.00] |

| Decision bar | Verdict | Train estimate / paired bounds / held-out estimate |
|---|---|---|
| replace_box | MISSING | MISSING / MISSING / MISSING |
| fused_path | MISSING | MISSING / MISSING / MISSING |
| gather_safe | MISSING | MISSING / MISSING / MISSING |
| selector_worth | MISSING | MISSING / MISSING / MISSING |
| selector_adopt | MISSING | MISSING / MISSING / MISSING |
| size_screen | MISSING | MISSING / MISSING / MISSING |
| first_seen_screen | MISSING | MISSING / MISSING / MISSING |
| tower_challenger | MISSING | MISSING / MISSING / MISSING |

Every deviation and limitation:
- A0/A1/A4/A5/A8 were not executed; StageOne replay and selector training code are unvalidated because dependencies are absent.
- A2/A3/A6 and all five DA3/Pi3X fusion variants ran only on the two dry captures. No A3 winner was chosen for A4/A5/A7/A8.
- The full four-shard train coordinator is not implemented. The task forbids starting full pricing before the dry gate passes.
- Size ratios/MRA are MISSING: the per-instance GT full-box join is unfinished; no dimension or half/full convention was guessed.
- First-seen records use the specified 0.002 threshold, but the referenced B12 document was outside the allowed NFS reads.
- Predicted member precision, gap-band/member-frame aggregation, and full-train diagnostics are unfinished.
- The required early five-held-out replay conflicts with the task’s train-first discipline; it was deferred, not counted as passed.
- Mixed manifest/label container bytes were read and hashed for filtering; only train records were decoded. No held-out record was decoded or priced.
- The expected top-level tree is missing; the existing b04host3 mirror is the path resolved by lift_price.py and was used read-only.
- R1 grounding.py/stage1.py byte equality cannot be checked: the remote trinity-3-30 source is unavailable locally and SSH is prohibited.
- The NFS replay2.py archive and LANE_RULES.md were not opened; only the two prompt-named NFS documents were copied.
- Replay uses the local StageOne producer and raw-name cache adapter; the archived replay was not substituted or claimed identical.
- Source harness declarations are AST-loaded with workspace globals; inventory/startup audit/main are not executed. Tree files are unchanged.
- GTGeometry receives C=c2w for the reader’s frame_count interface. Its lift arithmetic is unchanged.
- Dry reference parity uses the stored S4 scale. Corrected labels score every reported MRA; stored labels appear only in exact parity evidence.
- Fusion keeps original points in voted voxels; trim uses allspread box axes and 2nd/98th percentile extents. Equal gather overlaps use proposal index.
- Nonull uses the fixed run_iso config and trainer seed 20261116; multiple positives get uniform CE mass. This choice was not fit to results.
- No copied source line was edited: edited-line list is empty; SOURCE_VERIFICATION.json checks every copied source byte.
- No GPU, SSH, network, Git, tmux, process termination, or external write was requested. The tar remains local as the task requires.
- LADDER_HELDOUT_once.txt is reserved for the reviewed pass; its NOT_RUN companion records the missing stage.

Exact missing GT inputs (33 manifest train rows; excluding them leaves the specified 1,037 rows / 192 rooms):
- /scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/41125829.npz
- /scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/42899325.npz
- /scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt/scannetppv2__ef69d58016.npz
Expected tree: /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449 (MISSING).
R1 reference: trinity-3-30:/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4/src (not locally available).
Dependency location: /scratch/jjyeung/envs/planner_local_v1/bin/python cannot import torch or safetensors.
All inputs for each JSON are SHA256-pinned; source hashes, per-item provenance, exact parity rows, and logs are in out/box_ladder/.
Archive: out/sb_kbox.tar; checksum: out/sb_kbox.tar.sha256. It contains code, configs and reports, without rasters or tower caches.
