# Clean-Sheet Manifesto: Metric Depth + Pose Heads, Unlimited Gemini Trace Engines, Verifiable Geometric RL, and Universal VLA Co-Training

## 1. First-Principles Thesis: One Euclidean Manifold Spans Every Spatial Question and Robot Action
Current geometry-aware VLMs plateau around 73–75% on VSI-Bench yet drop 15–22 points on ReVSI (e.g., 73.7 $\to$ 52.0) and transfer poorly to Vision-Language-Action (VLA) manipulation for four structural reasons:
1. **Semantic Shortcut Memorization:** Models trained on static room templates guess distances and sizes from object categories ("beds are 2.0 m") and 2D pixel area rather than measuring 3D geometry.
2. **Fragile Single-View Head Reads:** Naive tool/head routing queries one frame without checking depth boundary bleed, specular dropout, or narrow-baseline triangulation blowup ($\sigma_Z \propto Z^2 / (f B)$).
3. **Outcome-Only RL Collapse:** Rewarding only final VQA answers lets chain-of-thought (CoT) hallucinate plausible-sounding coordinates while guessing answers (collapsing ReVSI to ~30.5).
4. **The Room-to-Gripper Chasm:** Walkthrough scans (1.5–10 m, slow cameras, zero hands) omit manipulation geometry (0.01–1.0 m clearance, wide-FOV wrist cameras, articulated joints, dynamic contacts).

**The Unifying Primitive Hypothesis:** Equipped with **(1) a Metric Depth + Uncertainty Head** $(\hat{D}_t, \hat{\sigma}_{D,t})$, **(2) a Focal-Aware SE(3) Camera Pose + Covariance Head** $(\hat{K}_t, \hat{\mathbf{T}}_{\mathcal{W}\leftarrow t}, \hat{\Sigma}_t)$, and **(3) 2D Pixel/Mask Grounding** $(u,v,M_t)$, a single backbone can lift any observed pixel across time into a shared 4D metric world frame:
$$\mathbf{p}_{\mathcal{W}}(t) = \hat{R}_t \hat{K}_t^{-1} [u, v, 1]^\top \hat{D}_t(u,v) + \hat{\mathbf{t}}_t.$$
Every static spatial benchmark (distance, size, relative azimuth, room area, visibility census), every spatiotemporal query (camera trajectory, moving-object 3D velocity), and every robot manipulation primitive (6-DoF end-effector delta $\Delta \mathbf{T}_{\text{ee}} \in SE(3)$, obstacle clearance, hinge screw axis) reduces to deterministic operations on $\mathbf{p}_{\mathcal{W}}(t)$ and surface normals $\hat{\mathbf{n}}_{\mathcal{W}}(t)$.

**Dual-Speed VLA Backbone Architecture:**
- **System-1 (30–50 Hz Reactive Control & Direct VQA):** High-resolution geometry tokens from the depth+pose heads fuse into early/mid LLM blocks and feed lightweight **SE(3) Flow-Matching Action & 3D Affordance Heads** for zero-latency control.
- **System-2 (1–2 Hz Epistemic Spatial Reasoning & Subgoal Planning):** For multi-hop spatial QA, occlusion recovery, or novel manipulation instructions, the LLM emits typed geometric head queries (`<query_geom>`, `<zoom_crop>`, `<move_cam>`, `<emit_subgoal_se3>`), cross-checks multi-view 3D consistency across its own depth+pose heads, and outputs either a verified spatial answer or a metric target pose $\mathbf{T}_{\text{goal}} \in SE(3)$ for System-1 to track.

Below are **eight clean-sheet engines** exploiting unlimited Google Gemini API capacity (`Neon`, `Carbon`, `Argon`, `Flash`) + 4D reconstruction to train this unified model.

---

