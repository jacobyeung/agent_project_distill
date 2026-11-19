Regeneration needs missing pinned generators and complete input manifests; raw datasets alone do not establish either byte identity or equivalent GT.
Command for every count, list, hash and proxy below: `PYTHONDONTWRITEBYTECODE=1 python scope.py`; methods, exact scenes, paths and full hashes are in `REGEN_SCOPE.json`. GB means decimal GB.

**(a) Missing GT rasters**

| Item | Exact scene list / output pins | Generator | Raw inputs and local state | Raw GB; compute |
|---|---|---|---|---|
| ScanNet: 80 | JSON `rasters.groups.scannet`; all NPZ SHA256 known | Original entrypoint/commit MISSING; candidate below | Instance mesh, segments/aggregation, boxes/alignment, poses/K and frame pins; loader contract/raw root MISSING | GB/scene, total and CPU/GPU-hours MISSING |
| ScanNet++ v2: 227 | JSON `rasters.groups.scannetppv2`; all NPZ SHA256 known | Candidate `build_t1_cr.py`, SHA `eef52cfe…`; related adapter `66772ccb…` | Mesh + segment/OBB JSON + aligned poses/per-frame K + COLMAP + exact pins; training inputs MISSING | Proxy 2.79–111.53 GB total (median-scenario 17.74); 0.55–33.46 worker-h (median 2.31); related adapter uses 0 GPU-h |

These 307 files affect 4,420 sources; no ARKit raster occurs in this missing list. Full 307-file GB and measured CPU-hours remain MISSING.
Candidate files expected at `/scratch/jjyeung/orch_n30/rows_a2/work/builder_cr/builder_cr/{build_t1_cr.py,raycast_cr.py}` are MISSING. Their recorded SHA256s are `eef52cfe0f1dcdb4e428a172bf3d0cd2cb59c8dc73c5cbce1f21b25fde5b09f8` and `80b2a1521c8215bf8a65ecea51eaec340a5d9887ae7f96fd3fb6a91cfbc4688b`. Neither is proven to be the original 307-file entrypoint.
Available adapter: `n30_mirror/rows_r1/work/codeB/build_rasters.py`, SHA256 `66772ccb5ee0721ce528ea4d02df398647f06ad5f6f96ba9859d4cfd87482910`; it builds R0-dev, not these training scenes. Commit MISSING. Its `r0lib.py` dependency is also MISSING locally.
The adapter specifies 32 × 240 × 320 samples, pixel centres +0.5, camera-z depth, majority face-instance assignment, first-vertex tie breaking, COLMAP convention checks and verified OBB extents. Recover the training version before adopting these choices.
Proxy basis: 71 R0 receipts (68 pass), 0.012–0.491 GB/scene, median 0.078; 8.8–530.7 elapsed seconds/scene, median 36.7. Multiply by 227; these are worker elapsed hours, not measured CPU-hours or a training forecast.
The proxy includes `scans/{mesh_aligned_0.05.ply,segments.json,segments_anno.json}`, sliced `iphone/pose_intrinsic_pins.json`, and `iphone/colmap/{images.txt,cameras.txt}`. It excludes RGB, full pose extraction, downloads and proof work. Its R0 scene inputs cannot replace training inputs.
Available raster consumer: `n30_mirror/rows_a2/v4/vsti/code/generate.py`, SHA `fceb45e6bee7aff7d8c4b388cdf0caf269c1141b42d06c24c6833d23afabcb88`; it uses fixed/hash-derived seeds. Row replay also needs the original alias/frame manifests and exclusions. All 307 target raster pins match `RASTERS_v3.json`; full hashes for consumer dependencies are in JSON.

**(b) Missing direction packs**

Each row lists retained direction rows, exact affected-scene counts by dataset (S=ScanNet, P=ScanNet++, A=ARKitScenes), and the full pack scene count reported upstream. Exact affected lists are in JSON; complete pack scene manifests are MISSING.

