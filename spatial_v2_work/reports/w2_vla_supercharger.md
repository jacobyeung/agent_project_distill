# Wave-2 Blueprint: VLA-Supercharged 9B Spatial Foundation Model & Week-1 GPU Campaign (`w2_vla_supercharger`)

## Executive Thesis
Naive spatial-VQA SFT fails to improve downstream Vision-Language-Action (VLA) policies (`28/200` vs `29/200` in our Oct LIBERO pilot; InternVLA-M1 `98.0` vs `98.8`) because metric 3D geometry stays trapped in slow text CoT or discarded readout heads while LM visual patch states remain 2D-blind, pixel grounding erodes (`75.9% → 24.7%`), and policies overfit third-person pixels ($\pi_0$ collapses `94.2% → 15.8%` on `LIBERO-Plus +Cam`). Turning our 9B spatial VLM into the **#1 foundation backbone across manipulation (`LIBERO`, `LIBERO-Plus`, `RoboCasa`, `OXE/DROID`) and navigation (`R2R-CE`, `R2RIE-CE`, `RxR-CE`)** executes two coupled tracks:
1. **Immediate Week-1 Yardstick (Starting Today on Orchard Priority + Trinity):** Run a 6-hour single-GPU gate wave (`~16 GPU-h`), then launch CPU-sealed **Test L** (`B0` vs `B1` vs `U1` on 5-demo `LIBERO-Spatial` + `LIBERO-Plus +Cam`) and **Test N** (`N0` vs `N1` vs `NU` on 10% `R2R-CE` + `R2RIE-CE`) across Orchard `advanced` + `preempt` H100s—proving explicit metric 3D routing (`U1 > B1`, `NU > N1`) and locking the paired benchmark every clean-sheet model must beat.
2. **Blue-Sky VLA-Supercharged 9B Backbone:** Reshape `Qwen3.5-9B`'s hybrid DeltaNet/Full-Attention trunk so canonical metric 3D pointmaps, 4D residual flow, and oriented 3D object slots live **natively at hidden-state `taps 16, 24, -1`**, driving a **30+ Hz System-1 `FlowExpert`** in the exact canonical metric $SE(3)$ frame predicted by own depth+pose heads while **1 Hz System-2** plans persistent 3D subgoals with zero spatial forgetting.

---

## 1. Why Spatial VLMs Fail on VLAs (Measured Root Causes & Proven Dead Ends)

| Structural Flaw | Measured Empirical Evidence | Architectural Cure |
|---|---|---|
| **1. 2D-blind hidden states when heads drop** | Qwen3.5's SigLIP-lineage ViT (`temporal_patch=2`) destroys ray phase (`71°–93°` pose probes even at 2× px or `G=8`). `step-544` puts pose only on `32` `CAM` tokens; `B1` (`1d6eeb28`) drops heads, leaving `taps 16, -1` uncalibrated. | Multi-teacher correspondence absorption (`Spatial-Forcing²`) + mid-trunk `GeoLoop` **Metric 3D-RoPE** into `taps 16, 24, -1`. |
| **2. Grounding erosion & missing 3D `OBB` extents** | Prose VQA SFT cut `f17` pointing `75.9% → 24.7%`; action-only FT wipes RefCOCO in `20k` steps. `Rank 1`+`J1` prove masks/boxes bind (`+13.8` GT masks; `J1` GT 2D box → `SAM 3` recovers `+11.0` = `80%`). | Native encoder `Own-Box-3D` slots (`Candidate 3` + 2-frame eroded voxel voting) + **15% online grounding/depth replay**. |
| **3. Third-person pixel lock & metric scale drift** | Camera shifts crash $\pi_0$ (`94.2 → 15.8%`) and OpenVLA-OFT (`95.3 → 59.7%`). Monocular depth drifts out-of-domain (`V-C` reads `1.94×` on Habitat; raw `G3T` translation is `0.46×`). | Bayesian FK hand-eye scale lock + online `wrist ↔ exo` $SE(3)$ cancellation (`U1` → `U1-Native`); gravity floor-click lift (`NU`). |
| **4. Rigid-world bias & zero pre-motor dynamics** | Moving arms/hands break static BA (`Any4D` `-41.6` VSTI pts; static `G3T` `-8` DSI pts vs `Point4D`). Room scans (`1.5–10 m`) omit `1–50 cm` gripper-object contacts. | Rigidity-masked 4D flow $p^{\text{stat}}$ + pre-training on `10,000+ h` human $SE(3)$ pinch trajectories, screws, and floor clicks. |
| **5. CoT/tower latency vs 30 Hz closed-loop control** | `500–2,000` CoT tokens or external `FrozenG3TTower` (`18–25 s`) stall control and hit token caps (`CP1` route `8/20` caps; `E0` `10/25` caps). | `<120 ms` `U1-Native` + **30+ Hz System-1** `FlowExpert` (`<25 ms`) + async **1 Hz System-2** metric subgoal planner. |