## Engine 1: Inverse-Geometric Program Synthesis & Epistemic Error-Recovery Factory
**(a) Core Idea & Pipeline**
Flip VQA generation from "ask a VLM to label videos" to **3D-first inverse program synthesis with real head-noise injection**. Across ScanNet++, ARKitScenes, Matterport3D, Waymo, and Ego-Exo4D, construct dense 4D scene graphs (metric meshes/TSDFs or bundle-adjusted DA3-Giant + ViPE + SAM3 + CoTracker3 tracks). Feed the 4D scene graph and multi-frame keyframes to Gemini, asking it to invent open-ended compositional spatial problems paired with **executable Python geometric programs** over 30+ typed operators (eroded-mask 3D surface-to-surface min-distance, local SE(3) frame rebasing, TSDF free-space raycasting for line-of-sight, alpha-shape floor area, oriented 3D bounding boxes, 4D trajectory curvature). Crucially, run **our current student's Depth and Pose heads** on every candidate clip during synthesis. Whenever a queried frame exhibits real student head error ($>0.20\text{ m}$ depth bleed, grazing angle $>70^\circ$, or pose drift), synthesize an **Epistemic Recovery Trace** where the trace queries two views, detects high 3D backprojection disagreement $\|\hat{\mathbf{p}}_{\mathcal{W}}^{(t_1)} - \hat{\mathbf{p}}_{\mathcal{W}}^{(t_2)}\|_2 > \tau$, diagnoses the bad view/edge, switches to a wider-baseline clean frame with 5-pixel mask erosion, confirms cross-view agreement, and computes the verified answer.

**(b) Exact Role of Unlimited Gemini API + Depth/Pose Heads**
- **Gemini Neon / Carbon:** Act as compositional problem architects and recovery-trace authors—turning raw 4D scene graphs + student head residual maps into diverse natural-language tasks and readable epistemic CoT programs (target: 5M verified traces).
- **Gemini Flash:** Paraphrases prompts into natural embodied instructions, audits referent uniqueness on RGB frames, and filters ambiguous phrasing at massive throughput.
- **Depth + Pose Heads:** Provide the exact numerical readouts (`eroded_median_3d`, `obb_extents`, `rel_pose_se3`, `depth_sigma`) inside every trace, teaching the LLM how to *audit* its own imperfect heads rather than blindly trusting single-pixel reads.

**(c) Expected Impact on Spatial Benchmarks AND VLA Transfer**
- **Spatial Benchmarks:** Directly closes the gap between GT-backed and predicted-head routing (+8 to +14 pts on ReVSI and VSTI camera/distance tasks) by eliminating single-frame outlier failures and semantic template overfitting.
- **VLA Transfer:** Gives System-2 VLA planners self-diagnostic spatial verification—catching bad wrist-depth reads on clutter edges before issuing a collision-inducing grasp waypoint.

**(d) Hidden Trap / Risk**
Synthesizing error-recovery traces from *artificial Gaussian noise* teaches useless heuristics because real head errors are structured (occlusion-boundary depth bleeding, pure-rotation scale drift, specular dropouts). Recovery traces must be mined exclusively from **out-of-fold real student head predictions** where multi-view inconsistency is genuinely observable from the student's own outputs.

**(e) Fast Decisive Pilot (48–72h)**
Run current student depth+pose heads + SAM3 on 2,000 ScanNet++ and ARKit clips. Have Gemini Carbon generate 60K verified Python-backed traces: 30K clean multi-view triangulations and 30K real head-disagreement recovery traces. Fine-tune for 500 steps and test paired accuracy on ReVSI dev + a corrupted-frame stress slice against static single-frame routed traces.

---

## Engine 2: Unified 4D Workspace-to-Room Corpus ("5-Meter Rooms to 5-Millimeter Grippers")
**(a) Core Idea & Pipeline**
Bridge architectural room scale ($2\text{--}10\text{ m}$) and manipulation workspace scale ($0.01\text{--}1.0\text{ m}$) by building a **3M-clip Metric Workspace-to-Room 4D Corpus** across DROID (76K stereo dual-cam trajectories), AgiBot-World (1M bimanual episodes), BridgeV2, OXE subsets, Ego-Exo4D, HD-EPIC, ManiSkill3, and Habitat. Reconstruct every clip with **DA3-Metric + ViPE + SAM3 + CoTracker3**, locking global metric scale $s^*$ to $\pm 1\text{ cm}$ via stereo baselines (DROID), Aria SLAM (Ego-Exo4D), or least-squares alignment between segmented robot links/gripper jaw widths and forward kinematics $\mathbf{T}_{\text{base}\leftarrow\text{ee}}(t)$ (OXE/BridgeV2). Extract four workspace task families: (1) **Cross-View Ego-to-Exo Registration** predicting $\mathbf{T}_{\text{wrist}\leftarrow\text{exo}}(t) \in SE(3)$ across $60^\circ\text{--}160^\circ$ baselines, (2) **Centimeter Clearance & Bottleneck QA** (gripper-to-obstacle clearance, container opening diameter vs object width), (3) **4D Object & End-Effector Point-Flow** $\Delta \mathbf{p}_{\mathcal{W}}(t \to t+k)$, and (4) **Contact-Phase Spatial Subgoal Decomposition**.

