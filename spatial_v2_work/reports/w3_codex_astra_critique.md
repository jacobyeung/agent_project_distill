**The portfolio is not launch-ready. Its strongest components justify controlled experiments; its claims of exact geometry, camera immunity, native 30–50 Hz control, and guaranteed VLA transfer do not.**

I read all five Wave-1 dossiers and eight available Wave-2 blueprints. **`w2_ttba_scale_calibration.md` is missing at the specified path.** Its assessment below uses the other blueprints’ TT-BA specifications. This audit verifies contradictions within the supplied reports; it does not independently verify code, current allocations, or dataset licenses.

**Kill-or-keep audit — 15 items**

1. **EpiAdapter + Spatial-Forcing² — CONDITIONAL GO (Fix Specific Flaw First).**  
   Frozen-Qwen pose probes are a demonstrated failure; unfrozen, pre-merger adaptation remains an experiment. Also, **58–77° measures translation-direction error**, not rotation; rotation is 71–93°. Neither these probes nor improved monocular depth establish that unfreezing will recover correspondence. Run a correspondence-native teacher/side-stem comparator from step 0; do not spend 2,000 steps before discovering that the proposed fallback is necessary. DA3/DINOv2 is **not proven indispensable**, and DINOv2 alone is not a calibrated geometry solver. Dense patch distillation deserves testing independently of the remaining architecture changes.  
   Evidence: `w1_heads_bottlenecks.md:17–33`; `w2_geoloop_trunk.md:46–57,116,123`.

2. **GeoLoop + Metric 3D-RoPE — DEFER (High Risk / Premature).**  
   Zero-initialized phase amplitudes preserve the original RoPE initially; the **simultaneously changed bidirectional attention mask does not preserve the original model**. Detaching erroneous coordinates stops their gradients but leaves their erroneous forward attention phases intact. The master/VLA variants replace M-RoPE without specifying the trunk proposal’s zero-amplitude protection. Moreover, learned geometry feedback, bidirectional attention, and RoPE change together, defeating attribution. Require separate ablations, cached-versus-full-forward parity, and language/grounding retention before promotion.  
   Evidence: `w2_geoloop_trunk.md:29,69–74,117,124`; `w2_vla_supercharger.md:31–37`; `w2_architecture_eval_master.md:52`.

3. **DeltaSLAM / native GeoDecay — KILL / REDUNDANT as specified.**  
   The stated state shape and multiplication order are inconsistent. Under the dimensionally consistent convention \(S\in\mathbb R^{d_v\times d_k}\), a normalized-key update gives  
   \[
   S_tk=\alpha(1-\beta)S_{t-1}k+\beta v.
   \]
   This is exact overwrite only when \(\beta=1\); sigmoid confidence does not guarantee it. RFF keys have approximately unit norm in expectation, not exactly, and distinct locations are not orthogonal. “8,192 slots” is not a demonstrated storage capacity. At token-wise retention 0.999, 500 frames ×130 patches attenuate untouched state by **\(5.7\times10^{-29}\)**. A linear ray aggregate is not a TSDF first-hit query. Parallel geometric heads protect original weights initially; they do not guarantee unchanged language behavior after training.  
   Evidence: `w2_radical_wildcards.md:18–27`; `w2_geoloop_trunk.md:77–79`.

4. **Native 2D boxes → masklets → persistent 3D slots — STRONG GO (Immediate Kill-Test).**  
   This has the strongest measured intervention: **GT boxes into existing SAM3 recover +11.0 points**. That validates localization as a bottleneck, not the proposed learned box predictor or removal of SAM3. Run box-tolerance and learned-box tests first. The latency table omits the LM-L16 noun-span computation; feeding resulting slots back into the LM input also needs a defined pass/cache strategy. Pairwise zero affinity alone does not enforce transitive must-not-link constraints, and 64 sampled surface points do not provide exact surface distance.  
   Evidence: `w1_heads_bottlenecks.md:48,67–73`; `w2_native_grounding_3d.md:65–85,92–96,113–117`.

