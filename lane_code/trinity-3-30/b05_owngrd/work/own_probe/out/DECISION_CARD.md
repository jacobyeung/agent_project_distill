# E-A decision rules

`work/RULES.json` and its SHA256 pin fix the rules before GPU measurement. No clean-33 read is authorized.

The primary readout standardizes each native channel of each of four taps, applies non-affine token layer norm, averages channels to 256 per tap, and applies layer norm again. The final-layer control uses the same standardization and 1,024 channels. The unstandardized four-tap control omits channel standardization and retains both layer norms. All three have 1,024 input channels and identical head capacity. The primary readout alone chooses keys.

Extraction fits per-channel means and population variances on every stride-selected **train** frame. Validation and tuning cannot contribute. A streaming calibration sweep retains only channel moments; the variance floor is 1e-6. A second sweep applies those fixed statistics to every split. Dense features never reach disk. T2/T3 load the same pinned statistics. A8 uses the separately fitted A2/A4 transforms. The card reports every arm/tap's token-weighted largest-channel energy share before and after standardization, after token layer norm.

Every arm/readout receives 1,200 T1, 1,500 T2, 1,500 T3 and 800 T4 steps; fusion receives 300 when its training inputs exist. Learning rates are 0.001 for T1/T4, 0.0001 for T2/T3 and 0.01 for fusion. T2/T3 globally shuffle batches of four, seed 17. G3T sees each sampled frame's ordered clip. There is no per-arm search.

All intervals use 4,000 paired bootstrap draws over rooms at 95% confidence, seed 17. Each sampled room retains every object and its observations. The card rejects mismatched paired cohorts.

| Rule | Decision |
|---|---|
| R1 | Compare feature-only T1 on-target share with A7 under the same head. FAIL if the upper bound of arm − A7 is below −0.03; PASS if the lower bound is above −0.03; otherwise INCONCLUSIVE. Name-consistent and held-out training-room top-1 bars fail only if their upper bounds are below 0.90. |
| R1+ | Fused gain over SAM selection ≥0.05, with a strictly positive paired lower bound. This sends a selector to branch S; it does not choose keys. |
| R2 | SAM-target IoU divided by A7's same-target IoU ≥0.80 overall and ≥0.60 below 1% area. R2 chooses mask keys only. |
| R3 | Presence AUROC ≥0.95 and shortlist recall minus SAM recall ≥−0.02. |
| R4 | Retrieval gain over centroid ≥0.05 with a positive interval, or member AUROC ≥0.85 with a positive paired AUROC gain. |

For R2–R4, an interval clearing the bar passes, an interval wholly below it fails, and an overlapping interval is INCONCLUSIVE. Missing measurements are PENDING. **R1 INCONCLUSIVE permits the pilot**: 221 tuning objects resolve roughly eight points, and the room-disjoint pilot read supplies the stronger test.

The card prints every available pair of T1 differences and a written provisional selection choice even while R2/R3 remain PENDING. A1 is the own default. A2 replaces it only when the entire A1 − A2 interval is negative and A2 has no failed applicable selection gate. The provisional choice uses T1/R1 alone; the selection/presence choice also respects R3. A failed own gate cannot by itself justify switching on a point estimate.

An outside arm replaces the own arm only when its paired T1 improvement excludes zero and it fails neither R1 nor R3. Challenger order is A8, A3, A5, A6; unresolved comparisons keep the current choice. R2 never vetoes or changes selection/presence keys. If the preferred own arm fails R1/R3 and no separably better eligible arm exists, selection waits; the provisional T1 evidence remains visible.

Mask keys use the selection arm when it passes R2. Otherwise they use A7, unless an outside arm's paired per-object mean SAM-target IoU improvement over the selected own baseline excludes zero. That arm becomes a **frozen dense tower for masks only**. Both R2 ratio bars remain visible. A positive point estimate with an interval containing zero never switches mask keys.

`ready_for_downstream` permits R1 INCONCLUSIVE but waits for R1/R3 measurements and matched T1/T4 controls. R2 PENDING leaves masks with SAM and does not erase selection. The pilot can ship selection and presence while retaining tower masks. A4 adds G3T only when R4 passes. Any clean read needs a separate `rev_ctrl` card.
