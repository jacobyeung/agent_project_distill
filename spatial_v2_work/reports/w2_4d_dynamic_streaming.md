# Wave-2 Blueprint: 4D Dynamic Motion, Causal Streaming 3D Memory & Calibration-Free Cross-View Registration

**Lane:** `bluesky28/w2_4d_dynamic_streaming` | **Date:** 2026-11-28 | **Target:** Native `Qwen3.5-9B` Spatial-VLA Backbone

## Executive Premise
Our current student is locked inside a **32-frame static monocular room**: `carrier_c1.py:590` requires exactly 32 frames, `FrozenG3TTower` (`tower_read.py:36-57`) demands 32/64/96 monotonic rigid anchors, Qwen3.5's `temporal_patch=2` ViT caps own pose at `12.0°–17.9°` (vs G3T `3.1°–6.3°`), `92.7%` (`1,112/1,200`) of `v7` VSTI queries ask about out-of-view objects, and `20` long `R0-dev` scans (`178–705 s`) hold `6.5` of `22.4` lost ReVSI points. Meanwhile, SPLIT proved that 4D geometry (`Point4D+MapAnything`: `+16–27 pp` on ReSTI/DSI, `98% vs 10%` on reversed VSTI), streaming loop-closed submaps (`HD-EPIC` `87.0` flat at 55 min in `6.12 GB` RAM; `VQ3D` `1.56→0.43 m`), and cross-view registration (`Ego-Exo4D` `+33.5 pp` overall, `+44.6` Suite 2A) collapse the remaining spatial bottlenecks—yet still break on stationary speed jitter (`-35.9`), heading-sign errors (`69%`), cross-submap fragmentation (`40.3` vs `68.1`), and `1.11×–1.52×` scale bias.

This blueprint extends our **metric depth + camera-pose heads** along three composable axes—assuming mid-trunk 3D absorption (`GF-1` / Spatial-Forcing²) removes Qwen ViT pose blindness—so one self-contained streaming backbone serves dynamic 4D QA, hour-long memory, cross-view QA, and 5–30 Hz VLAs.

---

## 1. Minimal 4D Extension to Depth + Pose Heads

### 1.1 Architecture & Minimal Channels
Attach two dense per-patch channels (`~18M` params) to the shared geometry trunk (parallel to `PointDepthHead` and `CameraSupervision` at mid-trunk layer $L_{\text{geo}}$):
1. **Static Rigidity Probability:** $p^{\text{stat}}_t(u,v) = \sigma(z^{\text{stat}}_t(u,v)) \in [0,1]$, partitioning every pixel into rigid world support ($p^{\text{stat}} \to 1$) vs moving foreground ($m^{\text{dyn}} = 1 - p^{\text{stat}}$: humans, robot arms, grasped objects, doors).
2. **Ego-Decoupled World-Frame 3D Point-Flow + Epistemic Variance:** $\Delta \mathbf{P}^{\text{obj}}_{t \to t+\delta}(u,v) \in \mathbb{R}^3$ and log-variance $\log \sigma^2_{\text{flow},t}(u,v)$ across multi-horizon offsets $\delta \in \{-1, +1, +4, +16\}$ (backward/forward kinematics plus 8–16-step robot action horizons).

