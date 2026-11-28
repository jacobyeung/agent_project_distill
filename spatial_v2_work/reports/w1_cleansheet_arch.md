# Clean-Sheet Architecture Manifesto: Depth & Pose Heads as a Unified 4D Spatial-VLA Backbone

## Thesis & Root-Cause Diagnosis
Current spatial VLMs bolt read-only depth/pose heads onto a causal 2D-ViT LM and call external 2D segmenters/3D towers (`SAM 3`, `G3T`) through lossy ASCII `<tool_response>` text. That ceiling (~65–75 VSI, ~58 ReVSI, weak VLA transfer) stems from four structural flaws: (1) **epipolar blindness** — causal attention forbids cross-frame triangulation and hides predicted 3D geometry from upper LM reasoning layers; (2) **grounding-geometry schism** — 2D masks drift across views while ASCII summaries discard topology, occlusion, and uncertainty; (3) **static-world & sparse-frame bias** — 32 rigid frames miss small objects and break on moving humans or robot arms; (4) **VLA latency/action mismatch** — 9B autoregressive tool calls cannot drive 30 Hz continuous 6-DoF control.

Below are **8 paradigm-shifting architectural breakthroughs** centered on **metric depth + camera pose heads** (plus minimal synergistic 3D heads) that push static/dynamic spatial QA toward oracle (>85 VSI / >70 ReVSI) and yield the strongest possible foundation backbone for downstream VLAs.

---

## 1. GeoLoop-VLM: Bidirectional Epipolar Mid-Trunk + Metric 3D-RoPE Feedback
**(a) Core Breakthrough & Mechanism**
Replace post-LM read-only heads with a **closed-loop mid-trunk geometry cycle** inside the 9B backbone (split at layer $L_{\text{geo}} = 12/36$). Layers $1..L_{\text{geo}}$ run **prefix-bidirectional alternating attention** (intra-frame self-attention interleaved with cross-frame global attention across all visual tokens $\mathbf{X} \in \mathbb{R}^{(T \cdot H_p W_p) \times d}$; text remains strictly causal). At layer $L_{\text{geo}}$, lightweight Depth + Pose/Intrinsics + Gravity heads predict per-frame $T_t = (R_t, \mathbf{t}_t) \in SE(3)$, $K_t$, metric depth $D_t(u,v) \in \mathbb{R}_+$, and epistemic log-variance $\sigma_t^2$. Every visual patch deterministically unprojects into a gravity-aligned canonical world frame:
$$\mathbf{P}_{t,u,v} = R_t^\top \big(D_t(u,v) K_t^{-1}[u,v,1]^\top - \mathbf{t}_t\big) \in \mathbb{R}^3, \qquad \mathbf{r}_{t,u,v} = (\mathbf{d}, \mathbf{o}_t \times \mathbf{d}) \in \mathbb{R}^6 \text{ (Plücker ray)}$$
Layers $L_{\text{geo}}+1..36$ swap 2D/temporal M-RoPE on visual tokens for **Metric 3D-RoPE**: partition head dimension $d_h$ into 4 continuous rotary subspaces $(P_x, P_y, P_z, t)$ with log-spaced frequencies $\omega_m \in [0.05, 50]\text{ rad/m}$ so dot-product attention $\mathbf{q}_i^\top R(\mathbf{P}_i)^\top R(\mathbf{P}_j) \mathbf{k}_j$ natively encodes exact 3D Euclidean displacement $\mathbf{P}_j - \mathbf{P}_i$. A zero-initialized gated MLP injects $[\mathbf{P}_i, \mathbf{r}_i, \log D_i, \sigma_i]$ into residual streams. Anneal gradient scale $\alpha(s): 0 \to 0.25$ through $\mathbf{P}$ so VQA and action losses directly sharpen mid-trunk geometry.

**(b) Spatial QA + VLA Transfer**
Upper LM attention directly reads metric distances, 3D alignments, and viewing rays across all frames with zero tool calls; for VLAs, wrist and third-person cameras automatically register into one shared metric robot-base frame inside attention, eliminating multi-camera extrinsics fragility.

**(c) Bottleneck Obliterated**
Eliminates causal epipolar blindness and the one-way wall between geometry heads and language/action reasoning.

