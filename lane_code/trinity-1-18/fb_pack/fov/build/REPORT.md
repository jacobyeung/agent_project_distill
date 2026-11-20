`score_fov.py` is built and validated. All three full synthetic runs passed. The real input is **MISSING** at `/scratch/jjyeung/orch_n30/sb_own400/in/own_544_fov/native/probe`; no real donor decision was made.

The scorer authenticates all 242 train captures before scoring. It imports the frozen statistics and routed-geometry functions unchanged and uses the frozen pairs, rooms, folds, thresholds and bootstrap. It checks both served-depth arrays bit for bit, receipt identities and file hashes, V2 reference agreement, and depth/FoV validity. It records D1, D2, D3 and H with their measured values, then applies the frozen V2/V1/NONE preference.

| Synthetic F1 F2 | Choice | V1−A points | V2−A points | Runtime, seconds |
|---|---|---:|---:|---:|
| 1.0 1.0 | V2 | 0.000000 | 0.000000 | 353.612 |
| 1.0 1.02 | V1 | 0.000000 | -1.017980 | 688.588 |
| 1.02 1.02 | NONE | -1.017980 | -1.017980 | 689.899 |

For `1.0 1.0`, both sources pass every criterion. A factor of `1.02` fails D1, D2 and D3; H passes. Its combined displacement contrast is −1.017980 points, with 95% CI [−1.294510, −0.743281]. Every synthetic result says `synthetic: true` and `decision_usable: false`.

Each full run scored 239 captures, 117,551 displacement pairs and 1,037 routed-distance items. The three frozen GT exclusions remain listed as MISSING with their exact paths. Arm A matches the accepted donor scorer **exactly** in both folds and combined, for both metrics, in all three runs.

The small-probe suite passed 15 checks in 0.255713 seconds, including every requested refusal and both served-depth bit checks. Each execution used a two-capture fixture copied from arm A; fabricated receipts are labelled `test_fixture`. Five criterion-boundary cases passed. Four output-guard checks passed in 0.346501 seconds. Existing output directories are refused; real outputs must be fresh children of `sb_own400/out`. Synthetic outputs may use this workspace. Both modes use `core.fresh` and `core.write_guard`.

These commands produced the numbers above and verified the completed artifacts. Run them from this workspace; the three scorer output directories already exist and will be refused if reused.

```bash
env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 CUDA_VISIBLE_DEVICES= nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B score_fov.py --synthetic 1.0 1.0 --out tests/full_1_1
env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 CUDA_VISIBLE_DEVICES= nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B score_fov.py --synthetic 1.0 1.02 --out tests/full_1_1p02
env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 CUDA_VISIBLE_DEVICES= nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B score_fov.py --synthetic 1.02 1.02 --out tests/full_1p02_1p02
env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 CUDA_VISIBLE_DEVICES= nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B tests/test_refusals.py
env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 CUDA_VISIBLE_DEVICES= nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B tests/test_output_guards.py
env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 CUDA_VISIBLE_DEVICES= nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B tests/run_synthetic.py --verify-only
env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 CUDA_VISIBLE_DEVICES= nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B tests/final_audit.py
```

The detailed evidence is in `tests/SYNTHETIC_RESULTS_1795133046128932626.json`, `tests/REFUSAL_RESULTS_1795131491235408410.json`, `tests/OUTPUT_GUARD_RESULTS_1795131491623429217.json` and `tests/FINAL_AUDIT.json`. All output JSON artifacts record input hashes. The audit verified the workspace remains below 1 GB. `du -sb .` independently checks its size.

The exact real-run command is:

```bash
cd /scratch/jjyeung/orch_n30/sb_own400 && env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 CUDA_VISIBLE_DEVICES= nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B /scratch/jjyeung/orch_n30/fb_pack/fov/build/score_fov.py --own-root in/own_544_fov/native/probe --out out/fov544_score
```

The scorer writes `FOV_RESULT.json`, `DISTANCE_ROWS.json` and `PREFLIGHT.json`. Results include input SHA-256 values, arm/contrast summaries, criterion values, choice, missing GT, FoV agreement by dataset and axis, scale ratios and fit-half factors. V2−V1 and all calibration/agreement summaries remain report-only. A refused run records `choice: MISSING` and its named failure. One working geometry file per capture bounds disk use.

`sha256sum score_fov.py` produced:

```text
3fed65b261ccb3c04941bd85433a51a8eebc0391fba2b66c5ea1f30c72a3b4df  score_fov.py
```

The scorer verifies the supplied FoV-bars hash `c1905484873704ae9b8af5cb653cf2cb1b911d789d181811767fa5f8707fa878` and its source pins. The bars leave these details unspecified:

- **Receipt source pins:** `FOV_RECEIPT.json` does not define source-pin field names or the required set. The scorer hashes and preserves the receipt and checks the explicit capture/checkpoint/file requirements and numerical V2 reference. It does not invent a producer-proof schema.
- **FoV pooling:** The bars do not define pooling across captures. The output supplies per-capture medians and explicitly labelled pooled-anchor medians for each dataset and axis. These do not affect the choice.
- **NONE:** The bars do not define a binding procedure for a frozen pose-head FoV copy. The result names the missing frozen-path specification, source/checkpoint/capture evidence and binding rule without inventing that procedure.

No held-out, R0-dev or dev-S1 payload was opened. The imported training selector reads the pinned manifest to select train metadata. No Git, SSH, network, GPU or process-stopping operation was used. The `no-archaeology` writing skill retained no borderline historical sentences.