5. **DA3 swap + TT-BA + Geo-Maj@K — CONDITIONAL GO (Fix Specific Flaw First).**  
   **DA3-only is the mandatory cheap comparator.** It has better reported pose/tail metrics, but superiority on every failed capture or downstream task is unproven. BA can refine a valid initialization; it cannot manufacture overlap, recover unobservable monocular metric scale, or guarantee escape from gross pose errors. Lower reprojection loss is not proof of more accurate geometry. The K5-S AUROC concerns numerical-path instability; it does **not** validate the proposed ray-versus-extrinsic trigger. Geo-Maj must align gauges/scales before fusion; cycle consistency is vacuous when all relative poses come from one consistent set of absolute poses. Test stability as a diagnostic before using consensus as training truth.  
   Evidence: `w1_heads_bottlenecks.md:21,35–37,126`; `w2_geoloop_trunk.md:74`; `w2_radical_wildcards.md:75–82`; `w2_architecture_eval_master.md:39`.

6. **4D rigidity + ego-decoupled point flow — CONDITIONAL GO (Fix Specific Flaw First).**  
   The stationarity rule is wrong: **high rigidity OR small endpoint displacement** can zero the speed of an object that moves out and back, or rotates in place. Thresholds calibrated only on stationary objects cannot establish mover recall. Accumulated noisy path length generally grows with the number of increments; the stated \(\sqrt T\) scaling confuses path length with displacement uncertainty. Sparsity and rigidity priors also do not make camera/object motion identifiable when static support disappears. Future scene-flow prediction needs causal inputs and action/intent conditioning before it can function as a controller.  
   Evidence: `w2_4d_dynamic_streaming.md:27–39,44–52`; `w1_split_breakthroughs.md:62–64`.

7. **Causal streaming memory + calibration-free cross-view registration — CONDITIONAL GO (Fix Specific Flaw First).**  
   External streaming geometry has evidence; the native constant-memory implementation does not inherit it automatically. A 1,024-voxel store cannot preserve arbitrary scene detail indefinitely without compression loss. The frame index and pose graph grow with duration, so constant LM context is not constant total memory/work. Restricting retrieval to \(t\le t_q\) is insufficient if poses, gravity, or loop closures already used future frames. Rotation continuity cannot recover missing translation observations. “Hold last calibration” also fails after a camera bump during low overlap.  
   Evidence: `w1_split_breakthroughs.md:30–32,61`; `w2_4d_dynamic_streaming.md:74–87,99–102`.

8. **SPLIT recovery SFT + GeoAPI + parallax-gated RLVR — CONDITIONAL GO (Fix Specific Flaw First).**  
   Bounded recovery SFT is well motivated by SPLIT’s measured +11.8-point advantage. The RL “anti-hack guarantees” are not valid: the **OR** baseline/parallax gate can admit poor triangulation, the formula does not explicitly exclude adjacent frames, and dropping answer supervision on unlabeled clips permits consistent wrong geometry. Broad centroid/IoU rewards can credit the wrong instance. Perturbing tool values while leaving RGB unchanged tests obedience to conflicting evidence; it must remain distinct from perceptual correctness. Finally, training with H900/D580 lexical skins invalidates claims that those same wording families remain unseen.  
   Evidence: `w1_split_breakthroughs.md:25–27`; `w2_split_internalization_rl.md:66,104–124,153`.

9. **Gemini factory + GeoSynth-∞ — CONDITIONAL GO (Fix Specific Flaw First).**  
   Keep the small, provenance-controlled pilot. Reject “zero geometry/sign errors,” transferred 96.9% precision, and million-row throughput as established facts. Exact arithmetic over biased reconstructions produces precisely computed wrong labels. A **uniform world-scale change leaves intrinsics unchanged**; image crop/resize changes intrinsics. Temporal reversal requires frame-consistent inverse transforms, not generally negating camera-frame translation. Clone/rescale edits require re-rendered visibility, contacts, and labels; correct twins still do not prove head use. Unlimited dollars do not remove API service-time, teacher-GPU, or human-audit bottlenecks.  
   Evidence: `w2_api_data_flywheel.md:24–28,77–95,148–160`; `w2_radical_wildcards.md:88–95`; `w2_architecture_eval_master.md:49`.

