# Geometry adapter review

## Requested decision

Approve or reject GPU admission for the sealed portable kit after reviewing its geometry, scoring and admission adapters. No GPU result or model winner is claimed. The orchestrator owns review assignment; this lane launches no reviewer or paid API.

The payload is `/scratch/jjyeung/geo_bakeoff_assets/kit`. `KIT_SEAL.json` binds code, model sources, fixed scoring inputs, baseline outputs, runtime records and authenticated weight receipts. The final digest appears in `out/receipts/kit_seal.json` in the lane. Approval must name that exact digest. `out/RUNCARD.md` defines the comparison and operating procedure.

This is the same reviewer's delta check of the eleven findings in the lane's `REVIEW_VERDICT.md`. Evidence paths below refer to the lane unless labelled as payload paths. Review `inputs.py`, `provenance.py`, `resume.py`, `admission.py`, `protocol.py`, `family.py`, `native.py`, `exporting.py`, `pricing_policy.py`, `backends.py`, `smoke.py`, `io.py`, `guard.py`, `run_arm.py`, `kit_env.sh`, `launch.sh` and their tests. Reference-program bytes and geometry conventions remain pinned.

## Evidence to inspect

- `out/receipts/cpu_integrity_current.json` verifies all eight baseline cells against their authority. GT cells each contain 7,353 items on 312 scenes. Selector cells each contain 3,138 paired rows on 76 scenes and match 2,986 non-room authority predictions.
- `work/tests/` exercises the export contract, frame identity, shared checkpoint aliases, paired bootstrap, native calibration/storage, temporal consensus, affine failure handling and guarded launch primitives.
- `out/receipts/portable_cpu_integrity.json` in the lane authenticates all four relocated eight-frame CPU paths: MoGe-2, MapAnything, DA3 and Pi3X. It verifies frame membership, native array shapes, finite depth and both export and native-output hashes. MoGe-3 cannot run on CPU. None establishes 64-frame GPU memory capacity.
- `out/exports/moge2_native_verified/summary.json` covers a real 64-frame CPU reconstruction with 32 exact anchors. Its native archive, dense poses/scales and diagnostic files have separate SHA-256 receipts.
- The native and 51-grid pricing smokes each cover the same 23 questions. They test adapter execution, not model quality.
- `PAYLOAD.json` records the runtime closure and absent optional package dependencies. `out/receipts/kit_integrity.json` in the payload is the portability check. Require its current seal digest before admission.

## Review these boundaries

1. **Frame and camera contract:** `work/geo_bakeoff/contract.py`, `inputs.py` and `exporting.py`. Check optical-Z depth, camera direction, quaternion order, metric translation scale, first-camera gauge, frozen G3T gravity, exact 64-frame identities and the 32 anchor slots. The legacy interpolation preserves the authority's arithmetic order.
2. **Model adapters:** `backends.py`. Check source-image transforms and focal scaling. DA3's loader may expand only aliases of the same live parameter; missing unrelated keys must fail. All inference uses staged assets offline, without GT.
3. **MapAnything calibration:** full intrinsics survive native storage and lifting. The legacy centre projection is labelled approximate. The candidate-depth/G3T-pose arm keeps G3T calibration; the pose counterfactual separately holds candidate calibration fixed.
4. **Native geometry:** `native.py`. Check half-pixel resampling, metric float16 storage, frame/shape checks and retained intrinsics. Native and 51-grid scores stay separate. Full-resolution G3T is not claimed from its cached 51-grid baseline.
5. **Hybrid semantics:** `hybrids.py` and `arms.py`. A clip scalar changes depth and translation together; the depth-only control is separate. Affine fitting records positive scale-only fallbacks and frame abstentions rather than dropping scenes. Temporal consensus fits all 64 native candidate frames without GT; anchor-only reconstruction is forbidden.
6. **Scoring parity and selection:** `pricing_policy.py`, `selectors.py`, `reference.py` and `work/reference_policy/`. Check the deployed accept/merge rule, missing-name abstention, type-aware fusion, mask-free rooms, direct fallback, exact item intersections and scene-cluster bootstrap. VSTI selector cells remain deferred.
7. **Admission and liveness:** check the configurable host, fresh PID/memory gate, UUID binding, sealed interpreter/CWD, GO and seal-bound review, vnice, two eight-thread reservations, source deferrals, native/parent receipts and separate storage budgets. Explicit resume must reuse only verified scenes/cells, preserve partial files and never relaunch automatically.
8. **Decision family:** `protocol.py` and `family.py` must retain all fifteen hypotheses, use VSI selector rows and a common 51-grid, label VSTI-policy exploratory, and apply Holm to whole-scene paired tests. Missing models or scenes cannot reduce the family. Native G3T is deferred; native candidate results are secondary.

