# Internalizing SPLIT: Executable Geometry (`GeoAPI-v2`), Epistemic CoT & Parallax-Gated Geo-RLVR

**Lane:** `bluesky28/w2_split_internalization_rl` | **Date:** 2026-11-28 | **Target:** 9B Self-Contained Spatial VLM + VLA Backbone

---

## 0. Core Thesis & Quantitative Problem Statement
SPLIT proved three laws that govern a 9B student: (1) small models require **both** metric perception and grounded thinking (`X1`: Qwen3-8B drops `74.8 → 48.7` without CoT), (2) offloading perception into structured geometry collapses metric guessing (`14.4% → 2.1%`) and compresses thinking tokens `2.6–7.1×` (`Paired Thoughts`), and (3) **closed-loop verification over noisy tools beats one-shot programs by `+11.8 pp` (`75.4 vs 63.6`, `W1`)** because single-shot scripts cannot recover from empty detections (`15.3%` of queries: `52.6 vs 72.0`) or multi-instance tracks (`80.8%`: `64.9 vs 78.1`).

Our current student (`LEG-S1 step 544 → R1 step 400`, `Qwen3.5-9B + frozen G3T×OwnDepthScale + SAM 3`) already achieves `73.89` on VSTI-450 primary (matching `Argon 73.73`) and `100%` tool-copy fidelity on in-distribution camera queries, yet fails to internalize SPLIT for four structural reasons:
1. **Surface-template & unit brittleness:** Novel phrasings drop camera call rate `100% → 66.4%` (`H900`, `84.1 → 53.0`) and distance calls `97.6% → 44.5%` (`D580`; `62/150` skipped at R1 m200); prose unit conversion causes `-19.6` imperial slips and neighbor-task hijacks (`rel_size -10.7`, `rel_count 64.7 → 38.1`).
2. **One-shot blindness over broken fragments:** `0/73,088` SFT pool rows contained `"not seen"` or multi-instance conflicts, producing 16k-token loops (`136–198` calls) on null returns and `AUROC 0.60–0.66` on offline cue choosers (`≤0` held-out gain). Meanwhile `84/89` `dev-S1` operands fail pre-lift (`92%` of empty visible frames are vetoed by `SAM 3`'s `presence < 0.05`, yet box-prompted `SAM 3` arm `k` recovers `+11.0 [+0.7, +20.9]` = `80%` of the `+13.8` GT-mask ceiling).
3. **Missing geometric primitives:** No gravity-leveled egocentric polar readout (causing `13–30%` text `atan2` errors, `-1.33` ReVSI `away`-flip omissions, and `2,100` wasted trig tokens), no `camera@k` query (`92.7%` of VSTI cam-obj targets are out of view at frame `k`), no 4D dynamic velocity, and no visibility/VLA clearance raycast.
4. **SFT prior lock-in & tower fragility:** Direct paths collapse onto class-median size (`<30 cm` MRA `48.0`) and constant-`"2"` counting (`≥5` MRA `14–17`), while `G3T` fails rigid checks on `21/23` ARKit captures (`K5-S` deterministic/default divergence separates gross failures at `AUROC = 1.000`).

We eliminate all four failures via **(1) `GeoAPI-v2`** (a 6-primitive wording- and unit-invariant executable interface), **(2) Out-of-Fold Real-Residual Epistemic Recovery SFT**, **(3) Parallax-Gated Geo-RLVR** on `rlkit-v1` + `R0-rl` (`272` zero-leak rooms) with closed-loop EM head refinement, and **(4) a 72-hour kill-test ladder**.

---

## 1. `GeoAPI-v2`: Universal, Wording-Invariant, Zero-Brittleness Geometry Interface

### 1.1 Orthogonal 6-Primitive Basis over `{Depth, Pose/Gravity, 4D Flow, 3D Slots}`
Replace ad-hoc `<ground>/<gap>/<move>/<turn>` templates with **six typed, composable JSON-in-tag primitives** executed deterministically inside `generate()` against the checkpoint's perception backend (`DA3 Nested` / `G3T×scale_donor`, `Point4D` flow, box-prompted `SAM 3` / `Candidate 2-3`, persistent 3D voxel slots). Every primitive shares one **gravity-leveled metric world frame** (`+Z` up, floor $\parallel XY$, metres, OpenCV camera axes `+X right, +Y down, +Z fwd`).

| Primitive | Typed Signature | Deterministic Backend Operation | Returned Fields (Primary Metric + Epistemic Telemetry) |
|---|---|---|---|
| **`locate`** | `locate(q, frames="auto", box_hint=None, max_k=3)` | Resolves persistent **3D Instance Slots** (`slot_id`). When `box_hint=[t,x1,y1,x2,y2]` is passed, bypasses text/presence veto and calls **box-prompted frozen `SAM 3`** (`J1` arm `k`, `+11.0 pp`) + multi-view `vote_10_3_best` OBB lifting (`+5.65` K1). | `slots:[{id, xyz, obb_lwh, yaw, first_t, vis_f, reproj_m, parallax_deg, spread_m}]`, `margin_top2`, `pose_cond_deg`, `status ∈ {OK, MULTI_SLOT, LOW_PARALLAX, UNSEEN}` |
| **`ego_polar`** | `ego_polar(ref, look_at=None, targets=[...], facing="toward"\|"away", unit="m")` | Rebases `targets` into a **gravity-leveled egocentric frame** at camera `ref=t` (solving `92.7%` out-of-view VSTI@k) or `ref=slot_id` looking toward/away from `look_at`. Applies exact `180°` yaw offset for `facing="away"` inside code—eliminating LM `atan2` and `"Step 1: find"` spurious correlations (matches SPLIT `L12` `2.2×` speedup). | Per target: `{id, r_horiz, r_3d, bearing_deg ∈ [-180,180], dz, octant, unit_val, reproj_m}` (`0°` ahead, `+90°` right, `±180°` behind) |
| **`measure`** | `measure(op, a, b=None, delta_xyz=None, unit="m")` | `op ∈ {surface_gap, center_dist, obb_size, volume, room_area, swept_clear}`. Runs `box_grid_5cm` gap, co-calibrated paired-pixel known-$K$ trimmed OBB extents, alpha-shape floor area, or TSDF swept-box clearance. **Executes exact unit conversion inside code** (`unit ∈ {m,cm,ft,in,m2,ft2}`). | `{val_unit, unit, val_m, lwh_unit, clear_ok, min_clear_m, margin_m, status}` — LM **never** converts metres→feet/cm in prose! |
| **`motion`** | `motion(target, t0, t1, frame="ego_t0"\|"world", unit="m")` | `target="camera"` or `slot_id`. Computes SE(3) ego displacement/yaw (`DA3 Nested` / `G3T×scale_donor`) or `p_stat`-decoupled 4D object track (`Point4D`, endpoint-clamped, 3-pt median-filtered path, stationarity probability). | `{disp, dx_fwd, dy_right, dz_up, yaw_deg, path_len, speed_mps, p_stat, pose_cond_deg, unit}` |
| **`raycast`** | `raycast(origin, target_or_dir, mode, clearance_m=0.0)` | `mode ∈ {los, corridor_clear, floor_waypoint, subgoal_se3}`. Marches occupancy grid along ray/corridor for line-of-sight, route turns, `NU` floor-plane click lifting (`88.7%` R2R-CE oracle), and `U1` 6-DoF robot reach vectors (`reach_base`). | `{visible, occluded_by, free_frac, min_clear_m, waypoint_xyz, subgoal_se3}` |
| **`inspect`** | `inspect(frame, crop_box=None, view="rgb"\|"bev")` | **Foveated visual verification:** returns a crisp `640×480` RGB crop (for `<1%`-area small objects, specular checks, or emitting `box_hint`) OR a labeled top-down BEV projection with `slot_id` overlays (`s0, s1...`) to disambiguate multi-instance tracks. | Visual tokens injected as `<tool_obs>` (capped at `≤2` crops/episode to keep latency bounded) |

### 1.2 Task-to-Primitive Composition Matrix (Zero New Templates Across Benchmarks & VLAs)
| Spatial / Embodied Task | Minimal `GeoAPI-v2` Composition | Defect Eliminated |
|---|---|---|
| **Abs. distance / Room / Obj. size** | `locate(A)` → `locate(B)` → `measure(op, A, B, unit=req)` | `62/150` skipped calls, `-43.9` cm copy bugs, `-19.6` imperial slips, `rel_size` hijacks |
| **Rel. direction (`toward`/`away`) & VSTI@k** | `locate(ref, target)` → `ego_polar(ref, look_at, [target], facing)` | `13–30%` text `atan2` errs, `"Step 1: find"` away-bug (`-1.33`), `92.7%` out-of-view VSTI@k |
| **Camera / 4D object kinematics (VSTI/DSI/ReSTI)** | `motion("camera"\|slot_id, t0, t1, frame="ego_t0", unit=req)` | Reversed-playback forward priors (`10%→98%`), `66.4%` H900 held-out wording drop |
| **Counting (`≥5`), Appearance order, Multi-inst.** | `locate(q, max_k=12)` → if `MULTI_SLOT`/low margin: `inspect(view="bev")` | Constant-`"2"` collapse (`≥5` MRA `14–17`), `28/150` counting loops, `>32` hallucinated frames |
| **Route planning, LOS, VLA `U1` / `NU`** | `locate(goal)` → `raycast(origin, goal, mode="corridor_clear"\|"subgoal_se3"\|"floor_waypoint")` | Unserved route calls, `1.94×` Habitat depth drift, camera-shift fragility (`LIBERO-Plus`) |

### 1.3 Wire Format Example (Closed-Loop `UNSEEN` → `box_hint` Recovery + Built-In Units)
```xml
<think>Intent: abs_distance(heater, sofa, unit=ft). Locate both in shared world frame.</think>
<geo>{"op":"locate","q":"heater"} ; {"op":"locate","q":"sofa"}</geo>
<tool_response>{"heater":{"status":"UNSEEN","best_cand_f":14,"pose_cond_deg":1.2},
 "sofa":{"status":"OK","slots":[{"id":"s0","xyz":[1.82,2.40,0.45],"parallax_deg":31.4,"reproj_m":0.06}]}}</tool_response>
<think>Heater vetoed (presence<0.05); inspect f14 to box-prompt SAM 3 directly.</think>
<geo>{"op":"inspect","frame":14,"view":"rgb"}</geo>
<tool_obs>[640x480 high-res visual tokens of frame 14]</tool_obs>
<think>Radiator visible lower-left [0.08,0.52,0.34,0.88]; re-locate with box_hint.</think>
<geo>{"op":"locate","q":"heater","box_hint":[14,0.08,0.52,0.34,0.88]}</geo>
<tool_response>{"heater":{"status":"OK","slots":[{"id":"s1","xyz":[0.21,1.15,0.42],"parallax_deg":24.8,"reproj_m":0.08}]}}</tool_response>
<geo>{"op":"measure","op_type":"surface_gap","a":"s1","b":"s0","unit":"ft"}</geo>
<tool_response>{"status":"OK","val_unit":"4.68 ft","unit":"ft","val_m":1.426,"margin_m":0.09}</tool_response>
<think>Check: 1.43 m ≈ 4.68 ft, both slots OK (reproj<=0.08 m, parallax>=24.8°). Answer ready.</think>
<answer>4.68</answer>
```

### 1.4 Eliminating Wording Brittleness, Unit Hijacks & Advisory-Flag Regressions (`S3`)
1. **Hard Epistemic Status Codes, Never Soft Prose Warnings (`S3` Rule):** SPLIT proved advisory warnings (`"please verify visually"`) regress `-8` to `-18` pp because LMs still copy the default scalar. `GeoAPI-v2` enforces a **strict value-gating contract**:
   - When `status == OK` (`reproj_m ≤ 0.15`, `parallax_deg ≥ 15°`, `pose_cond_deg ≤ 3.0°`, `margin_top2 ≥ 0.15`), `GeoAPI-v2` emits the clean primary scalar in the requested `unit`.
   - When `status ∈ {MULTI_SLOT, LOW_PARALLAX, POSE_UNSTABLE, UNSEEN}`, `GeoAPI-v2` **withholds the aggregated single scalar** and prints the exact diagnostic payload (e.g., competing `slot_0/slot_1` frames & positions, or `pose_cond_deg=9.4°` from `K5-S` / `DA3` covariance) so the model cannot lazily copy a poisoned number and must branch into recovery or visual fallback.
2. **Built-In Exact Unit Normalization:** `measure`/`motion`/`ego_polar` accept `unit ∈ {m, cm, ft, in, m2, ft2}` parsed from the question intent; the return prints `val_unit` as the primary field (`"142.5 cm"` / `"4.68 ft"`). This eliminates prose unit arithmetic, `-43.9` cm copy bugs, `-19.6` imperial slips, and `D0`-style neighbor-task hijacks (`rel_size`/`rel_count` share the exact same `measure` / direct grammar with zero stripped templates).
3. **Wording-Invariant Semantic Dispatch:** Both SFT and RL wrap every prompt through **12+ diverse lexical skins** (VSI-590K, ReVSI, H900, D580, embodied VLA commands, Gemini Flash paraphrases) and **identical opening tokens** (`<think> Intent: ...`) across `toward`/`away`, routed/direct, and all task families—destroying the `"Step 1: find"` vs `"Seen:"` surface-correlation bug.
4. **Co-Calibrated Metric Scale + Oriented Extents (`S1–S2` Fix):** Replace single-frame `lift_bestspread` (`0.73–0.81×` shrinkage) with paired-pixel known-$K$ scale (`scale_donor` `V2` or native metric `DA3 Nested`) + `vote_10_3_best` oriented trimmed boxes, preventing scale overestimation (`1.11–1.52×`) and extent shrinkage (`0.8×`) from masking each other.

---

## 2. Closing the `+11.8 pp` `W1` Gap: Closed-Loop Epistemic Recovery & Self-Verification

One-shot programs fail `−11.8 pp` below SPLIT (`63.6 vs 75.4`) strictly on **empty detections**, **multi-instance disambiguation**, and **noisy single-view lifts**. Training recovery requires **zero synthetic Gaussian noise** (real head errors are structured: `SAM 3` presence veto, grazing depth bleed, ARKit pose ill-conditioning).

### 2.1 Four Canonical Recovery Playbooks (Bounded `T_max = 3` Turns, Zero 16k Loops)
```
Call 1: locate(q) / motion(...)
  ├─ status == OK & reproj_m <= 0.15 & parallax >= 15° ──► compose(ego_polar/measure) ─► 1-line check ─► <answer>
  ├─ status == UNSEEN (92% presence-vetoed!)           ──► inspect(best_frame) ─► emit box_hint=[t,x1,y1,x2,y2]
  │                                                        ─► locate(q, box_hint=...) [J1 arm k: +11.0 pp!]
  ├─ status == MULTI_SLOT (margin_top2 < 0.15)         ──► inspect(view="bev") or crop(s0,s1) ─► bind referent slot_id
  ├─ status == LOW_PARALLAX or reproj_m > 0.15         ──► locate(q, frames=wide_baseline_t2) [Δθ >= 15°] ─► confirm agreement
  └─ status == POSE_UNSTABLE (pose_cond_deg > 5°) or   ──► explicit graceful fallback to direct RGB visual reasoning
     turn == T_max (hard stop)                             (never repeat an identical call -> 0% cap loops)
```

### 2.2 Stage A: Out-of-Fold Real-Residual Recovery SFT (Unlimited Gemini API Factory)
1. **Mine Real Student Residuals Out-of-Fold:** Run our actual perception stack (`R1 step 400` / `DA3 Nested` + `SAM 3` + `Candidate 3` box head) on **clean training rooms** (`ScanNet`, `ScanNet++`, `ARKitScenes`, `MP3D`, `Ego-Exo4D`; **strictly 0 rooms from `BENCH v2`, `dev-S1`, `R0-dev`, or `R0-rl`**). Partition outcomes into:
   - `45%` **Clean 1-Pass Grounded CoT (`status=OK`)**: Minimalist SPLIT Paired-Thought traces (`<250` think tokens, `0%` metric guessing `M`, `0%` blind pixel search `V`, explicit `G` geometric composition + `C` 1-line sanity verification).
   - `35%` **Real-Residual Epistemic Recovery Traces**: Sampled exclusively from real OOF failures (`UNSEEN → inspect + box_hint`, `MULTI_SLOT → BEV/crop disambiguation`, `LOW_PARALLAX → second view Δθ ≥ 15°`, `POSE_UNSTABLE → direct visual fallback`).
   - `20%` **Complete Neighbor & Invariance Coverage**: Includes **every** direct/neighbor task (`relative_size`, `relative_count`, multi-category `"1+1=2"` counting, counts `≥5`, small objects `<30 cm`, `away/toward` twins, out-of-view VSTI@k) plus **physical invariance twins** (L/R mirrored videos flipping `bearing_deg`, reversed playback negating `motion`, and in-scene rescaled objects) to kill Cambrian-P/VLM-3R shortcut overfitting.
2. **Gemini `Neon` + `Carbon` + `Argon` Verification Pipeline:** `Neon` writes compact recovery traces conditioned on real OOF head outputs + exact 3D scene graphs; our deterministic 3D solver verifies every intermediate coordinate and final answer; `Argon + Carbon` agreement (`96.9%` precision) filters referent ambiguity; `Flash` injects `12×` lexical/unit paraphrasing.
3. **Training Hygiene:** Loss-mask all `<tool_response>` and `<tool_obs>` tokens; enforce **uniform Low-thinking compression** on post-tool turns (SPLIT `L9`/`L11`); freeze `scale_donor` (`V2`) so SFT cannot drift metric scale (`H3`-proof).

---

## 3. Parallax-Gated Geo-RLVR (Online GRPO on `rlkit-v1` + Closed-Loop EM Head Refinement)

### 3.1 Composite Verifiable Reward (Zero Leakage, `<2 ms` CPU Eval/Rollout)
On zero-leak `R0-rl` (`272` rooms) + clean 3D training rooms, each rollout $y_i$ in a GRPO group $\{y_1, \dots, y_G\}$ ($G=8$) interacting live with `GeoAPI-v2` receives:
$$R(y_i) = R_{\text{ans}}(y_i) + \lambda_{\text{tri}} R_{\text{tri}}(y_i) + \lambda_{\text{calib}} R_{\text{calib}}(y_i) + \lambda_{\text{ground}} R_{\text{ground}}(y_i) - \lambda_{\text{loop}} R_{\text{loop}}(y_i)$$
with initial weights $\lambda_{\text{tri}}=0.20,\; \lambda_{\text{calib}}=0.25,\; \lambda_{\text{ground}}=0.20,\; \lambda_{\text{loop}}=0.40$ ($R_{\text{ans}}$ always dominates):
- **$R_{\text{ans}} \in [0,1]$:** Deterministic benchmark scorer—exact MCQ match, standard 10-threshold MRA for numeric metric answers, or tolerance-gated SE(3) subgoal success for VLA prompts. Zero LLM judge.
- **$R_{\text{tri}} \in [0,1]$ (Parallax-Gated Multi-View Triangulation Consistency):** For any target queried across two views $(t_1, t_2)$, compute viewing-ray angle $\Delta\theta_{12} = \arccos(\hat{\mathbf{r}}_1 \cdot \hat{\mathbf{r}}_2)$ and baseline ratio $\beta_{12} = \|\hat{\mathbf{t}}_1 - \hat{\mathbf{t}}_2\|_2 / \bar{D}$.
  $$R_{\text{tri}} = \mathbb{I}\!\big(\Delta\theta_{12} \ge 15^\circ \;\lor\; \beta_{12} \ge 0.20\big) \cdot \mathbb{I}\!\big(R_{\text{ans}} \ge 0.5\big) \cdot \exp\!\left(-\frac{\|\hat{\mathbf{p}}_{\mathcal{W}}^{(t_1)} - \hat{\mathbf{p}}_{\mathcal{W}}^{(t_2)}\|_2}{0.25\text{ m}}\right)$$
  **Anti-hack guarantees:** (a) adjacent frames ($t_2 = t_1+1$, $\Delta\theta < 15^\circ$) get **exact 0**—eliminating degenerate baseline hacking; (b) gating by $R_{\text{ans}} \ge 0.5$ blocks triangulating a wrong background object for free reward. On unlabeled videos (Waymo/DROID/Ego4D), drop the $R_{\text{ans}}$ gate and cross-check against `CoTracker3`/`ViPE` correspondences for unsupervised RL!
- **$R_{\text{calib}} \in [-0.25, +0.30]$ (Calibrated Epistemic Head-Use & VoI Reward):**
  - **Recovery bonus (`+0.30`):** Initial call returned `status ∈ {UNSEEN, MULTI_SLOT, LOW_PARALLAX}`, policy executed recovery (`inspect`/`box_hint`/wide-baseline call), and improved $R_{\text{ans}}$ over the frozen one-shot baseline on that prompt.
  - **Clean efficiency bonus (`+0.10`):** Initial call returned `status == OK` (`reproj_m ≤ 0.12`) and policy answered in 1 tool turn without wasted extra calls.
  - **Blind-trust / hallucination penalty (`-0.25`):** Policy copied a metric from `POSE_UNSTABLE` without verification, or ignored `UNSEEN` to fabricate numbers in prose.
- **$R_{\text{ground}} \in [0, 0.25]$:** Pre-cached `R0-rl` 3D scene-graph grounding score (`1.0` if queried `slot_id` or `box_hint` achieves 2D IoU `≥0.5` or 3D centroid error `≤0.35 m` on all required operands; `0` otherwise)—closing the `AUROC 0.60` wrong-object trap.
- **$R_{\text{loop}} \ge 0$:** `+0.50` per duplicate identical call, `+0.30` per turn beyond $T_{\max}=3$, `+0.50` on malformed tags/empty `print("Done")`, `+0.15` if think tokens exceed `512` without invoking a new tool call.

### 3.2 Preventing Direct-Guess Collapse & Fast Live Rollouts (`rlkit-v1` → `Geo-RLVR v2`)
Naive outcome GRPO collapses into short direct guesses (SpaceR ReVSI `30.5`) because prior guesses are faster and get lucky on easy items. We upgrade `rlkit-v1`'s proven path-forcing + `×1.37` perturbation into **four locked mechanisms**:
1. **Stratified Dual-Branch Rollout Groups ($G=8$) & Advantage Mixing:** On every routable/hybrid prompt, partition the group into **4 Tool-Forced rollouts** ($\mathcal{G}_{\text{tool}}$, decoding grammar requires $\ge 1$ `GeoAPI-v2` call + path-specific `n_min` length floor from `rlkit-v1`) and **4 Free rollouts** ($\mathcal{G}_{\text{free}}$). Compute:
   $$\hat{A}_i = 0.7\,\frac{R(y_i) - \mu_{\text{branch}(i)}}{\sigma_{\text{branch}(i)} + \epsilon} + 0.3\,\frac{R(y_i) - \mu_{\text{all}}}{\sigma_{\text{all}} + \epsilon}$$
   Within-branch normalization (`0.7`) optimizes *which* primitive/frame/recovery wins inside the tool path without competing against short guesses; pooled normalization (`0.3`) teaches risk-aware routing ONLY when head calls beat direct RGB.
2. **Runtime Counterfactual Faithfulness Perturbations (`25%` of RL batch):** On 1/4 of tool-forced prompts, perturb the returned `<tool_response>` on the fly and re-score the continuation against the perturbed ground truth:
   - **Metric scaling (`×1.37` or `×0.73`):** `measure` / `motion` scalars scale by `1.37×`; if the policy still emits the unperturbed class/room prior, set $R_{\text{ans}}=0$ and apply `-0.50` shortcut penalty.
   - **Chiral bearing flip (`bearing_deg → -bearing_deg`):** `ego_polar` flips left↔right; MCQ answer must invert.
   - **Slot-order shuffle (`slot_0 ↔ slot_1` on `MULTI_SLOT`):** Kills blind "pick first slot" heuristics without `inspect`.
3. **Anti-Prior RL Curriculum:** Oversample `R0-rl` prompts where blind priors score `<0.30`: counts `≥5`, objects `<30 cm` or `>250 cm`, `away`-facing twins, out-of-view VSTI@k, and held-out lexical paraphrases.
4. **Hybrid Pre-Cache + Live `<40 ms` Recovery Engine (`~15 h` for `32K` Rollouts on 4× H100):** Re-running `G3T`/`DA3` inside every rollout would stall RL. Because `R0-rl` has **272 rooms**, Rung 0 pre-caches per-room dense depth, poses, gravity, 4D flow, `SAM 3` image embeddings, and default text pools on Orchard node-local `/tmp` (`~38 GB`). During GRPO, `ego_polar`/`measure`/`motion`/`raycast` run in **`<2 ms` CPU**, while live interactive recovery (`locate(box_hint=...)` → frozen `SAM 3` mask decoder + `vote_10_3_best` lift) runs in **`<40 ms` GPU**—saturating 4× H100 cleanly.

### 3.3 Closed-Loop EM / RL Head Refinement (Refining Heads Without `H3` Scale Drift)
Passing noisy RL policy gradients straight into `PointDepthHead` triggers the exact `H3` scale-drift failure (`+1.4%` at R1 step 400). Instead, run a **strictly decoupled Alternating EM-RL Loop** every 150 GRPO steps:
- **E-Step (Orchard 4× H100 — Policy GRPO, Frozen `scale_donor` & Towers):** Optimize the 9B LM policy with live `GeoAPI-v2` rollouts. Log a lightweight **Hard-State Replay Buffer** of every decision-critical perception failure: (1) `UNSEEN` frames rescued by `inspect + box_hint` (producing verified 2D box pseudo-labels!), (2) wrong-slot frames caught by `R_ground == 0`, and (3) wide-baseline pairs ($\Delta\theta \ge 15^\circ$) where winning rollouts measured high 3D backprojection disagreement (`>0.15 m`).
- **M-Step (Trinity 49GB GPUs in parallel — Weighted Supervised Head Update):** Run a `150`-step isolated supervised update on:
  1. **`Candidate 3` Own 2D Box+Presence Head (or `Candidate 2` `SAM 3` Detector LoRA):** `3×` upweight the RL-mined `UNSEEN`/wrong-slot frames + `box_hint` recoveries (directly attacking the `+11.0/+13.8` grounding ceiling).
  2. **Pose / Depth / 4D Flow Heads (or `DA3 Nested` distillation):** `3×` upweight RL-mined wide-baseline pairs (`Δθ ≥ 15°`) while keeping `scale_donor` (`V2`) frozen behind an automated **scale-parity gate (`|s_new/s_GT - 1| ≤ 0.005`)**.
  3. **RAFT/RWR SFT Anchor (`10%` mix):** Re-anchor KL/SFT on the top-reward verified recovery trajectories so format, units, and non-routed skills never drift.

---

## 4. Decisive 48–72h Kill-Test Ladder (Starting Today on `rlkit-v1` + `R0-rl` + Orchard 4× H100)

**Compute Allocation (Claimable Now, 2026-11-28):** Orchard `advanced` (**4× H100 80GB**, 24h non-preempt; full distillation priority granted—auto-yields SPLIT's 4 single-H100 jobs; stage datasets/ckpts on node-local `/tmp` ~6 TB free, NEVER `/project/community` at 22 GiB free), Orchard `general` (**1× H100 80GB**, 12h evals), Trinity **`0-13:0,2`** (unwrapped 49GB Ada) + **`2-28:4-7`** (4× 49GB Ada under `vnice.sh`, 1.8 TB `/scratch`), and **Unlimited Gemini API** (`neon`/`carbon`/`argon`/`flash`). Connect to Orchard via `ossh.sh` (`ControlMaster`).

| Rung & Window | Hardware & Budget | Concrete Execution Spec | Pre-Registered Pass Bar | Hard Kill / Stop Trigger |
|---|---|---|---|---|
| **Rung 0 (H 0–6): Build, Cache & Head Gate** | Trinity `2-28:4-7` (`vnice`) + `0-13:0,2` (~12 GPU-h) + Orchard `general` (2h) + Gemini API | **(A)** Extend `rlkit-v1` (80 CPU tests PASS) with `GeoAPI-v2` executor, parallax-gated `R_tri`, `R_calib`, & `×1.37`/chiral hooks; pre-cache `R0-rl` (**272 zero-leak rooms**, ~12K prompts) head tensors & 3D scene-graph rewards; run 20-step admission smoke on 1× H100. **(B)** Run `J1-T` box-tolerance (`10m`) + `Candidate 3` box-head fail-fast (`≤4` A6000-h) + `DA3 Nested` vs `G3T` parity on `38` `dev-S1` GT captures (`K5-S` ARKit check). **(C)** Generate 30K OOF real-residual recovery traces via `Neon+Carbon+Flash` on clean train rooms (`0` overlap w/ `R0-rl`/`dev-S1`/`R0-dev`). | `rlkit-v1` v2 CPU+20-step smoke PASS (`<2 ms`/reward, `0` room leak, `100%` counterfactual tests); `DA3` cuts ARKit gross fails `21/23 → ≤4/23` (or keep `G3T` + `pose_cond_deg` gate); `scale_donor` parity `≤0.5%`. | Any room overlap with `BENCH v2`/`dev-S1`/`R0-dev`; reward latency `>10 ms`; `scale_donor` drift `>0.5%`. |
| **Rung 1 (H 6–24): `GeoAPI-v2` + OOF Recovery SFT** | Orchard `advanced` 4× H100 (~45 H100-h, ~12h wall) | Init **`R1 step 400` (`5083243c`)** (or `Vehicle N` m200 if already landed). `200` steps full-FT (`lm: full`, LR `6e-6`, `scale_donor` frozen `V2`, `288` rows/step) merging `Vehicle N` wording/unit/away-twin fixes + `GeoAPI-v2` (`ego_polar`, built-in `unit` in `measure`, `cam@k`) + 30K OOF real-residual recovery traces + full neighbor coverage (`rel_size`, `rel_count`, `"1+1=2"`). Eval on `dev-S1` + `R0-dev` + `H900` + `D580` (Orchard `general`, 1× H100). | `H900` cam calls `66.4% → ≥95%`; `D580` dist calls `44.5% → ≥92%`; `0%` cap loops (`≤0.5%`); `scale_ratio 1.000±0.005`; `R0-dev` direct-8 `≥+1.5` vs step 400 (`+6.6` vs `544`); VSTI cam-obj `≥+15` pts; `0` hijack on `rel_count`/`rel_size`. | `H900`/`D580` calls `<90%`; any `H3` scale drift (`-0.7` disp); `rel_count`/`rel_size` regression `>2` pts. |
| **Rung 2 (H 24–48): Parallax-Gated Geo-RLVR Pilot** | Orchard `advanced` 4× H100 (~60 H100-h, ~15h wall) | **Colocated vLLM sleep/wake + FSDP2 GRPO on all 4× H100** (required because 9B full-FT uses `57–81 GiB/rank` at world 4; fallback: LoRA `r=64` on all projections if rollout KV headroom tight). `R0-rl` (`272` rooms, 12K prompts, anti-prior oversampled), `G=8` (4 tool-forced + 4 free), `16` prompts/step (`128` rollouts/step), `250` GRPO steps, `β_KL=0.02`, `ε=0.2`, `T_max=3`, `25%` counterfactual faithfulness (`×1.37` / bearing flip / slot swap), `scale_donor` frozen. Checkpoint every 50 steps to `/tmp` → `gs://cmu-gpucloud-jjyeung/q8/`. | Paired 95% room-cluster CI vs Rung 1: `dev-S1` routed dist **`≥+4.0`** MRA; recovery win rate **`≥55%`** on initial `UNSEEN`/`MULTI_SLOT` items (closing `≥35%` of `W1` gap); `R0-dev` overall **`≥+3.0`** (`≥64.0`); anti-prior slices (`count≥5`, `<30 cm`, `away`) **`≥+5.0`**; `×1.37`/chiral faithfulness **`≥90%`**; `OK`-item think tokens **`-25%`**. | Direct-guess collapse (routed call rate drops `>5%`); `×1.37` faithfulness `<85%`; `R0-dev` gain `<+1.5` at step 150. |
| **Rung 3 (H 48–72): EM Head M-Step + Round-2 RL + 1 Official Read** | Trinity `2-28`+`0-13` (12 A6000-h) + Orchard `advanced` (28 H100-h) + `general` (12 H100-h) | **(1) M-Step (H 48–56, Trinity):** Retrain `Candidate 3` box+presence head (or `Candidate 2` SAM 3 LoRA) with `3×` weight on Rung-2 RL-mined `UNSEEN`/wrong-slot frames; promote `DA3 Nested` if Rung 0 passed; pass `≤0.5%` scale-parity gate. **(2) GRPO Round 2 (H 56–64, Orchard `advanced`):** `150` GRPO steps against upgraded heads. **(3) Single Official Read (H 64–72, Orchard `general`, `EAT-1` sealed reader):** Full **ReVSI-999 (all 7 cats)**, **VSI-Bench Full (5,130, 8 tasks)**, **VSTI-450 v3 (5-task + 9-type)** + export `full_weights` for VLA `Test L` & `Test N`. | **ReVSI-999 (7 cats, 32f): `≥67.0`** (beats `GeoWeaver-10B 57.5` by `+9.5`, `CROSS-32B 60.2` by `+6.8`); **VSI-Bench (5,130, 8 tasks, 32f): `≥74.5`** (stretch `≥76.7` vs `ConsiSpace`/`Argon`); **VSTI-450 primary `≥80.0`** (beats `Argon 73.73` by `+6+`), **9-type `≥80.0`**. | ReVSI `<64.0` or VSI `<72.0` -> halt Round 3 and diagnose grounding vs pose split from Rung-3 traces before scaling to 64f / full `RL-200K`. |

---

## 5. Key Risks & Pre-Registered Mitigations
1. **9B Full-FT + Online Rollout Memory Ceiling (`57–81 GiB/rank`):** Never split 2 GPUs learner + 2 GPUs vLLM (OOMs 9B full-FT). Use colocated vLLM sleep/wake across all 4× H100 (or `LoRA r=64` on all Qwen linear layers + merged checkpoint export for `GeoAPI-v2` parity if sleep/wake fragmentation exceeds `74 GiB`).
2. **Orchard `/project/community` Exhaustion (`22 GiB` free):** Keep all `R0-rl` caches, vLLM weights, and step checkpoints strictly on node-local `/tmp` (`~6 TB` free) and stream milestone exports directly to `gs://cmu-gpucloud-jjyeung/q8/`.
3. **Reward Hacking via Silent Scale or Format Drift:** Keep `scale_donor` (`V2`) optimizer-excluded in every LM SFT/GRPO step; enforce `×1.37`/chiral perturbations on `25%` of RL batches and run `0`-overlap room assertions before every launch.
4. **VLA Downstream Compatibility:** Because `GeoAPI-v2`'s `raycast(mode="floor_waypoint"|"subgoal_se3")` and `ego_polar` share the exact gravity-leveled metric frame used by `vla_where` (`U1`) and `navrun` (`NU`), every RL-refined representation transfers directly into `Test L` (LIBERO-Spatial `+Cam`) and `Test N` (R2R-CE) without an external harness.
