# Geometry backends for the student's spatial programs

## Question

Should the student keep its frozen G3T geometry tower, learn a better metric correction, replace depth, or replace depth and pose together? The deciding evidence is benchmark points under the fixed routed programs, not a model's reconstruction leaderboard.

## Answer so far

Keep G3T as the primary baseline until a candidate beats its own depth head under the frozen primary family. That family contains fifteen VSI selector-mask hypotheses: five candidate-depth/G3T-pose-and-calibration arms on absolute distance, size and room, under the policy, with Holm correction. Every primary arm uses the common 51-grid because native G3T is unavailable. Native results remain secondary until a matched native G3T export exists. No full-cohort candidate result justifies an encoder or attention change.

With the fixed direct-answer fallback and GT masks, G3T scores 79.28 on absolute distance, 78.12 on object size and 78.41 on room size. With the deployed selector, it scores 66.48, 62.35 and 78.95. The corresponding V-C/GT-mask policy scores are 72.74, 65.24 and 75.57. The comparison must hold the fusion policy fixed; beating V-C with fuse-all is not enough.

The CPU kit tests MoGe-2, MapAnything, Depth Anything 3 and Pi3X. MoGe-3 is a CUDA-only reserve. Each candidate reconstructs 64 native frames before selecting the tower's exact 32 priced anchors.

## Evidence

- The lane is `/scratch/jjyeung/orch_cd/geo_bakeoff`. Its `out/CANDIDATES.md` records primary paper, repository and model-card sources with access dates. Its authenticated download ledger covers five checkpoints totalling 19.90 GB.
- `out/receipts/cpu_integrity_current.json` verifies eight baseline cells: two depth heads, two fusion rules and two mask settings. Each GT cell contains 7,353 questions on 312 ScanNet scenes and matches the authority's predictions and scores exactly. Each selector cell contains 3,138 paired rows on 76 scenes; all 2,986 non-room authority predictions match. Room questions are mask-free.
- Sixty-five unit tests pass in both source and portable runtimes. DA3 and Pi3X pass eight-frame CPU inference at their official resolutions. Four models pass CPU inference; MoGe-2 also passes a complete 64-frame reconstruction, native-depth storage and 32-anchor export.
- `out/receipts/native_cpu_integrity.json` authenticates that full CPU export, four derived hybrids, and native/51-grid pricing on the same 23 questions. This is contract evidence, not a model ranking.
- `GT_CEILING_DECOMPOSITION_20261111.md` and the `gt_ceiling` lane motivate the target. Its G3T clip-scale-aligned AbsRel is 0.021 and median per-frame log-scale variation is 0.021. V-C's corresponding values are 0.072 and 0.077. The approximate two-point-loss tolerance is below 0.05 log-scale noise for absolute distance and below 0.02 for room. G3T pose error is about 3.9 degrees and 9 cm.

The portable payload is `/scratch/jjyeung/geo_bakeoff_assets/kit`. It includes the runtime, model sources and weights, pinned programs, GT and selector inputs, eight baseline outputs, a 64-frame fixture, and 37 arm scripts. It uses about 30.75 GB of unique payload content. The source asset tree uses about 32.32 GB of unique inodes because weights are hard links. No tar archive is created on the source node.

## Options and controls

The primary queue runs MoGe-2, MapAnything, DA3 and Pi3X. MoGe-2 isolates metric depth; the joint models test cross-frame consistency and pose. MoGe-3 requires a separate CUDA admission.

Every candidate supplies a depth-with-G3T-pose arm. Candidate-derived clip scalars change G3T depth and translations together; a depth-only scalar is a separate consistency control. Per-frame affine corrections record positive scale fallbacks and frame abstentions rather than dropping scenes. Two equal-weight depth ensembles test complementary errors.

