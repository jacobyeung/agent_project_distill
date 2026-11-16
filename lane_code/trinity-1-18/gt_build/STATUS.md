# gt_build STATUS (trinity-1-18) — DONE, stopped 2026-11-15T21:16Z
- RESULT 20261115T2116Z_RESULT_rasters_built.md: 259/300 rasters equal pins (ScanNet 51/51, ScanNet++ 86/87, ARKit 122/162); 41 deferred; PIN_CHECK.tsv, VARIANTS.md in events/gt_build.
- RESULT 20261115T1921Z_RESULT_scorer_check.md: surviving official_mra differs from authority MRA (zero target, negative target, 0.85 threshold ulp); k1_report.py line 6 must change path.
- Outputs: out/dose_pool/out/{t1_gt,arkit_gt}/gt (pin-equal only), out/RASTERS_SHA256SUMS, out/K1_GT_RASTERS_259.tar (sha256 823ca442b262ea14b7b5990e4206ca5432e23805d62a7f3f105275e84a8a6460).
- Mirror: trinity-1-3.ib:/scratch/jjyeung/n30_mirror/gt_build/K1_GT_RASTERS_259.tar (same sha256, verified remotely).
- Staged inputs: stage/{scannet,scannetpp,arkit} (3.6 GB); governor records gt_build_{scannet,arkit,scannetpp} renamed .done.
- Variants and rejected builds: out/variants/, out/rejected/; code work/ (GT_BUILD_SCRIPTS.tar.gz in events, 52f4a3c9).
- Resume (if asked to chase the 41): rebuilding is ~1 min per variant with work/run_variant.py NAME BUILDER SRCSET CID...; then work/place_variants.py, work/pin_check.py, re-tar and re-mirror.
