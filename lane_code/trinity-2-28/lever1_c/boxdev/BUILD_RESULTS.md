Build checks passed. The real 150-item dev verdict remains pending.

Six tests passed: exact synthetic depth round-trip and base equality on all 150 items; a complete 150-item synthetic run; STOP before arm evaluation on a failed gate; an independent bootstrap seed check; real T1 depth-free parity; and frozen-vote/renderer agreement.

Real T1: all 142 available stored-box/printed-gap checks matched at 0.00 m across the authenticated 150-item capture. This does not test real depth relifting.

K1: three changed predictions in arkitscenes/41098085 reproduced r2/out_box/BOX.json exactly, including voted printed boxes. The replay uses saved selected-mask memberships and original local inputs; it does not rerun selector inference.

| K1 row suffix | Base gap (m) | Vote gap (m) |
|---|---:|---:|
| 27762848dd42 | 0.81 | 0.76 |
| a950ad14a47d | 3.75 | 3.72 |
| caf0b388c0e2 | 2.78 | 2.77 |

CPU: AMD EPYC 9224 24-Core Processor on trinity-2-28; one process, one numeric-library thread, nice 10.

| Measured workload | Base seconds/item | Vote seconds/item | Base peak traced MiB | Vote peak traced MiB | Extra peak traced MiB |
|---|---:|---:|---:|---:|---:|
| Synthetic, 150 items | 0.007196 | 0.006523 | 0.135 | 0.132 | -0.002 |
| K1, three changed rows | 0.101351 | 0.075496 | 19.972 | 18.125 | -1.847 |

Each timing covers both operands: lift, fit, served guard/box formatting, and exact grid gap. Peak traced allocation is measured in a separate pass. It is not total RSS. These small fixtures do not estimate the real dev distribution; the runner records all 150 real per-item measurements once depth arrives.

Both readers touch the same grounded frames. Base repeats the best frame; vote retains filtered points from all valid frames and builds voxel-support counts. Per-object frame lists, lift calls, and retained numeric bytes are in K1_TEST.json and SYNTHETIC_MEASUREMENTS.json.

The renderer test changes numeric box responses while preserving the field format. GT-valued training supervision can remain GT-valued; training traces intended to reproduce the voted reader require re-rendered numeric observations and a GT-answer consistency audit. The complete training corpus was not inspected.

Not verified: real served-depth parity, real dev scores/intervals/verdict, or real dev runtime. Both returned/0.gz and returned/4.json were absent at build time.