**(b) Exact Role of Unlimited Gemini API + Depth/Pose Heads**
- **Gemini Neon / Carbon:** Watch synchronized exo+wrist RGB videos overlaid with metric 3D tracks to segment manipulation phases (reach, pre-grasp align, grasp, lift, insert), write physically grounded clearance/subgoal QA, and verify reconstruction sanity (rejecting clips where tracked gripper contact disagrees with visual contact).
- **Depth + Pose Heads:** Supervised jointly on 5 mm gripper-object depth and extreme wide-baseline wrist-to-third-person SE(3) transforms, parameterized with **focal-normalized ray maps** $(\log(f_x/W), \log(f_y/H))$ so wide-FOV ($105^\circ$) wrist cameras and narrow-FOV ($65^\circ$) phone scans share one metric head without focal-distance confusion.

**(c) Expected Impact on Spatial Benchmarks AND VLA Transfer**
- **Spatial Benchmarks:** Boosts fine-grained object size, relative orientation, and multi-camera perspective benchmarks (MMSI, Ego-Exo QA, VSTI) by +6 to +10 pts via extreme wide-baseline SE(3) supervision.
- **VLA Transfer:** Eliminates workspace domain shift—giving multi-camera VLAs native metric fusion between static third-person cameras and moving wrist cameras from epoch 0.

**(d) Hidden Trap / Risk**
Mixing uncalibrated monocular OXE videos with wide-angle radial distortion into metric depth training corrupts global scale calibration. Enforce pinhole undistortion and train a binary `metric_scale_locked` mask: clips without stereo, SLAM, or kinematic link calibration supervise *scale-invariant relative depth + rotation* only, never metric scale.

**(e) Fast Decisive Pilot (48–72h)**
Process 5,000 DROID stereo-kinematic episodes + 1,500 Ego-Exo4D kitchen takes into 75K Gemini Carbon workspace clearance, $\mathbf{T}_{\text{wrist}\leftarrow\text{exo}}$, and subgoal traces. Co-train alongside room spatial QA and measure: (1) held-out wrist-to-exo pose error, (2) ReVSI zero-degradation check, and (3) 25-demo DROID Franka pick-and-place fine-tuning success vs room-only checkpoint.

---

## Engine 3: Process-Verified & Self-Calibrating Geometric RLVR ("Geo-RLVR")
**(a) Core Idea & Pipeline**
Replace outcome-only CoT RL (which rewards lucky answer guesses on hallucinated coordinates) with **Group Relative Policy Optimization over Live Head-Query Rollouts (Geo-RLVR)**. During RL rollouts, the policy dynamically invokes `{query_geom(frame, mask/pt), zoom_crop(frame, bbox), switch_anchor(frame), emit_answer}` against **its own live Depth + Pose + Uncertainty heads**. Every intermediate rollout step receives a deterministic, non-hackable reward computed in $<2\text{ ms}$ against cached 4D geometry:
$$R = R_{\text{ans}} + \lambda_1 R_{\text{ground}} + \lambda_2 R_{\text{triang}} + \lambda_3 R_{\text{calib}} - \lambda_4 C_{\text{queries}}.$$
Here $R_{\text{ground}}$ scores 3D proximity of queried masks to ground-truth target surfaces; $R_{\text{triang}}$ rewards **multi-view 3D backprojection agreement** across distinct frames; $R_{\text{calib}}$ applies a strictly proper scoring rule rewarding the policy when it distrusts high-$\hat{\sigma}$ head reads and switches/crops to cleaner views; and $C_{\text{queries}}$ penalizes redundant head calls once two views converge. Furthermore, **alternate RL policy updates with RL-focused head refinement**: log the exact pixels and wide-baseline frame pairs queried by winning rollouts and upweight depth/pose regression losses on those decision-critical states.

