# GeoLoop-Delta (`GD-Trunk`): Trunk-Native 3D/4D Geometry for Qwen3.5-9B & 30 Hz VLAs

**Goal:** Shatter the student's native pose plateau (`12.0°–17.9°` rot, `18.4°–20.1°` dir, `46–49%` / `77%` center error) without slow `18–25 s` external towers (`G3T`/`DA3`), and embed continuous metric 3D geometry directly inside Qwen3.5-9B's visual and mid-LM hidden states (`taps 16, 24, -1`) so both spatial QA and `QwenOFT`/`FlowExpert` VLAs win.

---

## 1. Root-Cause Surgery on the `~18–20°` Own-Pose Plateau

Reading `32` sparse `CAM` tokens from `Qwen3.5-9B` stalls at `~12–20°` while `G3T` (`2.72°` K1, `3.1°` SN) and `DA3 Nested` (`1.78°` K1, `0.043–0.064` raw metric AbsRel) succeed because **four coupled structural defects** choke epipolar geometry before it reaches upper reasoning layers:

| Structural Defect in Current `CarrierC1` (`Qwen3.5-9B`) | Verified Empirical Evidence (`w1_heads_bottlenecks`) | Exact Minimal Surgery in `GD-Trunk` |
|---|---|---|
| **1. Frozen SigLIP-lineage ViT erases epipolar phase** (`self.model.visual.eval()`; `320×416` -> `10×13` merged grid) | Frozen ViT probes stay at chance (`58–77°` dir, `71–93°` rot) even with `G=8` cross-frame transformer or `2×` px (`RES2`). Unfreezing private ViT `V-C` cut depth `AbsRel` `0.29 -> 0.10` and solved metric scale (`1.016×` GT). | **Unfreeze single shared ViT** (retire redundant `0.45B` `PrivateDepth` copy!) + pre-merger **`EpiAdapter`** (`6` alternating Frame/Global blocks, `d=768`, `85M`, `~11 ms`). |
| **2. Hybrid 24-DeltaNet / 8-Full-Attn causal wall** (`Qwen3.5-9B` has ONLY 8 full-attn layers `{4,8,12,16,20,24,28,32}` and 24 strictly causal Gated DeltaNet layers) | `1`-token `CAM` matches all `4,160` visual tokens at L16 (`29–30°`), and `IF-P0` (L1–8 vision branches) moves probes only `18.1° -> 15.5°`: 3 causal DeltaNet layers between each full-attn layer overwrite early-frame spatial keys across `4,160` tokens. | **Bidirectional visual prefix** on all 8 full-attn layers (`C1_C` hook) + **3D-key-addressed `GeoDecay`** turning upper DeltaNet layers (`17–31`) into a persistent 3D associative map. |
| **3. Sparse post-LM `pose9` loss + one-way head wall** (`32×9` scalars at L32; `C1-r` aligns only 32 `CAM` tokens; geometry never re-enters LM) | `C1-r` accelerates step 100 but hits identical `49%` center plateau; `GXC` input injection immediately halves dir error (`20.1° -> 9.8°`). Dropping heads (`B1`) leaves `taps 16, -1` geometry-blind. | **Spatial-Forcing² dense patch + Gram distillation** from `DA3 Nested` into LM **`taps 16, 24`** + **GeoLoop** L16 heads feeding **Metric 3D-RoPE** into L17–32. |
| **4. Hard-coded 32-frame video contract** (`group_embed[32]`, `frame_queries[32]`, `frame_layout: duplicate` sequential M-RoPE) | Cannot run `2` simultaneous VLA cams (`wrist_t + agent_t`) or unordered wide-baseline views (`MMSI`/`MindCube`/`Ego-Exo4D`). | **ViewSet-Unified** permutation-invariant `EpiAdapter`/`GeoPoseHead` + continuous view metadata `[is_video, Δτ_v, cam_id]`, supporting `N ∈ [2, 96]` views. |

---

## 2. `GD-Trunk` Architecture: Exact Tensors, Math & Dataflow

