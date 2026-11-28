# Wave-2 Blueprint: 24/7 Unlimited-API Gemini 4D Spatial & Embodied Data Factory (`w2_api_data_flywheel`)

**Goal:** Train a unified 9B Spatial-VLA backbone that surpasses open and closed frontier models across static, multi-view, dynamic, and hour-scale spatial benchmarks (`>82` VSI-Bench, `>78` ReVSI, `>83` VSTI, `>72` MMSI/DSI, `>85` Ego-Exo4D, `<0.40 m` VQ3D) while unlocking `5–50` demo robot VLA manipulation and navigation transfer (`LIBERO-Spatial/+Cam`, `DROID`, `R2R-CE`, `RoboCasa365`).

**Core Design Thesis:** Naive frontier VLM distillation caps student accuracy at the teacher's perceptual illusions (`~62–77%`) and memorizes room/template priors (`20-pt` VSI$\to$ReVSI cliff, `44.5%` reworded distance call rate, `24%` valid `Locate` frames). Our factory breaks frontier ceilings by separating **what Gemini is superhuman at** (2D referent grounding at `96.9%` `Argon+Carbon` agreement, compositional problem authoring, linguistic diversity, epistemic error diagnosis, procedural code generation) from **what exact 4D solvers guarantee** (`DA3 Nested` `1.78°` metric pose/depth, `ViPE`, `Point4D`, `CoTracker3`, box-prompted `SAM 3` + `vote_10_3_best` multi-view lifting, and `0`-error Python SE(3) execution).

### Master Stream Ranking (by Immediate Points-Per-Day & Downstream VLA Leverage)
| Rank | Stream | Target Scale | Primary Gemini Roles | Spatial Benchmark Win | Downstream VLA Win |
|---:|---|---:|---|---|---|
| **1** | **Stream 2:** Prior-Breaking & Phrasing Suite | **300k** rows | `Flash` (50x phrasings), `Carbon` (vis check) | **+12–18 ReVSI, +8–12 VSI** (kills call skips & priors) | `180°` face-camera chiral & FOV-crop invariance |
| **2** | **Stream 1:** SPLIT Closed-Loop Epistemic Traces | **250k** + **400k** boxes | `Neon`+`Carbon` (recovery CoT), `Argon`+`Carbon` (boxes) | **+10–14 VSI/ReVSI routed, +11 VSTI cam-obj** | System-2 wrist-depth self-audit; trains `OWNHEAD` |
| **3** | **Stream 3:** Cross-Cam & Tabletop Embodied 4D | **220k** rows | `Neon` (clearance/subgoals), `Carbon` (grasp mode) | **+8–15 Ego-Exo4D, MMSI, VSTI** wide-baseline | Native `wrist↔exo` SE(3), cm clearance, `5–50` demo VLA |
| **4** | **Stream 4:** Dynamic 4D & Streaming 3D Memory | **120k** rows | `Flash` (crop-probe), `Neon` (4D/submap traces) | **+15–25 DSI, clean ReSTI, VQ3D, HD-EPIC** | Ego-decoupled 3D flow & out-of-view mobile memory |
| **5** | **Stream 5:** Adversarial Red-Teaming Self-Play | **80k** rows (`20k`/rd) | `Neon` (twins), `Neon+Carbon+Argon` (blind filter) | **+4–8 pts/rd** on tail cells; cold-starts Geo-RLVR | Eliminates coordinate sign bugs & ambiguous grasps |
| **6** | **Stream 6:** Procedural Specular/Cluttered 3D | **80k** rows (`<=10%` mix) | `Neon` (BlenderProc/ManiSkill code), `Carbon` (critic) | **+3–5 pts** kitchen/bathroom glass & containment | Zero depth-through-glass crashes; exact hinge axes |

---

## 1. Six High-Leverage API Trace Streams (Architecture, Schemas & Failure Guards)