**(d) Biggest Risk / Failure Mode**
Noisy early-training $\mathbf{P}$ corrupts pretrained LM attention via Metric 3D-RoPE phase jitter. Mitigation: zero-init residual gate + start with detached GT/teacher $\mathbf{P}$ annealing smoothly to predicted $\hat{\mathbf{P}}$.

**(e) Cheapest Decisive First Experiment**
Freeze a 9B VLM's ViT, add bidirectional visual mask on layers 1–12 + zero-init Metric 3D-RoPE on layers 13–36 fed by frozen teacher pointmaps vs. own mid-trunk depth+pose on a 20k VSI/ReVSI split; kill if Metric 3D-RoPE gains <+4 pts on direct relative/abs distance and direction-hard over standard M-RoPE.

---

## 2. Unified 4D Canonical World-State Head (Rigid $SE(3)$ + Depth + Residual 3D Flow)
**(a) Core Breakthrough & Mechanism**
Rigid multi-view geometry breaks whenever people, doors, or robot arms move. Add two minimal channels to the mid-trunk depth/pose head: per-patch **rigidity probability** $p^{\text{stat}}_{t,u,v} \in [0,1]$ and **canonical 3D world-frame scene flow** $\Delta \mathbf{P}_{t \to t+\delta} \in \mathbb{R}^3$ ($\delta \in \{-1, +1, +4, +16\}$). Any observed 3D point motion decomposes cleanly into ego-camera motion plus non-rigid residual flow:
$$\mathbf{P}^{\text{cam}}_{t+\delta} = T_{t+\delta} \Big( \mathbf{P}^{\text{world}}_t + (1 - p^{\text{stat}}_{t,u,v}) \Delta \mathbf{P}_{t \to t+\delta} \Big)$$
Mask multi-view pose reprojection supervision by $p^{\text{stat}}_{t,u,v}$ so moving arms/humans never corrupt camera pose $T_t$. Supervise $\Delta \mathbf{P}$ jointly from synthetic 4D datasets (Kubric/DynamicReplica/PointOdyssey), CoTracker3-lifted pseudo-tracks on Ego4D, and robot proprioceptive EE tracks.

**(b) Spatial QA + VLA Transfer**
Unlocks dynamic spatial QA (DSI-Bench, trajectory/speed/collision, appearance/motion order) without harming static VSI/ReVSI. For VLAs, **manipulation action IS future 3D point-flow**: predicting $\Delta \mathbf{P}_{t \to t+H}$ on the gripper and target object unifies internet human hand-object videos and robot teleop demos under one 4D geometric pretraining objective.

**(c) Bottleneck Obliterated**
Shatters the rigid-scene assumption that causes camera pose collapse on dynamic videos and prevents robot-arm/object dynamics transfer.

**(d) Biggest Risk / Failure Mode**
Scale-flow ambiguity (confusing camera translation with global scene flow when static background is small, e.g., close-up wrist cameras). Mitigation: enforce $\ell_1$ sparsity prior on $(1-p^{\text{stat}})\|\Delta \mathbf{P}\|$ + IMU/proprioception prior on wrist cams.

**(e) Cheapest Decisive First Experiment**
Train static-masked pose + 3D flow head on PointOdyssey + DynamicReplica + Ego4D pseudo-tracks (50k clips); kill if camera rotation/translation ATE on dynamic scenes does not drop >=30% vs. unmasked rigid pose head or if wrist-camera hand/object future-flow 3D EPE exceeds 5 cm.

---

