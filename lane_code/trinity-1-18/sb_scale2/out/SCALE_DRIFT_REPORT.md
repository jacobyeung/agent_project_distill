# Price of stopping tower-arm scale drift

The question is whether freezing or calibrating the depth-derived tower scale gives vehicle N a defensible gain at its first boundary. The available K1 own-depth cache prices step 544 only. It cannot price N’s step-400 initialization or prove that a particular training source caused the drift.

Global calibration changes displacement by **+0.153 [+0.087, +0.222] MRA points**. Dataset calibration minus global calibration is **-0.147 [-0.337, +0.047]**. The frozen displacement preference is **G**; the choice after the distance-harm guard is **G**. A means unchanged step544 scale, G global calibration, and D calibration per dataset.

Keep N first-boundary comparisons on the existing serving pin. Complete the 1.04 GPU-h step400 K1 own forward before claiming a donor/freezing benefit. Do not use dataset calibration or remove a source without its required evidence. Prefer a frozen donor400 dependency closure for prospective drift control because it preserves N init; its MRA price must await that forward. Donor544 is an immediately priceable alternative, but it has no measured advantage over N init. Do not present a live-scale N read as drift-controlled.

**Serving consequence:** Any changed scale rule, coefficient or donor input means every tower-arm baseline is read again before any N export is read under it.

## Test-half prices

Each interval is a paired room bootstrap with 10,000 draws, seed 17 and 95% coverage. Both swapped folds use exactly the sb_scale1 rooms. The combined table scores each available room once. Fit factors use fit-half displacement only; distance uses those same factors with exact relifting. The distance guard rejects a calibration if either test half or the combined interval shows harm (upper bound below zero).

### Displacement

| Arm | Fold 1 MRA [95% CI] | Fold 2 MRA [95% CI] | Combined MRA [95% CI] |
|---|---:|---:|---:|
| A | 83.098 [81.138, 84.933] | 84.509 [81.790, 86.838] | 83.800 [82.183, 85.343] |
| G | 83.211 [81.262, 85.034] | 84.701 [81.992, 87.029] | 83.953 [82.336, 85.497] |
| D | 82.976 [81.043, 84.779] | 84.644 [82.008, 86.943] | 83.806 [82.216, 85.361] |

| Arm minus A | Fold 1 MRA points [95% CI] | Fold 2 MRA points [95% CI] | Combined MRA points [95% CI] |
|---|---:|---:|---:|
| A | +0.000 [+0.000, +0.000] | +0.000 [+0.000, +0.000] | +0.000 [+0.000, +0.000] |
| G | +0.114 [+0.049, +0.179] | +0.193 [+0.075, +0.314] | +0.153 [+0.087, +0.222] |
| D | -0.122 [-0.466, +0.225] | +0.135 [-0.063, +0.341] | +0.006 [-0.193, +0.214] |

| Arm minus A, benchmark contribution | Fold 1 points [95% CI] | Fold 2 points [95% CI] | Combined points [95% CI] |
|---|---:|---:|---:|
| A | +0.000 [+0.000, +0.000] | +0.000 [+0.000, +0.000] | +0.000 [+0.000, +0.000] |
| G | +0.023 [+0.010, +0.036] | +0.039 [+0.015, +0.063] | +0.031 [+0.017, +0.044] |
| D | -0.024 [-0.093, +0.045] | +0.027 [-0.013, +0.068] | +0.001 [-0.039, +0.043] |

### Distance

| Arm | Fold 1 MRA [95% CI] | Fold 2 MRA [95% CI] | Combined MRA [95% CI] |
|---|---:|---:|---:|
| A | 67.122 [61.788, 72.162] | 69.443 [63.820, 74.669] | 68.295 [64.396, 71.964] |
| G | 67.138 [61.831, 72.093] | 69.741 [64.164, 75.038] | 68.453 [64.562, 72.074] |
| D | 67.417 [62.017, 72.436] | 70.161 [64.479, 75.487] | 68.803 [64.869, 72.413] |