**(b) Exact Role of Unlimited Gemini API + Depth/Pose Heads**
- **Gemini Argon / Neon:** Generate 200K RL prompt curricula with verified ground-truth intermediate entity bindings and multi-step dependency DAGs, plus initialize cold-start rollouts on multi-hop problems where zero-shot sampling has $<5\%$ hit rate.
- **Depth + Pose Heads:** Act as the interactive environment inside GRPO rollouts; $R_{\text{triang}}$ even unlocks **unsupervised RL on raw unlabeled videos** using CoTracker3 point correspondences!

**(c) Expected Impact on Spatial Benchmarks AND VLA Transfer**
- **Spatial Benchmarks:** Prevents the SpaceR ReVSI collapse while adding +4 to +7 pts beyond SFT by optimizing frame selection, high-res cropping on small distant objects, and uncertainty-gated triangulation.
- **VLA Transfer:** Calibrates epistemic uncertainty—teaching the VLA backbone when its current 3D estimate is precise enough to execute a grasp vs when it must crop or acquire another view.

**(d) Hidden Trap / Risk**
**Degenerate Baseline Hacking:** If $R_{\text{triang}}$ rewards $\|\hat{\mathbf{p}}_{\mathcal{W}}^{(i)} - \hat{\mathbf{p}}_{\mathcal{W}}^{(j)}\|_2 \to 0$ unconditionally, GRPO immediately hacks it by querying adjacent video frames ($j = i+1$) where camera pose barely moved and depth errors correlate 1.0! Gate $R_{\text{triang}}$ strictly on ray-parallax separation $\Delta \theta_{ij} \ge 15^\circ$ (or $\|\Delta \mathbf{t}_{ij}\|/\bar{D} \ge 0.20$), assigning zero triangulation bonus to near-duplicate views.

**(e) Fast Decisive Pilot (48–72h)**
Run 300 GRPO steps on 15K ScanNet++/ARKit/DROID spatial prompts with pre-cached student head tensors, comparing `(a) Outcome-Only GRPO` vs `(b) Parallax-Gated Geo-RLVR`. Evaluate on ReVSI + unseen workspace clearance QA, measuring both final accuracy and mean 3D coordinate error of intermediate CoT steps.

---

## Engine 4: 3D-Consistent Counterfactual, Prior-Breaking & Virtual Wrist-Cam Engine
**(a) Core Idea & Pipeline**
Turn every posed 3D scene into 10x supervision while systematically destroying semantic size shortcuts via four **projectively exact geometric augmentations**:
1. **Focal-Crop Parallax Warps:** Crop and resample frames $I_t \to I'_t$ with exact pinhole intrinsics updates $K_t \to K'_t$, breaking "bounding-box pixel height = metric distance" shortcuts while preserving exact $(D_t, \mathbf{T}_t)$ consistency.
2. **In-Scene Non-Canonical Object Rescaling ("Prior Breaker"):** Inside 3DGS / ScanNet++ / simulation scenes, splice or rescale individual target objects by $\alpha \in [0.25, 3.0]$ inside standard-scale rooms/tables (e.g., a $0.35\text{ m}$ miniature chair or $0.45\text{ m}$ giant mug next to normal objects with metric camera translation). Semantic priors fail completely; triangulating depth+pose across views recovers exact dimensions.
3. **Arbitrary SE(3) Ego-Rebasing & Virtual Wrist-Cam Trajectories:** Re-anchor questions inside any object or gripper coordinate frame, and render smooth **virtual wrist-camera swoop trajectories** paired with fixed third-person views from high-res ScanNet++/tabletop 3DGS reconstructions.
4. **TSDF Swept-Volume Counterfactuals:** Exact raycasting and OBB sweeps answering counterfactual dynamics ("if the kettle moves $+0.25\text{ m}$ left, does it clear the toaster?", "which cabinet slot fits a $24\times 18\times 15\text{ cm}$ box?").

**(b) Exact Role of Unlimited Gemini API + Depth/Pose Heads**
- **Gemini Carbon / Flash:** Act as perceptual realism gates on 3DGS novel-view wrist renders (discarding splat floaters/holes) and rewrite counterfactual physics/clearance specs into natural manipulation and navigation queries.
- **Depth + Pose Heads:** Forced to compute scale from multi-view parallax and camera translation rather than memorized object class priors, directly supervising wide-baseline wrist+exo pose consistency on room scans.

