# N launch 174134: the division-pin refusal in prepare, and the five refusals a walk on the held node found behind it (tree_rebuild27 fix6, 2026-11-21)

Status: first refusal DIAGNOSED and its receipt fix CONFIRMED on the node (candidate bf2e7ebb); refusals 2-5 FOUND by a scratch walk that reached the forward, the receipts and the gate copy; their fixes are PENDING orchestrator rulings (2 ruled to the tree, 3-5 open). The training start after the gate is NOT YET EXERCISED to a step.

## Question
Why did job 174134 (kit n_go 9e809db4, tree seal 9d2bbb8a, mode q) refuse with "Preservation/pointing receipt or division differs" at carrier_c1_run.py:542 after 94 min of admit, which side is wrong, and what refuses after it on the rest of the mode-q path?

## Answer
1. The vqa stream fails `division_admits(receipt['division'], division)` at line 540, and only that sub-check. The run's pose division a3v2 (f41d15aa) names its parent 0d28fdd4 under P's path .../ap/e84d901c/z/4c230a7e.json; N's vqa receipt u/e3ee51da pins the same bytes under .../tree_rebuild_w/w12/work/n1fix2/inputs/0d28fdd432b0.json. c1_pose_mix.ancestor_admits compares pins as whole {path, sha256} dicts. N's receipt is the wrong side (a relocated pin; class (a) of ORDER 1502Z). P passed the same check because its vqa receipts pin the parent under P's path.
2. The tree demands a TRAIN scene of the receipt's division for every row that survives the scene rule and the removal files (carrier_c1_data.build_stream 611-626; scene_division_gate.check_rows). The 601 v7 rows outside 0d28 train (474 in scenes a3v2 added, 127 in neither) are all dropped by P's removal file 02315a74, which N carries; neither run trains on them.
3. Behind that check a job meets, in order: (2) s1_exclusions.py:320 "Filter differs from independent scene census: pose", then routing, at every read of the preparation: the exact census counts whole stores while the pose mix reads 27,604 of a2v3's 66,934 rows and routing reads 35,423 of 47,898 base rows and 9 of 14 pool sources; (3) s1_admission.py:58 "Retained RGB is absent or outside its frame store": the frame map resolves to X/data2root, the kit's request names the copies in p/q/f as roots; (4) kit b/cs.py:119 "R1_CENSUS_ROOM_UNRESOLVED:pose" after the forward: the kit's room classifier resolves none of the 185,667 admitted pose rows (also rv.py evidence R1_PROTECTED_ROOM_UNRESOLVED and cs.verify R1_CENSUS_NOT_PASS); (5) same place, "R1_CENSUS_PROTECTED_ADMITTED:routing": 841 of 43,101 admitted routing rows lie in K1 held-out rooms.
4. With 1-3 logged and the census in the kit's diagnose mode, the rest ran clean: prepare() to its receipt, bind_prepared, handover and admission (resume step 0, milestone 400), loader audit, the forward on cuda:0 (288 records, 4 ranks x 72, all finite; pose 0.337, vqa 0.072, routing 0.00003, pointing 0.433 mean loss; 22.0 GiB GPU peak), finish_host PASS, h.py, rv.py to WAITING_REVIEW, the six-file gate copy.

5. Two facts a fix must meet: the frame audit takes 81 min single-threaded (13.9 million frame pins; its hash sample is equal in both frame stores), and through the tiered alias map 2,183 admitted pose rows fall in K1 held-out rooms (20 rooms, scannet/scene0630 first) while 140,720 pose rows get no room from any map.
6. A two-step training start in scratch got four ranks through staged-pin verification and launch_r1.entry.admit (with a scratch stand-in for the review pin) and then stopped in train()'s rank-0 preparation check on a layout fault; no step ran.

## Evidence
/scratch/jjyeung/orch_n30/tree_rebuild27/work/fix6/REPORT.md on trinity-3-30 holds every number with its output file (fix6/rd/), the scripts (fix6/s/, fix6/node/) and the files pulled from the node (fix6/pull/): event logs of the scratch runs, the forward's records file, the census evidence c4.json and the 841 routing row keys c2.json.

## Method that worked: a read-only copy of the job's sandbox on the held node
fix6/node/L.sh rebuilds the job shell's bwrap command from the job's j.sh with three changes: the job directory is bound read-only at both of its names, one scratch folder under /tmp is writable, and scratch folders stand in for the run folder and for X/o/<job>/live. The job's venv, tree, staged inputs and GPUs are then usable from `srun --overlap --jobid <job>` without touching the job's state. fix6/node/c.py (c2, c4) continues production_proof._run from the admit call in a scratch root: it reloads p/q/c.json, repeats the closure check, opens cuda:0 as the opener step had, links the three streams the job built into the new prepare directory through patched builders, and turns a named check into a logged warning by calling the tree's check first and repeating it relaxed only for the diagnosed difference. The tree's own phase journal makes later runs resume after prepare. Reaching the first refusal again costs 14 min instead of 95; the forward was reached 80 min after the walk started. Long steps run as detached srun steps; a local script polls one small event file at most once a minute.

## Options considered
- Receipt re-pin to P's parent path (F1, a7682dae): passes; not chosen. Receipt pinned to a3v2 (RULING 1523Z, bf2e7ebb): chosen and confirmed (five sub-checks pass; row rule under a3v2: read 212,384, removed 23,315, outside 0, heldout 0, admitted 189,069).
- Naming the v7 build's receipt 8091154c: rejected, it also changes database.path and source.path that other N records pin.
- Comparing division pins by sha256 in the tree: rejected by RULING 1523Z.
- Census over the admitted population with equality kept, in the tree: ruled 1554Z, after proof by row keys; no re-cut of the routing stores.
- Frame audit: kit namespace under /tmp/jjyeung with the map pointed at the staged copy, or a tree change to the audit roots; no smaller kit fix satisfies both begin_host and resolve_read. Open.
- Pose rooms in the kit census and the 841 routing rows in K1 rooms: open, they define what the post-condition certifies.

## What might not work, and how we would notice
- The walk reused the streams 174134 built and logged three checks; a refusal that only a rebuilt stream, the real census or a PASS census receipt would raise stays hidden. The next job's own steps are the test; each has a CPU preflight below.
- A scratch layout for the training start must bind the tree as a real directory at <root>/p/s (a symlink makes carrier_c1_run.py:188 raise 250 s after rank start) and must give the sandbox a writable scratch p/q with the job's entries bound read-only, because the config's run output p/q/r lies in the job folder.

## Tests that would settle it
- Kit build time, CPU, seconds: fix6/proto/pf_streams.py check_streams(cfg) (lines 536-541 predicate with the tree's division_admits).
- Right after staging, about 3 min CPU: s1_exclusions.apply/coverage_report on the staged stores; one frame pin per stream through resolve_read against request['frame_roots']; the kit classifier on the first 100 admitted rows of each stream.
- At kit build on P's preparation, 15 min CPU: cs.publish.
- A fresh job on jn7.sh that reaches WAITING_REVIEW with an armed kit.
