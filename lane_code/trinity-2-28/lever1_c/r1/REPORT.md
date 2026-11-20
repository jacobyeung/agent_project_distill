The depth package and seven-cell CPU relift harness are built. CPU validation passes; the missing-depth dry run stops cleanly. No mask-ceiling measurement or selection/completeness verdict is available before the depth return and all-150 parity gate.

The package is `out/delivery.tgz`, token `a09fdd101cc93`. `PLACE.md` gives the exact lane commands, byte counts, receipt names, and governed stream. The builder ran only CPU work on trinity-2-28, with writes inside `r1/`; it ran no SSH, Git, network, GPU, Slurm, or deletion command.

| Forecast | Value |
| --- | ---: |
| Worker | 16.75 minutes |
| Including staging/publication allowances | 28.75 minutes |
| Requested allocation | 40 minutes |
| Compressed depth return | 40 MB forecast; 80 MB conservative budget |
| Enforced compressed cap | 1.0 GB |
| Delivery | 6,265,674 bytes |

T1's recorded first item for each of the 60 captures took 1,005.013 seconds in total, including SAM and linking. Its tower calls took 430.614 seconds. The forecast retains the full 1,005.013 seconds, adds 600 seconds for staging and 120 for publication, and does not claim that those allowances were measured. The inherited package checker requires at least 40 allocated minutes. The worker itself has a 30-minute cap.

The writer runs one original prompt prefill per capture and calls the unchanged lazy geometry constructor. Own depth and gravity depend on that prefill, so a tower-only forward cannot reproduce serving. The worker disables the segmentation socket and stops after geometry construction: it performs no segmentation, linking, selector query, answer decoding, or repeat. It retains the sealed tower forward, including its auxiliary point-head computation, rather than claim an untested equivalent shortened forward. The same PNG binder, dense tower inputs, own-depth scale adapter, and camera conversion remain active.

Each capture returns the served metric depth grid at the lift's actual 32 × 51 × 51 resolution, float16; an exact float64 residual; the depth-grid axis; intrinsics; metric and unscaled camera-to-world matrices; applied scale; source/anchor/dense indices; canvas-to-source transform; source size; raw/selected mask grids; and the pinned RGB binding digest. Float16 alone occupies 9,987,840 bytes across 60 captures. The residual prevents storage quantization from independently breaking the zero-tolerance parity gate. Depth reconstruction is byte-exact in the round-trip test. The original applied scale is retained as metadata; the CPU geometry constructor receives already-metric depth and cameras with scale one.

The runtime compares every available T1 item geometry for each capture, not just the representative item. T1 supplies geometry for 149 calling items covering all 60 captures; its sole non-caller has no geometry record. Twice the largest corresponding primary/repeat absolute difference across ten T1 repeats gives these bounds:

| Field | Absolute bound |
| --- | ---: |
| Applied scale | 0.00004291534423828125 |
| Metric camera matrix entries | 0.003719304943947843 |
| Unscaled camera matrix entries | 0.0013606724294485811 |
| Intrinsic matrix entries | 0.15798443532821693 |
| Canvas-to-source entries | 0 |

The matrix bounds apply elementwise; they are not rotation-angle bounds. `out/REFERENCE.json` contains all repeat deviations and reference geometries. The returned receipt records per-item, per-capture, and global maximum deviations and a Boolean trusted flag. A failed bound still publishes the complete or partial capture. The 60-capture failure-path test verifies this behavior.

The relift CLI authenticates the returned gzip with its verified upload receipt, checks all 60 capture identities and RGB bindings, then evaluates served masks on all 150 items. T1's registered printed-gap tolerance is **0.00 m**, because all repeat printed gaps matched. The CLI rounds the imported gap formula through the reader's own two-decimal formatter before comparison. It requires 95% of operand flags to match; each operand inherits its item's printed-gap comparison, so this equals the all-150 item fraction. It emits no intervention cells after a failed gate.

The cells use the following explicit operations. The harness imports the deployed lift, box fit, formatter, score, and gap formula; it reuses rank 3's exact-search acceleration and transport.

| Cell | Operation |
| --- | --- |
| a | Saved selected masks through deployed bestspread and minimum-area fit. |
| b | Existing accepted linked candidate with maximum full mask-volume IoU against the bound GT instance. Input-order ties are stable; zero overlap yields null. |
| c | Pool b plus candidates from the unchanged lift/link/accept producers with the proposal score floor changed from 0.3 to 0. Detector retention is unchanged. |
| d | Pool c's choice plus per-frame unions of tracks matching the same GT identity in at least half their nonempty frames at IoU > 0.25. |
| e | Landscape GT instance masks through the deployed bestspread and minimum-area fit. |
| f | Each GT view through the deployed spread filter; imported 5 cm, two-frame voting plus the largest view; deployed minimum-area fit. |
| g | Cell e's camera-local points through each operand's own GT anchor into GT world, then rank 3's transport at anchor 1 into one common served world. |

Cell f uses the sealed `vote_points` rule and the vote-plus-best support rule documented by `PolicyBoxProvider`. It does not introduce that older provider's erosion, depth-cut, random 4,000-point cap, alternate fitter, or best-view gap override. Cell g changes relative pose while retaining served depth, intrinsics, mask support, and metric scale. Its synthetic test replaces an 8 m relative-translation error without changing object size. These definitions are recorded in the output before interpreting any real result.

The saved census contains **66 GT-bound items**, not 72. The specified 20 portrait objects account for ten bound items; censoring them leaves **56 items across 28 captures**. All 38 available GT capture files remain accounted for. Missing annotations and unbound operands are explicit exclusions. `out/COHORT.json` lists the eligible items; no fuzzy label matching, portrait rotation, or fitted scale is used.

Every cell reports all-data, ARKit, and ScanNet/ScanNet++ means and paired differences from a. The harness reuses the 10,000 item-weighted bootstrap draws over the original 46 physical rooms, seed 20261120. Undefined subgroup draws are counted. It applies the registered G = e − a and b − a thresholds mechanically only after parity passes.

Validation: **14 CPU tests pass**, including the delivered numeric entry with stub weights, actual operator rehearsal, package/resource pins, known-box GT-mask lifting, vote support, relative-pose transport, all-cell dataset bootstrap, dump round trips and cap, failed-parity return retention, and 20 real T1 printed gaps at 0.00 m tolerance. Fresh-process reader provenance and the inherited package input checker both pass. All authored shell scripts pass `bash -n`. The dry run writes `out/DRY_RUN.json` with `depth return missing`.

The public job/transport token and added payload filenames are opaque, following the inherited kit. Worker and staging stdout/stderr are discarded to prevent third-party names and paths from entering public logs; returned errors use numeric codes and hex-encoded types. The sealed inherited source layout and scientific receipt contents remain descriptive, as in the trusted T1 kit. Live Orchard staging, allocation, GPU numerics, runtime, and publication remain untested.
