# fb_pack removal candidates (never deleted by the lane; orchestrator decides). Sizes at 2026-11-19T21:31Z.
## trinity-1-18 (100 GB free at 21:31Z)
- /scratch/jjyeung/orch_n30/fb_pack/patchArev/work/test_runs (722 MB): gate-run test fixtures of review fbp_patchArev; verdict and results/*.json stay.
- /scratch/jjyeung/orch_n30/fb_pack/route/out/shards (424 MB) and fb_pack/cam/out/shards (32 MB): 2,000-row shard copies used for dry intake only; the rows, envelopes and receipts stay.
- /scratch/jjyeung/orch_n30/fb_pack/relcnt (87 MB): relative-count v1, superseded by relcnt2 (review GO 21:25Z).
## trinity-2-28 (3.0 TB free)
- /scratch/jjyeung/orch_n30/fb_pack/patchA/work (about 16 GB at 20:10Z): test scratch of build fbp_patchA; keep out/ and the patch.
- /scratch/jjyeung/orch_n30/fb_pack/prior2/work (about 11 GB at 20:10Z): test scratch of build fbp_prior2; keep out/.
- /scratch/jjyeung/orch_n30/fb_pack/ro (about 5.4 GB): read-only copies of 1-18 inputs, removable once all 2-28 builds and reviews end.
## Added by fb_pack3 (23:30Z)
- B/events/k1fwd2/ (one 1.6 KB file): folder created by mistake; the same answer is in events/k1fwd and events/fb_pack.
- trinity-1-18 /scratch/jjyeung/orch_n30/sb_own400/out/real400_score (first scorer attempt, refused before any score; frozen bars copy and empty cache dirs only).
- trinity-2-28 /tmp/fbp3_mirror_228.tar (348 KB; mirrored to 1-18 n30_mirror/fb_pack).