10. **Immediate Test L / Test N campaign — STRONG GO (Immediate Kill-Test).**  
    This supplies the missing evidence: **zero decisive student VLA GPU runs exist**. Measure B0/B1/U1 and N0/N1/NU after their unresolved GPU checks. U1−B1 tests the added perception/provider system, not native backbone transfer; B1−B0 addresses that separately. NU changes the action interface and controller assistance, so NU−N1 is not pure representation attribution. Keep observations, demonstrations, training budget, seeds, and evaluation episodes matched; report task/scene uncertainty and training-seed variability. None of the forecasts establishes even a 1-point SR improvement.  
    Evidence: `w1_vla_bridge.md:12,22–29,84–91`; `w2_vla_supercharger.md:115–119,127–137`.

11. **Dual-speed 30–50 Hz VLA / exact camera immunity — DEFER (High Risk / Premature).**  
    The fast path claims to execute only L1–12 while consuming taps **16,24,−1**. Those features require additional computation or explicitly stale caches. Four Euler steps do not establish end-to-end 25 ms latency, and fast execution of an action chunk is not fresh-observation closed-loop control. Camera-transform cancellation is an algebraic identity assuming correct geometry and corresponding visible points; learned calibration errors and occlusion do not cancel. The \(6\times10^{-8}\) m replay fit residual is not real-world perception accuracy.  
    Evidence: `w1_vla_bridge.md:17,23–24,42`; `w2_vla_supercharger.md:40,46–55,77–86`; `w2_architecture_eval_master.md:27,97`.

12. **MentalCam-3D — DEFER (High Risk / Premature).**  
    Its headline +74-point away-facing opportunity uses an obsolete baseline: R1 already reaches **91.3% away-facing** on the reported dev twins. Compare against the current checkpoint and deterministic coordinate readouts. Splatting observed surfaces can help canonicalization, but inpainting cannot certify hidden obstacles or unseen back faces. Camera invariance remains conditional on reconstruction and visibility. “Held-out views” used for training must mean views from training scenes, not evaluation rooms.  
    Evidence: `w1_student_state.md:48`; `w2_radical_wildcards.md:32–42`.

13. **Act4D-World — DEFER (High Risk / Premature).**  
    Camera displacement is not a sufficient manipulation action: identical camera motion can accompany different gripper forces, contacts, and object futures. Observational human video does not establish counterfactual robot dynamics. Pointmaps at different times also need correspondence/rasterization and disocclusion handling before elementwise prediction losses are meaningful. MPC can exploit precisely these learned-model errors. The 50K-clip teacher cache and 5K-step pilot are not demonstrated to fit 24 H100-hours.  
    Evidence: `w2_radical_wildcards.md:47–53`; `w1_vla_bridge.md:29`.

14. **GeoScratch — CONDITIONAL GO (Fix Specific Flaw First).**  
    **The written experiment contaminates its evaluation:** it trains on `dev-S1` and then measures its gain on `dev-S1`. Move training to clean rooms before any run. The unnormalized soft-min depends on mask mass and can yield negative “distances”; PCA covariance alone is not object extent, and radial hulls overfill non-star-shaped rooms. Removing text does not remove grounding ambiguity or taxonomy failures. Keep only primitives that pass independent numerical and perception checks.  
    Evidence: `w2_radical_wildcards.md:58–70`.

15. **ScrewVLA / human-hand SE(3) factory — DEFER (High Risk / Premature).**  
    An object trajectory does not fully specify feasible robot contact, reachability, friction, force, or collision avoidance. Jacobian pseudoinverse control does not supply those missing constraints. A fixed 8.4 cm hand prior cannot establish centimetre-accurate metric labels across people. LIBERO-Object/Goal pretraining also changes the data regime: “zero Spatial demos” is not zero robot demonstrations, and shared assets/tasks need an overlap audit. The proposed 10,000-hour pipeline would require roughly **23,000 teacher GPU-hours at the cited ViPE rate alone**, before hand tracking and other teachers.  
    Evidence: `w2_radical_wildcards.md:100–107`; `w2_api_data_flywheel.md:41–45`; `w2_vla_supercharger.md:61`; `w1_vla_bridge.md:29`.

**Contamination and benchmark validity**

- **Verified proposed violation:** GeoScratch trains and evaluates on `dev-S1`. The master additionally uses a ReVSI subset every 50 RL steps; that becomes development monitoring, not untouched final evaluation. Geo-Maj self-distillation must exclude evaluation queries and their source scenes.  
  Sources: `w2_radical_wildcards.md:70,79–82`; `w2_architecture_eval_master.md:83`.

