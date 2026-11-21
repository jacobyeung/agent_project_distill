# R0 exclusion checks: inventory (lever5, read-only, trinity-2-28, 2026-11-21)
Read about 25 files/dirs on /data2 and /data3 (records, one tsv, one JSON, one PLY header); no copy, ssh, Orchard, Git.
NFS bytes read by me: about 0.5 MB (records ~0.3 MB, R0_SCENES.json 0.32 MB, 400 B of one PLY).
D = /data2/jjyeung/agent_project_data/distill_design

## Check 1: T0 / CP1 stream scene lists through test_exclusion.py
- Compares: the R0 room list (D/R0_RESERVE_20261116/R0_ROOMS.txt, 7,482 B; R0_SCENES.json 319,810 B) against each stream list, through the aliases (native id, rung1/rung2/v590kgt/posedata tokens). Collision = any R0 capture's native id, room id or alias token occurring in the list's text. test_exclusion.py (9f25653f) = 3 tests, mutation check included.
- No separate T0 or CP1 scene list exists on /data2 or /data3 that I could name. Manifests from which scene ids follow (D/AWS_COPYOFF_MANIFEST_20261109.tsv, 100,192 B, rows A12, A13, A27, A28):
  - T0 routing receipt bc67ca08: AWS ap/244cdf20/f/bc67ca08 (receipt.json, rows.sqlite); "receipt copies only in p3_build/work/aws_t0/evidence" (p3_build on a lane host; not found under /scratch/jjyeung/orch_n30 here); queued to Mind.
  - T0 prep receipts 13e69a8d, 4df58a04: AWS ap/244cdf20/arm/{13e69a8d,4df58a04} (receipt.json, pose_mix_order.json); not queued. Pinned in p3_build/work/aws_cp1x/EXTERNALS.json.
  - CP1 prep output: AWS ap/f2ad01ad/arm/0435c16e and ap/f2ad01ad/k/ (18 files incl. 66c427e2, dafa4a9c, 600ef69d, 932c0c4e, 99e6eed6); receipt a7edbb91; queued to Mind, not on Mind then.
  - A1 pose arm 6f27ae81 + training-scene lists (ap/e84d901c/z/{4c230a7e.json,...}): Mind new/e84d901c_z.tar (member list unchecked) and GCS q7/7822a58d; a local copy at heads_up/work/aws_a1/kit/z/4c230a7e.json (host unknown).
  - Sizes: unknown for all of these ("unknown (index files)" in the tsv).
- Already partly covered: division A3 f41d15aa and A1 4c230a7e bound the streams (TRAIN_EVAL_SCENE_AUDIT_20261110.md rows 54-82); R0 was tested against A3, kit07, D0 v5, LEG-S1 lists, BENCH v2, exclusions, dev-S1, WITHHELD_80; T0/CP1 stream-specific lists are the gap.
- AWS-free reach: the only Trinity-side copies found are lane-scratch paths (p3_build, heads_up) not on this node, and the K1 mirror dirs under /scratch/jjyeung/n30_mirror hold none. D/N_SCENE_CENSUS_ROWKEY_20261121.md says no Trinity mirrors exist for the pose stores or base on 1-18 or 3-30.
- NFS bytes: reading the lists is KBs to a few MB (receipts, JSON and pose_mix_order.json are index files); test_exclusion.py itself runs on /scratch (1-18, copy may also be in the 3.80 GB archive /data3/jjyeung/n30_b10_reserve/R0_RESERVE_20261116.tar or mirror trinity-1-3; do NOT scan the tar, it is a full-file read). Time: CPU seconds.
- Reads under 20 MB from NFS: YES for the lists on Trinity (R0_SCENES.json 0.32 MB + any receipt/pose_mix_order files). If a list exists only on AWS/GCS/Mind (rows.sqlite is not needed, only receipt.json), fetch the small JSON members only, not the row stores; the fetch crosses the head node, so under 20 MB needs no governor registration but needs an Orchard/GCS call, which is outside my brief.

