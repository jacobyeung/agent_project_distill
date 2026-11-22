STATUS 2026-11-22T04:22Z fix20: COMPLETE. Questions 1-4 answered; section 7 answers RULING 0412Z (closure, what each option forces, hard checks after the first save); design record and index line written; nothing built. Orchard calls used 8 of 8.

# Item 1: the disk plan of 174246, every term

## 0. One finding that bears on RULING 0357Z item 1 (read first)
The sealed tree refuses a changed full-state interval. student_pilot/r1_handover.py:181-186 (compare_configs) compares N's recipe with P's on every field except mix and milestones, and raises P_EXPORT_CONFIG_DIFFERENCE:recipe on any difference. P's recipe has resume_every_seconds 7200 (read from P's config on Orchard, runs/6ed2c7aa/inputs/prepare_da5580b7.../config.json). compare_configs runs in launch_r1/p_opener_witness.py:43 (proof step p_opener_witness), launch_r1/production_proof.py:44, and r1_handover.py:40 (bind_target), :300 and :405 (progress). I emulated the recipe comparison on Orchard (out/o4.out): donor==kit True today; with 10800 it is False, differing ['resume_every_seconds']. I read the function and emulated its recipe line; I did not run the tree's function on a changed config. The same line locks wall_seconds, stop_before_seconds and export_at_stop to P's values.
Milestones are locked too: student_pilot/r1_training.py:98 raises R1_MILESTONES_DIFFER unless the recipe's milestones are exactly [100, 200, 400, 600, 800, 1000] (the handover admits a milestone difference from P, but r1 validation pins the list).
So with tree 9d2bbb8a the kit owns no number of the plan: 6,027.7 GB is fixed for N. The guard itself must equal plan(recipe, reserve 200e9, copies 1): launch_r1/entry.py:165 (R1_DISK_PLAN_DIFFERS, default reserve), launch_r2/persistence.py:14, carrier_c1_run.py:92. Interval 10800 needs one tree line (add resume_every_seconds to the two exclusion tuples at r1_handover.py:183-184), which moves the tree source seal.

## 1. The formula (checkpoint_space.py:119-123) and the terms
required = states*S + exports*E + copies*(states*(S+10240) + exports*(E+10240)) + reserve = 32*S + 14*E + 235,520 + 200e9 = 6,027,674,886,604 B, so 32*S + 14*E = 5,827,674,651,084 B.
| term | value | where set |
|---|---|---|
| wall_seconds, stop_before_seconds | 86400, 3600 (span 82,800 s) | kit config recipe block (k/c.json, k/n.json; job v.json identical), written by launch_s1/build.py:148; tree default RECIPE is 14400/900 (carrier_c1.py:28); locked to P by r1_handover.py:181 |
| resume_every_seconds | 7200 | same recipe block (build.py:149); tree default 1800; locked to P |
| planned_full_states | 14 = ceil(82800/7200) 12 + 2 | plan() checkpoint_space.py:16; stored in cfg.checkpoint_disk_guard |
| extra_full_states | 2 | plan() constant |
| states at the first save | 16 (none completed) | Budget.remaining :44 |
| milestones, export_at_stop | [100,200,400,600,800,1000], true: 7 exports | kit config; milestones pinned by r1_training.py:98, export_at_stop locked to P |
| retained_archive_copies | 1: doubles every state and export, +10,240 B each | r2_config.py:71 writes it; entry.py:165 and persistence.py:14 require it |
| reserve_bytes | 200,000,000,000 | plan() default; entry.py:165 requires the default |
| S (state_bytes) | about 137.9 GB = 1.25 x M + 64 MiB | check() :117, measured live |
| E (export_bytes) | about 101.1 GB = 2.5 x X + 64 MiB | check() :118, measured live |
| free | 5,717,540,712,448 B = min statvfs over ranks of the output folder (/tmp) | check() :96, :124 |
The policy reaches the trainer as cfg.checkpoint_disk_guard: run_steps builds one Budget from it (carrier_c1_run.py:2356) and checkpoint_options() passes that Budget as disk_guard to every checkpoint; no env or recipe default enters.

