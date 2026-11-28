# Blue-Sky Round 2A: Post-`KT-6` & `J1-T` Geometry-Native Spatial Architectures

**Date:** `2026-11-28` | **Lane:** `bluesky28/bs2_arch_neon` | **Scope:** 5 post-empirical architectural breakthroughs shattering today's `KT-6`, `KT-1b`, `J1-T`, and `Point4D` walls (distinct from Round-1 `Spatial-V2` baselines).

---

## Diagnostic Synthesis: What Today's Four Walls Actually Prove
1. **The `KT-6` `45.1°` Paradox:** `Arm B` (`DA3` DINOv2-L + `EpiAdapter`) already nails unseen-room monocular geometry (`AbsRel 0.119`, ScanNet `0.084 / d1 94.1%`, scale `0.997`) and **gravity (`4.78°`)**—meaning 2 of 3 `SO(3)` rotational DoFs (pitch, roll) generalize on `214` rooms. The `45.05°` all-pairs rotation plateau (despite `91.7%` train loss collapse `3.40→0.28`) proves that **black-box transformer pose regression memorizes room appearance instead of solving the remaining 1D azimuthal yaw (`S^1`) from visual correspondences**.
2. **The `J1-T` Box-Prompt Autopsy:** Frozen `SAM 3` collapses at `IoU=0.50` (`-14.70` vs `k`, `-3.68` vs `a`), degrades `-8.03` at `IoU=0.70`, drops `-18.12` (`-32.83` ScanNet++) when `<1%`-area objects vanish, loses `-15.30` on `h1` empty-frame FPs, and loses `-9.06` if replaced by raw 2D box fill. **2D rectangular boxes are the wrong interface for 3D grounding**: 1 px in 2D crosses meters of 3D depth cliff, `<1%` objects vanish in `10×10` pooled tokens, and single-frame FPs lack multi-view 3D veto.
3. **The `reproj_p90` vs `TT-BA` Inversion:** Quantized `51×51` self-depth NN `TT-BA` regressed `+0.48°` (`NO-GO`), yet zero-GT `reproj_p90` detects `>30°` pose failures at **`0.898 AUROC` in `2.98 ms`** (`free_space_viol`: `0.876 AUROC`) and `ScaleAnchor` locks scale to **`0.42%`**. Geometry already knows when it fails—in `<3 ms`—without using that certificate to repair, gate, or self-train itself.
4. **The 4D & Reasoning Gap:** `Point4D` cleanly isolates static scenes (`0.018–0.033 m` residual under `15–53 m` ego motion), yet `DSI-Bench` drops `-26.5` to `-33.3 pp` on time-reversal/mirror (`73.0%→46.5%/39.7%`), and verbal CoT still cannot differentiate through metric geometry.

---

## Breakthrough 1: `GravSync-Corr` — Gravity-Pinned `S^1` Differentiable Correlation-Kabsch Solver
### 1. Radical Thesis
Kill black-box `SO(3)` pose regression (`GeoPoseHead` MLP). Because `gravity_head` already solves pitch and roll to `4.78°` on unseen rooms, decompose relative camera pose into **exact gravity leveling + 1D circular yaw (`S^1`) + 3D translation**, solved inside the forward pass by a **parameter-free DINOv2-L 4D correlation volume → `GeoDepthHead` 3D lifting → closed-form weighted 2D-yaw Kabsch → `reproj_p90`-weighted Hermitian `SO(2)` spectral sync**. Zero appearance-memorization capacity forces generalization even from `214` rooms.

