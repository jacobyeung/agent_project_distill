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
