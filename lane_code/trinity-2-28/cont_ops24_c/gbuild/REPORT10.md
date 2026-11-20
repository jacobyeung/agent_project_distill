The saved tower outputs do not include a camera-confidence score. Predicted orientation gives a descriptive flag: origin-camera tilt has gross/pass AUC 0.917 overall and 1.000 within ARKit. K3d A′–T1 instability also separates its five gross from two passing captures, but needs two runs and covers only ten captures.

The cohort is 38 distance-GT captures (6 pass, 22 moderate, 10 gross); ARKit has 2 pass, 13 moderate, 8 gross. Classes follow CAMERA_SPLIT/REPORT9 and ARKit’s pose/RGB binding remains unresolved. Failing means moderate+gross. Every result and threshold is descriptive with n=38; subgroup and missing-feature counts are explicit.

| Quantity | Served path | Existing captures / K3d |
| --- | --- | --- |
| Pose/camera confidence | No confidence head | Absent / absent; AUC undefined (n=0) |
| Depth + depth confidence | Kept as 32×51×51 grids; scale consumes confidence | Depth hash only / omitted; confidence AUC undefined (n=0) |
| World points + confidence | Points kept; confidence discarded | Both omitted / omitted; confidence AUC undefined (n=0) |
| Tower gravity, trajectory step, validity | Conversion computes them, then discards them | Absent / absent |
| Tokens, LayerNorm, refinement intermediates | Transient; no exported scalar token norm | Absent / absent |
| Metric scale | One scalar from service scale path | Saved / frozen T1 input |
| Checkpoint gravity | Defines gravity world; direction recoverable from R0 | World [0,0,1] plus recoverable normalized origin up / frozen own-head vector |
| Checkpoint own depth/pose | Depth supplies default scale; own poses distinct from tower | Absent / absent |
| Crop/grid/indices/intrinsics | Sampling and binding metadata | Indices/K/transforms saved / IDs/slots saved; not confidence |

The full inventory distinguishes model outputs from transient conversion quantities, own checkpoint heads, and downstream SAM3/selector scores. G3T confidence is 1+exp(logit), not a calibrated probability. The vendor tracking outputs exist only in its docstring. gpkg/runtime/c.py:55 writes geometry without depth pixels, confidence, points, tokens or own pose9; all records confirm that omission.

AUC below uses increasing scores and half credit for ties; counts are positive/pass captures. Low origin-up z reverses the listed direction. Every arm/summary and both directions appear in CONF_R10.md/JSON. Scalar scale/gravity summaries have no frame spread; per-frame statistics use mean, min, population std and max−min on 32 anchors.

| Candidate (higher means flag) | All gross/pass | All fail/pass | ARKit gross/pass | ARKit fail/pass |
| --- | --- | --- | --- | --- |
| Metric scale | 0.600 (10/6) | 0.552 (32/6) | 0.312 (8/2) | 0.405 (21/2) |
| World gravity components/norm (constant) | 0.500 (10/6) | 0.500 (32/6) | 0.500 (8/2) | 0.500 (21/2) |
| Origin up x | 0.400 (10/6) | 0.422 (32/6) | 0.812 (8/2) | 0.714 (21/2) |
| Origin up y | 0.917 (10/6) | 0.833 (32/6) | 1.000 (8/2) | 0.857 (21/2) |
| Origin up z (low is worse) | 0.083 (10/6) | 0.167 (32/6) | 0.000 (8/2) | 0.143 (21/2) |
| Origin tilt from camera-up, degrees | 0.917 (10/6) | 0.833 (32/6) | 1.000 (8/2) | 0.857 (21/2) |
| Anchor tilt mean | 0.850 (10/6) | 0.661 (32/6) | 0.938 (8/2) | 0.881 (21/2) |
| Anchor tilt maximum | 0.900 (10/6) | 0.667 (32/6) | 1.000 (8/2) | 0.810 (21/2) |
| Camera-up x RMS | 0.950 (10/6) | 0.724 (32/6) | 0.875 (8/2) | 0.714 (21/2) |
| Camera-up x maximum | 0.867 (10/6) | 0.740 (32/6) | 1.000 (8/2) | 0.952 (21/2) |
| Consecutive rotation maximum | 0.950 (10/6) | 0.573 (32/6) | 1.000 (8/2) | 0.762 (21/2) |
| Consecutive translation mean | 0.917 (10/6) | 0.792 (32/6) | 0.750 (8/2) | 0.762 (21/2) |
| Translation second-difference RMS | 0.950 (10/6) | 0.844 (32/6) | 0.875 (8/2) | 0.857 (21/2) |
| T2–T1 relative-rotation RMS | 0.608 (10/6) | 0.440 (32/6) | 0.438 (8/2) | 0.333 (21/2) |
| K3d A′–T1 relative-rotation RMS | 1.000 (5/2) | 0.938 (8/2) | 1.000 (5/2) | 0.938 (8/2) |
| Dense–T1 anchor difference (inherited) | 0.500 (10/6) | 0.500 (32/6) | 0.500 (8/2) | 0.500 (21/2) |