**(c) Expected Impact on Spatial Benchmarks AND VLA Transfer**
- **Spatial Benchmarks:** Directly attacks the 15–22 pt VSI-to-ReVSI generalization cliff (+7 to +12 pts on ReVSI size, distance, and relative direction under unusual viewpoints).
- **VLA Transfer:** Pre-trains swept-volume collision checking, packing/placement fit prediction, and ego-wrist camera alignment across thousands of diverse real-world clutter layouts.

**(d) Hidden Trap / Risk**
**Projective Global Scale Ambiguity:** Never multiply global scene coordinates $(D_t, \mathbf{t}_t)$ by $\alpha$ while leaving RGB images $I_t$ and intrinsics $K_t$ unchanged—pure perspective projection $\pi(K R^\top (\alpha \mathbf{P} - \alpha \mathbf{t}))$ is invariant to global $\alpha$, creating an ill-posed supervision conflict! Always rescale *individual objects relative to metric surroundings* or adjust pinhole intrinsics $K'_t$ via physical crops.

**(e) Fast Decisive Pilot (48–72h)**
Generate 100K focal-crop + SE(3) ego-rebased + TSDF swept-volume QA rows and 20K in-scene rescaled-object scenes (BlenderProc/3DGS filtered by Gemini Flash). Train a 400-step ablation vs unaugmented data and test on ReVSI + an adversarial "miniature/oversized object" metric eval set.

---

## Engine 5: Multi-Teacher Adversarial Spatial Red-Teaming & Exact-Solver Flywheel
**(a) Core Idea & Pipeline**
Distilling a single frontier model caps student accuracy at that teacher's spatial ceiling (~61–77%). Break through frontier ceilings by coupling **Gemini Neon + Carbon + Argon + an Exact 3D Geometric Solver** in an iterative **Adversarial Red-Team Curriculum**:
- **Stage 1 (Failure Clustering):** Score our current student checkpoint on 100K 3D-reconstructed clips and cluster errors by geometric failure taxonomy (foreshortened perspective illusions, chiral $180^\circ$ turnaround left/right flips, moving-object vs panning-camera confounds, repetitive identical instances, grazing-angle depth spikes).
- **Stage 2 (Adversarial Twin Generation):** Gemini Neon inspects the 3D scene graph + student failure cluster and authors **hard-negative twin questions** on the same video—perturbing the reference frame or target timestamp so naive heuristics flip wrong—alongside surgical distractors matching classic sign bugs ($-R^\top \mathbf{t}$ vs $\mathbf{t}$, ego vs allocentric axes).
- **Stage 3 (Superhuman Geometry Mining):** The **Exact 3D Engine** computes undeniable ground truth. Neon, Carbon, and Argon attempt blind RGB-only rollouts. Items where *all three frontier VLMs fail blind* yet **our exact solver + head-backed trace succeeds** are upweighted 3x: Neon then receives the exact intermediate 3D coordinates to write a crystal-clear derivation showing *why* visual intuition fails and *how* head triangulation resolves the illusion.

**(b) Exact Role of Unlimited Gemini API + Depth/Pose Heads**
- **Neon + Carbon + Argon Ensemble:** Red-team proposer (Neon), blind difficulty calibrators (all three), and post-oracle pedagogical trace synthesizer (Neon/Carbon), scaled across continuous training rounds at zero API budget friction.
- **Depth + Pose Heads:** Provide the empirical geometric measurements enabling a 9B student to beat 100B+ frontier teachers on perspective illusions where raw visual tokens deceive human/VLM intuition.

**(c) Expected Impact on Spatial Benchmarks AND VLA Transfer**
- **Spatial Benchmarks:** Systematically hunts down tail failure modes each round (+5 to +9 pts on hardest cells: ReVSI allocentric direction, VSTI camera rotation/displacement, MMSI multi-camera).
- **VLA Transfer:** Eliminates chiral left/right coordinate inversions when a robot faces the camera ($180^\circ$ exo-to-base flip)—a notorious failure mode in language-conditioned bimanual manipulation.

