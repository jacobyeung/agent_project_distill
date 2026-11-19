# Kit specification: count pricing (does the SAM 3 instance evidence count large sets on the dev items, before any training?)

Lane sb_countdesign, 2026-11-19. Design record: `distill_design/COUNT_LARGE_SETS_DESIGN_20261119.md`. `B` = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30`. Nothing here trains, and no output of this kit may ever become a training label: every capture it reads is a dev capture.

## 1. What it decides
Whether a count read off the frozen SAM 3 tower's per-frame instances, by fixed math, beats the model's direct answer on the dev counting items whose truth is 5 or more. Primary arm **N**: the most instances of the category seen in one frame. The read also prints three references that decide what a win means: the best constant answer, the rank correlation of the tool count with the truth, and two composites with the direct answers.

It does not decide the route. A route is decided after training, from the trained model's own calls.

## 2. Bar, written before any number
Scores are VSI-Bench MRA with the official comparison. Every large item of the set stays in the denominator; a capture or category with no SAM 3 output counts as a tool count of 0.

| Set of large items | Items (rooms) | Direct, R1 step 200 | NEAR line | Direct, step 544 | PASS line | Best constant (6) |
|---|---|---:|---:|---:|---:|---:|
| R0-dev (Part A1) | 64 (44) | 14.06 | 19.06 | 25.31 | 30.31 | 63.59 |
| dev-S1 (Part A2) | 29 (18) | 17.24 | 22.24 | 36.55 | 41.55 | 46.21 |
| Both | 93 | 15.05 | 20.05 | 28.82 | 33.82 | 58.17 |

- **PASS:** arm N is at or above the PASS line and the 95% lower bound of N minus the step-544 direct answer is above 0 (10,000 room-bootstrap draws, seed 20261119, paired per item).
- **NEAR:** not PASS; N is at or above the NEAR line and the lower bound of N minus the step-200 direct answer is above 0.
- **FAIL:** otherwise.
- **+INFORMATIVE** is added when N is also at or above the best constant on the same items and the rank correlation of the tool count with the truth inside those items is 0.5 or more.
- The verdict is read on R0-dev alone when only Part A1 has run, and on both sets when Part A2 has run too. The scorer prints it; nobody recomputes it by hand.

**Forecast, mine, before the run:** N on R0-dev between 30 and 40 (K1's ScanNet++ large sets: 35.0 [29.1, 41.0]); verdict NEAR or PASS, without INFORMATIVE.

**What each verdict licenses.**
| Verdict | Consequence |
|---|---|
| any +INFORMATIVE | The per-frame evidence carries the count on dev. Build the extended response (section 8) and call rows for large sets in the next vehicle. |
| PASS | Read `R2_floor_S1_544_minus_direct_S1_544` on `every_R0-dev`. Teach a floor line only if it is +2 or more with its lower bound above 0 and `truth_2` loses under 2 points. Otherwise nothing changes. |
| NEAR | Nothing changes for rows. The head waits for the K1 identity test (design record, tests, item 3). |
| FAIL | The same, and report `tool_zero` and the categories SAM 3 never finds. |

## 3. Inputs, by path
| Input | Node and path | Check |
|---|---|---|
| Kit files | `B/events/sb_countdesign/sb_countdesign_files.tar` (unpack anywhere on `/scratch`; `KIT` below is the unpacked root, holding `files/` and `work/`; write its absolute path in every command, and create `KIT/out` first) | `cd KIT/files && sha256sum -c KIT_SHA256SUMS` |
| Item list, all 535 dev counting items | `KIT/files/COUNT_ITEMS_535.jsonl` | sha256 `b20e72603589aa8c900f993a83d670e880dd8a9b151cb5c300b02bbf00a3398a`; fields `id, set, scene, room, categories, truth, source_frame_indices, direct{S1_544,R1_100,R1_200}{pred,score,forced_close}` |
| The 93 large items | `KIT/files/ITEMS93.json` | sha256 `55279a488abb93c81d8dd0db37ce9c8c96f9a28d895803a9e51234c2fbb03413` |
| R0-dev frames | trinity-1-18 `/scratch/jjyeung/orch_n30/b10_reserve/frames/scannetpp/<scene>/<index:06d>.png` (640x480) | per-scene hashes in `/scratch/jjyeung/orch_n30/b10_reserve/out/frame_manifests/<scene>.json`; the manifest builder checks every frame |
| R0-dev frames, second copy | `/data3/jjyeung/n30_b10_reserve/R0_RESERVE_20261116.tar` (3.8 GB) | only if trinity-1-18's copy is gone; a governed read |
| SAM 3 runner | trinity-1-18 `/scratch/jjyeung/orch_n30/b05_owngrd/code` (`owngrd/teacher.py`, `owngrd/stub_tower.py`, `owngrd/vendor/`) | the kit's runner imports it unchanged |
| SAM 3 environment | trinity-1-18 `/scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python` | |
| SAM 3 weights and source | trinity-1-18 `/scratch/jjyeung/orch_cd/ttower/work/sam3_weights/sam3.pt`; `/scratch/jjyeung/orch_cd/mdg_next/work/data/sam3src`; receipt `/scratch/jjyeung/orch_n30/b05_owngrd/code/owngrd/vendor/SAM3_RECEIPT.json` | weights sha256 `9999e2341ceef5e136daa386eecb55cb414446a00ac2b55eb2dfd2f7c3cf8c9e` (lane b05's contract); the file is present on trinity-1-18 (3,450,062,241 B, listed 2026-11-19); I did not hash it, so hash it first |
| K1 reproduction inputs | trinity-3-30 `/scratch/jjyeung/orch_n30/b05_owngrd/work/labels_k1` and `.../work/teacher_k1_full/teacher_k1`; capture list `KIT/work/K1_LIFT_META.json` | mirror: trinity-1-18 `/scratch/jjyeung/n30_mirror/b05_owngrd/B05_K1_TEACHER_LABELS.tar` |
| dev-S1 frames | none on a reachable node | Part A2 |

The contract of the SAM 3 pass is lane b05's teacher contract, unchanged: joint floor 0.2, at most 10 instances per frame and prompt, resolution 1008, bf16, mask threshold 0.5. The prompt is the category string of the question, verbatim.

## 4. Fixed math (`KIT/files/score_count_pricing.py`, sha256 `957619e8e1509857d1c2f6029f33f28dfd7b40e1609b6cc2f33ac44ca7444c79`)
1. For one capture and one category, in each of the 32 frame slots: take the instances with `joint_score >= 0.35`, in decreasing `joint_score`. Decode each mask and subsample it `[::2, ::2]`. Drop an instance when its mask has IoU above 0.5 with a kept one, or when its overlap with a kept one exceeds 0.8 of the smaller mask. The frame count is the number kept.
2. The tool count of the category is the largest frame count over the 32 slots. The tool count of an item is the sum over its categories (R0-dev's two-category items).
3. Arm N answers the tool count.
4. Composites, each with the direct answer of step 544 and of R1 step 200 stored in the item file: `R1_replace_if_large` answers the tool count when it is 4 or more and the direct answer otherwise; `R2_floor` answers the larger of the two.
5. References: constants 5, 6 and 7; the rank correlation (Spearman, average ranks) of the tool count with the truth.
6. Groups reported: `large_all`, `large_<set>`, `every_item`, `every_<set>`, `truth_2`, `truth_3`, `truth_4`. Intervals: rooms drawn with replacement, 10,000 draws, seed 20261119, percentile 95%.

Where the constants come from: 0.35 with duplicate removal was the best per-frame-maximum rule on K1's 196 train large sets among those that remove duplicates (41.7; held-out 45.2); K1 held-out was visible when I chose it. No dev counting item has ever had SAM 3 output on a reachable node, so the dev sets are untouched. Do not change a constant after the GPU run.

## 5. CPU dry run (all four must pass before a card is asked for)
```
# (a) scorer self-test, any node
python3 KIT/files/score_count_pricing.py --selftest --items KIT/files/COUNT_ITEMS_535.jsonl
#   expected: "bars from the item file: large items n 93, direct step 544 28.82, direct R1 step 200 15.05" ... "selftest OK"