```
N RGB views (N ∈ [2..96], video OR simultaneous wrist+exo / multi-view)
  ├─► Shared Unfrozen Qwen3.5 ViT (0.45B; taps [9,17,25] pre-merger [N, 2Hm, 2Wm, 1152] + merged [N, Hm·Wm, 4096])
  │     └─► EpiAdapter (85M, 6×[Intra-Frame 2D-RoPE Attn -> Inter-Frame Global Attn], d=768, NO temporal index)
  │           ├─► Fine Geometry Map F_fine [N, 2Hm, 2Wm, 256]  (saved for L16 GeoDepthHead)
  │           └─► Zero-Init Linear(768->4096) residual into LM Layer 1 visual tokens + per-view [CAM_v]
  ▼
LM Layers 1..16 (Full-Attn {4,8,12,16}: visual prefix BIDIRECTIONAL via C1_C SDPA mask; Text strictly causal)
  │   [Train-only Spatial-Forcing² at L16: Patch Cosine + Cross-Frame Gram Distillation vs DA3 Nested]
  ▼
=== MID-TRUNK GEOLOOP SPLIT AT L_geo = 16 (Exact FlowExpert tap-16 & Qwen3.5 Full-Attn midpoint!) ===
  ├─► GeoDepthHead (18M): Fuses L16 visual [N,Hm,Wm,4096] + F_fine + FiLM(FoV) -> log D̂, log σ̂², p̂^stat
  ├─► GeoPoseHead  (32M): 4-layer bidir trunk on L16 [CAM_v] + pooled patch tokens -> 6D R̂_v, t̂_v, ĝ_v, FoV_v, Plücker rays r̂
  ├─► Optional TT-BA (<15 ms, test-time only when ray-disagreement flags ill-conditioned clips like ARKit)
  └─► Deterministic Gravity-Leveled Unprojection -> World P̂ ∈ R^3, confidence ĉ = exp(-½ŝ)
        ├─► Zero-Init Residual MLP(4.3M) -> H^(16)'_vis  (enters Layer 17; NO scalar tanh gate!)
        ├─► Zero-Init Metric 3D-RoPE -> Full-Attn Layers {20, 24, 28, 32}
        └─► GeoDecay Gate Bias + 3D-Key Addressing -> Upper DeltaNet Layers {17-19, 21-23, 25-27, 29-31}
  ▼
LM Layers 17..32  [Train-only Spatial-Forcing² at L24 + Delta3D-Probe at L19, L27]
  ├─► Spatial QA Output (causal text decode; KV-cache 100% standard; zero external towers!)
  └─► 30 Hz VLA Action Heads: FlowExpert reads enriched taps {16, -1}; QwenOFT reads tap -1 (heads droppable!)
```

### 2.1 Unfrozen Shared ViT + Pre-Merger `EpiAdapter` (`85M` new; `-450M` by retiring `PrivateDepth`)
- **Inputs:** Extract pre-merger ViT block outputs `[9, 17, 25]` at native `[N, 2H_m, 2W_m, 1152]` (`20×26` at `320×416`; `30×40` at `480×640`), fuse via per-tap `LayerNorm + Linear(1152, 256)` into `F_fine` `[N, 2H_m, 2W_m, 256]`, and `2×2` strided-conv downsample to `Z_0` `[N, H_m W_m, 768]`. Prepend one learned `[CAM_0]` register token per view (`Z_0 ∈ R^{N × (H_m W_m + 1) × 768}`).
- **Alternating Epipolar Attention:** `6` blocks, each running (1) **Intra-Frame Self-Attn** with 2D axial RoPE `(u, v)` + (2) **Inter-Frame Global Self-Attn** over all `N(H_m W_m + 1)` tokens with **zero 1D temporal RoPE** (strict permutation invariance across arbitrary camera sets!).
- **Zero-Init Residual into LM Layer 1:** Project output patches via `RMSNorm -> Linear_zero(768, 4096)` and add to merged Qwen ViT visual tokens; add projected `[CAM_v]` to each view's carrier token. Latency for `32 × 131 = 4,192` tokens in bf16 FlashAttn2: **`~11 ms`** on H100 / **`~14 ms`** on 6000 Ada.
- **Fallback Escape Hatch:** If KT-1A shows unfrozen SigLIP ViT + `EpiAdapter` plateaus `>8.5°` rot (patch stem phase loss), swap in a parallel **`86M` DINOv2-B/14 epipolar stem** feeding `EpiAdapter` (still `<20 ms`, zero `1.4B` tower).

