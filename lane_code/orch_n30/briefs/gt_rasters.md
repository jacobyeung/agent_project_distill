# Lane gt_rasters (runs ON trinity-1-18): find the builder of the K1 ground-truth rasters and prove it on one pinned raster

Lane folder: `/scratch/jjyeung/orch_n30/gt_rasters` on trinity-1-18. Events folder: `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/gt_rasters/`. First read `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md` and obey it. No GPU. This is a scoping lane: you find, prove on one capture, and report. You do not start the bulk rebuild.

## Why
The K1 grounding test (step P1 of the re-freeze) scores the deployed mask backend against ground-truth rasters of 300 training captures (51 ScanNet, 87 ScanNet++, 162 ARKitScenes). Those rasters (`orch_cd/dose_pool/out/{arkit_gt,t1_gt}/gt/*.npz`, 1,367,513,161 bytes, each pinned by sha256 in the kit's `CAPTURES.json`) existed only on trinity-2-18, which is down, and no copy survives. K1's GPU phases need no raster; its CPU kill test and selector refit do. The orchestrator must decide whether to rebuild the rasters or wait for the node.

## What is known (lane k1_ops3, same node; read its events first)
- `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/k1_ops3/20261115T1724Z_BLOCKER_gt_raster_builder_absent.md` and `ANSWER_1704_DETAIL.md`.
- 93 rasters of the same family are on this node under `/scratch/jjyeung/orch_cd/dose_pool/out/{arkit_gt/gt,t1_gt/gt}`; 79 of them are in the kit's inventory and match their pins. None is one of the 300.
- Raster schema: depth, inst [32,240,320], K, K_frames, c2w, valid, ids, labels, obb_centroid/lengths/axes, frame_indices.
- The only code in the mirror that writes this schema is `/scratch/jjyeung/orch_cd/integ_v3/work/generator/derivgen/native.py` (`prepare_native`, a converter from FIRST_HITS, a labelled mesh, calibration, label provenance, a selection record and an RGB manifest). No code in the mirror produces FIRST_HITS for these captures.
- The kit learned raster paths from `dose_pool/out/POOL_S1/*_admitted.jsonl.gz` rows (`gt_authority.gt`) and `dose_pool/out/t1_gt/REGISTRY_H1.json`, `REGISTRY_H2.json`; none is on this node.
- The kit is `/scratch/jjyeung/orch_cd/k1_build/work/kit_k1a` (read-only for you; it is the only copy). The mirror `/scratch/jjyeung/orch_cd` is local disk: you may `grep -r` inside it, read-only.
- Candidates for the builder: the distillation repository `/home/jjyeung/agent_project_distill` (ground-truth adapters, materialization wrappers, `tools/gtmeasure`; `docs/VERIFICATION.md` names verification recipes) and the generator code archived on Mind (batch 4 holds derivgen; not reachable from here without a copy, so say what you would need).

## Reading the repository (it is on /home: stay light)
List its top level and one level below with plain `ls` (no `-R`, no `find`, no recursive grep, no Git command). Pick the code folders that can hold the rasterizer, check each folder's size with a single-level `ls -la`, and copy only Python sources of those folders into your lane folder as one tar stream (`tar cf - --exclude='*.pyc' <folders> | tar xf -`), under 20 MB in all; larger needs the orchestrator's word. Search and read your local copy.

## Tasks
1. Identify the code path that produced a raster of this family from source data: which module renders first hits (mesh, poses, intrinsics to depth and face index), which assigns instance ids and labels, which writes the npz. Name every input per dataset (ScanNet, ScanNet++, ARKitScenes): files, where they live today (`/data2`, `/data3/shared/datasets`, a node's /scratch), and their sizes per capture, from single-directory listings of one example capture per dataset.
2. Prove the path on ONE of the 79 pinned rasters that are on this node (choose the capture whose inputs are smallest): rebuild its npz on CPU in your lane folder and compare array by array with the existing file, then by sha256 with its pin. Byte equality is the goal; if arrays are equal and bytes differ, find why (compression, key order, dtype, library version) and say whether it can be made equal. The inputs for this one capture may be read from /data* as one stream under 500 MB (registered with the governor if above 20 MB, as the rules say).
3. Price the bulk rebuild for the 300 K1 captures: can their identities and frame indices be derived without the lost POOL_S1 rows and registries (from the kit's `CAPTURES.json` and manifests)? Total input bytes to read from /data* per dataset, CPU hours on this node (96 cores, share them: use at most 24), output size, and every input that no longer exists.
4. Write one RESULT event: builder found or not; the proof's outcome; the bulk price (bytes, hours); your recommendation (rebuild now, or wait for trinity-2-18) with the reason. Put the detail in `GT_RASTER_REBUILD_SCOPE.md` in your events folder. Then stop and leave the lane folder as it is.

If no builder can be found in the repository or the mirror, say exactly which step is missing and what a from-scratch rasterizer would have to match, in a BLOCKER event, and stop.
