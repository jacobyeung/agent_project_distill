# Capture acceptance rules

Registered before new-capture measurements. Dataset reproduction must pass first.
All 32 source indices must match the manifest; all served PNG SHA256 values must verify.
Poses must be finite proper rigid transforms (maximum orthogonality/determinant/bottom-row error <= 1e-4).
Depth must be finite and nonnegative. Every labeled pixel must have positive depth and a declared instance ID.
REPORT6 geometry: more than half of visible instance/anchor pairs must have projected-box versus mask-bounding-box IoU > 0.25.
Report lifted-point containment too: require at least 95% of labeled pixels within their boxes. T1 allows 1e-4 m arithmetic slack. ARKit allows its native 0.03 m assignment margin plus the world-coordinate displacement caused by nearest-neighbor source-pixel sampling (computed per point); this is a sampling bound, not an enlarged stored box.
ScanNet stores full lengths. ScanNet++ v1 stores half lengths, doubled when projecting and checking containment. ARKit stores full lengths.
REPORT9 binding: uniquely bind query labels using strip/lowercase, pool visible same-frame object/anchor rows, and compare raw served-frame proposals against same, shifts -2/-1/+1/+2, 180-degree rotation, horizontal/vertical flips, and portrait 90-degree rotations. Score empty predictions as zero; omit out-of-range shifts. Require a measured positive same-frame median and no alternative with paired median gain > 0.2 in either T1 or points arm. An unmeasured arm fails, rather than passing vacuously. Preserve all alternative scores and paired baselines.
ScanNet++ additionally requires median aligned-pose versus COLMAP camera-center discrepancy < 0.05 m.
No pose correction, box fit, frame shift, or tolerance adjustment is selected from these checks.