### Rank 1 — Stream 2: Prior-Breaking Anti-Overfitting & Phrasing-Invariance Suite (`300k` Verified Rows)
* **Bottleneck Attacked:** Eliminates our three fastest-recoverable SFT bleeds: wording-bound tool skips (`H900` camera calls `66.4%`, `D580` distance calls `44.5%`), semantic class-median/prior guessing (`<30 cm` size `48.0 MRA`, `>=5` count `14.1–17.2 MRA`, `away` vs `toward`, `84%` front bias), and neighbor-task hijacking (`R1 m400` crashing zero-row `relative_count` `64.7 -> 38.1`).
* **Pipeline & Geometric Transforms (`ScanNet`, `ScanNet++`, `ARKit`, `MP3D`, `R0-rl` clean rooms):**
  1. **Projectively Exact Video Augmentations:** (a) **Horizontal Mirror (`I_t[:, ::-1]`):** Negate camera/world $X$ (`fx` principal offset updated, `left ↔ right` and `clockwise ↔ counterclockwise` inverted). (b) **Temporal Reversal (`t -> T-1-t`):** Invert camera displacement $\Delta\mathbf{t}$, yaw turn sign, and appearance order (`98%` vs `10%` bidirectional VSTI). (c) **Focal-Crop Parallax Warps (`I_t -> I'_t`, `K_t -> K'_t`):** Random `0.55–0.85x` crop + resize updating $(f'_x, f'_y, c'_x, c'_y)$ so 2D pixel area no longer predicts metric distance or object size. (d) **Frame-Rate & Anchor Jitter:** Sample `24/32/48/64` non-uniform motion-spaced clips so traces never memorize anchor `32`.
  2. **Allocentric & Unseen-Viewpoint (`>90°`) Ego-Rebasing:** Anchor local `+Z`-leveled frames at arbitrary object pairs (`"standing at A facing away from B"`, `"after turning 135° right from frame k"`), balancing `{front, back, left, right}` (`25%` each).
  3. **50+ Open-Ended Paraphrases + Comparative Neighbor Pairs:** `gemini-3.8-flash` + `gemini-4-hydrogen` rewrite every routed and direct template into `50+` natural, imperative, and robotic phrasings (`m / cm / mm / ft / in / deg`), always emitting **paired scalar + comparative rows** (`abs_size` + `relative_size`; `count` + `relative_count` + `"1+1=2"` multi-category sums) on the same room.
  4. **`X6`-Hard Multi-Instance Counting (`3..14` instances):** Reconstruct persistent 3D world instance clusters via `DA3 Nested` + `SAM 3` video tracking + mask-appearance cosine affinity; `Carbon` verifies every instance's first-seen anchor so `100%` of `Locate` frame citations have unoccluded raster support (vs `24%` in `R1`).
* **Hidden Trap & Guard:** *Projective scale conflict & opening-token leakage.* Never rescale global coordinates $(D_t, \mathbf{t}_t)$ without updating $K'_t$; randomize trace opening phrasing across all directions so `"Step 1"` never correlates with `toward` (`R1` lost `-1.33` ReVSI pts from `"Step 1" -> toward` correlation).

### Rank 2 — Stream 1: SPLIT-Style Closed-Loop Epistemic Traces on Real Noisy Head Outputs (`250k` Traces + `400k` 2D Box Rows)
* **Bottleneck Attacked:** Closes both the **grounding recall ceiling** (`DEV-MASK` GT masks `+13.8`, `J1 arm k` tight 2D boxes `+11.0`, while `Branch O` starved on `233` captures) and **single-shot head fragility** (SPLIT one-shot scripts lose `-11.8 pp` vs closed-loop verification on empty/fragmented tracks and noisy depth edges).
* **Two-Stage Pipeline (`ScanNet`, `ScanNet++`, `ARKit`, `MP3D`, `R0-rl` clean rooms):**
  1. **Stage 1A — Scaling `OWNHEAD` Supervision via `Argon+Carbon` + Frozen `SAM 3` (`400k` Box/Mask Rows):** Run blind `gemini-4-argon` and `gemini-4-carbon` 2D box + presence labeling across `4,000+` clean room captures (`IoU >= 0.70` agreement = `96.9%` accuracy), bypassing `SAM 3`'s broken text-`presence` veto (`<0.05` on `82%` of misses). Feed agreed tight boxes into frozen `SAM 3` mask decoder + `DA3 Nested` (`1.78°` pose, repairing `21/23` ARKit `G3T` failures) + `1-px` mask erosion + `vote_10_3_best` 2-frame voxel voting to build clean pseudo-GT 3D OBBs and train `Candidate 3` (`OWNHEAD`) at `15x` K1 scale.
  2. **Stage 1B — Mining Real Out-of-Fold Residual Traces (`250k` Multi-Turn Traces):** Run **out-of-fold student heads** (`PointDepth`, `CameraHead`, `OWNHEAD` fold models) + `SAM 3`/`G3T` on clean captures to capture *real* structured failures: (i) empty detection or indoor taxonomy mismatch (`"heater"` vs `"radiator"`), (ii) occlusion-boundary depth bleed (`>0.20 m` cross-view backprojection residual $\|\hat{\mathbf{p}}_{\mathcal{W}}^{(t_1)} - \hat{\mathbf{p}}_{\mathcal{W}}^{(t_2)}\|_2 > 0.25\text{ m}$), (iii) single-view truncated OBB (`0.73x` extent), and (iv) **out-of-view frame-$k$ queries** (`92.7%` of VSTI rows). `Neon` + `Carbon` synthesize compact 2–3 turn closed-loop traces (`<ground>`, synonym retry, `<look frame=k crop=...>`, wide-baseline $\Delta\theta \ge 15^\circ$ re-query, `<cam_to_box frame=k>` returning gravity-leveled `(range_m, bearing_deg, dz_m)`).
* **Hidden Trap & Guard:** *Never inject synthetic Gaussian noise*—real errors are edge-bleed, fragment peeling, and low-parallax blowup ($\sigma_Z \propto Z^2/(fB)$). Enforce `70%` clean 1-turn traces + `30%` genuine out-of-fold disagreement recovery traces so the student does not over-query clean views (`S3` rule: put uncertainty/disagreement directly in returned numeric fields, never soft text warnings).