| Arm minus A | Fold 1 MRA points [95% CI] | Fold 2 MRA points [95% CI] | Combined MRA points [95% CI] |
|---|---:|---:|---:|
| A | +0.000 [+0.000, +0.000] | +0.000 [+0.000, +0.000] | +0.000 [+0.000, +0.000] |
| G | +0.016 [-0.458, +0.482] | +0.298 [-0.295, +0.933] | +0.158 [-0.230, +0.552] |
| D | +0.295 [-0.383, +0.953] | +0.718 [+0.122, +1.357] | +0.509 [+0.041, +0.957] |

| Arm minus A, benchmark contribution | Fold 1 points [95% CI] | Fold 2 points [95% CI] | Combined points [95% CI] |
|---|---:|---:|---:|
| A | +0.000 [+0.000, +0.000] | +0.000 [+0.000, +0.000] | +0.000 [+0.000, +0.000] |
| G | +0.002 [-0.057, +0.060] | +0.037 [-0.037, +0.117] | +0.020 [-0.029, +0.069] |
| D | +0.037 [-0.048, +0.119] | +0.090 [+0.015, +0.170] | +0.064 [+0.005, +0.120] |

## Calibration decision

Displacement decisions are global versus A: SUPPORTED; dataset versus A: INCONCLUSIVE; dataset versus global: INCONCLUSIVE. The distance guard reports supported harm for the preferred calibration: False. The fit-half factors price a fixed rule; they are not a single production coefficient. A production factor and dataset identity policy still need explicit export pins.

## Benchmark conversion

Camera displacement is one of five equally weighted VSTI task groups, so a displacement change of Δ MRA points contributes Δ/5 benchmark points if the other groups remain fixed. Object absolute distance is one of eight VSI groups, so its contribution is Δ/8. These projections refer to different benchmarks and must not be added. The official code defines the groups at lines 109–139 and averages group scores at lines 544–564.

Source: `/scratch/jjyeung/orch_n30/trin_read/kit_src/reader/evaluator/evalpath/official.py`, SHA-256 `a5d6d79fd29fce43791401cd01438f16f3ff6ad7a6c2651cb70d0d42088cf589`. Only source code was read; no benchmark row was opened.

The arithmetic converts type points; it does not establish benchmark improvement. This experiment averages rooms and uses all eligible anchor pairs or GT-mask distance rows. Official benchmark questions have different distributions and include grounding and routing errors. Geometrically, scaling all translations uniformly leaves move direction and turn rotation unchanged, but other scale-dependent tasks can change and were not priced here.

## Bias and origin

ITEMS12.md reports pooled and per-dataset served/GT ratios, capture distributions, paired global-versus-dataset tests, own/GT depth, pose-scaled G3T/GT depth, and depth-implied/pose-length scale. The JSON includes every fit-room identity and capture diagnostic.

A depth-implied/pose-length discrepancy is measured through G3T. It can reflect G3T shape, FoV, registration or GT errors. It is not an independent proof that dataset metric depth disagrees with metric poses. A decisive label audit needs matched depth reprojections across metric poses and trustworthy camera intrinsics, followed by the actual training-target audit.

All four pose-stream source comparisons are MISSING: a2v3 d1, a2v3 d2, a3v2 d1 and a3v2 d3. The local scene lists contain identifiers, not depths. The receipts name opaque dataset codes only. No source can be named for removal, and no retraining gain can be priced.

### Step-544 bias by dataset

| Dataset | Displacement pooled ratio; capture p10 / p50 / p90 | Distance pooled ratio; capture p10 / p50 / p90 |
|---|---:|---:|
| all | 1.0110; 0.9255 / 1.0087 / 1.0941 | 0.9351; 0.7882 / 0.9511 / 1.1821 |
| arkitscenes | 1.0018; 0.9167 / 0.9943 / 1.1057 | 0.9739; 0.7777 / 0.9918 / 1.2073 |
| scannet | 1.0372; 0.9628 / 1.0414 / 1.0839 | 1.0438; 0.8974 / 1.0437 / 1.2743 |
| scannetpp | 1.0074; 0.9391 / 1.0068 / 1.0639 | 0.9184; 0.7916 / 0.9136 / 0.9885 |

