# Verbatim excerpts of the G3T measurements gate_eval.G3T_REFERENCE quotes

## lanes/g3t_scale_20261029/RESULT.md, section 1 (sha256 b322518cb23939664e104bedf0923974dbafd8ffd5ff572abf83b944a61c0deb)

| Dataset | $n$ | Median $s$ | Mean $s$ | IQR of $s$ (P25–P75) | Min–Max $s$ | Mean $\ln s$ | SD($\ln s$) | Mean $|\ln s|$ | Sim(3) Rot Err Mean (Med) | Procrustes Rot Err Mean (Med) | Pairwise Rel Rot Mean (Med) | Median ATE RMS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **ScanNet** (`scannet`) | 30 | **1.995** | 1.942 | 1.374–2.362 | 0.954–3.261 | +0.608 | **0.345** | 0.611 | 3.23° (2.75°) | 2.41° (2.13°) | 3.47° (2.96°) | 0.066 m |
| **ScanNet++** (`scannetppv2`) | 32 | **2.259** | 2.541 | 1.858–2.633 | 1.410–8.448 | +0.857 | **0.356** | 0.857 | 4.13° (2.29°) | 3.19° (1.71°) | 4.51° (2.55°) | 0.089 m |

## lanes/g3t_scale_20261029/PROBE_RESULT.md, By dataset (ridge) (sha256 e2322e854d178bd329f269856a3b47c1f42b9f3cd1d694e0c667fb2b84187bc1)

| features | d1 (502) MRA | d1 ln err | d1 R² | d2 (684) MRA | d2 ln err | d2 R² |
|---|---|---|---|---|---|---|
| g3t | 0.939 [0.931, 0.947] | 0.052 | 0.949 [0.932, 0.961] | 0.907 [0.895, 0.919] | 0.070 | 0.912 [0.882, 0.937] |