### 2.2 Spatial-Forcing² Dense Patch + Gram Distillation at LM `taps 16` & `24` (`0` Test-Time Cost)
During training only, attach 2-layer MLP probes $P_l: \mathbb{R}^{4096} \to \mathbb{R}^{d_{\text{tea}}}$ at `l ∈ {16, 24}` (both full-attention layers; `16` is `FlowExpert`'s exact mid-trunk tap!). Teacher features $\mathbf{f}^{\text{tea}}$ come from offline-cached **DA3 Nested Giant-Large** (`1.40B`, `1.78°` rot, native metric depth; supplemented by **$\pi^3$** on dynamic/wide-baseline clips), area-pooled onto Qwen's `[N, H_m, W_m]` grid via `gf1.py:area_pool`:
1. **Dense Patch Cosine Alignment:** $\mathcal{L}_{\text{feat}}^{(l)} = 1 - \frac{1}{M}\sum_{i=1}^M \cos\big(P_l(\mathbf{h}^{(l)}_i),\, \text{sg}(\mathbf{f}^{\text{tea}}_i)\big)$.
2. **Cross-Frame Correspondence Gram Distillation:** Sample $K = 512$ visual patches stratified across all $N$ views; let $\tilde{\mathbf{U}}^{(l)} = \text{Norm}(P_l(\mathbf{H}^{(l)}_K)) \in \mathbb{R}^{K \times d_{\text{tea}}}$:
   $$\mathcal{L}_{\text{gram}}^{(l)} = \frac{1}{K^2}\left\| \tilde{\mathbf{U}}^{(l)} (\tilde{\mathbf{U}}^{(l)})^\top - \tilde{\mathbf{U}}^{\text{tea}} (\tilde{\mathbf{U}}^{\text{tea}})^\top \right\|_F^2$$
   Unlike `C1-r` (which aligned only 32 global `CAM` tokens), $\mathcal{L}_{\text{gram}}$ forces patch-to-patch epipolar similarity directly into `tap 16` and `tap 24` dot products!

### 2.3 Mid-Trunk Geometry Heads ($L_{\text{geo}} = 16$) & GeoLoop Metric 3D-RoPE Feedback
- **`GeoDepthHead` (`18M`, scale-decoupled):** Fuses bilinearly upsampled `Linear(4096, 256)(H^(16)_vis)` with `F_fine`, FiLM-modulated by predicted FoV $(\hat{f}_x, \hat{f}_y)$, followed by 2 lightweight `CrossFrameBlock` layers (`d=256`) and dual `3×3` conv readouts predicting:
  $$\log \hat{D}_{v,u,v'} = \underbrace{\tilde{d}_{v,u,v'}}_{\text{zero-mean shape}} + \underbrace{\mu_v}_{\text{per-view shift}} + \underbrace{\log \gamma_{\text{scene}}}_{\text{global metric scale}}, \quad \hat{s}_{v,u,v'} = \log \hat{\sigma}^2 \in [-6, 4], \quad \hat{p}^{\text{stat}}_{v,u,v'} \in (0,1)$$
  *Why decoupled?* Prevents `R1`'s `+1.38%` AdamW scale drift (zero weight decay on $\gamma_{\text{scene}}$) and allows exact kinematic (`U1` hand-eye) or floor-plane (`NU`) scale override on robots without perturbing depth shape (fixing `E0`'s `1.94×` Habitat drift).