- **Ancestor contamination matters:** the current student already trained on 75 ScanNet rooms represented in ReSTI. Excluding those rooms from new data cannot cleanse inherited weights; retain the documented restricted clean evaluation unless lineage provenance establishes otherwise. Synthetic edits of held-out rooms remain derived from held-out rooms.  
  Sources: `w1_vla_bridge.md:83`; `w2_api_data_flywheel.md:74`; `w2_radical_wildcards.md:88`.

- **Split policy is internally inconsistent:** the factory lists `R0-rl` as input while blocking “all 372 R0 rooms”; the RL blueprint describes 272 eligible `R0-rl` rooms. Resolve canonical-ID membership before generation. Ego-Exo/HD-EPIC exclusions must cover shared environments/captures, not merely renamed clips. Five planted canaries test the guard’s wiring, not the completeness of its exclusion list.  
  Sources: `w2_api_data_flywheel.md:23,32,70–75`; `w2_split_internalization_rl.md:88,100`.

- **Few-demo protocol:** use only authorized training demonstrations for LIBERO labels/caches; never generate training labels from +Cam evaluation rollouts. Separate additional robot-data pretraining from the five-demo adaptation count. No supplied report establishes dataset/API-upload/derived-data redistribution rights; **license legality remains unverified**, especially for the promised public corpus.  
  Sources: `w2_native_grounding_3d.md:101,117`; `w2_radical_wildcards.md:107`; `w2_architecture_eval_master.md:115`.

- **Headline comparisons are invalid as written:** full VSI cannot be declared superior to a VSI-500 reference; 5-demo LIBERO is not the cited 5%-data condition. A ReVSI target above 75 does not beat the documented frontier scores of 86.6/89.76.  
  Sources: `w1_student_state.md:29–40`; `w1_vla_bridge.md:84`; `w2_architecture_eval_master.md:108–115`.

**Lineage, compute, and wall-clock verdict**

Keep a **bounded Vehicle N reference**, but reject “cap-and-fork” as a mandate for an immediate wholesale rewrite. Existing VLA baselines can occupy H100s while V2 develops, so “clean cutover necessarily idles four H100s” is a false choice. A codebase rewrite and a model-architecture experiment are separate interventions. N’s projected scores remain forecasts, and its resume kit had not been run on Orchard in the student dossier. The newer inventory grants Orchard priority; the older capacity hold should not be presented as current.  
Sources: `w2_architecture_eval_master.md:12–23`; `w1_student_state.md:64–79`; `w1_compute_inventory.md:20–30`.

- **Budget deficit:** three manipulation arms ×18 plus three navigation arms ×27 = **135 H100-hours training**, plus the VLA blueprint’s **22 evaluation hours**. Master E02 budgets 96 training hours. Optional N-checkpoint arms add more.  
  Sources: `w2_vla_supercharger.md:118–119`; `w2_architecture_eval_master.md:37`.

- **Capacity is conditional:** 4+1 non-preemptible H100s provide a theoretical **1,680 GPU-hours over 14 days**; this does not validate a schedule that assumes 16–32 preemptible GPUs on its critical path. It needs an explicit five-GPU fallback, staging/evaluation time, and restart allowance.  
  Sources: `w1_compute_inventory.md:7–9`; `w2_architecture_eval_master.md:72–84`.

- **Timing arithmetic fails:** 4,000 steps at 4.5 steps/s is **0.247 hours**, not 14; 400 steps at 1.1 steps/s is **0.101 hours**, not 1.5. The advertised rates and budgets cannot both be correct.  
  Source: `w2_geoloop_trunk.md:104–106`.

- **Memory and restart claims need measurement:** under a common 16-byte-per-parameter mixed-precision Adam accounting, 9B/4 already consumes **33.5 GiB/rank before activations**. Fused CE does not prove 35 GiB full-training occupancy. Exact CPU resume does not prove durable upload inside a two-minute preemption window.  
  Sources: `w2_architecture_eval_master.md:14,23`; `w2_vla_supercharger.md:106`; `w1_student_state.md:75`.