**Hard Guardrails from Verified NO-GOs (`w1_heads_bottlenecks` §4A):** Do NOT repeat pose heads on frozen SigLIP/Qwen ViT tokens (`chance`), loss-only `CAM` alignment (`C1-r`, plateaus at `49%` centre error), early vision-only LM branches (`IF-P0`, stalls at `15.5°`), scalar `tanh` input gates (lock `<0.04`), unprompted text `SAM 3` (`presence < 0.05` vetoes `92%` of empty visible frames), naive multi-frame cloud union (`-40.9` pts), or learned scalar scale-regression heads (`-9.3` disp pts).

---

## 2. Five Architectural Fixes That Flip Spatial Pre-Training to a Landslide VLA Win

### 2.1 Fix 1 — Metric 3D Action-Space Alignment (`GeoLoop-Qwen3.5` + `Spatial-Forcing²` + `Own-Box-3D`)
`Qwen3.5-9B` (`32` layers, `d=4096`) interleaves **8 full-attention layers (`4, 8, 12, 16, 20, 24, 28, 32`)** with **24 Gated DeltaNet recurrent layers**, ruling out $\pi_0$-style per-layer KV sharing and requiring geometry hooks specifically aligned to its full-attention vs DeltaNet split. Both perception and action operate in **one canonical Z-up metric frame $\mathcal{B}$** (robot base for manipulation; gravity-leveled start/odometry frame for navigation):
- **Front-End Correspondence Absorption (`Spatial-Forcing²` + Streaming State $\mathbf{S}_t$):**
  - Unfreeze the ViT + a streaming 3D state bank $\mathbf{S}_t \in \mathbb{R}^{1024 \times d}$ (`~8 ms/frame`, `Causal-3D-SLAM`) and pre-train layers `1..12` on unlabeled `DROID`, `OXE`, `Ego4D`, and `ScanNet++` clips against `DA3-Nested Giant` (`1.78°` rot, native metric) + `Point4D` + `CoTracker3`.
  - Supervise via patch cosine loss, **cross-frame Gram correspondence loss** $\mathcal{L}_{\text{gram}} = \|\tilde{\mathbf{H}}\tilde{\mathbf{H}}^\top - \tilde{\mathbf{H}}_{\text{tea}}\tilde{\mathbf{H}}_{\text{tea}}^\top\|_F^2$, and a training-only 4D Gaussian splatting head $\mathcal{L}_{\text{splat}}$ (dropped at inference). During transition from frozen towers, inject `GF-1` multi-layer `DA3/G3T` features via per-channel linear maps (`GXC` halved pose error in 200 steps).
- **Closed-Loop Mid-Trunk Geometry at Full-Attention Layer `L_geo = 12`:**
  - Enable prefix-bidirectional cross-frame visual attention at full-attention blocks **`4, 8, 12`** (keeping text strictly causal).
  - At layer `12`, focal-normalized heads $(\log(|f_x|/W), \log(f_y/H), \text{sign}(f_x))$ (handling MuJoCo left-right raster mirror `fx < 0, diag(-1,1,1)` natively inside $K_t$) predict metric depth $(\hat{D}_t, \hat{\sigma}_{D,t})$, canonical pose $\hat{\mathbf{T}}_{\mathcal{B}\leftarrow t} = (\hat{R}_t, \hat{\mathbf{t}}_t) \in SE(3)$, patch rigidity $p^{\text{stat}}_{t,u,v} \in [0,1]$, and 4D flow $\Delta\mathbf{P}^{\mathcal{B}}$. Unproject every patch into $\mathcal{B}$:
    $$\mathbf{P}^{\mathcal{B}}_{t,u,v} = \hat{R}_t \hat{K}_t^{-1}[u,v,1]^\top \hat{D}_t(u,v) + \hat{\mathbf{t}}_t \in \mathbb{R}^3, \qquad \mathbf{r}^{\mathcal{B}}_{t,u,v} = (\mathbf{d}_t, \hat{\mathbf{t}}_t \times \mathbf{d}_t) \in \mathbb{R}^6.$$