**(d) Hidden Trap / Risk**
Unconstrained red-teaming drifts toward **unobservable or linguistically ambiguous trick questions** (2-pixel targets, heavy motion blur, or "the white chair" among three white chairs). Enforce automated **Observability & Referent Gates**: target SAM3 mask $\ge 400\text{ px}^2$ in $\ge 2$ frames, blind Carbon referent-uniqueness agreement $= 100\%$, and ground-truth metric margin between choices $> 3\sigma_{\text{GT}}$.

**(e) Fast Decisive Pilot (48–72h)**
Mine the top 5 failure clusters of our current checkpoint on dev scenes, run one Neon adversarial red-team + 3D-solver + Carbon/Argon blind-filter pass to produce 40K hard-negative twin traces, fine-tune 300 steps, and measure recovery on chiral flips and camera-motion cells.

---

## Engine 6: Universal Human-to-Robot SE(3) Action, Affordance & Articulation Bridge
**(a) Core Idea & Pipeline**
Convert **10,000+ hours of human egocentric manipulation video** (Ego4D, Ego-Exo4D, Epic-Kitchens, HD-EPIC, Something-Something-v2) plus articulated assets (PartNet-Mobility, ArtVIP) into **direct SE(3) VLA motor pre-training** inside our Depth + Pose coordinate frame:
1. **Ego-Motion Decoupled 6-DoF Hand Trajectories:** Run **HaMeR/WiLoR (3D MANO hand meshes)** + **ViPE/DA3-Metric** calibrated to true metric scale via anatomical hand-breadth priors ($8.4 \pm 0.6\text{ cm}$) and Aria SLAM where available. Subtract camera ego-motion $\hat{\mathbf{T}}_{\mathcal{W}\leftarrow\text{cam}}(t)$ so hand trajectories live in static world coordinates $\mathbf{T}_{\mathcal{W}\leftarrow\text{hand}}(t)$, then project into any query camera frame!
2. **Universal Pinch-Frame Retargeting:** Map thumb-index pinch midpoint $\mathbf{p}_{\text{pinch}} \in \mathbb{R}^3$, approach vector $\mathbf{a} \in \mathbb{S}^2$, closing axis $\mathbf{b} \in \mathbb{S}^2$, and normalized aperture $g(t) \in [0,1]$ directly onto an embodiment-agnostic **Parallel-Jaw / Dexterous End-Effector Frame** $\mathbf{T}_{\text{ee}}(t) \in SE(3)$.
3. **Contact Affordances & Post-Contact Articulation Screw Axes:** Track object part motion *after* hand contact via SAM3 + 3D point tracks to fit exact **Plücker screw parameters** $(\hat{\omega}, \mathbf{q}, \theta(t))$ for revolute hinges (doors, microwaves, laptops) and prismatic sliders (drawers). Co-train lightweight **3D Contact Affordance + $H$-Step Chunked SE(3) Flow-Matching Heads** directly atop the depth+pose visual tokens.

**(b) Exact Role of Unlimited Gemini API + Depth/Pose Heads**
- **Gemini Neon / Carbon:** Annotate fine-grained manipulation instructions, contact timestamps, grasp taxonomy (pinch, power, hook, bimanual), failure vs success outcomes, and functional affordance labels ("grasp kettle *by insulated handle*, not hot spout") across millions of clips.
- **Depth + Pose Heads:** Decouple head motion from hand motion (solving the classic egocentric optical-flow entanglement bug!) and anchor predicted SE(3) action chunks directly onto metric observed 3D surfaces.

**(c) Expected Impact on Spatial Benchmarks AND VLA Transfer**
- **Spatial Benchmarks:** Sharpens dynamic object tracking, part-level grounding, and kinematic motion prediction on VSTI, EgoSchema-Spatial, and HD-EPIC 3D benchmarks.
- **VLA Transfer:** Game-changing **5–50 demo sample efficiency**: downstream robot fine-tuning only adapts a thin embodiment offset $\mathbf{T}_{\text{robot}\leftarrow\text{pinch}}$ and velocity profile on top of an already-trained metric SE(3) manipulation policy!

**(d) Hidden Trap / Risk**
Humans execute compliant side/power grasps using five-finger friction that two-finger parallel grippers drop. Have Gemini Carbon tag grasp morphology on every clip and condition the SE(3) Flow-Matching Head on `embodiment_mode ∈ {parallel_jaw, dexterous_hand, suction}`, upweighting pinch/hook grasps for parallel-jaw VLA transfer.