### 2. Exact Mechanism
- **Gravity-Leveled Lifting:** Given `GeoDepthHead` depth $D_t \in \mathbb{R}^{H\times W}$ and `gravity_head` unit vector $\mathbf{g}_{c,t}$, build deterministic shortest-arc leveling $R_{\text{lvl},t} \in SO(3)$ mapping $\mathbf{g}_{c,t} \mapsto [0,0,-1]^\top$. Then $R_{\text{w2c},t} = R_{\text{lvl},t}^\top R_z(\psi_t)$ reduces unknown rotation to scalar yaw $\psi_t \in S^1$, and leveled 3D patch clouds are $\tilde{\mathbf{P}}_t = R_{\text{lvl},t}(D_t K_t^{-1}\tilde{\mathbf{u}}) \in \mathbb{R}^{HW \times 3}$.
- **4D Correlation & Soft-MNN:** Compute normalized DINOv2-L tap-`23` cosine correlation $C_{ij} = \hat{F}_i \hat{F}_j^\top / \tau \in \mathbb{R}^{HW\times HW}$ across all $\binom{N}{2}$ view pairs. Extract dual-softmax mutual nearest neighbors $M_{ij} = \operatorname{softmax}_{\text{row}}(C_{ij}) \odot \operatorname{softmax}_{\text{col}}(C_{ij})$ and top-$K$ ($K=64$) soft matches $(\tilde{\mathbf{p}}_i^{(m)}, \tilde{\mathbf{p}}_j^{(m)})$ weighted by $w_{ij}^{(m)} = M_{ij}^{(m)} \cdot p^{\text{stat}}_i p^{\text{stat}}_j \cdot \sigma(\text{MLP}([\Delta z_m, c_m, \sigma_{D,i}, \sigma_{D,j}]))$ (tiny `0.4M`-param inlier gate exploiting yaw-invariant vertical consistency $\Delta z_m$).
- **Exact Differentiable `S^1` Kabsch + Spectral Sync:** For centered residuals $(\mathbf{u}_m, \mathbf{v}_m)$, compute closed-form relative yaw (no SVD instability):
  $$\Delta\psi_{ij} = \operatorname{atan2}\!\Big(\sum_m w_{ij}^{(m)}(u_{m,x}v_{m,y} - u_{m,y}v_{m,x}),\; \sum_m w_{ij}^{(m)}(u_{m,x}v_{m,x} + u_{m,y}v_{m,y})\Big),\quad \Delta\mathbf{t}_{ij} = \bar{\mathbf{p}}_j - R_z(\Delta\psi_{ij})\bar{\mathbf{p}}_i.$$
  Assemble Hermitian matrix $H_{ij} = \gamma_{ij} e^{\mathrm{i}\Delta\psi_{ij}}$ with $\gamma_{ij} = \exp(-\text{reproj\_p90}_{ij}/\tau_e)\sum_m w_{ij}^{(m)}$, solve global $\psi_{1..N}$ via 5 differentiable complex power iterations, solve global camera centers $\mathbf{o}_{1..N}$ via weighted graph Laplacian SPD solve (`torch.linalg.solve`), and add a bounded `<=8°` residual tilt correction $\delta\boldsymbol{\omega}_t$.
- **Losses:** Standard `PoseAnd4DLoss` + correspondence cycle consistency; gradients flow *through* Kabsch + spectral sync into DINOv2-L descriptors and `GeoDepthHead`, training correspondence-equivariant features instead of room memorization.

### 3. Why Today's Data Specifically Points Here
`Arm B` hit `4.78°` gravity and `0.119` `AbsRel` (`0.084` ScanNet) while stalling at `45.1°` all-pairs rotation on `214` rooms (`91.7%` train loss drop). Factoring out solved gravity and replacing 30M-param regression with analytic DINOv2-L correlation Kabsch removes the exact overfitting pathway AND solves unordered wide-baseline pairs (`VSTI`, `Ego-Exo4D`).

### 4. Fastest 48-Hour Falsification Test
Drop `GravSync-Corr` onto today's exact `KT-6 Arm B` `233`-capture (`214`-room) split on `trinity-2-28` (`1× RTX 6000 Ada`, `~65 min`, identical `2,000` steps & `K1-heldout n=53`).
- **GO:** Held-out `rot_med_deg` drops from **`45.05° → <= 18.0°`** (`clip-med <= 12.0°`) and `rot_acc_15deg` rises `21.4% → >= 55%` on the *exact same 214 rooms* without degrading `AbsRel` (`<= 0.122`).
- **NO-GO / KILL:** `rot_med_deg > 28.0°` (proving `20×20` DINOv2-L correlation lacks wide-baseline match recall without pretrained multi-view attention).

---