- **Upper-Trunk Metric 3D-RoPE (`L16, 20, 24, 28, 32`) + Native `Own-Box-3D` Object Slots:**
  - Swap 2D M-RoPE on visual tokens at full-attention blocks **`16, 20, 24, 28, 32`** for **Metric 3D-RoPE** over $(P_x^{\mathcal{B}}, P_y^{\mathcal{B}}, P_z^{\mathcal{B}}, t)$ ($\omega_m \in [0.05, 50]\text{ rad/m}$), while injecting Fourier-encoded $[\mathbf{P}^{\mathcal{B}}, \mathbf{r}^{\mathcal{B}}, \log\hat{D}, \hat{\sigma}]$ via zero-init linear adapters into DeltaNet blocks `13..31` (annealing coordinate gradient $\alpha: 0 \to 0.25$).
  - Supervise dense 3D pointmap + flow alignment directly on **`taps 16, 24, -1`** (all full-attention outputs!).
  - Emit $N_{\text{slot}} = 32$ **Native 3D Object Slots** $\mathcal{O}_m = (\boldsymbol{\mu}_m^{\mathcal{B}}, \mathbf{e}_m^{\text{OBB}}, \psi_m, \mathbf{f}_m^{\text{id}})$ via an encoder 2D box+presence head (`Candidate 3` trained at `1,000+`-scene scale, bypassing `SAM 3`'s `presence < 0.05` veto) + 1-px eroded, Tukey 1.5-IQR multi-view voxel voting (`vote_10_3_best`, `+5.65` K1 pts).
- **3D-Equivariant 30+ Hz `FlowExpert` (`~180M` params) / `QwenOFT`:**
  - Upgrade `FlowExpert` (`Beta(1.5, 1)` flow matching, **4 Euler steps = `<25 ms`**) to cross-attend directly to **`taps 16, 24, -1`**, native 3D slots $\mathcal{O}_{1..32}$, proprioception $\mathbf{q}_t$, and head-side `Linear(36→1024)` `reach_base = x_target_base - x_eef_base`.
  - Apply **identical Metric 3D-RoPE** to noisy end-effector chunks $\mathbf{T}^{\mathcal{B}}_{\text{ee}}(t:t+H) \in SE(3)^H \times [0,1]^H$ so motor generation shares the exact $SE(3)$ Lie-algebra frame supervised by the camera pose head.

### 2.2 Fix 2 — Camera-Shift Immunity by Construction (`LIBERO-Plus +Cam` `>88%`, `U1` → `<120 ms` `U1-Native`)
Standard VLAs collapse on `LIBERO-Plus +Cam` because rotating `agentview` shifts 2D patch coordinates while action axes stay fixed in $\mathcal{B}$. We make third-person camera extrinsics a **canceled internal gauge variable**:
- **Bayesian Kinematic Hand-Eye Scale & Extrinsics Lock (Zero $t=0$ Singularity):**
  - Wrist camera pose in $\mathcal{B}$ is known exactly from forward kinematics: $\mathbf{T}_{\mathcal{B}\leftarrow\text{wrist}}(\mathbf{q}_t) = \mathbf{T}_{\mathcal{B}\leftarrow\text{ee}}(\mathbf{q}_t)\mathbf{T}_{\text{ee}\leftarrow\text{wrist}}$ (`6e-8 m` fit residual).
  - Across rolling 5-view window $\mathcal{W}_t = \{\text{wrist}_t, \text{agent}_t, \text{wrist}_{t-8,t-16,t-32}\}$, fuse the $t=0$ `OwnDepthScale` / gripper-jaw prior $s_{\text{own}}$ (`own/GT = 1.016`, weight $\lambda_0$) with FK wrist translations (preventing $0/0$ degeneracy when stationary at $t=0$, then locking to $|s^*/s_{\text{GT}} - 1| \le 2.4\times 10^{-7}$ once cumulative wrist travel exceeds `1.5 cm`):
    $$s^* = \frac{\lambda_0 s_{\text{own}} + \sum_{\tau \in \{8,16,32\}} \Delta\tilde{\mathbf{t}}_{\tau}^\top \Delta\mathbf{t}^{\text{FK}}_{\tau}}{\lambda_0 + \sum_{\tau \in \{8,16,32\}} \|\Delta\tilde{\mathbf{t}}_{\tau}\|_2^2}, \qquad \hat{\mathbf{T}}_{\mathcal{B}\leftarrow\text{agent}}(t) = \mathbf{T}_{\mathcal{B}\leftarrow\text{wrist}}(\mathbf{q}_t) \cdot \hat{\mathbf{T}}_{\text{wrist}_t \leftarrow \text{agent}_t}(s^*).$$
- **Exact Perturbation Cancellation + 3-Step `TT-BA` (`<10 ms`):**
  - Polish $\hat{\mathbf{T}}_{\text{wrist}_t \leftarrow \text{agent}_t}$ online with 3 Levenberg-Marquardt Gauss-Newton steps minimizing static-masked ($p^{\text{stat}}$) feature/depth reprojection error (committed only if residual drops `>10%`).
  - Any arbitrary camera shift $\mathbf{T}_{\text{shift}} \in SE(3)$ cancels identically: $\mathbf{P}^{\mathcal{B}}_{\text{agent}} = (\hat{\mathbf{T}}_{\mathcal{B}\leftarrow\text{agent}}\mathbf{T}_{\text{shift}})(\mathbf{T}_{\text{shift}}^{-1}\mathbf{P}^{\text{cam}}_{\text{agent}}) = \mathbf{P}^{\mathcal{B}}$.
  - Pair with `25%` training dropout of `agentview` 2D appearance features, focal-crop parallax warps (`Engine 4`), and occlusion-exempt cross-view mask lifting (`r = 0.05`, rescuing `30/30` bowl-occluded plate lifts).
- **Two-Stage Serving Path (`U1` → `U1-Native` & `NU`):**
  - **Week-1 (`U1`, CPU-sealed):** `ViewSetG3T` + `Sam3Tower` + student V1 presence/pointing emits `[2, 18]` fp32 `where` (`X_wrist`, `reach_base`, OBB extents) every 8-step chunk (`~0.4 s` amortized).
  - **Wave-2 (`U1-Native`, `<120 ms` single-checkpoint):** Replace external `ViewSetG3T + Sam3Tower` with our `Spatial-Forcing²` + `Ego-Exo` wide-baseline SE(3) heads (`<2.5°` rot) + `Own-Box-3D`, running perception + `FlowExpert` in **one `<120 ms` forward pass**.
  - **Navigation Scale Immunity (`NU`):** Clicking `<goal frame=32 x=u y=v>` and lifting via gravity-leveled `floor_plane` ($Z_{\text{cam}} = 1.25\text{ m}$) + `DA3/G3T` slope/obstacle check bypasses `1.94×` Habitat depth-scale drift (`88.7% SR` GT-click ceiling).

### 2.3 Fix 3 — Unified Action = Future 4D Flow, Human $SE(3)$ Pinch & Floor-Click Pre-Training
Eliminate cold-start motor learning by pre-training the exact downstream action heads on millions of metric 4D video clips (`Engines 2, 6`, annotated by unlimited Gemini `Carbon`/`Neon`):
1. **Rigidity-Decoupled 4D Scene Flow ($\Delta\mathbf{P}^{\mathcal{B}}_{t\to t+H}$):** On `DROID` (stereo), `Ego-Exo4D` (Aria SLAM), `OXE` (FK link-calibrated; uncalibrated monocular clips masked via `metric_scale_locked=0` so radial distortion never corrupts global scale), and `PointOdyssey`, supervise $\mathbf{P}^{\text{cam}}_{t+\delta} = \mathbf{T}_{t+\delta}(\mathbf{P}^{\mathcal{B}}_t + (1 - p^{\text{stat}})\Delta\mathbf{P}^{\mathcal{B}}_{t\to t+\delta})$ with an $\ell_1$ sparsity prior on $(1-p^{\text{stat}})\|\Delta\mathbf{P}^{\mathcal{B}}\|$.
2. **10,000-Hour Human-to-Robot $SE(3)$ Pinch & Articulation Bridge (`Engine 6`):** Subtract camera ego-motion $\hat{\mathbf{T}}_{\mathcal{W}\leftarrow\text{cam}}(t)$ from `HaMeR/WiLoR` 3D hand meshes (`8.4 cm` hand-breadth + SLAM scale) across `Ego-Exo4D`, `HD-EPIC`, and `Epic-Kitchens`. Retarget thumb-index pinch midpoint $\mathbf{p}_{\text{pinch}}$, approach $\mathbf{a}$, closing axis $\mathbf{b}$, and aperture $g(t) \in [0,1]$ into `SE(3)^H × [0,1]^H` chunks (conditioned on Carbon-tagged `embodiment_mode ∈ {parallel_jaw, dexterous, suction}`), plus post-contact Plücker screw axes $(\hat{\omega}, \mathbf{q}, \theta)$ for doors/drawers. Pre-train `FlowExpert` (`embodiment_tag = human_pinch`) + a **3D Contact Affordance Point Head** before seeing 1 robot demo.
3. **Zero-Demo Floor-Waypoint & Egocentric Polar Pre-Training:** Project collision-free future camera positions (`1.0–3.0 m` ahead on `ScanNet++`, `MP3D-train`, `ARKit`) onto current frames as `<goal frame=t x=u y=v>` floor clicks paired with `(range_m, bearing_deg)` (`SPLIT L12`). Downstream `5`-demo LIBERO and `1%` R2R-CE simply adapt a thin embodiment offset $\mathbf{T}_{\text{robot}\leftarrow\text{pinch}}$!

### 2.4 Fix 4 — Knowledge-Insulated VLA Fine-Tuning (`F1-Insulated`: Zero Spatial Forgetting)
Full-backbone action gradients wipe out VLM grounding in `20k` steps and drifted `OwnDepthScale` `+1.38%` in `400` `R1` steps. Every VLA fine-tuning run enforces **4-layer knowledge insulation**:
1. **Stop-Gradient Continuous Motor Head (`detach_backbone: true` on `FlowExpert`):** Continuous flow-matching / L1 motor noise never backpropagates raw high-frequency gradients into the 9B backbone (`F1`).
2. **`FAST` Discrete Auxiliary Loss + Upper-Trunk LoRA + Frozen Scale Donor:** Co-train discrete `FAST` action tokens (`247019..248043`, weight `0.2`) through rank-32 LoRA (`LR 2e-5` = `0.1×` action-head LR `2e-4`) restricted to upper layers `L13..32`, keeping mid-trunk `L1..12` and `OwnDepthScale` (`scale_donor` + `G3T` intrinsics) **optimizer-frozen (`0.000%` scale drift)**.
3. **15% Online Multi-Task Geometric & Grounding Replay:** Every VLA batch mixes **85% robot action chunks** + **15% spatial replay** (`5%` metric depth + `S2` pose + `Spatial-Forcing²` Gram loss, `5%` 2D/3D box & mask-pointing, `5%` head-backed VSI/ReVSI/Ego-Exo CoT).
4. **Hard Retention Gate:** Require `< 0.5 pt` VSI/ReVSI dev drop, `0.000%` scale-donor drift, and `>= 98%` 2D/3D grounding retention at `10k` steps.

### 2.5 Fix 5 — Asynchronous Dual-System Control (System-2 1 Hz Planner + System-1 30 Hz Controller)
Long-horizon tasks (*"go behind the kitchen island, open the second drawer, pick the mug behind the bowl"*) require multi-room memory without stalling 30 Hz control:
- **System-2 (1–2 Hz Asynchronous 9B Spatial Planner, `L13..32` + Loop-Closed Memory $\mathcal{M}_t$):**
  - Maintains persistent $SE(3)$ object-slot / voxel memory $\mathcal{M}_t$ (`VQ3D` `0.43 m` L2, `HiP3R+SALAD` yaw-continuity submap stitching across rooms/blackouts).
  - Runs differentiable 3D ops (`<q_locate>`, `<q_raycast>`, `<mental_cam>` virtual pre-grasp splat check, and VoI-gated active `<move_cam>` emitted *only* while target $\sigma_{\mathbf{p}} > 2.0\text{ cm}$ or visibility `< 40%`), writing a **world-anchored metric subgoal** into a lock-free buffer:
    $$\mathbf{g}^{\mathcal{W}}_{\text{plan}} = \big(\texttt{mode} \in \{\text{nav},\text{reach},\text{articulate},\text{peek}\},\; \mathbf{T}^{\mathcal{W}}_{\text{goal}} \in SE(3),\; \texttt{target\_slot\_id},\; \mathcal{B}^{\text{OBB}}_{\text{avoid}},\; \hat{\mathbf{s}}_{\text{screw}},\; \sigma_{\text{goal}}\big).$$
- **System-1 (30+ Hz Reactive Metric Controller, `<25 ms`/chunk):**
  - Re-projects $\mathbf{g}^{\mathcal{W}}_{\text{plan}} \mapsto \mathbf{g}^{\mathcal{B}_t}_{\text{plan}} = \mathbf{T}_{\mathcal{B}_t\leftarrow\mathcal{W}}(t)\,\mathbf{g}^{\mathcal{W}}_{\text{plan}}$ at **30 Hz** via live FK/odometry so subgoals never lag behind robot motion during System-2's `0.5–1.0 s` reasoning tick.
  - Executes only the fast 3D trunk (`ViT + S_t + L1..12`, `~1.5B` active) + 4-step Euler `FlowExpert`, trained with `0.2–1.5 s` random subgoal staleness and contact/slip perturbations for instant local recovery until `<subgoal_reached>` (`\|\mathbf{x}_{\text{ee}} - \mathbf{x}_{\text{goal}}\| < 1.5\text{ cm}`).

```
RGB (Wrist + Exo / 32..512f) + Proprio q_t
  └─► [Streaming 3D Trunk S_t + L1..12 (Spatial-Forcing²)] ─► Depth + SE(3) Pose + p_stat 4D Flow + Own-Box-3D Slots
        └─► [Bayesian FK Scale s* + 3-Step TT-BA (<10 ms)] ─► Canonical Frame B Pointmap P^B + Metric 3D-RoPE
              ├─► SYS-1 (30+ Hz, <25 ms, detached): FlowExpert x-attends [Taps 16,24,-1 + Slots + reach_base + g_plan^B_t]
              └─► SYS-2 (1–2 Hz, LoRA+FAST+15% Replay): L13..32 + 3D Memory M_t + <q_locate>/<mental_cam> ─► updates g_plan^W
```

### 2.6 Per-Domain Embodiment Binding Across One Shared 9B Checkpoint
| Downstream Suite | `--embodiment-tag` & Action Head | Active 3D / Memory Interface |
|---|---|---|
| **`LIBERO-Spatial` & `LIBERO-Plus +Cam`** | `franka_libero` (`7-D` delta EE + gripper; `QwenOFT` Wk1 → `FlowExpert` Wk2) | `U1` → `U1-Native` (`wrist + exo` FK scale $s^*$ + `TT-BA` + `reach_base`). |
| **`RoboCasa` (Mobile Kitchens)** | `panda_mobile_12d` (`7-D` arm + `5-D` base/torso `FlowExpert`) | Sys-2 causal submap memory $\mathcal{M}_t$ + Plücker screw $\hat{\mathbf{s}}_{\text{screw}}$ + Sys-1 `FlowExpert`. |
| **`OXE / DROID` (Multi-Robot Real)** | Per-robot normaliser + `SE(3)` EE `FlowExpert` (`human_pinch` init) | Stereo/FK `metric_scale_locked` + `Own-Box-3D` slots + VoI `<move_cam>`. |
| **`R2R-CE`, `R2RIE-CE`, `RxR-CE`** | `habitat_vln` (`controller_v2` `0.25 m / 15°` over `NU` clicks → continuous `SE(2)`) | `NU` gravity `floor_plane` `<goal>` click + 32–256f loop-closed pose/submap $\mathcal{M}_t$. |

---

## 3. Immediate Week-1 GPU Execution Plan (Orchard Priority + Trinity)

### 3.1 Cluster Guardrails & Zero-Contention Co-Scheduling (`2026-11-28`)
- **Orchard (`5` non-preempt H100s = `4` `advanced` + `1` `general`, plus up to `32` `preempt` H100s):**
  - Distillation holds full Orchard priority (`04:12 AM PT` ruling; SPLIT's 4 1-GPU jobs `176609, 176637, 176638, 176641` auto-yield on submission or are pre-authorized for `scancel` with a stop notice in `/data3/jjyeung/orch_n13_20261026/STOP_NOTICES.md`).
  - Always connect via `timeout 60 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh '<cmd>'`.
  - **Disk Guardrail (`/project/community` has only `~22 GiB` free; `$HOME` `25 GB`):** Export `HF_HOME`, `TORCH_HOME`, `TRITON_CACHE_DIR`, `PIP_CACHE_DIR`, and `XDG_CACHE_HOME` to `/tmp/jjyeung_cache`, unpack `vla_libero` (`e6bccd3d`) and `navrun` (`6.2 GB` PNGs) onto **node-local `/tmp` (`6.0 TB` free)**, and stream checkpoints/evals to `gs://cmu-gpucloud-jjyeung` (`CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud`).
  - **Parallelism with Vehicle N:** Both `vla_libero` and `navrun` pass bitwise `HOOK_RESUME_EXACT` (2-min `preempt` grace saves state cleanly to `/tmp`+GCS), letting Test L and Test N run **in parallel across `preempt_qos` (`16–24× H100`)** while `advanced` (`4× H100`) runs either Test L immediately or Vehicle N (`job 174444`, `~10.4 wall-h`) once cleared.
- **Trinity (`0-13:0,2` unwrapped + `+6` in ~45m; `2-28:4,5,6,7` wrapped in `/data3/shared/scripts/vnice/vnice.sh`):**
  - `0-13:/scratch` has only `69 GB` free (`96%` used): run compute on `0-13` streaming outputs over `.ib` (`172.16.1.x`, exempt from `30 MB/s` NFS cap) directly to `2-28:/scratch` (`1.8 TB` free, `/dev/shm` `463 GB` free).
  - Before **Nov 29** (7-day cleaner cutoff), archive `1-18:/scratch/jjyeung/orch_n30/b15_vla/` tars to `/data3` via `io_governor` (`rsync --bwlimit=4000`). Launch while Gemini `neon`/`carbon` + Astra cross-checks run in parallel (`CLAUDE.md` launch-first rule).

### 3.2 Day-by-Day Launch Sequence & GPU-Hour Budget

| Window | Hardware Allocation | Exact Job, Kit & Attribution Protocol | Budget | Pass Gate / Immediate Next Trigger |
|---|---|---|---:|---|
| **Day 1 (`H0–H6`)** | `trinity-0-13` (`0,2` unwrapped → `.ib` → `2-28`) | **`vla_where` Pre-Check & `d5_s0` Cache:** Run `T-11` (`P-5` bf16 parity), `P-1..P-4` LIBERO replays (`fx<0` mirror `>=19/20` in-mask, FK scale `|s/s_GT-1|<=1e-4`, `30/30` occluded plate rescue), and generate `d5_s0` (`6,281`f, `50` demos) `U1` `[2,18]` `where` cache. | `4` Ada-h | **PASS `T-11` & `P-1..P-4`**; push `d5_s0` `where` cache (`<50 MB`) to GCS/`/tmp` to unlock `U1` training at `H6`. |
| **Day 1 (`H0–H6`)** | `trinity-2-28` (`4,5` `vnice`) + Orchard `general` (`1×H100`) | **`navrun` Smoke & Patch:** Apply `student_pilot_nav_mode.patch`; run `rand100` closed-loop Habitat `0.2.4` (`controller_v2`, `512×512`, `32f`) + occlusion-tested oracle-click verification. | `5` GPU-h | **0 blocked-leg stalls**; confirm `~88.7%` GT / `~68.3%` geodesic ceiling; unlock Test N at `H6`. |
| **Day 1 (`H0–H6`)** | `trinity-2-28` (`6,7` `vnice`) + `0-13` (`6` once free) | **`dyn_probe` Stage 0 + `Own-Box` `C3`:** Run TUM/Bonn/LIBERO dynamic Stage 0 (`R1/R2`, `<3h`); run `J1-T` (`10m`) + start `Candidate 3` encoder 2D box+presence head on frozen `step-544` ViT (`<=4h` fail-fast). | `7` Ada-h | Lock dynamic ATE/flow baseline; gate `Candidate 3` box recall (`IoU>=0.5`) for `U1-Native`. |
| **Day 1–2 (`H6–H30`)** | Orchard `advanced` (`4×H100`) + `preempt` (`3×4 H100`) | **Decisive Baseline Test L (`vla_libero` `e6bccd3d`):** Train paired `d5_s0` (`5` demos/task, batch `64`, `10k` steps, `QwenOFT`, `4.5 wall-h`/arm): **`B0`** (base `c2022362`), **`B1`** (`step-544` `1d6eeb28` via `bind/train_b1_544.sh`), and **`U1`** (`B1` + `where` `Linear(36→8192)` + text w/ `20%` dropout). *(Add `B1-R1` `5083243c` on 4th `preempt` shard if free.)* | `54` H100-h train + `12` H100-h eval | Closed-loop OSMesa on **`500` paired Spatial + `376` `+Cam` eps** + **Holm 5-check attribution** (`gt_where`, `shuffled_where`, `withheld_where`, `uncalibrated_scale`, `wrist_only`). |
| **Day 1–2 (`H8–H36`)** | Orchard `preempt` (`3×4 H100`) + `general` (`1×H100`) | **Decisive Baseline Test N (`navrun` `10%` R2R-CE):** Train paired `1,082`-ep (`63,302`f, `1,000` steps, `6.75 wall-h`/arm): **`N0`** (base `nav_text`), **`N1`** (`step-544` `nav_text`), and **`NU`** (`step-544` `<goal>` floor-click + `floor_plane` lift + 32f pose history). | `81` H100-h train + `10` H100-h eval | Paired Habitat eval on **`val_unseen_600_s0`** (`SR`, `SPL`, `NE`, `OSR`) + **`r2rie_direction_300`** + attribution (`gt_click`, `raw_depth_vs_floor`, `no_pose`). |
| **Day 3–5 (`H36–H108`)** | Orchard `advanced` + `preempt` (`16–24×H100`) | **Sample-Efficiency Curves + `F1-Insulated`:** On Test L/N GAIN, run **`1`-demo (`d1_s0`) & `2`-demo (`d2_s0`)** LIBERO + **`1%` R2R-CE (`108` eps)** + `RxR-CE` pilot, and launch **`F1-Insulated`** (`FlowExpert` `taps 16,24,-1` + `detach_backbone` + `FAST` + `15%` online spatial replay). | `110` H100-h | Establish 1/2/5-demo & 1%/10% scaling laws; verify `<0.5 pt` `dev-S1` spatial forgetting & `30+ Hz` `FlowExpert`. |
| **Day 4–7 (`H72–H168`)** | Orchard `preempt` (`16×H100`) + `2-28` + Gemini API (`$0` cap) | **3 Blue-Sky Bridge Kill-Tests:** **(K-SF2)** `Spatial-Forcing² + GeoLoop` (`DA3`+`Point4D` Gram + `L_geo=12` 3D-RoPE on `100k` ScanNet++/DROID/Ego-Exo clips → Test L `B2`, `48` H100-h); **(K-U1N)** `<120 ms` `U1-Native` own-head swap (`24` GPU-h); **(K-Pinch)** `100k` Carbon-labeled Ego-Exo/Epic $SE(3)$ pinch + screw pre-train → 1/5-demo LIBERO & 25-demo RoboCasa (`36` H100-h). | `108` GPU-h | Prove tower-free `B2 >> B1` (`>= +10 pp`), `<120 ms` `U1-Native` parity (`<= 2.5 pp` to `U1`), and `+10 pp` 1-demo human-pinch gain. |

---

## 4. Pre-Registered Quantitative Targets & Decisive Kill Gates

*Hypothesis Attribution Note:* Because `step-544` supervised pose only on dropped `CAM` tokens over a frozen SigLIP ViT, we pre-register a small `B1 − B0` (`+2..+5 pp`) alongside a large **`U1 − B1 >= +8.0 pp`** (`>= +25 pp` on `+Cam`) in Week 1—cleanly proving that **metric 3D state drives the VLA win**, then closing the `B1 → U1` gap natively inside the trunk via `B2` (`Spatial-Forcing² + GeoLoop + Own-Box-3D`).

| Benchmark / Metric | Published Bars & Priors | `B0` / `N0` (Vanilla 9B) | Week-1 `B1` / `N1` (`step-544`) | Week-1 `U1` / `NU` (Explicit 3D) | Blue-Sky Supercharged 9B (`SF²+GeoLoop+Pinch+Sys1/2`) | Pre-Registered Promotion / Kill Gate |
|---|---|---:|---:|---:|---:|---|
| **LIBERO-Spatial (`5` demos/task, `500` eps)** | Replay `54.2%`; SF@5% `75.8%`; 50-demo OFT `95.3%`, $\pi_0$ `94.2%` | `~68%` | `~72%` | **`>= 82.0%`** | **`>= 91.5%`** (`>= 98.0%` @ 50-demo) | Promote on `U1 − B1 >= +6.0 pp` ($p<0.01$) & `gt_where > shuffled_where` (Holm 5-check). |
| **LIBERO-Spatial (`1` / `2` demos/task)** | Spatial Forcing @ 1% (`~0.5–1` demo): `42.3%` | `~38% / 53%` | `~42% / 57%` | **`>= 60% / 74%`** | **`>= 76.0% / 86.0%`** | Kill `K-Pinch` if human $SE(3)$ pinch adds `< +10 pp` at 1-demo over non-pinch init. |
| **`LIBERO-Plus +Cam` (`376` camera-shift eps)** | **$\pi_0$ `15.8%`**, **OpenVLA-OFT `59.7%`** (50-demo!); Replay `44.1%` | `~46%` | `~49%` | **`>= 78.0%`** | **`>= 89.0%`** (`<= 3 pp` shift drop) | Beats 50-demo $\pi_0$ by **`+62–73 pp`** using 5 demos; kill `U1-Native` if `> 2.5 pp` below `U1`. |
| **RoboCasa / DROID (`25`-demo manipulation)** | OpenVLA / $\pi_0$ 25-demo kitchen/tabletop `~42–55%` | `~40%` | `~44%` | `>= 58%` | **`>= 72.0%`** (w/ `M_t` + Screw) | Kill `GeoLoop` (`K-SF2`) if novel-viewpoint/placement gain `< +15%` over `B0`. |
| **R2R-CE `val-unseen` @ `10%` (`SR` / `SPL`)** | Blind `4.7%`; 100%-data JanusVLN `52.8%`, Eff-VLN `64.2%`; Oracle `68.3/88.7%` | `~28% / 0.24` | `~33% / 0.28` | **`>= 46% / 0.41`** | **`>= 58.0% / 0.52`** (`>= 68%` @ 100%) | Promote on `NU − N1 >= +8.0 pp SR`; Blue-Sky @ 10% beats 100%-data JanusVLN! |
| **R2R-CE @ `1%` (`108` eps) & `R2RIE-CE` (`300`)** | Qwen3.5-9B ZS `7.0% SR`; `f17` E0 `37.5%` | `~12% / 48%` | `~16% / 55%` | **`>= 28% / 72%`** | **`>= 42.0% SR` / `>= 84.0%`** | Confirms zero-demo floor-click + 32f pose history transfer; scales next to `RxR-CE`. |
| **Control Rate (`Hz`) & Spatial QA Retention** | External `G3T` `0.05 Hz`; `QwenOFT` `10 Hz` chunk | `10 Hz` (`-18` VSI) | `10 Hz` (`-15` VSI) | `2.5 Hz` (`20 Hz` step) | **`>= 33 Hz` Sys-1 (`<25 ms`) + `1 Hz` Sys-2; `<0.5 pt` VSI drop** | Hard gate: `<120 ms` `U1-Native`, `0.000%` scale-donor drift, `<0.5 pt` VSI/ReVSI loss (`F1-Insulated`). |