| Distance dataset | Refusals A / G / D | Captures with a finite A ratio |
|---|---:|---:|
| all | 36 / 36 / 36 | 195 |
| arkitscenes | 36 / 36 / 36 | 113 |
| scannet | 0 / 0 / 0 | 22 |
| scannetpp | 0 / 0 / 0 | 60 |

| Dataset | Own / GT depth, pooled | Pose-scaled G3T / GT depth, pooled | Depth-scale / pose-scale capture p10 / p50 / p90 |
|---|---:|---:|---:|
| all | 1.0164 | 1.0077 | 0.9310 / 0.9917 / 1.0344 |
| arkitscenes | 1.0276 | 1.0229 | 0.9118 / 0.9786 / 1.0104 |
| scannet | 1.0009 | 0.9661 | 0.9949 / 1.0290 / 1.1061 |
| scannetpp | 1.0145 | 1.0073 | 0.9681 / 0.9941 / 1.0139 |

Depth ratios use the matched confidence/valid-depth grid mask specified in ITEMS12 and the frozen bars. Capture quantiles are descriptive distributions, not confidence intervals. The JSON also reports room-bootstrap intervals for the means of room median depth ratios.

## Options and implementation needs

### a: frozen donor544: PRICED

Same depth outputs and FoV inputs reproduce arm A exactly; this prevents later head drift but does not establish a gain over N init.
Use arm A in both fold tables and benchmark-contribution tables above. Its combined displacement change is +0.000 [+0.000, +0.000]; its projected VSTI contribution is +0.000 [+0.000, +0.000].

Tree: Add an immutable scale donor with its own frozen private visual features and donor pose FoV conditioner; live point-depth training may continue for other callers.

Export: Bundle or reference donor544 weights, private-visual and FoV dependencies, preprocessing, scale rule, and SHA-256 pins separately from live heads.

Reader: Select the pinned donor only for tower-arm scale; use the same scalar once on tower pose translations and routed G3T depth. Re-read every tower baseline under this rule before any N export.

### a: frozen donor400: MISSING

Step400 K1 own depth is absent. The donor reproduces N init scale, whose paired price is unknown.
Both fold prices, the combined price, and benchmark-point conversions are MISSING; rejection is a decision, not an invented measured price.

Tree: Same frozen-donor path as donor544, with step400 dependencies.

Export: Pin the complete step400 donor dependency closure.

Reader: Use the pinned donor400; re-read tower baselines if the rule changes.

### b: freeze point-depth training and FoV inputs: MISSING

Serving equals N init = R1 step400 head only if depth weights, private visual inputs, FoV conditioner, preprocessing and query layout remain invariant. Freezing weights alone is insufficient.
Both fold prices, the combined price, and benchmark-point conversions are MISSING; rejection is a decision, not an invented measured price.

Tree: Exclude point-depth weights from optimizer updates and freeze its FoV-producing path; use fixed private visual features. Set modules to deterministic evaluation behavior where required.

Export: Record frozen head and FoV dependency hashes at N init and boundary; include an identical-output check.

Reader: Keep existing OwnDepthScale arithmetic. If the contract and dependency sources are unchanged, a training freeze alone does not change the serving rule; any new FoV/donor source requires baseline re-reading.

### c: global calibration alone: PRICED_AT_544_ONLY

One fit-half room-balanced factor applied to live own scale; does not prevent subsequent head drift.
Use arm G in both fold tables and benchmark-contribution tables above. Its combined displacement change is +0.153 [+0.087, +0.222]; its projected VSTI contribution is +0.031 [+0.017, +0.044].

Tree: Multiply OwnDepthScale output by pinned global c; preserve confidence mask and validity filter.

Export: Pin c, fit-room identities, donor/live head identity, and scale-rule version.

Reader: Apply c once to shared pose/depth scalar; re-read all tower baselines.

### c: dataset calibration alone: PRICED_AT_544_ONLY