| Pack / SHA256 prefix | Retained rows | Affected scenes S/P/A | Full-pack scenes | Generator | Raw GB / CPU / GPU |
|---|---:|---|---:|---|---|
| weak_data easy / pin MISSING | 12,969 | 240/551/974 | MISSING | commit 73934511…; script MISSING | MISSING / MISSING / MISSING |
| weak_data hard / pin MISSING | 21,385 | 247/599/1027 | MISSING | commit 73934511…; script MISSING | MISSING / MISSING / MISSING |
| weak_data medium / pin MISSING | 15,547 | 245/546/981 | MISSING | commit 73934511…; script MISSING | MISSING / MISSING / MISSING |
| ARKIT_gaps / 6053fd47c70c0b25 | 3,508 | 0/0/399 | 1045 | r3 | MISSING / MISSING / MISSING |
| T0_gaps / 7a1c59097139f59d | 8,020 | 103/145/0 | 343 | r3 | MISSING / MISSING / MISSING |
| T0_gen_r2 / 7e4e92918e312afd | 9,831 | 107/149/0 | 340 | r2 | MISSING / MISSING / MISSING |
| T1H2_gaps / 9bf0518db09a07d8 | 3,428 | 0/140/0 | 222 | r3 | MISSING / MISSING / MISSING |
| ARKIT_gen_r2 / 9eecedf23da3bd91 | 5,421 | 0/0/427 | 1217 | r2 | MISSING / MISSING / MISSING |
| T1H1_gaps / b6ac18d55d697a23 | 3,732 | 48/120/0 | 492 | r3 | MISSING / MISSING / MISSING |
| T1H1_gen_r2 / ba96a4182147a384 | 5,009 | 50/134/0 | 414 | r2 | MISSING / MISSING / MISSING |
| T1H2_gen_r2 / c16c5db36e04c1ef | 4,520 | 0/149/0 | 212 | r2 | MISSING / MISSING / MISSING |

The packs affect 93,370 rows across 1,979 distinct recorded canonical captures. Do not sum overlapping per-pack scenes or treat retained scene lists as complete pack inputs.
r2: `/scratch/jjyeung/orch_cd/dose_pool/work/v314r2/dose_t0.py` SHA `58d03b0488bfad58e270ded1f0e594d9bca70de9ca87d3a912c34c58cb69fce8`; renderer `ground_rows_out/render_full.py` SHA `584d6e031f1970a522a8f9c476c07ed3cd2d1c1107fe10cf10cac6b5e39d102d`.
r3: corresponding `work/v314r3/dose_t0.py` SHA `dd73f017703417e11b022e5b2def31c3c0c41d73bd477c0bf961f4387edca1d0`; renderer SHA `63a7cbc068de174730b9e0030082ed5107e22a17ee19a39a34b4800f5a315344`. These are manifest pins; executable copies and commit IDs are MISSING in the inspected mirror.
The three weak-data packs record commit `73934511aff5dac8af4b3b12490a88762105dc24` and frame-map SHA `17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3`; their generator filename, frame-map filename and pack SHA256 are MISSING. Their exact expected pack paths remain in JSON; no remote path was probed.
ScanNet/ScanNet++ packs require the native geometry/annotation/camera inputs above plus original qid→instance roles, scene release, sampled-frame evidence, selection seeds, exclusions, templates and packing rules. T0 records `scannetppv2`; T1 records `scannetpp`. Do not infer release equality from canonical aliases.
ARKit packs additionally need stable annotated OBB IDs, the original mesh/depth visibility source, trajectory, per-frame intrinsics, timestamp/frame mapping and Training metadata. Native candidate filenames are listed separately in JSON; the exact loader and raw root are MISSING, so no fetch list is asserted.
All direction GB/scene, total GB and CPU/GPU-hours are MISSING: the full raw manifests, loaders and matching timing logs were not recovered. The R0 raster proxy does not price pack selection, role reconstruction or validation. Retained-row reconstruction may cost less than full-pack byte replay but cannot inherit its file hash.

**Local availability and verification**

`evidence/local_paths.txt` records the exact `ls -ld` command: training staging roots `orch_n30/{rows_a2,b12_cntapp}/work`, their checked mirrors, R0 raw roots, and explicit conventional dataset-root probes are absent. Only the checked R0 receipt directory exists; it does not establish raw-data availability. No raw directory was available to size with `du -s`.
This is a bounded path check, not proof that the entire node has no datasets. Fetch or restore is required for these expected paths unless an owner supplies another pinned local root; the training raw roots and exact raw-file hashes remain MISSING. No NFS or unreachable `orch_cd` path was searched.
Rasters: all target hashes permit exact checking, but deterministic byte replay is unproven. Pin raycaster/mesh versions, poses, float dtypes, ordering, NumPy and NPZ/ZIP/zlib behavior. A container mismatch cannot be dismissed without original member hashes/arrays or an independently accepted per-source GT proof.
Packs: eight full SHA256 targets are recovered; three are MISSING. Exact replay also needs JSON/float ordering, gzip headers/mtime and compression versions. Source-row hashes, a commit or a frame-map hash are not pack hashes.
Equivalent GT requires exhaustive source-bound checks of instance roles, frame visibility, signed-up/frame conventions, facing transforms, boundary margins, numeric operands and answers. Old labels or statistical agreement cannot certify equivalence. Available `build_away.py` is a downstream text/selection transform, not a raw-GT generator.
Before execution: recover the missing code/input closure; size only the named raw files; validate one pinned scene per dataset and one pack against hashes or an explicit equivalence contract; then estimate CPU time from that pilot. No pilot, regeneration or fetch ran for this scope.
Recommendation: **PARTIAL** — recover pinned builders and raw/frame/instance manifests first; do not bulk-fetch datasets or claim bit-for-bit/equivalent regeneration yet.