## Breakthrough 2: `RayField-3D + Fovea3D` — Box-Free, SAM-Free 3D Surfel Grounding & Multi-View Free-Space Veto
### 1. Radical Thesis
Delete 2D bounding boxes and frozen `SAM 3` entirely. Ground language queries **directly on canonical `+Z`-up 3D surfels** lifted by `GeoDepthHead + GeoPoseHead` via a **3D metric-bilateral CRF** (segmenting across *meters* of 3D depth cliff, not 2D pixel boxes), recover `<1%` small objects via **Depth-Guided Foveal Ray-Casting (`Fovea3D`)** onto the nearest full-res frames, and annihilate empty-frame FPs via **Multi-View Free-Space + Cross-View Feature Consensus**.

### 2. Exact Mechanism
- **3D Surfel Field & Metric-Bilateral Refinement:** Unproject `DA3` DINOv2-L features `F` with `GeoDepthHead` + `GeoPoseHead` into surfels $\mathcal{S} = \{(\mathbf{P}_i^w, \mathbf{n}_i^w, \mathbf{f}_i, \sigma_{D,i}, p^{\text{stat}}_i)\}$ (normals $\mathbf{n}_i^w$ via parameter-free 3D finite differences). Language query token $\mathbf{q}$ emits coarse surfel logits $\ell^{(0)}_i = \langle W_q \mathbf{q}, W_s[\mathbf{f}_i; \operatorname{PE}_{3D}(\mathbf{P}_i^w); \mathbf{n}_i^w]\rangle$, refined by 3 differentiable 3D metric-bilateral CRF steps:
  $$\ell^{(r+1)}_i = \ell^{(0)}_i + \lambda \sum_{j \in \mathcal{N}_{3D}(i)} \exp\!\Big(-\frac{\|\mathbf{P}_i^w - \mathbf{P}_j^w\|^2}{2\sigma_x^2} - \frac{1 - \mathbf{n}_i^w\cdot\mathbf{n}_j^w}{\sigma_n^2}\Big)\,\ell^{(r)}_j,\quad \sigma_x = 0.08\text{ m}.$$
  Background surfels behind an object edge sit `0.5–4.0 m` away, driving kernel weight to `0`—yielding crisp foreground 3D masks with zero `SAM 3` and zero box leakage.
- **`Fovea3D` Small-Object Recovery (`+4 ms`):** Extract top-$K$ ($K=3$) 3D candidate peaks $(\mathbf{c}_k^w, r_k)$ from coarse surfel probabilities (plus high-recall 2D DINOv2-L attention peaks). For each peak, select the 2–3 frames minimizing camera-to-object distance $\|\mathbf{c}_k^w - \mathbf{o}_t\|$ (maximizing projected pixel area), crop native full-res `224×224` RGB around $\pi_t(\mathbf{c}_k^w)$, re-run the *shared* `DA3` stem + `GeoDepthHead` on those crops, and lift the `8×`-denser foveal surfels back into `+Z`-up world coordinates.
- **Multi-View Presence Veto (Zero-FP Filter):** Project every candidate 3D cluster $\Omega_q$ into all $N$ views via `GeoPoseHead`. Compute (a) free-space violation $v_{\text{free}}(\Omega_q) = \Pr[D_t(\pi_t(\Omega_q)) > Z_{\text{proj}} + 3\sigma_D]$ and (b) cross-view semantic agreement $s_{\text{xview}}(\Omega_q) = \text{mean}_{t \in \mathcal{V}_{\text{vis}}} \cos(W_q \mathbf{q}, F_t(\pi_t(\Omega_q)))$. Predict presence $p_{\text{pres}} = \sigma(w_1 s_{\text{xview}} - w_2 v_{\text{free}} + w_3 \log|\mathcal{V}_{\text{vis}}| + b)$. Single-frame FPs fail cross-view agreement and ray carving.
- **Losses:** 3D surfel Focal + Dice loss distilled from `J1-k` lifted masks + 3D ScanNet/ARKit GT instance clouds + hard-negative empty-frame BCE on `p_pres`.