One factor per known dataset; deployment needs a legitimate dataset identity and an explicit unknown-dataset policy.
Use arm D in both fold tables and benchmark-contribution tables above. Its combined displacement change is +0.006 [-0.193, +0.214]; its projected VSTI contribution is +0.001 [-0.039, +0.043].

Tree: Lookup a pinned c by receipt-backed dataset identity; refuse unknown identities until a policy is priced.

Export: Pin factors, fit-room identities, dataset mapping and rule version.

Reader: Apply dataset c once to shared scale and re-read all tower baselines; K1 dataset codes are not pose-stream source mappings.

### c: global calibration on donor544: PRICED

Exactly the G price while donor544 supplies identical depth and FoV inputs.
Use arm G in both fold tables and benchmark-contribution tables above. Its combined displacement change is +0.153 [+0.087, +0.222]; its projected VSTI contribution is +0.031 [+0.017, +0.044].

Tree: Compose donor544 with one fixed c.

Export: Pin both donor closure and c.

Reader: Re-read every tower baseline under the composed rule.

### c: dataset calibration on donor544: PRICED

Exactly the D price with the same identity requirements.
Use arm D in both fold tables and benchmark-contribution tables above. Its combined displacement change is +0.006 [-0.193, +0.214]; its projected VSTI contribution is +0.001 [-0.039, +0.043].

Tree: Compose donor544 and dataset lookup.

Export: Pin donor closure, factors and mapping.

Reader: Re-read every tower baseline under the composed rule.

### c: calibration on donor400 or frozen N init: MISSING

Factors and gains at step544 cannot be transferred as measured step400 prices.
Both fold prices, the combined price, and benchmark-point conversions are MISSING; rejection is a decision, not an invented measured price.

Tree: Fit factors using step400 train predictions on these folds.

Export: Pin step400 donor, factors and fit provenance.

Reader: Re-read baselines if the scale rule changes.

### d: remove or reweight a biased depth source: MISSING

All four source target-depth comparisons and dataset mappings are missing. K1 depth/pose inconsistency cannot identify a training source or price causal retraining.
Both fold prices, the combined price, and benchmark-point conversions are MISSING; rejection is a decision, not an invented measured price.

Tree: After source identification, change its depth-loss sampling/weight only in a controlled training comparison.

Export: Pin training-source receipts, weights, training recipe and resulting head.

Reader: Compare exported candidates under one serving pin; if a new scale rule is introduced, re-read baselines first.

### e: pinned learned scale head: REJECTED

The user supplies a 9.3-point loss; no local K1 training prediction here supports reversal. That loss is not re-scored or represented as a K1 measurement.
Both fold prices, the combined price, and benchmark-point conversions are MISSING; rejection is a decision, not an invented measured price.

Tree: No change recommended.

Export: Keep its existing pin out of the recommended scale path.

Reader: Do not substitute it; require K1 training predictions and paired intervals before reconsideration.

## What could fail, and how to detect it

| Failure | Observable test |
|---|---|
| The frozen head still receives moving FoV inputs. | Compare depth, FoV and scale on fixed training RGB before and after an optimizer update; freeze the full input dependency closure. |
| Freezing the live depth head harms other depth callers. | Compare those callers on permitted training inputs; a separate scale donor allows the live head to keep learning. |
| A donor export silently mixes live and frozen dependencies. | Verify donor weight, private-feature, FoV, preprocessing and scale-rule hashes; reproduce its cached 51×51 grids. |
| Dataset calibration overfits or uses the wrong identity. | Require D−G to pass both folds and combined; validate dataset lookup from receipts and refuse an unknown identity. |
| A camera calibration harms routed distance. | Relift with the changed scale and compare paired GT-mask distance scores; monitor refusals and per-dataset losses. |
| GT depth/pose discrepancy is caused by geometry rather than labels. | Audit frame registration, optical-axis depth, intrinsics, multi-view reprojection and G3T shape before blaming a source. |
| GT-mask improvement does not survive predicted masks or routing. | Run a separately authorized complete reader comparison under the same serving pin; no such claim is made here. |
| A scale is applied twice. | Check geometry scale counts and linearity of camera translations and lifted depths; preserve a single shared scalar. |
| The first N comparison mixes serving rules. | Check baseline and N serving-pin hashes; reject a mixed comparison and re-read all tower baselines first. |