# (b) K1 reproduction, trinity-3-30, about 2 minutes on one core
python3 KIT/files/score_count_pricing.py --k1 /scratch/jjyeung/orch_n30/b05_owngrd/work/labels_k1 \
    /scratch/jjyeung/orch_n30/b05_owngrd/work/teacher_k1_full/teacher_k1 --captures KIT/work/K1_LIFT_META.json
#   expected, exactly: truth 1: 42.3 (n 1522) truth 2: 39.4 (n 392) truth 3: 39.7 (n 174) truth 4: 46.1 (n 93) truth 5+: 42.5 (n 254)

# (c) manifest, trinity-1-18 (reads and hashes 3,136 PNGs on local scratch)
python3 KIT/files/build_count_manifest.py --items KIT/files/COUNT_ITEMS_535.jsonl --set R0-dev \
    --frames-root /scratch/jjyeung/orch_n30/b10_reserve/frames/scannetpp \
    --frame-manifests /scratch/jjyeung/orch_n30/b10_reserve/out/frame_manifests --out KIT/out/MANIFEST_R0DEV.json
#   expected: "captures 98 prompts 464 manifest sha256 <SHA>"; keep <SHA>

# (d) stub pass and score, trinity-1-18, CPU only
cd /scratch/jjyeung/orch_n30/b05_owngrd/code && CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 \
  /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python KIT/files/run_count_teacher.py \
  --manifest KIT/out/MANIFEST_R0DEV.json --manifest-sha256 <SHA> --out KIT/out/stub_r0dev --stub
