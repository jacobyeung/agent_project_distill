# Distillation Student Ground-Truth State Dossier (2026-11-28)

Scope: verified read-only state of the spatial-understanding distillation student across architecture, official/dev benchmarks, checkpoints, runs, compute (Trinity + Orchard), open blockers, and structural point ceilings. Citations use `DD` = `/data2/jjyeung/agent_project_data/distill_design/`, `EV` = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/`, and `FACTS` = `/home/jjyeung/distill-paper/FACTS.md`.

---

## 1. Current Student Architecture (`LEG-S1 step 544` -> `R1 step 400` -> `Vehicle N`)

- **Backbone & Token Layout (`DD/ARCHITECTURE_CURRENT.md`):** `Qwen3.5-9B` (`base_identity c2022362...`), full fine-tune (`lm: full`, LR `6e-6`). Takes **32 RGB frames** (`frame_layout: duplicate`, `all_frames`, `frame_markers: on`; ~4,160 visual tokens) plus 32 per-frame `CAM` carrier tokens (`carrier_c1_data.py:232`). Carrier readout hard-requires 32 frames (`carrier_c1.py:590`); eval layout/fps mismatch costs 3–13 pts.
- **Total Artifact Footprint (`DD/NEXT_LEG_DECISION_20261117.md` §1.4):** ~9B trainable VLM/heads + ~2.05B frozen perception towers inside one self-contained checkpoint (`SAM 3` `0.85B` + `G3T` `~1.2B`, `~11B` total). Zero external harness: mid-CoT tool calls execute inside a single `generate` call, printing `<tool_response>...</tool_response>` (loss-masked during SFT).
- **Student-Trained Heads & Streams:**
  1. **PointDepthHead (`carrier_c1.py:39-60`):** Trainable private ViT deepcopy (`encoder_copy`, LR `1e-5`, merger frozen) -> 3 ViT taps + cross-frame blocks -> metric depth at `(u,v)` (LR `1e-4`, loss weight `0.25`, `depth_fov 0.05`). Serves deployment only via fixed clip-level metric scale math: `tower_scale = median(own_depth / G3T_depth)` over a 51x51 grid on 32 anchors (`own/GT = 1.016` on K1 train; learned ridge scale head lost `-9.3` displacement pts).
  2. **CameraSupervision Head (`camera_head.py:81-107`):** Depth-4 trunk on `CAM` carrier states predicting `pose9`, `FoV`, `gravity` (weight `1.0`), and `log-scale` (`weight_scale 0.04` in R1/N). **Gravity head** serves the level frame and 3D box yaw at inference; **own pose head** trains as auxiliary (`64` rows/step, weight `1.5`, LR `6e-5`) and serves no call (`12.0°–17.9°` rot error vs G3T `3.1°–6.3°`).
  3. **Track Selector Head (`b04 run_iso`, `6d97c524`):** Fitted on K1 train (215 captures / 200 rooms; verified 0 overlap with BENCH v2, `dev-S1`, or `R0-dev`). Ranks linked SAM 3 tracks using `candidates_argmax` (cuts `not seen` refusals on `dev-S1` distance from `38.7%` under `null_argmax` to `4.7%`).
  4. **Pointing & Presence:** Pointing trains as a text JSON stream (`32` rows/step, weight `1.0`); presence uses LM yes/no probes (AUROC `0.93–0.96` single-image, `0.62` in-video). **Not active in checkpoint:** own mask decoder (`MDG`, IoU `0.09–0.24`) and online G3T-to-LM feature fusion (`GF-1`, `geometry_online` unset).
- **Frozen In-Checkpoint Towers & Serving Contract (`DD/NEXT_LEG_DECISION_20261117.md` §1.1):**
  - `<move from=i to=j>` -> `G3T` relative translation/rotation x `tower_scale` in frame `i` `own_gravity` level frame (`dx, dy, dz, distance` in m).
  - `<turn from=i to=j>` -> `G3T` rotation + `own_gravity` heading math (`turn = +-N deg`).
  - `<ground obj=A mode="box">` -> `SAM 3` (`dense_aliases` text detector + linker) + `run_iso` selector -> `bestspread` single-best-frame lift on `G3T_depth * tower_scale`, carried to frame 1 via `G3T_pose * tower_scale` + `own_gravity` yaw (64 tower frames on ScanNet/++, 32 on ARKit).
  - `<gap a=A b=B>` -> fixed `box_grid_5cm` surface-to-surface OBB distance in metres.
- **Routing vs. Direct Split (`TRACE_RULING 2026-11-15` + `R1` room update, `288` rows/step = `128 VQA + 64 routing + 64 pose + 32 pointing`):**
  - **Routed (`64` rows/step, GT-valued tool responses in SFT):** object absolute distance, camera displacement, camera movement direction, camera rotation.
  - **Direct (`128` rows/step, qualitative CoT trace with `B2048` think budget, no fabricated metrics, no tool tags):** relative direction (easy/med/hard + toward/away), relative distance, object size (`0` rows drawn in R1/P via `SIZE-V`), **room size** (switched from unserved `<ground mode="room">` to traced qualitative direct in R1/N), counting & totals, appearance order, 3D box, route planning, and 6 VSTI relative types.

---

## 2. Verified Benchmark & Dev Scores

Do not compare partial-task reads (`6/8` VSI-Bench, `5/7` ReVSI) or `VSI-500` (`3.7–8.4` pts lower than full VSI-Bench) directly against full-benchmark headlines without stating task coverage.

### 2A. Official Benchmarks (Base vs. Student vs. Open/Closed Bars)

| Benchmark / Split | Base `Qwen3.5-9B` (32f) | Earlier Students (32f) | Current Lineage (`step 544`, `1d6eeb28`, 32f) | SOTA Open (~8–10B) | Closed Frontier (32f) | Source / Notes |
|---|---:|---|---|---|---|---|
| **VSI-Bench Full (5,130, 8 tasks)** | `55.88` (off. direct; think caps 75%) | `FT-X` `64.47` (off) / `64.14` (own); `CPDM` `63.79` (own) | **Unread on all 8** (`64.76` routed read flagged NOT clean; waits on `EAT-1`) | `Cambrian-S-7B` `63.53` (32f) / `67.42` (128f); `Cambrian-P-7B` `72.03` (32f) / `73.54` (128f); `GeoWeaver-10B` **`75.05`**; `ConsiSpace` **`76.6`** | *(No full-5130 cell; see VSI-500)* | `FACTS` §17; `sota-bars-9b-20261109` |
| **VSI-Bench Direct-6 (4,008, 6/8 tasks)** | — | `f17` `65.60` (spread, 4k cap) | **`68.77` `[66.5, 71.0]`** (dir `88.8`, size `72.0`, rel-dist `70.6`, order `66.2`, count `63.0`, route `52.1`) | — | — | Job `170008`; abs-dist (`834`) & room (`288`) unread |
| **VSI-500 (500, 8 tasks)** | `29.93` (nothink) / `16.27` (think) | `CPDM` `60.90`; `FT-X` `60.86`; `FT-X-E2 m1400` `63.01` | — | `Cambrian-S` `56.94` (32f) / `59.03` (128f); `Cambrian-P` `66.27` (32f nocam) / `69.80` (128f) | `Argon high` **`76.68`**; `Carbon med` **`75.97`**; `Gem 3.1 Pro` `62.8` | `FACTS` §2, §6, §8, §19; `FRONTIER_READ_20261111` |
| **ReVSI-999 (tier-32, all 7 cats)** | — | `T0 m800` `45.65`; `CP1 m200` **`58.63`** (B2048) | **Unread on all 7** (`~63.3` est. w/ CP1 stand-ins; waits on `EAT-1`) | `GeoWeaver-10B` **`57.5`** (32f) | `Carbon med` **`89.76`**; `Argon high` **`86.60`**; `Gem 3.1 Pro` `65.9` | `result-revsi-student-reads-20261112`; `CP1` beats open bar, `-28` vs closed |
| **ReVSI-999 Direct-5 (679, 5/7 cats)** | — | `CP1 m200`: dir `48.4`, size `63.4`, route `42.9` | **`64.94` `[61.3, 68.4]`** (rel-dist `77.4`, size `70.9`, route `66.7`, count `58.6`, dir `51.2` [twd `88.3`, awy `14.0`]) | — | — | Job `170037`; abs-dist (`283`) & room (`37`) unread |
| **VSTI-450 v3 Primary (5 subtasks)** | `37.23` (nothink) / `29.36` (think) | `FT-X` `68.41`; `CPDM` `69.41`; `f17` `69.41` (`66.95` paired) | **`73.89` `[71.04, 76.79]`** (G3T cam: disp `86.2`, move-dir `100.0`; cam-abs-dist `50.6`) | `Cambrian-S` `47.37` (32f); `Cambrian-P` `49.53` (32f) / `51.40` (128f) | `Argon high` **`73.73`**; `Carbon med` **`72.65`** | Job `170294`; **matches/edges closed bars on 5-task primary** via tower pose |
| **VSTI-450 v3 9-Type Mean** | — | `f17` `77.0`; `P1 m200` `77.6` | `70.5` (0 VSTI rel rows in `544`: cam-rel `42/54/70`, obj-pos `94/62/76`) | — | `Argon high` **`83.33`**; `Carbon med` **`82.29`** | `VSTI_NATIVE_CAMERA_READ_STEP544_20261116` |

### 2B. Dev Suites, Leg R1 Progression, Grounding Audits & Downstream VLA/Nav

| Suite / Metric | `Step 544` (`1d6eeb28`) | `R1 Step 200` (`673bc60f`) | `R1 C' Step 400` (`5083243c`, **N Init**) | `R1 Step 600` (Diagnostic) | Key Takeaway & Citation |
|---|---|---|---|---|---|
| **Pooled Direct-8 (`dev-S1` 1,339 + `R0-dev` 1,781)** | Baseline (`R0-dev` `56.0%`; `CP1 dev-S1` `71.64`) | `+4.13` `[+2.27, +5.98]` (90 single-count loops) | **`+5.11` `[+2.92, +7.26]`** (`0/535` loops; count `+11.25`, dir `+5.9..+9.0`, size `-0.54`) | `+5.54` `[+3.18, +7.89]` (count `+4.50`, `0` loops; rel-size `91.33`) | Jobs `171197, 172646, 173038, 173409`; dropping 17,879 list-form rows eliminated loops |
| **Facing Twins (`dev-S1`, 150 away / 150 toward)** | Away `21.33` (`8/49` ReVSI) / Twd `94.67` | Away **`88.67`** (`45/49` ReVSI) / Twd `93.33` | Twd-hard `-10.0` `[99.82%: -26.3, 0.0]` (silent) | Away **`91.3`** / Twd `93.3` | Jobs `172658, 173044, 173411`; `+67–70` pt away-direction repair |
| **VSTI Rel Dev (`vsti_rel_dev_r0`, 900 unexposed)** | `46.11` (`65.6%` template capture) | `58.33` (`+12.22`, `0%` capture) | **`61.45`** (`+15.33`) | `60.56` (`+14.44`) | Jobs `172654, 173465`; repairs `step 544`'s missing VSTI relative skill |
| **Camera Routed (`dev-S1` 450: disp / rot / dir)** | Tower: **`82.33 / 75.60 / 94.67`** (Own: `47.2 / 42.7 / 75.3`) | Tower: `81.87 / 76.27 / 94.67` (calls `450/450`) | Tower: `81.60 / 76.13 / 94.67` (**`H3` STOP**: disp `-0.73 [-1.68, -0.07]` from `+1.4%` scale drift; Own: `51.4/47.1/81.3`) | Tower: `82.27 / 77.07 / 94.67` (scale ratio `1.003` vs `544`'s `1.002`; `H3` false) | Jobs `171253, 172744, 173060, 173333, 173348`; **held-out camera wordings (`H900`) drop to `64.9/38.1/56.0` (calls `66%`)** |
| **Abs Distance Routed (`dev-S1` 150, `candidates_argmax`)** | `28.27` MRA (calls `149/150`; m `60.70`; printed gap `58.6`) | `50.27` (`+22.0`; calls fell to `88/150`, m `56.98`) | **`47.53`** (`+19.27`; calls `113/150`, m `57.4`; `R0-dev D580` reworded `41.4` [calls `44.5%`] vs twins `53.0`) | — | Jobs `171253, 172744, 173060, 173241`; unit conversions drove `+20`, skipped calls hurt metres |
| **Room Size (`dev-S1` 36 + `R0-dev` 98 = 134)** | `6.57` (`dev-S1` `11.11`, `R0-dev` `4.90`; `115/134` cap on unserved call) | **`64.40`** (`dev-S1` `68.89`, `R0-dev` `62.76`; `0` calls) | `dev-S1` `64.17` (`0` calls) | — | Jobs `172456, 172858, 173060`; 425 traced qualitative room rows gained `+57.8` pts |
| **K1 Held-Out (`K1-X`, 216 rows / 48 rooms, corrected)** | Served `63.29` (`vote_10_3_best` **`68.94`**, `+5.65`); GT masks `75.05` (E3); GT masks+geom `79.07` (served lift) / `91.99` (E3) | — | — | — | `DD/ROUTED_READER_LEVER_PLAN_20261120.md`; GT geom at deployed masks `C1 = -0.46` (**geometry waits for masks**) |
| **Dev Grounding (`DEV-MASK` + `J1`, 117 items / 35 rooms)** | Served `a = 55.8`; oracle track `b-a = -0.2`; GT masks **`e-a = +13.8 [+5.5, +22.3]`**; dense GT-seed tracker `+7.9`; `J1` per-frame top-1 `h1-a = -12.0` (closed); **GT box -> SAM 3 `k-a = +11.0 [+0.7, +20.9]` (OPEN)** | — | — | — | `DD/MASK_SOURCE_AFTER_TRACKER_DESIGN_20261122.md`; 2D box prompt recovers 80% of perfect-mask gain |
| **E0 MP3D Nav & VLA (`LIBERO-Spatial` / `R2R-CE`)** | `E0` (`f17`, 900 items): direct = own = `37.5` (`<50.2` blind prior; 0 calls); `T0 m800 + G3T x s` (n=100): `+35.2` vs direct (disp scale ratio `1.94` fails gate). **VLA (`Test L` LIBERO 5-demo & `R2R-CE` navrun):** kits sealed & CPU-proven on Orchard (`KIT e6bccd3d`, `B1` = `step 544`); **0 student VLA GPU runs yet** | — | — | — | `DD/E0_F17_SCORE_20261110.md`, `DD/E0_CAMERA_ROUTED_READ_20261110.md`, `DD/VLA_KITS_RECOVERY_20261116.md` |

---

## 3. Active / Stopped Runs, Checkpoints, Compute & Exact Blockers

### 3A. Run & Lane Status Today (2026-11-28)
- **Live Orchard `squeue` check:** Single batched `ssh orchard` timed out during banner exchange (`orchard` SSH ControlMaster expires ~12h or login throttled; per rules, no retry loop run).
- **Zero distillation training or GPU eval jobs are active.** No distillation lane has posted an execution event since `2026-11-23T02:25Z` (`lever10` rotation) / `2026-11-24T07:57Z` (`nauto` watcher) while the main project occupied cluster/Orchard capacity (`Nov 22–27`).
- **Leg N (`Orchard job 174444`, kit `w35` `ea058fed`, tree `db42866f`, milestones `[100, 200]`, init = R1 step 400 `5083243c`) — CANCELLED / HELD:**
  - Passed staging disk-plan fix (`5.22 TB` plan vs `6.00 TB` `/tmp` free, fixing `174246`'s `6.03 TB` failure) and reached `WAITING_REVIEW` on `orchard-community-3` at `2026-11-22T12:01Z` (`8/8` gate checks PASS).
  - **Cancelled at `2026-11-22T12:11:53Z` before step 1** by main (`orch-home-43` / `ss2`, `174465:lv_slot_1122`) under user long-video priority (`EV/n_review/STATUS.md`). Saved user question (`12:16Z`) applied default: **no resubmission without user GO and main releasing `advanced`**.
  - **N Resume Kit (`dc38194d`, `DD/N_174444_RESUME_KIT_20261122.md`):** Built and CPU-verified (`20/20` checks, bitwise state parity) so mid-leg preemptions resume from uploaded states rather than step 0; unreviewed/unrun on Orchard.
- **Leg R1 (`job 171377` -> `C'` `job 172660`, run `6ed2c7aa` on Vehicle P) — STOPPED AT STEP 400:**
  - Stopped cleanly under pre-registered rule `H3` at step 400 (`2026-11-19`); step-400 export (`5083243c`) is N's pinned parent.
- **Mask-Source / Grounding Lane (`lever10`, `EV/lever/STATUS.md`) — WAITING FOR GO:**
  - Completed `J1` (`2026-11-22`); registered `PRICING_C2_C3.md` (`ac19bb7c`, reviewed `GO AFTER FIXES`, awaiting 2nd review + orchestrator GO) to run: (1) `J1-T` box-tolerance check (`~10` GPU-min on `trinity-0-13`), (2) **Candidate 3** (own box+presence head on frozen `step-544` ViT taps + SAM 3 box prompt, `<=4` A6000-h fail-fast), and (3) **Candidate 2** (SAM 3 detector LoRA rank-16, `~7` A6000-h).

### 3B. Checkpoints & Compute Availability
- **Banked Checkpoints:** `LEG-S1 step 544` (`1d6eeb28`) and `R1 step 400` (`5083243c`, plus `step 200` `4c230a85` & diagnostic `step 600`) are staged on Orchard (`okh7` / `X`) and Trinity mirrors (`trinity-1-18`, `3-30`, `2-28`). Earlier finals (`CP1 m200/s346`, `T0 m800`, `f17`, `FT-X`, `CPDM`, `PDG v3 S2`) sit on Mind (`aws_evac/`) and `gs://cmu-gpucloud-jjyeung/ae/`.
- **Trinity Compute:** 9B full-FT needs `57–81 GiB/rank` at world 4 and **cannot fit 49 GB Trinity GPUs**; Trinity serves frozen-LM head training (`Candidate 2/3`), `J1-T`, and relift pricing. Local check on `trinity-2-28` (`8x RTX 6000 Ada 49 GB`): GPUs `0–3` hold `35–37 GiB`, **GPUs `4–7` are completely free (`2 MiB`, `0%` util)**, `/scratch` has `1.8 TB` free (`43%`), `/data2` `977 GB` free, `/data3` `17 TB` free. Rules: `trinity-0-13` normal priority (main has first claim); `2-28`, `1-18`, `3-30` require `vnice`; `1-13` GPUs off-limits; `0-8, 0-18, 0-23, 3-23` excluded; `2-18` dead.
- **Orchard Compute:** Shared per-user `advanced` (`4x H100 80 GB`, 24h max, `~0.153 H100-h/step` = `30.6 H100-h` per 200 steps + `~11 H100-h` staging) and `general` (`1x H100`, 12h max).

### 3C. Exact Open Blockers
1. **Orchard Slot & User Clearance for Leg N:** `job 174444` (`kit ea058fed`) is ready to resubmit unchanged (remembering to clear `X/n_r/review.json` first), blocked only on main releasing `advanced` and user/orchestrator GO (plus optional user ruling `U6` on `step 400` vs `step 600` init).
2. **Orchard `/project/community` Near-Full (`4–22 GiB` free):** `N_WATCH_STATUS.md` (`2026-11-24`) flags `PROJECT_DISK<150G` (`22 GiB` free; dipped to `4 GiB` on `11-22`). While N writes checkpoints to node-local `/tmp` + GCS, <5–10 GiB on `/project` threatens admission/staging metadata.
3. **Orchard SSH ControlMaster Down & `code_sync` Stale:** SSH to `orchard` timed out at banner exchange today (needs `ossh.sh` ControlMaster refresh); `EV/code_sync` has been in `BLOCKER_code_sync_failed` since `2026-11-23T17:07Z`.
4. **GCS `gs://cmu-gpucloud-jjyeung/ae/` Expiry (~2026-12-01, 3 days away):** ~610 GB of AWS-evacuated checkpoints (`CP1 s346`, `GXP s218`, `GH0`, `CP1 m50/m100`) have their sole copy in `ae/` unless already pulled to Mind/data3 (`DISTILLATION_HANDOFF_20261110_0110Z.md` §1, §4).
5. **Unsealed Official Reader (`EAT-1` / `build 10`) & Orchestrator GO on `PRICING_C2_C3`:** Official 8-task VSI-Bench and 7-category ReVSI reads remain gated on `build 10` passing `EAT-1` (`DD/NEXT_LEG_DECISION_20261117.md` §4 rank 3); Trinity mask-head work (`J1-T` -> `Candidate 3/2`) awaits orchestrator GO.

---

## 4. Top 5 Structural Ceilings Right Now (Where Points Are Lost)

1. **2D Whole-Object Grounding Recall & Completeness on Routed Distance (`-5.0 VSI` / `-5.7 ReVSI` headline pts; `-41.4` type MRA):**
   - Served metre distance plateaus at `58.6–60.7` MRA (vs `96.7` with perfect gaps). On the 117-item paired dev relift (`DD/MASK_SOURCE_AFTER_TRACKER_DESIGN_20261122.md`), GT masks add **`+13.8 [+5.5, +22.3]`** (`+16.4` on ScanNet/++), whereas oracle selection over SAM 3's linked tracks adds **`-0.2`** (`84/89` judged objects fail pre-lift: `27` never proposed, `27` wrong instance, `29` in `<3` frames). Per-frame text SAM 3 (`-12.0`) and video tracking (`+4.0` 32f / `+7.9` dense) miss the `+8` bar, while **GT 2D boxes into frozen SAM 3 recover `+11.0 [+0.7, +20.9]`** (80% of `e-a`), isolating 2D box localization (`Candidate 3` own ViT box head / `Candidate 2` SAM 3 LoRA) as the binding perceptions bottleneck.
2. **Direct-Path Priors on Multi-Instance Counting (`>2`), Small Object Size (`<30 cm`), Relative Distance & Order (`~17–25 ReVSI` / `~16.5 VSI` pts):**
   - Answers follow CoT conclusions on `99.9%+` of direct items (`DD/R1_M200_TRACE_ANALYSIS_20261119.md`), so losses sit in single-line perceptual assertions near priors:
     - *Counting (`-5.5 VSI / -7.1 ReVSI` at m200):* Removing list-form rows cured loops (`0/535` at m400), but non-looping single-category accuracy (`68.3–72.0`) merely matches constant `"2"` (`71.3–73.5`); counts `>=5` score **`14.1–17.2` MRA**, and multi-category `"1+1=2"` has `0` training rows (worth up to `+1.6` ReVSI).
     - *Object size (`-3.8 VSI / -6.0 ReVSI`):* Beats class-name median by only `1–5` pts; `<30 cm` items score **`48.0` MRA** (`1.19x` overshoot); routing via current 3D boxes loses (`50.7` vs `73.6` direct).
     - *Relative distance (`-3.3 VSI / -4.7 ReVSI`, `74/131` errors within `<1.25x` margin)* and *Appearance order (`-4.7 VSI`, wrong first-seen frames on `92/93` errors; `41%` cite frame indices `>32`)*.
3. **Wording-Bound Tool Routing & Unpassed `EAT-1` Reader Gate (`-11.6` to `-38.7` type pts on novel phrasing):**
   - Tool calls key off surface templates rather than task semantics (`result-r1-step400-routed-h3-stop-20261119`): at R1 step 400, held-out camera phrasings (`H900`) drop call rate from `100%` to **`66.4%`** (`direction` `46%`) and mean accuracy from **`84.1` to `53.0`**; reworded `R0-dev D580` distance drops call rate from `97.6%` to **`44.5%`** (`41.4` vs `53.0` on twins; `"Calculate the minimal span..."` calls on `1/20`). Vehicle N adds wording-coverage rows, and `build 10` must pass `EAT-1` before full official VSI/ReVSI routed scores can be claimed.
4. **32-Frame Sparse Subsampling & Out-of-View VSTI Targets (`~6.5 ReVSI` pts in long scans + `-11.0 VSTI` cam-obj pts):**
   - In `v7` VSTI rows, **`92.7%` (`1,112/1,200`)** of questions query at least one object with **zero visible pixels** at queried frame `k` (`49%` have *all* queried objects out of view at `k`), trapping `camera_obj_rel_dist` at `37.3–59.3%` (`4–13` pts over constant). On `R0-dev`, the longest third of scans (`178–705 s`) trails shorter rooms by `~7` pts (`20` long rooms hold `6.5` of `22.4` lost ReVSI pts), and `29/60` sparse `dev-S1` objects appear in `0–2` of 32 anchors.
5. **Qwen ViT Pose Blindness, Scale Drift & ARKit Tower Fragility (`-19 to -35` pts own-vs-tower; ARKit `10.4° / 0.60 m` error):**
   - Qwen3.5 ViT tokens yield chance pose (`58–77°`), capping the student's own pose head at `51.4 / 47.1 / 81.3` vs G3T `81.6 / 76.1 / 94.67` at step 400. Even under G3T: (a) co-training the depth head drifts `tower_scale` (`+1.4%` at step 400 triggered `H3` stop; requires frozen scale donor), (b) G3T is ill-conditioned on upscaled `192x256` ARKit frames (`2/23` pass rigid check; GT relative pose adds `+22.1` MRA on ARKit in `DEV-MASK` cell `g`), and (c) single-frame `bestspread` + `5 cm` grid lifting loses **`-12.9` MRA** vs multi-frame fusion even with GT masks + GT geometry (`79.07` vs `91.99` on K1 held-out; `vote_10_3_best` recovers `+5.65` on K1 held-out).