### Rank 3 — Stream 3: Cross-Camera & Tabletop Embodied 4D Corpus (`220k` Verified Rows)
* **Bottleneck Attacked:** Bridges the `5 m` room-scan $\to$ `5 mm` robot-workspace chasm (`LIBERO-Plus` camera shifts drop OpenVLA `97.1 -> 59.7` and $\pi_0$ `94.2 -> 15.8`; room scans have `0` hands, `0` wrist cameras, and `0` sub-cm contact geometry).
* **4D Reconstruction & Metric Scale Locking (`DROID` 76k stereo episodes, `BridgeV2`, `OXE`, `Ego-Exo4D`, `Ego4D`, `HD-EPIC`):**
  - Run `DA3-Metric` + `ViPE` (`×1/1.089` scale, rejecting clips with `ViPE-vs-DA3 > 5°` static rotation delta) + `SAM 3` + `CoTracker3`.
  - **Strict Scale Locking:** Lock global metric scale $s^*$ to `±1 cm` via stereo baselines (`DROID`), Aria SLAM (`Ego-Exo4D`), or least-squares fit of segmented robot link/jaw widths to forward kinematics $\mathbf{T}_{\text{base}\leftarrow\text{ee}}(t)$ (`BridgeV2`/`OXE`). Uncalibrated monocular clips carry `metric_scale_locked = 0` (supervising relative depth + rotation + bearing only, never metric scale) and include focal-normalized ray metadata $(\log(f_x/W), \log(f_y/H))$ so `105°` wrist cams and `65°` room cams share one depth head.
* **Three Synthesized Supervision Families (`Neon` + `Carbon` over synced wrist+exo montages + 3D tracks):**
  1. **Wide-Baseline `wrist ↔ exo` SE(3) & `reach_base` (`80k` rows):** Predict $\mathbf{T}_{\text{wrist}\leftarrow\text{exo}}(t)$ across `60°–160°` baselines and robot-base 3D reach vectors `reach_base = x_target_base - x_eef_base` (directly pre-training `U1` `WhereProvider` and `FlowExpert` taps `16, -1`).
  2. **Millimeter Grasp Clearance, Swept-Volume & Occlusion QA (`70k` rows):** Gripper-to-obstacle clearance, container-slot fit (`L×W×H` margin), and cross-view recovery of wrist-occluded targets (`bowl-occluded plate` failure mode).
  3. **Ego-Decoupled `MANO → SE(3)` Pinch Chunks & Plücker Screw Axes (`70k` rows):** Lift `HaMeR/WiLoR` 3D hands (`8.4 cm` palm prior / SLAM), subtract camera ego-motion $\hat{\mathbf{T}}_{\mathcal{W}\leftarrow\text{cam}}(t)$ to obtain world-frame pinch trajectories $\mathbf{T}_{\mathcal{W}\leftarrow\text{pinch}}(t:t+H)$, and fit post-contact Plücker axes $(\hat{\omega}, \mathbf{q}, \theta(t))$ on drawers/doors/microwaves (`Carbon` tags `embodiment_mode ∈ {parallel_jaw, dexterous, suction}`, upweighting pinch/hook grasps for 2-finger VLAs).

