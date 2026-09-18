# VSI-590K ground-truth teacher feasibility — result record

**Date:** 2026-09-18. **Decision stage:** design. **Final gate:** GO for the r1313 training adapter and first scene smoke; collection admission remains pending. **Execution:** read-only feasibility complete; teacher smoke not_run. **Scientific status:** untested. **Controlling reason:** source geometry, instance annotations, and camera assets already cover all 396 selected ScanNet-family videos and 32,513 questions; a prepared ScanNet++ scene has verified sampled RGB correspondence and all 32 selected source poses. **Attempt budget:** planned and actual zero GPU runs, zero model/API calls, zero question labeling; bounded local inspection, CPU video comparison, and primary-source web reads only.

## 1. Hypothesis and mechanism

Use the existing r1298 ground-truth-perception agentic ablation as the perception donor for the r1313 Gemini 3.1 Pro SPLIT training teacher. Released training-scene geometry and instance annotations replace predicted geometry and SAM3 masks. The student receives the question and the same 32 RGB frames; it receives no source geometry or instance annotations at benchmark inference. Better teacher perception may increase correct, complete training traces, but this inspection establishes neither acceptance rate nor gains in tool-free OneThinker8B or Qwen3.5-9B.

The immediate target is 20,000 accepted traces from the fixed 50,000-question pool. ScanNet-family raw assets cover 32,513 questions, so this subset alone needs at least 61.51% acceptance to supply 20,000. That arithmetic is a capacity requirement, not an acceptance forecast. ScanNet++ alone contains 19,851 questions and cannot reach 20,000 without another corpus. No measured preparation or collection runtime supports a completion-date estimate yet.

## 2. Exact implementation and provenance

### Selected pool and physical source coverage