## Tests that settle missing prices

- **step400 K1 own depth**: Use NEEDS_INPUTS.json capture and RGB pins: 242 train captures, 32 anchors each, frozen private visual depth path conditioned on matching pose FoV. Save 32x51x51 metre depth and checkpoint/capture/code receipts. No G3T or SAM forward. Score both frozen folds in a fresh output directory. GPU-hours: **1.04**. Planning estimate from sb_scale1; plus staging and model load, device unverified. 
- **three missing K1 GT archives**: Supply the exact GT archives and hashes listed in ITEMS12.json missing; rerun in a fresh frozen experiment. GPU-hours: **0.0**. CPU analysis only. 
- **pose-stream targets and source identities**: Stage receipt-pinned rows.sqlite for a2v3 and a3v2, an explicit dataset mapping receipt, and matched frame/intrinsic/pose/G3T pins. Use legal training rows only. Compare target-depth-implied G3T scale against pose-length scale on the same frames. GPU-hours: **0.0**. CPU if matching G3T and pose labels are supplied; otherwise G3T forward cost MISSING, requires measured pilot and row count. 
- **frozen donor or training-freeze implementation invariance**: Compare depth/FoV/output hashes on fixed train captures before and after optimizer updates; verify optimizer exclusion and immutable donor inputs. Assert exactly one scale multiplication on translations and routed depth. GPU-hours: **MISSING**. No new forward for CPU cached-grid identity test; model output invariance needs the implemented tree and measured pilot. A full cached-grid pass can use the 1.04 GPU-h planning estimate per checkpoint. 
- **source-removal causal price**: Run matched-control retraining with identical initial checkpoint, schedule and seeds, altering only identified depth-source weight; evaluate with the same room folds and paired bootstrap. GPU-hours: **MISSING**. Requires source evidence, training recipe and measured training throughput; 1.04 GPU-h own forward per resulting checkpoint is an additional estimate. 
- **learned-head K1 train predictions**: Supply pinned per-capture scale outputs and valid export/input receipts for K1 train. Require CI-positive paired gain over A in both halves and combined, plus no supported distance harm. GPU-hours: **MISSING**. CPU scoring costs 0 GPU-h if predictions exist; a new model forward needs a pilot because no matching runner timing is established. 

The step-400 forward is exactly the one specified in sb_scale1/out/NEEDS.md and NEEDS_INPUTS.json: 242 training captures and 7,744 RGB anchor slots, matched checkpoint context, no token generation, and one finite [32,51,51] own-depth grid per capture. Its 1.04 GPU-hour estimate excludes staging/model load. This CPU-only task ran no forward.

## Reproduction and validation

All measured tables originate from the frozen scoring command; benchmark conversions and option tables originate from the report command.

```sh
env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B code/test_scale_drift.py
env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B code/scale_drift.py freeze
env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B code/scale_drift.py score
env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B code/finish_report.py
```

IMPLEMENTATION_FIX.json documents exception handling for E3 geometry refusals and pins both code versions and the original bars. Metrics, folds, fitting and decisions are identical. The scorer refuses existing score files and verifies the frozen code and input hashes. The tests check exact room folds, dataset-fit isolation, refusal behavior, zero credit for program refusals and strict MRA parity. Final validation is recorded in VALIDATION.json. These commands describe the original run; a fresh scoring run requires a new experiment directory rather than overwriting these outputs.

Scoring elapsed time: 4598.01 seconds. Resource usage is in resources.log. All jobs used nice 10 and at most eight numerical-library threads. Inputs and imported scoring dependencies are SHA-256 pinned in the JSON outputs.

This internal diagnostic retains checkpoint names, split details and the supplied learned-head loss because the task requires reproducible option pricing. It does not claim an evaluated step400 result or a discovered biased training source.
