# T2 build: T1's recipe plus derivgen's READY routed traces (t2_build, 2026-11-09)

Status: trained 11-09 05:23-08:35Z on 32 GPUs (job 119664, root ap/330df157, run runs/2c6919f1). ORCH stopped it at step 506, right after a complete save (checkpoint_000506), because false-positive grounding clicks confound the routed read until grounding is fixed. The run can resume with the same kit (u32 b/088d1891.sh, resume 'latest'). Exports: m50, m100, m200, m400 (evalx has m100-m400). 0 of 2,535 microsteps skipped. Canaries at 20/50/100/200 matched T1 on the shared streams. The routed-vs-direct read waits on the grounding fix. Lane dir: /scratch/jjyeung/orch_cd/t2_build/ (STATUS.md, events/, work/).

## Question
Can the six READY trace types from derivgen's v3.10.1 E/F/G builds join T1's routing stream unchanged, so that T2 at step s compares with T1 at step s and differs only in routing for direction medium/hard and abs distance?

## Answer
Yes, with one provenance fix and no trainer change. T2 binds:
- routing f/29b7222a on AWS root ap/330df157: 135,676 rows, 131,014 of them unique;
- VQA f/eeb1f7d4: T1's 85,806 rows minus 37,929 direct rows of the three target types, leaving 47,877.

Every other input equals T1's run 696b5868: trainer 6dbfa27 with FULL_SHARD, the pose mix, pointing, init C1-a m800, the 1,800-step cosine and world 32.

## Evidence
- Selection: derivgen's CP1 head selection (v3102_01/before, which applies the shared label filter and the camera narrow-call filter), restricted to the READY types, gives 62,861 rows: dir medium 11,320, dir hard 12,204, abs 2,331, cam displacement 14,389, rotation 9,845, movement 12,772. The camera types equal the published and cp1_cam_filter selections.
- Frames: all 10,816 trace frames are already in kit bundle f3 (k3f8), which every mode stages. The substitute manifests keep the frames and source indices and add fps (24 ScanNet, 60 ScanNet++) and total_num_frames from each scene's SCENE.json student_input; all 338 match.
- Alias defect: 23,760 'scale-native' rows carry provenance.alias from derivgen's asset-plan namespace, not the rung-1 token. The builder keys the division on that alias, so 20,084 rows would fall outside A3; 3,676 would enter under a foreign token.
  - Fix: alias := alias_of(canonical), by an in-line value swap that leaves every other byte unchanged (work/apply_alias_fix.py, src/ALIAS_FIX.json).
  - Checks: all 338 canonicals are A3 train; 0 rows are held out under either token; 0 rows hit the exclusion list under canonical, room group or either token.
  - ORCH approved the fix, and derivgen confirmed that canonical is the identity. Their v3.10.2 J/K rows need the same fix.
- Builder (mode j, j 118667): 61,772 rows; refused movement_margin 258 and rotation_near_180 831; 0 over length. A local dry run without frame checks gave the same counts. gt_replay is 2000/2000 on camera rows. Object rows differ from the trainer's fixed layer by 0.01 m in some printed f1 points, which are loss-masked tool output.
- Abs upsample (ORCH 0313Z/0325Z): 4 DB rows per abs trace, 2 byte copies in the original wording and 2 in VSI wording (f/cdc646ba, qid '#v1', 'Measuring from the closest point of each object, what is the distance between the A and the B (in meters)?'). A script check shows only the question and qid change. Without the VSI copies, T2 would never see the benchmark wording for abs, because the VQA abs rows use other paraphrases.
- Merge: work/t2_merge.py (stdlib) concatenates c1-routing-stream-v1 receipts with matching division, role, policy, tokens and calculator. T1's rows keep i 0..66910 byte for byte, and only declared copies repeat a qid. It has 7 CPU tests. The prep checks run locally (duplicate layout, exclusions) pass on all trace rows.
- Exposure per step, T2 routed vs T1 direct: hard 2.88 vs 5.35, medium 2.67 vs 3.57, abs 2.20 vs 5.22. Camera routing goes from 32 to 24.25 and non-target VQA rises x1.79. Abs reaches 0.94 epoch at step 1,000.

## Options rejected
- Keeping the stored alias: loses 32% of the rows, and abs falls to 1,177.
- A superset division for the outside rows: prep requires the routing division to equal the pose division, so it needs a trainer change.
- One combined mode-j build over the A2 and trace sources: it gives the same rows, but it rebuilds T1's rows instead of copying them and gives no reusable trace-only receipt.
