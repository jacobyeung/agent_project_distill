# N launch 174134: the division-pin refusal in prepare, and what the walk past it found (tree_rebuild27 fix6, 2026-11-21)

Status: diagnosis CONFIRMED on the held node; receipt fix chosen by the orchestrator (RULING 1523Z), candidate bf2e7ebb confirmed; second refusal (scene census) found by the walk, fix ruled to the tree (RULING 1554Z); walk past both IN PROGRESS at the time of writing (see the last section).

## Question
Why did job 174134 (kit n_go 9e809db4, tree seal 9d2bbb8a, mode q) refuse with ValueError "Preservation/pointing receipt or division differs" at carrier_c1_run.py:542 after 94 min of admit, which side is wrong, and what else refuses after it?

## Answer
1. The vqa stream fails `division_admits(receipt['division'], division)` at line 540, and only that sub-check. The run's pose division a3v2 (f41d15aa) names its parent 0d28fdd4 under P's path .../ap/e84d901c/z/4c230a7e.json; N's vqa receipt u/e3ee51da pins the same bytes under .../tree_rebuild_w/w12/work/n1fix2/inputs/0d28fdd432b0.json. c1_pose_mix.ancestor_admits compares pins as whole {path, sha256} dicts, so the ancestor rule fails on the path string. N's receipt is the wrong side: a relocated pin, class (a) of ORDER 1502Z.
2. The tree demands a TRAIN scene of the receipt's division for every row that survives the scene rule and the removal files (carrier_c1_data.build_stream 611-626; scene_division_gate.check_rows). The 601 v7 rows outside 0d28 train (474 in scenes a3v2 added, 127 in neither) are all dropped by P's removal file 02315a74, which N carries, so neither P nor N trains on them.
3. With that check logged, prepare() refuses 150 s later at s1_exclusions.py:320 "Filter differs from independent scene census: pose"; routing would refuse next. The census (exact_rebuilt_population) counts whole stores; N's pose mix reads 27,604 of a2v3's 66,934 rows (frame prefix) and its routing build reads 35,423 of 47,898 base rows and 9 of 14 pool sources. The differences equal the listed rows outside the read subsets exactly (pose 1,841 dev / 159 test; routing pool 1,122 / 566, base 783 dev).

## Evidence
- /scratch/jjyeung/orch_n30/tree_rebuild27/work/fix6/REPORT.md (trinity-3-30) holds every number with its output file under fix6/rd/ and the scripts under fix6/s/ and fix6/node/.
- Node tests with the tree's own functions: d3.py (verbatim division_admits by AST, system python), cand.py (real imports inside the sandbox), q1/q2 (scene membership and filter attribution), q3/q4 (census both sides).

## Method that worked: a read-only copy of the job's sandbox on the held node
fix6/node/L.sh rebuilds the job shell's bwrap command from /tmp/q_22c714e1_<job>/j.sh with three changes: the job directory is bound read-only at both of its names, a scratch folder under /tmp is the only writable place, and scratch folders stand in for the run folder and for X/o/<job>/live. The job's venv, tree, staged inputs and GPUs are then usable from `srun --overlap --jobid <job>` without writing into the job's state. fix6/node/c.py continues production_proof._run from the admit call in a fresh scratch root: it reloads p/q/c.json, repeats the closure check, links the three streams the job had built into the new prepare directory through patched builders, and logs chosen checks as warnings. Cost to reach the first refusal again: 14 min (12.5 min of it the pose-mix pass), against 95 min for a fresh job.

## Options considered
- Receipt re-pin to P's parent path (F1, candidate a7682dae, 724 B): passes with the tree's function on the node. Not chosen by the orchestrator, who ruled the a3v2 pin.
- Receipt pinned to a3v2 exactly (RULING 1523Z, fix7's candidate bf2e7ebb, 729 B): chosen; confirmed on the node (five sub-checks pass; row rule under a3v2: read 212,384, removed 23,315, outside 0, heldout 0, admitted 189,069).
- Naming the v7 build's own receipt 8091154c: rejected, it also changes database.path and source.path, which other N records pin.
- Comparing division pins by sha256 in the tree: rejected by RULING 1523Z (no tree change, no sha-only comparison).
- For the census: census over the admitted population with exact equality kept, in the tree (RULING 1554Z item 3), after proof by row keys; no re-cut of the routing stores.

## What might not work, and how we would notice
- The scratch walk reuses the job's built streams and softens two checks; a refusal that only a rebuilt stream or the real census would raise stays hidden. The next job's own prepare is the test.
- The preflight below predicts only receipt-level refusals; row-level ones need the stream build.

## Tests that would settle it
- Kit build time, CPU: proto/pf_streams.py check_streams(cfg) on the kit's receipts (lines 536-541 predicate with the tree's division_admits).
- After staging, about 3 min CPU: apply/coverage_report on the staged stores (the census comparison).
- The fresh job on jn7.sh reaching s1_admission.prepare DONE.
