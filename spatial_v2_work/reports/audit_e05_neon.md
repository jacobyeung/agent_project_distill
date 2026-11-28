# Hostile Cross-Family Audit: `e05_api_factory/` & Pilot-0 Smoke Rows

**Scope:** `exclusions.py`, `geo_solver.py`, `gemini_client.py`, `pilot0_runner.py`, `tests/test_factory.py`, `reports/build_e05_api_factory.md`, `pilot0_smoke.jsonl` (`28` rows), `pilot0_ownhead_boxes.jsonl` (`39` rows), and `pilot0_smoke_summary.json`. All checks ran read-only (`python -B`).

---

## 1. Leakage & Provenance Audit

- **Emitted data is clean (`0` room/venue leaks):** Independent normalization of raw authority lists (`3119aa4a.raw`, `4d4736cf.raw`, `634820b4.raw`, `969cdb56.raw`, `bdb5d402.raw`, `authority_split.raw`, `authority_visits.raw`, `K1_ROWSETS/`) confirms **0/28** smoke rows, **0/39** ownhead box rows, and **0/233** filtered `pinned_train` captures hit `BENCH_v2` (`511` rooms), `ReSTI` ScanNet (`150` rooms `scene0000..0149`), `R0` (`372` rooms), `dev-S1` (`100` rooms), `K1-heldout` (`55` rooms), or `withheld_80` (`80` rooms).
- **Zero `H900`/`D580` skin leakage:** Cross-checking all `48` templates in `geo_solver.py:51-116` against `2,806` prompts from `r0dev.json`, `devs1_routed.json`, and `camera_generation.json` yields only one benign 5-gram overlap (`"the closest points of the"` in `metric_distance` template `2`).
- **Guard & report defects found:**
  1. `exclusions.py:118-126,371` lumps all `372` `R0` rooms (`272 R0-rl` + `100 R0-dev`) into `R0_dev`. Every `R0-dev` room is `scannetpp` (`100/100`), so canary `exclusions.py:371` (`scannet/scene0183`) tests an `R0-rl` room, and the guard cannot distinguish `R0-rl` from `R0-dev` for RLVR.
  2. `exclusions.py:140-150` reads `K1_CAPTURES_HELDOUT_57.txt` and `K1_EXCLUSIONS.json` **without SHA256 pins** and skips them silently if absent (`if heldout_57.is_file():`). Missing `K1_ROWSETS` drops `5` held-out captures (including `arkitscenes/45261532`) while still passing `expected_min["K1_heldout"] = 48` (`line 163`).
  3. `build_e05_api_factory.md:30,35` reports **fabricated scene IDs**: `scannet/scene0000_99` is absent from `R0_ROOMS.txt`, and the `6` actual blocked `withheld_80` captures are `scene0201_02, scene0255_01, scene0478_00, scene0478_01, scene0614_02, scene0692_03` (not `scene0247_01..scene0318_00`).

## 2. 3D Geometry & Math Audit (`geo_solver.py`)

- **Core math & parity verified:** Recomputing from raw `.npz` GT across all `233` clean captures confirms `0.0` max `box_grid_5cm` error against `train_labels.json` on all `946` K1 rows (`307` full, `639` half), `0` miscalibrated captures (`126` ARKit full + `1` empty, `28` ScanNet full + `7` half, `71` ScanNet++ half), row-vector `obb_axes` orientation, OpenCV `c2w` (`+Z` forward, `-Y` up), exact `180°` chiral inversions (`rows 4/8, 12/16`), exact `cam@k` `r_horiz`/bearings (`rows 6,9,17`), exact `SE(3)` displacement (`rows 2,18,21`), and exact `>=5` counts (`rows 7,15,25`). Row `27` (`scannet/scene0579_02`, `half_corrected_2x`) is genuinely half-extent in raw `.npz` (median containment ratio `0.953`).
- **Geometry & test defects found:**
  1. **Vacuous half-extent unit test (`tests/test_factory.py:83,93`):** Slicing `pinned_doc["captures"][:20]` inspects `20/20` ARKit `"full"` captures only. On any half-extent capture, `scene.extent_convention` (`"half_corrected_2x"`) != `lrow["convention"]` (`"half"`), so line `93` **fails on all `64` half-extent captures**.
  2. **Unsafe `scannetpp` blanket `2x` & `no_raster` fallthrough (`geo_solver.py:357-385`):** `if ds == "scannetpp": conv = "half"` skips the raster containment test (risks `2x` double-correction on full-extent ScanNet++ v2 data), and `"no_raster"` in `known_conventions` falls through to `mult = 1.0`.
  3. **Camera `yaw_deg` sign inverted vs `dev-S1` (`geo_solver.py:544-545`):** Emits `+` for right/clockwise (`rows 2,18,21`), opposite to `dev-S1` (`"Positive means left"`). Scalar `disp` answers are unaffected, but `<tool_response>` exposes inverted `yaw_deg`.