### 1.2 Exact Decomposition of Camera $SE(3)$ vs Independent Object Motion
Given gravity-aligned camera pose $T_t = (R_t, \mathbf{t}_t) \in SE(3)$, calibrated intrinsics $K_t$, and metric depth $D_t(u,v)$ (co-calibrated via **paired common-valid pixels** with exact $K_t$—eliminating SPLIT's unpaired `1.11×–1.52×` static bias and `1.36×` outdoor `MapAnything` over-scale), each pixel unprojects to canonical world coordinates (`+Z` up, meters):
$$\mathbf{P}^w_t(u,v) = R_t^\top \big(D_t(u,v) K_t^{-1}\tilde{\mathbf{u}} - \mathbf{t}_t\big), \qquad \tilde{\mathbf{u}} = [u,v,1]^\top$$
At time $t+\delta$, the observed 3D point in camera frame $t+\delta$ is the exact composition of rigid camera motion and non-rigid residual object displacement:
$$\hat{\mathbf{P}}^c_{t+\delta}(u,v) = R_{t+\delta}\Big(\mathbf{P}^w_t(u,v) + \big(1 - p^{\text{stat}}_t(u,v)\big)\Delta \mathbf{P}^{\text{obj}}_{t \to t+\delta}(u,v)\Big) + \mathbf{t}_{t+\delta}$$
Subtracting $\mathbf{P}^c_t = R_t \mathbf{P}^w_t + \mathbf{t}_t$ cleanly splits apparent camera-frame 3D motion $\mathbf{v}^{\text{tot}}_{t\to t+\delta} = \mathbf{v}^{\text{ego}} + \mathbf{v}^{\text{indep}}$:
$$\mathbf{v}^{\text{ego}}_{t\to t+\delta} = \big(R_{t+\delta}R_t^\top - I\big)\mathbf{P}^c_t + \big(\mathbf{t}_{t+\delta} - R_{t+\delta}R_t^\top \mathbf{t}_t\big), \qquad \mathbf{v}^{\text{indep}}_{t\to t+\delta} = R_{t+\delta}\big(1 - p^{\text{stat}}_t\big)\Delta \mathbf{P}^{\text{obj}}_{t \to t+\delta}$$

**Static-Masked Differentiable Gauss-Newton ($SE(3)$ Refinement, `<15 ms`):**
Open-loop rigid solvers fail when foreground moves (`VGGT` Sintel ATE `0.167` vs $\pi^3$ `0.074`), while unanchored 4D solvers collapse on static scale (`Any4D` `-41.6` pts on static VSTI). We refine relative poses $\boldsymbol{\xi}_t \in \mathfrak{se}(3)$ and per-frame affine depth corrections $(a_t, b_t)$ via 3–5 unrolled Levenberg-Marquardt steps weighted strictly by static confidence $w_t(u,v) = p^{\text{stat}}_t(u,v)\exp(-\sigma^2_{D,t})$:
$$\min_{\{\boldsymbol{\xi}_t, a_t, b_t\}} \sum_{(i,j)\in \mathcal{E}}\sum_{u,v} w_i(u,v)\Big[\rho_\delta\big(\phi_i(u,v) - \phi_j(\pi_{i\to j}(u,v))\big) + \lambda_z \big|\log \tilde{D}_j(\pi_{i\to j}) - \log z_{i\to j}\big|\Big]$$
Moving arms and walking humans receive $w_i \approx 0$ and never drag camera $T_t$. To break close-up scale-flow ambiguity (e.g., wrist cameras where moving objects fill >50% of the frame), we add three identifiability priors:
1. **$\ell_1$ Flow Sparsity:** $\mathcal{L}_{\text{sp}} = \lambda_{\text{sp}}\mathbb{E}\big[(1-p^{\text{stat}})\|\Delta \mathbf{P}^{\text{obj}}\|_1\big]$ forces camera motion to explain global parallax first.
2. **Piecewise-Rigid Object Twist Prior:** Within any 3D voxel/mask cluster $\mathcal{M}_m$, penalize deviation from a single rigid object motion $\Delta \mathbf{P}^{\text{obj}}_t(u) \approx (\exp(\hat{\boldsymbol{\xi}}^{\text{obj}}_m) - I)\mathbf{P}^w_t(u)$ (relaxed via Huber loss for articulated limbs).
3. **Optional Robot Proprioception Prior:** On manipulation platforms, replace or anchor $\Delta T_{\text{wrist}}$ with kinematic forward-kinematics `T_eef_cam` (`6e-8 m` residual in `T-6`), locking metric scale to `<1e-6` error.

### 1.3 Solving SPLIT's Two Exact 4D Failure Modes + Time-Reversal Bias
1. **Eliminating Stationary-Target Speed Inflation (SPLIT Pro `-35.9` / Flash `-18.2` on OSI):**
   Raw frame-to-frame 3D centroid differences integrate depth noise $\sigma_D$ into fake path length $\propto \sqrt{T}\sigma_D$. Our kinematics readout computes **direct calibrated scalars** (never advisory warnings, which regressed `-8` to `-18` pts in SPLIT `S3`) using a two-key **Certified Stationarity Gate**:
   - Aggregate object rigidity $\bar{p}^{\text{stat}}_m = \text{median}_{u\in \mathcal{M}_m} p^{\text{stat}}_t(u)$ and Mahalanobis net displacement $\chi^2_m = (\mathbf{c}_{t_2}-\mathbf{c}_{t_1})^\top(\Sigma_{t_1}+\Sigma_{t_2})^{-1}(\mathbf{c}_{t_2}-\mathbf{c}_{t_1})$ across visible-overlap windows.
   - Clamp $\hat{v}_m \equiv 0$ whenever $\bar{p}^{\text{stat}}_m > 0.75$ OR $\chi^2_m < \tau_{\chi}$ (calibrated on held-out static objects to `<2%` FPR); for certified movers, compute speed from 3-point temporal median + Savitzky-Golay filtered world centroids.
2. **Fixing 69% Object Heading-Sign / Turn Error:**
   Centroid velocity direction fails whenever an object rotates in place, reverses, or jitters. We fuse two complementary estimators in the gravity-leveled XY plane:
   - **Direct Kabsch/Procrustes Rotation from 3D Point-Flow:** Fit the weighted rigid transform $(\hat{R}^{\text{obj}}_{t\to t+\delta}, \hat{\mathbf{t}}^{\text{obj}})$ directly to matched interior patch pairs $\{(\mathbf{P}^w_t(u), \mathbf{P}^w_t(u)+\Delta\mathbf{P}^{\text{obj}}_{t\to t+\delta}(u))\}_{u\in\mathcal{M}_m}$ weighted by $\exp(-\sigma^2_{\text{flow}})$. Exact turn angle $\Delta\psi_m = \text{atan2}((\hat{R}^{\text{obj}})_{21}, (\hat{R}^{\text{obj}})_{11})$ is invariant to centroid jitter and detects in-place turns.
   - **Canonical Semantic Front-Axis Head:** Predict a 2D gravity-leveled unit heading vector $\mathbf{f}_m \in S^1$ per 3D cluster supervised by oriented boxes (ScanNet/Omni6DPose/Waymo), resolving forward vs backward motion sign.
3. **Time-Reversal & Mirror Equivariance Training:**
   Include paired temporally reversed clips $(I_T, \dots, I_1)$ and left-right mirrored clips in every 4D training batch with exact algebraic targets: $T^{\text{rev}}_{i\to j} = (T^{\text{fwd}}_{j\to i})^{-1}$, $\Delta\mathbf{P}^{\text{rev}}_{t+\delta \to t} = -\Delta\mathbf{P}^{\text{fwd}}_{t\to t+\delta}$, $\Delta\psi^{\text{rev}} = -\Delta\psi^{\text{fwd}}$. This bakes SPLIT's `98% vs 10%` bidirectional VSTI dominance directly into the student weights.

### 1.4 4D Loss Formulation, Supervision & Direct VLA Manipulation Trajectory Bridge
- **Composite 4D Head Loss (co-calibrated scale + dynamics):**
  $$\mathcal{L}_{\text{4D}} = \lambda_{\text{stat}}\,\text{BCE}(p^{\text{stat}}, y^{\text{stat}}) + \lambda_{\text{flow}}\sum_{\delta}\Big[\frac{\|\Delta\hat{\mathbf{P}}_{t\to t+\delta} - \Delta\mathbf{P}^*\|_\delta}{\sigma_{\text{flow}}} + \log \sigma_{\text{flow}}\Big] + \lambda_{\text{scale}}\,\mathcal{L}_{\text{paired-K}}(\hat{D}, D^*) + \lambda_{\text{sp}}\,\mathcal{L}_{\text{sp}} + \lambda_{\text{rev}}\,\mathcal{L}_{\text{rev}}$$
  where $\mathcal{L}_{\text{paired-K}}$ computes scale strictly over **common-valid pixels conditioned on exact pad-masked intrinsics $K_t$** (eliminating SPLIT's `1.11×–1.52×` static and `1.36×` outdoor `MapAnything` scale bias), and $\mathcal{L}_{\text{rev}}$ enforces forward/backward algebraic symmetry on paired reversed clips.
- **Training Data Mix:** (a) Exact synthetic 4D (`PointOdyssey`, `DynamicReplica`, `Kubric`: ground-truth $p^{\text{stat}}, \Delta\mathbf{P}, T_t, D_t$), (b) teacher-lifted real dynamic video (`Point4D` + `CoTracker3` + $\pi^3$ + `UniK3D(known-K)` paired-pixel scale + `ViPE` `2.72°` filter rejecting `>5°` G3T disagreements), (c) robot manipulation videos (`DROID`, `Open-X`, `LIBERO`) where FK supplies exact gripper 3D flow.
- **Manipulation Action = Future 3D Point-Flow:** At deployment time $t$, evaluating $\Delta\mathbf{P}^{\text{obj}}_{t\to t+h}(u)$ ($h \in \{1,4,8,16\}$) over gripper/hand patches $u \in \mathcal{M}_{\text{eef}}$ and target object patches $u \in \mathcal{M}_{\text{obj}}$ directly predicts the future 3D trajectory of both manipulator and object in canonical metric world coordinates. Fitting weighted Kabsch $SE(3)$ to gripper patches extracts candidate end-effector deltas $\Delta \hat{T}_{\text{eef}}(t\to t+h) \in SE(3)$—unifying unlabeled human hand-object videos (`Ego4D`/`HD-EPIC`) and robot teleop demos inside the exact same 3D representation consumed by `FlowExpert` (`F1`) and `QwenOFT` (`U1`).

---

## 2. Causal Streaming Loop-Closed 3D Submap Memory ("Neural Map Memory")

To move from 32 static frames to **256–1,000+ streaming frames at $O(1)$ per frame** without exploding Qwen3.5's 8 full-attention KV caches (`241k` prompt bloat on VQ3D), we design a causal submap-chunked memory modeled directly on SPLIT's `HiP3R+SALAD+UniK3D` proof (`6.12 GB` RSS / `10.5 GiB` VRAM, `87.0` flat across 55-min HD-EPIC, `0.43 m` VQ3D) and `w1_cleansheet_arch` Idea 6.

### 2.1 Streaming Submap Construction ($O(1)$/Frame)
```
Incoming RGB Stream (1..3,600 frames @ 1-2 fps or 5-20 Hz robot)
  ├─► [Blackout / Blur Gate] (luma/Laplacian sidecar; drop dark cuts before pose write)
  ├─► [Chunked 4D Geometry Trunk] (W=32 frames, O=12 overlap, ~10 ms/frame amortized)
  │      └─► Local Submap S_c: poses T^(c)_t, gravity g_c, static voxels V_c (<=128), SALAD/SigLIP keys d_k
  ├─► [3-Tier Stitcher + 4-DoF Loop-Closure Pose Graph] (<2 ms/chunk -> global metric Z-up world)
  └─► [Persistent Neural Map M_world (<=1,024 voxels) + Dense Frame Index (SigLIP)]
         ├─► Always-On Context (<=1,024 map tokens + BEV/egocentric polar table, O(1) vs T)
         └─► Two-Budget Read: Cheap Probe (256-1,024f, 0 LM KV) -> High-Res Verify (<=16-32 RGB frames)
```
Each chunk $c$ runs our student's own depth + pose + rigidity + gravity heads on $W=32$ frames (`12`-frame overlap with $c-1$) and scatters high-confidence static tokens ($p^{\text{stat}} > 0.6$) into a sparse local voxel grid $\mathcal{V}_c$ (`0.10–0.15 m` pitch, confidence-weighted mean $\mathbf{f}_v = \sum w_i \mathbf{h}_i / \sum w_i$, storing $(\mathbf{P}_v, \mathbf{f}_v, \sigma_v, t_{\text{first}}, t_{\text{last}}, p^{\text{stat}}_v)$). Moving objects write time-stamped dynamic entries $(\mathbf{P}^w_m(t), \mathbf{f}_m, t)$ into a separate compact entity ledger so transient objects stay queryable for causal VQ3D ("where did I last leave my keys?") without ghosting static walls.

### 2.2 Solving Cross-Submap Fragmentation (`40.3%` vs `68.1%`) & Gravity-Less Close-Ups
SPLIT's Ego-Exo 2B audit exposed a `27.8`-pt collapse across disconnected submaps (`40.3` cross-submap vs `68.1` within-submap), and floor RANSAC failed on `194/198` Ego-Exo submaps. We eliminate fragmentation with a **3-Tier Submap Stitcher + Post-Stitching Global Gravity**:
1. **Tier 1 — Static-Overlap Rigid Alignment:** When overlap frames $(c-1)\cap c$ yield $\ge 64$ static 3D correspondences ($p^{\text{stat}} > 0.7$), solve confidence-weighted Umeyama $SE(3)$ (upgrading to bounded $Sim(3)$ with $|\log s| \le 0.15$ only if depth-ratio residual exceeds `5%`).
2. **Tier 2 — Low-Inlier Overlap-Rotation + Yaw-Continuity Bridge (SPLIT v2):** On close-ups, planar walls, climbing, or scooter benches where point inliers collapse, compute relative rotation directly from overlap camera orientations $\Delta R = \text{mean}_{t\in\text{ov}} R^{(c-1)}_t (R^{(c)}_t)^\top$, project roll/pitch onto the **post-stitching global gravity vector** $\bar{\mathbf{g}}$ (aggregated across all high-confidence submaps, never noisy single-chunk floor RANSAC!), and bridge translation via yaw-continuous visual odometry. (In SPLIT, this lifted HourVideo single-frame coverage `1/20 → 19/20` and cut climbing heading error `35.2° → 6.1°`.)
3. **Tier 3 — Explicit Hard-Cut Only on Real Discontinuities:** Start a new `map_id` *only* across `>10 s` dark blackouts or teleport cuts. Expose `map_id` on every voxel and keyframe so the LM never computes metric distances across disjoint worlds.
4. **Global 4-DoF Loop Closure (`SALAD` + Pose Graph):** Each chunk's keyframe descriptors $\mathbf{d}_k \in \mathbb{R}^{256}$ query past keyframes with $|t_k - t_j| > 15\text{ s}$. Top matches passing $p^{\text{stat}}$-masked PnP geometric verification add a gravity-preserving 4-DoF loop constraint $\Delta\mathbf{x}_{a\to b} = (\Delta x, \Delta y, \Delta z, \Delta\psi)$ into a sparse Gauss-Newton pose graph (`<2 ms` for 200 submaps):
   $$\min_{\{\mathbf{p}_c, \psi_c\}} \sum_{(a,b)\in \mathcal{E}_{\text{odom}}\cup \mathcal{E}_{\text{loop}}} \rho_\delta\Big(\big\| R_z(-\psi_a)(\mathbf{p}_b - \mathbf{p}_a) - \Delta\mathbf{p}_{a\to b} \big\|_{\Omega_p}^2 + \big\| \text{wrap}(\psi_b - \psi_a - \Delta\psi_{a\to b}) \big\|_{\Omega_\psi}^2\Big)$$
   Updating submap poses $(\mathbf{p}_c, \psi_c)$ transforms all voxel coordinates $\mathbf{P}_v$ in $O(N_v)$ without re-running the ViT.

### 2.3 Bounded KV-Cache, Hierarchical Voxel Retention & Decoupled Probe/Verify Budgets
To prevent both KV explosion (`241k` prompt bloat on VQ3D) and forgetting early rooms over 55-minute videos, $\mathcal{M}_{\text{world}}$ uses **two-tier spatial hashing**: static background merges at adaptive pitch (`0.15 m` near agent / `0.35 m` far rooms) with confidence-weighted running averages so early rooms never evict, while the **dynamic entity ledger** retains the highest-salience and most-recent (`t_last`) 3D pose per moved object instance. The 9B LM reads $\mathcal{M}_{\text{world}}$ through **three constant-size channels (`<=1,800` total visual tokens for a 60-min video)**:
1. **Global Neural Map + Precomputed Egocentric Polar Readouts (`<=1,024` tokens):** Spatial-hash merged world voxels injected with Metric 3D-RoPE (or world coordinates + `t_last`), plus a lightweight **metric top-down BEV / yaw-stitched map token summary** and precomputed egocentric polar readouts `(bearing_deg, horizontal_distance_m, dz_m, t_last)` relative to query time $t_q$ (replicating SPLIT `L12`, which cut ~2,100 hand-trig tokens and halved latency `45.3s → 20.7s`).
2. **Decoupled Dense Semantic Probe (`256–1,024` frames, zero LM KV cost):** A causal mask ($t \le t_q$ for VQ3D and live mobile robots) filters the dense `SigLIP-SO400M` frame index + voxel semantic keys $\mathbf{f}_v$. Cheap cosine scoring retrieves top-$K$ candidate timestamps and 3D bounding regions across the full video without touching the 9B LM's KV cache.
3. **High-Res Visual Verify Budget (`<=16–32` RGB frames/crops):** Only the top-$K$ retrieved frames—or high-res crops around low-confidence, empty, or multi-instance detections—are encoded into full-resolution visual tokens for the 9B LM. This preserves SPLIT's `+11.8 pp` closed-loop visual verification advantage over one-shot scripts (`PILOT_ONESHOT_PROGRAM`) at a hard-capped context budget.
- **Exact Footprint (60 min @ 1 fps = 3,600 frames):** `~120` submaps → `<=1,024` merged world voxels (`4 MB` fp16) + `3,600` SigLIP/SALAD keys (`4 MB`) + pose graph (`<0.2 MB`); total host RAM `<6 GB`, VRAM `<10.5 GiB`, strictly $O(1)$ LM FLOPs wrt duration.

---

## 3. Calibration-Free Cross-View (`Ego-Exo` / `Wrist-Agent`) Registration

### 3.1 Removing Monotonic Temporal Lock-In
`FrozenG3TTower` (`tower_read.py:36-57`) and `carrier_c1.py:590` assume one monotonically ordered monocular camera, forcing `vla_where` (`U1`) to hack around simultaneous views with a 5-view external `ViewSetG3T` wrapper. We generalize our geometry trunk natively to **arbitrary uncalibrated camera sets**:
1. **Order-Agnostic `(stream_id, timestamp)` Embeddings & Cross-Camera Patch Isolation:** Replace strict sequential frame indices in the geometry trunk with learned `stream_id` embeddings (`ego`, `exo_1..k`, `wrist`) paired with continuous `timestamp_i`. Disable Qwen3.5's `temporal_patch=2` merging across different `stream_id`s so simultaneous `wrist_t` and `agent_t` frames never bleed into one visual token.
2. **All-Pairs Bidirectional Cross-View Attention:** Run alternating intra-frame and all-view global attention inside mid-trunk layers `1..L_geo` across all $N$ views simultaneously. The pose/depth heads emit relative extrinsics $T_{a\leftarrow b} \in SE(3)$ for every camera pair $(a,b)$, per-view intrinsics $K_a, K_b$, shared gravity $\mathbf{g}$, and metric depth $D_a, D_b$ in one forward pass—followed by 3-step $p^{\text{stat}}$-masked Gauss-Newton TT-BA (`<15 ms`) to sharpen wide-baseline (`45°–150°`) geometry.
3. **Dual-Mode Robot Base & Exo Camera Locking (`LIBERO-Plus` Camera-Shift Immunity):**
   - *Passive Ego-Exo Mode (`Ego-Exo4D`, `MMSI`, `MindCube`):* Static background patches ($p^{\text{stat}} > 0.7$) anchor $T_{\text{ego}\leftarrow\text{exo}}$ directly (targeting SPLIT's `1.65°–2.26°` rotation, `0.05 m` ATE, `83.9%` Suite 2A).
   - *Active Robot Mode (`LIBERO-Plus`, `DROID`, `RoboCasa365`):* Proprioception + hand-eye (`T_eef_cam`, `6e-8 m` residual) supplies exact metric $T_{\text{base}\leftarrow\text{wrist}}(t)$. Our cross-view head estimates $\hat{T}_{\text{wrist}\leftarrow\text{exo}}(t)$ online—using static tabletop background ($p^{\text{stat}} > 0.7$) **and**, when wrist close-ups lack tabletop overlap, using forward-kinematics 3D robot-arm keypoints as known dynamic fiducials—immediately recovering the uncalibrated third-person camera in robot-base coordinates:
     $$\hat{T}_{\text{base}\leftarrow\text{exo}}(t) = T_{\text{base}\leftarrow\text{wrist}}(t) \cdot \hat{T}_{\text{wrist}\leftarrow\text{exo}}(t)$$
     Every third-person pixel unprojects directly into invariant robot-base coordinates (`reach_base = x_target_base − x_eef_base`) fed to `QwenOFT`/`FlowExpert`. If an operator bumps the third-person camera by `±45°` or `±0.5 m` mid-episode, $\hat{T}_{\text{base}\leftarrow\text{exo}}(t)$ re-locks automatically in one forward pass—eliminating the `LIBERO-Plus` camera-shift collapse (OpenVLA-OFT `97.1 → 59.7`, $\pi_0$ `94.2 → 15.8`) without external `ViewSetG3T` or recalibration.
   - *Convention & Low-Overlap Guards:* Keep aspect-preserving, pad-masked per-view intrinsics $K_a, K_b$ (explicitly supporting signed `fx < 0` for mirrored MuJoCo rasters per `T-4`), and apply a trust-region gate on $\hat{T}_{\text{base}\leftarrow\text{exo}}(t)$: when instant wrist-exo static inliers drop below threshold (e.g., inside a drawer), hold the last verified $\hat{T}_{\text{base}\leftarrow\text{exo}}$ smoothed via exponential Lie-algebra filtering on $SE(3)$ while relying on wrist-frame `reach_base`.

### 3.2 Cross-View Objective, Training Mix & Dual Payoff
Supervise all camera pairs $(a,b)$ with symmetric cross-view pointmap reprojection + geodesic $SO(3)$ rotation + scale-normalized translation + shared-gravity consistency:
$$\mathcal{L}_{\text{xview}} = \sum_{a \neq b}\Big[\| \log(R_{a\leftarrow b}^\top \hat{R}_{a\leftarrow b}) \|_2 + \|\hat{\mathbf{t}}_{a\leftarrow b} - \mathbf{t}_{a\leftarrow b}\|_\delta + \lambda_{\text{pm}}\|\hat{T}_{a\leftarrow b}\hat{\mathbf{P}}_b - \mathbf{P}_a\|_\delta + \lambda_g\| \hat{R}_{a\leftarrow b}\hat{\mathbf{g}}_b - \hat{\mathbf{g}}_a \|_2\Big]$$
| Data Source | View Structure | Exact Supervision | Unlocked Capability |
|---|---|---|---|
| **Ego-Exo4D** | Sync Aria + 2–4 GoPro views | GT $T_{\text{ego}\leftarrow\text{exo}}$, gravity, metric scale | `+30–45 pp` cross-view QA (`39.3→83.9` bar) |
| **ScanNet / ScanNet++ / ARKit + MindCube-10K** | Wide-baseline N-view (`45°–150°`) | GT $SE(3)$ poses, depth, scene-clean QA | MMSI (`28→67.8` bar), MindCube (`>86`) |
| **DROID + LIBERO Multi-Cam (+ Synthetic Jitter)** | `wrist_t + 1..2×exo_t` + random `±45°/±0.5m` exo jitter | Exact FK $T_{\text{base}\leftarrow\text{wrist}}$, `reach_base`, mask-lifted OBBs | `LIBERO-Plus` `+Cam` immunity & zero-calib real-robot deploy |

---

## 4. Decisive 48–72h Kill-Test Ladder

Executed on **free 49 GB Trinity GPUs** (`trinity-2-28` GPUs `4–7` idle under `vnice`; `trinity-0-13` spare) and optional 1× Orchard H100 (`general` queue)—requiring **zero full 9B LM retraining** during Stages 0–3 so we validate every geometric mechanism before folding winners into the next unified 9B leg (post-Leg N).

| Stage | Window & Budget | Concrete Experiment | Exact Benchmarks | Hard Pass / Kill Gate |
|---|---|---|---|---|
| **Stage 0: `dyn_probe` Baseline** | **0–6h** (`<5 GPU-h`, 1× 49 GB, 0 train) | Run CPU-sealed `dyn_probe` (`47` tests PASS) on student `step-544` / `R1-400` + G3T + Point4D reference; measure dynamic ATE, stationary-speed FPR, heading-sign acc, and forward-vs-reversed VSTI gap. | TUM, Bonn, LIBERO replays, clean ReSTI (`999` Waymo+Omni6DPose), DSI-1k, reversed-VSTI | **Diagnostic Gate:** Quantify exact ATE jump on movers, stationary-target false speed, and reversal gap; confirm `0` data-leakage on clean splits before Stage 1 launches. |
| **Stage 1: 4D Rigidity + Flow Pilot** | **6–24h** (`12–16 GPU-h`, 2× 49 GB, frozen LM) | Train `~18M`-param `(p^stat, ΔP_obj, σ_flow)` head + 5-step static-masked TT-BA on frozen mid-trunk/G3T features using PointOdyssey + DynamicReplica + CoTracker3-lifted Ego4D/DROID (`20k` clips) + paired reversed clips. | TUM/Bonn/Sintel ATE; OSI/DSI stationary FPR & Kabsch heading sign; reversed-VSTI; LIBERO wrist-cam `H=8` 3D flow EPE | **PASS:** Dynamic camera ATE drops `>=30%` vs rigid pose; stationary-speed FPR drops `>=75%`; heading-sign acc `>=85%` (vs `69%`); reversed-VSTI bidir `>=90%` (vs `10%`); LIBERO gripper/object 3D EPE `<=5 cm`; static VSTI regresses `<=1.0` pt. **KILL** if ATE drop `<15%` or static regresses `>1.5` pt. |
| **Stage 2: Causal Streaming Memory Pilot** | **24–48h** (`14–18 GPU-h`, 2× 49 GB) | Run chunked (`W=32, O=12`) submap pipeline + 3-tier yaw-continuity stitcher + `SALAD` 4-DoF loop closure + `SigLIP` two-budget probe/verify (`<=1,024` voxels + `<=16` RGB verify) with `L12` polar readouts. | HourVideo `dev-20` single-frame coverage; VQ3D (`n=163` causal `t<=t_q`); HD-EPIC `4–55 min` subset; `E0` MP3D nav (`900` items); long `R0-dev` (`20` rooms `>178 s`) | **PASS:** HourVideo single-frame `>=18/20` (vs `1/20` unbridged); VQ3D proxy median L2 `<=0.60 m` (`Succ@1m >=65%`, vs `1.56 m` base); long `R0-dev` gains `>=+4.0` ReVSI pts at `<=2,000` visual tokens & `<8 GB` RAM; E0 nav beats `f17` (`37.5`) by `>=+30` pts with scale ratio within `[0.92, 1.08]` (fixing `1.94×` drift). **KILL** if cross-submap drop `>10` pts or RAM `>10 GB`. |
| **Stage 3: Cross-View `Ego-Exo` / `+Cam` Pilot** | **48–72h** (`18–24 GPU-h`, 2–4× 49 GB or 1× H100) | Train order-agnostic `stream_id` cross-view pose+depth adapter + $p^{\text{stat}}$-masked TT-BA on Ego-Exo4D train + wide-baseline ScanNet + jittered DROID/LIBERO; run `vla_where` `T-11` + `P-1..P-4` on LIBERO-Plus `+Cam` replays. | Ego-Exo4D Suite 2A (`n=100` val); MMSI; LIBERO-Plus `+Cam` (`376` eps) `reach_base` accuracy | **PASS:** Ego-Exo4D Aria↔GoPro rot error `<=5°` and Suite 2A `>=70%` (vs `39.3%` base); MMSI beats base by `>=+15` pts; LIBERO-Plus `+Cam` `reach_base` 3D error `<=3 cm` under `±45°` exo shift (keeping `+Cam` drop `<=5%` vs OpenVLA-OFT `-37.4` / $\pi_0$ `-78.4`). **KILL** if Aria↔GoPro rot `>10°` or `+Cam` `reach_base` error `>5 cm`. |

### Concrete Risks & Immediate Fallbacks
| Failure Mode | Detection Signal | Engineering Fallback |
|---|---|---|
| **Own ViT still pose-blind before Spatial-Forcing²** | Stage 1/3 own-head rot `>8°` on held-out clips | Attach our 4D rigidity+flow + TT-BA heads atop frozen `G3T`/$\pi^3$ features during Stages 1–3; swap to native mid-trunk once Spatial-Forcing² clears `<5°`. |
| **Wrist close-up scale-flow degeneracy** | LIBERO gripper EPE `>5 cm` when tabletop occluded | Lock wrist $\Delta T_{\text{wrist}}$ via FK proprioception and apply $\ell_1$ flow sparsity strictly to non-arm patches. |
| **Loop-closure false positives (repetitive corridors)** | Pose-graph chi-square spike after `SALAD` match | Require `>=32` static PnP inliers + gravity-angle agreement `<8°` + Huber loss on loop edges before committing. |
| **Habitat / outdoor depth-scale drift** | Scale ratio outside `[0.92, 1.08]` on E0 or OSI | Anchor scale via known camera height + floor plane (`NU` nav) or paired-pixel `UniK3D(known-K)` / proprioception (`U1`), never unpaired marginal medians. |

### Convergence Path (Hour 72+)
Any head clearing its Stage 1–3 gate folds directly into the unified 9B Spatial-VLA backbone alongside `GF-1` / Spatial-Forcing² absorption (dropping external `ViewSetG3T` and `FrozenG3TTower` once native own-head rotation hits `<5°` and scale error `<3%`), followed by `rlkit-v1` closed-loop verification RL (rewarding active high-res frame re-inspection on uncertain/empty detections) and low-data **Test L** (`LIBERO-Spatial` + `+Cam`) and **Test N** (`10% R2R-CE` + `R2RIE-CE`) VLA evaluations.