## Check 2: mesh-similarity scan, 98 R0-dev ScanNet++ meshes vs trained ScanNet++ scenes
- Compares: per dev scene, PLY header (vertex/face counts) and axis-aligned bbox of the aligned mesh against each trained ScanNet++ scene (685 in streams per POSE_SCENE_DIVERSITY_20261109.md; plus 50 benchmark scenes); collision = near-equal counts and bbox extents (recapture of the same room); only near matches get full-mesh comparison. Dev list: D/R0_RESERVE_20261116/R0_DEV_ROOMS.txt (2,101 B; 98 usable after 2 pose-gate deferrals; 100 listed).
- Inputs: /data2/jjyeung/raw_datasets/scannetpp/data/<scene>/scans/mesh_aligned_0.05.ply (1,001 scene dirs here). Sampled 04d0dc245b: 64,594,344 B (1,555,347 vertices x 15 B = 23.3 MB vertex block, 3,174,146 faces); the _semantic.ply 70.8 MB. Trained-scene id list: the 685 ScanNet++ rooms in the stream receipts (not located as a file; the R0 census lists the 1,001 dirs from which the rest follow).
- Finding: a PLY header holds counts, not a bbox. Header-only fingerprint (vertex and face counts) is about 1 KB per mesh = about 3 MB over about 783 scenes (a few thousand small NFS reads, trivial time). A bbox needs the vertex block: about 23 MB per mesh (one sample; scale by vertex count) = about 18 GB over 783 meshes = about 38 min at 8 MB/s, over the 30 GB/h cap only if sized wrongly. Cheaper bbox: read each mesh's vertex block only for dev scenes (98 x 23 MB = 2.3 GB, about 5 min) and the trained ones only when counts match within a tolerance.
- Full meshes for near matches: 64.6 MB each; "under 1 GB governed" holds up to about 15 near matches.
- NFS bytes: 3 MB (headers) to 18 GB (all bboxes); upper bound for whole files: 783 x 64.6 MB = about 50 GB (about 1.7 h at 8 MB/s; do not do). Over 20 MB, so governed.

## Check 3: MMSI-Video clip mapping (134 clips)
- Compares: phash of about 6 frames per MMSI-Video clip against phash of 6 frames per training recording; collision = phash match, giving the clip a scene mapping, then room exclusion. 134 clips = 38 ScanNet, 59 ARKit, 37 ScanNet++; clips are anonymized (scannet_fix_NNNN, arkitscenes_fix_NNNN, scannetpp_NNNN). The other 50 clips are already covered (BENCH_SCENE_EXCLUSIONS_20261108.md line 82).
- Inputs: MMSI-Video clips: DATA_MAP.md names AD/external_benchmarks/mmsi_video, but that path does not resolve under /data2/jjyeung or agent_project_data (location unconfirmed). Training recordings: about 4,400, frames in AWS shards (ap/bdad3598/f) or on 0-13; sizes not stated. Local ScanNet/ScanNet++ PNG store: 3-30 /scratch/jjyeung/frames64/ (about 20.7 GB, local disk, 1,285 scenes), not NFS.
- NFS bytes: about 4,400 x 6 frames = about 26,400 PNGs (about 0.3-0.5 MB each at 640x480) = about 8-13 GB if read from NFS; zero NFS if run on 3-30 local frames64 plus the MMSI frames (134 x 6 = 804 frames, under 0.5 GB). CPU: phash about 10 ms/frame, minutes; the cost is IO. The record says the shard work is CPU on AWS or 0-13, not NFS.

## Unknowns
- Whether any T0/CP1 scene list sits on Mind/GCS only, and exact sizes; location of p3_build and heads_up lane roots.
- Mean ScanNet++ mesh size (one sample) and the exact trained-scene id file for check 2.
- Real path of MMSI-Video videos and whether frames of the 4,400 recordings are on 3-30 local disk.
