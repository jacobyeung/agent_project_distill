# E3 geometry pricing harness

The harness runs on CPU in `planner_local_v1`, with CUDA hidden and numerical libraries limited to eight threads. It writes only inside this workspace. A Python audit hook blocks reads of `candidates.json` and writes outside the workspace.

The distance path uses the deployed v3.14 `Session`, GT instance masks, the deployed lifting backend, and the session's sensor or predicted box provider. The GT adapter binds each frame's intrinsics before calling the unchanged deployed `GTSource.lift`. R0 calls `room_v314.from_points`. `room_rules.py` implements the requested R1 floor band. R2 fits a separate multiplier for each tower geometry condition from successful train room rows.

Run the lightweight checks with:

```bash
bash run.sh preflight
```

The full run requires explicit heavy-I/O approval under the supplied cluster rules. After approval, run this command in a workspace-local tmux session:

```bash
bash run.sh run --approved-heavy-io --so-mask specified > out/run.log 2>&1
```

The run reads roughly 3.3 GB from local scratch across the feature and evaluation passes. No GPU, Git, SSH, deletion or network operation is needed. The four missing GT captures are listed in `out/INVENTORY.json`.

Scale fitting receives train captures only. The harness evaluates train rows and fits R2 before opening held-out rasters. All comparisons use an item-weighted mean and physical-room bootstrap with 10,000 draws and seed 20261116. Room references use R0. The four primary C-rules require a positive train paired lower bound and a positive held-out paired estimate.

The requested SO rule includes every eligible finite positive GT depth. The frozen estimator additionally restricts its depth input to `(0.1, 10)` metres. The default preserves the requested SO definition, checks the estimator against its exact documented mask, and separately reports literal mask equality. `--so-mask frozen` selects the restricted definition if the user requests it. The harness does not claim these definitions are identical.

The deployed program has fixed metric voxel, depth-cut and morphology thresholds. Its scale-linearity tests report observed deviations without changing deployed arithmetic. The room test defines “about 4x” as a ratio within 10% of four.

An optional `--gd-dir PATH` loads deployed geometry files unchanged. Each capture must resolve uniquely to `PATH/dataset/capture/geometry.npz`, `PATH/dataset__capture.npz`, or `PATH/<kit-canonical-digest-prefix>/geometry.npz`.

The full run writes `PER_ITEM.jsonl`, `PER_CAPTURE.jsonl`, `FITS.json`, `SUMMARY.json`, `REPORT.md`, `RUN_RECEIPT.json` and `tests.log` under `out`. It also saves each generated geometry NPZ and per-capture results. The receipt hashes imported deployed sources and records the environment, manifest hash, timings and failed checks.
