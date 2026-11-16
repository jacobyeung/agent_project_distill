The facing-away and forward-control families each contain 150 items: 50 easy, 50 medium and 50 hard. Both checkpoints receive the same items within each family. The paired items cover 40 captures and 33 held-out physical rooms.

All 150 facing-away items belong to `facing_away_no_released_label`. Their labels come from their own GT answers; no released label exists for this wording. All 150 forward controls belong to `forward_twin_gt_control` and use their stored GT answers in the displayed option order. No released-label score or answer weight is applied to either family.

| Family | Kind | Rows | Letter counts | Content counts | Requested constant | Majority constant | Back-family prevalence |
|---|---|---:|---|---|---|---|---|
| away | easy | 50 | {"A": 26, "B": 24} | {"left": 23, "right": 27} | right: 27/50 (54%) | right: 27/50 (54%) | 0/50 |
| away | medium | 50 | {"A": 19, "B": 13, "C": 18} | {"back": 18, "left": 12, "right": 20} | back: 18/50 (36%) | right: 20/50 (40%) | 18/50 |
| away | hard | 50 | {"A": 17, "B": 9, "C": 12, "D": 12} | {"back-left": 15, "back-right": 18, "front-left": 8, "front-right": 9} | back-right: 18/50 (36%) | back-right: 18/50 (36%) | 33/50 |
| forward | easy | 50 | {"A": 24, "B": 26} | {"left": 27, "right": 23} | left: 27/50 (54%) | left: 27/50 (54%) | 0/50 |
| forward | medium | 50 | {"A": 21, "B": 16, "C": 13} | {"back": 2, "left": 29, "right": 19} | back: 2/50 (4%) | left: 29/50 (58%) | 2/50 |
| forward | hard | 50 | {"A": 10, "B": 13, "C": 13, "D": 14} | {"back-left": 9, "back-right": 8, "front-left": 18, "front-right": 15} | front-left: 18/50 (36%) | front-left: 18/50 (36%) | 17/50 |

Constants refer to option content because option order varies. Medium uses “back” as the requested constant; easy and hard use the most frequent legal option. Back-family prevalence is not an exact-option score for hard questions. Every away count and rate equals `back_dir/out/r2/MANIFEST.json`.

The training direct-pair files contain no dev rows. All 150 dev forward sources do exist in `back_dir/work/forward_direction.jsonl.gz`, marked `_split="dev"`. Each joins by source qid and matches the away provenance’s source-line hash, forward answer, source GT authority, options and frame indices. The control copies the stored forward question and GT answer; it does not reverse the away text or swap label strings. ScanNet++ canonical names use `scannetpp/` in the source cache and `scannetppv2/` in the dev task metadata; the native capture is identical.

`PAIRS.jsonl` joins the two families. `FORWARD_SOURCE_PROOF.json` pins the cache and all 150 selected source lines. `DEV_FORWARD_TWINS/ROWS.jsonl` retains those source rows. `BYTE_IDENTITY.json` proves the complete away ITEMS and ROWS files unchanged and compares exact JSON value-token bytes for every unchanged task field, including questions, options and answers.

Each payload retains the complete 152-capture pass-3 frame manifest. ScanNet uses 24 fps, ScanNet++ uses 60 fps and ARKitScenes uses 10 fps. The plan supplies source indices and totals; ARKit totals retain the explicit lower-bound flag. All frame, timing-authority, held-out-scene and prompt-source files are byte-identical to pass 3.
