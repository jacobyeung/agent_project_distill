# A2 dense frames, tower cache and card: ready state (2026-11-16, lane b06_a2dense, trinity-1-3)
L = /scratch/jjyeung/orch_n30/b06_a2dense. Short hashes are sha256 prefixes.

## Counts
- Pre-pass (metadata only, no RGB): 6,195 clip signatures over 362,439 non-pose row records (vqa 152,123; routing 82,285; pointing 25,020; routing pool 103,011) -> 2,741 dense clips (d1 556, d2 683, d3 1,502), 0 refusals. L/out/plan_v4/ (plan e1067375, tasks_a 3def82f6, tasks_v 5d0f0388); per stream L/out/DEMAND_BY_STREAM.json.
- Frame origin over the 2,741 x 64 frames: row pins 87,712; k6 extras 29,815; new decodes 11,410 (1,225 ScanNet/ScanNet++ videos); ARKit range reads 46,424 (1,500 captures, about 4.3 GB from Apple, 13.5 GB PNG).
- The plan's "993 of 994 in-map d1/d2 clips need no new decode" does not hold under the tree's one dense rule (nested_indices midpoints): new decodes are needed for most clips.
- Off-map units clips: the A0 v4 families (units 10,945 rows / 1,867 scenes; recovery 786; room 476; reworded distance 1,867) have every scene planned and 0 off-map (L/out/A0_FAMILY_SCENE_COVERAGE.json); the plan's 586 off-map clips belong to an earlier family version.
- Row pins that differ from k6: 7 frames in 7 clips (1,474 rows), admitted: each row keeps its own pinned bytes and its clip is keyed by that content. The plan's 759 references were not reproduced (its scripts were lost with 2-18).
- Pose rows (item 3): 27,604 dense pose rows (d1 20,080, d2 7,524), every one with a nested 64 inside its posed ordinals: no new decode (L/work/inputs/pose_counts.txt). The brief's 18,547 is not reproduced by the dense_pose_row predicate on store a2v3; the decode count is zero either way.

## Unknowns
1. k6 replica on Orchard: the members needed for the 29,815 k6 extras were not counted individually (dparity found all 32 pins of the test capture). Closed when the seal runs: a missing k6 frame refuses its clip with a code.
2. ARKit fetch: Apple range reads work from the Orchard login node (one capture, 64/64 frames, 5 s). Compute-node egress is unproven: job 1 of the packet tests it.
3. Parity: same decoder versions, yet 29 of 32 re-produced frames differ in bytes from the k6 pins, all by at most 1 grey level (fraction <= 1.3e-5; CPU SIMD dispatch). Pixel rule fixed before the full run: max |d| <= 1, fraction <= 1e-3 (dparity.py; dense_manifest.parity holds any other mismatch).

## Packets
- Frame fetch/decode: L/out/packets/frame_fetch/ (tgz 525991fd), staged at Orchard okh7/db3954b2; SUBMIT.md has three jobs (egress test, 6-task fetch/decode array, pixel parity) with names in L/work/ORCHARD_LEDGER.jsonl. Not submitted.
- Tower cache: patch L/out/packets/gf1_cache/gf1_cache_on_b5_ba346bd9.patch (8294f618) on tree build 5 (seal ba346bd9); applies to the build-6 working tree. Tests: test_gf1_cache 10/11 (L/cache/out/tests_full_1235Z.json); the failure is the BF16 cache (one router gradient 0.0167 > 2**-6); FP32 cache passes every case, exactly under a BF16 tower. Default cache dtype FP32. Regression 30 pass + 2 pre-existing errors as in base.
- Cache size on the real grid (all dense frames 640x480 -> 10x13 = 130 cells): 102 MB per clip FP32 at 32 anchors, 280 GB for 2,741 clips (245 GB without the pool stream); 64 anchors double it (L/out/CACHE_SIZE.json). The plan's 51 MB / 156 GB was the BF16 figure.
- Shuffled-bank read mode: gf1_cache.shuffle_rows + dense_eval.prepare_membership(shuffle=...), tests pass (ShuffledBank, 3 tests).
- Cost: L/out/packets/cost_step/ (protocol + analyzer, synthetic-tested). Needs the patch in the A2 kit and an ORCH GO.
- Card: L/out/A2_CARD_DRAFT.md (8bae8480).

## Not done here
- Real-row cache parity in the trainer's dtype and the every-rank CPU first batch need the real tower and frames: they run inside the frame-host job.
- Export and reload of a GF-1 checkpoint on CPU passes in the patched tree: test_gf1_review export round trip and test_gf1 save/load/resume (tests_regress_1240Z.json). The cached-bank path is not yet in an exported-checkpoint test.
