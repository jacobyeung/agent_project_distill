# Geometry-backend bake-off

## Decision and admission

The experiment asks whether another geometry source improves the student's fixed spatial programs enough to justify its inference cost. The primary baseline is the G3T head with the type-aware fusion policy, not the V-C head. No candidate has a full-cohort result yet.

The payload lives at `/scratch/jjyeung/geo_bakeoff_assets/kit` on trinity-2-18. Evalx owns its transfer and GPU execution. The run host is an argument, not a code constant. This lane uses no GPU, SSH, Git or paid API. GPU admission requires an explicit GO and one independent adapter review bound to the exact `KIT_SEAL.json` digest. Do not treat the CPU checks as a 64-frame CUDA memory test.

## Frozen comparison

- Every model consumes the same 64 native RGB frames. The exporter selects the tower's exact 32 priced anchors. Before admitting mirror videos, preflight compares all 64 decoded frames of scene0011_00 with sealed PNG references. Every frame must match exactly or exceed 45 dB PSNR. The real local video passes byte-for-byte. Per-frame RGB hashes bind each scene across candidates and resume. Only this scene has an independent sealed pixel reference; other scenes retain that limitation.
- The legacy export retains the tower's 51×51 grid, fields of view, gravity-frame camera poses, raw pose fields, frozen gravity convention and frame identities. Every candidate uses the frozen G3T predicted gravity; none uses GT to infer geometry.
- The reference programs are pinned v3.14 snapshots. Every arm runs fuse-all and the type-aware policy. VSI policy uses `best1` for object absolute distance, `voteb5` for other box questions, the fixed interior cut and the fixed room vote. VSTI-policy rows retain the frozen implementation but are labelled exploratory and in-sample; VSTI decisions use fuse-all. The policy and its thresholds were selected on G3T geometry, so the comparison favours that reference.
- GT-mask pricing covers 7,353 questions on 312 ScanNet scenes: 1,617 VSI and 5,736 VSTI items. Deployed-selector pricing covers 1,569 VSI questions on 76 scenes, with paired GT-mask and selector rows. Of those questions, 1,493 require masks and 76 room questions are mask-free. VSTI selector pricing is deferred because those masks are unavailable.
- Each report retains raw scores and the fixed direct-answer fallback. Secondary comparisons use 2,000 paired scene-cluster bootstrap draws with seed 20261111 against G3T and V-C. A program exception contributes its fallback score and an error count by type; only parity or membership failures invalidate pricing.
- Invalid input sources remain in `request.json` with their deferral reasons and the original requested denominator. Valid sources proceed. A partial-source result is conditional on its admitted subset, not a result for all 312 scenes. Program failures and unavailable depth do not silently remove questions.

### Primary family and resolution

`work/geo_bakeoff/protocol.py` freezes fifteen hypotheses: five candidate-depth/G3T-pose-and-calibration arms, each on VSI absolute distance, object size and room size, under the policy with selector masks and fixed fallback. Missing hypotheses, including an unrun MoGe-3, receive p=1. Incomplete cohorts cannot establish a primary win.

The video mirror must cover all 76 selector scenes for a model to qualify for a primary decision. A missing scene blocks that model's primary decision, and each incomplete hypothesis stays in the family with p=1. Absolute-distance items cover 75 scenes; size and room items cover all 76, so all 76 are required for the joint decision.

The primary representation is **the common 51-grid for every arm**. Native G3T is unavailable in this kit. Native candidate results are secondary, not a fair native-resolution architecture comparison against the cached grid.

`geo_bakeoff.family` reports 20,000-draw paired scene-bootstrap intervals and Holm-adjusted one-sided paired scene-randomization tests. It swaps whole scenes, not individual questions; small scene sets use exact enumeration, and larger sets use 100,000 permutations. A primary win requires adjusted p≤0.05 and a positive 95% paired lower bound. The intervals themselves are unadjusted.