## 3. Trace Quality, Epistemic Realism & `Argon ∩ Carbon` Boxes

- **Concision & arithmetic:** Emitted `<think>` lengths span `26–96` words (`mean 59.5`, well under `<250` tokens) with `0` unit-conversion errors across `{m, cm, ft, in}`.
- **Critical epistemic shortcuts & realism failures:**
  1. **Oracle GT box & slot leak in `<tool_obs>` (`geo_solver.py:717-726`; `pilot0_smoke.jsonl` rows `3,5,13,22`):** On all `4/4` `UNSEEN` recovery rows, `inspect(view="rgb")` returns **ground-truth slot IDs and GT `box_1000`** in JSON (`"visible_targets":{"s5":{"box_1000":[308,722,571,947]}}`), which `<think>` reads (`"confirms the cardboard box (s5)"`) *before* `locate(box_hint)` resolves `s5`. At inference an RGB inspect on an `UNSEEN` target cannot return GT boxes or slot IDs.
  2. **Fake OOF `UNSEEN` mining (`geo_solver.py:469,624-632`; rows `3,5,13,22`):** `candidates.json` only stores `2–7` K1-queried phrases per scene. `oof_scores_by_phrase.get(lab, 0.0)` labels unqueried objects (`cardboard box`, `books`, `kitchen cabinets` [81% of frame], `bathtub` [71% of frame]) as `oof_joint_score = 0.0` (`0/4` were actually queried in `candidates.json`). `_op_locate` then leaks GT `best_cand_f` despite `oof_joint_score == 0.0`.
  3. **Fake `LOW_PARALLAX` & unvalidated recovery (`geo_solver.py:656-681`; row `26`):** Hardcodes `parallax_deg: 4.2`, leaks GT `[init_f, wide_cand_f]`, and clears `LOW_PARALLAX` for *any* `frames != "auto"` (even `[1, 1]`) without checking the required `AND` parallax gate ($\Delta\theta\ge 15^\circ \land \beta\ge 0.20 \land |t_2-t_1|\ge 2$), fabricating `parallax_deg >= 18.5`. `reproj_m=0.05`, `margin_top2=0.08/0.42`, and `pose_cond_deg=1.4` are hardcoded constants.
  4. **Multi-slot & counting shortcuts (`geo_solver.py:678`; `pilot0_runner.py:448,469,676-679`; rows `6,11,13,14,15,17,22,24,26`):** `vis_f[:8]` drops `best_t` on `7/28` rows (e.g., row `14` `best_t=28`, row `26` `best_t=27, wide_cand_f=30`). `multi_instance_disambig` (`rows 11,24`) always picks `objs[0]` (`slots[0]` shortcut) and calls a redundant `inspect(view="bev")` repeating `first_t` already returned by `locate`. `large_set_count_ge5` (`row 15`, `count=27`) verifies only `1` instance yet sets `referent_unique=true`, and truncates `slots` to `16` while emitting `"count": 27`. `10/28` Carbon rows emit robotic boilerplate (`"Standard measurement processing applied"`).
- **`Argon ∩ Carbon` boxes (`pilot0_ownhead_boxes.jsonl`):** All `39` boxes are non-degenerate (`ac_iou` min `0.6567`, mean `0.9600`; `gt_iou` mean `0.8468`, though `4` cover `>=70%` of the frame including row `18` `[0,0,1000,1000]` and `2` have `gt_iou < 0.55`). **Code bugs:** `gemini_client.py:488,493-498` averages two *disjoint* boxes into invalid consensus when `multi_vis=True` and `ac_iou < 0.55` passes via `gt_match_ok`; `pilot0_runner.py:758` injects a GT-derived 3×3 region hint (not strictly blind); `build_e05_api_factory.md:44` misstates `min_ac_iou` as `0.50` (code uses `0.55`).

## 4. Bandwidth, Scaling & Cluster Safety