**(e) Fast Decisive Pilot (48–72h)**
Extract 100K metric ego-motion-decoupled SE(3) pinch trajectories + articulation screw axes from Ego-Exo4D and Epic-Kitchens with Gemini Carbon task/grasp labels. Co-train the chunked SE(3) Flow-Matching head on our spatial VLM, then fine-tune on **10, 25, and 50 DROID / ManiSkill3 demos** (including articulated drawer/door opening) vs standard VLM init.

---

## Engine 7: Active Next-Best-View & Foveated 3D Information-Gain Policy
**(a) Core Idea & Pipeline**
Passive uniform frame sampling fails whenever target objects are occluded by clutter/robot arms or occupy $<20\text{ px}$ in wide shots. Because our model predicts $(\hat{D}_t, \hat{\mathbf{T}}_t, \hat{\sigma}_{D,t})$, any prefix of observed frames defines an explicit **3D Frustum Visibility & Uncertainty Field** (`Free`, `Occupied`, `Shadowed/Unobserved`). Train a unified **Active Spatial Perception Policy** across two regimes:
1. **Dense-Video Active Frame & Crop Retrieval (VQA Mode):** Given a cheap low-res pose/thumbnail strip of a 300–1,000 frame video, emit `<fetch_frames indices=[...]>` or `<zoom_crop frame=t box=[...]>` maximizing expected 3D triangulation baseline ($\Delta \theta \in [20^\circ, 60^\circ]$) and carving shadowed voxels around queried entities.
2. **Embodied Next-Best-View Camera Action $\Delta \mathbf{T}_{\text{cam}} \in SE(3)$ (VLA Mode):** From Habitat, ManiSkill3, and dense ScanNet++ view graphs, construct **Occluded Manipulation & Inspection Episodes** ("check if the mug behind the cereal box is empty, then grasp its handle") where optimal behavior first emits 1–2 metric camera movements $\Delta \mathbf{T}_{\text{cam}}$ maximizing target voxel information gain $\text{IG}(\Delta \mathbf{T}_{\text{cam}})$ before transitioning to `<exec_grasp>`.

**(b) Exact Role of Unlimited Gemini API + Depth/Pose Heads**
- **Gemini Carbon / Neon:** Author occluded inspection/search tasks over dense multi-view capture graphs and generate active-exploration rationales grounded in TSDF shadow maps ("the cereal box occludes $82\%$ of the counter behind it; move wrist camera $+12\text{ cm}$ right, yaw $-20^\circ$").
- **Depth + Pose Heads:** Supply the live frustum raycasting geometry and target 3D covariance $\text{tr}(\hat{\Sigma}_{\mathbf{p}})$ that drive both active frame retrieval and robot wrist-camera look-around control.

**(c) Expected Impact on Spatial Benchmarks AND VLA Transfer**
- **Spatial Benchmarks:** Breaks the uniform-32/64-frame visibility ceiling on long ScanNet/Ego4D videos (+5 to +8 pts on counting, small-object distance, and visibility-bound queries at equal full-res token budget).
- **VLA Transfer:** Unlocks **active occlusion-resolving VLAs** for mobile manipulators and wrist-cam arms—peeking around obstacles instead of grasping blindly into unobserved space.

**(d) Hidden Trap / Risk**
**Perception Procrastination Loops:** In closed-loop VLA control, an unpenalized information-gain policy oscillates the camera indefinitely chasing tiny uncertainty reductions. Enforce a calibrated **Value-of-Information (VoI) Stopping Rule**: emit `<move_cam>` *only* while target pose uncertainty exceeds grasp tolerance ($\sigma_{\mathbf{p}} > 2.0\text{ cm}$ or visibility $< 40\%$); once satisfied, lock into manipulation execution.

**(e) Fast Decisive Pilot (48–72h)**
On 1,000 dense ScanNet++ videos (all frames indexed) + 2,000 ManiSkill3 occluded-shelf episodes, train a 2-stage coarse-pose-scan $\to$ 16-frame active selector + $\Delta \mathbf{T}_{\text{cam}}$ head. Benchmark against uniform 32/64-frame sampling on VSI/ReVSI counting+distance and occluded-grasp success in ManiSkill3.

