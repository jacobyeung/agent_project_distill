This file replaces the lost original out/RUNCARD_K1.md (written by kit_k1a/work/finalize.py:46 on trinity-2-18; no copy or hash survives). Lines 2 onward are finalize.py's template text verbatim (kit_k1a/work/finalize.py on trinity-1-18, mtime 2026-11-15T06:55Z); each value the template took from a lost input is marked [NOT RECOVERED: expression]. Original line N is line N+1 here, so the records' citation "RUNCARD_K1.md:9" is line 10.
K1 is a prepared, fail-closed run kit. **Do not launch the supplied template.** It lacks dense RGB for [NOT RECOVERED: facts['unresolved_dense_captures']] selected captures, exact staging bytes, verified local model settings, and reviewed fallback traces (out/K1_PLAN_RESULT.json; out/GPU_SETTINGS.template.json). No GPU ran.

The required p1cpu interpreter has PyTorch 2.11.0+cpu and no compiled CUDA support (out/GPU_ENVIRONMENT_METADATA.json). Its commands below are a conditional run sequence, not an executable GPU launch on this environment. The user's standing instruction keeps non-fit work on p1cpu. A GPU-capable interpreter therefore needs explicit authorization and a compatibility proof before the GPU launcher can be made operational. This lane installs nothing and silently substitutes no interpreter.

The fixed pilot contains 300 captures: 51 ScanNet, 87 ScanNet++, and 162 ARKitScenes. Physical-room splitting with seed 17 yields 242 training and 58 held-out captures (out/INVENTORY_RESULT.json; exact membership in out/CAPTURES.json). K1's held-out rooms remain training-corpus rooms; the separate `k1_split` field controls fitting.

The pipeline first caches unselected proposals and checkpoint-scaled geometry. It then builds label-free candidate features, fits on K1 training rooms, and renders with that refit. The current selector may run only in explicit CPU fixture proofs. It never renders K1 training responses.

Frozen settings: dense_aliases, joint floor 0.05, per-prompt cap 30, merged cap 100, linker floor 0.3, mask threshold 0.5, SAM resolution 1008, BF16, batch one. G3T reconstructs a complete declared dense sequence before selecting the 32 anchors. geometry.convert uses the step-544 private heads for one scale application and gravity. The native candidate policy retains its interior depth cut and fit_gbox_policy_voteb5_best1_v1 box policy. Sources: legs1_routed/out/ROUTED_READ_SPEC_NOMDG.md; o3_cache/work/kit/pipeline.py and boundaries.py.

Estimated GPU work is [NOT RECOVERED: lo:.2f]–[NOT RECOVERED: hi:.2f] hours, including [NOT RECOVERED: timing['geometry_hours']:.2f] hours for geometry and [NOT RECOVERED: timing['sam_hours_low']:.2f]–[NOT RECOVERED: timing['sam_hours_high']:.2f] hours for [NOT RECOVERED: prompts] prompt calls. This extrapolates the named devs1_masks rates and the geometry estimate; it is not a measured K1 timing. CPU selection/rendering, model loads, and offloading are additional (out/GPU_ESTIMATE.json). Start with an operator-reviewed capture smoke before extrapolating the full run.

Before execution, the operator must:

1. Close out/HEAVY_IO_QUESTION.md and stage complete dense RGB on the assigned node. Complete and hash the production manifest; do not substitute sparse anchors. Mark `frame_staging_authorized` and `production_ready` true only after closure. Empty unresolved-source lists must reflect real input closure.
2. Complete every required model setting in out/GPU_SETTINGS.template.json with verified local paths and hashes. The known artifact/config/G3T/SAM hashes are already bound; model payload locations remain pending. Bind each model row's native fps, timestamps, total frame count, and scene identity from source metadata. Use the accepted step-544 artifact and matching config/data receipt, frozen E0 G3T weights/config, and frozen SAM checkpoint/source receipt. Nothing installs or downloads.
3. Supply reviewed visual fallback traces through each row's `fallback` field. Missing evidence produces an excluded row. GT enters only classification and fitting labels; no GT value is copied into a runtime response.
4. Check the cluster allocation board, choose one compute node and card, and use the operator's persistent session. Bind a node-local copy of the existing vnice.sh. This lane selects no card and launches no job.
5. Run work/verify_sources.py. A changed dependency requires review and revalidation, not a silent pin refresh.