- **`GeoPoseHead` (`32M`, 6D + Plücker rays):** `4`-layer bidirectional transformer (`d=768`, 12 heads, `key_mask` for arbitrary $N$) on `[Linear(4096,768)(H^(16)_cam) + mean-pooled H^(16)_vis]` with `4` adaLN iterative updates predicting per-view:
  - **6D continuous rotation** $\mathbf{r}_v \in \mathbb{R}^6 \xrightarrow{\text{GS}} \hat{R}_v \in SO(3)$ (eliminates `canon_unit_quat` antipodal sign flips!),
  - **Translation** $\hat{\mathbf{t}}_v \in \mathbb{R}^3$, **unit gravity up** $\hat{\mathbf{g}}_v \in S^2$, **bounded FoV** $(\hat{f}_{x,v}, \hat{f}_{y,v}) \in (10^{-4}, \pi - 10^{-4})$,
  - **Dense per-patch Plücker raymap** $\hat{\mathbf{r}}_{v,u,v'} = (\hat{\mathbf{d}}, \hat{\mathbf{o}}_v \times \hat{\mathbf{d}}) \in \mathbb{R}^6$ (`130×` richer spatial gradient per view than `pose9`!).
- **Gravity-Leveled Canonical Unprojection:** Define canonical world frame at View 1's center with $+z = \hat{\mathbf{g}}_1$ and $+y = \text{norm}(\mathbf{e}_{\text{fwd},1} - (\mathbf{e}_{\text{fwd},1}\cdot \hat{\mathbf{g}}_1)\hat{\mathbf{g}}_1)$. Transform all views into this frame and unproject every patch:
  $$\hat{\mathbf{P}}_{v,u,v'} = \hat{R}_v^\top \big(\hat{D}_{v,u,v'} \hat{K}_v^{-1} [u, v', 1]^\top - \hat{\mathbf{t}}_v\big) \in \mathbb{R}^3, \qquad \hat{c}_{v,u,v'} = \exp\!\big(-\tfrac{1}{2}\hat{s}_{v,u,v'}\big)$$
- **Closed-Loop Feedback into Layers `17–32` (Bit-Identical at Step 0):**
  1. **Zero-Init Residual Feature Injection (`4.3M`):** $\mathbf{H}^{(16)\prime}_{\text{vis}} = \mathbf{H}^{(16)}_{\text{vis}} + W_{\text{zero}}\,\text{MLP}([\text{Fourier3D}(\hat{\mathbf{P}}), \hat{\mathbf{r}}, \log\hat{D}, \hat{c}, \hat{p}^{\text{stat}}])$ (`W_zero = 0`, full-rank linear matrix — never scalar `tanh` gates, which froze `<0.04`!).
  2. **Zero-Init Additive Metric 3D-RoPE on Full-Attn Layers `{20, 24, 28, 32}`:** Preserve pretrained M-RoPE phase $\boldsymbol{\theta}^{\text{M-RoPE}}_i$ and add a continuous 3D phase shift with zero-initialized per-head amplitude $\boldsymbol{\beta}_h \in \mathbb{R}^{d_{\text{rot}}/2}$:
     $$\boldsymbol{\theta}^{\text{Geo}}_i = \boldsymbol{\theta}^{\text{M-RoPE}}_i + \boldsymbol{\beta}_h \odot \boldsymbol{\Omega}_{\text{3D}}(\hat{\mathbf{P}}_i), \qquad \omega_m \in [0.1, 20.0]\text{ rad/m}$$
     Partitioning $\boldsymbol{\Omega}_{\text{3D}}$ across $(P_x, P_y, P_z)$ lets dot-product attention $\mathbf{q}_i^\top R(\boldsymbol{\theta}^{\text{Geo}}_i)^\top R(\boldsymbol{\theta}^{\text{Geo}}_j)\mathbf{k}_j$ encode exact metric 3D displacement $\hat{\mathbf{P}}_j - \hat{\mathbf{P}}_i$ (text tokens set $\hat{\mathbf{P}}=\mathbf{0}$). Anneal teacher $\mathbf{P} \to$ student $\hat{\mathbf{P}}$ over first 30% of steps, then ramp straight-through gradient $\alpha_{\text{loop}}: 0 \to 0.20$.
  3. **Test-Time 3-Step Gauss-Newton Guard (`TT-BA`, `<15 ms`):** Triggered ONLY when ray-vs-extrinsic yaw disagreement exceeds `2.5°` (recall `K5-S` / yaw disagreement separates gross ARKit pose failures at `AUROC = 1.000`!). Runs 3 damped Gauss-Newton steps optimizing $(\boldsymbol{\xi}_v \in \mathfrak{se}(3), a_v)$ against `EpiAdapter` feature reprojection (masked by $\hat{p}^{\text{stat}}$); commits only if reprojection error drops `>10%`.

### 2.4 Turning Qwen3.5-9B's 24 Gated DeltaNet Layers into a Causal 3D Scene-State Accumulator
In each Gated DeltaNet layer, the fast-weight memory updates as $\mathbf{S}_k = \alpha_k \mathbf{S}_{k-1}(I - \beta_k \mathbf{k}_k \mathbf{k}_k^\top) + \beta_k \mathbf{k}_k \mathbf{v}_k^\top$. Previously, 2D semantic keys caused later views of an object to overwrite or blur earlier landmarks across `4,160` tokens. Once `H^(16)'_vis` injects $\hat{\mathbf{P}}_k$ into layers `17–31`, **same-3D-point patches across views produce collinear keys (automatic online 3D feature fusion!) while distinct-3D-point instances produce orthogonal keys (zero multi-view double-counting!)**. We actively unlock this with two tiny additions (`<0.2M` deployed):
1. **`GeoDecay` Gate Bias (Layers `17-19, 21-23, 25-27, 29-31`):** Add a zero-init linear modulation to the DeltaNet log-retention and write gates: $\Delta \log\alpha_k, \Delta \text{logit}(\beta_k) = W_{\text{gd}} [\log\hat{D}_k, \hat{c}_k, \hat{p}^{\text{stat}}_k, \|\Delta \hat{T}_v\|]$, keeping confident static landmarks persistent ($\alpha_k \to 0.999$) while suppressing blurry/moving frames ($\beta_k \to 0$).
2. **`Delta3D-Probe` Training-Only Supervision (Layers `19, 27`):** At each view's `[CAM_v]` output $\mathbf{o}^{\text{cam}}_v = \mathbf{S}_v^\top \mathbf{q}^{\text{cam}}_v$, supervise (a) cumulative causal ego-pose $T_{1\to v}$ (making $\mathbf{S}_v$ a real-time $O(1)$/frame 3D SLAM state for streaming VLAs!), and (b) **Frame-1 Coordinate Recall**: query $\mathbf{S}_{\text{end}}$ with a sampled frame-1 patch's 3D coordinate $\hat{\mathbf{P}}_{1,u,v}$ to reconstruct its semantic vector $\mathbf{h}_{1,u,v}$, directly penalizing long-horizon geometric forgetting!

### 2.5 Unified $N$-View / Multi-Camera Contract (`ViewSet-Unified`)
- **Zero Hard-Coded `32`:** Delete `group_embed[32]`, `frame_queries[32]`, and `frame_embeddings[32]`. Encode per-view metadata $\mathbf{m}_v = \text{MLP}([\text{is\_video}, \Delta\tau_v, \mathbf{e}_{\text{cam\_type}}])$ where `is_video=1, Δτ_v ∈ [0,1]` for continuous video (`8..96` frames) and `is_video=0, Δτ_v = 0` for simultaneous/unordered multi-view sets (`MMSI`, `MindCube`, `Ego-Exo4D`, LIBERO `[wrist_t, agentview_t]`).
- **M-RoPE Consistency:** For `is_video=1`, assign monotonically increasing temporal indices `t_v = v`; for `is_video=0`, share `t_v = 0` across simultaneous views (separated by `View k:` markers), letting `EpiAdapter` + `GeoPoseHead` register arbitrary wide baselines into View-1 or robot-base coordinates (`T_base<-wrist` kinematic override).

---

## 3. Exact Training Losses, Anti-Forgetting Recipe & Hardware Fit

### 3.1 Decoupled Loss Suite
$$\mathcal{L} = \mathcal{L}_{\text{VQA}} + 1.0\,\mathcal{L}_{\text{point}} + 0.5\,(\mathcal{L}_{\text{feat}}+\mathcal{L}_{\text{gram}}) + 0.4\,\mathcal{L}_{\text{depth}} + 1.5\,\mathcal{L}_{\text{pose}} + 0.4\,\mathcal{L}_{\text{ray}} + 0.4\,\mathcal{L}_{\text{pmap}} + 0.2\,\mathcal{L}_{\text{delta}} + 0.1\,\mathcal{L}_{\text{sem}}$$

- **$\mathcal{L}_{\text{depth}}$ (Scale-Decoupled + Aleatoric):** Laplacian heteroscedastic NLL $\frac{|r_i|}{\exp(\frac{1}{2}\hat{s}_i)} + \frac{1}{2}\hat{s}_i$ ($r_i = \log\hat{D}_i - \log D^{\text{gt}}_i$) + SILog ($\lambda=0.5$) + multi-scale gradient on shape $\tilde{d}$ + Huber scale loss on $\text{median}(r)$ (active ONLY on metric-GT datasets: ScanNet/++, ARKit, Hypersim, TartanAir; zeroed on uncalibrated web/robot clips).
- **$\mathcal{L}_{\text{pose}}$ (Pairwise All-Pairs $SE(3)$ + Gravity):** Over 256 stratified view pairs $(i,j)$ (covering short `0.2–0.5 m` and wide `>2 m` baselines): geodesic `SO(3)` rotation error + decoupled translation (cosine dir `1.0` + scene-normalized Huber `1.0` + log-baseline L1 `0.3`) + per-view and cross-view gravity consistency $\| \hat{R}_{ij}\hat{\mathbf{g}}_i - \hat{\mathbf{g}}_j \|_2^2$ + FoV Huber.
- **$\mathcal{L}_{\text{ray}} + \mathcal{L}_{\text{pmap}}$:** Confidence-weighted Huber on dense Plücker rays $(\hat{\mathbf{d}}, \hat{\mathbf{m}})$ and canonical 3D pointmaps $\hat{\mathbf{P}}$ (both scene-normalized and metric on metric-GT scenes), plus static-masked ($\hat{p}^{\text{stat}}$) photometric/feature reprojection on unlabeled videos.
- **Anti-Forgetting Guardrails:**
  1. **Semantic Anchor $\mathcal{L}_{\text{sem}}$:** Cosine loss keeping unfrozen ViT pre-`EpiAdapter` tokens close to frozen base ViT on 2D pointing/OCR rows (protects pointing from `f17`'s `75.9% -> 24.7%` erosion).
  2. **Differential LR & Zero-Decay Scale:** `ViT = 1e-5`, `LM = 5e-6`, `EpiAdapter/GeoHeads = 1e-4`, `Metric-3D-RoPE β_h = 5e-4`; `weight_decay = 0.0` on `γ_scene` and `β_h`.
  3. **Data Mix:** `Vehicle N` non-looping mix (`128` VQA + `64` routed + `64` pose/dense-3D + `32` pointing/box) + random-subset wide-baseline `2–8` view samples from ScanNet/++/ARKit + `MindCube-10K` (scene-audited).

### 3.2 Parameter Budget & Hardware VRAM Fit
| Component / Training Stage | Params (Deployed / Trainable) | Hardware Target | VRAM / Rank (Batch / Precision) | Latency / Throughput |
|---|---|---|---|---|
| **Deployed `GD-Trunk`** (retires `0.45B` `PrivateDepth`, `1.2B` `G3T`, `0.85B` `SAM3`) | **`9.14B`** (`-0.31B` vs bare `C1`; **`-2.50B`** vs `C1+G3T+SAM3`) | 1× H100 / 1× 6000 Ada | `~19.5 GiB` bf16 | **`<25 ms`** native 3D (vs `18–25 s` G3T = **`800×` faster**) |
| **Stage 1A: Vision + `EpiAdapter` + `GeoHeads`** (NO 9B LM in loop!) | `0.58B` trainable (`ViT 0.45B + Epi 85M + Heads 50M`) | **`trinity-2-28` 4× Ada 49GB (`vnice.sh`)** | **`~24 GiB/GPU`** (bs=2/GPU, 32f, bf16 + grad-ckpt) | `~4.5 steps/s` (`4k` steps in `~14h` wall; checkpoint/200 steps) |
| **Stage 1B: Trunk Warm-Start** (9B LM FSDP + `r=32` LoRA + full GeoLoop) | `~0.35B` trainable (`9B` bf16 sharded) | **`trinity-2-28` 4× Ada 49GB (`vnice.sh`)** | **`~28–32 GiB/GPU`** (FSDP ZeRO-3, grad-ckpt) | `~1.1 steps/s` (`400` warm steps in `~1.5h` wall) |
| **Stage 2: Full 9B Joint SFT** (`full_ft` + GeoLoop + SF² + Delta3D) | `9.15B` trainable (`+13M` train-only probes) | **Orchard `advanced` 4× H100 80GB** | **`~64 GiB/GPU`** (`-6 GiB` vs current `C1`!) | `~0.16 H100-h/step` (`400` steps = `~64 H100-h` = `16h` wall) |

---

## 4. Decisive 48–72h Kill-Test Ladder (Pre-Registered GO / NO-GO)

All three kill-tests run sequentially/overlapped across our immediately available footprint (**`trinity-2-28` 4× Ada `vnice.sh`**, **`trinity-0-13` 2× Ada unwrapped**, and **Orchard `advanced` 4× H100 + `general` 1× H100**) with **zero external towers at test time**.

| Test & Window | Cluster & Budget | Exact Experiment & Baselines | Primary Metrics & Eval Sets | Pre-Registered GO / NO-GO Bar |
|---|---|---|---|---|
| **KT-1: Native Pose/Depth Ceiling Break** *(Hours 0–18)* | **`trinity-2-28` 4× Ada 49GB** (`vnice.sh`, `~60 Ada-h`, `15h` wall) | **Stage 1A:** Unfrozen Qwen ViT + `EpiAdapter` + `GeoDepthHead` + `GeoPoseHead` + DA3-Nested patch/Gram distillation on `2–32` view ScanNet/++/ARKit clips (`4k` steps). **Baseline:** `R1 m400` own `CAM` (`12–18°` rot, `46–49%` / `77%` center) & frozen `G3T` (`2.7°` K1). | `K1-X` (48 rooms): rot°, dir°, center%, `AbsRel`, scale ratio. `dev-S1` 450 cam: disp/rot/dir. `LIBERO`/`MMSI` 2–5 wide-view pose. | **GO:** Held-out rot **`<6.5°`** (hard `<8.0°`), center error cut **`>=50%`** (`<23%` SN / `<38%` all), `AbsRel <= 0.085`, `|own/GT-1| <= 0.03`, `dev-S1` own-cam `>= 72/65/90` in `<25 ms`. **PIVOT:** If rot `>8.5°` at step 2k, swap in `86M` DINOv2-B/14 side-stem (`+7h`). |
| **KT-2: Trunk-Native QA Jump (`GeoLoop` + `3D-RoPE` + `Delta3D`)** *(Hours 18–40)* | **Orchard `advanced` 4× H100** (`~64 H100-h`, `16h` wall) + **`general` 1× H100** (`4h` eval) | **Stage 1B+2:** Graft KT-1 weights into `R1 m400` (`5083243c`) with `C1_C` bidir full-attn, L16/L24 Spatial-Forcing², L16->17 GeoLoop + Metric 3D-RoPE, `GeoDecay` + `Delta3D-Probe`. `100` warm + `300` full-FT steps on `Vehicle N` + multi-view mix. **Baseline:** `R1 m400` direct & own-head. | Paired `dev-S1` + `R0-dev` Direct-8, `VSTI-450` direct & own-cam, `ReVSI-999` Direct-5 (`64.94`), `VSI-Direct-6` (`68.77`) — **ZERO external towers**. | **GO:** Direct (zero-tool) VSI/ReVSI/VSTI jumps **`>=+4.5 pp`** (`+4–6 pp` target) on spatial categories; own-cam VSTI primary **`>=72.0`** (vs G3T `73.89`); `0` loops; pointing `>=65%` in-mask. **DIAGNOSTIC:** If Metric 3D-RoPE raises VQA loss `>+0.05` at step 100, detach $\hat{\mathbf{P}}$ ($\alpha_{\text{loop}}=0$). |
| **KT-3: Head-Dropped `B1` VLA Representation & LIBERO Proof** *(Hours 40–66)* | **KT-3A:** `trinity-0-13` 2× Ada (`8 Ada-h`, `4h`) <br> **KT-3B:** Orchard `advanced` (`18 H100-h`, `4.5h` + eval) | **KT-3A:** Drop ALL heads (test both `EpiAdapter-kept` and `LM-only` `B1`); freeze KT-2 vs `step 544` (`1d6eeb28`) & `R1 m400`. Train linear/2-MLP probes on **`taps 16, 24, -1`** for 3D `reach_base`, wrist↔agentview $SE(3)$, and patch depth. **KT-3B (if 3A passes):** Run sealed `vla_libero` `d5_s0` (`5` demos/task) `B1` (`QwenOFT` + `FlowExpert`). | **KT-3A:** `reach_base` 3D L2 (cm), wrist↔agent rot°/trans%, `tap-16` depth `AbsRel`. **KT-3B:** `500` LIBERO-Spatial + `376` LIBERO-Plus `+Cam` episodes. | **KT-3A GO:** `reach_base` L2 drops **`>=45%`** (`<=4.5 cm` vs `>9 cm` on `544`), wrist↔agent pose drops **`>=50%`** (`<8°`), `tap-16` linear `AbsRel <= 0.11`. **KT-3B GO:** Bare `B1` (zero external tower!) beats `544` `B1` by **`>=+8 pp`** on Spatial and **`>=+12 pp`** on `+Cam` shift. |

---

## 5. Risk Register & Mitigations
1. **SigLIP ViT Stem Phase-Loss Risk (KT-1):** Unfreezing Qwen ViT may adapt slowly on sub-pixel epipolar correspondence. *Mitigation:* Hard step-2k check (`rot > 8.5°`) triggers drop-in `86M` DINOv2-B/14 side-stem into `EpiAdapter` without changing LM/GeoLoop interfaces.
2. **Metric 3D-RoPE Attention Shock (KT-2):** Early noisy $\hat{\mathbf{P}}$ can perturb upper full-attention heads. *Mitigation:* Zero-init additive $\boldsymbol{\beta}_h$ (bit-identical step 0), 30% teacher-$\mathbf{P}$ annealing, and immediate $\alpha_{\text{loop}}=0$ fallback if step-100 VQA loss spikes.
3. **2D Pointing & OCR Erosion (KT-2):** Heavy 3D gradients on ViT can erode 2D localization (`f17` dropped `75.9% -> 24.7%`). *Mitigation:* $\mathcal{L}_{\text{sem}}$ cosine anchor to frozen base ViT on pointing rows + `1e-5` ViT LR + `32` pointing/box rows per step.
4. **Orchard `/project/community` Disk Exhaustion (`22 GiB` free):** Stage all KT-2/KT-3B checkpoints and cached DA3 targets on node-local `/tmp` (`6 TB` free) and stream durable exports to `gs://cmu-gpucloud-jjyeung`; run KT-1 and KT-3A entirely on Trinity local `/scratch` (`1.8 TB` free on `2-28`, streaming `0-13` artifacts over `.ib`).