## 3. Differentiable 3D Neural Scene Memory & Native Geometric Query Operators
**(a) Core Breakthrough & Mechanism**
Delete external `SAM 3` + ASCII `<tool_response>` plumbing. Fuse all unprojected visual tokens from Idea 1 into a **Canonical 3D Metric Voxel-Feature Cloud** $\mathcal{M} = \{(\mathbf{P}_v \in \mathbb{R}^3, \mathbf{f}_v \in \mathbb{R}^d, \sigma_v, \mathbf{t}_v)\}_{v=1}^{N_v}$ ($N_v \le 2048$, adaptive voxel pitch $\Delta \in \{0.05, 0.15\}\text{ m}$) via differentiable confidence-weighted scatter-mean: $\mathbf{f}_v = \frac{\sum_{i\in v} w_i \mathbf{h}_i}{\sum_{i\in v} w_i}$, $w_i = \exp(-\sigma_i^2)$. Give the LM four **native differentiable query tokens** whose hidden state $\mathbf{q} \in \mathbb{R}^d$ executes PyTorch geometric ops directly on $\mathcal{M}$ via soft voxel grounding $\alpha_v = \text{softmax}_v(\mathbf{q}^\top W_K \mathbf{f}_v / \sqrt{d})$:
1. `<q_locate>`: exact 3D centroid $\boldsymbol{\mu} = \sum \alpha_v \mathbf{P}_v$ and oriented bounding covariance $\Sigma = \sum \alpha_v (\mathbf{P}_v - \boldsymbol{\mu})(\mathbf{P}_v - \boldsymbol{\mu})^\top$ (eigenvalues = metric L/W/H).
2. `<q_measure>`: soft-min surface-to-surface and centroid-to-centroid Euclidean/Manhattan metric distance between two queried supports $\alpha^{(A)}, \alpha^{(B)}$.
3. `<q_count>`: build 3D spatial-semantic affinity $A_{uv} = \sqrt{\alpha_u \alpha_v}\exp(-\|\mathbf{P}_u - \mathbf{P}_v\|^2/2\tau^2)$; extract cluster count via differentiable normalized-Laplacian eigenvalue thresholding (collapses 50 views of one chair into exactly 1 3D entity!).
4. `<q_raycast>`: march $S=32$ points along $\mathbf{P}_A \to \mathbf{P}_B$ querying voxel occupancy density $\rho(\mathbf{x})$ for exact visibility, occlusion, and collision clearance.
Project operator outputs $[\boldsymbol{\mu}, \text{eig}(\Sigma), d_{\min}, \hat{c}, \text{occ}, \sum \alpha_v \mathbf{f}_v]$ via MLP directly into the next LM token embedding (end-to-end differentiable, zero text parsing).

**(b) Spatial QA + VLA Transfer**
Directly solves the four highest-ceiling QA categories (3D counting, metric distance, object/room size, occlusion/route) with native multi-view 3D entity binding. For VLAs, `<q_locate>` and `<q_raycast>` output exact metric 3D grasp coordinates, object OBBs, and collision-free corridor clearances with zero external segmentation latency.

**(c) Bottleneck Obliterated**
Obliterates 2D mask-to-3D lifting drift, multi-view double-counting, and external tool-harness latency/brittleness.

**(d) Biggest Risk / Failure Mode**
Soft attention $\alpha_v$ leaks mass onto distractor instances (e.g., two chairs), smearing $\boldsymbol{\mu}$ into empty space between them. Mitigation: run differentiable 3D spatial mean-shift / slot-competition over top-$K$ voxel modes before computing $(\boldsymbol{\mu}_m, \Sigma_m)$ per instance slot!

**(e) Cheapest Decisive First Experiment**
Freeze mid-trunk features + depth/pose on ScanNet/VSI val; train only $W_K$ and the 4 query MLPs (5M params, <4 GPU-h) on grounded 3D boxes/counts/distances; kill if `<q_locate>` + `<q_count>` does not beat external `SAM 3` + `G3T` lifting on abs-distance and counting on held-out rooms.

---

## 4. Counterfactual "Mental Camera" Head (Differentiable Egocentric Feature Splatting)
**(a) Core Breakthrough & Mechanism**
Perspective-taking ("standing at the lamp facing the sofa, is the desk left or right?"), route-planning turns, and pre-grasp collision checks fail in text CoT because rotating 3D frames in language tokens is unnatural. Exploit our existing canonical 3D feature cloud $\mathcal{M}$ by adding a **Mental Camera Token** `<mental_cam>` whose hidden state regresses a virtual camera pose $T_{\text{virt}} = (R_{\text{virt}}, \mathbf{t}_{\text{virt}}) \in SE(3)$ (or anchors directly to `<q_locate>` outputs: position $\boldsymbol{\mu}_A$, look-at $\boldsymbol{\mu}_B$, gravity-up $\mathbf{g}$). A fast differentiable z-buffered point/Gaussian feature splatter rasterizes $\mathcal{M}$ onto an $8 \times 8$ or $12 \times 12$ virtual ego-grid:
$$\tilde{\mathbf{F}}_{\text{virt}}(u,v) = \sum_{k \in \text{z-sorted}} \tilde{\alpha}_k(u,v) \prod_{j < k}\big(1 - \tilde{\alpha}_j(u,v)\big) \big[\mathbf{f}_k;\; z_k;\; \text{vis}_k\big]$$
Feed those 64–144 imagined egocentric feature tokens directly back into the LM as a short visual prefix! Train with ground-truth held-out real camera views (splat from frames $\{1..T\}\setminus \{t^*\}$ onto pose $T_{t^*}$ and match real ViT/mid-trunk features $\mathbf{F}_{t^*}$ via cosine loss) so imagined ego-views live in the exact same latent space as real camera frames.