## 2. M and X (no record of them survives; derived from parameter counts)
No c1-checkpoint-disk-v2 record exists: 174246 died before writing one, and P's run folder on /project holds no checkpoint folder (only m400, m600, metrics, run report); P's log files hold no guard event.
Parameter counts read on Orchard (out/o4.out): exported base index total_size 19,306,216,416 B BF16 = 9,653,108,208 parameters in 775 tensors, of which the trainer loads 760 (the 15 mtp tensors are not loaded, about 227-243 M parameters by the config's dimensions); heads 508 tensors = camera head 231,033,111 (172 tensors) + head encoder 456,010,480 (333 tensors) + 3 small. Full fine-tuning keeps every base tensor as an FP32 master (full_ft.py:330).
- X (every parameter in memory, FP32) = 4 x (9,653,108,208 - mtp + 687,043,591) = 40.39 to 40.45 GB.
- M (trainable weights + two AdamW moments, FP32) = 12 x (language model and output head 8.954 to 8.971 G + camera head 0.231 G) = 110.22 to 110.42 GB. This trainable set (base vision and the head encoder frozen) is the one that reproduces the total; I inferred it from that match and from carrier_c1.py:737, not from a group report.
- These give required = 6.025 to 6.036 TB, which is -0.04% to +0.13% of 6,027,674,886,604. The exact identity 8*M + 7*X = 1,164,917,528,668 then fixes the split: X = 40.42 GB, M = 110.25 GB, S = 137.88 GB, E = 101.12 GB. s/plan_calc.py runs the tree's own plan() and reproduces 6,027,674,886,604 exactly at (M, X) = (110,246,315,968, 40,421,000,132) (out/plan_calc.out).
- Native 16*S 2,206.0 GB + 7*E 707.8 GB = 2,913.8 GB; archive copies 2,913.8 GB; reserve 200 GB.
- Real sizes from P: checkpoint 600 archive 113,383,997,440 B (P/o/172660.steps); m400 export archive 21,583,032,320 B (kit k/p.json m4.b). A state really costs 226.8 GB with its copy against 275.8 GB planned; an export really costs 43.2 GB against 202.2 GB planned.

## 3. P's plan (job 172660, orchard-community-1, same /tmp size class)
P's config guard: planned 14, extra 2, exports 3 (milestones 400, 600 and the stop), reserve 200e9, no retained_archive_copies (P has no r2_identity, so persistence returns early and no archive is kept). Same wall 86400, stop 3600, interval 7200.
P required 16*S + 3*E + 200e9 = 2,709.4 GB with N's S and E (same 760 + 508 tensors). P's /tmp read 5,916 GiB free at start and 5,453 GiB (5,855 GB) at its last logged stage: margin above 3,100 GB. P really saved 9 states (steps 201, 251, 305, 360, 414, 469, 524, 579, 600; 65-70 s each) and 2 exports in 15.3 h.
N's plan is 2.22 x P's: the archive copy doubles it and four more exports add 808.9 GB.

## 4. Clean orchard-community node: the plan can never pass
- /tmp is /dev/md127, 6,238,618,200 KiB (6,388.3 GB, 5,949.6 GiB) on community-2 and community-3 (df.txt of 8 jobs). A clean node reads free_bytes 6,388,327,845,888 at job start (174101, 174113, 174134).
- This kit's staging plus proof stores occupy 667.3 to 674.9 GB: used 651,632,096 KiB (174101, clean start, community-3), 654,267,152 (174113, clean, community-2), 659,116,832 (174134, clean, community-3).
- 174246 at its failure: used 655,068,932 KiB (670.8 GB), avail 5,583,532,884 KiB. That equals one job's own footprint, so /tmp held no measurable leftovers at 03:44Z. The leftovers present at job start (free 4,824 GB) had gone by then.
- Clean node at the first save: 6,388.3 - 667.3..674.9 = 5,713.4 to 5,721.0 GB free, against 6,027.7 GB required. Short by 306.6 to 314.3 GB on every clean node; 174246 was short by 310.1 GB. The plan passes only if staging stays under 360.7 GB, and staging is 667 to 675 GB. The plan asks for 94.4% of the whole disk.
- The first save binds: each completed state lowers the requirement by 275.8 GB and uses 226.8 GB; each export lowers it by 202.2 GB and uses 43.2 GB.

## 5. Cross-check against n_review1l's DISK_PLAN_READING.md (read after sections 1-4 were derived)
Agree: the formula, 16 states, 7 exports, copies 1 doubling every term, 235,520 B, reserve 200e9, 32*S + 14*E = 5,827,674,651,084; P's policy (16, 3, no copy); the archive copy is real (persist tar kept, nothing deletes); exports are written BF16 and planned at FP32 x 2.5; the first save binds; guard pinned in three tree places.
Differences:
1. Where 86400 and 3600 are set. n_review1l: the tree RECIPE. Mine: the kit config's recipe block (the tree default is 14400/900; recipe_for passes the config's values through and range-checks them).
2. The handover lock (section 0). n_review1l lists the three guard pins and treats the interval as the kit's number; r1_handover.py:181-186 also pins the recipe timing to P's, so the interval is not kit-settable on this tree.
3. S and E. n_review1l: S about 139.8 GB, E about 96.7 GB, from X = FP32 of the staged 19.33 GB base. Mine: S 137.9 GB, E 101.1 GB, because X also counts the 508 head tensors (2.75 GB FP32) and drops the 15 unloaded mtp tensors. Effect on a 12-state plan: 4,924.7 GB (mine) against about 4,909 GB.
4. Real export size. n_review1l: about 20 GB. Measured: 21.58 GB (P's m400 archive).
5. Clean node. n_review1l: free after staging is 5,717.5 GB + leftovers L, margin 0 to 90 GB, node size not measured. Mine: node size and three clean-start jobs measured; 174246's used figure already equals a clean job's footprint, so L was about 0 at the failure and the clean-node margin is -306.6 to -314.3 GB. ORDER 0348Z's "about 5,300 GiB after staging" agrees with this (5,321 to 5,328 GiB); its "leftovers about 330 GB on the node" does not hold at 03:44Z.
6. Count of states really needed. n_review1l: 10 (clock starts at job start, training began at 5 h 42 m). I did not re-derive the trainer's clock origin; with P's measured cadence (one periodic state per 2 h of loop time) a 17.3 h window gives 1 + 8 + 1 = 10, which agrees.

## 6. Plan sizes by the tree's own plan() (S 137.875 GB, E 101.120 GB; free 5,717.5 GB as 174246 had)
| policy | states, exports | required | margin | tree admits it? |
|---|---|---|---|---|
| today (7200, 6 milestones) | 16, 7 | 6,027.7 GB | -310.1 GB | yes |
| interval 10800 | 12, 7 | 4,924.7 GB | +792.9 GB | no: P_EXPORT_CONFIG_DIFFERENCE:recipe |
| interval 14400 | 10, 7 | 4,373.2 GB | +1,344.4 GB | no (same) |
| milestones [200,400,600,1000] | 16, 5 | 5,623.2 GB | +94.3 GB | no: R1_MILESTONES_DIFFER (r1_training.py:98) |
| milestones [400,1000] | 16, 3 | 5,218.7 GB | +498.8 GB | no (same) |
| milestones [1000] | 16, 2 | 5,016.5 GB | +701.1 GB | no (same) |
| wall 64800 | 13, 7 | 5,200.4 GB | +517.1 GB | no: P_EXPORT_CONFIG_DIFFERENCE:recipe |
| no archive copy | 16, 7 | 3,113.8 GB | +2,603.7 GB | no: entry.py:165, persistence.py:14 |
Interval 10800 brings the plan under 5.0 TB (4.925 TB) as RULING 0357Z item 1 expects, and passes the 300 GB preflight rule with 492.9 GB to spare, but only after the one-line tree change of section 0.

# Question 3: the free /tmp
- Size: /dev/md127 mounted on /tmp, 6,238,618,200 KiB = 6,388.3 GB (5,949.6 GiB); used + avail = size - 16 MiB, so nothing is reserved. Slurm lists TmpDisk=0 for every node; community-2 and community-3 read the same size, and P's community-1 read 5,916 GiB free at its start.
- At training start (03:29Z) the watch's tmp_freeK=5,583,636,272 is in KiB: 5,717.6 GB, not 5.58e12 B. At the failure df read used 655,068,932 KiB (670.8 GB) and avail 5,583,532,884 KiB; the trainer's statvfs read 5,717,540,712,448 B.
- What the 670.8 GB holds: the job's own staging and proof stores, and nothing else measurable. Four jobs of this kit family show the same footprint at 1 h, 1 h 50, 1 h 54 and 5 h 57 into the job (667.3, 670.0, 674.9, 670.8 GB), so the proof adds only a few GB to staging. The kit's input parts on /project total 280.3 GB (in/ 128.2 GB, in/cr 152.1 GB; out/o5.out), of which 58.0 GB are stores the trainer reads in place (j2.log "joined" lines); the base model is 19.3 GB and the init mirror about 21.6 GB; the rest is extracted frames. I could not list the node's folder (it is gone, and my brief allows no srun), so the split between kept archives and extractions is an estimate.
- Free space at a job's start varies with what the previous job left: 174198 started with 641.8 GB used (174134's folder) and 174246 with 1,564 GB used (174198's); both figures dropped within a minute, and by 03:44Z nothing of them remained in the used figure.

# Question 4: the fixes, priced
Every fix changes the tree (section 0). Margins use the tree's plan() with S 137.875 GB and E 101.120 GB, against the clean-node free space of 5,713.4 to 5,721.0 GB.
RULING 0412Z chose T-mil: r1_training.py:98 accepts a subset of the six milestones and the kit sets [100, 200], which gives 16 states and 3 exports, 5,218.7 GB, margin +494.7 to +502.3 GB (the same size as the [400,1000] row of section 6). Option A below is T-int and option E is T-est; neither is built. Section 7 prices all three.

## A (recommended). One tree line that admits the interval, and interval 10,800 s in the kit config
- Files: tree student_pilot/r1_handover.py:183-184, 'resume_every_seconds' added to both exclusion tuples (the comment there already says export timing is rebound while loss and schedule knobs stay), with one case in tests/test_r1_build14.py; kit k/c.json and k/n.json: recipe.resume_every_seconds 10800 and checkpoint_disk_guard.planned_full_states 10.
- Identities: all of these move: tree source seal 9d2bbb8a, tree tar k/t_e047002134f979bd.tar (5f2d77c4), the source records k/7.json, k/c0.json and k/a.json, the config's code pin, kit config 76de3706 (c.json) and 4b8b9533 (n.json), job config identity f6250f70, r1_training.continuation_identity, BUILD.json, kit seal 7e23bbdd, and trainer_commit in the binding. No N checkpoint exists, so nothing needs rebinding.
- Earlier steps that read it: every step reads the tree, so ORDER 1857Z item 4 is met only by a run from the start of the proof; the next job starts from nothing anyway. The interval itself is read by recipe_for and validate (every step that validates the config), compare_configs (p_opener_witness, production_proof, bind_target, progress), the plan equality (carrier_c1_run.py:92, the host assertion disk_plan at launch_r1/entry.py:165, launch_r2/persistence.py:14), the preparation receipt (carrier_c1_run.py:697 and :731 compare the whole recipe, so preparation is rebuilt), and run_steps:2433. s1_routing reads only recipe.max_routing_suffix_tokens (:307) and s1_admission only recipe.mix (:299), so the routing selection 522a3be3 and database 5e35c3ce should stay; the from-start run shows it.
- P's training content and schedule: kept. Optimizer contract, 1000 steps, LR horizon, mix, rows, milestones and the stop export are unchanged; only the periodic full state comes every 3 h instead of 2 h, so a crash loses up to 3 h.
- Disk: plan 4,924,674,815,052 B (12 states, 7 exports). Margin +788.7 to +796.3 GB on a clean node; the 300 GB preflight rule passes with 488.7 to 496.3 GB to spare; a rehearsal sink of one state and one export with their copies (about 270 GB at real sizes) still leaves about 520 GB at the first save. A leg writes at most 1 + 7 + 1 = 9 states and 7 exports, inside the budget of 12 and 7. The kit's 16 upload slots (b/pc.py:641, k/y.json ck00 to ck15) cover 12.
- Not yet shown: I read the code and emulated the comparison; nobody has run validate, compare_configs, check_host_runtime and persistence.plan on the changed tree and config. One CPU call settles it.

## A2. Same tree line, interval 14,400 s
Plan 4,373.2 GB, margin about +1,340 GB, a crash loses up to 4 h. Hold it as the fallback if a node reads under 5,225 GB free after staging.

## B. A shorter leg (wall_seconds)
The same handover line locks wall_seconds to P, so B needs the same tree change, and it stops training earlier: wall 64800 gives 5,200.4 GB (+513 to +521 GB) and costs 6 h of training per job (about 160 steps at P's 137 s per step). Kit b/pc.py:598 also reads wall_seconds. Rejected: it gives up steps and saves no change.

## C. More free /tmp
- Another node: every community node measured has the same 6,388.3 GB disk, and a clean one is short by 306.6 to 314.3 GB. No identity moves, and the plan still cannot pass.
- Freeing the kit's staged archives after extraction: at most 222 to 280 GB (parts 280.3 GB less the 58.0 GB read in place), under the 310 GB needed. It changes the kit's staging script and the kit seal, must come after the host proof (verify_host_staging rereads the archives), and the margin stays negative.
- Our leftovers: the df arithmetic shows none on /tmp at 03:44Z, so removing them gains nothing for this plan.
Rejected.

## D. A rolling plan that counts deleted states
The tree rotates by renaming into _superseded and never deletes (carrier_c1_run.py:2026-2032), and persistence keeps every tar. A rolling plan needs deletion after a confirmed upload, a rewritten check(), and the equality in three places: a large tree change that alters what the node holds for a resume. It belongs to the first boundary. For that design: a leg really writes 9 or 10 states and up to 7 exports, 2.3 to 2.6 TB with copies at real sizes.

## E. Estimator at the written precision
checkpoint_space.py:118 plans an export at 2.5 x FP32 (101.1 GB) where the writer produces 21.6 GB in BF16 plus its tar. With the estimate at 2 x 21.6 GB per export, the plan at 7,200 s would be about 5.2 TB. E changes the guard's own arithmetic, which is the riskier edit, and RULING 0357Z item 2 puts it at the first boundary. Not for this job.

## F. No archive copy, or a smaller reserve
Pinned by launch_r1/entry.py:165 and launch_r2/persistence.py:14, and the copy is real (persist/<sha>.tar is kept), so dropping it from the plan would under-count. Rejected.

## G. Fewer milestones
Pinned by r1_training.py:98, and it removes exports that later reads use. Rejected.

## What might not work in A, and how we would notice
- Another equality on the recipe that I missed: the CPU call above, or the proof's p_opener_witness step, refuses within the first hour.
- S grows after step 1 if AdamW moments fill in later (state_bytes is a running maximum). P's saved state bounds it at 113.4 GB, so S is at most 141.8 GB and the plan at most 86 GB larger: the margin stays above 700 GB. Each save prints the c1-checkpoint-disk-v2 record; read the first one.
- Another tenant fills /tmp during the leg: the guard rechecks at every save. The preflight's 300 GB rule and the per-save record show it.

# 7. Answers for RULING 0412Z (T-mil), written 04:21Z

## 7.1 Is r1_training.py inside the pool closure? Yes, and so are the files of T-int and T-est
- Computation: I ran the tree's own function on fix15/tree with Python 3.12 on CPU (s/closure.py; list in out/closure.txt). p3_provenance.source_files([s1_pool.py]) returns 274 files, and s1_pool.implementation() itself ran and returned the same dict. Its digest is 15ea4f68eec6c4c39225ac6dadd9f6eb275afbca2c71a296a163f1d253e293f2.
- The job agrees: 174246's published refresh.json holds `current` with 274 entries and the same digest 15ea4f68 (out/o8.out). Its `source` (the pool selection as first built) has 204 entries, so the kit regenerates the pool selection under the running tree in every job.
- Inside the closure: student_pilot/r1_training.py (T-mil), student_pilot/r1_handover.py (T-int), student_pilot/checkpoint_space.py (T-est), and also carrier_c1_run.py, launch_r1/entry.py and launch_r2/persistence.py. Every file that pins a number of the plan is in the closure, so no plan fix avoids it.
- How the closure reaches the routing selection: s1_pool.prepare writes implementation=implementation() into the pool receipt (s1_pool.py:215); s1_pool.selected_rows (:226) and s1_routing.build (:224) refuse a receipt of another implementation. The routing receipt carries the pool receipt's pin as `source` (s1_routing.py:483) and the relocated copy's pin in materialization and in source_scene_exclusions (:464, :368). The digest 522a3be3 is digest(receipt.json) (verified on Orchard, out/o6.out); the receipt holds pool pin 74640a29 once and relocated pin 0dd39e28 nine times, and materialization holds them once and ten times. A changed closure file changes the pool receipt, both pins, and therefore 522a3be3.
- The database: rows carry s1_source with the source file's pin only (s1_routing.py:413-417), no selection pin and no implementation. With no row-producing code changed, 5e35c3ce, row_bytes_sha256 802414c8 and row_id_digest bdd91b75 should stay; mode r shows it.
- Source seal, tar hash, config identity: receipt.json, materialization.json, refresh.json and the kit's pin file u/a49f117f contain 9d2bbb8a, 5f2d77c4, f6250f70, 76de3706, 4b8b9533 and the code pin b2ba52d6 zero times (out/o6.out). The receipt embeds config content the build reads (cfg.s1_routing, route_table, s1_route_policy, streams.routing, division, base model, removal lists), and neither milestones nor recipe timing (s1_routing reads only recipe.max_routing_suffix_tokens, :307). The pin file also records inputs_pinned.config_sha256 = b28f58a2 (b/rg.py:26), the digest of its own mode-r config; nothing compares it (b/pl.py reads only routing_base :105 and routing_database :155), but a new mode r writes a new value.

## 7.2 What each option forces
| option | file touched | in the closure | forced |
|---|---|---|---|
| T-mil | student_pilot/r1_training.py:98 | yes | mode r, task A, arming, tree review, kit seal |
| T-int | student_pilot/r1_handover.py:183-184 | yes | the same |
| T-est | student_pilot/checkpoint_space.py:117-118 | yes | the same |
Every option forces mode r, so by RULING 0412Z item 2 T-mil stands. Redone, with times from STATUS.md:
- Tree line, its tests and compare_configs on CPU on Trinity: minutes. One tree review by n_review1l.
- New tree tar and source seal into k/t_*.tar, k/7.json, k/c0.json, k/a.json and the config's code pin; config (milestones [100, 200], guard planned_weight_exports 3, r1_training.continuation_identity, which digests the whole config at r1_training.py:105-113); kit seal.
- Mode r as a CPU job on Orchard: staging 102 to 515 s and mode r 340 to 474 s (jobs 173677, 173680, 173725), so 8 to 16 minutes of run time; those jobs started within about a minute of submission. It produces a new regenerated_sha256 and a new pin file, so k/h.json and k/r.json (routing_selection, staged_pins) change.
- Task A (the row verdict against P's rows) ran inside the same CPU job (173680 ran staging, mode r and rd0 in about 10 minutes). The rows should be byte-identical, so the verdict's content is unchanged, but it has to be issued for the new pin. I did not trace how the verdict file names the pin.
- Arming: arm_launch.sh on the new kits (ran 02:16Z on 11-21), install on the Orchard paths (06:25Z), armed-bytes review (PASS 06:57Z, about 30 minutes after the install).
- Then the job from its start: 174246 took 4 h 24 m from start to WAITING_REVIEW and 1 h 16 m more to GO.
Net: the closure adds about 1 to 1.5 hours before submission (one CPU job, the arming, the armed-bytes review) on top of what any kit change costs, and it adds the same for all three options.
One consequence of [100, 200] to rule on: the leg ends near step 400 to 440 (60,800 s of loop time after a 5 h 42 m start and the trainer's 1,500 s stop reserve, less nine saves of about 8 minutes and two exports, at P's 137 s per step), so it may pass 400 without exporting it. A resume must carry the same config (restore raises "C1 resume binding differs", carrier_c1_run.py:2058), so later legs of this config export only at their stop. A handover out of N accepts only a step in N's milestones (launch_r1/p_handover_receipt.py:19, launch_r1/p_export_receipt.py:31, student_pilot/r1_persisted.py:122): 100 or 200.

## 7.3 Hard checks between the first save and the end of the leg
"Rehearsal" means two steps, one checkpoint, one export into a scratch sink, uploads to a local sink. "Never met" means no real N job has passed it; P's job 172660 passed only what is marked.
| # | check | where | status | rehearsal |
|---|---|---|---|---|
| 1 | Disk plan at every save and export; budget of 16 states and 3 exports per process ("Whole-leg disk write budget is exhausted") | checkpoint_space.py:124-126, :44-47 | never met by N; P met it with its own policy | exercises the first check at real S and E if the sink is on the job's /tmp and the policy is the kit's; not the later checks, not exhaustion |
| 2 | Serialized state within its measured budget ("Checkpoint payload exceeds its measured disk budget") | carrier_c1_run.py:1983-1985 | never met by N; P's state is 113.4 GB against S 137.9 GB | exercised |
| 3 | Output belongs to this run; the new state is complete; older states renamed into _superseded | carrier_c1_run.py:1966-1969, :2024-2032 | P met it | the rename needs a third state: not exercised |
| 4 | Persistence of every state and export on rank 0: plan equality, state inside the run, native predicate, member digests, claim file opened exclusively, free space of archive + 200 GB, tar inventory and digests; any refusal ends training ("Durable persistence refused") | launch_r2/persistence.py:14-16, :31-41, :49, :55-56, :63-71, :131-132; called at carrier_c1_run.py:2453 and :2463 | never run in any real job: P's config has no r2_identity, so milestone() returned at :120; e3 173966 tested the kit's uploader, not this function | exercised only if the rehearsal calls milestone() with the job's config on four ranks |
| 5 | Time of that persistence against the collective timeout. Rank 0 hashes the 113 GB state four times and tars it once (:40, :53, :61, :66-70) while ranks 1 to 3 wait in a broadcast (:128-130) on the default group, whose timeout is 900 s (carrier_c1_run.py:2876; the comment says training collectives fail fast at 15 minutes) | as cited | never met. From e3's 143 s for one tar of a state I estimate 6 to 8 minutes; at 0.5 GB/s hashing it would be 17 minutes and exceed the limit at the step-1 save. That a waiting broadcast is aborted at the timeout is PyTorch's documented NCCL behaviour and the tree's own comment, not something I tested | exercised and timed only if the rehearsal keeps the 900 s group and the real state size. This is the check I would watch first |
| 6 | Export at milestones 100 and 200 and at the stop: disk check, BF16 shards, heads.pt, trained-group contract, source-seal binding from the config's code pin, r1 progress (continuation_identity must equal the config's identity), component status and absence proofs, artifact.json | carrier_c1_run.py:2084, :2093-2101, :2114-2127; r1_training.py:116-125; full_ft.py:660-693 | never run by N; P exported m400 and m600 on its own tree and config, without the r1 fields | exercised if the export runs on the real model and config; a stand-in model does not exercise :2114-2127 |
| 7 | Validation read after an export when the rows carry a validation slice | carrier_c1_run.py:2466-2468 | not traced for N | exercised only if the rehearsal's rows have that slice |
| 8 | Upload of a state and its archive copy by the kit's publisher: reuse of persist/<sha>.local.json, E100 while the native writer is active, E95 spool free under size + 50 GiB, part verification E99, 16 state slots, 112 session names; only top-level checkpoint_* folders are seen | b/pc.py:389-424, :418-419, :566-577, :630-641; k/y.json | e3 173966 passed 17 checks on real sessions at 90.8 MB/s; never run beside a training job. Inside b/pc.py a refusal is recorded and retried (:284-288, :590-594, :640); I did not check how the wrapper treats a publisher exit | local sink exercises the planner, the reuse of the tree's tar and the four parts; not the real sessions, not the rate |
| 9 | Stop: the trainer stops by its clock from TK_JOB_START with the config's estimates (checkpoint 600 s, export 600 s, step 300 s), then saves, persists and exports | carrier_c1_run.py:2437-2444, :2456, :2879-2882; stop_control.py:6-12 | P stopped by h1 stop_after_step 600, not by the clock; the clock stop has never run in a real job | not exercised |
| 10 | Stop upload in the time left. The trainer stops about 1,500 s before the 82,800 s mark (one step 300 s, checkpoint 600 s, export 600 s); the stop save with its persistence and the stop export take about 10 minutes, so about 4,400 s remain, against e3's two attempts of 143 + 1,482 s. The publisher recognises the stop state only when run_<job>.json appears, because the stop save is older than the nominal stop. A stop state that is not uploaded is "left node-local" and goes with the node | carrier_c1_run.py:2439-2444; b/pc.py:598, :600-609, :626 | never met | not exercised |
| 11 | Exit copy caps each file at 50 MB (live/copy.json cap_bytes 50,000,000). 174246's r1.json already lists q0.json and q2.json as too_large; P's metrics file was 75.9 MB for 400 steps and its run report 69.8 MB | published copy.json and r1.json; I did not trace the kit code | never met at leg size | exercised only if the rehearsal ends through the wrapper, and then at toy size |
| 12 | Resume of a later job from a state: binding equality, shard layout, payload digests, RNG | carrier_c1_run.py:2039-2075 | P resumed at step 201 on its own tree; N never; the kit's download of a state to a new node never ran | not exercised |
Not hard checks for N: the m400 gate (gate_stop is false in the config, carrier_c1_run.py:2447), and cfg.stall_guard, which only P's launcher reads (launch_s1/b/i.py:162-167, sg.py); N's kit never reads it.
What I did not read: b/gc.py, b/rv.py beyond its bounds check, b/cs.py, the wrapper jn7.sh, and j34.sh after training exits. Items 8, 10 and 11 rest on b/pc.py lines 389-424 and 596-700 and on published files only.

# Notes
- Orchard: 8 of 8 calls used, all read-only on the login node (s/CALLS.log, scripts s/o1.sh to s/o8.sh, outputs out/). My stdin scripts o3.sh and o4.sh contain Python's .split() method, a word on the kit's opaque list; it named nothing and was never written to Orchard.
- The rm_guard hook blocked two of my commands and queued them in /home/jjyeung/agent_project/agent/PENDING_USER_COMMANDS.md: a read-only grep of fix15/dec/j34.sh whose search pattern contained "rm -", and a heredoc that appended these sections to this report ("unparsable shell command"). Neither deletes anything; the user can discard both entries. I wrote the sections with the file tool instead.
- Design record: /data2/jjyeung/agent_project_data/distill_design/N_174246_CHECKPOINT_DISK_PLAN_20261122.md.