## Scientific limits

The strongest cached baseline is the G3T head under the type-aware policy. Its GT-mask scores are 79.28/78.12/78.41 for absolute distance/size/room; its selector scores are 66.48/62.35/78.95. A result against V-C alone does not establish a geometry-encoder gain.

The quoted G3T AbsRel of 0.021 is clip-scale-aligned. Candidate raw error must be reported separately. Available ScanNet GT is 240×320, so native-grid upsampling does not reveal new GT edge detail. Calibration fits use shared priced anchors; all model reconstruction and temporal-consensus fitting use 64 inputs.

ARKit-100 is a frozen raw-geometry sample with all RGB sources deferred. It is not a completed native-64 dataset or a benchmark result. Its unresolved timestamps and unknown archive sizes must not be silently filled or omitted.

## Finding, fix and test evidence

| Finding | The implementation enforces this condition. | CPU evidence |
|---|---|---|
| 1 | Mirror admission checks all 64 reference frames; decoded hashes bind every candidate and resume. | The real decoder gate finds zero nonidentical fixture frames. Input tests reject changed pixels and registries. |
| 2 | The sealed interpreter/CWD, manifests, parent exports and native files must match their receipts. | Launch, provenance and native tests reject unsealed roots, shadow modules and changed bytes. |
| 3 | VSI controls policy decisions; VSTI-policy rows remain exploratory. | Protocol tests and the pricing replay verify the labels. The run card discloses G3T policy bias. |
| 4 | Item exceptions retain fallback scores and per-type error counts. | A real program exception produces a scored fallback row without failing the cell. |
| 5 | Explicit resume reuses only verified scenes/cells and preserves incomplete artifacts. | Export/hybrid/controller replays reuse one native file; corruption tests force recomputation without deletion. |
| 6 | The kit/lane cap excludes a separate production RUNS root. | A regression test distinguishes the two budgets. Native namespaces and partial files share one cap. |
| 7 | The declared run host must match the executing host. | Admission tests reject a mismatched host. No live GPU query is part of the CPU suite. |
| 8 | Fifteen hypotheses use Holm, paired scene tests and explicit interval thresholds. | Tests retain missing models/scenes, reject cross-run references and distinguish scene from question replication. |
| 9 | Calibration labels reach pricing configurations and completion receipts. | Protocol tests separate MapAnything grid approximations, full intrinsics and frozen-calibration controls. |
| 10 | DA3 uses 504 pixels; Pi3X uses its official 255,000-pixel Lanczos transform. | Both models pass eight-frame CPU inference at the resulting official dimensions. |
| 11 | The selected card must have no compute PID and at most 1 GiB used. | Admission tests reject occupied and undersized cards; production binds the accepted UUID. |

Both source and portable suites pass 65 tests. Payload receipts `out/receipts/kit_integrity.json`, `out/receipts/final_pricing_parity_integrity.json` and `out/receipts/final_native_resume_integrity.json` bind the final seal. They verify five checkpoint hashes, all 800 replayed predictions/scores/fallback values, 64 decoded identities, 32 anchors, exactly one native file after resume and four 23-row pricing cells. `out/receipts/review_baselines_integrity.json` verifies all eight saved baseline cells.

## Approval format

An approval file in the destination kit inbox must contain a standalone `APPROVED` line and `kit_sha256: <digest>`. An independent `GO` line is still required in the orchestrator's admission file. A code or bound-input change requires a new seal and approval.