**(b) Spatial QA + VLA Transfer**
Turns allocentric/egocentric perspective-taking, facing twins, direction-hard, and multi-step route navigation into trivial 2D left/right/front visual inspection from the imagined viewpoint. For VLAs, acts as an **instant 3D mental simulator**: splat from a candidate wrist pose $T_{\text{grasp}}$ to check clearance/contact before acting, or query poses maximizing unobserved voxel coverage for active perception (next-best-view)!

**(c) Bottleneck Obliterated**
Eliminates multi-step 3D frame-rotation hallucination in language CoT and gives VLAs counterfactual visual foresight without heavy video-diffusion latency.

**(d) Biggest Risk / Failure Mode**
Sparse holes or noisy depth spikes create smeared virtual views. Mitigation: include explicit binary coverage/confidence channel $\text{vis}_k$ in $\tilde{\mathbf{F}}_{\text{virt}}$ + lightweight 2-layer 2D ConvNet feature-inpainting refiner trained on real held-out view features.

**(e) Cheapest Decisive First Experiment**
Train only the 2-layer feature-inpainting refiner on ScanNet held-out views (<6 GPU-h), then evaluate zero-shot + fine-tuned `<mental_cam>` on VSI direction-hard & facing-twins; kill if imagined ego-views yield <+8 pts over direct text CoT on perspective-taking.

---

## 5. Test-Time Self-Supervised Bundle Adjustment & Active Frame Infill ("TT-BA")
**(a) Core Breakthrough & Mechanism**
Feed-forward depth+pose heads run open-loop and never notice scale drift, flipped rotations, or depth discontinuities. Yet RGB + depth + pose obey an exact, label-free physical conservation law: **multi-view geometric and feature reprojection consistency**. For overlapping frame pairs $(i,j) \in \mathcal{E}$ using L2-normalized mid-trunk patch features $\phi_t$:
$$\mathcal{E}_{\text{reproj}}(T, a, b) = \sum_{(i,j)\in\mathcal{E}} \sum_{u} p^{\text{stat}}_i(u) \Big[ \rho_\delta\big(\phi_i(u) - \phi_j(\pi_{i\to j}(u))\big) + \lambda_z \big|\log D_j(\pi_{i\to j}(u)) - \log z_{i\to j}(u)\big| \Big]$$
Execute a two-stage test-time closed loop before layers $L_{\text{geo}}+1..36$:
1. **Active Adaptive Infill**: Any frame/region where $\mathcal{E}_{\text{reproj}}$ spikes (rapid camera turn, blur, scale jump) triggers selective re-encoding at $2\times$ resolution or temporal midpoint-frame insertion *only in the uncertain interval* (128-frame precision at ~36-frame cost).
2. **Unrolled Differentiable Gauss-Newton (3–5 steps, <15 ms)**: Solve batched damped normal equations $(J^\top W J + \lambda I)\Delta \boldsymbol{\theta} = -J^\top W \mathbf{r}$ over pose tangent updates $\boldsymbol{\xi}_t \in \mathfrak{se}(3)$ and per-frame affine depth corrections $\tilde{D}_t = a_t D_t + b_t$ ($T_0=I$).

**(b) Spatial QA + VLA Transfer**
Eliminates catastrophic pose flips and scale drift on long/hard walkthroughs (ReVSI, camera displacement, room size) with zero external models. For VLAs, provides **online self-calibrating multi-camera extrinsics** — automatically re-aligning bumped wrist or head cameras during live deployment!

**(c) Bottleneck Obliterated**
Obliterates open-loop feed-forward geometry fragility and uniform frame-sampling waste.

**(d) Biggest Risk / Failure Mode**
Textureless walls or extreme baseline jumps create flat/local-minimum Jacobians that worsen a decent initial pose. Mitigation: Levenberg-Marquardt damping + strict acceptance gate (commit refined $(T^*, \tilde{D}^*)$ only if $\mathcal{E}_{\text{reproj}}$ drops by >10% and stays within a trust region of the feed-forward prior).