python3 KIT/files/score_count_pricing.py --items KIT/files/COUNT_ITEMS_535.jsonl --teacher KIT/out/stub_r0dev --set R0-dev --out KIT/out/STUB_SCORE.json
#   expected: 98 folders each with DONE.json; the scorer prints "coverage 385 of 385"; the stub's numbers mean nothing
```
I ran (a), (b) and a two-capture fixture of (d) on trinity-3-30 (stub tower, frames hash-checked, scorer end to end). (c) and the full (d) need trinity-1-18's frames.

## 6. GPU run, Part A1 (R0-dev)
- **Card:** one 48 GB card, as lane b05 used. Lane b05 measured 2.0 s per prompt per card (4,546 prompts, two cards, 77 minutes). Part A1 is 464 prompts over 98 captures: about 16 minutes plus model load.
- **Budget:** 0.5 GPU-hours expected; the runner stops itself at 1.0 (`--hours 1`). Do not relaunch after a kill; write a BLOCKER.
- **Launch rule:** two `nvidia-smi` readings 5 or more minutes apart showing the card empty, recorded in the launch event; under `/data3/shared/scripts/vnice/vnice.sh` off trinity-0-13; in `tmux`; check output every minute.
```
cat > KIT/out/settings_gpu.json <<S
{"checkpoint_path": "/scratch/jjyeung/orch_cd/ttower/work/sam3_weights/sam3.pt", "receipt_path": "/scratch/jjyeung/orch_n30/b05_owngrd/code/owngrd/vendor/SAM3_RECEIPT.json", "source_root": "/scratch/jjyeung/orch_cd/mdg_next/work/data/sam3src", "device": "cuda", "precision": "bf16"}
S
tmux new-session -d -s count_pricing "cd /scratch/jjyeung/orch_n30/b05_owngrd/code && CUDA_VISIBLE_DEVICES=<card> \
  XDG_CACHE_HOME=/scratch/jjyeung/.cache TORCH_HOME=/scratch/jjyeung/.cache/torch /data3/shared/scripts/vnice/vnice.sh \
  /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python KIT/files/run_count_teacher.py --manifest KIT/out/MANIFEST_R0DEV.json \
  --manifest-sha256 <SHA> --out KIT/out/teacher_r0dev --settings KIT/out/settings_gpu.json --hours 1 > KIT/out/worker.log 2>&1; echo rc=\$? >> KIT/out/worker.log"