Origin tilt is acos(−g_y), where g is normalized checkpoint gravity in the origin camera; from captured c2w, g=R0ᵀ[0,0,1]. Anchor tilt and lateral-up RMS transport this predicted up through the tower poses. They measure predicted camera orientation, not disagreement with independent gravity. Motion statistics are plausibility proxies; legitimate motion can trigger them, and second differences are not time-normalized acceleration.

Illustrative read-time rule: if origin tilt >51°, use the direct answer. It flags 19/38 captures: 8 gross, 11 moderate, 0 pass; 42/76 GT-overlap distance items (42/150 total) and 34/900 camera items at each step would map to fallback. Restricting the same rule to ARKit flags 17/23 captures and 26 distance items; the camera corpus has no ARKit items.

The >51° rule flags ARKit 41069053, 41069054, 41098140, 41098149, 41291639, 41291643, 42446117, 42897921, 42897936, 42897942, 42899532, 42899535, 43828324, 45663051, 47332556, 47332598, 47332599; and ScanNet++ 17c5e6a336, ad562ce09b. It misses both non-ARKit gross captures.

Alternative: camera-up x RMS >0.085 flags 13/38 (8 gross, 5 moderate, 0 pass), 26 distance items and 92 camera items per step. Its gross/pass AUC is 0.950 overall but 0.875 within ARKit. Complete capture lists and thresholds for every ≥0.9 candidate are in CONF_R10.md/JSON; none is validated on held-out captures.

K3d A′–T1 relative-rotation RMS >1° flags six measured ARKit captures: 41069054, 41291643, 42899535, 44358634, 45663051, 47332598 (5 gross, 1 moderate; 11 distance items, 0 camera items). Its AUC is 1.000 (5/2) for gross/pass and 0.938 (8/2) for fail/pass. The other 28 captures remain unmeasured, not passing; this is not a one-pass read-time flag. Decode/numerical changes confound interpreting it as stochastic uncertainty.

Camera fallback counts are capture-level mappings from the distance-read flags into the R8 corpus, conditional on transferring that flag across reads. They are not evaluations on the exact camera-read tensors. The 37 camera-only captures lack a flag assignment. No direct-answer counterfactual score was measured.

Depth-confidence valid-pixel means, depth reprojection, point/depth consistency, tower-vs-own pose and tower-vs-own gravity disagreement are undefined (n=0): required tensors were not saved. R8’s gravity-error AUC 0.900 uses GT, so it cannot justify a read-time rule. Dense inherits T1 anchor geometry exactly and supplies no independent consistency test.

All capture hashes and the K3d receipt verify; 10 instability values reproduce the existing scorer. Independent rank-sum checks reproduce 1392 AUCs; all 323 rule counts reconcile. Extraction: 16.62 s, 89.8 MiB peak RSS, one numerical thread, 18 GiB address-space cap. No inference, SSH, Git, GPU, network, deletion or submission ran.

[Full inventory, summaries, AUCs and rules](../cap/score_conf/CONF_R10.md) · [Machine-readable evidence](../cap/score_conf/CONF_R10.json). New analysis sources: analyze_round10.py and render_round10.py. All writes are new session files in gbuild or cap/score_conf.