**(e) Cheapest Decisive First Experiment**
Implement 5-step batched PyTorch Gauss-Newton on existing depth+pose outputs over ReVSI + ScanNet++ val (zero training!); kill if camera ATE and scale-corrected abs-distance error do not drop >=15% on the worst quartile of scenes within <=25 ms latency.

---

## 6. Streaming 3D Recurrent Geometry Front-End ("Causal-3D-SLAM Trunk")
**(a) Core Breakthrough & Mechanism**
Batch-encoding 32 frames scales quadratically with video length, misses small objects in 3-minute walkthroughs, and cannot run at 30 Hz on robots. Replace the batch ViT + private ViT copy with a **~400M Streaming 3D Spatial Memory Front-End** (CUT3R/StreamVGGT-inspired) maintaining a fixed-size **Persistent Metric 3D Latent State** $\mathbf{S}_t \in \mathbb{R}^{N_s \times d_s}$ ($N_s = 1024$). At each incoming frame $t \in [1..512]$:
1. Shared ViT encodes frame $I_t \to \mathbf{v}_t$; $\mathbf{v}_t$ cross-attends to $\mathbf{S}_{t-1}$ to emit online metric depth $D_t$, camera pose $T_t$ in the running world frame, and reprojection novelty score $e_t$.
2. A gated 3D state update writes only genuinely new 3D geometry/semantics into $\mathbf{S}_t$: $\mathbf{S}_t = (1 - g_t) \odot \mathbf{S}_{t-1} + g_t \odot \text{CrossAttn}(\mathbf{S}_{t-1}, [\mathbf{v}_t, \mathbf{P}_t, \mathbf{r}_t])$ in $O(1)$ per frame (~8 ms/frame).
The 9B LM then ingests **only the 1,024 persistent 3D state tokens $\mathbf{S}_T$** plus top-8 question-relevant high-res 2D keyframes — delivering 256–512 frame coverage at **4× fewer LLM visual tokens** than 32 duplicated frames!

**(b) Spatial QA + VLA Transfer**
Eliminates the 32-frame visibility bottleneck on long VSI/ReVSI videos (capturing brief glimpses of small objects and smooth visual odometry across fast turns). For VLAs, provides an exact **30 Hz persistent 3D world memory** across arm/hand occlusions and multi-room mobile navigation!

**(c) Bottleneck Obliterated**
Breaks the quadratic $O(T^2)$ frame-count ceiling and decouples video/episode duration from LLM context cost.