A matched native G3T reference requires the tower producer to retain optical-Z depth before grid sampling, full source-image intrinsics, camera poses, the exact 64 frame identities and 32 anchor slots, and the frozen metric-scale/gravity rule. It must export in the same GPU run and use the same decoded-frame registry. Keeping 32 float16 depth rasters costs `312 × 32 × H × W × 2` bytes before compression: 4.05 GB at 392×518 or 6.13 GB at 480×640, plus small calibration/receipt files. If the tower already computes those rasters, this adds no model forward; transfer and serialization overhead remain unmeasured. The shared native cap still applies.

Evalx must provide that producer before a new seal can declare a native primary family. Report candidate native results against both G3T references when the native reference is authenticated. Until then, the native-G3T comparison is explicitly deferred rather than filled with grid results.

## Verified baseline

The source and portable-runtime suites pass 65 tests. The payload's `out/receipts/final_pricing_parity_integrity.json` verifies a fresh eight-cell, two-scene replay: all 800 predictions, scores and fallback values match. `out/receipts/final_native_resume_integrity.json` verifies the full-64 CPU exporter and explicit native/hybrid/pricing resume. Neither check claims CUDA capacity.

The eight baseline cells pass the independent membership, duplicate, score, fallback, summary and source-pin checks in `work/verify_cpu.py`. GT cells reproduce all 7,353 authority predictions and scores exactly. Each selector cell reproduces all 2,986 non-room authority predictions across its two mask regimes. The room rows use the mask-free program.

With GT masks, the G3T policy scores 79.28 on absolute distance, 78.12 on object size and 78.41 on room size. The corresponding V-C policy scores are 72.74, 65.24 and 75.57. With selector masks, G3T scores 66.48, 62.35 and 78.95. Absolute distance and room size beat their direct baselines; object size does not.

These headline scores use the fixed direct-answer fallback. Raw program scores remain separate.

The baseline quality target is strong. `gt_ceiling` reports median per-frame log-scale standard deviation 0.021 and clip-scale-aligned depth AbsRel 0.021 for G3T, versus 0.077 and 0.072 for V-C. Those AbsRel values include a fitted clip scale and must not be compared with unaligned candidate errors. Its tolerance tests place the approximate two-point-loss targets at log-scale noise below 0.05 for absolute distance and below 0.02 for room. G3T pose error is about 3.9 degrees and 9 cm. Room also needs a better global metric scale.

## Models and CPU evidence

`out/CANDIDATES.md` contains the primary-source comparison, access dates, weight sizes, available outputs, scale conventions, documented memory/speed claims and rejected alternatives. The payload includes five authenticated checkpoints totalling 19.90 GB.

1. **MoGe-2** tests metric depth and boundary quality without a new pose model. Its eight-frame CPU smoke passes. A separate CPU run processes all 64 frames, retains the 32 exact anchors and exports native float16 depth, consensus factors and diagnostics.
2. **MapAnything** tests joint metric geometry. Its eight-frame CPU smoke passes. Its predicted principal point is off-centre, so its 51-grid export is an explicit centre-projected approximation. Native pricing retains full predicted intrinsics. A native-depth/centred-calibration diagnostic separates calibration from sampling effects.
3. **Depth Anything 3** tests nested metric depth and pose. Its eight-frame CPU smoke passes. The loader fills only structurally proven shared-parameter aliases and otherwise requires a strict checkpoint match.
4. **Pi3X** tests multi-view consistency and pose. Its eight-frame CPU smoke passes. Its learned metric-scale behaviour still needs measurement on the full cohort.
5. **MoGe-3 is a reserve.** Its released refinement path requires CUDA. Its weights, source and NumPy-2 runtime overlay are staged, but CPU inference is unsupported. Evalx must obtain CUDA admission before treating it as a benchmark-ready candidate.