### 3. Why Today's Data Specifically Points Here
`J1-T` proved all 4 failure modes of 2D-box+`SAM 3`: `IoU=0.70` drops `-8.03` (`-10.30` ARKit, `-9.67` ScanNet++), `IoU=0.50` collapses (`-14.70`), dropping `<1%` area crashes ScanNet++ by `-32.83` (`39/117` refusals), `kP-fp` loses `-15.30`, and raw box fill loses `-9.06`. Lifting segmentation into 3D metric space + foveal nearest-view zoom + multi-view ray veto attacks every single mode at its physical root.

### 4. Fastest 48-Hour Falsification Test
Evaluate `RayField-3D` (3D bilateral CRF from `DA3` depth + DINOv2-L, zero `SAM 3`) + `Fovea3D` + multi-view presence veto on **`DEV-MASK 117`** (`46` captures, `trinity-2-28`, `~6 GPU-h` lightweight head fit on disjoint train rooms).
- **GO:** Beats served `a` (`55.81`) by **`>= +8.0` MRA (`>= 63.8`)** with **`0` `SAM 3` calls**, recovers `>= 85%` of `<1%`-area ScanNet++ anchors (refusals `<= 5/117`), and cuts `kP-fp` empty-GT masks by **`>= 85%`** (`1,098 → <= 165`).
- **NO-GO / KILL:** `MRA < 60.0` or `Fovea3D` fails to beat `kB(0.7)` (`58.80`) on ScanNet++ (`60` items).

---

## Breakthrough 3: `CertGeo-Loop` — Closed-Loop Active Infill, Feature-Metric BA & Self-Muting 3D-RoPE Driven by `reproj_p90`
### 1. Radical Thesis
Exploit today's discovery that zero-GT `reproj_p90` achieves **`0.898 AUROC` in `2.98 ms`** by turning geometry estimation into a **self-verifying closed loop**: use the `N×N` residual certificate matrix $E_{ij}$ to trigger (1) **Active Midpoint Frame Infill** across broken wide-baseline gaps, (2) **DINOv2-L Feature-Metric BA (`Feat-BA`)** replacing failed self-depth NN `TT-BA`, (3) **Per-Frame Self-Muting `Metric3DRoPE`** inside the LLM, and (4) **Zero-Label Web-Video Self-Distillation** to shatter the `214`-room data ceiling.

### 2. Exact Mechanism
- **Pairwise Certificate Tensor (`2.98 ms`):** Compute $E_{ij} = (\text{reproj\_p90}_{ij},\, \text{free\_space\_viol}_{ij},\, \text{parallax}_{ij}) \in \mathbb{R}^{N\times N\times 3}$ directly from `GeoDepthHead` + `GeoPoseHead`.
- **Active Midpoint Frame Infill (Graph-Bridge):** Extract the temporal spanning tree of $E$. Any adjacent gap $(t, t+1)$ with $\text{reproj\_p90}_{t,t+1} > 0.16$ triggers the video decoder to pull `4–6` dense intermediate frames *only in that gap*, running a local overlap bridge to convert disconnected wide-baseline jumps into dense `<5°` chains (zero extra cost on healthy clips).
- **Certified Feature-Metric BA (`Feat-BA`) + `ScaleAnchor`:** Replace quantized `51×51` depth NN (`+0.48°` regression) with 4 damped Gauss-Newton steps minimizing **PCA-32 DINOv2-L photometric feature reprojection** $r_{ij}(u) = \|F_j(\pi(T_{ij} P_i(u))) - F_i(u)\|_{\text{Huber}}$ weighted by $p^{\text{stat}}_i(1 - \text{free\_space\_viol}_{ij})$ plus explicit `ScaleAnchor` log-scale term (`0.42%` scale error). Commit **strictly iff** both `reproj_p90` drops `>= 15%` and `free_space_viol` does not increase.
- **Self-Muting `Metric3DRoPE` & Zero-Label Data Flywheel:** Gate each frame's `Metric3DRoPE` phase amplitude inside Qwen3.5-9B by $g_t = \sigma((\tau_r - \text{reproj\_p90}_t)/s_r)$: corrupted frames smoothly attenuate their 3D positional phases back to `0` (exact 2D fallback) instead of poisoning LLM spatial attention. Offline, harvest unlabelled web/egocentric videos passing $\text{reproj\_p90} < 0.08 \land \text{free\_space\_viol} < 0.05$ as zero-label pseudo-GT training clips for `Arm B`.