**(d) Biggest Risk / Failure Mode**
Recurrent drift over 300+ frames or overwriting early objects when memory saturates. Mitigation: loop-closure keyframe cross-attention every 32 frames (using Idea 5's pose graph) + 3D spatial-slot partitioning so distinct physical regions own disjoint subsets of $\mathbf{S}_t$.

**(e) Cheapest Decisive First Experiment**
Fine-tune a pretrained streaming 3D encoder (CUT3R/StreamVGGT) to feed 1,024 state tokens into the 9B LM on 128-frame VSI/ReVSI videos; kill if 128-frame streaming state does not beat 32-frame batch ViT by >=+5 pts on small-object counting/visibility categories at lower LLM FLOPs.

---

## 7. Dual-Speed "Fast-3D / Slow-Geo" Unified Architecture (30 Hz VLA + 1 Hz Reasoner)
**(a) Core Breakthrough & Mechanism**
Spatial QA rewards deliberate multi-step metric reasoning (System 2), whereas manipulation requires 30–50 Hz continuous 6-DoF action chunks (System 1). Unify both cleanly in a **Mixture-of-Experts Dual-Speed Backbone** sharing one metric 3D perception trunk:
- **Shared Fast 3D Trunk (~1.5B active/tick)**: Streaming ViT + 3D State $\mathbf{S}_t$ (Idea 6) + Layers $1..L_{\text{geo}}$ + Depth/Pose/4D-Flow Heads + Metric 3D-RoPE (Ideas 1–2), emitting metric 3D tokens $\mathbf{H}_{\text{3D}}$ at 30 Hz.
- **System 1 — 3D-Equivariant Flow-Matching Action Expert (~300M params)**: Cross-attends to $\mathbf{H}_{\text{3D}}$, robot proprioception $\mathbf{q}_t$, and asynchronously cached System-2 3D subgoal $\mathbf{g}_{\text{plan}} = (\mathbf{e}_{\text{intent}}, T_{\text{target}} \in SE(3))$. Denoises continuous trajectory chunks $\mathbf{a}_{t:t+H} \in SE(3)^H \times [0,1]^H$ in 4 Euler steps (<18 ms) via conditional flow matching $\mathcal{L}_{\text{CFM}} = \|\mathbf{v}_\theta(\mathbf{a}_\tau, \tau \mid \mathbf{H}_{\text{3D}}, \mathbf{g}_{\text{plan}}) - (\mathbf{a}_1 - \mathbf{a}_0)\|^2$. Crucially, end-effector 6-DoF targets share the **exact canonical metric $SE(3)$ Lie-algebra frame** of the camera pose head — so every camera-pose gradient directly structures the robot action manifold!
- **System 2 — Full 9B Spatial Reasoner (Layers $L_{\text{geo}}+1..36$ + Ideas 3–4)**: Runs asynchronously at 1–2 Hz on robots (emitting updated 3D subgoals $\mathbf{g}_{\text{plan}}$ and verifying progress via Mental Camera / `<q_locate>`) and full-speed on VSI/ReVSI benchmarks.

**(b) Spatial QA + VLA Transfer**
Zero motor-latency penalty from 9B CoT, zero degradation of 9B spatial QA from continuous motor jitter, and direct mathematical transfer because System 1 consumes the exact metric 3D coordinates, poses, and future point-flow supervised by Spatial QA.

**(c) Bottleneck Obliterated**
Resolves the fundamental speed-vs-deliberation trade-off between foundation spatial reasoning and real-time closed-loop robot control.

**(d) Biggest Risk / Failure Mode**
System-2 subgoal lag (1 Hz) conflicts with fast reactive contacts (e.g., object slipping). Mitigation: train System 1 with random $\mathbf{g}_{\text{plan}}$ staleness (0.2–2.0 s) + force/proprioceptive reflex conditioning so System 1 recovers locally while System 2 replans.

**(e) Cheapest Decisive First Experiment**
Attach a 300M flow-matching action expert to the shared mid-trunk $\mathbf{H}_{\text{3D}}$ (with vs. without depth/pose/3D-RoPE pretraining) on LIBERO-Spatial + RoboCasa + VLN-CE; kill if metric-3D mid-trunk initialization does not yield >=+15% zero-shot/few-shot spatial generalization (novel camera viewpoints & object placements) over a 2D-ViT VLM baseline.

---

## 8. Spatial-Forcing²: Multi-Teacher 3D Absorption + Training-Only 4D Splatting
**(a) Core Breakthrough & Mechanism**
Carrying frozen external 3D towers (`G3T`, `SAM 3`) doubles memory/latency and keeps the VLM's native ViT geometrically blind. **Absorb** dense 3D foundation geometry permanently into the native VLM vision-to-mid-trunk weights on millions of **unlabeled** internet, egocentric, and robot videos (YouTube/Ego4D/Open-X/DROID) via two synergistic pre-alignment losses:
1. **Multi-Teacher Geometric Distillation**: Align mid-trunk visual hidden states $\mathbf{H}$ to frozen $\pi^3$/VGGT/Depth-Anything-3/CoTracker3 via patch cosine loss plus **cross-frame Gram correspondence distillation** $\mathcal{L}_{\text{gram}} = \|\tilde{\mathbf{H}}\tilde{\mathbf{H}}^\top - \tilde{\mathbf{H}}_{\text{tea}}\tilde{\mathbf{H}}_{\text{tea}}^\top\|_F^2$ alongside dense pointmap, raymap, and 3D track targets.
2. **Training-Only Differentiable 4D Gaussian Splatting Head**: Predict auxiliary per-patch Gaussian parameters $(\mathbf{P}_k, \Sigma_k, \alpha_k, \mathbf{c}_k)$ from the depth+pose+flow heads and differentiably rasterize held-out views $I_{t'}$ and future frames $I_{t+\Delta}$ (warped by $\Delta \mathbf{P}$):
$$\mathcal{L}_{\text{splat}} = (1-\lambda)\|I - \hat{I}\|_1 + \lambda\big(1 - \text{SSIM}(I, \hat{I})\big) + \lambda_{\text{lpips}}\text{LPIPS}(I, \hat{I})$$
Discard the Gaussian color/covariance head at inference! Every unlabeled robot or human video now supplies sub-pixel 4D metric depth, pose, occlusion-boundary, and motion supervision without LiDAR or mocap.

**(b) Spatial QA + VLA Transfer**
Deletes frozen external towers at deployment (halving inference cost), closes the native-vs-tower pose/depth gap (pushing own-head accuracy to G3T/$\pi^3$ parity), and turns 100M+ unlabeled egocentric/robot clips into direct 4D geometric pretraining for VLAs.

**(c) Bottleneck Obliterated**
Obliterates labeled-3D data scarcity (ScanNet/ARKitScenes ceiling) and the deployment tax of bolted-on external 3D vision towers.

**(d) Biggest Risk / Failure Mode**
Photometric splatting loss overfits lighting/exposure changes by distorting depth or hallucinating floating Gaussians. Mitigation: per-frame affine exposure calibration + depth-normal smoothness prior + co-training with metric teacher distillation $\mathcal{L}_{\text{gram}}$.

**(e) Cheapest Decisive First Experiment**
Run 10k steps of Spatial-Forcing² ($\pi^3$/DA3 Gram distillation + training-only novel-view splatting) on 100k unlabeled RealEstate10K + DROID clips on the native ViT + layers 1–12; kill if native pose/depth accuracy does not close >=75% of the gap to the frozen 3D tower on held-out ScanNet++ and DROID cameras.

---

## North Star Synthesis: One Unified Architecture
All 8 ideas compose without redundancy into a single clean-sheet **4D Spatial-VLA Foundation Model**:
```
RGB Stream (1..512 frames / wrist + 3rd-person)
  └─► [Idea 6: Streaming 3D State Front-End (O(1)/frame, pretrained via Idea 8 Spatial-Forcing²)]
        └─► [Idea 1: Bidirectional Mid-Trunk (L1..12)] ─► Depth + SE(3) Pose + [Idea 2: 4D Residual Flow]
              └─► [Idea 5: Test-Time 3-Step Gauss-Newton BA + Active Infill (<15 ms)]
                    ├─► Metric 3D-RoPE + Canonical 3D Feature Cloud M (<=2048 voxels)
                    ├─► [Idea 7 / Sys-1 (30 Hz)]: 300M SE(3) Flow-Matching VLA Action Expert
                    └─► [Idea 7 / Sys-2 (1 Hz / QA)]: 9B LM (L13..36) + [Idea 3: Differentiable 3D Ops]
                                                                       + [Idea 4: Mental Camera Splat]
```

## Prioritized Kill-Test Stack (Highest Signal-per-GPU-Hour First)
| Priority | Idea | Core Lever Tested | Decisive Pass Gate |
|---|---|---|---|
| **P0** | **#8 Spatial-Forcing²** | Native ViT/mid-trunk absorbs 3D tower geometry | Closes >=75% of native-vs-tower pose & depth gap on held-out scenes |
| **P0** | **#1 GeoLoop (3D-RoPE)** | Closed-loop 3D coordinates inside LM attention | >=+4 pts direct VSI/ReVSI over standard M-RoPE (zero tool calls) |
| **P1** | **#3 Diff. 3D Scene Ops** | Native voxel `<q_locate>/<q_count>/<q_measure>` | Beats external `SAM 3 + G3T` lifting on abs-dist & counting |
| **P1** | **#5 Test-Time BA** | Zero-training 5-step Gauss-Newton on own heads | >=15% drop in worst-quartile pose ATE & abs-dist error in <=25 ms |
| **P2** | **#4 Mental Camera** | Virtual ego-view feature splatting | >=+8 pts on direction-hard & facing-twins vs. direct text CoT |
| **P2** | **#6 Streaming 3D State** | 128–256 frame $O(1)$ map into 1,024 LM tokens | >=+5 pts small-object/long-video QA at lower LLM FLOPs than 32-frame batch |
| **P3** | **#2 + #7 4D Flow + Dual-Speed** | Residual 3D flow + 30 Hz $SE(3)$ action expert | >=30% dynamic ATE drop + >=+15% viewpoint-generalization on VLA benchmarks |