MoGe-2 and MapAnything pass relocated eight-frame CPU inference. DA3 uses its official 504-pixel input, and Pi3X uses its official 255,000-pixel sizing rule and Lanczos resize: 378×504 and 434×574 on the fixture. Their source-environment eight-frame checks pass in 138.43 s and 258.72 s at eight threads. These times establish execution, not GPU speed or quality. The full MoGe-2 CPU smoke uses 1,200 tokens; production requests 3,600.

## Arms and interpretation controls

`work/geo_bakeoff/arms.py` registers every executable arm; `launch/` contains one script per arm.

- `<model>_native` uses candidate depth and calibration. Joint models also supply pose; MoGe-2 and MoGe-3 use frozen G3T pose.
- `<model>_depth` uses candidate depth with G3T pose and calibration.
- `<model>_g3t_clip_scale` applies one candidate-derived scalar to G3T depth and camera translations together. `<model>_g3t_scale_depth_only` is the deliberately inconsistent depth-only control.
- `<model>_g3t_frame_affine` fits a robust per-frame scale and shift to candidate depth. Non-positive slopes fall back to a positive median-ratio scale; frames with fewer than 100 valid pairs abstain. Receipts list both cases, and scoring keeps the scene and questions.
- Calibration coefficients use the shared priced anchors, because the cached G3T depth covers those anchors. This does not change the models' 64-frame reconstruction. Per-frame fitting is independent across frames.
- `<model>_consensus` estimates relative temporal scales from all 64 native candidate predictions and camera poses before subsampling. It fixes the scale gauge without GT. Run this diagnostic only after a joint model demonstrates better pose; do not spend GPU time on it independently. The G3T-pose version has negative evidence from `gt_ceiling`, so the MoGe-2/MoGe-3 versions are not in the primary queue.
- `average_moge2_mapanything` and `average_mapanything_da3` use equal depth weights and require both pixels to be valid.
- The three `<model>_g3t_pose_candidate_calibration` controls hold candidate depth and calibration fixed while substituting G3T pose. Compare these with their joint native arms to attribute a gain to pose rather than intrinsics.

Hybrids and consensus use saved inference outputs and cost no additional model GPU time.

## Native depth and diagnostics

Pass one shared native root outside the kit and ordinary run output, on the declared run host. The writer stores compressed float16 anchors under a run/model namespace with unique immutable filenames. It keeps full intrinsics and a per-file SHA-256 receipt. Pricing verifies each file against the producing receipt and the native manifest. The 30,000,000,000-byte cap counts all namespaces and partial files; the writer reserves a 150 GiB post-export disk floor. All 64 predictions participate in temporal consensus before unused rasters are released.

Do not pool native results with 51-grid results. MapAnything additionally reports native depth with the legacy centred calibration. The primary G3T head baseline is its cached 51-grid export; this kit does not claim a matched full-resolution G3T decoder comparison. A gain confined to higher-resolution sampling calls for that comparison before adding an encoder.

The exporter measures depth AbsRel and delta-1 overall, inside object masks, and within one and five raster pixels of GT depth edges. It reports scale ratios, per-frame scale variation, pose errors and the scatter of lifted object centres. Native and 51-grid diagnostics state their raster sizes. Available ScanNet GT is 240×320; nearest-neighbour upsampling adds no GT detail. GT is used only for evaluation.

## Run order and GPU-hour reservations

Run MoGe-2, MapAnything, DA3 and Pi3X in that order. Admit MoGe-3 only after its CUDA-specific check. For each candidate, price native geometry and the depth/G3T-pose arm first, then the scale and affine arms. Run the calibration-held pose controls for joint candidates. Run ensembles and qualifying consensus diagnostics after the individual results.

These are planning reservations, not measured GPU performance: allow 0.5–2 GPU-hours for MoGe-2, 0.5–2 for MapAnything, 0.5–3 for DA3, 0.5–3 for Pi3X and 1–4 for optional MoGe-3 over 312 clips. Re-estimate from recorded first-clip time and peak allocated/reserved memory. Record CPU scoring time separately.

