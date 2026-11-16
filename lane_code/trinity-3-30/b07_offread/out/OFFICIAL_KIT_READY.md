# Official read kit (queue brief 07): state on 2026-11-16 17:00Z

The direct reader is ready for both benchmarks and both exports; the harness and end-to-end readers are built and pass CPU fixtures on both benchmarks but wait on owner inputs, so no routed official number can be read yet. ReVSI ranks first.

## Matrix (benchmark x reader; exports step544 and the init-rule D0 export bind the same way)

| Reader | ReVSI official999 (999 items, 302 videos, 7 categories) | VSI-Bench (5,130 items, 288 videos, 8 tasks) |
|---|---|---|
| direct (build R) | READY: five direct categories, 679 items; reproduces 64.94 [61.3, 68.4]; D0 export needs the init-selection JSON | READY: six direct tasks, 4,008 items; reproduces 68.77 [66.5, 71.0]; same |
| harness (build N) | NOT READY: P8 freeze file with g3t_source original, K1-refit selector, SAM 3 Orchard source, ReVSI media fold + remap of 2 suspect videos (P8 pass; media staged and hashed, receipt events/b07_offread/REVSI_MEDIA_RECEIPT_20261116.json), production-CONFIG rehearsal | NOT READY: P8 freeze file, SAM 3 source, VSI media sizes and receipts, rehearsal |
| e2e (build N, b04 core) | NOT READY: b04 artifact manifest, EAT-1 PASS, loaded entry; ReVSI media fold (P8 pass); rehearsal | NOT READY: same as ReVSI plus VSI media |

## Pieces and hashes
- offkit (binding, frame guard, aggregation, labels, adapters): `/scratch/jjyeung/orch_n30/b07_offread/kit/offkit`; bind bd74a97f, report 2656c053, frames 2ed9fcc1, adapt_native 8b90fdcb, adapt_direct 667b19b9, spec 539a67a3; 59 tests. Reviews review_offkit and review_offkit2: all fixes applied.
- Build R (direct re-bind): `builds/R/out/REBIND_READY.md`; package_vsi.tar 9af22265, package_revsi.tar 3a639231; 50 tests (49 pass, 1 skip; run with ROFF2_ROOT=/tmp/a_900000_<hex>), CPU rehearsals on RAM and production-style roots; review fixes landed; offkit pinned at run time; in-job paths are random tokens and job names a15_cot_ap + 16 hex.
- Build N (native worker, harness and e2e readers): `builds/N/out/NATIVE_KIT_READY.md`; code.tar 66d1a0a7; 125 tests (122 pass, 2 skip; the reviewer case R4 fails by construction, a sibling test covers it); synthetic CPU worker fixtures pass for both benchmarks and both readers through all seven phases (stage, frames, towers, identity proof, canary, read, score). The harness runs C8r's real decoder and proposal/cache path; the e2e reader runs a pinned b04 snapshot (vendor/b04_54dce738597e). Answers reach the official scorer byte-equal; C8r's scripted unit-conversion arm is never scored. Review review_offnative: fixes 1-6 applied (ReVSI prompt indices, unserved budget 2048+64, reduced proof, naming, VSI-Bench sharding); re-review review_offnative2 pending.

## Frames
- Frame count and layout are binding parameters. Step 544 and the D0 lineage train on 32 anchors, duplicated; a 64-anchor read of them is refused without an override that every report prints. 64 spread and 32 duplicate send the same 64 frames and 32 temporal groups to the processor, so visual tokens are about equal; a 64 read waits for a 64-trained export.
- Dense G3T on ReVSI uses the official 64-frame clips, then selects the 32 model anchors (`hf_metadata/sampled_video_frame_idx.json`: the 32-frame indices are a subset of the 64-frame indices for 302/302 videos; mapping sha aaa9a53b). `clip32` is a diagnostic only.

## Time estimates (from job 170056's measured per-item rates; extrapolations, not measurements)
- ReVSI harness: routed primary decode 1.95 H100-hours plus G3T 0.32, so at least 2.26 before SAM 3, direct items, unserved decodes, proof and staging (queue expected 1-2).
- VSI-Bench harness: routed primary decode 6.11 plus G3T 0.30, so at least 6.41 (queue expected 3-6).
- Direct reads: 35 minutes VSI-Bench and 13 minutes ReVSI (jobs 170008, 170037) plus D0 staging.

## Open inputs (owners)
P8 freeze file with g3t_source and backend values (P8 owner); K1-refit selector that passed its kill rules (K1); init-selection JSON after D0 ends (init-rule owner); b04 artifact manifest, EAT-1 PASS and loaded entry (b04, b03); SAM 3 checkpoint Orchard source (sha 9999e234); ReVSI media are staged on Orchard and hashed (receipt events/b07_offread/REVSI_MEDIA_RECEIPT_20261116.json); the P8 pass folds the hashes and remaps two misaligned videos (42899739, 48018572). The five 170056 distance mask files are lost, so the identity proof is reduced for distance items. VSI media: all 288 on Orchard (3.73 GB).

## Mirrors
trinity-1-18:/scratch/jjyeung/n30_mirror/b07_offread/ (see STATUS.md for file names and sha256).