### Rank 4 — Stream 4: Dynamic 4D & Long-Horizon Causal Streaming Traces (`120k` Verified Rows)
* **Bottleneck Attacked:** Static bundle adjustment breaks on moving objects/arms, while uniform 32-frame sampling loses `-6.5` ReVSI pts in long scans and collapses on `55-min` `HD-EPIC` (`53.2` Base vs `88.6` SPLIT) and causal `VQ3D` (`1.56 m -> 0.43 m`).
* **Sub-Stream 4A — Leak-Free Dynamic 4D Kinematics (`60k` rows; `Waymo train`, `NuScenes`, `DynamicReplica`, `PointOdyssey`, `Epic-Kitchens`):**
  - Reconstruct via `Point4D` + `CoTracker3` + `SAM 3` video masks, anchored to **paired-pixel known-$K$ `DA3-Metric` scale** on static background (`p_stat > 0.8`, eliminating `MapAnything`'s `1.36x` outdoor scale inflation) and **3-pt median-filtered stationarity-gated tracks** (eliminating jitter-induced stationary speed errors `-35.9 pp`). `Neon` authors ego-decoupled 3D velocity, relative closing speed, true object heading/turn sign, and moving-camera-vs-moving-object traces.
* **Sub-Stream 4B — Causal Loop-Closed 3D Memory (`60k` rows; `Ego4D` train `0 <= t <= t_q`, `HD-EPIC` train kitchens, `MP3D` multi-room tours):**
  - Build streaming 60-frame `DA3/HiP3R` submaps (`30f` overlap) + `SALAD` loop closure + blackout-aware yaw-continuity stitching (`dark_1fps` sidecar, gravity leveled *after* stitching). Train **two-budget causal retrieval traces**: coarse `SigLIP` timestamp scan (`<=t_q`) $\to$ `Flash` high-res crop check $\to$ `Neon` SE(3) submap projection emitting current egocentric `(range_m, bearing_deg, dz_m)` to out-of-view objects (`RoboCasa365` / `NU` mobile memory).
* **Hidden Trap & Guard:** *Future-frame leakage in causal memory.* Enforce hard video-slice truncation `frames[:t_q]` before feature extraction or Gemini prompt construction on all `VQ3D`/mobile-memory rows.

### Rank 5 — Stream 5: Adversarial Red-Teaming Self-Play Flywheel (`80k` Rows; `20k` per SFT/RL Round)
* **Bottleneck Attacked:** Hunts live checkpoint tail failures (`chiral 180° flips`, `foreshortened perspective illusions`, `grazing-angle >70° depth spikes`, `repetitive distractors`) and breaks past single-teacher ceilings.
* **4-Step Automated Self-Play Loop:** (1) Evaluate current student checkpoint (`R1 m400` $\to$ `Vehicle N` $\to$ `GeoLoop`) on `50k` clean 3D items and cluster residual errors by geometric taxonomy. (2) `Neon` inspects the 4D scene graph + failure cluster and writes **hard-negative twin pairs** on the *same* video (perturbing anchor frame $k_1 \to k_2$ or swapping reference object so heuristic shortcuts flip wrong) plus distractors matching exact coordinate bugs ($-R^\top\mathbf{t}$ vs $\mathbf{t}$, ego vs allocentric axes). (3) **Superhuman Mining:** Run blind RGB-only `Neon`, `Carbon`, and `Argon` rollouts; items where **all three frontier models fail blind** yet our **exact Python 3D solver + multi-view head trace succeeds** receive **3x training weight** and seed `rlkit-v1` / Parallax-Gated Geo-RLVR ($\Delta\theta_{ij} \ge 15^\circ$).
* **Hidden Trap & Guard:** *Unobservable/ambiguous trick drift.* `Carbon` enforces hard observability gates: target mask `>=400 px^2` in `>=2` frames, `100%` blind referent-uniqueness agreement, and GT choice margin `>3\sigma_{\text{GT}}`.

### Rank 6 — Stream 6: Procedural Synthetic Specular/Cluttered Tabletop 3D Data (`80k` Rows, Capped `<=10%` Mix)
* **Bottleneck Attacked:** Real RGB-D sensors and monocular teachers (`DA3`/`G3T`/`ViPE`) refract or drop out through **transparent glassware, stainless steel, mirrors, wire racks, and deep cabinet interiors**, causing robot grippers to smash straight through glass cups.
* **Autonomous Code-to-4D Loop:** `Neon` writes `1,000+` executable Python layout/material scripts over `BlenderProc` and `ManiSkill3` (`PartNet-Mobility` articulated appliances + `Objaverse` kitchenware + PBR glass/liquid/metal/mirror shaders + HDRI lighting + randomized wrist+exo rigs). Renderer exports **true first-surface mesh depth** (replacing optical refraction!), exact SE(3) poses, exact 3D OBBs, pixel visibility fractions, swept-volume collision labels, and Plücker hinge/slider screw axes. `Carbon` inspects `2x2` rendered grids and rejects mesh interpenetrations, floating objects, or uncanny lighting (`~70%` pass).
* **Hidden Trap & Guard:** *Synthetic texture drift.* Hard-cap procedural rows at **`<=10%` of total training tokens** and regularize ViT features with real video streams.

---

## 2. Exact Leak-Free Governance, Quality Gates & `trinity-2-28` Throughput Math

### 2.1 Fail-Closed Room-Keyed Exclusion Guard (`RoomExclusionGuard`)
Every candidate video/capture passes a canonical scene-ID normalizer (`dataset :: canonical_room_id`, stripping `_00/_01` visit suffixes, ScanNet++ DSLR/iPhone pairs, ARKit visit aliases, and MP3D scan hashes) checked against a SHA256-sealed blocklist before frame extraction:
1. **`BENCH v2` Official Splits:** All `VSI-Bench` (`5,130`), `ReVSI` (`6,158`), `VSTI-Bench` (`5,736`), `MMSI`, `MindCube` eval, `DSI-Bench`, `Ego-Exo4D` val/test, `VQ3D` val/test, `HD-EPIC` eval kitchens, `LIBERO` test episodes, and `R2R-CE val_seen/val_unseen`.
2. **Internal Dev & Calibration Suites:** All `372` `R0` rooms (`R0_ROOMS.txt` `bdb5d402...`), all `35` `dev-S1` rooms (`46` captures, `117` `DEV-MASK` items), and `vsti_rel_dev_r0` (`900` items).
3. **Held-Out & Withheld Grounding Rooms:** All `48` `K1-heldout` rooms (`216` `K1-X` rows) + all `80` withheld rooms (`sb_kbox4` rule: `239` `pinned_train` captures minus `6` withheld-room captures = **`233` clean K1 captures / `187` rooms**).
4. **`ReSTI ScanNet` Train-Split Trap:** Explicit block on all **`75` ScanNet `train` rooms used in `ReSTI`** + `21` `ScanNet-val` clips + `ReSTI` `Waymo`/`Omni6DPose` eval segment IDs (preventing standard ScanNet-train mining from contaminating `ReSTI`).
5. **Startup Canary Assert (`sb_auditfix2` pattern):** Worker startup injects 5 planted canary IDs (one from each set above) and aborts unless `5/5` raise `LeakageFatalError`; every `.tar.zst` shard embeds `EXCLUSION_MANIFEST_SHA256`.

### 2.2 Four-Stage Deterministic + Cross-Family Verification Funnel (`~75%` Yield, `0` Math Errors)
| Gate | Mechanism Executed on Local `/dev/shm` + Python `-I` | Defect Eliminated |
|---|---|---|
| **G1: Physical Calibration** | ScanNet++ v1 `2x` full-extent fix (`0.765` gap fix); paired-pixel known-$K$ scale (`DA3` vs `G3T/ViPE` static rot `<=5°` gate = `AUROC 1.00` ill-conditioned filter); `+Z` gravity; `1-px` mask erosion + Tukey IQR `vote_10_3_best`. | Over-scale (`1.11–1.52x`), half-box inflation, ARKit pose blowups, depth edge bleed. |
| **G2: Python 3D Solver** | Gemini emits typed `geo_ops` AST / `<ground>/<gap>/<move>/<turn>/<cam_to_box>` calls—never freehand math. Sandboxed Python recomputes & overwrites all intermediate readouts, bearings (`atan2(v·right, v·fwd)`), and unit conversions (`1e-6` exact); enforces choice margin `>3\sigma_{\text{GT}}` and `>=15%` relative gap. | **`0` arithmetic, trig, sign, or unit-conversion errors**; zero noisy boundary guesses. |
| **G3: `Argon+Carbon` Blind Filter** | Independent blind `gemini-4-argon` + `gemini-4-carbon` check on inline ROI crops: requires `IoU(box_A, box_C) >= 0.70`, `100%` referent uniqueness, target `>=400 px^2` in cited `Locate` frames, and zero synthetic artifacts. | **`96.9%` grounding precision**; kills ambiguous nouns & hallucinated `Locate` frames (`76% -> 0%`). |
| **G4: Grammar & Balance Hygiene** | Asserts `0` repetitive frame lists (`0` 16k loops), all cited frames $\in [1..N]$, answer prior caps (`"front" <=35%`, count `"1–2" <=35%`), mandatory comparative twin rows, and de-correlated opening tokens. | Zero counting loops, zero `relative_count`/`relative_size` hijacks, zero shortcut priors. |

### 2.3 Inline-JPEG Bandwidth, `OVER_CAP` Governance & `trinity-2-28` Throughput Math
* **Zero File-API & Zero NFS Architecture:** Do **not** upload MP4s to Gemini File API (`0.0 / 20.5 GB` used) and do **not** spawn heavy `claude -p` subagents per row. Run an async Python HTTP/2 worker pool (`/scratch/jjyeung/envs/gemini_proxy_v1/bin/python`, wrapped in `lanemsg register/run`) staging frames in **`/dev/shm` (`463 GB` free)** and **`/scratch/jjyeung` (`1.8 TB` free)**. Every API call logs exact tokens to `GEMINI_USAGE_LOG` and `GEMINI_USAGE_SHARED`, polling `/data2/.../gemini_subagents/OVER_CAP` + `proxy.log` HTTP `429`s every `15s` to auto-throttle whenever Main/SPLIT ramps up.
* **Exact Head-Node Internet Payload Math (`30 MB/s` Shared Cap Safe):**
  - Encode each capture as **2 numbered `3x4` contact-sheet JPEGs** (`1152x864`, q78 = `230 KB` for 24 badged frames) + **4 `512x512` ROI crops** (`88 KB`) = `318 KB` binary $\to$ **`0.425 MB` base64 outbound** + `0.018 MB` JSON inbound = **`0.44 MB` per 8-row `Neon/Carbon` synthesis call**.
  - Batched `Argon` + `Carbon` verification (`4` ROI crops = `0.12 MB`/call $\times 2$) = `0.24 MB` per 8 candidate (`~6.0` verified @ `75%` yield) rows $\implies$ **`0.113 MB` (`113 KB`) of head-node internet per verified row!**

| Operating Mode on `trinity-2-28` | Async Workers | API Rate (`RPM`) | Head-Node Internet | Verified Rows / Hour | Verified Rows / 24h | Time to `1.0M` Rows |
|---|---:|---:|---:|---:|---:|---:|
| **Conservative (Main-Active 25% Duty)** | `12` | `~144 RPM` | **`0.55 MB/s`** (`1.8%` of cap) | **`17,200 / hr`** | **`412,800 / day`** | **`2.4 days`** |
| **Standard Sustained (Tonight Default)** | `24` | `~288 RPM` | **`1.09 MB/s`** (`3.6%` of cap) | **`34,500 / hr`** | **`828,000 / day`** | **`1.2 days`** |
| **Peak Burst (Off-Peak Night Window)** | `48` | `~576 RPM` | **`2.18 MB/s`** (`7.3%` of cap) | **`69,000 / hr`** | **`1,656,000 / day`** | **`14.5 hours`** |

* **Governed `/data3` Archival:** Every `100k` verified rows compress via `zstd -9` to `~280 MB` (`.tar.zst`) on `/scratch/jjyeung`, mirrored over `.ib` (`172.16.1.x`, `0` NFS cap cost) and shipped to `/data3/jjyeung/distill_flywheel_20261128/` via `/scratch/jjyeung/io_governor/copy_archive.py` (`--bwlimit=4000` $\implies$ `70s` per `100k` rows).

### 2.4 Multi-Model API Routing, Exact `geo_ops` DSL & Sealed Row Schema
* **Division of Labor Across the 5 Unlimited Gemini Models:**
  - **`gemini-4-neon` (`high` effort):** Complex multi-turn Stream-1 recovery trace synthesis, Stream-3 clearance/subgoal planning, Stream-4 dynamic/causal submap reasoning, Stream-5 adversarial twin authoring, and Stream-6 `BlenderProc`/`ManiSkill3` Python scripts (`~5.2k` prompt / `~2.8k` output tokens per 8-row scene call).
  - **`gemini-4-carbon` (`medium` effort):** Co-author on Stream-1/3 traces, blind cross-model 2D box/referent verifier (paired with `Argon`), grasp morphology classifier (`parallel_jaw | dexterous | suction`), and Stream-6 render-artifact critic.
  - **`gemini-4-argon` (`medium/high` effort):** Blind 2D box + referent + option-uniqueness verifier (`Argon ∩ Carbon` `IoU >= 0.70` $\implies$ `96.9%` precision) and blind RGB rollout baseline in Stream-5 superhuman mining.
  - **`gemini-3.8-flash` (`default`) & `gemini-4-hydrogen` (`low`):** High-throughput `50x` open-ended wording/unit expansion (Stream 2) and dense timestamp crop-probing on hour-scale videos (`192–1,024` low-cost probes in Stream 4B).
* **Deterministic `geo_ops` Executable Primitives (Zero LLM Arithmetic):**
  1. `ground_obb(obj, frames, box2d_ac)` $\to$ `SAM 3` box-decode + `1-px` erosion + `DA3` lift + Tukey IQR `vote_10_3_best` $\to$ `{center_xyz, lwh_m, yaw_deg, n_views, backproj_err_m}`.
  2. `surface_gap(obj_a, obj_b, rule="box_grid_5cm")` $\to$ exact surface-to-surface min distance (`m`, `cm`, `ft`, `in`) + propagation $\sigma_{\text{gap}}$.
  3. `cam_delta(f_i, f_j)` $\to$ `+Z`-leveled `(dx, dy, dz, dist_m, yaw_turn_deg)` in frame `f_i` coordinates.
  4. `cam_to_box(frame_k, obj)` $\to$ projects persistent world OBB into frame `k` (even when `0` pixels visible at `k`!), returning `(range_m, horiz_dist_m, bearing_deg, dz_m, visible_px)`.
  5. `ego_rebase(origin_obj, face_obj, target_obj, flip_away=bool)` $\to$ exact `(bearing_deg, quadrant_4way, quadrant_8way, dist_m)`.
  6. `track_kinematics(obj, t0, t1)` & `fit_plucker_joint(part_track, t_contact, t_end)` $\to$ median-filtered static-decoupled `speed_mps`, `turn_deg`, or screw `(axis_xyz, moment_xyz, angle_deg)`.
  7. `swept_clearance(moving_obb, delta_se3, scene_tsdf)` $\to$ `(min_clearance_mm, collides_bool, blocking_obj)`.

```json
{
  "row_id": "w2_s1_scannetpp_0a5c_0042", "stream": "S1_epistemic_recovery",
  "canonical_room": "scannetpp::0a5c013435", "exclusion_sha256": "8f31c9...",
  "metric_scale_locked": 1, "intrinsics_norm": {"log_fx_w": -0.142, "log_fy_h": 0.145},
  "frame_transform": {"mirror_x": false, "reverse_t": false, "crop_xywh": [0.0, 0.0, 1.0, 1.0]},
  "prompt": "In inches, what is the closest clearance between the radiator and the armchair?",
  "trace_turns": [
    {"think": "Query radiator and armchair boxes across views.", "call": "<ground obj=\"radiator\" mode=\"box\">"},
    {"tool_response": "status=not_seen (0 proposals >=0.30)"},
    {"think": "Indoor scan alias check: retry radiator as heater and inspect frame 14.", "call": "<ground obj=\"heater\" mode=\"box\">"},
    {"tool_response": "center=[-1.12,2.41,0.44] lwh=[0.94,0.16,0.62] views=4 err=0.03m"},
    {"think": "Ground armchair and compute 5cm surface gap.", "call": "<ground obj=\"armchair\" mode=\"box\"><gap a=\"heater\" b=\"armchair\">"},
    {"tool_response": "distance 0.84 m"},
    {"think": "0.84 m * 39.3701 in/m = 33.07 in.", "answer": "33.1 inches"}
  ],
  "gt_solver": {"op": "surface_gap", "raw_m": 0.8398, "unit": "in", "exact_val": 33.063, "sigma_m": 0.038},
  "audit": {"argon_carbon_iou": 0.84, "referent_unique": true, "locate_frames_valid": true}
}
```

### 2.5 Training Integration Mix (Drop-In `Vehicle N+` & Clean-Sheet `GeoLoop` + `FlowExpert`)
* **Stage A — Immediate `Vehicle N+` / `OWNHEAD` Upgrade:** Train `Candidate 3` (`OWNHEAD`) on Stream-1's `400k` `Argon+Carbon` boxes; co-train `9B` SFT at `288` rows/step (`112` Stream-2 direct/comparative + `64` Stream-1/2 routed + `48` Stream-3/4 embodied/4D + `32` pose/flow + `32` box/pointing), keeping procedural Stream-6 `<=10%`.
* **Stage B — `Geo-RLVR` (`rlkit-v1`) & VLA Co-Training (`Test L` / `Test N` / `DROID`):** Run Parallax-Gated GRPO ($\Delta\theta_{ij} \ge 15^\circ$, length floor `n_min`, `×1.37` counterfactual value checks) on `80k` Stream-5/1 prompts; during VLA `FlowExpert` (`F1`) training, retain `15%` Stream-1/3 geometric replay on mid-trunk taps `16, 24, -1` so action fine-tuning never erases 3D grounding.

---

## 3. Immediate Tonight-Launchable Pilot: Phase 0 (`10,000` Verified Rows in `24h`, Zero NFS Reads)

### 3.1 Zero-NFS Local Inputs Already Staged on `trinity-2-28:/scratch/jjyeung` RIGHT NOW
1. **`233` Clean Room Captures (`187` rooms, `0` overlap with `BENCH v2`/`R0-dev`/`dev-S1`/`K1-heldout`/withheld):** `/scratch/jjyeung/orch_n30/sb_kbox4/pinned_train.json` (filtered against `RESTI_SCANNET_75`), paired with local frames `/scratch/jjyeung/k1_frames/`, corrected GT 3D boxes `/scratch/jjyeung/k1/run_convert_2/`, served `SAM 3 + G3T` caches `/scratch/jjyeung/k1/run_tower_sam_2/`, and real `step-544` own-head outputs `/scratch/jjyeung/k1/own_170235/native/probe/`.
2. **Local `DA3 Nested Giant-Large` (`6.76 GB`):** `/scratch/jjyeung/geo_bakeoff_kit/assets/da3/model.safetensors` + `/scratch/jjyeung/envs/sam3_capretry_native_v1`.
3. **Local Prompt Pool & 4D Kitchen/Dynamic Slices:** `/scratch/jjyeung/n30_mirror/tree_rebuild27/s27fix_n_go.tar` (`R0-rl` clean room prompts) + clean train-only captures in `/scratch/jjyeung/lv_hd6_1123` (`HD-EPIC`) and `/scratch/jjyeung/lv_pt_1122_t714` (`Point4D`).

### 3.2 Exact `10,000`-Row Phase-0 Composition (`~1.13 GB` Total Internet = `<20 min` at `1.09 MB/s`)
* **`3,500` rows (Stream 1 — Closed-Loop Epistemic Recovery) + `15,000` `Argon+Carbon` 2D Box Labels:** Mined from real disagreements between `own_170235` / `run_tower_sam_2` (`SAM 3` fragmentation, `presence` vetoes, ARKit `G3T` drift) and `DA3 Nested` + `Argon+Carbon` box-prompted `SAM 3` (`vote_10_3_best`), including `1,000` `<cam_to_box frame=k>` out-of-view VSTI recovery traces. The `15,000` verified tight 2D boxes export directly into `Candidate 3` (`OWNHEAD`) format.
* **`3,500` rows (Stream 2 — Prior-Breaking & Wording Suite):** `1,200` `50`-phrasing open-ended routed distance & camera rows (`m/cm/ft/in/deg`), `1,000` mirrored (`L↔R`) + reversed (`Δt`) + `>90°`/`away` ego-rebased rows, `800` focal-crop warped (`K -> K'`) `<30 cm` object-size & `X6`-hard (`>=5` + `"1+1=2"`) counting rows (`100%` `Carbon`-verified `Locate` frames), and `500` `relative_count`/`relative_size` neighbor-guard pairs.
* **`1,500` rows (Streams 3 & 4 — Kitchen Embodied Clearance & Causal 4D):** Ego-decoupled kitchen hand-object cm clearance, articulated cabinet/drawer Plücker axes, causal `t <= t_q` 3D object memory, and stationarity-gated `Point4D` velocity traces from local `lv_hd6_1123` / `lv_pt_1122_t714` train captures.
* **`1,500` rows (Stream 5 — Adversarial Truth-Flipping Twins):** Paired `(frame k1, frame k2)` VSTI & chiral `180°` hard-negative twins authored by `Neon` and certified by Python 3D solver + blind `Carbon` referent check.

### 3.3 Hour-by-Hour 24h Execution Schedule & Decisive Pass/Kill Gates
1. **Hours `0–2` (Local Pre-Flight & `DA3` Relift on `trinity-2-28` GPUs `4,5,6,7` under `vnice.sh`):** Run `RoomExclusionGuard` (`5/5` canary test), stage contact sheets in `/dev/shm/w2_phase0`, and run `DA3 Nested` + frozen `SAM 3` box-relift across the `233` clean captures (`~22 min` on 4x Ada 49GB, `0` NFS IO).
2. **Hours `2–4` (API Generation & 4-Gate Filtering):** Launch `C=24` async workers (`lanemsg run bluesky28/w2_phase0`, `1.09 MB/s` internet, `OVER_CAP`-guarded) across `Neon`/`Carbon`/`Argon`/`Flash` $\to$ `13.5k` raw $\to$ **`10,000` G1–G4 verified rows** + **`15,000` `OWNHEAD` box labels**.
3. **Hours `4–6` (Cross-Family Hostile Audit & Governed Archive):** Run 1 targeted `nv_agent.sh --model astra-6.2 --effort high` hostile audit on `200` stratified rows (gate: `>=98%` math/visual validity, `0` leaks); seal `w2_phase0_10k.tar.zst` (`~32 MB`) to `/data3` via `io_governor` (`--bwlimit=4000`, `<10s`). Launch full `1M`-row Stream 1–6 daemon immediately while training runs (`launch-first-check-after`).
4. **Hours `6–24` (Two Parallel Decisive GPU Kill-Tests):**
   - **Kill-Test A (`trinity-2-28` `vnice.sh`, `<=4` Ada-h):** Train `Candidate 3` (`OWNHEAD`) with the `15k` `Argon+Carbon` boxes; evaluate on `DEV-MASK 117` (**PASS:** `OWN - a >= +8.0` MRA, presence `AUROC >= 0.88`).
   - **Kill-Test B (Orchard `advanced` `4x H100`, `~15 H100-h`, 100-step branch from `R1 step 400`):** Co-train `phase0_10k` and evaluate paired deltas (**PASS:** `H900` camera call rate `66.4% -> >=95%` [`+15` pts], `D580` distance call rate `44.5% -> >=92%` [`+8` pts], `>=5` count & `<30 cm` size `+5` pts, `relative_count >= 64%` with `0` loops).

### 3.4 Exact Tonight Launch Sequence on `trinity-2-28` (`0` NFS Reads, `vnice` + `OVER_CAP` Compliant)
```bash
# 1. Stage workspace on local NVMe + /dev/shm RAM disk; verify 5/5 leak-canary asserts fail-closed
mkdir -p /scratch/jjyeung/w2_flywheel_20261128/{work,out,logs} /dev/shm/jjyeung_w2_sheets
/scratch/jjyeung/envs/gemini_proxy_v1/bin/python -I /scratch/jjyeung/w2_flywheel_20261128/guard_exclusion.py \
  --pinned /scratch/jjyeung/orch_n30/sb_kbox4/pinned_train.json --assert-canaries

# 2. Relift 233 clean captures with local DA3 Nested + frozen SAM3 on free Ada GPUs 4,5,6,7 under vnice
CUDA_VISIBLE_DEVICES=4,5,6,7 /data3/shared/scripts/vnice/vnice.sh \
  /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python -I /scratch/jjyeung/w2_flywheel_20261128/relift_da3_k1.py \
  --da3 /scratch/jjyeung/geo_bakeoff_kit/assets/da3/model.safetensors --frames /scratch/jjyeung/k1_frames \
  --sheets-out /dev/shm/jjyeung_w2_sheets --out /scratch/jjyeung/w2_flywheel_20261128/work/da3_clean233.npz

# 3. Launch 24-worker inline-JPEG Gemini Neon/Carbon/Argon/Flash factory (~1.09 MB/s internet, OVER_CAP-polled)
lanemsg register bluesky28/w2_phase0_gen
lanemsg run bluesky28/w2_phase0_gen -- /scratch/jjyeung/envs/gemini_proxy_v1/bin/python -I \
  /scratch/jjyeung/w2_flywheel_20261128/run_factory.py --workers 24 --target-rows 10000 \
  --sheets /dev/shm/jjyeung_w2_sheets --geom /scratch/jjyeung/w2_flywheel_20261128/work/da3_clean233.npz \
  --own /scratch/jjyeung/k1/own_170235/native/probe --tower /scratch/jjyeung/k1/run_tower_sam_2 \
  --out /scratch/jjyeung/w2_flywheel_20261128/out/phase0_10k.jsonl
```
