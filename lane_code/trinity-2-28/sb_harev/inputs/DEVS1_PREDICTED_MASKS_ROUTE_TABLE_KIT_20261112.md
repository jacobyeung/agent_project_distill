# dev-S1 mask kit design record

**Question:** Which spatial question types should use the frozen mask-and-geometry program instead of CP1's direct answer on held-out physical rooms?

**Answer and status:** The executable path and CPU evidence are delivered. The predicted-mask route decision awaits one SAM3 GPU pass. The GT-mask stand-in supports absolute distance and counting in the pooled comparison; it cannot authorize deployment routing.

| Decision | Answer and evidence | Options rejected |
|---|---|---|
| Candidate density | Joint score ≥0.2, cap 10 per frame, normalized P0 only; masks >0.5, resolution 1008, bf16. `RUN_CARD_DENSE.md` identifies this as the trained cache. The E1 linker additionally requires instance score ≥0.3. | Dense 0.05/30/P0+plural is a sensitivity run, not the trained deployment density. No dev density sweep. |
| Frozen selector | Requested `setsel/price2.py` policy: `DEPLOY|portable_np|logistic`, unique top-1 by accept probability then SAM peak; counting accepts ≥0.15, falling back to top-1 if none passes. | STATUS mentions a newer xph score map but explicitly says it is not wired into price2. No xph refit or invented deployment model. |
| Merge | Frozen logistic pair model; average linkage at ≥0.2; any shared-frame overlap below 0.2 of the smaller mask blocks a merge. Merge masks by per-frame union, as price2 actually executes. | The setlib prose describes selecting one member per frame, but price2 calls `price.union`. The executable rule governs this kit. |
| Features and models | Reuse E1 linking, all linked candidates, portable no-prior feature functions, and pair functions. V-C geometry supplies these features, as in training. NumPy applies exported StandardScaler/logistic coefficients. | No sklearn install and no training. No labels, GT geometry, student PRES32 or V3 features enter deployment selection. |
| Geometry and programs | Reuse `devs1_price` executor, unit conversion, farthest handling and scorer. G3T supplies program depth and pose. Absolute distance uses the largest view; other boxes use two-frame 5 cm voxel votes plus largest view; masks use interior depth cuts; rooms use floor-cell voting. | V-C program depth, scale fitting, GT-dependent pose alignment, or retuning fusion on dev-S1. |
| Coordinate convention | Deployment uses raw exported tower coordinates. On identical inputs, 22/22 dataset/type checks reproduce the reference. Aligned-input checks also reproduce the saved GT rows. | Existing GT pricing aligns pose by yaw/translation. Voxel grids and room grids make this operation slightly non-invariant; it is unavailable without GT and cannot be required for 152-capture deployment. |
| Coverage | 152 captures, 4,864 anchors, 819 capture/prompt calls, 6,161 questions in eight supported types. 304 head files pass 9,728 anchor joins. Eleven room placeholders lack labels and retain null scores. | Camera types lack a validated frame binding; relative_count, relative_size_object and route_planning have no program in the supplied frozen runner. Their exclusions are counted in `INPUT_AUDIT.json`. |
| Route pairing | Frozen CP1 ON16k report from r5; its source journal matches the merge receipt SHA256. Pair exact qids with primary released-label scores. Report All and each source dataset. | Selecting a budget arm using dev outcomes; canonical/released label mixing; dropping abstentions; silently intersecting incomplete predicted runs. |
| Interval and verdict | 10,000 physical-room bootstrap draws, seed 20261112; draw whole rooms with replacement, use item-weighted means, percentile 95% interval. Route if low>0; direct if high<0; otherwise undecided. | Capture bootstrap, item bootstrap, or a new sample-size threshold. Room counts expose tiny or degenerate groups. Intervals are marginal, without multiplicity correction. |
| Abstentions | Raw program no-answer score is zero. The JSON separately reports direct-fallback means. | The selector lane's fallback score is not silently substituted for the requested raw program comparison. |
| Holdout | No overlap between the selector's 84 training captures/physical rooms and the 152 dev-S1 captures. Every question belongs to the withheld room/native registry. | Learning thresholds, features, models or fusion on these held-out answers. |
| Commit/resume | Each capture uses exclusive NPZ creation and an fsynced journal hash. Resume verifies both. Corrupt or uncommitted files stop the run. Clean STOP/cap boundaries resume; HALTED requires explicit operator review. | File rename, deletion, silent replacement, automatic relaunch after a killed job, and a keeper process. |

