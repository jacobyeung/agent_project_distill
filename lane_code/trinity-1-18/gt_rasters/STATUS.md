# gt_rasters STATUS (trinity-1-18) — DONE, stopped 20261115T1859Z
- RESULT 20261115T1859Z_RESULT_rebuild_scope.md: clean-room builder byte-exact on 6 pinned rasters (2 ScanNet-family, 4 ARKit); bulk priced (3.64 GB read, ~1 CPU-h); recommend rebuild now.
- Detail: events/gt_rasters/GT_RASTER_REBUILD_SCOPE.md; builder tar events/gt_rasters/GT_RASTER_BUILDER_CR.tar.gz (sha256 381944a5338a2c63e225e8fa3b39b597f95b47945e056edf185c0dfab568d34e) = work/builder_cr + work/PILOT300_INPUTS.json on 1-18.
- Lane work: work/proof_scannet, proof_pinned/{scene0475_01,spp_17c5e6a336}, proof_arkit, proof_arkit2, proof_arkit_{41098139,45261332} (inputs + rebuilt npz); work/PILOT162_ARKIT_LISTINGS.json, LOCAL_PINNED_79.json, LOCAL52_TIMELINE.json; work/repo_src (distill repo python copy), work/recovered (v1 recovered tar).
- Record: distill_design/K1_GT_RASTER_REBUILD_20261115.md (+INDEX line).
- Resume (if bulk assigned): governed streams per dataset into /scratch, build with builder_cr (24 procs, OMP_NUM_THREADS=1), sha256 vs CAPTURES pins, defer mismatches.