The pool authority is `/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/membership/v2/TRAIN50K_SCENE_REUSE_MANIFEST.json`; rows are `train50k_scene_reuse_answer_free.jsonl` in the same directory. This lane recomputed corpus and scene counts directly from all 50,000 answer-free rows. Source release: [VSI-590K revision 346fbd4e41dec974bf24894d0541a49327ee6669](https://huggingface.co/datasets/nyu-visionx/VSI-590K/tree/346fbd4e41dec974bf24894d0541a49327ee6669). The official card describes six video corpora and question generation from scene metadata; the main release contains media archives and question JSONL, without a separate camera manifest. [Official card](https://huggingface.co/datasets/nyu-visionx/VSI-590K).

| Corpus | Selected questions | Selected videos | Evidence and next dependency |
|---|---:|---:|---|
| ScanNet++ v2 | 19,851 | 162 | All 162 have local aligned mesh, segment/instance annotations, iPhone aligned poses/intrinsics, COLMAP cameras/images, raw RGB video, and depth.bin. Full original laser point clouds are absent at the checked `pc_aligned.ply` paths; meshes suffice for the donor. One representative video alignment checked below. |
| ScanNet | 12,662 | 234 | All 234 have local `.sens`, annotation mesh, segmentation, and aggregation files. Exact VSI-video-to-sensor-frame correspondence remains to be checked per video. |
| ADT | 8,094 | 32 | Official VSI metadata JSON matches all 32 selected names; full dynamic depth/mask/pose assets and preview-video timestamp correspondence remain pending. |
| ARKitScenes | 7,330 | 571 | None of the 571 selected IDs exist in the checked local raw Training/Validation roots; the local root contains Validation only. Official raw assets are downloadable, but extraction and video timestamp alignment remain pending. |
| ProcTHOR | 1,735 | 110 | Source simulator exists; the exact released traversal/house/camera mapping was not verified. Pending. |
| S3DIS | 328 | 38 | Official VSI metadata JSON matches all 38 selected room names. Source-camera mapping for these rendered videos remains pending. Too small to drive the 20k target. |

Counts describe filenames and source inventories, not hash-verified launch readiness. Six training media archives are already local; the existing archive receipt is `media_archives/ALL_ARCHIVES_VERIFIED_RECEIPT.json`. This lane did not rehash large media or download large assets.

ScanNet++ source root: `/data2/jjyeung/raw_datasets/scannetpp/data/<scene>/`. Required files are `scans/mesh_aligned_0.05.ply`, `scans/segments.json`, `scans/segments_anno.json`, `iphone/pose_intrinsic_imu.json`, and `iphone/rgb.mkv`. All 162 also have `iphone/depth.bin` and `iphone/colmap/{cameras,images}.txt`. ScanNet source root: `/data2/jjyeung/raw_datasets/scannet/scans/<scene>/`, with `<scene>.sens`, `<scene>_vh_clean_2.ply`, `<scene>_vh_clean_2.0.010000.segs.json`, and `<scene>.aggregation.json` present for all 234.

ScanNet++ supplies an aligned laser-derived mesh, annotated segments, and source cameras. Its aligned poses refer to mesh coordinates; raw ARKit poses do not. The iPhone depth images use millimeters. This is source scan/reconstruction supervision, not mathematically exact surfaces. [Official ScanNet++ format](https://scannetpp.mlsg.cit.tum.de/scannetpp/documentation). ScanNet supplies reconstructed meshes, RGB-D streams, camera poses, and instance semantic segmentations; its aggregation labels join to per-vertex segments. It is also a reconstructed source scan, rather than a perfect scene model. [Official ScanNet repository](https://github.com/ScanNet/ScanNet).

### Exact frozen perception donor

Use `/data2/jjyeung/agent_project_data/r1298_req229_common_gt/v14/cells/gt_gt_high/package/`. Its `contract.json` identifies `geometry=mixed_gt_gt`, `grounding=gt_masks`, Google-native `gemini-3.1-pro-preview`, temperature 0, high thinking, and a 32,768 output-token cap. The actual package includes generated adapters missing from the tracked source directory. This lane verified the following runtime files against the donor contract:

| File | SHA-256 of inspected code |
|---|---|
| `gt_channel_adapter_r1298.py` | `e01470bcd868b3c6d680c043ee62a7b9d8658c10d7a8b32358ab4f027f2d1f9e` |
| `gt_geometry_provider_r1298.py` | `06650b04480dd4eadd5c13b71314b6c9d220a6c220427e1a73ca9838da98f85d` |
| `gt_grounding_provider_r1298.py` | `121bc05ea43a615db7db28ee192c4282e525dc9298e1ef75559185bb5b41c73c` |
| `gt_label_matcher_r1298.py` | `e56d7c165a90bb6dcc63f7566378c57cac3a8b4c25214030bd37ae96fbc9e12a` |
| `frame_alignment.py` | `87c7ecca5fb487f26fc50a4bd6e18df4e7180efc9fd74e86f7c9419c56998ad0` |
| `spatial_agent_r1298.py` | `d5ecff3266040de14a9239e99b11fc455f7b8904150e5d075650a717d64b08a6` |

Maintained construction code is `agent/rounds/candidates/r1298_req229_common_gt_v14/source/`, particularly `materialize_sources.py`, `mixed_geometry.py`, and the provider modules. Reuse these perception mechanisms through a new immutable r1313 adapter. Keep the existing training collector's native trace/summary export, offline grading, and training membership. Authenticate the same 32 RGB frames for student input; the teacher may receive its initial text/question and privileged GT through tools. Do not copy the evaluation runner or its evaluation-specific admission manifests.

The agent calls `load_selected_dense(scene_id, point_cloud_source)` at lines 1198/1471. `_run_sam3_request` routes to the GT provider's `segment_frame` at lines 2678–2681; the video mask path routes to `segment_video` at 2934–2935. Grounding operates on scene, frame, and requested label, and returns every matching visible instance. The inspected provider has no question ID, task answer, or question-specific target-instance argument. Label matching is imperfect: its generic synonym/token rules can match broader classes. Geometry alone cannot resolve a referred object's name.

Three donor constraints require explicit training adaptation. First, provider constructors enforce evaluation counts `(801,118,121)`, 121 scene records, and a frozen evaluation membership; replace those assertions with the authenticated training scene subset. Second, the ablation renders through an R2 intrinsics carrier and intersects predicted/GT support for factorial comparability. The GT training adapter should bind official source intrinsics and GT-valid support, so predicted geometry is unnecessary. Third, the donor contract uses text-only control with zero inline frames. The authorized training teacher may likewise start from text/question; its perceptual-evidence acceptance must establish receipt of successful GT tool outputs. The student receives the authenticated 32 RGB frames. These changes prevent a claim that the new training collector is byte-identical to the ablation.

The donor uses a VLM in `find_frames_with_object`. The authorized r1313 amendment connects frame search, boxes, masks and points to the donor's existing GT methods, removing avoidable VLM perception from those methods while retaining Gemini reasoning. This is an explicit change from the donor and must pass the implementation gate; it does not introduce a separate perception engine. The controlling amendment and teacher-input clarification are `runtime_control/gt_teacher_r1313/GT_PERCEPTION_AMENDMENT.md` and `CONTROLLING_USER_CLARIFICATION.md` under the training root.

### Fastest representative scene smoke

Use ScanNet++ `104acbf7d2`, which has 297 selected questions across all seven training classes. Its existing selected-frame receipt is `/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/collector_assets_v2/scene_assets/scannetppv2__15b109bd584d/frames_receipt.json`.

The VSI video `media/scannetppv2/104acbf7d2.mp4` contains 11,354 frames at 60 fps, 640×480. The original `iphone/rgb.mkv` has 11,354 frames at 60 fps, 1920×1440. Read-only OpenCV checks compared identical ordinals after area-downsampling the original:

| Ordinal | Mean absolute RGB/BGR byte difference | Pixel correlation |
|---:|---:|---:|
| 0 | 2.1401 | 0.998537 |
| 5493 | 2.5464 | 0.998370 |
| 11353 | 2.4695 | 0.997250 |

This is strong sampled correspondence evidence, not exhaustive frame-by-frame identity. All 32 selected `frame_XXXXXX` stems exist in the official pose JSON with `aligned_pose` and `intrinsic`; its 11,354 keys match the video frame count. The JSON uses singular field names `pose`, `aligned_pose`, and `intrinsic` inside each frame record. All 176 `segments_anno.json` object groups already include an OBB.

The r1313 builder should:

1. Bind that receipt, original scan inputs, source-video identity, and exact 32 ordinals. Extract source `aligned_pose` and intrinsic matrices; convert the 1920×1440 K to the 640×480 image canvas by scaling its first two rows by one third, then apply any explicitly defined render-grid resize/crop. Preserve camera-to-world convention and metric units.
2. Adapt the existing donor scene and grounding manifests to training IDs. The instance inventory is `segGroups` with `objectId`/`id`, label, and OBB. The donor expects OBB `axesLengths` as **half-extents**. The r1313 build receipt identifies this scene's source lengths as full extents and divides them by two; the implementation gate must verify that conversion. The grounding mesh NPZ expects `vertices_world`, triangular `faces`, and `face_instance_ids`; its annotation JSON expects `instances[].instance_id`. Derive these from the training mesh/segment memberships.
3. Use donor projection, scene-depth occlusion, and visibility masks on the selected frames. Do not return unseen full-scene objects as visible objects. Keep full-scene inventory available only behind the donor's normal visibility-controlled tools. Keep geometry and grounding cameras on the same pixel canvas.
4. Preserve the donor's `canonical_geometry` convention for points and camera poses together: meters, first-camera origin, +Z gravity up, +Y initial horizontal view. Do not estimate a new scale or fit a predicted camera trajectory. Preserve source-world coordinates inside mask projection.
5. Produce the training dense interface: `pts3d_world[32,H,W,3]`, `depth_z[32,H,W]`, `intrinsics[32,3,3]`, `conf[32,H,W]`, boolean `mask[32,H,W]`, `camera_poses[32,4,4]`, and original `indices[32]`. Hash-bind the new scene receipt and sources. The current training loader checks exactly these arrays and authenticated frame assets.
6. Verify reprojection and a visible instance overlay, run the inherited tool path, then run one real Gemini teacher question and grade it separately. This lane did not execute that smoke. After it passes, fill the ready ScanNet++ scenes while adding ScanNet video/sensor mapping; do not wait for all six corpora.

The first scene can reuse its existing RGB frames; its predicted dense arrays do not define the GT teacher. The mesh/instance preprocessing and the new training admission bindings remain implementation work, owned by the r1313 Devin lane.

### Other released assets and actual access limits

The official Cambrian-S repository links a separate [VSI-590K-MetaInfo release](https://huggingface.co/datasets/nyu-visionx/VSI-590K-MetaInfo), revision `df1d7c979ef84d4862495fcd55190ac914de81ac`. An unauthenticated API listing succeeded. Small JSON reads also succeeded. `s3dis_meta_info_v2.json` is 1,212,553 bytes and contains `video_path`, object counts, object bounding boxes, room size, and dataset; its room keys cover 38/38 selected S3DIS videos. `adt_video_meta_info_jy_20250430.json` is 7,889,082 bytes and contains scene name, dataset, object counts, bounding boxes, and video path; stripping `ADT_` and `_preview_rgb` matches 32/32 selected ADT videos. These are derived scene annotations, not dense geometry or frame masks. Neither inspected JSON establishes selected-frame visibility. Keep them separate from task-answer labels. [Official release announcement](https://github.com/cambrian-mllm/cambrian-s).

The metadata repository also lists `metainfo_mega.zip` (1.041 GB), `scannet_train_frame_category_info_20250304.npy` (658.8 MB), and `scannetpp_v2_train_frame_category_info_20250420.npy` (1.709 GB). They were not downloaded or deserialized; their detailed contents and exact training coverage remain unknown.

ARKitScenes publishes per-video raw mesh, annotations, depth, camera intrinsics, and timestamped trajectory; its trajectory translations are meters and depth PNGs millimeters. Box annotations are not pixel instance masks. Its downloader supports selecting video IDs/assets; this lane did not verify a specific asset download. [Official ARKitScenes formats](https://raw.githubusercontent.com/apple/ARKitScenes/main/DATA.md). ADT publishes object trajectories, segmentation, depth, and camera calibration, but its full downloader requires signup and expiring links; exact local access was not established. [ADT format](https://facebookresearch.github.io/projectaria_tools/docs/open_datasets/aria_digital_twin_dataset/data_format), [download procedure](https://facebookresearch.github.io/projectaria_tools/docs/open_datasets/aria_digital_twin_dataset/dataset_download).

The 2D-3D-S release includes meshes, point/instance labels, camera poses, and rendered RGB/depth, with a license-agreement download step. It does not by itself prove how the VSI S3DIS MP4 ordinals join those cameras. [Official 2D-3D-S repository](https://github.com/alexsax/2D-3D-Semantics). ProcTHOR provides a simulator/house generator; reproducing arbitrary houses would not establish the selected VSI traversal. The exact asset/version/trajectory mapping remains pending. [Official ProcTHOR repository](https://github.com/allenai/procthor).

ScanNet requires its source-data agreement for new downloads; the selected source files are already present locally. ScanNet++ has dataset terms, and its required source files are also local. This lane did not inspect account credentials or claim a new legal approval. Public metadata access succeeded; no new large download or credential request is needed for the first ScanNet-family smoke.

## 3. Revisions

| Revision | Change | Reason | Outcome |
|---|---|---|---|
| v1 | Bound the feasibility decision to the existing all-GT ablation and actual selected training assets. | The user requested reuse of the established perception mechanism. | r1313 donor, first scene, and adapter boundary handed to collection ops. |

## 4. Reviewer findings

No reviewer swarm or formal gate ran. The source inspection found implementation requirements, not a reviewed launch approval: evaluation-only coverage assertions; estimated K/common-support dependence; text-only donor input; half-extent OBB semantics; scene-level rather than question-specific label matching; and incomplete per-corpus frame alignment. Each is stated in section 2. No source evidence establishes accepted-trace yield or student improvement.

## 5. Final decision and controlling reason

GO for r1313 implementation and the representative ScanNet++ smoke. Local sources cover 65.026% of the fixed question pool and include a directly aligned prepared scene. This is sufficient to begin the requested training adapter without a source-download campaign. Bulk collection starts only after the new training bindings and real tool/teacher smoke succeed. Keep predicted-teacher traces under their existing provenance; GT traces use a separate run root, package identity, scene receipts, and archive metadata.

## 6. What would change the decision

A failed image/pose join, incompatible OBB convention, unsupported source labels, or wrong source-world projection would block the affected scene until repaired. A successful first smoke establishes executable collection, while measured acceptance and throughput determine whether the subset can supply 20,000 traces. Only student training and tool-free evaluation can establish the intended benchmark gains.

## 7. Salvage and non-revival boundary

Reuse the donor's perception tools, source annotations, and existing selected RGB frames. Keep benchmark evaluation manifests, question-specific mappings, task-answer labels, and predicted-provider arrays outside the new teacher's source closure. Offline source labels remain the acceptance grader's input. Do not modify frozen r1298/r1311 files. The separately authorized benchmark-trained student diagnostic may use existing r1298 GT-perception traces, but its examples and results must remain distinct from the clean VSI-590K training campaign.

For that diagnostic, the exact existing run root is `/data2/jjyeung/agent_project_data/r1298_req229_common_gt/v14/cells/gt_gt_high/run`; category directories, sibling `offline_audit`, and `receipts` exist. Its contract lists 264 inference rows and the teacher pin above. A registered answer-bank pointer and the number of complete/correct traces were not verified here. The student-design lane received these exact paths.

## 8. Audit receipts

Evidence was observed on `trinity-1-8` through bounded direct filesystem reads and CPU OpenCV comparisons. The training manifest/answer-free input and all raw geometry/annotation/video sources are path-only here (`hash=omitted_unsafe` for raw annotation-bearing data). Donor code hashes appear in section 2. No executable implementation, large download, experiment launch, or source question solving occurred. The report is the sole file this lane writes. The parent owns its path-limited commit and campaign bookkeeping; that dispatched-worker rule takes precedence over the general worker-commit instruction.

## 9. Handoff

Collection ops owns r1313 implementation through Devin Astra, max effort, priority; it has received donor hooks, source paths, frame checks, and training-specific differences. The parent owns the experiment/request record. No benchmark score or accepted-training-trace claim is made by this result.