The first production scene is the full 64-frame CUDA admission, not a 32-frame substitute. Do not launch another candidate until that first receipt confirms execution and memory headroom. A failure stops the arm; never reduce the reconstruction to 32 frames to make it fit.

## Transfer and verification — evalx only

The payload has about 30.75 GB of unique content. Its source asset tree uses about 32.32 GB of unique inodes. Weights are hard links, not second copies. The source keeps more than 100 GiB free. There is no tar file on trinity-2-18.

Evalx checks the destination's free space, creates the destination directory after inspecting its parent, confirms `dev ib0` with `ip route get "$DESTINATION_IB_IP"`, and reuses its SSH master. The following is a transfer template for evalx on the source compute node, not an action for this lane:

```bash
tar -C /scratch/jjyeung/geo_bakeoff_assets/kit -cf - . |
  timeout 7200 ssh -o ConnectTimeout=10 -o BindAddress="$SOURCE_IB_IP" \
    "$USER@$DESTINATION_IB_IP" \
    'tar -C /scratch/jjyeung/geo_bakeoff_kit -xf -'
```

Use one direct InfiniBand tar stream. Do not relay through the head node, use `rsync` for this node-to-node payload, create a large local tar, or retry a killed/dropped transfer. Keep the native-video mirror separate from the payload.

On the destination, run the CPU verification before admission:

```bash
KIT=/scratch/jjyeung/geo_bakeoff_kit
unset GEO_BAKEOFF_ASSETS GEO_BAKEOFF_DATA_ROOT GEO_BAKEOFF_OUTPUT_ROOT
source "$KIT/work/kit_env.sh"
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
"$KIT/runtime/base/bin/python3" -m pytest -q "$KIT/work/tests"
"$KIT/runtime/base/bin/python3" "$KIT/work/verify_kit.py" --weights
"$KIT/runtime/base/bin/python3" "$KIT/work/verify_cpu.py"
```

The runtime pins the interpreter, data, assets and child working directory to the sealed bundle. It disables user-site packages, enables Python safe-path mode and rejects external input-root overrides. The preflight manifest is rebuilt and compared before reuse. Parent exports must match their summary/configuration receipts. Optional CLI, plotting, cloud-storage and audio dependencies declared by `evo` and `uniception` are not all installed; `PAYLOAD.json` records them. Actual inference paths define the portability gate.

## Launch commands — only after GO and independent review

The reviewer approves the final seal with a file under the destination kit's `inbox/` containing:

```text
APPROVED
kit_sha256: <SHA256 of the exact KIT_SEAL.json file>
```

The orchestrator supplies a separate inbox file with a standalone `GO` line. Evalx performs the cluster availability scan and sets `RUN_HOST` and `GPU`. Immediately before inference, the launcher checks the actual host and selected card. It refuses any compute PID or more than 1 GiB used and binds CUDA to the verified card UUID. This lane performs no live GPU query.

Set `VIDEOS` to evalx's complete native-video mirror. Set `RUNS` and `NATIVE` to new node-local roots. Use the same roots across arms so the hybrids can find their parents.

```bash
"$KIT/launch/moge2_native.sh" --video-root "$VIDEOS" --output-root "$RUNS" \
  --native-output-root "$NATIVE" --check-only

"$KIT/launch/moge2_native.sh" --video-root "$VIDEOS" --output-root "$RUNS" \
  --native-output-root "$NATIVE" --gpu "$GPU" --run-host "$RUN_HOST" \
  --go-file "$KIT/inbox/go.md" --review-file "$KIT/inbox/review.md" --skip-pricing

"$KIT/launch/moge2_native.sh" --output-root "$RUNS" \
  --native-output-root "$NATIVE" --price-only

"$KIT/launch/moge2_depth.sh" --output-root "$RUNS" --native-output-root "$NATIVE"
```

The native launcher runs under `/data3/shared/scripts/vnice/vnice.sh`. It records peak CUDA memory and per-scene time. Its first full-scene receipt is the CUDA check; do not run a separate probe into the same native namespace and then overwrite it.