```
- **Done when:** `KIT/out/teacher_r0dev/PROGRESS.0of1.jsonl` ends with `shard_complete` and 98 folders hold `DONE.json`. Output size: about 10 MB.
- If trinity-1-18's cards are taken, move the 98 scenes' 32 frames (about 0.8 GB), the environment and the weights to the free node with one tar pipe over InfiniBand, as lane b05's `work/x118/stage113.sh` did, and rebuild the manifest there.

## 7. Score and report
```
python3 KIT/files/score_count_pricing.py --items KIT/files/COUNT_ITEMS_535.jsonl --teacher KIT/out/teacher_r0dev --set R0-dev --out KIT/out/COUNT_PRICING_R0DEV.json
```
Report, from that file and nothing else: the printed verdict; for `large_all`: `N_tool`, both direct scores, both differences with intervals, `best_const`, `spearman_tool_truth`, `tool_under`, `tool_over`, `tool_zero`; for `every_item`: `N_tool`, the four composites and their differences from the two direct answers; `truth_2`, `truth_3`, `truth_4` for arm N and `R1_replace_if_large_S1_544`. Add the ten categories with the largest summed error. Mirror `KIT/out` (without the stub folder) to a second node and append one line to the design record's status.

## 8. If the verdict carries +INFORMATIVE: the response and the rows
- **Response.** The existing call `<ground obj="chair" mode="instances">` keeps its first line and adds two: `per frame: f3 2, f7 4, f12 6, f20 3` (frames with at least one instance) and `most in one frame: 6 (frame 12)`.
- **Rows.** Only for a truth of 4 or more, where the tool's count is within the larger of 1 and 20% of the truth on the training capture (41% of such K1 train pairs for arm N). The trace states that the set is large, makes the call, copies the printed count and answers it. Other large-set rows stay direct. Sources: K1 train captures first (SAM 3 output and labels exist: 344 pairs with a truth of 4 or more), then a SAM 3 pass over the ground-truth-raster scenes. Never R0, the 80 withheld rooms, benchmark rooms, dev-S1 or K1 held-out.

## 9. Part A2 (dev-S1), not specified to the letter
The 29 large dev-S1 items sit in 23 captures (ScanNet++ 13 items, ScanNet 8, ARKitScenes 8); all 150 dev-S1 counting items sit in 79. No frames of these captures are on a reachable node: the copy staged for the 11-12 mask run was on trinity-2-18. A builder stages the 32 frames of each capture at the item's `source_frame_indices` as `<root>/<dataset>/<scene name>/<index:06d>.png`, with the decoder the dev reads use, through the IO governor (about 0.2 GB for 23 captures, 0.8 GB for 79), then runs:
```
python3 KIT/files/build_count_manifest.py --items KIT/files/COUNT_ITEMS_535.jsonl --set dev-S1 --frames-root <root> --out KIT/out/MANIFEST_DEVS1.json   # add --large-only for the 23 captures
```
and sections 6 and 7 with `teacher_devs1`, about 5 minutes of GPU for 150 prompts. For the verdict on all 93 items, score both folders together without `--set`: `--teacher KIT/out/teacher_r0dev,KIT/out/teacher_devs1`.

## 10. Not in this kit
- A merged instance list (the learned accept and merge of the design record). It needs G3T geometry for each dev capture in K1's converted format, which no lane has exported for R0-dev, and on K1 it does not beat the constant.
- Any change to the reader or to rows.