- **Confirmed safe:** `0` File API uploads (blocked at `gemini_client.py:285-287`); bounded inline JPEGs (`15–51 KB` single frame, `55–88 KB` 6-tile contact sheet; `0.0461 MB/s` internet IO); backoff + jitter on `429/503` runs outside `self.semaphore`; all scene/frame reads hit local `/scratch` NVMe.
- **Scaling & NFS hazards (`C=16..32`):**
  1. **Hardcoded `102`-candidate cap (`pilot0_runner.py:153,187-465`):** Bucket caps sum to `102` candidates (`48` scenes max). The `50,000`-row launch command (`build_e05_api_factory.md:106-115`) will exhaust the queue at `~70` rows and exit `1`.
  2. **`21.1%` timeout rate (`pilot0_runner.py:742`; `pilot0_smoke_summary.json:69-74`):** Hardcoding `request_timeout_s=55.0` caused **`39/185` timeouts** (omitted from `build_e05_api_factory.md:46-47`), re-uploading JPEGs and inflating `neon_to_carbon_fallbacks` (`9` vs `7` HTTP `503`s).
  3. **Synchronous NFS writes/stats in asyncio loop (`gemini_client.py:41-46,261-270,405`):** Every HTTP `200` runs synchronous `mkdir + open + write + close` on `/data2/.../usage.<host>.jsonl` (NFS writes count `2×` under Trinity's `30 MB/s` cap and stall the event loop), and all `32` workers stampede `/data2/.../OVER_CAP` every `5s` when active (`line 269`).

---

## Prioritized Issue List

1. **`[BLOCKER]` Oracle GT box/slot leak in `inspect(view="rgb")` & fake OOF `UNSEEN`/`LOW_PARALLAX` recovery (`geo_solver.py:469,624-632,656-681,717-726`; `pilot0_smoke.jsonl` rows `3,5,13,22,26`):** Strip GT `visible_targets`/`box_1000`/`slot_id` from RGB `inspect` `<tool_obs>` (return image frame metadata only so the student must predict `box_hint` visually); mine `UNSEEN` strictly from labels *actually queried* in `candidates.json` (`lab in oof_scores_by_phrase`) without leaking GT `best_cand_f`; enforce the `AND` parallax gate ($\Delta\theta\ge 15^\circ \land \beta\ge 0.20 \land |t_2-t_1|\ge 2$) on `locate(frames=...)`.
2. **`[BLOCKER]` Hardcoded `102`-candidate cap prevents scaling past `~70` rows (`pilot0_runner.py:153,187,202,217,242,272,301,348,395,438,465`):** Remove fixed per-bucket caps (scale proportionally to `max_candidates`) and enumerate multiple clean pairs/triples/frames across all `233` clean captures.
3. **`[BLOCKER]` `55s` client timeout causes `21.1%` call timeouts (`pilot0_runner.py:742`; `pilot0_smoke_summary.json:74`):** Raise `request_timeout_s` to `>=120s` (or use `argon_level="MEDIUM"` with `120s` timeout) and add timeout rate to the build report / health gate.
4. **`[WARNING]` Synchronous per-call NFS writes & `OVER_CAP` stampede (`gemini_client.py:41-46,261-270,405`):** Log per-call usage to local `/scratch` and flush batched summaries off-loop to `/data2`; coordinate `OVER_CAP` checks via a shared lock/timestamp.
5. **`[WARNING]` Unpinned optional `K1_ROWSETS` & conflated `R0-dev`/`R0-rl` (`exclusions.py:118-126,140-150,371`):** Require and SHA256-pin `K1_CAPTURES_HELDOUT_57.txt` + `K1_EXCLUSIONS.json`; split `R0_dev` (`100`) and `R0_rl` (`272`) sets and canary both; fix fabricated scene IDs in `build_e05_api_factory.md:30,35`.
6. **`[WARNING]` Vacuous half-extent test & blanket `scannetpp` `2x` rule (`tests/test_factory.py:83,93`; `geo_solver.py:357-385`):** Test across all datasets including `"half"` captures (map `"half"` -> `"half_corrected_2x"`), run the raster containment check on `scannetpp`, and reject `"no_raster"` explicitly.
7. **`[WARNING]` Multi-instance box averaging corruption (`gemini_client.py:488,493-498`):** When `ac_iou < min_ac_iou` but `gt_match_ok` triggers, select the GT-matching model's box (or reject) instead of averaging two different objects' boxes.
8. **`[WARNING]` `yaw_deg` sign convention & trace hygiene (`geo_solver.py:544-545,678`; `pilot0_runner.py:448,469,676-679`):** Align `yaw_deg` sign with `dev-S1` (`+ = left`), ensure `best_t` is included in `vis_f`, randomize target slot index in `multi_instance_disambig`, and remove redundant BEV echoes / Carbon boilerplate.

**VERDICT: GO_AFTER_FIXES**