---

## Engine 8: Gemini-Architected Procedural Physics, Specular Depth & Articulation Factory
**(a) Core Idea & Pipeline**
Real RGB-D sensors and monocular teachers (DA3, G3T, ViPE) systematically fail on **transparent glassware, stainless-steel pots, mirrors, glossy wet sinks, wire racks, and interior container volumes**—causing depth heads to hallucinate straight through glass mugs on kitchen counters! Use **Gemini Neon/Carbon as Autonomous Procedural 3D World & Task Programmers** writing thousands of executable Python scripts over **BlenderProc, Isaac Lab, and ManiSkill3 + PartNet-Mobility / Objaverse-XL**. Synthesize 250K photorealistic multi-camera episodes featuring randomized PBR glass/liquid/metal/mirror materials, nested bowls, tight shelf passages, stacked unstable piles, and articulated appliances, exporting **true first-surface mesh depth** (replacing optical refraction dropouts!), exact SE(3) poses, exact Plücker joint axes, support-stability margins, and exact volumetric containment capacities.

**(b) Exact Role of Unlimited Gemini API + Depth/Pose Heads**
- **Gemini Neon (Code Architect) + Carbon (Visual Critic):** Neon writes diverse scene-layout, material-randomization, physics-perturbation, and camera-rig scripts; Carbon inspects rendered multi-view grids to reject mesh interpenetrations, floating assets, or unnatural lighting before generating verified spatial + VLA traces.
- **Depth + Pose Heads:** Supervised directly on **true surface depth of glass/specular objects and sub-centimeter clutter boundaries**, curing the #1 sensor blind spot of real-world RGB-D and pseudo-labeled datasets.

**(c) Expected Impact on Spatial Benchmarks AND VLA Transfer**
- **Spatial Benchmarks:** Boosts volumetric capacity, containment, physical stability, and specular indoor kitchen/bathroom scenes (+3 to +5 pts on tricky indoor slices).
- **VLA Transfer:** Prevents catastrophic gripper collisions on transparent cups, shiny utensils, and glass doors while supplying exact ground-truth articulation axes across 2,000+ appliance geometries.

**(d) Hidden Trap / Risk**
Over-weighting synthetic renders (>25% of mix) degrades real-world ViT texture representations. Cap procedural data at **15% of total training tokens**, apply real HDRI environment maps + realistic sensor noise, filter strictly via Gemini Carbon visual realism checks, and regularize ViT features against real video streams.

**(e) Fast Decisive Pilot (48–72h)**
Have Gemini Neon author 300 BlenderProc/ManiSkill3 kitchen-counter scripts with glass/steel mugs, pitchers, and articulated cabinets (30K clips filtered by Carbon). Co-train depth+pose+QA at 15% mix for 400 steps and evaluate depth RMSE + grasp-point 3D error on real transparent/metallic tabletop benchmarks (ClearGrasp / DROID kitchen glass subset).

---

## Summary Execution Roadmap: Stacking Order & Target Data Flywheel (~10M Rows)
| Priority | Engine | Target Scale | Primary spatial-VQA win | Primary VLA win |
|---|---|---|---|---|
| **P0 (Foundation)** | **E1** Inverse-Geom + Recovery & **E2** Workspace-to-Room 4D | 5M + 2M rows | Crushes GT-vs-own-head gap; wide-baseline SE(3) | Native exo+wrist metric fusion & cm clearance |
| **P1 (Generalization)** | **E4** Prior-Breaking Warps & **E6** Human-to-SE(3) Bridge | 1.5M + 1.5M rows | Eliminates 20-pt VSI$\to$ReVSI shortcut cliff | 5–50 demo robot transfer via 10,000h hand SE(3) |
| **P2 (Alignment)** | **E3** Parallax-Gated Geo-RLVR & **E5** Red-Team Flywheel | 150K RL + 200K/rd | Calibrated head routing; beats frontier teachers | Chiral flip immunity; calibrated grasp confidence |
| **P3 (Completeness)** | **E7** Active NBV Policy & **E8** Procedural Glass/Articulation | 400K + 250K rows | Breaks uniform-frame visibility ceiling | Active occlusion peeking; glass/hinge mastery |
