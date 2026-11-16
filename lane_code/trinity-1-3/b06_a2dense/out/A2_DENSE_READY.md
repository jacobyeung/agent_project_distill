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
- Tower cache: patch L/out/packets/gf1_cache/gf1_cache_on_b5_ba346bd9.patch (3610e972, after review 1) on tree build 5 (seal ba346bd9); applies to the build-6 working tree. Tests: test_gf1_cache 11/12 (L/cache/out/tests_full_1330Z.json); the failure is the BF16 cache (one router gradient 0.0167 > 2**-6); FP32 cache passes every case (BF16 tower: logits exact, residuals rel 5.6e-7). Default cache dtype FP32. Regression 30 pass + 2 pre-existing errors as in base.
- Cache size on the real grid (all dense frames 640x480 -> 10x13 = 130 cells): 102 MB per clip FP32 at 32 anchors, 280 GB for 2,741 clips (245 GB without the pool stream); 64 anchors double it (L/out/CACHE_SIZE.json). The plan's 51 MB / 156 GB was the BF16 figure.
- Shuffled-bank read mode: gf1_cache.shuffle_rows + dense_eval.prepare_membership(shuffle=...), tests pass (ShuffledBank, 3 tests).
- Cost: L/out/packets/cost_step/ (protocol + analyzer, synthetic-tested). Needs the patch in the A2 kit and an ORCH GO.
- Card: L/out/A2_CARD_DRAFT.md (8bae8480).

## Not done here
- Real-row cache parity in the trainer's dtype and the every-rank CPU first batch need the real tower and frames: they run inside the frame-host job.
- Export and reload of a GF-1 checkpoint on CPU passes in the patched tree: test_gf1_review export round trip and test_gf1 save/load/resume (tests_regress_1240Z.json). The cached-bank path is not yet in an exported-checkpoint test.

## Where the 280 GB FP32 cache lives (answer to ORCH 1300Z)
- The cache is a derived artifact: the writer is deterministic and content-addressed (identity record with the tensor sha256; a rewrite that differs refuses). Nothing depends on a stored copy: the leg's job writes it at start on the training node's local storage (node-local /tmp or /dev/shm; advanced nodes have 1.86 TB RAM, 8 GPUs) from the frames and the frozen tower, then trains from it. Writer cost is measured by the cost packet (guess: under 2 GPU-h for 2,741 clips) and is paid again on every new allocation; that cost goes into the card.
- What must survive is the frames: the 16.4 GB of new PNG (parts tars) are copied to GCS after the seal, size-checked, and the k6 store already has GCS shard parts. The Orchard project FS (2.4 TB free at 13:05Z) holds a working copy only.
- If the node-local space is too small (job 1 reports df), the leg runs the online tower for every row: correct, slower; the cost packet prices it.

## Refute review 1 (Codex gpt-6-astra high, 13:08Z; receipt agent/scratch/codex_runs/20261116T130347Z_b06_refute1) and what changed
1. FPS-only clock merge (MEDIUM): fixed, seal refuses `clock_conflict` (0 such groups in plan_v4).
2. Stale signatures (MEDIUM): fixed, seal recomputes the signature (`stale_signature`) and checks every student-ordinal frame against the row pin (`student_pin_differs`); 0 of 2,741 entries fire.
3. Missing parity evidence passed (HIGH): fixed, a scene with new frames and no re-produced student frame is held (`parity_missing`).
4. Pixel rule cannot prove identity (MEDIUM): accepted as residual risk; two distinct real frames of a moving camera do not agree within 1 grey level on 99.9% of values; the member choice is the unchanged k6 rule (nearest traj timestamp, 2 ms).
5. Shuffled read rejected path aliases (MEDIUM): fixed, rows of one clip are compared by ordinals, sha256 and timestamps; test added.
6. Production parity unverifiable (MEDIUM): stays in the frame-host job (real row, trainer dtype).
7-8. Rule 3 two-sided / shuffled harm is not useful geometry (HIGH): card rule 3 is now one-sided; a claim rule requires beating both init and shuffled; a zero-bank read is printed.
9. One-point power unknown (MEDIUM): measured on D0's m200 read: half-width 4.13 pp on the 450-item paired mean (L/power/m200_power.json b8ee62f0); rule 3 is a point rule and the card says so.
10. Missing cache record fell back online (MEDIUM): fixed, refuses for non-pose rows.
Tests after fixes: dense 19/19; test_gf1_cache 11/12 (only the known BF16-cache case fails; L/cache/out/tests_full_1330Z.json).
R0 (ORCH 1307Z): 0 rows, frames or clips removed: no R0 room occurs in the plan, the row clips or the A2 pose rows (L/out/R0_OVERLAP.json; 2,160 s5 sample rows have aliases outside the k6 plan and are not A2 rows).

## Fetch on Orchard (job 170379, 18:52-19:22Z; cancelled for main's general slot, ORCH 1913Z)
- ARKit range fetch, parts a0-a2 DONE: 1,483 of 1,500 captures, 51,072 frames, 0 misses, 4.1 GB from Apple in 13.5 min. 17 captures refused by the clock guard (known k6 ordinals differ from traj rows, 19-30 ordinals each); their 17 d3 clips are refused, never re-aligned.
- Video decode: v0 DONE (409 videos); v1, v2 owed (one job, same command; DONE parts are skipped).
- Seal dry-run on the four parts (L/work/fetch_partial/SEALED_partial.json): 1,902 clips sealed + 839 refused = 2,741; parity 6,510 frames checked, all byte-equal to the k6 pins on the compute node, 0 differ.
- Compute-node storage (logs/disk.170377.txt): /tmp 5.9 TB (4.8 TB free), /dev/shm 922 GB, RAM 1.8 TB: the 280 GB FP32 cache fits node-local storage.
- Parts (Orchard okh7/db3954b2/parts, sha256 in L/work/parts_sha_1930Z.txt): a0n3 71e920bc, a1n3 aff4914f, a2n3 01654203, v0n3 628e058a.
- Power for card rule 3 (D0 m200 read): 450-item paired half-width 4.13 pp (L/power/m200_power.json); rule 3 is a point rule.