- **Storage deadlines precede speculative training:** preserve Nov-29 scratch artifacts and Dec-01 `ae/` objects with verified destination completeness and lifecycle retention. Cloud-side copying avoids Trinity payload traffic; it is not automatically instantaneous or proof against expiry. Respect the existing heavy-IO approval rule. Keep bulk work off Orchard `/project` and `0-13:/scratch`; use `2-28:4–7` under `vnice`, and claim `0-13:6` only after release confirmation. NFS writes count double under the shared 30 MB/s limit.  
  Sources: `w1_compute_inventory.md:33–34,43–55,71–74`; `w1_student_state.md:82`; `w2_architecture_eval_master.md:59–67`.

**Collapse three proposals into one minimal architecture**

Combine **correspondence-feature injection/dense distillation**, **native localization with persistent instance slots**, and **the existing continuous U1/NU/action interfaces**. Share one depth/pose representation and one instance store. This directly connects the strongest grounding evidence to the hidden states and robot coordinates actually consumed downstream. RoPE surgery, DeltaSLAM, MentalCam, world-model MPC, and RL are separate experiments—not prerequisites.  
Sources: `w1_heads_bottlenecks.md:32,67–73`; `w1_vla_bridge.md:55–71`; `w2_native_grounding_3d.md:84–86`.

For **five-demo LIBERO and +Cam**, U1 and accurate native localization have the clearest testable mechanism. For **10% R2R-CE**, NU and causal pose history have the clearest mechanism. Dense distillation might improve bare-backbone transfer. Text recovery, geometric voting, and spatial-QA gains alone establish no robot SR gain.

**Top five actions for the next 72 hours, strictly ranked by qualitative information/lift per GPU-hour**

1. **Zero-training Trinity probes:** run J1-T, DA3-only versus G3T on the same failed/pass captures, and the missing VLA GPU admission checks. Add BA only as a separate paired arm. These resolve grounding tolerance, geometry failure, and executable-baseline uncertainty before expensive training.  
   Sources: `w1_student_state.md:71`; `w1_vla_bridge.md:24–29`; `w2_native_grounding_3d.md:113`.

2. **Orchard H100 baseline campaign:** launch matched B0/B1/U1 and N0/N1/NU after their required checks. Budget **135 H100-hours training + evaluation**, serialize on `advanced` if preempt capacity fails to materialize. This directly answers whether spatial training or explicit geometry improves robot success.  
   Source: `w2_vla_supercharger.md:115–119`.

3. **24/7 Gemini generation, initially bounded:** produce the proposed 10K trace/15K box pilot from verified clean inputs; prioritize wording coverage, real recovery failures, and localization. Audit by scene, object size, negative presence, and domain before scaling. Measure accepted throughput and teacher-GPU consumption; defer mass hand-trajectory generation.  
   Source: `w2_api_data_flywheel.md:148–160`.

4. **Short Trinity grounding training:** run Candidate 3 with the pilot labels and its ≤4 GPU-hour fail-fast check. Continue only if learned boxes recover downstream distance/target-localization value; oracle-box success alone does not qualify.  
   Sources: `w1_student_state.md:71`; `w2_api_data_flywheel.md:159`.

5. **One bounded representation experiment:** test dense correspondence injection/distillation against the pinned backbone, with the correspondence-native comparator ready immediately. Measure actual action-tap geometry and matched VLA transfer; postpone RoPE/DeltaNet changes. Use Orchard for full FT, Trinity only for demonstrated-fitting head/adapter work.  
   Sources: `w1_vla_bridge.md:55–61`; `w2_geoloop_trunk.md:116–118`.

**OVERALL_VERDICT: BLOCKERS_FOUND**

Five mandatory guardrails before affected GPU launches:

1. **Seal provenance:** resolve R0 membership, exclude evaluation scenes and derivatives, and remove train-on-`dev-S1`/ReVSI monitoring from held-out claims.
2. **Fix physical contracts:** consistent SE(3), reversal, scale/intrinsics, stationarity, and causal-state semantics; estimated teachers remain estimates.
3. **Prove execution:** real GPU memory/throughput, complete perception-to-action latency, and durable restart checks.
4. **Protect assets and allocations:** verify expiry rescue, honor IO gates/caps, use approved GPUs/wrappers, and keep preempt capacity optional.
5. **Preserve attribution:** pinned baselines, matched data/controllers, separate architecture ablations, and measured closed-loop SR before claiming VLA transfer.