Commands, from this lane's directory on the staged node:

```bash
bash work/run_k1.sh NODE CARD /scratch/jjyeung/k1/manifest.json /scratch/jjyeung/k1/cache /scratch/jjyeung/tools/vnice.sh
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/k1_pipeline.py tables --manifest /scratch/jjyeung/k1/manifest.json --cache /scratch/jjyeung/k1/cache --out /scratch/jjyeung/k1/tables
/scratch/jjyeung/envs/planner_local_v1/bin/python -I -B work/refit/train.py --candidates /scratch/jjyeung/k1/tables/candidates.jsonl --pairs /scratch/jjyeung/k1/tables/pairs.jsonl --inventory out/CAPTURES.json --out /scratch/jjyeung/k1/refit
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/k1_pipeline.py render --manifest /scratch/jjyeung/k1/manifest.json --cache /scratch/jjyeung/k1/cache --fit /scratch/jjyeung/k1/refit --out /scratch/jjyeung/k1/rendered
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/k1_report.py --rows /scratch/jjyeung/k1/rendered/K1_ANALYSIS_INPUT.jsonl --inventory out/CAPTURES.json --manifest /scratch/jjyeung/k1/manifest.json --fit /scratch/jjyeung/k1/refit/FIT_RECEIPT.json --out /scratch/jjyeung/k1/K1_RESULT.json
```

The refit writes MODELS.json (`coef` for frozen pricing), NATIVE_POLICY.json (`coefficient` and `pair` for the native policy), and the original pickle bundles. Every fit receipt records Python, NumPy and scikit-learn versions, input/source hashes, and room splits. The fixed policy thresholds are inherited constants; no K1 label tunes them. The constant-answer baseline uses training rooms only. K1 reports AUC/AP/top-one metrics for both models on identical held-out candidates.

The cache writes append-only PROGRESS.jsonl and per-capture receipts. Resume checks source, manifest, geometry, and proposal hashes. A partial capture or HALTED run refuses resume. The watchdog supervises only its own child; it halts after 900 seconds without a capture commit or 21,600 wall seconds. It never retries. A clean time/STOP boundary returns 4. Write RESUME into the existing STOP file only after the operator authorizes continuation. An unexpected cluster kill must be reported and reviewed before any rerun.

The output cap is 1.5 GB and the run requires a 100 GiB free-space reserve in addition to that cap. Use at most eight CPU threads; this card defaults to one. The build lane remains below its separate 2 GB cap. Large raw proposal JSON may hit the bounded 20 MB reader; that failure requires a streaming format change before continuing.

Live parity: work/parity_live.py --print-command prints the command for a manifest containing exactly ten eligible scenes. The cache stage retains parity_raw.jsonl before merging. Its entries bind frame bytes, verbatim raw prompt, cached per-prompt response and SAM settings. The harness runs the real encode/detect path at the dense floor/cap and the tower's noise-aware rule. Merged alias records cannot substitute because merging reindexes proposal IDs. CPU KIT exercises raw-record collection; production collection and real GPU parity remain unverified.

Build the fixed ten-scene manifest from completed cache outputs:

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/parity_live.py --prepare --manifest /scratch/jjyeung/k1/manifest.json --cache /scratch/jjyeung/k1/cache --out /scratch/jjyeung/k1/PARITY_10.json
```

Each rank must run the actual row admission before its first batch:

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/first_batch.py --rows RANK_FIRST_ROWS.jsonl --contract SEALED_MEMBERSHIP_CONTRACT.json --rank RANK --out RANK_FIRST_BATCH_RESULT.json
```

rs_tree must seal production membership itself. out/FIRST_BATCH_32.jsonl and out/FIRST_BATCH_CONTRACT.json are synthetic CPU fixtures and confer no training admission. No patch to a seal tree is required or supplied.