### 3. Why Today's Data Specifically Points Here
`KT-1b` proved self-depth `TT-BA` regresses `+0.48°` (`6W/259T/31L`), while `reproj_p90` already catches failures at `0.898 AUROC` in `2.98 ms` and `ScaleAnchor` hits `0.42%`. The missing link is swapping self-depth NN for visual feature residuals + active gap-bridging + using the certificate to gate LLM 3D-RoPE and mine `100×` more training rooms.

### 4. Fastest 48-Hour Falsification Test
Run Active Midpoint Infill + `Feat-BA` (PCA-32 DINOv2-L, strict certificate guard) on `dev-S1` (`n=28`) and `K1` (`n=296`, `DA3` failures `rot_max > 15°`, `trinity-2-28` GPU 4, `<3 GPU-h`).
- **GO:** Cuts `DA3-only` `rot_max > 15°` rate by **`>= 35%` additional relative reduction** (`dev-S1` `21.4% → <= 14%`; `K1` `12.8% → <= 8.3%`) with **`0` captures regressing `>1.0°`** (vs `TT-BA`'s `31` regressions).
- **NO-GO / KILL:** `<15%` additional reduction in `>15°` failures OR `>= 5` captures regressing `>1.0°`.

---

## Breakthrough 4: `ChronoMetric-4D` — 3D-Keyed DeltaNet Static Memory & CPT-Equivariant Dynamic Rigid Tubes
### 1. Radical Thesis
Unify static 3D (`VSI`/`ReVSI`), dynamic 4D (`Point4D`/`DSI`/`ReSTI`), and 1-hour egocentric streaming (`HD-EPIC`/`HourVideo`) in one forward pass by splitting world state into: (1) an **$O(1)$-memory 3D-World-Coordinate-Keyed Static Scaffold inside Qwen3.5's 24 Gated DeltaNet layers** (indexed by metric `P^w`, never decaying over time when a room is revisited 40 min later), and (2) **CPT-Equivariant Dynamic Object Tubes `(c_k^w, v_k^w, ω_k^w)`** whose exact time-reversal (`t→-t`) and mirror (`fx<0`) antisymmetry kills `DSI-Bench`'s `-33.3 pp` reversal/mirror collapse by construction.

### 2. Exact Mechanism
- **3D-Metric-Keyed DeltaNet Static Memory (`SpatialHash-DeltaNet`):** In Qwen3.5's 24 DeltaNet layers ($S_t = \alpha_t S_{t-1} + \mathbf{k}_t \mathbf{v}_t^\top$), augment keys for visual tokens with gravity-leveled metric world Fourier keys $\mathbf{k}_t^{\text{3D}} = \phi_{\text{3D}}(\mathbf{P}_t^w)$ gated by static rigidity $p^{\text{stat}}_t$:
  $$S_t = \big(I - \beta_t\,p^{\text{stat}}_t\,\mathbf{k}_t^{\text{3D}}(\mathbf{k}_t^{\text{3D}})^\top\big)\,S_{t-1} + p^{\text{stat}}_t\,\mathbf{k}_t^{\text{3D}}\mathbf{v}_t^\top.$$
  This is an exact **3D-location-addressed associative write**: empty/unvisited 3D coordinates suffer **zero temporal forgetting** (`O(1)` memory across 1,000+ frames), while revisiting the same kitchen counter overwrites/refines only that 3D slot!
- **Factorized Dynamic `SE(3)` Tubes & CPT-Equivariance:** Pool dynamic surfels ($p^{\text{dyn}}_t > 0.5$) via $K_{\text{dyn}}=16$ cross-attention slots into world-frame rigid motion states $\mathcal{D}_k(t) = (\mathbf{c}_k^w(t), \mathbf{v}_k^w(t), \boldsymbol{\omega}_k^w(t))$ explicitly decoupled from ego twist $(\mathbf{v}_{\text{ego}}^w, \boldsymbol{\omega}_{\text{ego}}^w)$. Train on `Point4D`/`Any4D` stores with **Siamese Time-Reversal & Mirror Antisymmetry Loss**:
  $$\mathcal{L}_{\text{CPT}} = \|\mathbf{v}_k^w(V_{\text{rev}}) + \mathbf{v}_k^w(V_{\text{fwd}})\|_1 + \|\mathbf{v}_{\text{ego}}^w(V_{\text{rev}}) + \mathbf{v}_{\text{ego}}^w(V_{\text{fwd}})\|_1 + \|\mathbf{M}_x \mathbf{v}_k^w(V_{\text{hflip}}) - \mathbf{v}_k^w(V_{\text{fwd}})\|_1$$
  using `GeoDepthHead`'s already-verified handedness-preserving `fx < 0` mirror unprojection.

### 3. Why Today's Data Specifically Points Here
Today's `Point4D` validation proved `0.018–0.033 m` static background residual under `15–53 m` ego motion (`10/10` stores, `551 MiB` pilot convergence), confirming `p_stat` is clean enough to drive 3D-keyed static memory. Simultaneously, `DSI-Bench` exposed a catastrophic symmetry break (`std 73.0%` vs `reverse 46.5%`, `reverse_hflip 39.7%`) caused by entangling ego motion with object motion in 2D image coordinates.

### 4. Fastest 48-Hour Falsification Test
Train a lightweight `ChronoMetric-4D` tube head + `SpatialHash-DeltaNet` adapter on `trinity-0-13`'s `492` `Point4D` stores (`1× RTX 6000 Ada`, `<8 GPU-h`, zero-leak verified) and evaluate (a) `DSI-Bench` `std` vs `reverse` / `reverse_hflip` gap and (b) 3D revisit retrieval accuracy on `HD-EPIC` (`152` Qs, `>5 min` gaps).
- **GO:** Shrinks `DSI-Bench` `std - reverse_hflip` gap from **`33.3 pp → <= 6.0 pp`** while lifting overall `DSI` `>= +8.0 pp` (`58.4% → >= 66.4%`), AND beats temporal-decay DeltaNet by `>= +10 pp` on `>5 min` `HD-EPIC` revisit queries.
- **NO-GO / KILL:** `std - reverse_hflip` gap remains `> 15 pp` or static 3D-keyed memory saturates/collides on `>200`-frame clips.

---

## Breakthrough 5: `GeoVM-Latent` — Differentiable In-Stream 3D Spatial ALU Replacing Verbal Geometric CoT
### 1. Radical Thesis
Stop forcing an LLM to execute 3D Euclidean algebra, counterfactual perspective transforms, and occlusion ray-marching via **brittle English CoT tokens** or opaque attention weights. Embed a **differentiable `fp32` 3D Spatial ALU (`GeoVM`)** directly between Qwen3.5-9B's upper full-attention layers (`L ∈ {16, 20, 24}`), invoked by `M=8` continuous latent pointer registers over `RayField-3D` surfels—allowing downstream VQA, RLVR, and VLA losses to **backpropagate directly through exact 3D Euclidean equations** into `GeoDepthHead` and `GeoPoseHead`.

### 2. Exact Mechanism
- **Latent Pointer & Op Emission (`~2 ms`, `<4M` params):** At layers `L ∈ {16, 20, 24}`, `M=8` learnable `[GEO_OP]` registers cross-attend to `RayField-3D` surfels to emit soft pointer masks $\mathbf{a}_m^{(1)}, \mathbf{a}_m^{(2)} \in \Delta^{NHW}$, a continuous virtual pose $T_{\text{virt},m} \in SE(3)$ (6D rot + `t`), horizon $\Delta t_m$, and soft op weights $\boldsymbol{\pi}_m \in \Delta^6$.
- **6 Exact Differentiable `fp32` Primitives** operating directly on $(\mathbf{P}^w, \mathbf{n}^w, \mathbf{v}^w, \sigma_D, \text{reproj\_p90})$:
  1. `DIST_MIN(a1, a2)`: soft-min ($\text{LSE}_{-\beta}$) surface-to-surface Euclidean distance between two surfel clouds (exact closest-point distance, never centroid error).
  2. `BBOX_EXTENT(a1)`: gravity-leveled weighted 3D PCA eigenvalues `(L, W, H)` and floor-projected area.
  3. `TRANSFORM_VIEW(a1, T_virt)`: exact `SE(3)` re-projection of selected 3D surfels into any counterfactual camera/agent/robot-wrist frame → exact `(left/right, front/back, azimuth, depth)`.
  4. `RAY_VISIBILITY(o_virt, a1)`: soft surfel z-buffer occlusion test along rays from `o_virt` to `a1` ("is X visible from Y / path collision-free?").
  5. `MOTION_EXTRAP(a1, Δt)`: propagates `ChronoMetric-4D` tubes $\mathbf{P}^w + \mathbf{v}^w \Delta t$ for interception/collision queries.
  6. `CERT_WEIGHT(a1)`: outputs pointer-weighted `(reproj_p90, free_space_viol, σ_D)` so the LLM knows exact geometric reliability before committing to a scalar.
- **Zero-Init Residual Re-Injection & VLA Tap:** Fourier-encode the `32`-D continuous ALU output vector per register and inject into layer `L+1` (zero-init gate, preserving base VLM at step 0), while exposing the same `GeoVM` registers to `FlowExpert` for `SE(3)` contact/collision residuals.

### 3. Why Today's Data Specifically Points Here
`R1` and `K1-X` proved that verbalizing head outputs into discrete text tools suffers hard refusal/calibration cliffs and cannot pass task gradients back to fix depth/pose/grounding errors. Meanwhile, today's `spatial_v2` benchmark proved the entire native 3D forward pass runs in `18.9 ms` (`GeoDepth 1.66 ms + GeoPose 2.09 ms`). Adding a `2 ms` exact differentiable ALU turns those heads from passive features into an **end-to-end trainable geometric computer**.

### 4. Fastest 48-Hour Falsification Test
Attach `GeoVM-Latent` (`L=16` single-tap pilot, `M=8` registers, frozen base LM except LoRA-16 + `GeoVM` + `RayField` pointers) on top of cached `DA3` surfels and train `1,000` steps on `ReVSI` + `VSTI` (`trinity-0-13`/`2-28`, `~12 GPU-h`, paired vs matched direct-LoRA + text-CoT baselines).
- **GO:** Beats direct-LoRA by **`>= +6.0 pp`** on `ReVSI` distance/size/route and **`>= +8.0 pp`** on `VSTI` counterfactual camera-perspective items *without generating a single text-tool call*, AND `CERT_WEIGHT` prevents regression on injected `>30°` corrupt-pose stress clips (`<= 1.5 pp` drop vs `>= 6 pp` without `CERT_WEIGHT`).
- **NO-GO / KILL:** `<= +2.0 pp` over direct-LoRA or pointer entropy collapses (`a_m` fails to localize target surfels without explicit pointer supervision).

---

## Composability & 48-Hour Dispatch Matrix (Zero Overlap with Round-1 Queue)
| ID | Breakthrough | Primary Empirical Wall Shattered | GPU Cost | Key Dependency | Synergizes With |
|---|---|---|---:|---|---|
| **B1** | `GravSync-Corr` | `KT-6` `45.1°` wide-baseline pose plateau (`214` rooms) | `1.1 GPU-h` | Today's `Arm B` `KT-6` harness | Feeds **B2, B3, B5** |
| **B2** | `RayField-3D + Fovea3D` | `J1-T` `IoU 0.5/0.7`, `<1%` drop, FP spam, `SAM 3` removal | `6.0 GPU-h` | `DA3` stem + `DEV-MASK 117` | Feeds **B5** (`GeoVM`) |
| **B3** | `CertGeo-Loop` | `TT-BA +0.48°` NO-GO; weaponizes `reproj_p90` `0.898 AUROC` | `3.0 GPU-h` | `dev-S1` + `K1` `DA3` caches | Gates **B1, B5**; scales data `100×` |
| **B4** | `ChronoMetric-4D` | `DSI` `-33.3 pp` reversal cliff + 1-hr `HD-EPIC` memory | `8.0 GPU-h` | `492` `Point4D` stores (`0-13`) | Feeds **B5** (`MOTION_EXTRAP`) |
| **B5** | `GeoVM-Latent` | Brittle verbal CoT vs exact differentiable 3D algebra | `12.0 GPU-h` | `Qwen3.5-9B` + `DA3` surfels | Unifies **B1–B4** → `FlowExpert` VLA |