Two eight-thread reservations cap this kit's concurrent compute. A per-card lock prevents two native arms using the same visible GPU. Pricing releases the GPU and uses four single-threaded workers. Evalx may score one finished arm while the next model infers, within those reservations and the cluster's total allocation.

The guard writes a BLOCKER to `$KIT/events/` after ten minutes without progress. Evalx must forward blockers. It never kills or retries jobs. `COMPLETE.json` binds the pricing-cell receipts and declares calibration, scope and deferred inputs.

After the required approval for any cluster-killed work, repeat the command with explicit `--resume`. The launcher checks the sealed epoch, source membership and native root. Exporters reuse verified scene receipts, preserve incomplete artifacts and recompute only unverified scenes. Pricing verifies scene checkpoints and completed cells. Attempt records preserve terminal receipts and logs. There is no automatic relaunch. The 5 GB lane limit applies to the kit/lane, not a separate production `RUNS` root; free-space floors apply everywhere.

After the primary cells finish, source `kit_env.sh` in the reporting shell before invoking the family module. The direct module command needs its sealed Python path, data root and safe-path settings:

```bash
source "$KIT/work/kit_env.sh"
"$KIT/runtime/base/bin/python3" -m geo_bakeoff.family --runs "$RUNS" \
  --out "$KIT/out/primary_family.json"
```

An authenticated native G3T policy/selector cell may be supplied with `--native-g3t-cell` for secondary comparisons. It does not change this seal's 51-grid primary family.

## Pre-registered reading and next training leg

1. **Keep G3T and test a scale head** if a GT-free correction's paired 95% lower bound exceeds zero on a target type, all other target lower bounds are at least −2 points, and full geometry's added gain over that correction has its entire interval inside [−2,+2] on all three types. An affine-only result motivates a temporal scale/shift head. This is a secondary training hypothesis, not a corrected model win.
2. **Swap the depth source** only if the registered depth/G3T-pose-and-calibration arm passes Holm at 0.05, its paired 95% lower bound exceeds zero on a target, and both other target lower bounds are at least −2 points. Use that depth for teacher supervision before changing the student encoder or attention.
3. **Test replacing pose too** if joint geometry beats the calibration-held G3T-pose control with a positive paired 95% lower bound, both other target lower bounds are at least −2 points, and paired scene intervals for rotation, translation and centre-scatter error differences all have upper bounds below zero. Use VSI selector rows. This is secondary evidence for joint supervision, not a primary-family win.
4. **Keep the tower** when no candidate meets the corrected depth criterion. V-C-only, GT-mask-only, VSTI-policy or GT-scale-fitted gains do not satisfy it. A native-only gain requires the matched native G3T comparison.

Report every tested arm and its input coverage. Do not choose a winner from a one-clip smoke, pool approximate and native calibration, or call the paired intervals a held-out architecture-selection guarantee.

## ARKit-100: frozen sample, deferred pull

`out/arkit100_manifest.json` fixes 100 training captures from 1,480 by a deterministic hash order. It fixes 3,200 exact sensor anchors and requests 6,400 distinct native RGB frames. Extra timestamps that lack native archive evidence remain unresolved. All 100 captures stay in the denominator and are explicitly deferred; no RGB has been staged.

After the orchestrator decides that ScanNet warrants the transfer, evalx resolves the declared archive members and timestamps, checks capture/GT hashes, and pulls one approved archive at a time with the download/storage limits. Raw archive byte sizes are unknown, so obtain a size receipt and approval before that pull. The canonical decoded RGB budget is 5,898,240,000 bytes at 640×480; the PNG budget is 6.5 GB. The fixed K6 rotation and image transform must preserve calibration and all 64 source identities.

This is a raw-geometry transfer test, not VSI benchmark points on a training capture. VSI's ARKit validation geometry remains deferred because sensor depth is unavailable. Do not report its known tower scale ratio of 1.245 as a candidate result or substitute 32-frame replay.