## Loss decomposition

The CPU diagnostics use GT only after the deployable mask sets have been chosen. Candidate acceptance labels follow the selector lane: at least half the candidate's members must match the named-category GT at IoU >0.5. Proposal coverage uses greedy one-to-one IoU >0.5 matching per frame. Visible-instance diagnostics use the fixed 154-pixel gate on the half-resolution raster, including portrait rasters.

The score chain is `predicted → oracle_accept → gt_proposed → gt_ever_proposed → gt`:

- **Wrong object accepted:** replace predicted accepts with the label-accepted union for unique operands and label accepts with the same learned merge for counting. This matches the selector's label-oracle construction; it can also alter mask support.
- **Mask shape and identity residual:** replace oracle-selected candidate masks with GT masks only at raw-proposal-matched frame/instance pairs. This residual prevents assigning all shape or identity errors to wrong accepts.
- **Fewer frames:** restore every GT frame for instances proposed at least once.
- **Object never proposed:** restore GT instances that no raw proposal matched on any frame.

The four paired score contrasts telescope to GT minus predicted. They can be negative and are counterfactual contrasts, not mutually exclusive causal error counts. The route JSON computes them on the same paired GT-available items, separately by dataset and type. `MASK_DIAGNOSTICS.jsonl` records instance/frame coverage and candidate labels. Missing GT is explicit; the 59 GT-missing captures still receive deployment predictions.

## Evidence and limits

`TESTS.md` reports the tests. `REPLAY_PARITY.json` includes 22 checks spanning all eight supported types and all three datasets where those types exist. Two sampled size scores and one room prediction change between raw and GT-aligned coordinates; the adapter agrees with the reference under either convention. The supplied GT stand-in therefore tests the statistics on the supplied GT results, rather than claiming exact production-coordinate equivalence.

The GT stand-in has 617/1,086 eligible direct pairs; the other 469 lack GT program results. Pooled absolute distance gains 27.1 pp [13.6,42.4]; counting gains 29.0 [17.1,41.1]. The six other pooled intervals include zero. GT masks are an oracle reference called an upper bound here; noisy geometry can make them worse than predicted masks on individual items. The report never exports these hypothetical verdicts as deployment decisions.

The fusion policy was initially found on benchmark test scenes and then re-derived on separate development data, as the frozen policy file discloses. This kit does not erase that provenance. The new type-routing choice will use dev-S1 only.

| Risk / open point | How we would notice | Test that settles it | Status |
|---|---|---|---|
| Missing or changed PNGs | Preflight hash, size or format failure | Run full staged `preflight.py`; 4,864 expected files | Pending; PNGs are not present here |
| SAM/source/runtime mismatch | Receipt/source/weight refusal or first-call failure | Seal check, receipt checks and first 32-frame GPU call | Pending GPU staging |
| Portrait/domain shift | ARKit/ScanNet++ proposal coverage or scores fall | Dataset-specific coverage, score contrasts and room intervals | CPU portrait path passes; quality unmeasured |
| GT category/annotation gaps | Low label acceptance despite plausible candidates | Inspect sampled diagnostic masks and labels; retain the raw candidate evidence | Known limitation of GT diagnostics |
| Raw-coordinate voxel effects | GT-aligned and raw replay differ | Paired raw/GT-aligned checks without selecting a new policy | Measured; disclosed, no policy tuning |
| Low room count / multiple comparisons | Wide or degenerate intervals; many subgroup verdicts | Report room counts and use a fresh confirmatory set if needed | Counts exposed; no significance correction added |
| Runtime/output underestimate | Journal throughput, cache growth or cap exit | First capture timing and actual RLE bytes | GPU time and cache size are estimates |
| Runtime source size unknown | Source tree/asset inventory at staging | Measure on the run host; validate receipt hashes | Source is not local; no fabricated size |

All work in this lane used the CPU interpreter, local read-only sources, and local outputs. No GPU, SSH, Git, network, `/home` or `/data*` access occurred. No files were deleted or moved.
